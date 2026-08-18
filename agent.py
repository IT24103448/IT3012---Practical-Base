# agent.py
import random
from collections import deque
import heapq


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
    def __init__(self):
        self.plan = []
        self.active_algo = 'UCS'

        # Internal position tracker.
        # Environment starts the agent at (0, 0).
        self.current_pos = (0, 0)

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

    def dfs_search(self, start_pos, goal_pos, walls, grid_size):
        width, height = grid_size
        walls_set = set(walls)

        stack = [(start_pos, [])]
        reached = {start_pos}

        moves = [
            ((0, 1), 'Up'),
            ((0, -1), 'Down'),
            ((-1, 0), 'Left'),
            ((1, 0), 'Right')
        ]

        while stack:
            (cx, cy), path = stack.pop()

            if (cx, cy) == goal_pos:
                return path

            for (dx, dy), action_name in moves:
                nx, ny = cx + dx, cy + dy
                next_pos = (nx, ny)

                if (
                    0 <= nx < width
                    and 0 <= ny < height
                    and next_pos not in walls_set
                    and next_pos not in reached
                ):
                    reached.add(next_pos)

                    stack.append(
                        (
                            next_pos,
                            path + [action_name]
                        )
                    )

        return None

    def ucs_search(self, start_pos, goal_pos, walls, grid_size):
        width, height = grid_size
        walls_set = set(walls)

        priority_queue = []
        heapq.heappush(
            priority_queue,
            (0, start_pos, [])
        )

        reached = {start_pos: 0}

        moves = [
            ((0, 1), 'Up'),
            ((0, -1), 'Down'),
            ((-1, 0), 'Left'),
            ((1, 0), 'Right')
        ]

        while priority_queue:
            cost, (cx, cy), path = heapq.heappop(priority_queue)

            if (cx, cy) == goal_pos:
                return path

            for (dx, dy), action_name in moves:
                nx, ny = cx + dx, cy + dy
                next_pos = (nx, ny)

                if (
                    0 <= nx < width
                    and 0 <= ny < height
                    and next_pos not in walls_set
                ):
                    new_cost = cost + 1

                    if (
                        next_pos not in reached
                        or new_cost < reached[next_pos]
                    ):
                        reached[next_pos] = new_cost

                        heapq.heappush(
                            priority_queue,
                            (
                                new_cost,
                                next_pos,
                                path + [action_name]
                            )
                        )

        return None

    def sense_and_act(self, percept: dict) -> str:
        # If the agent is currently standing on food, collect it first
        if percept.get('food_here'):
            return 'Suck'

        # If there is no existing plan, create a new one
        if not self.plan:
            all_food = percept.get('all_food', [])

            # No food remaining
            if not all_food:
                return 'Suck'

            grid_size = percept['grid_size']
            walls = percept['walls']
            current_x, current_y = self.current_pos

            # Find the closest food using Manhattan distance
            closest_food = min(
                all_food,
                key=lambda food: (
                    abs(food[0] - current_x)
                    + abs(food[1] - current_y)
                )
            )

            # Run the selected search algorithm
            if self.active_algo == 'BFS':
                self.plan = self.bfs_search(
                    self.current_pos,
                    closest_food,
                    walls,
                    grid_size
                )
            elif self.active_algo == 'DFS':
                self.plan = self.dfs_search(
                    self.current_pos,
                    closest_food,
                    walls,
                    grid_size
                )
            elif self.active_algo == 'UCS':
                self.plan = self.ucs_search(
                    self.current_pos,
                    closest_food,
                    walls,
                    grid_size
                )
            else:
                raise ValueError(
                    f"Unknown search algorithm: {self.active_algo}"
                )

            # Search failed to find a path
            if not self.plan:
                self.plan = []
                return 'Suck'

            print(
                f"\nAlgorithm: {self.active_algo}"
                f"\nStart: {self.current_pos}"
                f"\nGoal: {closest_food}"
                f"\nPlan: {self.plan}"
                f"\nPlan Length: {len(self.plan)}\n"
            )

        if not self.plan:
            return 'Suck'

        # Execute the first action in the stored plan
        action = self.plan.pop(0)

        # Update the SearchAgent's internal position
        x, y = self.current_pos
        if action == 'Up':
            self.current_pos = (x, y + 1)
        elif action == 'Down':
            self.current_pos = (x, y - 1)
        elif action == 'Left':
            self.current_pos = (x - 1, y)
        elif action == 'Right':
            self.current_pos = (x + 1, y)

        return action