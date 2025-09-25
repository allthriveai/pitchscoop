#!/usr/bin/env python3
"""
Test runner for PitchScoop tests.

This script provides easy ways to run different categories of tests
from the organized tests/ directory structure.
"""
import subprocess
import sys
from pathlib import Path
import argparse

def run_command(cmd, cwd=None):
    """Run a shell command and return success status."""
    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"Error running command: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Run PitchScoop tests")
    parser.add_argument(
        "category",
        nargs="?",
        choices=["unit", "integration", "mcp", "e2e", "tools", "all"],
        default="unit",
        help="Test category to run (default: unit)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "-f", "--fail-fast",
        action="store_true", 
        help="Stop on first failure"
    )
    parser.add_argument(
        "--docker",
        action="store_true",
        help="Run tests inside Docker container"
    )
    
    args = parser.parse_args()
    
    project_root = Path(__file__).parent
    tests_dir = project_root / "tests"
    
    # Build pytest command
    pytest_cmd = ["python", "-m", "pytest"]
    
    if args.verbose:
        pytest_cmd.append("-v")
    
    if args.fail_fast:
        pytest_cmd.append("-x")
    
    # Add test path based on category
    if args.category == "all":
        pytest_cmd.append(str(tests_dir))
    else:
        category_dir = tests_dir / args.category
        if not category_dir.exists():
            print(f"Error: Test category '{args.category}' directory not found: {category_dir}")
            return 1
        pytest_cmd.append(str(category_dir))
    
    # Add configuration
    pytest_cmd.extend(["-c", str(tests_dir / "pytest.ini")])
    
    print(f"🧪 Running {args.category} tests...")
    print("=" * 60)
    
    if args.docker:
        # Run inside Docker container
        docker_cmd = [
            "docker", "compose", "exec", "api"
        ] + pytest_cmd
        success = run_command(docker_cmd, cwd=project_root)
    else:
        # Run locally (need to set PYTHONPATH)
        env = {**os.environ}
        env["PYTHONPATH"] = f"{project_root}:{project_root}/api"
        success = run_command(pytest_cmd, cwd=project_root)
    
    if success:
        print("\n✅ Tests completed successfully!")
        return 0
    else:
        print("\n❌ Tests failed!")
        return 1

if __name__ == "__main__":
    import os
    sys.exit(main())