# Python file used for defining utilities

from sys import stdout
from typing import TextIO
from datetime import date, datetime


# can be replaced by default logging from Python
class Printer:
    '''Class used for printing stuff either to a console or to a log file'''
    output_str: TextIO = stdout

    def __init__(self, output="") -> None:
        if (output != ""):
            try:
                 self.output_str = open(output, mode='at')
            except:
                print("Can't open file for logging!")
                exit(1)
               
    def __del__(self) -> None:
        if (self.output_str != stdout):
            self.output_str.close()
        print("printer got destroyed")

    def printout(self, msg) -> None:
        current_datetime = "[" + date.today().strftime("%d/%m/%Y") + " - " + datetime.now().strftime("%H:%M:%S") + "] "
        self.output_str.write(current_datetime + str(msg) + '\n')