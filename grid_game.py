# grid_game.py
import random


class GridHuntGame:
    """A small Pacman-style grid environment (4x4) where an agent collects food."""

    def __init__(self, width=4, height=4):
        self.width = width
        self.height = height
        self.agent_pos = [0, 0]  # Starting position (x, y)
        self.agent_dir = 'Up'

        # Place food pellets and obstacles (walls) as tuples
        self.food_positions = {(1, 2), (2, 3), (3, 0), (2, 1)}
        self.walls = {(1, 1), (2, 2)}

        self.score = 0
        self.steps = 0

    def _is_wall_ahead((self) -> bool:
        x, y = self.agent_pos
        if self.agent_dir == 'Up':
            next_pos = (x, y + 1)
        elif self.agent_dir == 'Down':
            next_pos = (x, y - 1)
        elif self.agent_dir == 'Left':
            next_pos = (x - 1, y)
        elif self.agent_dir == 'Right':
            next_pos = (x + 1, y)
        else:
            next_pos = (x, y + 1)

        nx, ny = next_pos
        if nx < 0 or nx >= self.width or ny < 0 or ny >= self.height:
            return True
        return next_pos in self.walls

    def get_percept(self, agent=None) -> dict:
        return {
            'wall_ahead': self._is_wall_ahead(),
            'food_here': tuple(self.agent_pos) in self.food_positions,
            'agent_pos': list(self.agent_pos),
            'smells_food': tuple(self.agent_pos) in self.food_positions,
            'hit_wall': tuple(self.agent_pos) in self.walls,
            'score': self.score,
            'remaining_food': len(self.food_positions)
        }

    def execute_action(self, agent_or_action, action: str = None):
        act = action if action is not None else agent_or_action
        if not isinstance(act, str):
            act = 'Up'
        self.steps += 1
        new_pos = list(self.agent_pos)

        if act in ['Up', 'Down', 'Left', 'Right']:
            self.agent_dir = act
            if act == 'Up':
                new_pos[1] = min(self.height - 1, new_pos[1] + 1)
            elif act == 'Down':
                new_pos[1] = max(0, new_pos[1] - 1)
            elif act == 'Left':
                new_pos[0] = max(0, new_pos[0] - 1)
            elif act == 'Right':
                new_pos[0] = min(self.width - 1, new_pos[0] + 1)

        # Check collision with walls
        if tuple(new_pos) in self.walls:
            self.score -= 5  # Penalty for hitting a wall
        else:
            self.agent_pos = new_pos

        # Check if eating food
        tuple_pos = tuple(self.agent_pos)
        if tuple_pos in self.food_positions or act in ['Suck', 'suck']:
            if tuple_pos in self.food_positions:
                self.food_positions.remove(tuple_pos)
                self.score += 20  # Reward for eating food pellet

    def is_done(self) -> bool:
        return len(self.food_positions) == 0 or self.steps >= 20