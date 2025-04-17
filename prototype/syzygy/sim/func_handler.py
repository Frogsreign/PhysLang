#!/usr/bin/python3
#
# @author Jacob Leider
#
#
# A helper class for the SimState class. FuncHandler compiles functions (forces 
# and updates) and maps functions to their output objects in the global data 
# array.


from syzygy.compile import compile3


class FuncHandler:
    def __init__(self, forces, update_rules, data_layout):
        self.process_forces(forces, data_layout)
        self.process_update_rules(update_rules, data_layout)


    def process_forces(self, forces, data_layout):
        force_names = []
        force_funcs = []
        force_outps = []

        compiler_options = {
            "variables_predefined": True,
            "output_lang": "py",
            "particle_metadata": data_layout.particle_metadata,
            "variables": ["A", "B", "data"],
        }

        self._compile_forces(forces, force_names, force_funcs, 
                            force_outps, compiler_options, data_layout)

        self.forces = force_funcs
        self.force_names = force_names
        self.force_outps = force_outps
            

    def process_update_rules(self, update_rules, data_layout):
        update_rule_names = []
        update_rule_funcs = []
        update_rule_outps = []
                    
        compiler_options = {
            "variables_predefined": True,
            "variables": ["A", "dt", "data"],
            "output_lang": "py",
            "particle_metadata": data_layout.particle_metadata,
        }
        
        self._compile_update_rules(update_rules, update_rule_names, 
                                   update_rule_funcs, update_rule_outps,
                                   compiler_options, data_layout)

        self.update_rules = update_rule_funcs
        self.update_rule_names = update_rule_names
        self.update_rule_outps = update_rule_outps



    def _compile_forces(self, force_entries, force_names, force_funcs, 
                       force_outps, compiler_options, data_layout):
        # Compile all forces.
        for entry in force_entries:
            compiler_options["func_name"] = entry["name"]
            self._compile_force(entry["func"], compiler_options, 
                               force_names, force_funcs)
            # Assign force to an output variable (net-force).
            #print("FORCE")
            self.set_outp(entry, force_outps, data_layout)


    def _compile_update_rules(self, update_rules, update_rule_names, 
                             update_rule_funcs, update_rule_outps, 
                             compiler_options, data_layout):
        # Compile all update_rules.
        for entry in update_rules:
            # Compile.
            compiler_options["func_name"] = entry["name"]
            self._compile_update_rule(entry["func"], 
                                      compiler_options, 
                                      update_rule_names, 
                                      update_rule_funcs)
            #print("UPDATE")
            self.set_outp(entry, update_rule_outps, data_layout)


    def _compile_force(self, force_code, compiler_options, force_names, force_funcs):
            # Compile.
            force_name, force_func = compile3.compile_tree(force_code,
                    compiler_options=compiler_options)
            # Append to lists.
            force_names.append(force_name)
            force_funcs.append(eval(force_func))


    def _compile_update_rule(self, update_rule_code, compiler_options,
                             update_rule_names, update_rule_funcs):
            # Compile.
            update_rule_name, update_rule_func = compile3.compile_tree(
                    update_rule_code, compiler_options=compiler_options)
            # Append to lists.
            update_rule_names.append(update_rule_name)
            update_rule_funcs.append(eval(update_rule_func))


    def set_outp(self, update_rule_entry, update_rule_outps, data_layout):
        #for k, v in update_rule_entry.items(): if k != "func": print(f"    {k}: {v}")
        outp = update_rule_entry["output"]

        update_rule_outps.append(data_layout.idx_of(
            prop_name=outp["property_name"], index=outp["property_index"]))
