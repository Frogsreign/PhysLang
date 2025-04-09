#
# @author Jacob Leider
#
# DESCRIPTION ==================================================================
#
# This script implements a parser for algebraic expressions. The parser...
#     * Validates expressions.
#     * (Optionally) Calls a function at each state the PDA transitions into.
#
# DETAILED DESCRIPTION =========================================================
#
# The set of acceptable expressions for force/update functions is not a regular
# language, it is at best a CFG. The following is a PDA that accepts strings in
# the language of force/update function definitions.
#
# If you don't know any formal language theory, learn what a PDA is:
#     * https://en.wikipedia.org/wiki/Pushdown_automaton
#
# Defning the CFG
#     * Alphabet
#         * [a-z], [0-9], (), +-*/^, "."
#     * Terminal Expressions
#         * Property access (REF)
#         * Lieral (LIT)
#         * Operand (OP)
#     * Production rules
#         * A -> A OP A
#         * A -> (A)
#         * A -> REF
#         * A -> LIT
#     * States set
#         * 0: Requires the next token not to be an operand or RPAREN.
#         * 1: Next token may be an operand or RPAREN, cannot be a LIT or REF
#     * Aditional Notes
#         * Stack doesn't distinguish between a reference and a literal.
#         * This PDA is possibly incomplete. I didn't use any mathematical
#           software to derive it.
#
# ==============================================================================

import re
import enum


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
    (1, Token.TERM, StackToken.TERM):      [State.ACC, False, None]
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
  print(f"lexing {s}")
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
    state = transition(state, transitions, tok_id, stack)
  # print("parsed... Final state: ", state)
  return state == State.ACC
