import importlib.util
import multiprocessing
from queue import Queue
import time
from openevolve.evaluation_result import EvaluationResult
import os
import sys
import logging

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from game_runner import run_game


# Configure logging
logging.basicConfig(level=logging.WARNING, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def evaluate(program_path, num_rounds, max_obstacles):
    """
    Evaluates the generated AI program and returns a score.

    Returns:
        EvaluationResult: An object containing the following:
            - metrics (dict): A dictionary with the following keys:
                * "avg_score" (float): The average score across all simulations.
                * "combined_score" (float): The combined score, which is the same as avg_score.
            - artifacts (dict): A dictionary with the following keys:
                * "game_results" (str): A formatted string summarizing the results of the games.
                * "Game_over_reason meaning" (str): A description of possible game-over reasons.
    """

    # ========== import initial_program and game_logic
    spec = importlib.util.spec_from_file_location("program", program_path)
    program = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(program)

    if not hasattr(program, "run_game"):
        return EvaluationResult(
            metrics={"combined_score": -100},
            artifacts={"error_reason": "required function `run_game` is missing"},
        )  # Penalty if the required function is missing

    game_logic_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "game_logic.py")

    # ========== store game results
    total_score = 0
    all_game_results = [[None] * num_rounds for _ in range(max_obstacles + 1)]

    # ========== get number of CPUs (for multi processing)
    cpu_cores = os.cpu_count()
    if cpu_cores is None:
        cpu_cores = 1

    # ========== multi process sname_game
    processes = [None] * num_rounds
    remaining_processes = Queue()
    processes_started_at: list[float] = [-1] * num_rounds
    # Queue to receive the results from each child process
    result_queue: multiprocessing.Queue[list[dict[str, any]]] = multiprocessing.Queue()

    timeout = 6 + max_obstacles * 3 + 30

    for i in range(num_rounds):
        p = multiprocessing.Process(
            target=run_game,
            kwargs={
                "max_obstacles": max_obstacles,
                "program_path": program_path,
                "game_logic_path": game_logic_path,
                "result_queue": result_queue,
            },
        )
        processes[i] = p
        remaining_processes.put((i, p))

    last_stated_time = time.time()
    while True:
        active_process_count = 0
        for i in range(num_rounds):
            p = processes[i]
            if p.is_alive():
                active_process_count += 1

                elapsed_time = time.time() - processes_started_at[i]
                if elapsed_time > timeout:
                    logger.warning(f"run_game: Timed out after {timeout} seconds. Terminating...")
                else:
                    continue

                p.terminate()  # Kill the process
                p.join()  # Wait for the process to finish
                for i in range(num_rounds):
                    if all_game_results[0][i] == None:
                        for obstacles in range(max_obstacles + 1):
                            all_game_results[obstacles][i] = {
                                "score": 0,
                                "steps": 0,
                                "game_over_reason": "Timed out",
                            }
                        break

        if active_process_count < cpu_cores:
            for i in range(cpu_cores - active_process_count):
                if not remaining_processes.empty():
                    active_process_count += 1
                    i, p = remaining_processes.get()
                    processes_started_at[i] = time.time()
                    p.start()
                    # print(f"run_game: Process {i} started")
                    last_stated_time = processes_started_at[i]

        while not result_queue.empty():
            # Get result from queue
            game_results = result_queue.get()
            for i in range(num_rounds):
                if all_game_results[0][i] == None:
                    for obstacles in range(max_obstacles + 1):
                        total_score += game_results[obstacles]["score"]
                        all_game_results[obstacles][i] = game_results[obstacles]
                    break

        # All processes finished
        if active_process_count == 0 and remaining_processes.empty() and result_queue.empty():
            break

        # Should all processes to be terminated
        if time.time() - last_stated_time > timeout:
            for obstacles in range(max_obstacles + 1):
                for i in range(num_rounds):
                    if all_game_results[obstacles][i] == None:
                        all_game_results[obstacles][i] = {
                            "score": 0,
                            "steps": 0,
                            "game_over_reason": "Timed out",
                        }
                        break
            break

        time.sleep(0.2)  # Wait for a short time to free up the CPU

    avg_score = total_score / (num_rounds * (max_obstacles + 1))

    game_results_str = ""
    for obstacles in range(max_obstacles + 1):
        # truncate to 6 - 7 logs
        if (
            max_obstacles <= 5
            or obstacles % (max_obstacles // 5) == 0
            or obstacles == max_obstacles
        ):
            if obstacles == 0:
                game_results_str += "#### With no obstacles\n"
            if obstacles == 1:
                game_results_str += "\n#### With 1 obstacle\n"
            if obstacles >= 2:
                game_results_str += "\n#### With " + str(obstacles) + " obstacles\n"
            for i in range(num_rounds):
                # truncate to 4 - 5 logs
                if num_rounds <= 5 or i % (num_rounds // 5) == 0:
                    game_results_str += (
                        "* Score: "
                        + str(all_game_results[obstacles][i]["score"])
                        + ", Steps: "
                        + str(all_game_results[obstacles][i]["steps"])
                        + ", Game_over_reason: "
                        + str(all_game_results[obstacles][i]["game_over_reason"])
                        + "\n"
                    )

    game_over_reason_description = (
        "* Hit wall: Clash with wall (out of the field)\n"
        "* Hit self: Clash with yourself\n"
        "* Hit obstacle: Crash with obstacles\n"
        "* Infinite loop: Possibly travelling along the same route\n"
        "* Timed out: Calculation is taking too long\n"
        "* Game completed!: No more place to locate new apple (completely cleared!)"
    )

    # Normal mode: score is the average of multiple simulations
    return EvaluationResult(
        metrics={"avg_score": avg_score, "combined_score": avg_score},
        artifacts={
            "game_results": game_results_str,
            "Game_over_reason meaning": game_over_reason_description,
        },
    )


if __name__ == "__main__":
    evaluate(r"F:\openevolve\examples\snake_game\initial_program.py", 10, 20)


def evaluate_stage1(program_path):
    return evaluate(program_path, 5, 5)


def evaluate_stage2(program_path):
    return evaluate(program_path, 10, 20)
