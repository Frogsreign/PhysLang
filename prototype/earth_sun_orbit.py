# Example simulation. Simulates the earth's orbit about the sun.

import forces
from particle import Particle

import numpy as np
import matplotlib.pyplot as plt
from anim import *

SUN_MASS = 1.989e30
EARTH_MASS = 5.972e24
EARTH_VELOCITY = 29784.8 # Tangential to its orbit with the sun
EARTH_SUN_DIST = 150e9

if __name__ == '__main__':
    # Create figure and 3D axis.
    fig = plt.figure()
    ax = fig.add_subplot(projection='3d')

    # Setup background.
    config_fig(fig)
    config_bg(ax)
    config_plot_limits(
            ax, 
            (-1.5 * EARTH_SUN_DIST, 1.5 * EARTH_SUN_DIST), 
            (-1.5 * EARTH_SUN_DIST, 1.5 * EARTH_SUN_DIST), 
            (-1.0 * EARTH_SUN_DIST, 1.0 * EARTH_SUN_DIST))

    # Simulation parameters.
    t0 = 0                  # Start at time t = 0
    dt = 60 * 60 * 24       # Update animation once per day
    steps_per_update = 24   # Update simulation once per hour

    Particle.add_force("gravity", forces.f_grav)

    earth = Particle()
    earth.set("mass", EARTH_MASS)
    earth.set("pos", np.array([EARTH_SUN_DIST, 0, 0]))
    earth.set("vel", np.array([0, EARTH_VELOCITY, 0]))
    earth.set("acc", np.array([0, 0, 0]))

    sun = Particle()
    sun.set("mass", SUN_MASS)
    sun.set("pos", np.array([0, 0, 0]))
    sun.set("vel", np.array([0, 0, 0]))
    sun.set("acc", np.array([0, 0, 0]))

    ani = create_animation(fig, ax, dt, steps_per_update, particles=[sun, earth])

    # Display the animation
    plt.show()
