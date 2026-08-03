# visual_grid_game.py
import random
import tkinter as tk


class VisualGridHuntGame:
    """A flexible Pacman-style grid environment with support for configurable opponents and larger scales."""

    def __init__(self, width=10, height=10, num_food=10, num_opponents=2, custom_walls=None):
        self.width = width
        self.height = height
        self.agent_pos = [0, 0]  # Starting position (x, y)
        self.facing = "Right"
        self.last_move_succeeded = True

        if custom_walls is not None:
            self.walls = set(custom_walls)
        else:
            # Standard scattered walls layout for a clean 10x10 grid
            self.walls = {(2, 2), (2, 3), (5, 5), (6, 5), (3, 7)}

        # Dynamically generate random food positions avoiding walls and agent start
        self.food_positions = set()
        while len(self.food_positions) < num_food:
            fx = random.randint(0, self.width - 1)
            fy = random.randint(0, self.height - 1)
            pos_tuple = (fx, fy)
            if pos_tuple != (0, 0) and pos_tuple not in self.walls:
                self.food_positions.add(pos_tuple)

        # Generate adversarial opponents
        self.opponents = []
        while len(self.opponents) < num_opponents:
            ox = random.randint(0, self.width - 1)
            oy = random.randint(0, self.height - 1)
            op_pos = [ox, oy]
            if tuple(op_pos) != (0, 0) and tuple(op_pos) not in self.walls and tuple(op_pos) not in self.food_positions:
                self.opponents.append(op_pos)

        # Generate toxic traps safely avoiding position (0, 0), walls, and food
        self.toxic_traps = set()
        num_traps = 4
        while len(self.toxic_traps) < num_traps:
            tx = random.randint(0, self.width - 1)
            ty = random.randint(0, self.height - 1)
            pos_tuple = (tx, ty)
            if pos_tuple != (0, 0) and pos_tuple not in self.walls and pos_tuple not in self.food_positions and pos_tuple not in [tuple(op) for op in self.opponents]:
                self.toxic_traps.add(pos_tuple)

        self.score = 0
        self.steps = 0
        self.collision = False

    def get_percept(self) -> dict:
        """
        Step 1.1: Partial Observability
        Returns ONLY local booleans and last move status.
        No global coordinates (agent_pos), score, or opponent lists are exposed to the agent!
        """
        x, y = self.agent_pos

        # Find the cell directly ahead of the agent
        if self.facing == "Up":
            ahead_position = (x, y + 1)
        elif self.facing == "Down":
            ahead_position = (x, y - 1)
        elif self.facing == "Left":
            ahead_position = (x - 1, y)
        else:  # Right
            ahead_position = (x + 1, y)

        ahead_x, ahead_y = ahead_position

        # Check whether the cell ahead is outside the grid
        outside_grid = (
            ahead_x < 0
            or ahead_x >= self.width
            or ahead_y < 0
            or ahead_y >= self.height
        )

        # A boundary or wall counts as wall_ahead
        wall_ahead = outside_grid or ahead_position in self.walls

        return {
            "wall_ahead": wall_ahead,
            "food_here": tuple(self.agent_pos) in self.food_positions,
            "toxin_here": tuple(self.agent_pos) in self.toxic_traps,
            "last_move_succeeded": self.last_move_succeeded
        }

    def execute_action(self, action: str):
        self.steps += 1
        self.collision = False

        # Action: collect food from the current cell
        if action in ["Suck", "suck"]:
            current_position = tuple(self.agent_pos)
            if current_position in self.food_positions:
                self.food_positions.remove(current_position)
                self.score += 20
            return

        # Action: turn left without changing position
        if action == "TurnLeft":
            left_turn = {
                "Up": "Left",
                "Left": "Down",
                "Down": "Right",
                "Right": "Up"
            }
            self.facing = left_turn[self.facing]
            return

        # Action: turn right without changing position
        if action == "TurnRight":
            right_turn = {
                "Up": "Right",
                "Right": "Down",
                "Down": "Left",
                "Left": "Up"
            }
            self.facing = right_turn[self.facing]
            return

        # Action: move one cell forward
        if action == "MoveForward" or action in ["Up", "Down", "Left", "Right"]:
            if action in ["Up", "Down", "Left", "Right"]:
                self.facing = action

            new_pos = list(self.agent_pos)

            if self.facing == "Up":
                new_pos[1] += 1
            elif self.facing == "Down":
                new_pos[1] -= 1
            elif self.facing == "Left":
                new_pos[0] -= 1
            elif self.facing == "Right":
                new_pos[0] += 1

            new_x, new_y = new_pos

            outside_grid = (
                new_x < 0
                or new_x >= self.width
                or new_y < 0
                or new_y >= self.height
            )

            # Prevent movement through boundaries and walls
            if outside_grid or tuple(new_pos) in self.walls:
                self.score -= 5
                self.last_move_succeeded = False
            else:
                self.agent_pos = new_pos
                self.last_move_succeeded = True

            current_position = tuple(self.agent_pos)

            # Trap penalty
            if current_position in self.toxic_traps:
                self.score -= 15

            # Move opponents
            for opponent in self.opponents:
                move = random.choice(["Up", "Down", "Left", "Right", "Stay"])
                if move == "Up" and opponent[1] < self.height - 1:
                    opponent[1] += 1
                elif move == "Down" and opponent[1] > 0:
                    opponent[1] -= 1
                elif move == "Left" and opponent[0] > 0:
                    opponent[0] -= 1
                elif move == "Right" and opponent[0] < self.width - 1:
                    opponent[0] += 1

                if opponent == self.agent_pos:
                    self.score -= 50
                    self.collision = True

    def is_done(self) -> bool:
        return len(self.food_positions) == 0 or self.steps >= 60 or self.collision


class SimpleReflexAgent:
    """
    A memoryless agent that chooses actions using only the current percept.
    """

    def sense_and_act(self, percept: dict) -> str:
        # IF food is in the current cell, THEN collect it
        if percept.get("food_here"):
            return "Suck"

        # IF there is a wall ahead, THEN turn left
        if percept.get("wall_ahead"):
            return "TurnLeft"

        # OTHERWISE move forward
        return "MoveForward"


class ModelBasedAgent:
    """
    A model-based agent that remembers its relative position,
    facing direction, visited cells, and previous action.
    """

    def __init__(self):
        # Internal model of the agent's position.
        # This is relative, so the agent still does not receive
        # the real environment coordinates from its sensors.
        self.relative_position = (0, 0)

        # Internal estimate of the direction it is facing
        self.facing = "Right"

        # Memory of visited cells
        self.visited_cells = {(0, 0)}

        # Remember the previous action
        self.last_action = None

    def _turn_left(self):
        left_turns = {
            "Up": "Left",
            "Left": "Down",
            "Down": "Right",
            "Right": "Up"
        }
        self.facing = left_turns[self.facing]

    def _turn_right(self):
        right_turns = {
            "Up": "Right",
            "Right": "Down",
            "Down": "Left",
            "Left": "Up"
        }
        self.facing = right_turns[self.facing]

    def _position_ahead(self):
        x, y = self.relative_position

        if self.facing == "Up":
            return x, y + 1
        if self.facing == "Down":
            return x, y - 1
        if self.facing == "Left":
            return x - 1, y
        return x + 1, y

    def _position_left(self):
        x, y = self.relative_position

        if self.facing == "Up":
            return x - 1, y
        if self.facing == "Down":
            return x + 1, y
        if self.facing == "Left":
            return x, y - 1
        return x, y + 1

    def _position_right(self):
        x, y = self.relative_position

        if self.facing == "Up":
            return x + 1, y
        if self.facing == "Down":
            return x - 1, y
        if self.facing == "Left":
            return x, y + 1
        return x, y - 1

    def _update_internal_state(self, percept):
        """
        Update the internal state using the previous action
        and the newest percept.
        """
        # Transition / action model:
        # If the previous action was MoveForward and the move succeeded, update estimated position.
        if (
            self.last_action == "MoveForward"
            and percept.get("last_move_succeeded", True)
        ):
            self.relative_position = self._position_ahead()
            self.visited_cells.add(self.relative_position)

        elif self.last_action == "TurnLeft":
            self._turn_left()

        elif self.last_action == "TurnRight":
            self._turn_right()

    def sense_and_act(self, percept: dict) -> str:
        # First update the internal model
        self._update_internal_state(percept)

        # Condition-action rule 1: IF food is here, THEN collect it
        if percept.get("food_here"):
            action = "Suck"

        else:
            ahead_position = self._position_ahead()
            left_position = self._position_left()
            right_position = self._position_right()

            ahead_is_visited = ahead_position in self.visited_cells
            left_is_visited = left_position in self.visited_cells
            right_is_visited = right_position in self.visited_cells

            # IF wall ahead and left has already been visited, THEN try turning right
            if percept.get("wall_ahead") and left_is_visited:
                action = "TurnRight"

            # IF wall ahead, THEN turn left
            elif percept.get("wall_ahead"):
                action = "TurnLeft"

            # IF the cell ahead has already been visited, prefer an unvisited side
            elif ahead_is_visited and not left_is_visited:
                action = "TurnLeft"

            elif ahead_is_visited and not right_is_visited:
                action = "TurnRight"

            # Otherwise move forward
            else:
                action = "MoveForward"

        self.last_action = action
        return action


class GridGameGUI:
    """Tkinter wrapper that dynamically scales cell sizes to keep larger grids on screen."""

    def __init__(self, root, width=10, height=10, num_food=10, num_opponents=2, walls=None):
        self.root = root
        self.root.title("IT3012 - Scalable Multi-Agent Grid Hunt")

        self.env = VisualGridHuntGame(width=width, height=height, num_food=num_food, num_opponents=num_opponents,
                                      custom_walls=walls)
        self.agent = ModelBasedAgent()

        # Dynamically calculate cell size so the total canvas fits nicely within a 500x500 window ceiling
        max_canvas_dim = 500
        self.cell_size = max(20, min(max_canvas_dim // self.env.width, max_canvas_dim // self.env.height))

        canvas_w = self.env.width * self.cell_size
        canvas_h = self.env.height * self.cell_size

        self.canvas = tk.Canvas(root, width=canvas_w, height=canvas_h, bg="white")
        self.canvas.pack(pady=10)

        self.label = tk.Label(root, text="Score: 0 | Steps: 0", font=("Arial", 11, "bold"))
        self.label.pack(pady=5)

        self.btn = tk.Button(root, text="Start Simulation", command=self.run_loop, font=("Arial", 11, "bold"), bg="#000066",
                             fg="white", padx=10, pady=4)
        self.btn.pack(pady=5)

        self.draw_grid()

    def draw_grid(self):
        self.canvas.delete("all")

        for x in range(self.env.width):
            for y in range(self.env.height):
                x1 = x * self.cell_size
                y1 = (self.env.height - 1 - y) * self.cell_size
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size

                color = "#f1f5f9" if (x, y) not in self.env.walls else "#64748b"
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="#cbd5e1")

                # Only draw text if cell is large enough
                if self.cell_size >= 35 and (x, y) in self.env.walls:
                    self.canvas.create_text(x1 + self.cell_size / 2, y1 + self.cell_size / 2, text="W", fill="white",
                                            font=("Arial", 9, "bold"))

        for fx, fy in self.env.food_positions:
            offset = self.cell_size * 0.25
            x1 = fx * self.cell_size + offset
            y1 = (self.env.height - 1 - fy) * self.cell_size + offset
            self.canvas.create_oval(x1, y1, x1 + self.cell_size * 0.5, y1 + self.cell_size * 0.5, fill="#f59e0b",
                                    outline="#d97706")

        for ox, oy in self.env.opponents:
            offset = self.cell_size * 0.2
            x1 = ox * self.cell_size + offset
            y1 = (self.env.height - 1 - oy) * self.cell_size + offset
            self.canvas.create_rectangle(x1, y1, x1 + self.cell_size * 0.6, y1 + self.cell_size * 0.6, fill="#990000",
                                         outline="#7a0000")

        # Render toxic traps as custom purple diamond shapes
        for tx, ty in self.env.toxic_traps:
            offset = self.cell_size * 0.2
            x1 = tx * self.cell_size + offset
            y1 = (self.env.height - 1 - ty) * self.cell_size + offset
            cx = x1 + self.cell_size * 0.3
            cy = y1 + self.cell_size * 0.3
            self.canvas.create_polygon(cx, y1, x1 + self.cell_size * 0.6, cy, cx, y1 + self.cell_size * 0.6, x1, cy,
                                       fill="#8b5cf6", outline="#6d28d9")

        ax, ay = self.env.agent_pos
        offset = self.cell_size * 0.15
        x1 = ax * self.cell_size + offset
        y1 = (self.env.height - 1 - ay) * self.cell_size + offset
        self.canvas.create_oval(x1, y1, x1 + self.cell_size * 0.7, y1 + self.cell_size * 0.7, fill="#000066",
                                outline="#1e3a8a")

    def run_loop(self):
        self.btn.config(state="disabled")

        def step():
            if not self.env.is_done():
                percept = self.env.get_percept()

                action = self.agent.sense_and_act(percept)

                self.env.execute_action(action)

                self.draw_grid()

                rel_pos = getattr(self.agent, "relative_position", "N/A")
                rel_facing = getattr(self.agent, "facing", "N/A")
                visited = getattr(self.agent, "visited_cells", set())

                self.label.config(
                    text=(
                        f"Score: {self.env.score} | "
                        f"Steps: {self.env.steps} | "
                        f"Facing: {self.env.facing} | "
                        f"Action: {action} | "
                        f"Visited: {len(visited)}"
                    )
                )

                print(
                    f"Percept: {percept} | "
                    f"Action: {action} | "
                    f"Environment Facing: {self.env.facing} | "
                    f"Internal Position: {rel_pos} | "
                    f"Internal Facing: {rel_facing} | "
                    f"Visited Cells: {visited}"
                )

                self.root.after(250, step)

            else:
                if self.env.collision:
                    end_text = f"Collision! Game Over! Final Score: {self.env.score}"
                else:
                    end_text = f"Finished! Final Score: {self.env.score}"

                self.label.config(text=end_text)
                self.btn.config(state="normal")

        step()


if __name__ == "__main__":
    root = tk.Tk()

    # Standard 10x10 grid layout with 10 food items and 2 opponents
    app = GridGameGUI(root, width=10, height=10, num_food=10, num_opponents=2)

    root.mainloop()