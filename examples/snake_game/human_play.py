# This script allows a human to play the Snake game manually.

import pygame
import sys
import time
import importlib

# Attempt to import SnakeGame Class
spec = importlib.util.spec_from_file_location(
    "game_logic", r"F:\openevolve\examples\snake_game\game_logic.py"
)
game_logic = importlib.util.module_from_spec(spec)
spec.loader.exec_module(game_logic)

# --- Constants ---
SCREEN_WIDTH = 480
SCREEN_HEIGHT = 480
GRID_SIZE = 40
GRID_WIDTH = SCREEN_WIDTH // GRID_SIZE
GRID_HEIGHT = SCREEN_HEIGHT // GRID_SIZE
# GAME_SPEED is no longer needed as the game is turn-based.

# --- Colors (RGB) ---
WHITE = (255, 255, 255)
GREEN = (0, 150, 0)
LIME_GREEN = (50, 205, 50)
RED = (200, 0, 0)
GRAY = (50, 50, 50)
BLACK = (0, 0, 0)
BLUE = (0, 0, 200)


def draw_game(screen, game):
    """Draws the current game state on the Pygame screen."""
    screen.fill(BLACK)

    # Draw snake body
    for segment in list(game.snake_body)[1:]:
        rect = pygame.Rect(segment[0] * GRID_SIZE, segment[1] * GRID_SIZE, GRID_SIZE, GRID_SIZE)
        pygame.draw.rect(screen, GREEN, rect)
        pygame.draw.rect(screen, LIME_GREEN, rect, 3)

    # Draw snake head
    head = game.snake_body[0]
    head_rect = pygame.Rect(head[0] * GRID_SIZE, head[1] * GRID_SIZE, GRID_SIZE, GRID_SIZE)
    pygame.draw.rect(screen, LIME_GREEN, head_rect)

    # Draw apple
    apple_rect = pygame.Rect(
        game.apple_pos[0] * GRID_SIZE, game.apple_pos[1] * GRID_SIZE, GRID_SIZE, GRID_SIZE
    )
    pygame.draw.rect(screen, RED, apple_rect)

    # Draw obstacles
    for obs in game.obstacles:
        obs_rect = pygame.Rect(obs[0] * GRID_SIZE, obs[1] * GRID_SIZE, GRID_SIZE, GRID_SIZE)
        pygame.draw.rect(screen, GRAY, obs_rect)

    # Display score
    font = pygame.font.Font(None, 36)
    score_text = font.render(f"Score: {game.score}", True, WHITE)
    screen.blit(score_text, (10, 10))

    pygame.display.flip()


def main():
    """Main function to run the human-playable game."""
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Human Player - Snake (Turn-Based)")
    clock = pygame.time.Clock()

    # Create a game instance
    game = game_logic.SnakeGame(num_obstacles=120, max_steps=3000)

    while not game.game_over:
        draw_game(screen, game)
        # --- Handle human input ---
        # The game will now wait here for the user to press a key.
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # Process game logic ONLY when a key is pressed.
            if event.type == pygame.KEYDOWN:
                current_direction = game.snake_direction
                next_direction = None  # Assume no valid move initially

                # UP
                if event.key == pygame.K_UP and current_direction != (0, 1):
                    next_direction = (0, -1)
                # DOWN
                elif event.key == pygame.K_DOWN and current_direction != (0, -1):
                    next_direction = (0, 1)
                # LEFT
                elif event.key == pygame.K_LEFT and current_direction != (1, 0):
                    next_direction = (-1, 0)
                # RIGHT
                elif event.key == pygame.K_RIGHT and current_direction != (-1, 0):
                    next_direction = (1, 0)

                if next_direction:
                    # If a valid direction key was pressed, update the game state.
                    head = game.snake_body[0]
                    new_head = (head[0] + next_direction[0], head[1] + next_direction[1])
                    if game._check_collision(new_head, game.snake_body) == None:
                        game.step(next_direction)

        # Limit the loop speed slightly to prevent high CPU usage while idle.
        clock.tick(60)

    # --- Game Over Screen ---
    font = pygame.font.Font(None, 74)
    text = font.render("GAME OVER: " + game.game_over_reason, True, RED)
    text_rect = text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 50))
    screen.blit(text, text_rect)

    font = pygame.font.Font(None, 50)
    score_text = font.render(f"Final Score: {game.score}", True, WHITE)
    score_rect = score_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 20))
    screen.blit(score_text, score_rect)

    pygame.display.flip()

    # Wait for a few seconds before closing
    time.sleep(4)
    pygame.quit()


if __name__ == "__main__":
    main()
