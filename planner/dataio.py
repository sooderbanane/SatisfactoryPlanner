import json
from pathlib import Path
from typing import Dict
from .models import Recipe, Building


def load_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path.resolve()}")
    try:
        with path.open("r", encoding="utf-8") as f: 
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {path.resolve()} : {e}") from e
    

def validate_recipes(raw: dict) -> None:
    required_fields = {"produced_in", "time_s", "output", "input"}
    if not isinstance(raw, dict):
        raise TypeError("recipes.json must be a JSON object (dict).")

    for item_name, recipe in raw.items():
        missing = required_fields - set(recipe.keys())
        if missing:
            raise ValueError(f"{item_name}: missing fields: {sorted(missing)}")

        if item_name not in recipe["output"]:
            raise ValueError(
                f"{item_name}: output must include '{item_name}'. "
                f"Output keys are: {sorted(recipe['output'].keys())}"
            )
        
def parse_recipes(raw: dict) -> Dict[str, Recipe]:
    # Your file is keyed by item_name for now => produces=item_name
    recipes: Dict[str, Recipe] = {}
    for item_name, r in raw.items():
        recipes[item_name] = Recipe(
            produces=item_name,
            produced_in=r["produced_in"],
            time_s=float(r["time_s"]),
            input={k: float(v) for k, v in r["input"].items()},
            output={k: float(v) for k, v in r["output"].items()},
        )
    return recipes


def parse_buildings(raw: dict) -> Dict[str, Building]:
    buildings: Dict[str, Building] = {}
    for bid, b in raw.items():
        buildings[bid] = Building(
            id=bid,
            power_mw=float(b.get("power_mw", 0.0)),
            water_m3_min=float(b.get("water_m3_min", 0.0)),
            build_cost={k: float(v) for k, v in b.get("build_cost", {}).items()},
        )
    return buildings