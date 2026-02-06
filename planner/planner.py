from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Tuple
from .models import Recipe, Building


@dataclass
class FactoryPlanner:
    recipes: Dict[str, Recipe]
    buildings: Dict[str, Building]

    def expand_one_level(self, item: str, target_rate_per_min: float) -> Dict[str, float]:
        if item not in self.recipes:
            raise ValueError(f"No recipe for '{item}'")


        r = self.recipes[item]
        output_per_min_one = r.output_per_min_per_machine()
        eq_machines = target_rate_per_min / output_per_min_one
        crafts_per_min_one = 60 / r.time_s
        
        needed: Dict[str, float] = {}
        for in_item, qty_per_craft in r.input.items():
            needed[in_item] = crafts_per_min_one * qty_per_craft * eq_machines
        return needed
    

    def build_merged_graph(self, target_item: str, target_rate: float) -> Tuple[Dict[str, float], Dict[Tuple[str, str], float]]:
        item_rate: Dict[str, float] = {}
        edge_rate: Dict[Tuple[str, str], float] = {}

        def add(d, k, v):
            d[k] = d.get(k, 0.0) + v

        def walk(item: str, rate: float, stack=()):
            if item in stack:
                raise ValueError("Cycle: " + " -> ".join(stack + (item,)))

            add(item_rate, item, rate)

            if item not in self.recipes:
                return

            inputs = self.expand_one_level(item, rate)
            for in_item, in_rate in inputs.items():
                add(edge_rate, (in_item, item), in_rate)
                walk(in_item, in_rate, stack + (item,))

        walk(target_item, target_rate)
        return item_rate, edge_rate
    

    def node_stats(self, item_rate: Dict[str, float]) -> Dict[str, dict]:
        nodes: Dict[str, dict] = {}
        for item, rate in item_rate.items():
            if item not in self.recipes:
                nodes[item] = {"type": "raw", "rate": rate}
                continue

            r = self.recipes[item]
            machines = rate / r.output_per_min_per_machine()
            b = self.buildings.get(r.produced_in)
            power_total = None if b is None else b.power_mw * machines

            nodes[item] = {
                "type": "crafted",
                "building": r.produced_in,
                "rate": rate,
                "machines": machines,
                "power_mw": power_total,
            }
        return nodes