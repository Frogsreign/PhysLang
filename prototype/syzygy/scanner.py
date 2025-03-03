import interpreter
import token
from tokentype import *

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

    def scan(self):
        
        # Loop through the text and get tokens
        token = None
        while not self.atEnd() and (token := self.getNextToken()) != None:
            if token.type != IGNORE: self.tokens.append(token)
            print(token.toString())

        # End with EOF
        self.tokens.append(token(EOF, None, self.line))

    # Interface for token scanning
    def getNextToken(self):
        token = None

        token = getSingleCharacterToken(self)
        if token == None: token = getComparisonToken()
        if token == None: token = getStringToken()
        if token == None: token = getNumericToken()
        if token == None: token = getReservedToken()
        if token == None: 
            character = self.source[self.current]
            raise Exception("Unexpected character {character} at position {self.current}.")

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
        elif nextChar == ';': type = SEMICOLON
        elif nextChar == '&': type = AND
        elif nextChar == '|': type = OR
        elif nextChar == '\n':
            type = IGNORE
            line += 1
        elif nextChar == ' ': type = IGNORE
        elif nextChar == '\t': type = IGNORE
        else: pass

        # Valid token
        if type != UNDEFINED:
            self.current += 1
            return token(type, nextChar, self.line)
        else: return None


    # Helper functions
    def atEnd(self):
        return self.current > len(self.source)

