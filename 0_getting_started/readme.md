# Getting Started with Solid Simulation

Free fall, spring, and mass-spring solid simulation with symplectic Euler time integration.

## Dependencies
```
pip install numpy scipy pygame
```

## Run
Free falling particle:
```
python simulator0.py
```
Hanging particle:
```
python simulator1.py
```
Hanging square:
```
python simulator2.py
```
Newton's method (the nonlinear solver that implicit/backward Euler time integration relies on):
```
python newton.py           # scalar root finding f(x)=x^2+3x-12 with tangent-line visualization
python newton.py spring    # implicit (backward) Euler spring: Newton solves one nonlinear system per time step
```