#!/usr/bin/env python
"""
Debug del simplesso duale
"""

import sys
sys.path.insert(0, '.')

from core.models import SolverOptions
from core.solver import solve_problem


problem = """min
c = [2, 3]
A = [
  [1, 1],
  [2, 1]
]
signs = [">=", ">="]
b = [4, 5]
"""

options_dual = SolverOptions(method='dual_simplex', max_iterations=100)
result_dual = solve_problem(problem, options_dual)

print(f'Status: {result_dual.status}')
print(f'Message: {result_dual.message}')
