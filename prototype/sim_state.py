import json
from logging import error
from matplotlib.pyplot import step
import numpy
from particle import Particle

import compile2

# JSON Standards:
#   https://datatracker.ietf.org/doc/html/rfc7159.html
#   https://ecma-international.org/publications-and-standards/standards/ecma-404/

class SimState:
    def __init__(self, particles: list[Particle], forces=None, update_rules=None) -> None:
        self._particles = particles
        self._forces = forces
        self._update_rules = update_rules

        self.init_props_map()

        self.config_functions()
        self.compile_functions()

        print(self._data)
        



    def config_functions(self):
        self.config_forces()
        self.config_update_rules()

    def compile_functions(self):
        self.compile_forces()
        self.compile_update_rules()


    def config_update_rules(self):
        rules = []
        for name, update_rule in self.update_rules().items():
            ast_prop_name = update_rule["out"]
            # Offset from beginnning of object data to the address of 
            # the value this function updates.
            idx = self.index_of_prop(ast_prop_name)
            # Append the pair (index of prop to be updated, function 
            # that returns the updated prop value).
            rules.append([idx, update_rule["func"]])
        self._update_rules = rules


    def config_forces(self):
        forces = []
        for name, force in self.forces().items():
            coord = force["out"]
            if not coord.startswith("%"):
                raise SyntaxError("Incorrectly formatted force output arg")
            coord = int(coord[1:])
            forces.append([coord, force["func"]])
        self._forces = forces



    def compile_forces(self):
        # Hate that we have to do this
        variables = ["particle_id_1", "particle_id_2", "data"]

        def var_converter(ast_var_name):
            particle_id = None
            if ast_var_name.startswith("obj1"):
                particle_id = "particle_id_1"
            else:
                particle_id = "particle_id_2"
            return f"data[{self.index_of_prop(ast_var_name)} + {particle_id} * {self.particle_size()}]"
    
        compiler_options = {
            "variables_predefined": True,
            "output_lang": "py",
            "var_converter": var_converter
        }

        
        for i in range(len(self.forces())):
            # Don't need the name.
            _, self._forces[i][1] = compile2.compile_tree(
                    self._forces[i][1],
                    compiler_options=compiler_options, 
                    old_variables=variables)
            self._forces[i][1] = eval(self._forces[i][1])
            print(self._forces[i][1])


    def compile_update_rules(self):
        # Compile update rules
        # Compile forces
        
        # fi: force component i
        variables = ["particle_id", "data", "dt", "f1", "f2", "f3"]

        def var_converter(ast_var_name):
            if ast_var_name.startswith("%"):
                arg_idx = int(ast_var_name[1:])
                if arg_idx == 0:
                    return "dt"
                elif arg_idx > 0:
                    return "f" + str(arg_idx)
                
            return f"data[{self.index_of_prop(ast_var_name)} + particle_id * {self.particle_size()}]"

        compiler_options = {
            "variables_predefined": True,
            "output_lang": "py",
            "var_converter": var_converter
        }

        
        for i in range(len(self.update_rules())):
            # Don't need the name.
            ast = self._update_rules[i][1]
            _, self._update_rules[i][1] = compile2.compile_tree(
                    ast, 
                    compiler_options=compiler_options, 
                    old_variables=variables)

            self._update_rules[i][1] = eval(self._update_rules[i][1])


    def init_prop_sizes_map(self):
        # Create a property -> size map.
        prop_sizes_map = {}
        for particle in self.particles(): 
            for name, val in particle.props().items():
                prop_size = 1
                if isinstance(val, numpy.ndarray):
                    prop_shape = val.shape
                    if len(prop_shape) != 1:
                        raise ValueError("array props must be one-dimensional."
                                         " Found " + name + " = " + str(prop_shape))
                    prop_size = prop_shape[0]
                if name in prop_sizes_map:
                    if prop_sizes_map[name] != prop_size:
                        raise ValueError("Inconsistent sizes for property " + name)
                prop_sizes_map[name] = prop_size
        # Initialize props, sizes, offsets.
        self._particle_size = 0
        self._props = []
        self._prop_offsets = []
        self._prop_sizes = []
        for name, size in prop_sizes_map.items():
            self._props.append(name)
            self._prop_offsets.append(self._particle_size)
            self._prop_sizes.append(size)
            self._particle_size += size
        # Map props to their indices.
        self._prop_to_idx = {}
        for i in range(len(self.props())):
            prop = self.props()[i]
            self._prop_to_idx[prop] = i


    def init_props_map(self):
        self.init_prop_sizes_map()
        # Allocate enough room for the entire set of particles.
        # Index k of property j of particle i will be i * (particle_size) + (prop_offsets[j]) + k
        self._data = numpy.zeros(self.particle_size() * self.num_particles())
        self._fresh_data = numpy.zeros(self.particle_size() * self.num_particles())
        for i in range(self.num_particles()):
            for j in range(len(self.props())):
                # FIXME For now, ignore if particle doesn't have this property.
                prop_name = self.props()[j]
                if prop_name not in self.particles()[i].props():
                    continue
                prop_val =  self.particles()[i].get(prop_name)
                offset = self.particle_size() * i + self.prop_offsets()[j]
                print(f"{j}: {self.prop_sizes()[j]}")
                print(f"prop: {prop_name}, val: {prop_val}")
                print(f"offset: {offset}")
                if self.prop_sizes()[j] == 1:
                    self._data[offset] = prop_val
                else:
                    for k in range(self.prop_sizes()[j]):
                        print(prop_val[k])
                        self._data[offset + k] = prop_val[k]


    def index_of_prop(self, ast_prop_name):
        seq = ast_prop_name.split('.')
        prop_name = seq[1]
        idx = self.prop_to_idx()[prop_name]
        prop_idx = None
        if len(seq) == 3:
            idx_chunks = seq[2].split(':')
            if len(idx_chunks) < 2:
                raise ValueError(f"Error parsing index of ast-property {ast_prop_name}")
            try:
                prop_idx = int(idx_chunks[1])
            except:
                raise ValueError(f"Error parsing index of ast-property {ast_prop_name}")
            if prop_idx < 0:
                raise ValueError(f"Indices must be positive")
        if prop_idx is not None:
            idx += prop_idx
        return idx


    def new_positions(self):
        """
        Return a list of positions where the index corresponds to the 
        particle's ID.

        Returns
            An iterable of numpy.ndarrays.
        """
        pos_idx = self.prop_to_idx()["pos"]
        for i in range(len(self.particles())):
            offset = i * self.particle_size() + self.prop_offsets()[pos_idx]
            if i == 2:
                print(self.data()[offset:offset+3])
            yield self.data()[offset:offset+3]

    def positions(self):
        """
        Return a list of positions where the index corresponds to the 
        particle's ID.

        Returns
            An iterable of numpy.ndarrays.
        """
        for particle in self._particles:
            yield particle.get("pos")


    def _new_step(self, dt, t, steps=1):
        """
        Iterate the state of the simulation.

        Args
            dt: Time elapsed between steps.
            t: Time since the start of the simulation.
            steps: Number of times to iterate the simulation state.
        """
        if not isinstance(steps, int):
            raise ValueError("`steps` must be an int")

        # Step `steps` times.
        for _ in range(steps):
            # Step once.
            dim = 3
            df = numpy.zeros((len(self.particles()), dim))
            for i in range(len(self.particles())):
                for j in range(len(self.particles())):
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
                        coord, force = self.forces()[k]
                        df[i][coord] += force(i, j, self._data)

            for i in range(len(self.particles())):
                # Update props for particle i based on the net force, and dt.
                #
                # e.g. 
                #
                #   for update-rule R with output prop.idx:
                #       data[index-of(prop.idx)] = R(dt, net force)
                #       
                for i in range(len(self.update_rules())):
                    prop_idx, rule = self.update_rules()[i]
                    # Location of the data to be updated.
                    offset = self.particle_size() * i + prop_idx
                    self._fresh_data[offset] = rule(i, self._data, dt, *df[i])

            self._fresh_data, self._data = self._data, self._fresh_data
            self._fresh_data[:] = 0


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

        # Step `steps` times.
        for _ in range(steps):
            # Step once.
            for i in range(len(self._particles)):
                # Compute net force between each particle pair.
                df = numpy.zeros((3,))
                for j in range(len(self._particles)):
                    if j == i:
                        continue
                    df += self._particles[i].net_force_from(self._particles[j], t)

                self._particles[i].update_props(df, dt)


    def to_json(self) -> str: 
        """
        Output a serialized representation of the simulation state.
        """
        obj_list = [p._dict() for p in self._particles]
        return json.JSONEncoder().encode({"particles": obj_list})
    
    def num_particles(self):
        return len(self.particles())
    
    def particles(self):
        return self._particles

    def particle_size(self):
        return self._particle_size

    def props(self):
        return self._props

    def prop_sizes(self):
        return self._prop_sizes

    def num_props(self):
        return len(self.prop_sizes())

    def prop_offsets(self):
        return self._prop_offsets

    def set_data(self, i, val):
        self._data[i] = val

    def get_data(self, i):
        return self._data[i]

    def data(self):
        return self._data

    def forces(self):
        return self._forces

    def update_rules(self):
        return self._update_rules

    def prop_to_idx(self):
        return self._prop_to_idx
