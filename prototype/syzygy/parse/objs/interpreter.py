# imports
from syzygy.parse.objs.tokens import *
from syzygy.parse.objs.tokentype import *
from syzygy.parse.objs.statement import *
from syzygy.parse.objs.expression import *
from syzygy.parse.objs.parser import *
import numpy as np

# Interpreter class
class Interpreter(object):
    def __init__(self, statements):
      self.statements = statements
      self.dictionary = {"group-id": 0, "forces": [], "update-rules": [], "particles": []} # What will be output to the json file for animation
      self.pointCount = 0
      self.forceCount = 0
      self.updateCount = 0

    def run(self):
        for statement in self.statements:
            self.interpretStatement(statement)

    def interpretStatement(self, statement):

        if isinstance(statement, PointStatement): self.interpretPoint(statement)
        elif isinstance(statement, ForceStatement): self.interpretForce(statement)
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

        if pos is None: pos = [0, 0, 0]
        if vel is None: vel = [0, 0, 0]
        if acc is None: acc = [0, 0, 0]
        if m is None: m = np.inf
        if e is None: e = 0

        # Set up the net force property (this isn't provided by the user but we'll need it for the animation)
        net_force = 0
        if np.shape(pos) != ():
            net_force = list(np.zeros_like(pos))

        if np.shape(pos) != np.shape(vel) or np.shape(pos) != np.shape(acc) or np.shape(vel) != np.shape(acc):
            raise Exception("Dimensions of position, velocity, and acceleration must be the same.")

        # Create the property dictionary
        properties = {
            "net-force": net_force,
            "pos": pos,
            "mass": "Infinity" if m == np.inf else m,
            "vel": vel,
            "acc": acc,
            "e_charge": e
        }

        # Create the dictionary for the point
        pointDict = {
            "name": self.pointCount, 
            "props": properties
        }

        self.dictionary["particles"].append(pointDict)
        self.pointCount += 1
        print(pointDict)

    def interpretForce(self, statement):

        # Create a json dictionary to pass on to the force function handler
        force = {
            "name": self.forceCount,
            "in": statement.input.toDict(),
            "force": statement.func.toString()        
        }
        
        self.dictionary["forces"].append(force)
        print(force)
        self.forceCount += 1

    def interpretUpdate(self, statement):

        update = {
            "name": self.updateCount,
        }

        self.dictionary["update-rules"].append(update)
        print(update)
        self.updateCount += 1

    def interpretBinary(self, expression):
        left = self.interpretExpression(expression.left)
        right = self.interpretExpression(expression.right)
        operator = expression.operator.type

        if operator == PLUS: return left + right
        elif operator == MINUS: return left - right
        elif operator == MULTIPLY: return left * right
        elif operator == DIVIDE: return left / right
        elif operator == EXPONENT: return left**right

        return None

    def interpretUnary(self, expression):
        right = self.interpretExpression(expression.right)
        operator = expression.operator.type

        return -float(right)

    def interpretLiteral(self, expression):
        return expression.value

    def interpretParentheses(self, expression):
        return self.interpretExpression(expression.expression)

    # These two should always appear together and the result needs to return a numpy array
    def interpretComma(self, expression):
        return list(np.insert(self.interpretExpression(expression.right), 0, self.interpretExpression(expression.left)))

    def interpretBracket(self, expression):
        return self.interpretExpression(expression.expression)


    # Helper functions
    # validateOperands -> currently the program throws errors with i.e. 5 + try, since the parser is
    # not built for it. Would need to add something like this if I upgrade the parser.



    

