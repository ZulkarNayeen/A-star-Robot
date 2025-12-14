import numpy as np
import heapq

def heuristic(a, b):
    """
    Calculates the Euclidean distance between two points a and b.
    """
    return np.sqrt((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2)

def astar(grid, start, goal):
    """
    Performs A* pathfinding on a binary grid.
    
    Args:
        grid (numpy.ndarray): 2D array where 0 is walkable and 1 is obstacle.
        start (tuple): (row, col) coordinates of the start point.
        goal (tuple): (row, col) coordinates of the goal point.
        
    Returns:
        tuple: (path, explored_nodes)
            - path: List of (row, col) tuples from start to goal (empty if no path).
            - explored_nodes: List of all nodes visited during search (for animation).
    """
    # 8-way movement: (row_change, col_change)
    neighbors = [(0,1), (0,-1), (1,0), (-1,0), (1,1), (1,-1), (-1,1), (-1,-1)]
    
    close_set = set()
    came_from = {}
    
    g_score = {start: 0}
    f_score = {start: heuristic(start, goal)}
    
    oheap = []
    heapq.heappush(oheap, (f_score[start], start))
    
    explored_nodes = []

    while oheap:
        current = heapq.heappop(oheap)[1]
        explored_nodes.append(current)

        if current == goal:
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            return path[::-1], explored_nodes

        close_set.add(current)
        
        for i, j in neighbors:
            neighbor = (current[0] + i, current[1] + j)
            
            # Check map boundaries
            if not (0 <= neighbor[0] < grid.shape[0] and 0 <= neighbor[1] < grid.shape[1]):
                continue
                
            # Check for obstacles (1 = blocked)
            if grid[neighbor[0]][neighbor[1]] == 1:
                continue
            
            # Diagonal move cost = sqrt(2), Straight = 1
            move_cost = np.sqrt(i**2 + j**2)
            tentative_g_score = g_score[current] + move_cost

            if neighbor in close_set and tentative_g_score >= g_score.get(neighbor, 0):
                continue
                
            if tentative_g_score < g_score.get(neighbor, float('inf')):
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g_score
                f_score[neighbor] = tentative_g_score + heuristic(neighbor, goal)
                heapq.heappush(oheap, (f_score[neighbor], neighbor))
                
    return [], explored_nodes
