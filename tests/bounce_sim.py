#!/usr/bin/python3 
#
# @author Jacob Leider
#
# Example simulation. Simulates a ball bouncing.
#
# Relative imports requires you run this script as follows:
#
#           python3 -m tests.bounce_sim_2


import syzygy
import syzygy.sim.sim_state
from syzygy import anim_native


if __name__ == '__main__':
    # Simulation objects (particles).
    state = syzygy.sim.sim_state.create_simulation(open("tests/scripts/bounce.txt", "r").read())

    # Simulation parameter (s).
    video_speed = 0.05
    zoom = 0.1

    # Create figure and 3D axis.
    sim = anim_native.Simulation(dt=video_speed, 
            steps_per_update=500, 
            state=state)

    # Setup background.
    sim.config_fig() 
    sim.config_bg() 

    sim.create_animation()
    sim.run_animation()
