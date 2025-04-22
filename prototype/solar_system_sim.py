# Example simulation. Simulates the planets' orbits about the sun.

# Relative imports requires you run this script as follows:
#
#           python3 -m tests.solar_system_sim

import syzygy
import syzygy.sim.sim_state
from syzygy import anim_native

from syzygy.sim.sim_state import SimState
import json

SUN_TO_PLUTO_DISTANCE = 59064e8



if __name__ == '__main__':
    # Simulation objects (particles).
    state = syzygy.sim.sim_state.create_simulation(open("tests/data/new_solar_system.txt", "r").read())

    # Simulation parameter (s).
    video_speed = 100
    zoom = 0.1

    x = 2

    # Create figure and 3D axis.
    sim = anim_native.Simulation(dt=60 * 60 * video_speed, 
            steps_per_update=video_speed * x, 
            state=state)

    # Setup background.
    sim.config_fig() 
    sim.config_bg()
    sim.config_plot_limits(
            (-zoom * SUN_TO_PLUTO_DISTANCE, zoom * SUN_TO_PLUTO_DISTANCE), 
            (-zoom * SUN_TO_PLUTO_DISTANCE, zoom * SUN_TO_PLUTO_DISTANCE), 
            (-zoom * SUN_TO_PLUTO_DISTANCE, zoom * SUN_TO_PLUTO_DISTANCE))

    sim.create_animation()
    sim.run_animation()
