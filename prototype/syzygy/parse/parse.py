
#
# @author Jacob Leider
#
# This module is responsible for parsing an entire script; objects, functions 
# and all.

import copy

from numpy import isin
import lark
from syzygy.parse.funcs import lex
from syzygy.parse.funcs import ast
from syzygy.parse.objs import interpreter
from syzygy.parse.objs import scanner
from syzygy.parse.objs import parser
from syzygy.sim import data_layout


FUNC_GRAMMAR_PATH = "../syntax/function.lark"


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
            exp_tree = lark.Tree("literal", [lark.Token('literal__SIGNED_NUMBER', '0.5')])
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
        print(tree)
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
        # Check for keyword (e.g. `dt` is obviously 1-D)
        if len(tree.children) == 1:
            child = tree.children[0]
            if child.data == "identifier__keyword":
                tree.dimension = 1
                return

        particle_name, prop_name, prop_index = tree.children
        prop_name = prop_name.children[0]
        if prop_index is not None:
            tree.dimension = 1
        else:
            if prop_name not in self.particle_metadata.prop_name_to_idx:
                raise Exception(f"Add \"{prop_name}\" to metadata")
            tree.dimension = self.particle_metadata.prop_size(prop_name)

    def keyword(self, tree):
        tree.dimension = 1


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


class LiteralFlattener(lark.Visitor):
    def literal(self, tree):
        if len(tree.children) == 1:
            child = tree.children[0]
            if isinstance(child, lark.Token):
                tree.children = [child.value]
                

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
        for i in range(dim - 2):
            cp = copy_with_index(prod, i + 1)
            curr.children.append(lark.Tree("add", [cp]))
            curr = curr.children[1]

        cp = copy_with_index(prod, dim - 1)
        curr.children.append(cp)


# For example, if the output of the force is `net-force`, this can create a net 
# force for each coordinate.
class IndexExtractor(lark.Visitor):
    def identifier(self, tree):
        # Check for keyword (e.g. `dt` is obviously 1-D)
        if len(tree.children) == 1:
            child = tree.children[0]
            if child.data == "identifier__keyword":
                tree.dimension = 1
                return

        particle_name, prop_name, prop_index = tree.children
        
        if prop_index is None:
            if self.particle_metadata.prop_size(prop_name.children[0]) > 1:
                tree.children[2] = lark.Tree("identifier__prop_index", [self.extracted_index]) 




func_parser = lark.Lark.open(FUNC_GRAMMAR_PATH, rel_to=__file__, strict=False)


# Factored out in case we change the tree format.
def get_particles(tree: dict):
    return tree["particles"]


def func_expr_to_ast(expr, metadata):
  # lex
  tree = func_parser.parse(expr)

  MergeIds().visit(tree)
  #print(tree.pretty())

  #print("TRANSFORMATION 2: ANNOTATING DIMENSIONS")

  dimension_annotator = DimensionAnnotator()
  dimension_annotator.particle_metadata = metadata
  dimension_annotator.visit(tree)
  #print(tree.pretty())

  #print("TRANSFORMATION 3: EXPANDING NORMS")
  NormToDotConverter().visit(tree)
  #print(tree.pretty())

  #print("TRANSFORMATION 4: EXPANDING DOTS")
  DotExpander().visit_topdown(tree)
  #print(tree.pretty())

  #print("TRANSFORMATION 5: COLLAPSING DOTS")
  DotToScalarConverter().visit_topdown(tree)
  #print(tree.pretty())
  
  #print("TRANSFORMATION 6: FLATTING LEAVES")
  LiteralFlattener().visit(tree)

  

  return tree

def convert_force_to_ast(force, metadata):
    expr = force["func"]
    force_ast = func_expr_to_ast(expr, metadata)
    # Becomes a subtree of the AST
    force["func"] = force_ast


def convert_update_rule_to_ast(update, metadata):
    expr = update["func"]
    print("EXPR:", expr)
    update_ast = func_expr_to_ast(expr, metadata)
    # Becomes a subtree of the AST
    update["func"] = update_ast


def convert_funcs_to_asts(tree: dict):
    particles = get_particles(tree)
    metadata = data_layout.ParticleMetadata(particles)


    new_forces = []
    new_update_rules = []

    for entry in tree["forces"]:
        # Assume > 1
        dim = metadata.prop_size("pos")
        for i in range(dim):
            idx_entry = {"name": str(entry["name"]) + str(i), 
                         "in":entry["in"], 
                         "out": f"A.net-force[{i}]",
                         "func": copy.deepcopy(entry["func"])}

            expr = idx_entry["func"]
            force_ast = func_expr_to_ast(expr, metadata)

            print("TRANSFORMATION 7: ")
            index_extractor = IndexExtractor()
            index_extractor.particle_metadata = metadata
            index_extractor.extracted_index = i
            index_extractor.visit(force_ast)
            idx_entry["func"] = force_ast

            new_forces.append(idx_entry)


        #convert_force_to_ast(entry, metadata)
        print("TRANSFORMATION 7: ")

    tree["forces"] = new_forces

    for entry in tree["update-rules"]:
        dim = metadata.prop_size("pos")
        for i in range(dim):
            idx_entry = {"name": str(entry["name"]) + str(i), 
                         "in":entry["in"], 
                         "out": entry["out"] + f"[{i}]",
                         "func": copy.deepcopy(entry["func"])}

            expr = idx_entry["func"]
            force_ast = func_expr_to_ast(expr, metadata)

            print("TRANSFORMATION 7: ")
            index_extractor = IndexExtractor()
            index_extractor.particle_metadata = metadata
            index_extractor.extracted_index = i
            index_extractor.visit(force_ast)
            idx_entry["func"] = force_ast

            new_update_rules.append(idx_entry)


    tree["update-rules"] = new_update_rules

def build_entire_ast(script):
    scan = scanner.Scanner(script)
    # Lex
    tokens = scan.scan()
    # Parse
    obj_parser = parser.Parser(tokens)
    statements = obj_parser.parse()
    # Convert to AST
    terp = interpreter.Interpreter(statements)
    terp.run()

    unfinished_tree = terp.dictionary

    # Convert functions to subtrees
    convert_funcs_to_asts(unfinished_tree)

    print(unfinished_tree["update-rules"])

    return unfinished_tree
