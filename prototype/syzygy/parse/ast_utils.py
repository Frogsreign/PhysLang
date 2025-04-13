#!/usr/bin/python3
#
# @author Jacob Leider
#
#
# Utilities for AST Shaping. Each class performs a round of shaping.
# 

import copy
import lark



# Round 1 (VISIT BOTTOM UP)
#
# Concatenate children of variable names (said children are either words, numbers or underscores).
class IdentifierNameFlattener(lark.Visitor):
    def particle_name(self, tree):
        concat_child = "".join([child for child in tree.children])
        tree.children = [concat_child]

    def property_name(self, tree):
        concat_child = "".join([child for child in tree.children])
        tree.children = [concat_child]


# Round 2 (VISIT BOTTOM UP)
#
# Expand `norm(a)` to `dot(a, a)^0.5`, `or abs(a)`
class NormToDotConverter(lark.Visitor):
    def norm(self, tree):
        child = tree.children[0]
        if tree.convert_to_abs:
            tree.data = "abs"
        else:
            dot_tree = lark.Tree("dot", [child, child])
            exp_tree = lark.Tree("literal", [lark.Token('literal__SIGNED_NUMBER', '0.5')])
            tree.data = "pow"
            tree.children = [dot_tree, exp_tree]


# Round 3 (VISIT BOTTOM UP)
#
# Assigns a `dimension` attribute to each subtree.
class DimensionAnnotator(lark.Visitor):

    def __init__(self, particle_metadata):
        self.particle_metadata = particle_metadata

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
        #print(tree)
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
        # TODO: Test the `abs` stuff
        tree.convert_to_abs = (tree.children[0].dimension == 1)


    def identifier(self, tree):
        # Check for keyword (e.g. `dt` is obviously 1-D)
        if len(tree.children) == 1:
            child = tree.children[0]
            tree.dimension = child.dimension
        else:
            raise Exception("IDENTIFIER SHOULD HAVE ONE CHILD. CURRENT IDENTIFIER:", tree)


    def particle_property_access(self, tree):
        _, prop_name, prop_index = tree.children
        prop_name = prop_name.children[0]
        if prop_index is not None:
            tree.dimension = 1
        else:
            if prop_name not in self.particle_metadata.prop_name_to_idx:
                raise Exception(f"Add \"{prop_name}\" to metadata")
            tree.dimension = self.particle_metadata.prop_size(prop_name)

            if tree.dimension == 1:
                tree.children[2] = lark.Tree("property_index", [0]) # Give an explicit index of zero if the property is 1-D..


    def keyword(self, tree):
        # TODO: This depends.
        tree.dimension = 1


# Round 4 (VISIT TOP DOWN)
#
# Expand the dot products by linearity (e.g. <x + y, z> becomes 
# <x, z> + <y, z>, and <a * x, y> becomes a * <x, y>)
class DotExpander(lark.Visitor):

    def dot(self, tree):
      if len(tree.children) != 2:
          raise Exception("`dot` must have two children. Encountered `dot` with {len(tree.children)} chidren")

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



# Round 5 (VISIT TOP DOWN)
#
# Only call AFTER `DotExpander`
class DotToScalarConverter(lark.Visitor):
    def _approve_dot_to_scalar_conversion(self, tree):
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


    def _copy_with_index(self, tree, i):
        cp = copy.deepcopy(tree) # This tree should have 2 terminal children, so deepcopy is acceptable.
        cp.children[0].children[0].children[2] = lark.Tree("property_index", [i])
        cp.children[1].children[0].children[2] = lark.Tree("property_index", [i])
        cp.dimension = 1
        return cp

    def dot(self, tree):
        dim = tree.children[0].dimension
        if not self._approve_dot_to_scalar_conversion(tree):
            raise Exception("Cannot convert dot product to real arithmetic")
        prod = self._copy_with_index(tree, 0)
        prod.data = "mul"
        # Build out the sum.
        tree.data = "add"
        tree.children = [prod]
        curr = tree
        for i in range(dim - 2):
            cp = self._copy_with_index(prod, i + 1)
            curr.children.append(lark.Tree("add", [cp]))
            curr = curr.children[1]

        cp = self._copy_with_index(prod, dim - 1)
        curr.children.append(cp)


# Round 6 (VISIT BOTTOM UP)
#
# Inlines keywords such as `dt` and literals 
# (e.g [literal, [[number, [5]]]] becomes [literal, [5]])
class LiteralAndKeywordFlattener(lark.Visitor):
    def literal(self, tree):
        if len(tree.children) == 1:
            child = tree.children[0]
            if isinstance(child, lark.Token):
                tree.children = [child.value]

    def keyword(self, tree):
        if len(tree.children) == 1:
            child = tree.children[0]
            if isinstance(child, lark.Token):
                tree.children = [child.value]


# Round 7
#
# After rounds 1-6 are complete, `CoordinateBuilder` converts any non-scalar 
# inputs to scalars by assigning them an index (specified in the constructor).
#
# For example, if the output of the force is `net-force`, this can create a net 
# force for each coordinate.
#
# TODO: Prove that this works and explain it. 
#   * Outline: vectors may only be added and multiplied by scalars, so 
#              coordinates are preserved.
class CoordinateBuilder(lark.Visitor):
    def __init__(self, particle_metadata, extracted_index):
        self.particle_metadata = particle_metadata
        self.extracted_index = extracted_index

    def particle_property_access(self, tree):
        # Check for keyword (e.g. `dt` is obviously 1-D)
        if len(tree.children) == 1:
            child = tree.children[0]
            if child.data == "identifier__keyword":
                tree.dimension = 1
                return

        _, prop_name, prop_index = tree.children
        
        if prop_index is None:
            if self.particle_metadata.prop_size(prop_name.children[0]) > 1:
                tree.children[2] = lark.Tree("identifier__prop_index", 
                                             [self.extracted_index]) 
