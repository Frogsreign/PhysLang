#!/usr/bin/python3
#
# @author Jacob Leider
#
#
# The abstract class `SimState` may be subclassed depending on how you want to 
# deal with functions. The default `SimStatePythonLambdas` compiles functions 
# to lambda objects. This is slower than, say, translating to C, compiling 
# clang, and accessing via `ctypes`. However, `SimStatePythonLambdas` is 
# platform independant and simple to understand, so it serves as our default
# `SimState` object.
#
# A `SimStatePythonLambdas` instance is constructed from a parse-tree with 
# three main branches: particles, forces, and update rules. `SimState` uses 
# helper classes to organize and flatten the simulation data, and to compile the
# functions and map functions to their outputs. Specifically,
#
#   * `DataLayout` handles the particles
#   * `FuncHandler` handles the functions (forces and update rules)
#

import numpy
from syzygy.parse import parse
from syzygy.sim import data_layout
from syzygy.sim import func_handler

import inspect

import time



class SimState:
    def __init__(self, particles: list, forces: list, updates: list):
        self.data_layout = data_layout.DataLayout(particles)
        self._data = numpy.zeros(self.data_layout.sim_size(), dtype=numpy.float64)
        self._fresh_data = self._data.copy()
        self.data_layout.init_data(self._data, particles)


    def data(self):
        """Raw simulation data"""
        return self._data
    

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
        Iterates the state of the simulation.

        Args
            dt: Time elapsed between steps.
            t: Time since the start of the simulation.
            steps: Number of times to iterate the simulation state.
        """
        # Step `steps` times.
        for _ in range(steps):
            self._step_once(dt, t)

    
    def _step_once(self, dt, t):
        """See `step`"""
        raise NotImplementedError

        

class SimStatePythonLambdas(SimState):
    def __init__(self, particles: list, forces: list, updates: list):
        super().__init__(particles, forces, updates)
        # Manages functions as python lambdas.
        self.func_handler = func_handler.FuncHandler(forces, updates, self.data_layout)


    def _step_once(self, dt, t):
        """Overridden"""
        self._compute_step(dt, t)
        self._refresh_data()
        # Zero out net-force.
        self._data[self.data_layout.prop_idx_all_particles("net_force")] = 0
        

    def _refresh_data(self):
        """
        Update the simulation data with any fresh data, and zero out 
        fresh_data`.
        """
        indices = self._fresh_data != 0
        self._data[indices] = self._fresh_data[indices]
        self._fresh_data[:] = 0
    

    def _compute_step(self, dt, t):
        num_particles = self.data_layout.num_particles()
        # Compute forces.
        for i in range(num_particles):
            for j in range(num_particles):
                if i == j: continue # DON'T FORGET THIS


                # Compute the force between particles i and j, and apply to 
                # particle i.
                for force, index in self.func_handler.forces(i):
                    signature = inspect.signature(force)
                    number_of_arguments = len(signature.parameters)
                    if (number_of_arguments == 3):
                        self._data[index] += force(i, j, self._data) 
        

        # Compute forces (2).
        for i in range(num_particles):
            # Compute the force between particles i and j, and apply to 
            # particle i.
            for force, index in self.func_handler.forces(i):

                signature = inspect.signature(force)
                number_of_arguments = len(signature.parameters)

                if (number_of_arguments == 2):
                    self._data[index] += force(i, self._data) 

        #time.sleep(1)
        #print(self.data_layout.state_str(self.data()))



        # Compute and apply updates.
        for i in range(num_particles):
            # Update properties for particle i based on the net force, and dt.
            for update_rule, index in self.func_handler.updates(i):
                self._fresh_data[index] = update_rule(i, dt, self._data)


# FIXME: This should probably move.
def create_simulation(script, sim_state_class="python-lambdas"):
    """Builds a `SimState` object from a syzygy script."""
    # Parse
    ast_builder = parse.AstBuilder()
    tree = ast_builder.build_entire_ast(script)

    if sim_state_class == "python-lambdas":
        return SimStatePythonLambdas(tree["particles"], tree["forces"], tree["updates"])
    else:
        raise Exception(f"Unknown SimState subclass \"{sim_state_class}\"")
