# Example simulation. Simulates the planets' orbits about the sun.

import forces
import update_rules
from particle import Particle
from anim import *
from sim_state import SimState

import json
import numpy as np

SCALE = 100

def decode_particle(obj: dict):
    particle = Particle(obj["name"])
    # Forces
    particle.add_force("gravity", forces.f_grav)
    particle.add_force("electromagnetism", forces.f_elec)
    # Update rules
    particle.add_update_rule("pos_update", update_rules.pos_update)
    particle.add_update_rule("vel_update", update_rules.vel_update)
    particle.add_update_rule("acc_update", update_rules.acc_update)
    # Properties
    for prop_name in ("mass", "pos", "vel", "acc"):
        prop_val = obj["properties"][prop_name]
        if isinstance(prop_val, list):
            prop_val = np.array(prop_val)
        particle.set(prop_name, prop_val)
    return particle

def create_solar_system():
    planets_json_file = open("data/coulomb.json", "r")
    objs = json.JSONDecoder().decode(planets_json_file.read())
    planets_json_file.close()
    return [decode_particle(obj) for obj in objs]

if __name__ == '__main__':
    # Simulation objects (particles).
    planets = create_solar_system()
    state = SimState(planets)

    # Simulation parameter (s).
    video_speed = 1
    zoom = 0.1

    # Create figure and 3D axis.
    sim = Simulation(dt=60 * 60 * 24 * video_speed, 
            steps_per_update=24 * video_speed, 
            state=state)

    # Setup background.
    sim.config_fig()
    sim.config_bg()
    sim.config_plot_limits(
            (-zoom * SCALE, zoom * SCALE), 
            (-zoom * SCALE, zoom * SCALE), 
            (-zoom * SCALE, zoom * SCALE))

    sim.create_animation()
    sim.run_animation()
