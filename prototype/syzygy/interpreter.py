# imports
from token import *
from tokentype import *
from statement import *
from expression import *
from parser import *
import numpy as np

# Interpreter class
class Interpreter(object):
    def __init__(self, statements):
      self.statements = statements
      self.dictionary = {}
      self.pointCount = 0

    def run(self):
        for statement in self.statements:
            self.interpretStatement(statement)

    def interpretStatement(self, statement):

        if isinstance(statement, PointStatement): self.interpretPoint(statement)
        # more branches for different types of statments
        else: pass

    def interpretExpression(self, expression):

        if isinstance(expression, CommaExpression): return self.interpretComma(expression)
        elif isinstance(expression, BinaryExpression): return self.interpretBinary(expression)
        elif isinstance(expression, UnaryExpression): return self.interpretUnary(expression)
        elif isinstance(expression, LiteralExpression): return self.interpretLiteral(expression)
        elif isinstance(expression, ParenthesesExpression): return self.interpretParentheses(expression)
        elif isinstance(expression, BracketExpression): return self.interpretBracket(expression)
        else: return None

    # Creates a JSON entry for a singular point statement
    def interpretPoint(self, statement):

        # Interpret the individual params
        pos = self.interpretExpression(statement.pos)
        vel = self.interpretExpression(statement.vel)
        acc = self.interpretExpression(statement.acc)
        m = self.interpretExpression(statement.m)
        e = self.interpretExpression(statement.e)

        # Set up the net force property (this isn't provided by the user but we'll need it for the animation)
        net_force = 0
        if np.shape(pos) != ():
            net_force = np.zeros_like(pos)

        # Create the property dictionary
        properties = {
            "net-force": net_force,
            "pos": pos,
            "mass": m,
            "vel": vel,
            "acc": acc,
            "e_charge": e
        }

        # Create the dictionary for the point
        pointDict = {
            "Name": self.pointCount, 
            "Props": properties
        }

        print(pointDict)

    def interpretComma(self, expression):
        pass

    def interpretBinary(self, expression):
        pass

    def interpretUnary(self, expression):
        pass

    def interpretLiteral(self, expression):
        return expression.literal

    def interpretParentheses(self, expression):
        return self.interpret(expression.expression)

    # Needs to return a numpy array
    def interpretBracket(self, expression):
        pass


    # Helper functions
    # validateOperands -> currently the program throws errors with i.e. 5 + try, since the parser is
    # not built for it. Would need to add something like this if I upgrade the parser.



    

