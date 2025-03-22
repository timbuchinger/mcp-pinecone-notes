#!/usr/bin/env python3
import argparse
import subprocess
import sys
import time
from typing import List

# ANSI color codes for output formatting
HEADER = "\033[95m"
OKBLUE = "\033[94m"
OKGREEN = "\033[92m"
WARNING = "\033[93m"
FAIL = "\033[91m"
ENDC = "\033[0m"
BOLD = "\033[1m"


def run_command(
    cmd: List[str], description: str, show_output: bool = True
) -> tuple[int, float]:
    """Run a command and return its exit code and execution time."""
    print(f"\n{HEADER}{BOLD}Running {description}...{ENDC}")
    start_time = time.time()

    try:
        result = subprocess.run(
            cmd,
            check=False,  # Don't raise an exception on non-zero exit
            capture_output=True,
            text=True,
        )
        # Always show output for failed commands
        # Respect show_output flag for successful ones
        if result.returncode != 0 or show_output:
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(f"{FAIL}{result.stderr}{ENDC}", file=sys.stderr)

        execution_time = time.time() - start_time
        status = "✓" if result.returncode == 0 else "✗"
        color = OKGREEN if result.returncode == 0 else FAIL
        print(
            f"{color}{status} {description} "
            f"(took {execution_time:.2f}s, exit code: {result.returncode}){ENDC}"
        )
        return result.returncode, execution_time
    except Exception as e:
        print(f"{FAIL}Error running {description}: {e}{ENDC}", file=sys.stderr)
        return 1, time.time() - start_time


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run various linting and testing tools",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--ruff", action="store_true", help="Run ruff linter")
    parser.add_argument(
        "--black", action="store_true", help="Run black formatter in check mode"
    )
    parser.add_argument("--mypy", action="store_true", help="Run mypy type checker")
    parser.add_argument("--pytest", action="store_true", help="Run pytest")
    parser.add_argument(
        "--verbose", action="store_true", help="Show command output even on success"
    )
    return parser.parse_args()


def main() -> int:
    """Run the linting tools. Returns 0 on success, 1 on any failures."""
    args = parse_args()

    # If no specific tools are selected, run all of them
    run_all = not (args.ruff or args.black or args.mypy or args.pytest)
    exit_codes: List[int] = []
    total_time_start = time.time()

    if run_all or args.ruff:
        code, _ = run_command(
            ["ruff", "check", "."], "ruff check", show_output=args.verbose
        )
        exit_codes.append(code)

    if run_all or args.black:
        code, _ = run_command(
            ["black", "--check", "."], "black format check", show_output=args.verbose
        )
        exit_codes.append(code)

    if run_all or args.mypy:
        code, _ = run_command(
            ["mypy", "."], "mypy type check", show_output=args.verbose
        )
        exit_codes.append(code)

    if run_all or args.pytest:
        code, _ = run_command(["pytest"], "pytest", show_output=args.verbose)
        # Don't treat pytest as failing if no tests were collected
        if code == 5:
            result = subprocess.run(
                ["pytest"],
                check=False,
                capture_output=True,
                text=True,
            )
            if "no tests ran" in result.stdout:
                code = 0
        exit_codes.append(code)

    # Print summary
    total_time = time.time() - total_time_start
    failed = sum(1 for code in exit_codes if code != 0)
    passed = len(exit_codes) - failed

    print(f"\n{BOLD}Summary:{ENDC}")
    print(f"Total time: {total_time:.2f}s")
    if passed > 0:
        print(f"{OKGREEN}Passed: {passed}{ENDC}")
    if failed > 0:
        print(f"{FAIL}Failed: {failed}{ENDC}")

    return 1 if any(exit_codes) else 0


if __name__ == "__main__":
    sys.exit(main())
