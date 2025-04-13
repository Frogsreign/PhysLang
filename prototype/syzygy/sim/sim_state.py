#
# @author Jacob Leider
#

import numpy
import time

from syzygy.parse import parse
from syzygy.sim import data_layout
from syzygy.sim import func_handler

# Ignore the long schematic comments.

# JSON Standards:
#   https://datatracker.ietf.org/doc/html/rfc7159.html
#   https://ecma-international.org/publications-and-standards/standards/ecma-404/

class SimState:
    def __init__(self, particles: list, forces: list, update_rules: list):
        self.data_layout = data_layout.DataLayout(particles)
        self._data = numpy.zeros(self.data_layout.sim_size(),
                                 dtype=numpy.float64)
        self._fresh_data = self._data.copy()
        self.data_layout.init_data(self._data, particles)
        # Empty data buffer.
        # Initialize forces and update rules.
        self.func_handler = func_handler.FuncHandler(forces,
                                                     update_rules,
                                                     self.data_layout)


    def positions(self):
        """
        Return a list of positions where the index corresponds to the 
        particle's ID.

        Returns
            An iterable of numpy.ndarrays.
        """
        for idxs in self.data_layout.prop_idx_all_particles("pos"):
            yield self._data[idxs]


    def step(self, dt, t, steps=1):
        """
        Iterate the state of the simulation.

        Args
            dt: Time elapsed between steps.
            t: Time since the start of the simulation.
            steps: Number of times to iterate the simulation state.
        """
        particle_size = self.data_layout.particle_size()
        num_particles = self.data_layout.num_particles()





        # Step `steps` times.
        for _ in range(steps):
            #time.sleep(1)
            #print(self._data[0:13])
            # Step once.
            for i in range(num_particles):
                for j in range(num_particles):
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
                    for force, prop_idx in zip(
                            self.func_handler.forces, 
                            self.func_handler.force_outps):
                        offset = i * particle_size + prop_idx
                        self._data[offset] += force(i, j, self._data) 

            for i in range(num_particles):
                # Update props for particle i based on the net force, and dt.
                #
                # e.g. 
                #
                #   for update-rule R with output prop.idx:
                #       data[index-of(prop.idx)] = R(dt, net force)
                #       
                for update_rule, prop_idx in zip(
                        self.func_handler.update_rules, 
                        self.func_handler.update_rule_outps):
                    # Location of the data to be updated.
                    offset = i * particle_size + prop_idx
                    self._fresh_data[offset] = update_rule(i, dt, self._data)

            # Awful debugger function.
            def print_data():
                for i in range(self.data_layout.num_particles()):
                    for j in range(particle_size):
                        print(self._data[i * particle_size + j], end=" ")
                    print("")

            # Zero out net-force.
            self._data[self._fresh_data != 0] = self._fresh_data[self._fresh_data != 0]
            self._data[self.data_layout.prop_idx_all_particles("net-force")] = 0


    def data(self):
        return self._data


def create_simulation(script):
    tree = parse.build_entire_ast(script)
    state = SimState(tree["particles"], tree["forces"], tree["update-rules"])
    return state
