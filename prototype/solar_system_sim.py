# Example simulation. Simulates the planets' orbits about the sun.

# Relative imports requires you run this script as follows:
#
#           python3 -m tests.solar_system_sim

import sys
print(sys.path)
import syzygy

from syzygy import anim
import syzygy.sim.sim_state
from syzygy import anim_native

from syzygy.sim.sim_state import SimState
import json

SUN_TO_PLUTO_DISTANCE = 59064e8


def create_solar_system():
    planets_json_file = open("tests/data/solar_system.json", "r")
    objs = json.JSONDecoder().decode(planets_json_file.read())
    planets_json_file.close()

    particles = objs["particles"]
    forces = objs["forces"]
    update_rules = objs["update-rules"]

    state = SimState(particles, forces, update_rules)
    return state


if __name__ == '__main__':
    # Simulation objects (particles).
    
    state = syzygy.sim.sim_state.create_simulation(open("tests/data/solar_system.txt", "r").read())

    # Simulation parameter (s).
    video_speed = 100
    zoom = 0.1

    # Create figure and 3D axis.
    sim = anim_native.Simulation(dt=60 * 60 * video_speed, 
            steps_per_update=video_speed, 
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
