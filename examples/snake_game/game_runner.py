import importlib
from time import sleep
import traceback
from turtle import heading


def run_game(
    max_obstacles,
    program_path,
    game_logic_path,
    result_queue,
):
    spec = importlib.util.spec_from_file_location("program", program_path)
    program = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(program)

    game_results = [None] * (max_obstacles + 1)

    for obstacles in range(max_obstacles + 1):
        if obstacles == max_obstacles:
            visualize = True
        else:
            visualize = False

        try:
            game_result = program.run_game(
                game_logic_path=game_logic_path,
                width=12,
                height=12,
                num_obstacles=obstacles,
                max_steps=3000,
                visualize=visualize,
            )

            if game_result["game_over_reason"] == "Game completed!":
                # Reward game completion
                game_result["score"] = 12 * 12

            game_results[obstacles] = game_result

        except Exception as e:
            error_msg = "".join(list(traceback.TracebackException.from_exception(e).format()))
            game_results[obstacles] = {
                "score": -100,
                "steps": 0,
                "game_over_reason": "Error has occured: " + error_msg,
            }

    result_queue.put(game_results)
