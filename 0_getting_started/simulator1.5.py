# Spring Simulation v2

import math
import numpy as np  # for vector data structure and computations
import pygame       # for visualization

# simulation setup
m1_0 = 2000                     # base mass1 of particle
m2_0 = 1000                     # base mass2 of particle
mass_period = 8.0               # period of the mass variation in seconds
mass_amp = 0.2                  # amplitude of the mass variation (fraction of base mass, keeps mass > 0)
m = np.diag([m1_0,m1_0,m2_0,m2_0])   # mass matrix of particles
x1 = np.array([-1.0, 0.0])    # position of particle1
x2 = np.array([1.0, 0.0])    # position of particle2
x = np.hstack([x1,x2])
v1 = np.array([0.0, 0.0])    # velocity of particle1
v2 = np.array([0.0, 0.0])    # velocity of particle2
v = np.hstack([v1,v2])

spring_rest_len = 1.5     # rest length of the spring ###
spring_stiffness = 1e3      # stiffness of the spring ###
h = 0.01                    # time step size in seconds

# visualization/rendering setup
pygame.init()
render_FPS = 100                    # number of frames to render per second
resolution = np.array([900, 900])   # visualization window size in pixels
offset = resolution / 2             # offset between window coordinates and simulated coordinates
scale = 200                         # scale between window coordinates and simulated coordinates
def screen_projection(x):           # convert simulated coordinates to window coordinates
    return [offset[0] + scale * x[0], resolution[1] - (offset[1] + scale * x[1])]
screen = pygame.display.set_mode(resolution)    # initialize visualizer

time_step = 0   # the number of the current time step
running = True  # flag indicating whether the simulation is still running
while running:
    # run until the user asks to quit
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    
    # update the time-varying masses, m(t) = m0 * (1 + amp * sin/cos(2*pi*t/T))
    # mass changes gently around its base value and always stays positive
    m1 = m1_0 * (1 + mass_amp * math.sin(2 * math.pi * time_step * h / mass_period))
    m2 = m2_0 * 2*(1 + mass_amp * math.cos(2 * math.pi * time_step * h / mass_period))
    m = np.diag([m1, m1, m2, m2])   # keep the mass matrix in sync with the varying masses

    # update the frame to display according to render_FPS
    if time_step % int(math.ceil((1.0 / render_FPS) / h)) == 0:
        # fill the background with white color, display simulation time at the top,
        # draw the spring segment, and render the particle as a circle:
        screen.fill((255, 255, 255))    
        pygame.display.set_caption('Current time: ' + f'{time_step * h: .2f}s')
        pygame.draw.aaline(screen, (0, 0, 255), screen_projection(x1), screen_projection(x2)) ###
        pygame.draw.circle(screen, (0, 0, 255), screen_projection(x1), m1/1e4 * scale)
        pygame.draw.circle(screen, (0, 0, 255), screen_projection(x2), m2/1e4 * scale)
        pygame.display.flip()   # flip the display
        pygame.time.wait(int(1000.0 / render_FPS))  # wait to render the next frame

    # step forward the simulation by updating particle velocity and position
    spring_cur_len = x2[0]-x1[0] ###
    spring_displacement = spring_cur_len - spring_rest_len ###
    spring_force_1 = spring_stiffness * spring_displacement  ###
    spring_force_2 = -spring_stiffness * spring_displacement  ###
    v1[0] += h * (spring_force_1 / m1)
    v2[0] += h * (spring_force_2 / m2)
    x1[0] += h * v1[0]
    x2[0] += h * v2[0]
    if x1[0]<=-2.25:
        v1[0]*=-1
    elif x2[0]>=2.25:
        v2[0]*=-1
    time_step += 1  # update time step counter