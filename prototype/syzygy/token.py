class Token(object):
    def __init__(self, type, text, line):
        self.type = type
        self.text = text
        self.line = line

    def __init__(self, type, text, line, lit):
        self.type = type
        self.text = text
        self.line = line
        self.literal = lit

    def toString():
        return "Line: {self.line} Token: {self.type} Text: {self.text}"