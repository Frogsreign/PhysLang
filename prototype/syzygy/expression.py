class Expression(object):
    pass

class CommaExpression(Expression):
    def __init__(self, left, right):
        self.left = left
        self.right = right
    
    def toString(self):
        return self.left.toString() + ', ' + self.right.toString()

class BinaryExpression(Expression):
    def __init__(self, left, operator, right):
        self.left = left
        self.operator = operator
        self.right = right
    
    def toString(self):
        return self.left.toString() + self.operator.type + self.right.toString()

class UnaryExpression(Expression):
    def __init__(self, operator, right):
        self.operator = operator
        self.right = right
    
    def toString(self):
        return self.operator.type + self.right.toString()

class LiteralExpression(Expression):
    def __init__(self, value):
        self.value = value
    
    def toString(self):
        return str(self.value)

class ParenthesesExpression(Expression):
    def __init__(self, expression):
        self.expression = expression

    def toString(self):
        return f"({self.expression.toString()})"

class BracketExpression(Expression):
    def __init__(self, expression):
        self.expression = expression
    
    def toString(self):
        return f"[{self.expression.toString()}]"
