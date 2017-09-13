import unittest
import mock
import os
import sys
sys.path.insert(0, '../redeem')
# sys.path.insert(0, './gcode/TestStubs')

sys.modules['evdev'] = mock.Mock()
sys.modules['RotaryEncoder'] = mock.Mock()
sys.modules['Watchdog'] = mock.Mock()
sys.modules['GPIO'] = mock.Mock()
sys.modules['Enable'] = mock.Mock()
sys.modules['Key_pin'] = mock.Mock()
sys.modules['GPIO'] = mock.Mock()
sys.modules['DAC'] = mock.Mock()
sys.modules['ShiftRegister.py'] = mock.Mock()
sys.modules['Adafruit_BBIO'] = mock.Mock()
sys.modules['Adafruit_BBIO.GPIO'] = mock.Mock()
sys.modules['StepperWatchdog'] = mock.Mock()
sys.modules['StepperWatchdog.GPIO'] = mock.Mock()
sys.modules['_PathPlannerNative'] = mock.Mock()
sys.modules['PruInterface'] = mock.Mock()
sys.modules['PruInterface'].PruInterface = mock.MagicMock() 
sys.modules['PruFirmware'] = mock.Mock()
sys.modules['HBD'] = mock.Mock()
sys.modules['RotaryEncoder'] = mock.Mock()
sys.modules['JoinableQueue'] = mock.Mock()
sys.modules['USB'] = mock.Mock()
sys.modules['Ethernet'] = mock.Mock()
sys.modules['Pipe'] = mock.Mock()

from CascadingConfigParser import CascadingConfigParser
from Redeem import *
from EndStop import EndStop


"""
Override CascadingConfigParser methods to set self. variables
"""
class CascadingConfigParserWedge(CascadingConfigParser):
    def parse_capes(self):
        self.replicape_revision = "0A4A" # Fake. No hardware involved in these tests (Redundant?)
        self.reach_revision = "00A0" # Fake. No hardware involved in these tests (Redundant?)


class MockPrinter(unittest.TestCase):

    """
    MockPrinter, in combination with the many sys.module[...] = Mock() statements
    above, creates a mock Redeem instance. The mock instance has only what is
    needed for our tests and does not access any BBB hardware IOs.
    """

    @classmethod
    def setUpPatch(cls):
        """"
        Override this method for mocking something other than the path planner
        """
        cls.printer.path_planner = mock.MagicMock()

    @classmethod
    def setUpConfigFiles(cls, path):
        """
        This seems like the best way to add to or change stuff in default.cfg,
        without actually messing with the prestine file. Overwrite if you want
        different printer.cfg and/or local.cfg files. For example, copy example filles...

        copyfile(os.path.join(os.path.dirname(__file__), "my_test_local.cfg"), os.path.join(path, 'local.cfg'))
        copyfile(os.path.join(os.path.dirname(__file__), "my_test_printer.cfg"), os.path.join(path, 'printer.cfg'))

        """
        tf = open("../configs/local.cfg", "w")
        lines = """
        [System]
        log_to_file = False
        """
        tf.write(lines)
        tf.close()

    @classmethod
    @mock.patch.object(EndStop, "_wait_for_event", new=None)
    @mock.patch.object(CascadingConfigParser, "get_key")
    @mock.patch("Redeem.CascadingConfigParser", new=CascadingConfigParserWedge)
    def setUpClass(cls, mock_get_key):

        mock_get_key.return_value = "TESTING_DUMMY_KEY"

        """
        Allow Extruder or HBP instantiation without crashing 'cause not BBB/Replicape
        """
        class DisabledExtruder(Extruder):
            def enable(self):
                self.avg = 1
                self.temperatures = [100]
                pass
        class DisabledHBP(HBP):
            def enable(self):
                pass
        mock.patch('Redeem.Extruder', side_effect=DisabledExtruder).start()
        mock.patch('Redeem.HBP', side_effect=DisabledHBP).start()

        cfg_path = "../configs"
        cls.setUpConfigFiles(cfg_path)

        cls.R = Redeem(config_location=cfg_path)
        cls.printer = cls.R.printer

        cls.setUpPatch()

        cls.gcodes = cls.printer.processor.gcodes
        cls.printer.send_message = mock.create_autospec(cls.printer.send_message)

        cls.printer.movement = Path.ABSOLUTE
        cls.printer.feed_rate = 0.050  # m/s
        cls.printer.accel = 0.050 / 60  # m/s/s

        Gcode.printer = cls.printer
        Path.printer = cls.printer

        cls.printer.speed_factor = 1.0
        """ 
        We want to ensure that printer.factor is always obeyed correctly
        For convenience, we'll set it to mm/inch and check that resulting 
        paths have the correct meter values, converted from inch input.
        """
        cls.printer.unit_factor = cls.f = 25.4  # inches

        cls.printer.probe_points = []

    @classmethod
    def tearDownClass(cls):
        cls.R = cls.printer = None
        if os.path.exists("../configs/local.cfg"):
            os.remove("../configs/local.cfg")
        if os.path.exists("../configs/printer.cfg"):
            os.remove("../configs/printer.cfg")

    """ directly calls a Gcode class's execute method, bypassing printer.processor.execute """
    @classmethod
    def execute_gcode(cls, text):
        g = Gcode({"message": text})
        cls.printer.processor.gcodes[g.gcode].execute(g)
        return g

    @classmethod
    def full_path(cls, o):
        return o.__module__ + "." + o.__class__.__name__

    def assertCloseTo(self, a, b, msg=''):
        """test to the nearest thousandth of a millimeter"""
        match = np.isclose(a, b, rtol=1e-6, atol=1e-6)
        if not match:
            exception = self._formatMessage(msg, "{} is not close to {}: {}".format(a, b, msg))
            raise self.failureException(exception)