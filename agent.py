# agent.py
import random
from collections import deque


class SimpleReflexAgent:
    """
    Step 1.2: Simple Reflex Agent
    Implements Condition-Action rules (IF-THEN logic) based purely on immediate percepts.
    Does NOT maintain any internal state or memory across steps.
    """

    def __init__(self):
        pass  # Strictly no history or memory initialized

    def sense_and_act(self, percept: dict) -> str:
        # Condition-Action Rule 1: IF food_here THEN suck (collect food)
        if percept.get('food_here'):
            return 'Suck'
        # Condition-Action Rule 2: IF wall_ahead THEN turn / change direction
        elif percept.get('wall_ahead'):
            return 'Right'
        # Condition-Action Rule 3: ELSE move forward / step Up
        else:
            return 'Up'


class ModelBasedAgent:
    """
    Step 1.3: Model-Based Agent
    Maintains an internal memory state (visited locations, consecutive wall hits, and orientation tracker)
    to update its Transition and Sensor models and escape infinite loops.
    """

    def __init__(self):
        self.directions = ['Up', 'Right', 'Down', 'Left']
        self.dir_index = 0  # Start facing 'Up'
        self.pos = (0, 0)    # Internal coordinate tracker (relative position)
        self.visited = {self.pos: 1}  # Memory: map of relative coordinates to visit counts
        self.last_action = None
        self.consecutive_wall_hits = 0

    def sense_and_act(self, percept: dict) -> str:
        # Update Sensor Model / Internal state based on percepts
        wall_ahead = percept.get('wall_ahead', False)
        food_here = percept.get('food_here', False)

        if wall_ahead:
            self.consecutive_wall_hits += 1
        else:
            self.consecutive_wall_hits = 0

        # Rule 1: IF food_here THEN suck
        if food_here:
            action = 'Suck'
            self.last_action = action
            return action

        # Rule 2: IF wall_ahead OR stuck in a wall loop THEN use internal state to pick alternative direction
        if wall_ahead or self.consecutive_wall_hits > 0:
            # Change direction in memory when hitting walls to break infinite loops
            self.dir_index = (self.dir_index + max(1, self.consecutive_wall_hits)) % len(self.directions)
            action = self.directions[self.dir_index]
        else:
            # Rule 3: Memory-Guided Movement
            # Check if the target position in the current facing direction has been visited repeatedly
            dx, dy = [(0, 1), (1, 0), (0, -1), (-1, 0)][self.dir_index]
            target_pos = (self.pos[0] + dx, self.pos[1] + dy)

            # If current path is heavily visited (loop detected), query memory to turn right/left
            if self.visited.get(target_pos, 0) >= 2:
                self.dir_index = (self.dir_index + 1) % len(self.directions)
                action = self.directions[self.dir_index]
            else:
                action = self.directions[self.dir_index]

        # Transition Model Update: record position change in memory
        if action in self.directions:
            self.dir_index = self.directions.index(action)
            dx, dy = [(0, 1), (1, 0), (0, -1), (-1, 0)][self.dir_index]
            if not wall_ahead:
                self.pos = (self.pos[0] + dx, self.pos[1] + dy)
                self.visited[self.pos] = self.visited.get(self.pos, 0) + 1

        self.last_action = action
        return action


class GreedyGridAgent:
    """A simple agent that tries to move around systematically to clear the grid."""

    def __init__(self):
        self.actions_pool = ['Up', 'Down', 'Left', 'Right']

    def sense_and_act(self, percept: dict) -> str:
        if percept.get('food_here'):
            return 'Suck'
        return random.choice(self.actions_pool)


class SearchAgent:
    """
    Problem-Solving Agent using Breadth-First Search (BFS) for navigation.
    """

    def bfs_search(self, start_pos, goal_pos, walls, grid_size):
        width, height = grid_size
        walls_set = set(walls)
        queue = deque([(start_pos, [])])
        visited = {start_pos}

        moves = [
            ((0, 1), 'Up'),
            ((0, -1), 'Down'),
            ((-1, 0), 'Left'),
            ((1, 0), 'Right')
        ]

        while queue:
            (cx, cy), path = queue.popleft()
            if (cx, cy) == goal_pos:
                return path

            for (dx, dy), action_name in moves:
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < width and 0 <= ny < height and (nx, ny) not in walls_set:
                    if (nx, ny) not in visited:
                        visited.add((nx, ny))
                        queue.append(((nx, ny), path + [action_name]))

        return None