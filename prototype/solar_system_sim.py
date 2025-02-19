# Example simulation. Simulates the planets' orbits about the sun.

import forces
import update_rules
from particle import Particle
from anim import *
from sim_state import SimState

import json
import numpy as np

SUN_TO_PLUTO_DISTANCE = 59064e8


def decode_planet(obj: dict):
    planet = Particle(obj["name"])
    # Forces
    planet.add_force("gravity", forces.f_grav)
    # Update rules
    planet.add_update_rule("pos_update", update_rules.pos_update)
    planet.add_update_rule("vel_update", update_rules.vel_update)
    planet.add_update_rule("acc_update", update_rules.acc_update)
    # Properties
    for prop_name in ("mass", "pos", "vel", "acc"):
        prop_val = obj["properties"][prop_name]
        if isinstance(prop_val, list):
            prop_val = np.array(prop_val)
        planet.set(prop_name, prop_val)
    return planet

def create_solar_system():
    planets_json_file = open("data/solar_system.json", "r")
    objs = json.JSONDecoder().decode(planets_json_file.read())
    planets_json_file.close()
    return [decode_planet(obj) for obj in objs]

if __name__ == '__main__':
    # Simulation objects (particles).
    planets = create_solar_system()
    state = SimState(planets)

    # Simulation parameter (s).
    video_speed = 10
    zoom = 0.1

    # Create figure and 3D axis.
    sim = Simulation(dt=60 * 60 * 24 * video_speed, 
            steps_per_update=24 * video_speed, 
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
