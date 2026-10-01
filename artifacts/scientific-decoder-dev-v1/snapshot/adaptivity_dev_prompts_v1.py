"""Pure prospective decoder-prompt renderer; no I/O, oracle, or model calls.

The caller supplies one frozen coordinate task, the reviewed public grammar,
and either no training responses or exactly 64 responses. Test coordinates and
private law identities are never read to construct the observation.
"""

from __future__ import annotations

import json
import math
from collections.abc import Sequence


ACTOR_INSTRUCTIONS = """Infer one mathematical expression for the unknown scalar response described below.
This is a response-only task. Do not use tools, browse, read files, execute code, or request measurements.
Use only the supplied public problem description and observations. Standard textbook equations may or may not match this task; do not assume that a familiar domain fixes the unknown equation.
The observation list is the complete numerical evidence available to you. An empty list means that no measurements were supplied. Do not invent observations, fitted scores, test results, or unavailable constants.
Return exactly one JSON object with the four string fields action, expression, hypothesis, and revision, and no other fields. Set action to propose. Do not include Markdown fences or text outside the object.
expression must be one scalar formula in the exact syntax and operators specified by expression_grammar. Use only the mapped variable names x0, x1, and so on, and permitted numeric constants. Do not write a function definition, assignment, import, attribute access, loop, or executable program.
hypothesis should briefly state the proposed functional relationship and its assumptions. revision should briefly state what supplied evidence informed this proposal; if no observations were supplied, say that the proposal uses only public problem information. These fields request short public explanations, not a hidden reasoning transcript.
You have one final submission. Select one expression now; no repair, measurement, alternate candidate, or follow-up is available.
"""

_DOMAINS = {
    "m8_sound_speed": {
        "public_problem": "Infer the unknown scalar response for the sound-speed domain from the supplied input metadata and any observations.",
        "variables": ("gamma", "T", "M"),
        "descriptions": (
            "Adiabatic index of the gas; a positive real number.",
            "Temperature of the medium; a positive real number.",
            "Molar mass of the medium; a positive real number.",
        ),
    },
    "m10_be_distribution": {
        "public_problem": "Infer the unknown scalar response for the Bose–Einstein distribution domain from the supplied input metadata and any observations.",
        "variables": ("omega", "T"),
        "descriptions": (
            "Angular frequency; a positive real number.",
            "Temperature; a positive real number.",
        ),
    },
}


def canonical_json(value: object) -> str:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    )


def _finite_number(value: object) -> int | float:
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError("expected a finite exact int or float, excluding bool")
    return value


def make_observation(
    task_record: dict,
    expression_grammar: dict,
    training_outputs: Sequence[int | float] | None = None,
) -> dict:
    """Return only approved actor-visible metadata and optional training pairs.

    Law ID, version, difficulty, runtime keys, seed and test fields may exist in
    task_record but are neither included nor consulted. The caller must verify
    task/grammar bytes against the prelaunch contract; this renderer does not
    claim to authenticate arbitrary metadata or enforce mathematical grammar.
    """
    if not isinstance(task_record, dict):
        raise ValueError("task_record must be a dictionary")
    domain = _DOMAINS.get(task_record.get("domain_id"))
    if domain is None:
        raise ValueError("unsupported development domain")
    specification = task_record.get("specification")
    if not isinstance(specification, dict):
        raise ValueError("missing public specification")
    variables = specification.get("variables")
    if variables != list(domain["variables"]):
        raise ValueError("public variable order differs from reviewed metadata")
    units = specification.get("units")
    bounds = specification.get("bounds")
    if (not isinstance(units, list) or len(units) != len(variables)
            or any(not isinstance(unit, str) or not unit.strip() for unit in units)
            or not isinstance(bounds, list) or len(bounds) != len(variables)):
        raise ValueError("invalid input unit/bounds schema")
    public_bounds = []
    for interval in bounds:
        if not isinstance(interval, list) or len(interval) != 2:
            raise ValueError("invalid bound interval")
        low, high = map(_finite_number, interval)
        if not 0 < low < high:
            raise ValueError("this version requires positive ordered bounds")
        public_bounds.append([low, high])
    output = specification.get("output")
    output_unit = specification.get("output_unit")
    if any(not isinstance(value, str) or not value.strip()
           for value in (output, output_unit)):
        raise ValueError("invalid public output description")
    if not isinstance(expression_grammar, dict) or not expression_grammar:
        raise ValueError("reviewed nonempty public expression grammar is required")
    public_grammar = json.loads(canonical_json(expression_grammar))

    observations = []
    if training_outputs is not None:
        if (not isinstance(training_outputs, (list, tuple))
                or len(training_outputs) != 64):
            raise ValueError("reference condition requires exactly 64 responses")
        # Intentionally do not read coordinates['test'], even for validation.
        coordinates = task_record["coordinates"]["train"]["x"]
        if not isinstance(coordinates, list) or len(coordinates) != 64:
            raise ValueError("reference condition requires exactly 64 training rows")
        for coordinate, response in zip(coordinates, training_outputs, strict=True):
            if not isinstance(coordinate, list) or len(coordinate) != len(variables):
                raise ValueError("invalid training coordinate dimension")
            x = [_finite_number(value) for value in coordinate]
            if any(not low <= value <= high
                   for value, (low, high) in zip(x, public_bounds, strict=True)):
                raise ValueError("training coordinate outside frozen bounds")
            observations.append({"x": x, "y": _finite_number(response)})

    return {
        "schema": "astra-decoder-observation-v1",
        "public_problem": domain["public_problem"],
        "input_variables": [
            {
                "name": f"x{index}",
                "public_name": name,
                "description": domain["descriptions"][index],
                "unit": units[index],
                "bounds": public_bounds[index],
                "coordinate_transform": "log10",
            }
            for index, name in enumerate(variables)
        ],
        "output": {"description": output, "unit": output_unit},
        "expression_grammar": public_grammar,
        "observations": observations,
    }


def render_prompt(
    task_record: dict,
    expression_grammar: dict,
    training_outputs: Sequence[int | float] | None = None,
) -> str:
    """Render the literal LF instruction block and canonical observation JSON."""
    observation = make_observation(task_record, expression_grammar, training_outputs)
    return ACTOR_INSTRUCTIONS + "OBSERVATION_JSON\n" + canonical_json(observation) + "\n"
