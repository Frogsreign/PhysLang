#!/usr/bin/python3
#
# @author Jacob Leider
#
#
# Utilities for AST Shaping. Each class performs a round of shaping.
# 

import copy
import lark


keyword_dimensions = {
        "dt": 1
}


# EVERYTHING BECOMES A VECTOR.
@lark.visitors.v_args(tree=True)
class LinearAlgebraChecker2(lark.Transformer):
    def __init__(self, metadata, visit_tokens: bool = True) -> None:
        super().__init__(visit_tokens=True)
        self.particle_metadata = metadata

    
    def start(self, tree):
        # TODO: Test this for a function defined on one coordinate
        # Return the base vector_expr
        if len(tree.children) == 1:
            child = tree.children[0]
            if child.data == 'vector_expr':
                return child
            else:
                raise Exception("Expected one `vector_expr` child.")
        else:
            raise Exception("Expected one `vector_expr` child.")


    def vector_expr(self, tree):
        # Inline any children that are `vector_expr`s
        for i, child in enumerate(tree.children):
            if isinstance(child, lark.Tree):
                if child.data == "vector_expr":
                    if len(child.children) > 1:
                        raise Exception("Vectors can't have non-scalar coordinates")
                    else:
                        child = child.children[0]
            tree.children[i] = child
        return tree

    
    def particle_property_access(self, tree):
        particle_name, property_name, property_index = tree.children
        if property_index is None:
            dim = self.particle_metadata.prop_size(property_name.value)
            return lark.Tree(lark.Token('RULE', 'vector_expr'), 
                             [lark.Tree(
                                 lark.Token('RULE', 'particle_property_access'), 
                                 [particle_name, property_name, lark.Token('NUMBER', i)]) 
                              for i in range(dim)])


    def keyword(self, tree):
        # TODO: If we add more keywords, this will need to be updated.
        return lark.Tree(lark.Token('RULE', 'vector_expr'), 
                         [tree])


    def literal(self, tree):
        return lark.Tree(lark.Token('RULE', 'vector_expr'), [tree])


    def identifier(self, tree):
        return tree.children[0]

    
    def add(self, tree):
        # Expects two vector_expr children
        left, right = tree.children
        if (left.data != "vector_expr") or (right.data != "vector_expr"):
            raise Exception("Expected vector_expr operands")

        return lark.Tree(lark.Token('RULE', 'vector_expr'),
                         [lark.Tree(lark.Token('RULE', 'add'), 
                                    [ll, rr]) 
                         for ll, rr in zip(left.children, right.children)])


    def sub(self, tree):
        # Expects two vector_expr children
        left, right = tree.children

        if (left.data != "vector_expr") or (right.data != "vector_expr"):
            raise Exception("Expected vector_expr operands")

        if len(left.children) != len(right.children):
            raise Exception("Dimension mismatch.")

        return lark.Tree(lark.Token('RULE', 'vector_expr'),
                         [lark.Tree(lark.Token('RULE', 'sub'), 
                                    [ll, rr]) 
                          for ll, rr in zip(left.children, right.children)])


    def norm(self, tree):
        # Expects one vector_expr child
        if len(tree.children) != 1:
            raise Exception("Expected a single `vector_expr` child")

        child = tree.children[0]
        tree.children = [child, child]
        dotted = self.dot(tree) # Dot
        prod = dotted.children[0] # Extract expression from vector_expr wrapper

        return lark.Tree(lark.Token('RULE', 'vector_expr'), 
                         [lark.Tree(lark.Token('RULE', 'pow'), 
                                    [prod, lark.Tree(lark.Token('RULE', 'literal'), 
                                                     [lark.Token('SIGNED_NUMBER', 0.5)])])]) # take it's square root


    def dot(self, tree):
        # Expects two vector_expr children
        left, right = tree.children
        dim = len(tree.children[0].children)
        prod = lark.Tree("add", [])

        curr = prod
        summand = lark.Tree("mul", [left.children[0], right.children[0]])
        curr.children.append(summand)
        for i in range(1, dim - 1):
            curr.children.append(lark.Tree("add", []))
            curr = curr.children[1]
            summand = lark.Tree("mul", [left.children[i], right.children[i]])
            curr.children.append(summand)

        curr.children.append(lark.Tree("mul", [left.children[-1], right.children[-1]]))

        return lark.Tree(lark.Token('RULE', 'vector_expr'), [prod])


    def mul(self, tree):
        # Expects two vector_expr children
        left, right = tree.children
        #print(80 * '-')
        #for child in left.children: print(child.data)
        #print(80 * '-')
        #for child in right.children: print(child.data)
        #print(80 * '-')

        if (left.data != "vector_expr") or (right.data != "vector_expr"):
            raise Exception("Expected vector_expr operands")

        # Adapt for scalar multiplication. Scale a unit and take the pointwise product.
        if len(left.children) == 1:
            child = left.children[0]
            #if child.data == "vector_expr": raise Exception("Found it.")
            left.children = [copy.deepcopy(child) for _ in range(len(right.children))]
        if len(right.children) == 1:
            child = right.children[0]
            #if child.data == "vector_expr": raise Exception("Found it.")
            right.children = [copy.deepcopy(child) for _ in range(len(left.children))]

        # Dimension check
        if len(left.children) != len(right.children):
            raise Exception("Dimension mismatch.")

        return lark.Tree(lark.Token('RULE', 'vector_expr'),
                         [lark.Tree(lark.Token('RULE', 'mul'), [ll, rr]) for ll, rr in zip(left.children, right.children)])

    
    def div(self, tree):
        # Expects two vector_expr children
        left, right = tree.children
        if (left.data != "vector_expr") or (right.data != "vector_expr"):
            raise Exception("Expected vector_expr operands")

        # Adapt for scalar division. Scale a unit and divide pointwise. Scalar 
        # must appear on the right.
        if len(right.children) == 1:
            child = right.children[0]
            right.children = [copy.deepcopy(child) for _ in range(len(left.children))]

        # Dimension check
        if len(left.children) != len(right.children):
            raise Exception("Dimension mismatch.")

        return lark.Tree(lark.Token('RULE', 'vector_expr'),
                         [lark.Tree(lark.Token('RULE', 'div'), [ll, rr]) for ll, rr in zip(left.children, right.children)])


    def pow(self, tree):
        # Expects two vector_expr children
        left, right = tree.children
        if (left.data != "vector_expr") or (right.data != "vector_expr"):
            raise Exception("Expected vector_expr operands")

        # Adapt for scalar division. Scale a unit and divide pointwise. Scalar 
        # must appear on the right.
        if len(left.children) != 1:
            raise Exception("Only scalars can be exponentiated")

        # Dimension check
        if len(left.children) != len(right.children):
            raise Exception("Dimension mismatch.")

        return lark.Tree(lark.Token('RULE', 'vector_expr'),
                         [lark.Tree(lark.Token('RULE', 'pow'), 
                                    [ll, rr]) for ll, rr in zip(left.children, right.children)])


    def abs(self, tree):
        # Expects one vector_expr child.
        if len(tree.children) != 1:
            raise Exception("Expected one `vector_expr` child")
        
        child = tree.children[0]
        return  lark.Tree(lark.Token('RULE', 'vector_expr'), 
                          lark.Tree(lark.Token('RULE', 'abs'), [child]))


    def step(self, tree):
        # Expects one vector_expr child.
        if len(tree.children) != 1:
            raise Exception("Expected one `vector_expr` child")
        
        child = tree.children[0]
        return  lark.Tree(lark.Token('RULE', 'vector_expr'), 
                          lark.Tree(lark.Token('RULE', 'step'), [child]))


        
# TODO: Chain operands, reduce powers, etc.
# ALSO TODO: Precompute arithmetic of literals.
@lark.visitors.v_args(tree=True)
class ArithmeticSimplifier1(lark.Transformer):
    def __init__(self, metadata, visit_tokens: bool = True) -> None:
        super().__init__(visit_tokens=True)
        self.particle_metadata = metadata

    def pow(self, tree):
        left, right = tree.children
        if isinstance(left, lark.Tree):
            if left.data == "pow":
                left_left, left_right = left.children
                if isinstance(left_right, lark.Tree):
                    if left_right.data == "literal":
                        pow_hi = left_right.children[0].value
                        pow_lo = right.children[0].value
