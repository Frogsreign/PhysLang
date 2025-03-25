# Order of events:
# 1. Lex
# 2. Parse
# 3. Build AST
# 4. Expand dot products, norms
#     * Converts norms to dot products
# 5. Collapse dot products

precedence = {'+': 1, '-': 1, '*': 2, '/': 2, '^': 3}
right_associative = {'^'}


def find_comma(tokens):
  for i in range(len(tokens)):
    if tokens[i] == ',':
      return i
  return -1


def update_min_precedence(tokens, cur_index, min_index, cur_precedence, min_precedence):
  if (cur_precedence < min_precedence or
      cur_precedence == min_precedence and
      tokens[cur_index] not in right_associative):
    return cur_index, precedence[tokens[cur_index]]
  else:
    return min_index, min_precedence


# Helper: Finds the index of the operator with the lowest precedence
# (respecting associativity)
def min_precedence(tokens):
  depth = 0
  min_index = -1
  min_precedence = max(precedence.values())
  for i, token in enumerate(tokens):
    if token == '(':
      depth += 1
    elif token == ')':
      depth -= 1
    elif depth == 0 and token in precedence:
      min_index, min_precedence = update_min_precedence(
          tokens, i, min_index, precedence[token], min_precedence)
    elif token in ("norm", "dot"):
      continue
  return min_index


# NOTE: Leave variables in their own lists in case we find it helpful to provide
# extra info to the compiler about variables.
def tokens_to_ast(tokens):
  """
  Inserts pairs of parentheses into a token sequence to explicitly specify an
  order of operations.

  Example: "3 + 5 * 2 - 8 / 4" becomes `[-, [+, 3, [*, 5, 2]], [/, 8, 4]]`
  """
  tree = []
  stack = [(tokens, tree)]

  while len(stack) > 0:
    tokens, root = stack.pop()
    if len(tokens) == 1:
      root.append(tokens[0])
    else:
      min_precidence_index = min_precedence(tokens)
      if min_precidence_index == -1:
        if tokens[0] == 'norm':
          root.extend(['norm', []])
          stack.append((tokens[2:-1], root[1]))
        elif tokens[0] == 'dot':
          comma_idx = find_comma(tokens)
          if comma_idx == -1:
            print(tokens)
            raise Exception("Invalid dot expression")
          root.extend(['dot', [], []])
          stack.append((tokens[2:comma_idx], root[1]))
          stack.append((tokens[comma_idx+1:-1], root[2]))
        else:
          stack.append((tokens[1:-1], root))
      else:
        root.extend([tokens[min_precidence_index], [], []])
        stack.append((tokens[:min_precidence_index], root[1]))
        stack.append((tokens[min_precidence_index + 1:], root[2]))

  return tree


def expand_dot_sum_left(sub, stack):
  left = sub[1]
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


def expand_dot_scalar_prod_left(sub, stack):
  left = sub[1].copy()
  right = sub[2].copy()
  left_scalar = left[1]
  left_vector = left[2]

  sub[0] = left[0]
  sub[1] = left_scalar
  sub[2] = ['dot', left_vector, right]


def expand_dot_scalar_prod_right(sub, stack):
  left = sub[1].copy()
  right = sub[2].copy()
  right_scalar = right[1]
  right_vector = right[2]

  sub[0] = right[0]
  sub[1] = ['dot', left, right_vector]
  sub[2] = right_scalar


def expand_dot(sub, stack):
  if len(sub[1]) == 3:
    child = sub[1]
    if child[0] == '*':           expand_dot_scalar_prod_left(sub, stack)
    elif child[0] == '/':         raise NotImplementedError()
    elif child[0] in ('+', '-'):  expand_dot_sum_left(sub, stack)
  elif len(sub[2]) == 3:
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
    sub.extend(["+", ["*", [f"{a}.idx:{i}"], [f"{b}.idx:{i}"]], []])
    sub = sub[2]
  sub.extend(["*", [f"{a}.idx:{n - 1}"], [f"{b}.idx:{n - 1}"]])


def collapse_dots(tree):
  stack = [tree]
  while len(stack) > 0:
    sub = stack.pop()
    if sub[0] == 'dot':
      prop_a, prop_b = sub[1][0], sub[2][0]
      collapse_dot(sub, prop_a, prop_b, 3)
    else:
      stack.extend(sub[1:])
  return tree

