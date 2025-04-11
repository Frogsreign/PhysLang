# 
# @author Jacob Leider
#
# Order of events
# ---------------
# 1. Lex
# 2. Parse
# 3. Build preliminary AST
# 4.
#   (a) Convert norms to radicals of dot products
#   (b) Expand dot products (using linearity rules)
#   (c) Reduce dot products to 1-D algebra


# Helper-helper: Checks whether the current operator has lower precedence than 
# the token of least precedence so far seen, and potentially updates it.
def update_min_precedence(tokens, cur_index, least_precedence_seen_index, cur_precedence, 
                          least_precedence_seen, precedence, right_associative):
  if (cur_precedence < least_precedence_seen or
      cur_precedence == least_precedence_seen and
      tokens[cur_index] not in right_associative):
    return cur_index, precedence[tokens[cur_index]]
  else:
    return least_precedence_seen_index, least_precedence_seen 


# Helper: Finds the index of the operator with the least precedence
# (respecting associativity)
def min_precedence(tokens, precedence, right_associative):
  depth = 0
  least_precedence_seen_index = -1
  least_precedence_seen = max(precedence.values())
  for i, token in enumerate(tokens):
    if token == '(':
      depth += 1
    elif token == ')':
      depth -= 1
    elif depth == 0 and token in precedence:
      # Only update if we aren't inside any parentheses.
      least_precedence_seen_index, least_precedence_seen = update_min_precedence(
          tokens, i, least_precedence_seen_index, precedence[token], 
          least_precedence_seen, precedence, right_associative)
    elif token in ("norm", "dot"):
      continue
  return least_precedence_seen_index 


# NOTE: Leave variables in their own lists in case we find it helpful to provide
# extra info to the compiler about variables.
def tokens_to_ast(tokens):
  """
  Converts a validated expression into an AST.

  Recursively builds the AST. 

  Example: "3 + 5 * 2 - 8 / 4" becomes `[-, [+, 3, [*, 5, 2]], [/, 8, 4]]`
  """
  precedence = {'+': 1, '-': 1, '*': 2, '/': 2, '^': 3}
  right_associative = {'^'}

  tree = []
  stack = [(tokens, tree)]

  while len(stack) > 0:
    tokens, root = stack.pop()
    if len(tokens) == 1:
      # Leaf: Requires no further processing
      root.append(tokens[0])
    else:
      min_precidence_index = min_precedence(tokens, precedence,
                                            right_associative)
      if min_precidence_index == -1:
        # Terminal expression or dot/norm
        if tokens[0] == 'norm':
          root.extend(['norm', []])
          stack.append((tokens[2:-1], root[1]))
        elif tokens[0] == 'dot':
          comma_index = tokens.find(",")
          if comma_index == -1:
              raise Exception("Invalid dot expression: ", tokens)
          root.extend(['dot', [], []])
          stack.append((tokens[2:comma_index], root[1]))
          stack.append((tokens[comma_index+1:-1], root[2]))
        else:
          stack.append((tokens[1:-1], root))
      else:
        # Binary expression
        root.extend([tokens[min_precidence_index], [], []])
        stack.append((tokens[:min_precidence_index], root[1]))
        stack.append((tokens[min_precidence_index + 1:], root[2]))

  return tree


def expand_dot_sum_left(sub, stack):
  left = sub[1].copy()
  right = sub[2].copy()
  left_left = left[1]
  left_right = left[2]

  sub[0] = left[0]
  sub[1] = ['dot', left_left, right]
  sub[2] = ['dot', left_right, right]


def expand_dot_sum_right(sub, stack):
  left = sub[1].copy()
  right = sub[2].copy()
  right_left = right[1]
  right_right = right[2]

  sub[0] = right[0]
  sub[1] = ['dot', left, right_left]
  sub[2] = ['dot', left, right_right]


# Expand [dot, [*, c, a], b] -> [*, c, [dot, a, b]]
def expand_dot_scalar_prod_left(sub, stack):
  left = sub[1].copy()
  right = sub[2].copy()
  left_scalar = left[1]
  left_vector = left[2]

  sub[0] = left[0]
  sub[1] = left_scalar
  sub[2] = ['dot', left_vector, right]

# Expand [dot, a, [*, c, b]] -> [*, c, [dot, a, b]]
def expand_dot_scalar_prod_right(sub, stack):
  left = sub[1].copy()
  right = sub[2].copy()
  right_scalar = right[1]
  right_vector = right[2]

  sub[0] = right[0]
  sub[1] = ['dot', left, right_vector]
  sub[2] = right_scalar


def expand_dot(sub, stack):
  if len(sub[1]) == 3: # if left can be expanded
    child = sub[1]
    if child[0] == '*':           expand_dot_scalar_prod_left(sub, stack)
    elif child[0] == '/':         raise NotImplementedError()
    elif child[0] in ('+', '-'):  expand_dot_sum_left(sub, stack)
  elif len(sub[2]) == 3:  # if right can be expanded
    child = sub[2]
    if child[0] == '*':           expand_dot_scalar_prod_right(sub, stack)
    elif child[0] == '/':         raise NotImplementedError()
    elif child[0] in ('+', '-'):  expand_dot_sum_right(sub, stack)
  elif (len(sub[1]) != 1) or (len(sub[2]) != 1):
    raise ValueError("Invalid dot expression")


def expand_norm(sub, stack):
  child = sub[1]
  sub[0] = "^"
  sub[1] = ['dot', child.copy(), child.copy()]
  sub.append([0.5])


def expand_dots(tree):
  stack = [tree]
  while len(stack) > 0:
    sub = stack.pop()
    if sub[0] == 'dot': 
      expand_dot(sub, stack)
    elif sub[0] == 'norm': 
      expand_norm(sub, stack)
    stack.extend(sub[1:])
  return tree


def collapse_dot(sub, a, b, n):
  sub.clear()
  for i in range(n - 1):
    sub.extend(["+", ["*", [f"{a}.index:{i}"], [f"{b}.index:{i}"]], []])
    sub = sub[2]
  sub.extend(["*", [f"{a}.index:{n - 1}"], [f"{b}.index:{n - 1}"]])


# Validate before reducing to lower order logic.
def maybe_collapse_dot(sub, particle_metadata):
    prop_a, prop_b = sub[1][0], sub[2][0]
    # Dimensionality check.
    _, a_name = prop_a.split(".")
    _, b_name = prop_b.split(".")
    if particle_metadata.prop_size(a_name) != particle_metadata.prop_size(b_name):
        raise ValueError("encountered a dot product between vectors of different dimensions")
    # Checks passed.
    collapse_dot(sub, prop_a, prop_b, particle_metadata.prop_size(a_name))


def collapse_dots(tree, particle_metadata):
  stack = [tree]
  while len(stack) > 0:
    sub = stack.pop()
    if sub[0] == 'dot':
        maybe_collapse_dot(sub, particle_metadata)
    else:
      stack.extend(sub[1:])
  return tree
