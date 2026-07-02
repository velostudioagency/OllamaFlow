#!/usr/bin/env python3
"""
OllamaFlow CLI - Interactive REPL for building and running AI workflows.

Usage:
    python -m ollamaflow                       Start interactive REPL
    python -m ollamaflow --no-server           Start REPL without auto-starting the API server
    python -m ollamaflow --port 9000           Start REPL on a specific API server port
"""

import argparse
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    parser = argparse.ArgumentParser(
        prog="ollamaflow",
        description="OllamaFlow - Local-first visual AI workflow builder",
    )
    parser.add_argument("--url", "-u",
                        help="Server URL (default: http://localhost:8000)")
    parser.add_argument("--token", "-t",
                        help="API authentication token")
    parser.add_argument("--no-server", action="store_true",
                        help="Skip auto-starting the OllamaFlow API server")
    parser.add_argument("--port", "-p", type=int, default=8000,
                        help="OllamaFlow API server port (default: 8000)")

    args = parser.parse_args()

    from ollamaflow.repl import run_repl
    asyncio.run(run_repl(
        url=args.url,
        token=args.token,
        no_server=args.no_server,
        port=args.port,
    ))


if __name__ == "__main__":
    main()
