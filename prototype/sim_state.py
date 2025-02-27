import numpy

import compile2
import datalayout

# Ignore the long schematic comments.

# JSON Standards:
#   https://datatracker.ietf.org/doc/html/rfc7159.html
#   https://ecma-international.org/publications-and-standards/standards/ecma-404/

class SimState:
    def __init__(self, particles: list, forces: list, update_rules: list):
        self._offset_map = datalayout.create_offset_map(particles)
        # Empty data buffer.
        self._data = numpy.zeros(self._offset_map.sim_size(), dtype=numpy.float64)
        self._init_data(particles)
        # Initialize forces and update rules.
        self._force_names, self._force_outps, self._forces = self.compile_forces(forces)
        self._update_rule_names, self._update_rule_outps, self._update_rules = self.compile_update_rules(update_rules)


    def _init_data(self, particles):
        """
        Fill empty data buffer with particle data.
        """
        for particle in particles:
            particle_name = particle["name"]
            particle_data = particle["props"]
            for prop_name, prop_data in particle_data.items():
                prop_size = self._offset_map.prop_size(prop_name)
                if prop_size == 1:
                    idx = self._offset_map.idx_of(
                            particle_name, 
                            prop_name)
                    self._data[idx] = prop_data
                elif prop_size > 1:
                    for prop_idx, prop_val in enumerate(prop_data):
                        idx = self._offset_map.idx_of(
                                particle_name, 
                                prop_name, 
                                prop_idx)
                        self._data[idx] = prop_val


    def compile_forces(self, forces):
        force_names = []
        force_funcs = []
        force_outps = []
        # Define variables and variable name mapper.
        variables = ["particle_id_1", "particle_id_2", "data"]
        particle_size = self._offset_map.particle_size()

        def var_to_idx(ast_var_name):
            seq = ast_var_name.split(".")
            if len(seq) < 2:
                raise RuntimeError()
            prop_name = seq[1]
            prop_offset = self._offset_map.prop_offset(prop_name)
            prop_idx = 0
            if len(seq) > 2: # Should be == 3
                prop_idx = int(seq[2].split(":")[1])
            return prop_offset + prop_idx

        def var_converter(ast_var_name):
            particle_id = None
            if ast_var_name.startswith("obj1"):
                particle_id = "particle_id_1"
            else:
                particle_id = "particle_id_2"
            seq = ast_var_name.split(".")
            if len(seq) < 2:
                raise RuntimeError()
            prop_name = seq[1]
            prop_offset = self._offset_map.prop_offset(prop_name)
            prop_idx = 0
            if len(seq) > 2: # Should be == 3
                prop_idx = int(seq[2].split(":")[1])
        
            idx = prop_offset + prop_idx
            return f"data[{idx} + {particle_id} * {particle_size}]"    
    
        compiler_options = {
            "variables_predefined": True,
            "output_lang": "py",
            "var_name_mapper": var_converter
        }

        # Compile all forces.
        for force_name, force_entry in forces.items():
            force_func_tree = force_entry["func"]
            force_outp = force_entry["out"]
            force_inp = force_entry["in"]
            # Compile.
            compiler_options["func_name"] = force_name
            force_name, force_func = compile2.compile_tree(
                    force_func_tree,
                    compiler_options=compiler_options, 
                    variables=variables)
            # Append to lists.
            force_names.append(force_name)
            force_funcs.append(eval(force_func))
            force_outps.append(var_to_idx(force_outp))
            print(force_func)
        return force_names, force_outps, force_funcs


    def compile_update_rules(self, update_rules):
        update_rule_names = []
        update_rule_funcs = []
        update_rule_outps = []
        # Define variables and variable name mapper.
        variables = ["particle_id", "dt", "data"]
        particle_size = self._offset_map.particle_size()

        def var_to_idx(ast_var_name):
            seq = ast_var_name.split(".")
            if len(seq) < 2:
                raise RuntimeError()
            prop_name = seq[1]
            prop_offset = self._offset_map.prop_offset(prop_name)
            prop_idx = 0
            if len(seq) > 2: # Should be == 3
                prop_idx = int(seq[2].split(":")[1])
            return prop_offset + prop_idx

        def var_converter(ast_var_name):
            if ast_var_name.startswith("dt"):
                return "dt"
            else:
                seq = ast_var_name.split(".")
                if len(seq) < 2:
                    raise RuntimeError()
                prop_name = seq[1]
                prop_offset = self._offset_map.prop_offset(prop_name)
                prop_idx = 0
                if len(seq) > 2: # Should be == 3
                    prop_idx = int(seq[2].split(":")[1])
            
                idx = prop_offset + prop_idx
                return f"data[{idx} + particle_id * {particle_size}]"    
                    
        compiler_options = {
            "variables_predefined": True,
            "output_lang": "py",
            "var_name_mapper": var_converter
        }
        
        # Compile all update_rules.
        for update_rule_name, update_rule_entry in update_rules.items():
            update_rule_func_tree = update_rule_entry["func"]
            update_rule_outp = update_rule_entry["out"]
            update_rule_inp = update_rule_entry["in"]
            # Compile.
            compiler_options["func_name"] = update_rule_name
            update_rule_name, update_rule_func = compile2.compile_tree(
                    update_rule_func_tree,
                    compiler_options=compiler_options, 
                    variables=variables)
            # Append to lists.
            update_rule_names.append(update_rule_name)
            update_rule_funcs.append(eval(update_rule_func))
            update_rule_outps.append(var_to_idx(update_rule_outp))
            print(update_rule_func)
        return update_rule_names, update_rule_outps, update_rule_funcs


    def positions(self):
        """
        Return a list of positions where the index corresponds to the 
        particle's ID.

        Returns
            An iterable of numpy.ndarrays.
        """
        particle_size = self._offset_map.particle_size()
        num_particles = self._offset_map.num_particles()
        pos_idx = self._offset_map.prop_offset("pos")
        for i in range(num_particles):
            offset = i * particle_size + pos_idx
            yield self._data[offset:offset+3]


    def _step(self, dt, t, steps=1):
        """
        Iterate the state of the simulation.

        Args
            dt: Time elapsed between steps.
            t: Time since the start of the simulation.
            steps: Number of times to iterate the simulation state.
        """

        if not isinstance(steps, int):
            raise ValueError("`steps` must be an int")

        fresh_data = numpy.zeros(self._offset_map.particle_size() * self._offset_map.num_particles(), dtype=numpy.float64)
        # Step `steps` times.
        for _ in range(steps):
            # Step once.
            for i in range(self._offset_map.num_particles()):
                for j in range(self._offset_map.num_particles()):
                    if i == j:
                        continue # Cannot believe I forgot this. Took me an hour to debug.
                    # FORCE OF j ON i
                    #   - in direction (j - i)
                    #
                    # Compute net force between i and j, add it to i and j's overall net forces.
                    # Let comp(i - j, k) be the magnitude of the projection of the unit vector i - j
                    # onto the direction k (very easy to compute).
                    #
                    # e.g. 
                    #
                    #   for force F (with direction k):
                    #       net force on particle i in direction k += F(particle i, particle j) * comp(i-j, k)
                    #       net force on particle j in direction k += F(particle i, particle j) * comp(i-j, k)
                    #   
                    for k in range(len(self.forces())):
                        force = self.forces()[k]
                        offset = i * self._offset_map.particle_size() + self._force_outps[k]
                        df = force(i, j, self._data)
                        self._data[offset] += df 

            for i in range(self._offset_map.num_particles()):
                # Update props for particle i based on the net force, and dt.
                #
                # e.g. 
                #
                #   for update-rule R with output prop.idx:
                #       data[index-of(prop.idx)] = R(dt, net force)
                #       
                for k in range(len(self.update_rules())):
                    update_rule = self.update_rules()[k]
                    # Location of the data to be updated.
                    offset = i * self._offset_map.particle_size() + self._update_rule_outps[k]
                    fresh_data[offset] = update_rule(i, dt, self._data)

            # Awful debugger function.
            def print_data():
                for i in range(self._offset_map.num_particles()):
                    for j in range(13):
                        print(self._data[i * 13 + j], end=" ")
                    print("")

            self._data[fresh_data != 0] = fresh_data[fresh_data != 0]
            # Zero out net-force.
            # FIXME
            num_particles = self._offset_map.num_particles()
            particle_size = self._offset_map.particle_size()
            df_size = self._offset_map.prop_size("net-force")
            df_idx = self._offset_map.prop_offset("net-force")
            for i in range(num_particles):
                offset = i * particle_size + df_idx
                self._data[offset:offset+df_size] = 0

    def to_json(self) -> str: 
        """
        Output a serialized representation of the simulation state.
        """
        return NotImplemented
    
    def get_data(self, i):
        return self._data[i]

    def data(self):
        return self._data

    def forces(self):
        return self._forces

    def update_rules(self):
        return self._update_rules
