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
            raise ValueError(f"Invalid item key in recipes.json {item_name!r}")

        if not isinstance(recipe, dict):
            raise TypeError(f"{item_name}: recipe must be an object/dict")

        missing = required_fields - set(recipe.keys())
        if missing:
            raise ValueError(f"{item_name}: missing fields: {sorted(missing)}")

        time_s = recipe["time_s"]
        if not isinstance(time_s, (int, float)) or time_s <= 0:
            raise ValueError(f"{item_name}: time_s must be a number > 0 (got {time_s!r})")

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

        if item_name not in recipe["output"]:
            raise ValueError(
                f"{item_name}: output must include '{item_name}'. "
                f"Output keys are: {sorted(recipe['output'].keys())}"
            )

        produced_in = recipe["produced_in"]
        if not isinstance(produced_in, str) or not produced_in:
            raise ValueError(f"{item_name}: produced_in must be a non-empty string")


def output_per_min_per_machine(item: str, recipes: dict) -> float:
    if item not in recipes:
        raise ValueError(f"No recipe for item '{item}'")

    recipe = recipes[item]
    time_s = recipe["time_s"]
    qty_out = recipe["output"][item]

    crafts_per_min = 60 / time_s
    return crafts_per_min * qty_out

def expand_one_level(item :str, target_rate_per_minute: float, recipes: dict) -> dict:
    if item not in recipes:
        raise ValueError(f"No Recipe for '{item}'")

    r = recipes[item]
    time_s = r["time_s"]

    output_per_min_one_machine = output_per_min_per_machine(item, recipes)
    eq_machiens = target_rate_per_minute / output_per_min_one_machine

    crafts_per_min_one_machine = 60 / time_s

    needed = {} 
    for in_item, qty_per_craft in r["input"].items():
        needed[in_item] = crafts_per_min_one_machine * qty_per_craft * eq_machiens

    return needed

def merge_dicts(a: dict, b: dict) -> dict:
    out = dict(a)
    for k, v in b.items():
        out[k] = out.get(k, 0.0) + v
    return out 

def requirements(
        item: str,
        target_rate_per_min: float,
        recipes: dict,
        stack: tuple[str, ...] = ()
                 ) -> tuple[dict, dict]:
    
    if item in stack: 
        raise ValueError(f"Recipe cycle detected: {' -> '.join(stack + (item,))}")

    if item not in recipes:
        return {item: target_rate_per_min}, {}
    
    recipe = recipes[item]

    out_per_min_one_machine = output_per_min_per_machine(item, recipes)
    eq_machines = target_rate_per_min / out_per_min_one_machine


    machines = {recipe["produced_in"]: eq_machines}
    
    one_level = expand_one_level(item, target_rate_per_min, recipes)

    raw_total = {}

    machine_total = dict(machines)

    for in_item, in_rate in one_level.items():
        raw_sub, mach_sub = requirements(
            in_item,
            in_rate,
            recipes,
            stack + (item,)
        )
        raw_total = merge_dicts(raw_total, raw_sub)
        machine_total = merge_dicts(machine_total, mach_sub)
    return raw_total, machine_total 

def build_merged_graph(target_item: str, target_rate: float, recipes: dict) -> tuple[dict, dict]: 
    item_rate = {}
    edge_rate ={}

    def add(d,k,v):
        d[k] = d.get(k, 0.0) + v


    def walk(item: str, rate: float, stack=()):
        if item in stack:
            raise ValueError("Cycle: " + " -> ".join(stack + (item, ))) 
        
        add(item_rate, item, rate)

        if item not in recipes:
            return

        inputs = expand_one_level(item, rate, recipes)
        for in_item, in_rate in inputs.items():
            add(edge_rate, (in_item, item), in_rate)
            walk(in_item, in_rate, stack + (item, ))

    walk(target_item, target_rate)
    return item_rate, edge_rate

def compute_node_stats(item_rate: dict, recipes: dict, buildings: dict) -> dict:
    nodes = {}

    for item, rate in item_rate.items():
        if item not in recipes:
            nodes[item] = {"type": "raw", "rate": rate}
            continue

        out_per_min = output_per_min_per_machine(item, recipes)
        machines = rate / out_per_min

        building = recipes[item]["produced_in"]
        p = buildings.get(building, {}).get("power_mw", None)
        power = None if p is None else p * machines

        nodes[item] = {
            "type": "crafted",
            "building": building,
            "rate": rate,
            "machines": machines,
            "power_mw": power,
        } 

    return nodes


def to_mermaid_merged(nodes: dict, edge_rate: dict) -> str:
    lines = ["```mermaid", "flowchart LR"]
    def fmt(x): return f"{x:.2f}"

    for item, n in nodes.items():
        safe_id = "id_" + item.replace("-", "_").replace(" ", "_")
        n["id"] = safe_id

        if n["type"] == "raw":
            label = f"RAW<br/>{item}<br/>{fmt(n['rate'])}/min"
        else: 
            power_str = "?" if n["power_mw"] is None else f"{n['power_mw']:.1f} MW"
            label = (
                f"{n['building'].title()}<br/>"
                f"{item}<br/>"
                f"{fmt(n['rate'])}/min<br/>"
                f"x{fmt(n['machines'])}<br/>"
                f"{power_str}"
            )

        lines.append(f' {safe_id}["{label}"]')

    for (src, dst), rate in edge_rate.items():
        src_id = nodes[src]["id"]
        dst_id = nodes[dst]["id"]
        lines.append(f'  {src_id} -->|{src} {fmt(rate)}/min| {dst_id}')

    lines.append("```")
    return "\n".join(lines)


def main():
    recipes = load_json(path_recipes)
    buildings = load_json(path_buildings)

    validate_recipes(recipes)
    print("recipes.json validated ✅")

    target_item = "reinforced_iron_plate"
    target_rate = 10.0

    item_rate, edge_rate = build_merged_graph(target_item, target_rate, recipes)
    nodes = compute_node_stats(item_rate, recipes, buildings)

    mermaid = to_mermaid_merged(nodes, edge_rate)
    out_path = Path("/mnt/c/GIT/obs_vault/Notes/Sources/satisfactory/output/factory.md")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(mermaid, encoding="utf-8")
    print("Wrote factory.md")

if __name__ == "__main__":
    main()
