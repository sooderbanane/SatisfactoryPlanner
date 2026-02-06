# planner/main.py
from pathlib import Path
from .dataio import load_json, validate_recipes, parse_recipes, parse_buildings
from .planner import FactoryPlanner
from .render import to_mermaid_merged
from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())