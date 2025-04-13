#!/usr/bin/python3
#
# @author Jacob Leider
#
#
# This module is responsible for parsing an entire script; objects, functions 
# and all.

import copy

import lark
from syzygy.parse.objs import interpreter
from syzygy.parse.objs import scanner
from syzygy.parse.objs import parser
from syzygy.sim import data_layout

from syzygy.parse.ast_utils import * 


# Data class for a (particle name, property name, index) triple.
class ParticlePropertyAccess:
    def __init__(self, particle_name=None, property_name=None, property_index=None):
        self.particle_name = particle_name
        self.property_name = property_name
        self.property_index = property_index


# Helper class for the `AstBuilder` class:
#
# Builds a ParticlePropertyAccess object by walking a syntax tree rooted at 
# `particle_property_access`
class ParticlePropertyAccessBuilder(lark.Visitor):
    def __init__(self, ppa):
        self.ppa = ppa

    def particle_name(self, tree):
        self.ppa.particle_name = tree.children[0]

    def property_name(self, tree):
        self.ppa.property_name = tree.children[0]

    def property_index(self, tree):
        self.ppa.property_index = tree.children[0]



class AstBuilder:
    def __init__(self):
        # FIXME: Embed this in a context class or an environment variable
        FUNC_GRAMMAR_PATH = "../syntax/function.lark"
        # Generate parser
        self.parser = lark.Lark.open(FUNC_GRAMMAR_PATH, rel_to=__file__, strict=False)


    # Factored out in case we change the tree format.
    def _get_particles(self, tree: dict):
        return tree["particles"]


    def expr_to_ast(self, expr) -> lark.Tree:
        # Try to parse
        try:
            tree = self.parser.parse(expr)
            return tree
        except:
            raise Exception(f"Failed to parse function. Likely a syntax error:\n\n{expr}\n")


    def process_ast(self, tree, metadata):
        # Round 1
        IdentifierNameFlattener().visit(tree)
        # Round 2
        DimensionAnnotator(metadata).visit(tree)
        # Round 3
        NormToDotConverter().visit(tree)
        # Round 4
        DotExpander().visit_topdown(tree)
        # Round 5
        DotToScalarConverter().visit_topdown(tree)
        # Round 6
        LiteralAndKeywordFlattener().visit(tree)
        return tree


    def build_coordinate_function(self, entry, index, metadata):
        vector_output = entry["out"]
        coordinate_output = ParticlePropertyAccess(
                vector_output.particle_name,
                vector_output.property_name,
                index)
        
        coordinate_function_entry = {
                    "name": str(entry["name"]) + str(index),
                    "in":entry["in"],
                    "out": coordinate_output,
                    "func": copy.deepcopy(entry["func"])
        }

        coordinate_ast = self.expr_to_ast(coordinate_function_entry["func"])
        # Rounds 1-6
        self.process_ast(coordinate_ast, metadata)
        # Round 7 (project onto basis components)
        index_extractor = CoordinateBuilder(metadata, index)
        index_extractor.visit(coordinate_ast)
        coordinate_function_entry["func"] = coordinate_ast
        return coordinate_function_entry


    def maybe_split_function_into_coordinates(self, entry, metadata):
        coordinate_function_entries = []
        output = entry["out"]

        if output.property_index is None:
            dim = metadata.prop_size(entry["out"].property_name)
            for i in range(dim):
                coordinate_function_entries.append(
                        self.build_coordinate_function(entry, i, metadata))
        else:
            coordinate_function_entries.append(entry)

        return coordinate_function_entries


    # Create a `ParticlePropertyAccess` object for the function entry that 
    # represents the function's output.
    def specify_function_output(self, entry, function_type: str):
        if function_type == "force":
            if "out" not in entry: 
                entry["out"] = entry["in"][0] + ".net-force"
        elif function_type == "update":
            pass
        else:
            raise Exception(f"Invalid function type \"{function_type}\"")

        ppa_string = entry["out"]
        entry["out"] = ParticlePropertyAccess()
        
        tree = self.parser.parse(ppa_string)
        # Build the ParticlePropertyAccess object.
        IdentifierNameFlattener().visit(tree)
        ParticlePropertyAccessBuilder(entry["out"]).visit(tree)


    def convert_functions_strings_to_asts(self, tree: dict):
        particles = self._get_particles(tree)
        metadata = data_layout.ParticleMetadata(particles)

        new_forces = []
        for entry in tree["forces"]:
            # By default, a force's output is `net-force`.
            self.specify_function_output(entry, "force")
            new_forces.extend(self.maybe_split_function_into_coordinates(entry, 
                                                                    metadata))
        tree["forces"] = new_forces

        new_update_rules = []
        for entry in tree["update-rules"]:
            # Updates have no default output.
            self.specify_function_output(entry, "update")
            new_update_rules.extend(self.maybe_split_function_into_coordinates(entry, 
                                                                          metadata))
        tree["update-rules"] = new_update_rules


    
    def build_entire_ast(self, script):
        """
        The main interface to this class. Converts a script into an AST
        whose branches (`particles`, `forces`, `updates`) may be passed into 
        the `SimState` constructor.
        """
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

        self.convert_functions_strings_to_asts(unfinished_tree)

        return unfinished_tree
