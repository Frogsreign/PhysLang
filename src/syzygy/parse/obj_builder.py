#!/usr/bin/python3
#
# @author Jacob Leider
# @author Jonas Muhlenkamp
#
# 
# Walks the initial syntax tree and builds the following objects:
#
#   * particles
#   * forces
#   * update rules
#


import lark


class ParticleMetadataBuilder(lark.Visitor):
    def __init__(self) -> None:
        super().__init__()
        self.prop_sizes = {}
        self.num_particles = 0

        self.particles = {}
        self.forces = {}
        self.updates = {}

        self.data = {}
        self.data["force"] = self.forces
        self.data["update"] = self.updates
        self.data["particle"] = self.particles


    def particle_group(self, tree):
        # TODO
        if not hasattr(tree, "particle_group"):
            tree.particle_group = ""

        for child in tree.children:
            if isinstance(child, lark.Tree):
                pass
        

    def force(self, tree):
        name_assign, input_assign, output_assign, function_assign = tree.children
        
        # Require a name
        if tree.children[0] is None:
            tree.children[0] = lark.Tree(lark.Token('RULE', 'name_assign'), 
                                         [lark.Token('VARIABLE_NAME', str(len(self.forces)))])

        if tree.children[2] is None:
            tree.children[2] = lark.Tree(lark.Token('RULE', 'output_assign'), [
                lark.Tree(lark.Token('RULE', 'particle_property_access'), [
                    input_assign.children[0],
                    lark.Token('VARIABLE_NAME', 'net_force'),
                    None
                    ])
                ]) # Default to A.net_force

        name = tree.children[0].children[0].value
        assignments = tree.children[1:]

        for assignment in assignments:
            assignment.assignee = name
            assignment.function_type = "force"

        self.forces[name] = {}


    def update(self, tree):
        name_assign, input_assign, output_assign, function_assign = tree.children

        # Require a name
        if tree.children[0] is None:
            tree.children[0] = lark.Tree(lark.Token('RULE', 'name_assign'), 
                                         [lark.Token('VARIABLE_NAME', str(len(self.updates)))])

        name = tree.children[0].children[0].value
        assignments = tree.children[1:]

        for assignment in assignments:
            assignment.assignee = name
            assignment.function_type = "update"

        self.updates[name] = {}


    def name_assign(self, tree):
        # No need.
        pass 


    def particle(self, tree):
        # Expecting `name_assign`, `property_assign`*
        # Require particle to have a name
        if tree.children[0] is None:
            tree.children[0] = lark.Tree(lark.Token('RULE', 'name_assign'), 
                                         [lark.Token('VARIABLE_NAME', str(len(self.particles)))])

        name = tree.children[0].children[0].value
        property_assigns = tree.children[1:]

        for assignment in property_assigns:
            assignment.assignee = name

        self.particles[name] = {"props": {}}


    def property_assign(self, tree):
        property_name, property_value = tree.children
        property_value = [child.value for child in property_value.children] # children are tokens
        property_name = property_name.value # name is terminal

        self.particles[tree.assignee]["props"][property_name] = property_value # May throw an error

        dim = len(property_value) # dimension

        # Validate property, possibly document its size/dimension
        if property_name in self.prop_sizes:
            if dim != self.prop_sizes[property_name]:
                raise Exception("Encountered instances of a property with different dimensionality")
        else:
            self.prop_sizes[property_name] = dim


    def input_assign(self, tree):
        params = tree.children
        self.data[tree.function_type][tree.assignee]["inputs"] = [param.value for param in params]


    def output_assign(self, tree):
        self.data[tree.function_type][tree.assignee]["output"] = {
                "property_index": None # Default
        }

        for child in tree.children:
            if child is not None:
                child.assignee = tree.assignee
                child.function_type = tree.function_type


    def function_assign(self, tree):
        func_def = tree.children[0].value
        func_def = func_def.strip("\"") # Remember to remove the quotes!
        self.data[tree.function_type][tree.assignee]["func"] = func_def


    def particle_property_access(self, tree):
        particle_name, property_name, property_index = tree.children
        self.data[tree.function_type][tree.assignee]["output"]["particle_name"] = particle_name.value
        self.data[tree.function_type][tree.assignee]["output"]["property_name"] = property_name.value
        if property_index is not None:
            self.data[tree.function_type][tree.assignee]["output"]["property_index"] = property_index.value
