# A place to conveniently store all the types of tokens for universal reference
# Value types
NUMBER, STRING = 'NUMBER', 'STRING' 

# Structure symbols
LEFT_PAREN, RIGHT_PAREN, LEFT_BRACK, RIGHT_BRACK = '(', ')', '[', ']'
LEFT_BRACE, RIGHT_BRACE = '{', '}'
COMMA, SEMICOLON, EOL, EOF = ',', ';', 'EOL', 'EOF'

# Math symbols
PLUS, MINUS, DIVIDE, MULTIPLY, EXPONENT = '+', '-', '/', '*', '^'

# Logic symbols
AND, OR = 'AND', 'OR'
NOT, GREATER_THAN, LESS_THAN = '!', '>', '<'
NOT_EQUAL, GREATER_OR_EQUAL, LESS_OR_EQUAL = '!=', '>=', '<='
ASSIGN = '='
EQUIVALENT = '=='
TRUE, FALSE, NONE = 'TRUE', 'FALSE', 'NONE'

# Reserved words
POINT, SOLID, FORCE, UPDATE, POS = 'POINT', 'SOLID', 'FORCE', 'UPDATE', 'POS'
VEL, ACC, M, E = 'VEL', 'ACC', 'M', 'E'
INPUT, OUTPUT, FUNC = 'INPUT', 'OUTPUT', 'FUNC'
VAR, IDENTIFIER, NAME = 'VAR', 'IDENTIFIER', 'NAME'
PERIOD = "PERIOD"

# Ignore
IGNORE = 'IGNORE'

# Undefined (default)
UNDEFINED = 'UNDEFINED'