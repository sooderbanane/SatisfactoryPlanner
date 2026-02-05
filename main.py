import json
from pathlib import Path

path_recipes = Path("./data/recipes.json")
path_buildings = Path("./data/buildings.json")



def load_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path.resolve()}")
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {path.resolve()}: {e}") from e


def validate_recipes(recipes: dict) -> None:
    required_fields = {"produced_in", "time_s", "output", "input"}

    if not isinstance(recipes, dict):
        raise TypeError("recipes.json must contain a JSON object at the top level (a dict).")
    
    for item_name, recipe in recipes.items():
        if not isinstance(item_name, str) or not item_name:
            raise ValueError(f"Invalid item key i recipes.json {item_name!r}")

        if not isinstance(recipe, dict):
            raise TypeError(f"{item_name}: recipe must be an object/dict")

        # 1) Required fields exist
        missing = required_fields - set(recipe.keys())
        if missing:
            raise ValueError(f"{item_name}: missing fields: {sorted(missing)}")

        # 2) time_s > 0
        time_s = recipe["time_s"]
        if not isinstance(time_s, (int, float)) or time_s <= 0:
            raise ValueError(f"{item_name}: time_s must be a number > 0 (got {time_s!r})")

        # 3) input/output are dicts
        for side in ("input", "output"):
            val = recipe[side]
            if not isinstance(val, dict):
                raise TypeError(f"{item_name}: '{side}' must be a dict (got {type(val).__name__})")
            for dep_item, qty in val.items():
                if not isinstance(dep_item, str) or not dep_item:
                    raise ValueError(f"{item_name}: '{side}' contains invalid item key {dep_item!r}")
                if not isinstance(qty, (int, float)) or qty <= 0:
                    raise ValueError(
                        f"{item_name}: '{side}' quantity for '{dep_item}' must be a number > 0 (got {qty!r})"
                    )

        # 4) output contains the item itself
        if item_name not in recipe["output"]:
            raise ValueError(
                f"{item_name}: output must include '{item_name}'. "
                f"Output keys are: {sorted(recipe['output'].keys())}"
            )

        # Optional: produced_in sanity
        produced_in = recipe["produced_in"]
        if not isinstance(produced_in, str) or not produced_in:
            raise ValueError(f"{item_name}: produced_in must be a non-empty string")






def main():
    recipes = load_json(path_recipes)
    buildings = load_json(path_buildings)
    
    validate_recipes(recipes)
    print("recipies.json validated")

    print(f"Loaded {len(recipes)} recipes from {path_recipes}")
    print(f"Loaded {len(buildings)} buildings from {path_buildings}")



    print("First recipe keys:", list(recipes.keys())[:5])


if __name__ == "__main__":
    main()
