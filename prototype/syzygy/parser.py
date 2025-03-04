import interpreter
from token import *
from tokentype import *

class Parser(object):
    def __init__(self, tokens):
        self.tokens = tokens
        self.current = 0
        self.statements = []

    def parse(self):
        while not self.atEnd():
            self.statements.append(self.declaration())
        return self.statements
    
    def declaration(self):
        if self.match(VAR): return self.variableDeclaration()
        else: return self.statement()

    def statement(self):
        if self.match(POINT): return self.pointStatement()
        elif self.match(FORCE): return self.forceStatement()
        elif self.match(UPDATE): return self.updateStatement()

    # Helper functions
    def match(self, type):
        return self.tokens[self.current].type == type

    def atEnd(self):
        return self.peek().type == EOF
    
    def peek(self):
        return self.tokens[self.current]
    
    def previous(self):
        if self.current == 0: return None
        else: return self.tokens[self.current - 1]
    
    def advance(self):
        if not self.atEnd(): self.current += 1
        return self.previous()
    