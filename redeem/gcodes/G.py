"""
GCode G
List all implemented G-codes (help)

Author: Elias Bakken
email: elias.bakken(at)gmail(dot)com
Website: http://www.thing-printer.com
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""

from GCodeCommand import GCodeCommand


class G(GCodeCommand):

    def execute(self, g):
        gcodes = self.printer.processor.get_supported_commands_and_description()
        if g.has_letter("F"):
            formatting = g.get_int_by_letter("F", 0)
            # Format for Wiki
            if formatting == 0:
                self.printer.send_message(g.prot, "===G: List of currently implemented G-codes===")
                self.printer.send_message(g.prot, "This list has been autogenerated by issuing 'G F0' in Redeem")
                for gcode, desc in sorted(gcodes.items()):
                    if gcode[0] == "G":
                        self.printer.send_message(g.prot, "===="+gcode+": "+desc+"====")
                        l_desc = self.printer.processor.gcodes[gcode].get_long_description()
                        self.printer.send_message(g.prot, l_desc)
                        
        else:
            self.printer.send_message(g.prot, "Implemented G-codes:")
            for gcode, desc in sorted(gcodes.items()):
                if gcode[0] == "G":
                    self.printer.send_message(g.prot, gcode+": "+desc)

    def get_description(self):
        return "List all implemented G-codes"
    
    def get_long_description(self):
        return ("Lists all the G-codes implemented by this firmware. "
                "To get a long description of each code use '?' "
                "after the code name, for instance, G0? will give a long decription of G0") 
