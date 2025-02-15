# Example simulation. Simulates the planets' orbits about the sun.

import forces
from particle import Particle
from anim import *

import json
import numpy as np
import matplotlib.pyplot as plt

SUN_TO_PLUTO_DISTANCE = 59064e8

def newtonian_update(p: Particle, net_force, dt):
    """
    Update acceleration, velocity, then position.
    """
    p.set("acc", net_force / p.get("mass"))
    p.set("vel", p.get("vel") + (dt) * p.get("acc"))
    p.set("pos", p.get("pos") + (dt) * p.get("vel"))

def add_forces():
    # Check out what happens when you delete one of these lines. The simulation
    # still runs, but without the missing instruction.
    Particle.add_force_global("gravity", forces.f_grav)
    Particle.add_update_rule_global("pos_update", newtonian_update)

def decode_planet(obj: dict):
    planet = Particle(obj["name"])
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
    add_forces()
    planets = create_solar_system()
   
    # Simulation parameter (s).
    video_speed = 10
    zoom = 0.1

    # Create figure and 3D axis.
    fig = plt.figure()
    ax = fig.add_subplot(projection='3d')

    # Setup background.
    config_fig(fig)
    config_bg(ax)
    config_plot_limits(
            ax,
            (-zoom * SUN_TO_PLUTO_DISTANCE, zoom * SUN_TO_PLUTO_DISTANCE), 
            (-zoom * SUN_TO_PLUTO_DISTANCE, zoom * SUN_TO_PLUTO_DISTANCE), 
            (-zoom * SUN_TO_PLUTO_DISTANCE, zoom * SUN_TO_PLUTO_DISTANCE))

    ani = create_animation(
            fig, 
            ax, 
            dt=60 * 60 * 24 * video_speed, 
            steps_per_update=24 * video_speed, 
            particles=planets)

    plt.show()
