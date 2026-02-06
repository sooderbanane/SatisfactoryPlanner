# planner/render.py
from __future__ import annotations
from typing import Dict, Tuple


def to_mermaid_merged(nodes: Dict[str, dict], edge_rate: Dict[Tuple[str, str], float]) -> str:
    def fmt(x: float) -> str:
        return f"{x:.2f}"

    lines = ["```mermaid", "flowchart LR"]

    # nodes once
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

        lines.append(f'  {safe_id}["{label}"]')

    # edges
    for (src, dst), rate in edge_rate.items():
        lines.append(f'  {nodes[src]["id"]} -->|{src} {fmt(rate)}/min| {nodes[dst]["id"]}')

    lines.append("```")
    return "\n".join(lines)
