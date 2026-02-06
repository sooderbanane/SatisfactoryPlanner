from __future__ import annotations
from dataclasses import dataclass
from typing import Dict 


@dataclass(frozen=True)
class Recipe: 
    produces: str
    produced_in: str
    time_s: float
    input: Dict[str, float]
    output: Dict[str, float]

    def output_per_min_per_machine(self) -> float:
        return (60.0 / self.time_s) * self.output[self.produces]
    

@dataclass(frozen=True)
class Building:
    id: str
    power_mw: float
    water_m3_min: float
    build_cost: Dict[str, float]

