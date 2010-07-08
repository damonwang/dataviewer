class FileTypeError(Exception):
    def __init__(self, filename): 
        self.filename = filename
    
    def __str__(self):
        return "FileTypeError: %s of unrecognized type" % self.filename

class CtrlError(Exception):
    def __init__(self, ctrl, value):
        self.ctrl = ctrl
        self.value = value

    def __str__(self):
        return "CtrlError: %s set to %s (invalid)" % (self.ctrl, self.value)
