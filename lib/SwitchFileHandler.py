'''
    SwitchFileHandler
    Extension of FilHandler class from the logging module.
    Does:
        flush() - allows user to ensure log data is in the file when you need it
        switchLog() - switches from current log to new copy, renames outgoing current after
                        deleting previous previous
'''
import logging
import os

class SwitchFileHandler(logging.FileHandler):
    
    def switchLog(self, logName, saveName, mode="a", encoding="UTF-8"):
        try:
            os.remove(saveName)
        except OSError as e:
            pass
        os.rename(logName, saveName)
        formatter = self.formatter
        level = self.level
        self.close()
        self.__init__(logName, mode, encoding)
        self.setFormatter(formatter)
        self.setLevel(level)
        
    def flush(self):
        if hasattr(self.stream, "flush"):
            self.stream.flush()