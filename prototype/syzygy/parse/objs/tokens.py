class Token(object):
    def __init__(self, type, text, line, lit=None):
        self.type = type
        self.text = text
        self.line = line
        self.literal = lit


    def toString(self):
        return f"Line: {self.line} Token: {self.type} Text: {self.text}"