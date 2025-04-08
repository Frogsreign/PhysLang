import syzygy.parse.objs.interpreter as interpreter
from syzygy.parse.objs.tokens import *
from syzygy.parse.objs.tokentype import *

# Scanner class
class Scanner(object):
    def __init__(self, text):
        # Text to scan
        self.source = text

        # Track location in the text
        self.start = 0
        self.current = 0
        self.line = 0

        # Storage for tokens
        self.tokens = []

        self.reserved = {
            'point': POINT,
            'force': FORCE,
            'update': UPDATE,
            'solid': SOLID,
            'pos': POS,
            'var': VAR,
            'vel': VEL,
            'acc': ACC,
            'input': INPUT,
            'func': FUNC,
            'm': M,
            'e': E
        }

    def scan(self):
        
        # Loop through the text and get tokens
        toke = None
        while not self.atEnd() and (toke := self.getNextToken()) != None:
            if toke.type != IGNORE: self.tokens.append(toke)

        # End with EOF
        self.tokens.append(Token(EOF, None, self.line))

        return self.tokens

    # Interface for token scanning
    def getNextToken(self):
        token = None

        token = self.getSingleCharacterToken()
        # if token == None: token = self.getPeriodToken()
        if token == None: token = self.getComparisonToken()
        if token == None: token = self.getStringToken()
        if token == None: token = self.getNumericToken()
        if token == None: token = self.getReservedToken()
        if token == None: 
            character = self.source[self.current]
            raise Exception(f"Unexpected character {character} at position {self.current}.")
        
        return token

    # Token parsing functions
    def getSingleCharacterToken(self):
        nextChar = self.source[self.current]

        type = UNDEFINED

        # Switch tree on character
        if nextChar == '(': type = LEFT_PAREN
        elif nextChar == ')': type = RIGHT_PAREN
        elif nextChar == '{': type = LEFT_BRACE
        elif nextChar == '}': type = RIGHT_BRACE
        elif nextChar == '[': type = LEFT_BRACK
        elif nextChar == ']': type = RIGHT_BRACK
        elif nextChar == ',': type = COMMA
        elif nextChar == '-': type = MINUS
        elif nextChar == '+': type = PLUS
        elif nextChar == '*': type = MULTIPLY
        elif nextChar == '/': type = DIVIDE
        elif nextChar == '^': type = EXPONENT
        elif nextChar == ';': type = SEMICOLON
        elif nextChar == '&': type = AND
        elif nextChar == '|': type = OR
        elif nextChar == '\n':
            type = IGNORE
            self.line += 1
        elif nextChar == ' ': type = IGNORE
        elif nextChar == '\t': type = IGNORE
        else: pass

        # Valid token
        if type != UNDEFINED:
            self.current += 1
            return Token(type, nextChar, self.line)
        else: return None
        
    def getComparisonToken(self):
        nextChar = self.source[self.current]

        type = UNDEFINED
        if nextChar == '!':
            if self.checkForChar('='): type = NOT_EQUAL
            else: type = NOT
        elif nextChar == '=':
            if self.checkForChar('='): type = EQUIVALENT
            else: type = ASSIGN
        elif nextChar == '<':
            if self.checkForChar('='): type = LESS_OR_EQUAL
            else: type = LESS_THAN
        elif nextChar == '>':
            if self.checkForChar('='): type = GREATER_OR_EQUAL
            else: type = GREATER_THAN

        if type != UNDEFINED:
            if self.checkForChar('='):
                self.current += 2
                return Token(type, self.source[self.current-2:self.current], self.line)
            else:
                self.current += 1
                return Token(type, nextChar, self.line)
        else: return None

    def getNumericToken(self):
        nextChar = self.source[self.current]
        type = UNDEFINED
        
        # messy logic for handling periods and exponential notation
        if nextChar.isdigit() or nextChar == ".":
            start = self.current
            periodFound = (nextChar == ".")
            eFound = False
            if periodFound and self.current + 1 < len(self.source):
                self.current += 1
                nextChar = self.source[self.current]
            elif periodFound:
                raise Exception("Solitary '.' unexpected.")
            while nextChar.isdigit() or nextChar == '.' or nextChar == 'e':
                if nextChar == '.' and periodFound:
                    raise Exception("Invalid number with two periods ('.').")
                elif nextChar == '.':
                    periodFound = True

                if nextChar == "e" and eFound:
                    raise Exception("Multiple 'e's not permitted in number.")
                elif nextChar == "e":
                    eFound = True
                    dashFound = False
                    if self.current + 1 < len(self.source) and dashFound == False:
                        if self.source[self.current + 1] == "-": 
                            self.current += 1 # increase past the - if we have the right character
                            dashFound = True
                        
                            
                self.current += 1
                if (self.atEnd()): break

                nextChar = self.source[self.current]
            
            numberText = self.source[start:self.current]
            numberValue = float(numberText)
            return Token(NUMBER, numberText, self.line, numberValue)
        
        return None

    def getStringToken(self):
        nextChar = self.source[self.current]
        type = UNDEFINED
        
        if nextChar == '"':
            start = self.current
            while not self.atEnd():
                self.current += 1
                if self.atEnd() or self.source[self.current] == '\n':
                    self.current = start
                    raise Exception(f'String starting at position {start} on line {self.line} did not end before new line. Multi-line strings are not supported.')
                
                if self.source[self.current] == '"':
                    text = self.source[start+1:self.current]
                    self.current += 1
                    return Token(STRING, text, self.line, text)
                
            raise Exception(f'String starting at position {start} on line {self.line} terminate.')

        else: return None    

    def getReservedToken(self):
        nextChar = self.source[self.current]
        type = UNDEFINED
        
        if nextChar.isalpha():
            start = self.current
            while nextChar.isalpha() or nextChar == '.':
                self.current += 1
                if (self.atEnd()): break

                nextChar = self.source[self.current]

            word = self.source[start:self.current]

            if word in self.reserved: return Token(self.reserved[word], word, self.line, word)
            else: return Token(IDENTIFIER, word, self.line, word)

        if nextChar == ".":
            self.current += 1
            if (self.atEnd()): raise Exception("Unexpected '.' without accessed property in identifier.")
            

        return None

    # Helper functions
    def atEnd(self):
        return self.current >= len(self.source)
    
    def checkForChar(self, expectedChar):
        if self.current >= len(self.source) - 1: return False
        return self.source[self.current + 1] == expectedChar


