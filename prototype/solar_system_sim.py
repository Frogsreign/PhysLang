# Example simulation. Simulates the planets' orbits about the sun.

import forces
import update_rules
from particle import Particle
from anim import *
from sim_state import SimState
import compile2

import json
import numpy as np

SUN_TO_PLUTO_DISTANCE = 59064e8


def decode_planet(obj: dict):
    planet = Particle(obj["name"])
    # Forces
    test_case_reader = open("compile2_testcases.json", "r")
    tree = json.JSONDecoder().decode(test_case_reader.read())
    
    gravx = tree["gravity-x"]["func"]
    gravy = tree["gravity-y"]["func"]
    gravz = tree["gravity-z"]["func"]

    _, gxfunc = compile2.compile_tree(gravx, old_variables=["obj1", "obj2"], func_name="gravx")
    _, gyfunc = compile2.compile_tree(gravy, old_variables=["obj1", "obj2"], func_name="gravy")
    _, gzfunc = compile2.compile_tree(gravz, old_variables=["obj1", "obj2"], func_name="gravz")


    planet.add_force("gravity", forces.f_grav)
    # Update rules
    planet.add_update_rule("pos_update", update_rules.pos_update)
    planet.add_update_rule("vel_update", update_rules.vel_update)
    planet.add_update_rule("acc_update", update_rules.acc_update)
    # Properties
    for prop_name in ("mass", "pos", "vel", "acc"):
        prop_val = obj["properties"][prop_name]
        if isinstance(prop_val, list):
            # 1. Types need to be decided during compilation.
            # 2. Integer/fp overflow needs to be dealt with during runtime. 
            #    Bad things happen when distances become negative.
            prop_val = np.array(prop_val, dtype=np.float32) # FIXME
        planet.set(prop_name, prop_val)
    return planet

def create_solar_system():
    planets_json_file = open("data/solar_system.json", "r")
    objs = json.JSONDecoder().decode(planets_json_file.read())
    planets_json_file.close()
    planets = [decode_planet(obj) for obj in objs["particles"]]

    force_trees = objs["forces"]
    update_rule_trees = objs["update-rules"]

    state = SimState(planets, forces=force_trees, update_rules=update_rule_trees)
    return state

if __name__ == '__main__':
    # Simulation objects (particles).
    state = create_solar_system()

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
