#!/usr/bin/python3
#
# @author Jacob Leider
#
#
# Utilities for AST Shaping. Each class performs a round of shaping.
# 

import copy

from numpy import right_shift

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


    def _unpack_children(self, tree, num_children, vector_expr=True):
        """Unpack and validate."""
        # Expects two vector_expr children.
        if len(tree.children) != num_children:
            raise Exception("Expected two `vector_expr` children")

        for child in tree.children:
            if child.data != "vector_expr":
                raise Exception("Expected vector_expr operands")

        if len(tree.children) == 1:
            return tree.children[0]
        else:
            return tree.children


    def _tree(self, rule, children):
        """Shorthand for a <rule> tree tree wrapper"""
        return lark.Tree(lark.Token("RULE", rule), children)


    def _vector_expr(self, children):
        """Shorthand for a vector_expr tree wrapper"""
        return self._tree("vector_expr", children)
    

    def _unary_builtin(self, rule, child):
        """Shorthand for a <unary builtin function> tree tree wrapper"""
        arg = self._tree(rule, [child]) # 'arg' as in arg to the builtin
        return self._vector_expr([arg])


    def _pointwise_binary(self, rule, left, right):
        """Addition of vectors subtrees -> Vector of addition subtrees"""
        children = []
        for ll, rr in zip(left.children, right.children):
            children.append(self._tree(rule, [ll, rr]))

        return self._vector_expr(children)


    def _scalar_vector_binary(self, rule, left, right):
        """Scalar-vector product when scalar can act by left and right scalar product"""
        if len(left.children) == 1:
            left.children = [copy.deepcopy(left.children[0]) 
                             for _ in range(len(right.children))]
        elif len(right.children) == 1:
            right.children = [copy.deepcopy(right.children[0]) 
                              for _ in range(len(left.children))]
        else:
            raise Exception("Dimension mismatch and niether operand is a scalar")
        
        return self._pointwise_binary(rule, left, right)


    def _scalar_vector_binary_left(self, rule, left, right):
        """Scalar-vector product when scalar may only act by left scalar product"""
        if len(left.children) == 1:
            left.children = [copy.deepcopy(left.children[0]) 
                              for _ in range(len(right.children))]
        else:
            raise Exception("Can't divide a vector by a non-scalar of different dimension")
        
        return self._pointwise_binary(rule, left, right)


    def _scalar_vector_binary_right(self, rule, left, right):
        """Scalar-vector product when scalar may only act by right scalar product"""
        if len(right.children) == 1:
            right.children = [copy.deepcopy(right.children[0]) 
                              for _ in range(len(left.children))]
        else:
            raise Exception("Can't divide a vector by a non-scalar of different dimension")
        
        return self._pointwise_binary(rule, left, right)


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
            # Build indices
            indices = []
            for i in range(dim):
                children = [particle_name, property_name, lark.Token("NUMBER", i)]
                indices.append(self._tree("particle_property_access", children))
            # Convert to vector_expr
            return self._vector_expr(indices)
        else:
            return self._tree("vector_expr", [tree])


    def keyword(self, tree):
        # TODO: If we add more keywords, this will need to be updated.
        return self._vector_expr([tree])


    def literal(self, tree):
        return self._vector_expr([tree])


    def identifier(self, tree):
        return tree.children[0]
    

    def add(self, tree):
        left, right = self._unpack_children(tree, 2)

        if len(left.children) != len(right.children):
            raise Exception("Dimension mismatch.")

        return self._pointwise_binary("add", left, right)


    def sub(self, tree):
        left, right = self._unpack_children(tree, 2)
       
        if len(left.children) != len(right.children):
            raise Exception("Dimension mismatch.")

        return self._pointwise_binary("sub", left, right)


    def mul(self, tree):
        left, right = self._unpack_children(tree, 2) 

        if len(left.children) != len(right.children):
            return self._scalar_vector_binary("mul", left, right)
        else:
            return self._pointwise_binary("mul", left, right)

    
    def div(self, tree):
        # Expects two vector_expr children.
        left, right = self._unpack_children(tree, 2) 

        if len(left.children) != len(right.children):
            return self._scalar_vector_binary_right("div", left, right)
        else:
            return self._pointwise_binary("div", left, right)


    def pow(self, tree):
        # Expects two vector_expr children.
        left, right = self._unpack_children(tree, 2) 

        # Dimension check
        if len(left.children) != len(right.children):
            return self._scalar_vector_binary_right("pow", left, right) 
        else:
            return self._pointwise_binary("pow", left, right)


    def norm(self, tree):
        # Expects one vector_expr child
        child = self._unpack_children(tree, 1) 

        # Duplicate the child.
        tree.children.append(child)
        
        # Evaluate dot product and extract from 'vector_expr'
        dot_prod = self.dot(tree)
        dot_prod = dot_prod.children[0]
        
        one_half = self._tree("literal", [lark.Token("SIGNED_NUMBER", 0.5)])
        square_root = self._tree("pow", [dot_prod, one_half])
        return self._vector_expr([square_root]) # take it's square root


    def dot(self, tree):
        left, right = self._unpack_children(tree, 2) 

        dim = len(tree.children[0].children)
        prod = self._vector_expr([])

        # Expand the dot product into a sum.
        curr = prod
        for i in range(dim):
            summand = self._tree("mul", [left.children[i], right.children[i]])
            if i < dim - 1:
                curr.children.append(self._tree("add", [summand]))
                curr = curr.children[-1]
            else:
                curr.children.append(summand)

        return prod


    def abs(self, tree):
        # Expects one vector_expr child.
        child = self._unpack_children(tree, 1)
        child = child.children[0] # We're taking the absolute value of this
        return self._unary_builtin("abs", child)


    def step(self, tree):
        child = self._unpack_children(tree, 1)
        child = child.children[0] # We're taking the absolute value of this
        return self._unary_builtin("step", child)


    def sign(self, tree):
        child = self._unpack_children(tree, 1)
        child = child.children[0] # We're taking the absolute value of this
        return self._unary_builtin("sign", child)

        

# TODO: Chain operands, reduce powers, etc.
# ALSO TODO: Precompute arithmetic of literals.
@lark.visitors.v_args(tree=True)
class ArithmeticSimplifier1(lark.Transformer):
    def __init__(self, metadata, visit_tokens: bool = True) -> None:
        super().__init__(visit_tokens=True)
        self.particle_metadata = metadata

    def _tree(self, rule, children):
        return lark.Tree(lark.Token("RULE", rule), children)

    def pow(self, tree):
        """
        Converts

        ---------------------------------------------------------------
            pow ──── pow ──── tree
             │        │
             │        │
             e1       e2
        ---------------------------------------------------------------
        
        to 
                                
        ---------------------------------------------------------------
            pow ──── tree
             │
             │
            add ───── e1            
             │
             │
             e2                     
        ---------------------------------------------------------------
        """

        base, e1 = tree.children
        if isinstance(base, lark.Tree) and base.data == "pow":
            base, e2 = base.children
            exp_sum = self._tree("add", [e1, e2])
            return self._tree("pow", [base, exp_sum])
        else:
            return tree


