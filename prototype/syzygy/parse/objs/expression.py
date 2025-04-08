class Expression(object):
    pass

class CommaExpression(Expression):
    def __init__(self, left, right):
        self.left = left
        self.right = right
    
    def toString(self):
        return self.left.toString() + ', ' + self.right.toString()
    
    def toDict(self):
        return [self.left.toDict(), self.right.toDict()]
    
class VariableExpression(Expression):
    def __init__(self, var):
        self.var = var

    def toString(self):
        return self.var.text
    
    def toDict(self):
        return self.var.text

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
    
    def toDict(self):
        return self.value
    
class ParenthesesExpression(Expression):
    def __init__(self, expression):
        self.expression = expression

    def toString(self):
        return f"({self.expression.toString()})"
    
    def toDict(self):
        return self.expression.toDict()

class BracketExpression(Expression):
    def __init__(self, expression):
        self.expression = expression
    
    def toString(self):
        return f"[{self.expression.toString()}]"
    
    def toDict(self):
        return self.expression.toDict()

