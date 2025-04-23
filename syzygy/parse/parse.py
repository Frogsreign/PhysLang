#!/usr/bin/python3
#
# @author Jacob Leider
#
#
# This module is responsible for parsing an entire script; objects, functions 
# and all.

import copy
import lark

from syzygy.sim import data_layout
from syzygy.parse.obj_builder import *
from syzygy.parse.func_builder import * 


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
        GRAMMAR_PATH = "../grammar/grammar.lark"
        # Generate parsers
        self.obj_parser = lark.Lark.open(GRAMMAR_PATH, rel_to=__file__, start="particle_group") 
        self.parser = lark.Lark.open(GRAMMAR_PATH, rel_to=__file__, strict=False, start="start")


    # PARSING HAPPENS HERE
    def maybe_split_function_into_coordinates(self, entry, metadata):
        coordinate_function_entries = []
        output = entry["output"]
        func = entry["func"]
        
        # Parse
        tree = self.parser.parse(func)
        
        # Shape
        tree = LinearAlgebraChecker2(metadata).transform(tree)

        coords = tree.children
        for index, coord in enumerate(coords):
            coords[index] = {
                    "name": str(entry["name"]) + str(index),
                    "inputs": entry["inputs"],
                    "output": {
                        "particle_name": output["particle_name"],
                        "property_name": output["property_name"],
                        "property_index": index
                        },
                    "func": coord
            }

        return coords


    def build_out_functions(self, tree: dict):
        metadata = data_layout.ParticleMetadata(tree["particles"])

        new_forces = []
        for entry in tree["forces"]:
            # By default, a force's output is `net_force`.
            #self.specify_function_output(entry, "force")
            new_forces.extend(self.maybe_split_function_into_coordinates(entry, 
                                                                    metadata))
        tree["forces"] = new_forces

        new_update_rules = []
        for entry in tree["updates"]:
            # Updates have no default output.
            #self.specify_function_output(entry, "update")
            new_update_rules.extend(self.maybe_split_function_into_coordinates(entry, 
                                                                          metadata))
        tree["updates"] = new_update_rules

    
    def build_entire_ast(self, script):
        """
        The main interface to this class. Converts a script into an AST
        whose branches (`particles`, `forces`, `updates`) may be passed into 
        the `SimState` constructor.
        """
        tree = self.obj_parser.parse(script)

        tree_cpy = lark.Transformer().transform(tree)

        # TESTING
        pmb = ParticleMetadataBuilder()
        pmb.visit_topdown(tree_cpy)
    
        # --- Switch formats --- 
        # TODO: Link up the two ends and avoid the format-switching.
        particles = [{"name": name, 
                      "props": pmb.particles[name]["props"]} 
                     for name in pmb.particles.keys()]

        forces = [{"name": name, 
                   "inputs": pmb.forces[name]["inputs"],
                   "output": pmb.forces[name]["output"],
                   "func": pmb.forces[name]["func"]}
                  for name in pmb.forces.keys()]

        updates = [{"name": name, 
                   "inputs": pmb.updates[name]["inputs"],
                   "output": pmb.updates[name]["output"],
                   "func": pmb.updates[name]["func"]}
                  for name in pmb.updates.keys()]
        
        # Old format AST
        unfinished_tree = {
                "group-id":     0, 
                "forces":       forces, 
                "particles":    particles, 
                "updates": updates}

        self.build_out_functions(unfinished_tree)

        return unfinished_tree
