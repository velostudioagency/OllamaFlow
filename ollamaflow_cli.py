#!/usr/bin/env python3
"""
OllamaFlow CLI - Shortcut entry point.

Launches the interactive REPL for building and running AI workflows.
Usage:
    python ollamaflow_cli.py
    python ollamaflow_cli.py --no-server
    python ollamaflow_cli.py --port 9000
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))
from ollamaflow.__main__ import main
main()
