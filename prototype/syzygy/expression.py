class Expression(object):
    pass

class BinaryExpression(Expression):
    def __init__(self, left, operator, right):
        self.left = left
        self.operator = operator
        self.right = right
    
    def toString(self):
        return self.left.toString() + self.operator.toString() + self.right.toString()

class UnaryExpression(Expression):
    def __init__(self, operator, right):
        self.operator = operator
        self.right = right
    
    def toString(self):
        return self.operator.toString() + self.right.toString()

class LiteralExpression(Expression):
    def __init__(self, value):
        self.value = value
    
    def toString(self):
        return self.value

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
