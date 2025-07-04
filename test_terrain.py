import sys
import os
sys.path.append('src')
from terrain.obstacle import FlowingTerrainObstacle
import pymunk

print('Testing terrain obstacle pymunk integration...')

# Create a simple test terrain with solid areas
height_field = [
    [0.5, 0.9, 0.5], 
    [0.5, 0.9, 0.5], 
    [0.5, 0.9, 0.5]
]

obstacle = FlowingTerrainObstacle(height_field, 0.7, 10, 10)
body = pymunk.Body(body_type=pymunk.Body.STATIC)

try:
    shapes = obstacle.get_pymunk_shapes(body)
    print(f'Generated {len(shapes)} shapes')
    for i, shape in enumerate(shapes):
        print(f'Shape {i}: {type(shape)}')
        if hasattr(shape, 'a') and hasattr(shape, 'b'):
            print(f'  Segment from {shape.a} to {shape.b}')
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
