"""Compatibility entry point for the original Audio File render command."""
from pathlib import Path
from runpy import run_path

run_path(str(Path(__file__).with_name('source_motion.py')))
