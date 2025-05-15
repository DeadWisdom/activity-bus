# Main entry point for the activity-bus package
# Provides a simple CLI to run examples or start processing

import argparse
import asyncio
import sys


def run_example() -> None:
    """Run the example script."""
    try:
        from examples.run_example import main

        asyncio.run(main())
    except ImportError as e:
        print(f"Error importing example: {e}")
        sys.exit(1)


def main() -> None:
    desc = "Activity Bus - A rule-based activity processing system"
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument("--example", action="store_true", help="Run the example script")
    args = parser.parse_args()

    if args.example:
        run_example()
    else:
        print("Activity Bus - A rule-based activity processing system")
        print("\nUsage:")
        print("  --example    Run the example script")


if __name__ == "__main__":
    main()
