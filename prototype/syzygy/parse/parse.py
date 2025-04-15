#!/usr/bin/python3
#
# @author Jacob Leider
#
#
# This module is responsible for parsing an entire script; objects, functions 
# and all.

import copy
import os

import lark
from numpy import isin, partition
import numpy
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


class SimDataCollector(lark.Visitor):
    def __init__(self):
        self.particles = []
        self.forces = []
        self.updates = []


    def children(self, tree, *args):
        for i in args:
            tree = tree.children[i];
        return tree


    def variable_name(self, tree):
        tree.children = [self.children(tree, 0).value]


    def name_definition(self, tree):
        # Super annoying
        tree.children = [tree.children[0].children[0]]


    def particle_group_entry(self, tree):
        pass


    def particle(self, tree):
        particle = {  }
        particle["props"] = {}
        for child in tree.children:
            if isinstance(child, lark.Tree):
                if child.data == "name_definition":
                    particle["name"] = child.children[0]
                elif child.data == "property_definition":
                    particle["props"][child.property_name] = child.property_val

        # Assign a default name perhaps
        if "name" not in particle:
            particle["name"] = "particle_" + str(len(self.particles))

        self.particles.append(particle)


    def force(self, tree):
        force = {}
        for child in tree.children:
            if isinstance(child, lark.Tree):
                if child.data == "name_definition":
                    force["name"] = child.children[0]
                elif child.data == "input_definition":
                    force["in"] = child.children[0]
                elif child.data == "output_definition":
                    if child.children[0] is not None:
                        force["out"] = child.children[0]
                    else:
                        force["out"] = force["in"][0] + [".net-force"]
                elif child.data == "function_definition":
                    force["func"] = child.children[0]

        # Assign a default name perhaps
        if "name" not in force:
            force["name"] = "force_" + str(len(self.forces))

        self.forces.append(force)


    def update(self, tree):

        update = {}
        for child in tree.children:
            if isinstance(child, lark.Tree):
                if child.data == "name_definition":
                    update["name"] = child.children[0]
                elif child.data == "input_definition":
                    update["in"] = child.children[0]
                elif child.data == "output_definition":
                    update["out"] = child.children[0]
                elif child.data == "function_definition":
                    update["func"] = child.children[0]

        # Assign a default name perhaps
        if "name" not in update:
            update["name"] = "update_" + str(len(self.updates))

        self.updates.append(update)


    def property_definition(self, tree):
        name, val = tree.children
        tree.property_name = name.children[0]
        tree.property_val = val.children[0]
        tree.property_dimension = val.dimension


    def output_definition(self, tree):
        child = tree.children[0]
        tree.children[0] = f"{child.children[0]}.{child.children[1]}"
        if child.children[2] is not None:
            tree.children[0] += f"[{child.children[2]}]"


    def input_definition(self, tree):
        tree.children = [child.children[0] for child in tree.children]


    def function_definition(self, tree):
        tree.children[0] = "".join([child.value for child in tree.children]).strip("\"")


    def particle_property_access(self, tree):
        for i in range(len(tree.children)):
            if tree.children[i] is not None:
                tree.children[i] = tree.children[i].children[0]
        particle_name = tree.children[0].value
        property_name = tree.children[1].value
        property_index = tree.children[2]
        if property_index is not None:
            property_index = property_index.value
        tree.children = [particle_name, property_name, property_index]
        print(tree)


    def literal(self, tree):
        tree.dimension = tree.children[0].dimension
        tree.children = tree.children[0].children


    def literal_vector(self, tree):
        tree.dimension = len(tree.children)
        tree.children = [[numpy.float64(child.value) for child in tree.children]]
    

    def literal_scalar(self, tree):
        tree.children = [numpy.float64(child.value) for child in tree.children]
        tree.dimension = 1


class AstBuilder:
    def __init__(self):
        # FIXME: Embed this in a context class or an environment variable
        FUNC_GRAMMAR_PATH = "../syntax/function.lark"
        OBJ_GRAMMAR_PATH = "../syntax/sim_group.lark"
        # Generate parsers
        self.obj_parser = lark.Lark.open(OBJ_GRAMMAR_PATH, rel_to=__file__, start="particle_group") 
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
        LiteralFlattener().visit(tree)
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
        print(80 * "-")
        print(entry)
        print(80 * "-")
        if function_type == "force":
            if "out" not in entry: 
                entry["out"] = entry["in"][0] + ".net-force"
        elif function_type == "update":
            pass
        else:
            raise Exception(f"Invalid function type \"{function_type}\"")

        ppa_string = entry["out"]
        entry["out"] = ParticlePropertyAccess()

        print(ppa_string)
        
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
        tree = self.obj_parser.parse(script)

        sim_data_collector = SimDataCollector()
        sim_data_collector.visit(tree)

        unfinished_tree = {
                "group-id":     0, 
                "forces":       sim_data_collector.forces, 
                "particles":    sim_data_collector.particles, 
                "update-rules": sim_data_collector.updates}

        self.convert_functions_strings_to_asts(unfinished_tree)

        return unfinished_tree
