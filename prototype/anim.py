# See https://matplotlib.org/stable/api/animation_api.html for info on 
# matplotlib's animation scheme.

from sim_state import SimState

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.animation as animation
import matplotlib.axes


# Next steps:
#   This should all take place in a `simulation` class with a `state` attribute,
#   and attributes for all of the various simulation parameters. This will make 
#   it possible to pause, resume, load and save states, etc.


def config_fig(fig):
    # A `matplotlib.patches.Patch` is a 2D artist with a face color and an 
    # edge color.
    fig.patch.set_alpha(0.0)  # Make figure background transparent


def config_bg(ax: matplotlib.axes.Axes):
  # Remove ticks.
  ax.set_xticks([])
  ax.set_yticks([])
  ax.set_zticks([])
  # Remove labels.
  ax.set_xlabel('')
  ax.set_ylabel('')
  ax.set_zlabel('')
  ax.grid(False)
  # Make background transparent.
  ax.set_facecolor((1.0, 1.0, 1.0, 0.0))
  # Hide 3D panes.
  ax.xaxis.pane.fill = False
  ax.yaxis.pane.fill = False
  ax.zaxis.pane.fill = False
  # Set matplotlib.patches.Polygon (pane) edge colors.
  ax.xaxis.pane.set_edgecolor((1.0, 1.0, 1.0, 0.0))
  ax.yaxis.pane.set_edgecolor((1.0, 1.0, 1.0, 0.0))
  ax.zaxis.pane.set_edgecolor((1.0, 1.0, 1.0, 0.0))
  # Hide axis lines.
  ax.xaxis.line.set_color((1.0, 1.0, 1.0, 0.0))
  ax.yaxis.line.set_color((1.0, 1.0, 1.0, 0.0))
  ax.zaxis.line.set_color((1.0, 1.0, 1.0, 0.0))


def config_plot_limits(ax, xlim, ylim, zlim, origin=(0,0,0)):
    # Center the plot at `origin`
    ax.set(xlim3d=(xlim[0] + origin[0], xlim[1] + origin[0]))
    ax.set(ylim3d=(ylim[0] + origin[1], ylim[1] + origin[1]))
    ax.set(zlim3d=(zlim[0] + origin[2], zlim[1] + origin[2]))


def create_animation(fig, ax, dt, steps_per_update, state: SimState):
    # Initialize point objects.
    particles = state._particles
    num_points = len(particles)
    points = [ax.plot([], [], [], 'o', markersize=8)[0] for _ in range(num_points)]

    # Function to update the animation
    def update(frame):
        for i, data in enumerate(update_p(frame, dt, steps_per_update, particles)):
            points[i].set_data_3d(np.expand_dims(data, axis=1))
        return points

    return animation.FuncAnimation(
            fig, 
            update, 
            frames=np.arange(0, 10000), 
            interval=50, 
            blit=True, 
            repeat=True)


def run_animation(state):
    plt.show()
    # On exit, save state.
    state_writer = open("data/current_state.json", "w")
    state_writer.write(state.to_json())

def step(t, dt, steps_per_update, particles):
    for i in range(len(particles)):
        # Compute net force between each particle pair.
        df = np.zeros((3,))
        for j in range(len(particles)):
            if j == i:
                continue
            df += particles[i].net_force_from(particles[j], t)

        particles[i].update_props(df, dt / steps_per_update)

# Outputted update.
def update_p(t, dt, steps_per_update, particles):
    for _ in range(steps_per_update):
        # Inner update.
        step(t, dt, steps_per_update, particles)
    for particle in particles:
        yield particle.get("pos")
