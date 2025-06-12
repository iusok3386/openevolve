from enum import Enum, auto
import collections
import random
from copy import deepcopy
from collections import deque
from dataclasses import dataclass

from os import environ

environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

# --- Pygame constants ---
SCREEN_WIDTH, SCREEN_HEIGHT = 480, 480
GRID_SIZE = 40
GRID_WIDTH, GRID_HEIGHT = SCREEN_WIDTH // GRID_SIZE, SCREEN_HEIGHT // GRID_SIZE
BLACK, GREEN, LIME_GREEN, RED, GRAY = (
    (0, 0, 0),
    (0, 150, 0),
    (50, 205, 50),
    (200, 0, 0),
    (50, 50, 50),
)


class SnakeGame:
    def __init__(self, width=12, height=12, num_obstacles=5, max_steps=250, visualize=False):
        self.width = width
        self.height = height
        self.num_obstacles = num_obstacles
        self.max_steps = max_steps
        self.reset()

        self.visualize_enabled = visualize

        self.pygame = None  # Default to None

        if visualize:
            # Attempt to import pygame (only needed for visualization)
            try:
                import pygame

                self.pygame = pygame
            except ImportError:
                print("Pygame is not installed. Skipping visualization.")
                self.visualize_enabled = False

        if self.visualize_enabled:
            self.pygame.init()
            self.screen = self.pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
            self.pygame.display.set_caption("Live AI Evaluation")
            self.clock = self.pygame.time.Clock()

    def reset(self):
        self.snake_body = collections.deque([(self.width // 2, self.height // 2)])
        self.snake_direction = (0, -1)  # Initially moving up

        regenerate_obstacles_count = 0
        self.apple_pos = None
        while self.apple_pos == None:
            regenerate_obstacles_count += 1
            self.obstacles = self._generate_obstacles()
            self.apple_pos = self._generate_apple()
            if regenerate_obstacles_count > 100:
                break
        self.score = 0
        self.steps = 0
        self.game_over_reason = None

    @property
    def game_over(self):
        """Returns True if the game is over, False otherwise."""
        return self.game_over_reason is not None

    def _generate_obstacles(self):
        obstacles = set()
        while len(obstacles) < self.num_obstacles:
            pos = (random.randint(0, self.width - 1), random.randint(0, self.height - 1))
            if pos not in self.snake_body:
                obstacles.add(pos)
        return obstacles

    def _generate_apple(self):
        pos = (random.randint(0, self.width - 1), random.randint(0, self.height - 1))
        original_pos = (pos[0], pos[1])
        while True:
            if self._check_collision(pos, self.snake_body) == None and self._is_safe_apple_location(
                pos
            ):
                return pos

            # Collision or deadlock position
            # Move the apple next to it
            pos = (pos[0] + 1, pos[1])
            if pos[0] >= self.width:
                pos = (0, pos[1] + 1)
            if pos[1] >= self.height:
                pos = (0, 0)

            if pos == original_pos:
                return None

    def _is_safe_apple_location(self, apple_location):
        # Step 1: Reachability checks
        path_to_apple = self._bfs(
            start=self.snake_body[0], end=apple_location, snake_body=deque(self.snake_body[0])
        )
        if not path_to_apple:
            return False  # Cannot reach apple

        # Step 2: Check for survival after eating
        future_snake_body = deque()
        step_count = 0
        # Cut the snake from end to start
        for step in deepcopy(self.snake_body):
            step_count += 1
            if step_count > len(path_to_apple):
                break
            future_snake_tail = step
            future_snake_body.append(step)

        future_snake_body.append((future_snake_tail[0] + 1, future_snake_tail[1]))

        self._step_snake(future_snake_body, path_to_apple)

        path_to_tail = self._bfs(
            start=apple_location, end=self.snake_body[0], snake_body=future_snake_body
        )

        if not path_to_tail:
            return False  # Eating result in deadlock

        return True  # Safely placed

    def _step_snake(self, snake_body, steps):
        for step in steps:
            snake_body.appendleft(step)
            snake_body.pop()

    def step(self, direction):
        if self.game_over:
            return

        if self.visualize_enabled:
            # This is the most critical part to keep the window responsive.
            # It handles all OS events like mouse moves, key presses, and the quit signal.
            for event in self.pygame.event.get():
                if event.type == self.pygame.QUIT:
                    self.game_over_reason = "Timed out"
                    self.pygame.quit()
                    return

        self.snake_direction = direction
        head = self.snake_body[0]
        new_head = (head[0] + direction[0], head[1] + direction[1])

        # Collision checks
        game_over_reason = self._check_collision(new_head, self.snake_body)
        if game_over_reason != None:
            self.game_over_reason = game_over_reason
            if self.visualize_enabled:
                self.pygame.quit()
            return

        self.snake_body.appendleft(new_head)

        if new_head == self.apple_pos:
            self.score += 1
            self.apple_pos = self._generate_apple()
        else:
            self.snake_body.pop()

        self.steps += 1

        # No more place to put apple
        if self.apple_pos == None:
            # Game completely cleared
            self.game_over_reason = "Game completed!"
            if self.visualize_enabled:
                self.pygame.quit()
            return

        # To prevent infinite loops
        if self.steps > self.max_steps:
            self.game_over_reason = "Infinite loop"
            if self.visualize_enabled:
                self.pygame.quit()
            return

        if self.visualize_enabled:
            self._draw_game_pygame(self.screen)
            if self.steps < 300:
                self.clock.tick(60)  # 60 frames per second
            elif self.steps < 600:
                self.clock.tick(120)  # 120 frames per second
            elif self.steps < 1200:
                self.clock.tick(180)  # 180 frames per second
            else:
                self.clock.tick(240)  # 240 frames per second

    def _get_adjacent_cells(self, position):
        up = (position[0], position[1] - 1)
        down = (position[0], position[1] + 1)
        left = (position[0] - 1, position[1])
        right = (position[0] + 1, position[1])
        return [up, down, left, right]

    def _check_collision(self, cell, snake_body):
        if cell[0] < 0 or cell[0] >= self.width or cell[1] < 0 or cell[1] >= self.height:
            return "Hit wall"
        if cell in snake_body:
            return "Hit self"
        if cell in self.obstacles:
            return "Hit obstacle"
        return None

    def _bfs(self, start, end, snake_body: deque[tuple[int, int]]) -> list | None:
        queue = deque([(start, [start])])  # list of (current location, path)
        visited = {start}

        while queue:
            current_pos, path = queue.popleft()

            if current_pos == end:
                return path  # path found

            temp_snake_body = deepcopy(snake_body)
            if current_pos != start:
                self._step_snake(temp_snake_body, path)

            for next_pos in self._get_adjacent_cells(current_pos):

                if (
                    self._check_collision(next_pos, temp_snake_body) == None
                    and next_pos not in visited
                ):
                    visited.add(next_pos)
                    new_path = path + [next_pos]
                    queue.append((next_pos, new_path))

        return None  # path not found

    def _draw_game_pygame(self, screen):
        """Draws the game state on the Pygame screen."""
        screen.fill(BLACK)
        for segment in list(self.snake_body)[1:]:
            self.pygame.draw.rect(
                screen,
                GREEN,
                self.pygame.Rect(
                    segment[0] * GRID_SIZE, segment[1] * GRID_SIZE, GRID_SIZE, GRID_SIZE
                ),
            )
        head_rect = self.pygame.Rect(
            self.snake_body[0][0] * GRID_SIZE,
            self.snake_body[0][1] * GRID_SIZE,
            GRID_SIZE,
            GRID_SIZE,
        )
        self.pygame.draw.rect(screen, LIME_GREEN, head_rect)
        apple_rect = self.pygame.Rect(
            self.apple_pos[0] * GRID_SIZE, self.apple_pos[1] * GRID_SIZE, GRID_SIZE, GRID_SIZE
        )
        self.pygame.draw.rect(screen, RED, apple_rect)
        for obs in self.obstacles:
            self.pygame.draw.rect(
                screen,
                GRAY,
                self.pygame.Rect(obs[0] * GRID_SIZE, obs[1] * GRID_SIZE, GRID_SIZE, GRID_SIZE),
            )
        self.pygame.display.flip()


@dataclass
class SnakeGameResult:
    score: int
    steps: int
    game_over_reason: str
