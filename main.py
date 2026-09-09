"""Application entry point -- launches the desktop GUI.

Day 1's CLI still exists (cli.py) as a quick terminal-only way to poke
at the data layer, but the GUI is the primary interface as of Day 2.
"""

from gui import launch


if __name__ == "__main__":
    launch()
