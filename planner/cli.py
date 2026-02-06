from __future__ import annotations

import argparse
from pathlib import Path

from .dataio import load_json, validate_recipes, parse_recipes, parse_buildings
from .planner import FactoryPlanner
from .render import to_mermaid_merged

def build_planner(data_dir: Path) -> FactoryPlanner:
    recipes_path = data_dir / "recipes.json"
    buildings_path = data_dir / "buildings.json"

    raw_recipes = load_json(recipes_path)
    validate_recipes(raw_recipes)
    recipes = parse_recipes(raw_recipes)

    raw_buildings = load_json(buildings_path)
    buildings = parse_buildings(raw_buildings)

    return FactoryPlanner(recipes=recipes, buildings=buildings)

def cmd_validate(args: argparse.Namespace) -> int: 
    data_dir = Path(args.data_dir)
    _ = build_planner(data_dir)
    print("Data validated")
    return 0

def cmd_plan(args: argparse.Namespace) -> int:
    planner = build_planner(Path(args.data_dir))

    item_rate, edge_rate = planner.build_merged_graph(args.item, args.rate)
    nodes = planner.node_stats(item_rate)
    mermaid = to_mermaid_merged(nodes, edge_rate)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(mermaid, encoding="utf-8")

    print(f"Wrote {out_path.resolve()}")
    return 0

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="planner", description="Satisfactory production planner")
    p.add_argument("--data-dir", default="./data", help="Directory with recipes.json and buildings.json")

    sub = p.add_subparsers(dest="cmd", required=True)

    v = sub.add_parser("validate", help="Validate JSON data files")
    v.set_defaults(fn=cmd_validate)

    plan = sub.add_parser("plan", help="Generate a Mermaid factory diagram")
    plan.add_argument("item", help="Target item id (e.g. reinforced_iron_plate)")
    plan.add_argument("rate", type=float, help="Target rate per minute (e.g. 10)")
    plan.add_argument("--out", default="./output/factory.md", help="Output markdown path")
    plan.set_defaults(fn=cmd_plan)

    return p


def main(argv: list[str] | None = None ) -> int: 
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.fn(args)