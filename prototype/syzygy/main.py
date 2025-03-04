from scanner import *
from parser import *
from interpreter import *
import json
import electron_sim
from particle import Particle
from anim import *
from sim_state import SimState

input = input("Please enter a command: ")
scan = Scanner(input)
tokens = scan.scan()
for token in tokens:
    print(token.toString())

parse = Parser(tokens)
statements = parse.parse()
for statement in statements:
    print(statement.toString())

interpret = Interpreter(statements)
interpret.run()

with open("sample.json", "w") as outfile:
    json.dump(interpret.dicts, outfile)


# Simulation objects (particles).
planets = electron_sim.create_solar_system("sample.json")
state = SimState(planets)

SCALE = 1000

# Simulation parameter (s).
video_speed = 1
zoom = 0.1

# Create figure and 3D axis.
sim = Simulation(dt=video_speed, 
        steps_per_update=video_speed, 
        state=state)

# Setup background.
sim.config_fig()
sim.config_bg()
sim.config_plot_limits_track()
sim.config_plot_limits(
        (-zoom * SCALE, zoom * SCALE), 
        (-zoom * SCALE, zoom * SCALE), 
        (-zoom * SCALE, zoom * SCALE))

sim.create_animation()
sim.run_animation()