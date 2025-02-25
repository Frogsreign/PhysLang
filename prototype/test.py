import matplotlib.pyplot as plt
import numpy as np

import matplotlib.animation as animation


fig = plt.figure()
N = 10
r = np.random.randint(-100,100,2*N).reshape(N,2)
line, = plt.plot(r[:,0], r[:,1],'o')


lag_len = 10
history_x = np.zeros((N,lag_len))
history_y = np.zeros((N,lag_len))
trails = [plt.plot(hx,hy)[0] for hx,hy in zip(history_x,history_y)]

def update_frame(i):
    frame_num = i
    newdatax = r[:,0] + 100*np.random.rand(N)
    newdatay = r[:,1] + 100*np.random.rand(N)
    line.set_ydata(newdatay)
    line.set_xdata(newdatax)
    history_x[:,frame_num%lag_len] = newdatax
    history_y[:,frame_num%lag_len] = newdatay
    for hx,hy,ln_h in zip(history_x,history_y,trails):
         ln_h.set_xdata(hx)
         ln_h.set_ydata(hy)

    plt.title("At timestep: %d" %i)
    return (line,) + tuple(trails)

anim = animation.FuncAnimation(fig, update_frame, 
                           frames=100, interval=20)

plt.show()