import importlib

# Attempt to import SnakeGame Class
spec = importlib.util.spec_from_file_location(
    "game_logic", r"F:\openevolve\examples\snake_game\game_logic.py"
)
game_logic = importlib.util.module_from_spec(spec)
spec.loader.exec_module(game_logic)

# EVOLVE-BLOCK-START
# OpenEvolve will evolve the `decide_next_move` function within this block.


def decide_next_move(snake_body, snake_direction, apple_pos, obstacles, width, height):
    """
    Decides the snake's next move based on the current game state.

    Args:
        snake_body (collections.deque): A list of (x, y) coordinates for the snake's body parts. The head is at the front.
        snake_direction (tuple): The current direction of movement (dx, dy). e.g., (0, -1) is UP.
        apple_pos (tuple): The (x, y) coordinates of the apple.
        obstacles (set): A set of (x, y) coordinates for obstacles.
        width (int): The width of the board.
        height (int): The height of the board.

    Returns:
        tuple: The next direction of movement (dx, dy).
    """
    head = snake_body[0]
    possible_moves = [(0, -1), (0, 1), (-1, 0), (1, 0)]  # UP, DOWN, LEFT, RIGHT

    # Prohibit moving in the opposite direction of the current one (to avoid self-collision)
    if snake_direction in possible_moves:
        possible_moves.remove((-snake_direction[0], -snake_direction[1]))

    # Find the move that gets closer to the apple
    best_move = None
    min_dist = float("inf")

    for move in possible_moves:
        next_head = (head[0] + move[0], head[1] + move[1])
        dist = abs(next_head[0] - apple_pos[0]) + abs(next_head[1] - apple_pos[1])
        if dist < min_dist:
            min_dist = dist
            best_move = move

    # If no optimal move is found, choose a possible move randomly
    if not best_move:
        if possible_moves:
            best_move = possible_moves[0]
        else:  # If no moves are possible (should not happen, but as a fallback)
            return snake_direction

    return best_move


# EVOLVE-BLOCK-END


def run_game(game_logic_path, width, height, num_obstacles, max_steps, visualize):
    """Runs a single game simulation with visualization using Pygame."""

    spec = importlib.util.spec_from_file_location("game_logic", game_logic_path)
    game_logic = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(game_logic)

    game = game_logic.SnakeGame(
        width=width,
        height=height,
        num_obstacles=num_obstacles,
        max_steps=max_steps,
        visualize=visualize,
    )

    while not game.game_over:
        direction = decide_next_move(
            game.snake_body,
            game.snake_direction,
            game.apple_pos,
            game.obstacles,
            game.width,
            game.height,
        )
        game.step(direction)

    return {
        "score": game.score,
        "steps": game.steps,
        "game_over_reason": game.game_over_reason,
    }
