#
# @author Jacob Leider
#
# BREIF DESCRIPTION ============================================================
#
# This script implements a lexer and parser for syzygy functions (forces, 
# updates).
#
#     * Converts a script into a sequence of tokens
#     * Validates a token sequence
#
# DETAILED DESCRIPTION =========================================================
#
# If you don't know any formal language theory, learn what a PDA is:
#
#     * https://en.wikipedia.org/wiki/Pushdown_automaton
#
# The formal language of acceptable expressions for force/update functions a 
# context free grammar (CFG). There exists a unique pushdown automaton (PDA) 
# that accepts strings in this language. This module attempts to construct 
# this PDA. 
# 
# To simplify things, we actually define generate the character set of the 
# language of functions by tokenizing using regular expressions.
#
# The PDA is defined as follows:
#
#     * Alphabet
#
#         * Property access     (REF)
#         * Lieral              (LIT)
#         * Operand             (OP)
#         * Left Parehtesis     (LPAREN)
#         * Right Parehtesis    (RPAREN)
#         * Terminal Expression (TERM)
#         * Norm                (NORM)
#         * Dot Product         j(DOT)
#         * Comma               (COMMA)
#
#     * State set
#
#         * 0: Requires the next token not to be an operand or RPAREN.
#         * 1: Next token may be an operand or RPAREN, cannot be a LIT or reference
#
#     * Accepting State: State.ACC
#
# Aditional Notes
#
#     * Stack doesn't distinguish between a reference and a literal.
#     * This PDA is possibly incomplete. I didn't use any mathematical
#       software to derive it. Feel free to upgrade this.
#
# ==============================================================================

import os
import copy

from numpy import prod
import lark
import re
import enum

# Extended Backus-Naur Form: 
# Precedence based: ^, *, /, +, -
# Left-associative


FUNC_GRAMMAR_PATH = "../../syntax/function.lark"


func_parser = lark.Lark.open(FUNC_GRAMMAR_PATH, rel_to=__file__, strict=False)

# Concatenate names.
class MergeIds(lark.Visitor):
    def identifier__particle_name(self, tree):
        concat_child = "".join([child for child in tree.children])
        tree.children = [concat_child]

    def identifier__prop_name(self, tree):
        concat_child = "".join([child for child in tree.children])
        tree.children = [concat_child]


# Expand `norm(a)` to `dot(a, a)^0.5`
# VISIT BOTTOM UP (default visit)
class NormToDotConverter(lark.Visitor):
    def norm(self, tree):
        child = tree.children[0]
        if tree.convert_to_abs:
            tree.data = "abs"
        else:
            dot_tree = lark.Tree("dot", [child, child])
            exp_tree = lark.Tree("literal", [1/2])
            tree.data = "pow"
            tree.children = [dot_tree, exp_tree]


# VISIT BOTTOM UP (default visit) 
class DimensionAnnotator(lark.Visitor):
    def literal(self, tree):
        tree.dimension = 1

    def add(self, tree):
        left, right = tree.children
        if left.dimension != right.dimension:
            raise Exception("Invalid expression: cannot add terms with different dimensionality")
        tree.dimension = left.dimension

    def sub(self, tree):
        left, right = tree.children
        if left.dimension != right.dimension:
            raise Exception("Invalid expression: cannot subtract terms with different dimensionality")
        tree.dimension = left.dimension

    def mul(self, tree):
        left, right = tree.children
        if (left.dimension != 1) and (right.dimension != 1):
            raise Exception(f"Invalid expression: cannot multiply two non-scalar terms dim = {left.dimension} and dim = {right.dimension}")

        # Assert left operand is a scalar.
        if (left.dimension != 1) and (right.dimension == 1):
            tree.children = [right, left]

        tree.dimension = right.dimension

    def div(self, tree):
        left, right = tree.children
        if right.dimension != 1:
            raise Exception("Invalid expression: cannot divide by a non-scalar")

        tree.dimension = left.dimension

    def pow(self, tree):
        left, right = tree.children
        if (left.dimension != 1) or (right.dimension != 1):
            raise Exception("Invalid expression: cannot exponentiate a non-scalar factor, or raise a factor to a non-scalar power")
        tree.dimension = 1


    def dot(self, tree):
        left, right = tree.children
        if left.dimension != right.dimension:
            raise Exception("Invalid expression: cannot take an inner product of elements of different dimensionalities.")
        tree.dimension = 1


    def norm(self, tree):
        tree.dimension = 1
        tree.convert_to_abs = (tree.children[0].dimension == 1)
        print("convert to abs? ", tree.convert_to_abs)


    def identifier(self, tree):
        particle_name, prop_name, prop_index = tree.children
        prop_name = prop_name.children[0]
        if prop_index is not None:
            tree.dimension = 1
        else:
            if prop_name not in self.particle_metadata:
                raise Exception(f"Add \"{prop_name}\" to metadata")
            tree.dimension = self.particle_metadata[prop_name]


# VISIT TOPDOWN
class DotExpander(lark.Visitor):

    def dot(self, tree):
      if len(tree.children) != 2:
          print(f"Dot has {len(self.children)} children!!")

      left, right = tree.children

      if isinstance(left, lark.Tree):
        if left.data in ("add", "sub"):
          ll, lr = left.children
          tree.data = left.data
          tree.children = [lark.Tree("dot", [ll, right]), lark.Tree("dot", [lr, right])]
        elif left.data == "mul":
          scalar, vector = left.children
          tree.data = "mul"
          tree.children = [scalar, lark.Tree("dot", [vector, right])]
        elif left.data == "div":
          vector, scalar = left.children
          tree.data = "div"
          tree.children = [lark.Tree("dot", [vector, right]), scalar]

      if isinstance(right, lark.Tree):
        if right.data in ("add", "sub"):
          rl, rr = right.children
          tree.data = right.data
          tree.children = [lark.Tree("dot", [left, rl]), lark.Tree("dot", [left, rr])]
        elif right.data == "mul":
          scalar, vector = right.children
          tree.data = "mul"
          tree.children = [scalar, lark.Tree("dot", [left, vector])]
        elif left.data == "div":
          vector, scalar = right.children
          tree.data = "div"
          tree.children = [lark.Tree("dot", [left, vector]), scalar]


def approve_dot_to_scalar_conversion(tree):
    left, right = tree.children
    if not isinstance(left, lark.Tree):
        return False
    if not isinstance(right, lark.Tree):
        return False
    if left.data not in ("literal", "identifier"):
        return False
    if right.data not in ("literal", "identifier"):
        return False
    return True


def copy_with_index(tree, i):
    cp = copy.deepcopy(tree) # This tree should have 2 terminal children, so deepcopy is acceptable.
    cp.children[0].children[2] = lark.Tree("identifier__prop_index", [i])
    cp.children[1].children[2] = lark.Tree("identifier__prop_index", [i])
    cp.dimension = 1
    return cp


# Only call AFTER `DotExpander`
class DotToScalarConverter(lark.Visitor):
    def dot(self, tree):
        dim = tree.children[0].dimension
        if not approve_dot_to_scalar_conversion(tree):
            raise Exception("Cannot convert dot product to real arithmetic")
        prod = copy_with_index(tree, 0)
        prod.data = "mul"
        # Build out the sum.
        tree.data = "add"
        tree.children = [prod]
        curr = tree
        for i in range(dim - 1):
            cp = copy_with_index(prod, i + 1)
            curr.children.append(lark.Tree("add", [cp]))
            curr = curr.children[1]


          
def try_lex(s: str):
  tree = func_parser.parse(s)

  MergeIds().visit(tree)
  print(tree.pretty())

  print("TRANSFORMATION 2: ANNOTATING DIMENSIONS")

  dimension_annotator = DimensionAnnotator()
  dimension_annotator.particle_metadata = {
          "pos_123_p": 3,
          "pos": 3,
          "vel": 3,
          "acc": 3,
          "mass": 1,
  }

  dimension_annotator.visit(tree)
  print(tree.pretty())

  print("TRANSFORMATION 3: EXPANDING NORMS")
  NormToDotConverter().visit(tree)
  print(tree.pretty())

  print("TRANSFORMATION 4: EXPANDING DOTS")
  DotExpander().visit_topdown(tree)
  print(tree.pretty())

  print("TRANSFORMATION 5: COLLAPSING DOTS")
  DotToScalarConverter().visit_topdown(tree)
  print(tree.pretty())


class Token(enum.Enum):
  REF = enum.auto()
  LIT = enum.auto()
  OP = enum.auto()
  LPAREN = enum.auto()
  RPAREN = enum.auto()
  TERM = enum.auto()
  NORM = enum.auto()
  DOT = enum.auto()
  COMMA = enum.auto()


class StackToken(enum.Enum):
  LPAREN = enum.auto()
  TERM = enum.auto()


class State(enum.Enum):
  ACC = enum.auto()
  REJ = enum.auto()


# Terminal expressions.
RX_REF = re.compile("[AB].([a-z]|-)*(.idx:[0-9]*)?")
RX_LIT = re.compile("([+-]?([0-9]*[.])?[0-9]+(e(-)?[0-9]*)?)|(dt)")
RX_OP = re.compile(r"[\+\-\*\/\^]")
RX_LPAREN = re.compile(r"\(")
RX_RPAREN = re.compile(r"\)")
RX_COMMA = re.compile(",")
RX_NORM = re.compile("norm")
RX_DOT = re.compile("dot")
RX_TERM = re.compile(r"\$")


# State transition table: Maps (state, input character, stack character) triples
# to (next state, pop from stack?, push onto stack) triples.
transitions = {
    (0, Token.LPAREN, StackToken.TERM):    [0, False, StackToken.LPAREN],
    (0, Token.LPAREN, StackToken.LPAREN):  [0, False, StackToken.LPAREN],
    (0, Token.LIT, StackToken.TERM):       [1, False, None],
    (0, Token.REF, StackToken.TERM):       [1, False, None],
    (0, Token.LIT, StackToken.LPAREN):     [1, False, None],
    (0, Token.REF, StackToken.LPAREN):     [1, False, None],
    (1, Token.RPAREN, StackToken.LPAREN):  [1, True, None],
    (1, Token.OP, StackToken.TERM):        [0, False, None],
    (1, Token.OP, StackToken.LPAREN):      [0, False, None],
    (1, Token.TERM, StackToken.TERM):      [State.ACC, False, None],
    # Norm
    (0, Token.NORM, StackToken.LPAREN):     [2, False, None],
    (2, Token.LPAREN, StackToken.LPAREN):     [3, False, None],
    (3, Token.REF, StackToken.LPAREN):     [4, False, None],
    (4, Token.RPAREN, StackToken.LPAREN):     [1, False, None],
    (0, Token.NORM, StackToken.TERM):     [2, False, None],
    (2, Token.LPAREN, StackToken.TERM):     [3, False, None],
    (3, Token.REF, StackToken.TERM):     [4, False, None],
    (4, Token.RPAREN, StackToken.TERM):     [1, False, None],
    # Dot
    (0, Token.DOT, StackToken.LPAREN):     [5, False, None],
    (5, Token.LPAREN, StackToken.LPAREN):     [6, False, None],
    (6, Token.REF, StackToken.LPAREN):     [7, False, None],
    (7, Token.COMMA, StackToken.LPAREN):     [8, False, None],
    (8, Token.REF, StackToken.LPAREN):     [9, False, None],
    (9, Token.RPAREN, StackToken.LPAREN):     [1, False, None],
    (0, Token.DOT, StackToken.TERM):     [5, False, None],
    (5, Token.LPAREN, StackToken.TERM):     [6, False, None],
    (6, Token.REF, StackToken.TERM):     [7, False, None],
    (7, Token.COMMA, StackToken.TERM):     [8, False, None],
    (8, Token.REF, StackToken.TERM):     [9, False, None],
    (9, Token.RPAREN, StackToken.TERM):     [1, False, None]
}


# Only necessary since we use regexs as terminal expressions. We could
# technically avoid this by adding hundreds of transitions to the transition
# table above, but using regular expressions as literal tokens is more
# practical.
def get_token_id(tok):
  if   re.fullmatch(RX_REF, tok):     return Token.REF
  elif re.fullmatch(RX_LIT, tok):     return Token.LIT
  elif re.fullmatch(RX_OP, tok):      return Token.OP
  elif re.fullmatch(RX_LPAREN, tok):  return Token.LPAREN
  elif re.fullmatch(RX_RPAREN, tok):  return Token.RPAREN
  elif re.fullmatch(RX_COMMA, tok):   return Token.COMMA
  elif re.fullmatch(RX_NORM, tok):    return Token.NORM
  elif re.fullmatch(RX_DOT, tok):     return Token.DOT
  elif re.fullmatch(RX_TERM, tok):    return Token.TERM
  else: raise Exception(f"Invalid token {tok}")


def match_and_step(s: str) -> tuple:
  """
  Return the first token and the remaining string.
  """
  if re.match(RX_REF, s):       m = RX_REF.match(s)
  elif re.match(RX_LIT, s):     m = RX_LIT.match(s)
  elif re.match(RX_OP, s):      m = RX_OP.match(s)
  elif re.match(RX_LPAREN, s):  m = RX_LPAREN.match(s)
  elif re.match(RX_RPAREN, s):  m = RX_RPAREN.match(s)
  elif re.match(RX_COMMA, s):   m = RX_COMMA.match(s)
  elif re.match(RX_NORM, s):    m = RX_NORM.match(s)
  elif re.match(RX_DOT, s):     m = RX_DOT.match(s)
  elif re.match(RX_TERM, s):    m = RX_TERM.match(s)
  else: raise Exception(f"Invalid token {s}")
  return m.group(0), s[m.end(0):].lstrip()


def lex(s: str) -> list:
  """
  Convert a string to a token sequence.
  """
  try_lex(s)
  tokens = []
  while s:
    token, s = match_and_step(s)
    tokens.append(token)
  return tokens


def transition(state, transitions, tok, stack):
  """
  PDA State transition subroutine.
  """
  # Handle stack errors.
  if len(stack) == 0: raise Exception("Stack underflow")
  # Handle transition.
  if (state, tok, stack[-1]) not in transitions: return State.REJ
  print(transitions[(state, tok, stack[-1])])
  state, pop, push = transitions[(state, tok, stack[-1])]
  if pop: stack.pop()
  if push is not None: stack.append(push)
  return state


terminal_states = [State.ACC, State.REJ]

def parse(tokens: list) -> bool:
  """
  PDA implementation: A simple loop that
      1. Checks for termination
      2. Executes a state transition
      3. (Optinally) Calls an input function
  """
  stack = [StackToken.TERM]
  state = 0
  for tok in tokens + ['$']:
    # Termination check.
    if state in terminal_states: break
    # Transition.
    tok_id = get_token_id(tok)
    print(state, tok_id, stack[-1])
    state = transition(state, transitions, tok_id, stack)
  # print("parsed... Final state: ", state)
  return state == State.ACC
