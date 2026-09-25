"""Benchmark-0 observation adapter. No oracle, seed, files, or held-out API.

Reuses bounded dimensional enumeration, exact dependency substitution and the
dimensional nullspace solver. All expressions remain GENERATED/FITTED CANDIDATE.
"""
from __future__ import annotations

from fractions import Fraction
import hashlib
import json
import math

from Discovery.constants import PhysicalConstant
from Discovery.dependency_definitions import DependencyDefinition, build_dependency_catalog
from Discovery.dimensional_search import search_candidates, _exponent_complexity
from Discovery.dimensions import Dimension
from Discovery.monomial_constraints import NamedFactor, solve_monomial_constraints
from Discovery.planck_identities import normalize_exponent_signature

EVIDENCE = "GENERATED/FITTED CANDIDATE"
POLICY_KEYS = {"max_factors", "max_abs_power", "max_denominator", "complexity_lambda", "acceptance_validation_rmse"}


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def digest(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def exact_keys(obj, keys):
    if not isinstance(obj, dict) or set(obj) != set(keys):
        raise ValueError("unexpected or missing API fields")


def signature(values):
    return normalize_exponent_signature((k, Fraction(v)) for k, v in values.items())


def sig_record(sig):
    return {k: str(v) for k, v in sig}


def class_id(sig):
    return "|".join(f"{k}:{v}" for k, v in sig) or "1"


def catalog_for(features, target):
    exact_keys(target, {"key", "dimension"})
    if target["key"] in features:
        raise ValueError("target is its own feature")
    specs = {**features, target["key"]: {"dimension": target["dimension"], "definition": None, "unit": "target"}}
    definitions, dimensions = [], {}
    for key, spec in specs.items():
        exact_keys(spec, {"dimension", "definition", "unit"})
        if not isinstance(key, str) or not key.isidentifier() or not key.isascii():
            raise ValueError("invalid feature identifier")
        definitions.append(DependencyDefinition(key, None if spec["definition"] is None else signature(spec["definition"])))
        dimensions[key] = Dimension.from_mapping(spec["dimension"])
    return build_dependency_catalog(definitions, dimensions, required_keys=specs)


def reaches(key, sought, features):
    """Reachability, not net exponent: cancelling a target path is still leakage."""
    if key == sought:
        return True
    definition = features.get(key, {}).get("definition")
    return definition is not None and any(reaches(k, sought, features) for k in definition)


def prepare(raw):
    """Trusted eligibility gate: classify metadata BEFORE accessing feature values."""
    exact_keys(raw, {"features", "target", "train", "validation", "policy"})
    features, target = raw["features"], raw["target"]
    catalog_for(features, target)  # fail closed on unknown references/cycles/dimensions
    rejected = {k: "target_dependency_path" for k in features if reaches(k, target["key"], features)}
    kept = {k: v for k, v in features.items() if k not in rejected}
    rows = {}
    for split in ("train", "validation"):
        rows[split] = [{"features": {k: row["features"][k] for k in kept},
                        "target": row["target"], "group": row["group"]} for row in raw[split]]
    payload = {"features": kept, "target": target, **rows, "policy": raw["policy"]}
    classifications = {k: {"status": "ineligible" if k in rejected else "eligible",
                            "reason": rejected.get(k, "no_registered_target_dependency")} for k in features}
    return payload, classifications


def validate_payload(payload):
    exact_keys(payload, {"features", "target", "train", "validation", "policy"})
    exact_keys(payload["policy"], POLICY_KEYS)
    policy = payload["policy"]
    if any(type(policy[k]) is not int or policy[k] < 1 for k in ("max_factors", "max_abs_power", "max_denominator")):
        raise ValueError("invalid bounds")
    if any(not math.isfinite(policy[k]) or policy[k] < 0 for k in ("complexity_lambda", "acceptance_validation_rmse")):
        raise ValueError("invalid scoring policy")
    features, target = payload["features"], payload["target"]
    catalog = catalog_for(features, target)
    if any(reaches(k, target["key"], features) for k in features):
        raise ValueError("ineligible feature reached discovery")
    if not features:
        raise ValueError("empty discovery feature set")
    for split in ("train", "validation"):
        if not isinstance(payload[split], list) or not payload[split]:
            raise ValueError("missing observation split")
        for row in payload[split]:
            exact_keys(row, {"features", "target", "group"})
            exact_keys(row["features"], features)
            if not isinstance(row["group"], str):
                raise ValueError("invalid group")
            for value in [row["target"], *row["features"].values()]:
                if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
                    raise ValueError("observations must be finite positive numbers")
    return catalog


def log_monomial(surface, row):
    return math.fsum(float(Fraction(power)) * math.log(row["features"][key]) for key, power in surface.items())


def fit(surface, rows):
    return math.fsum(math.log(r["target"]) - log_monomial(surface, r) for r in rows) / len(rows)


def rmse(surface, log_coefficient, rows):
    if not rows:
        raise ValueError("empty scoring split")
    return math.sqrt(math.fsum((log_coefficient + log_monomial(surface, r) - math.log(r["target"])) ** 2 for r in rows) / len(rows))


def stable_decision(candidate, policy):
    return "stable_candidate" if candidate and candidate["validation_rmse"] <= policy["acceptance_validation_rmse"] else "no_stable_law"


def discover(payload):
    """Pure discovery boundary. No world class, irrelevant labels, seed or truth."""
    catalog = validate_payload(payload)
    features, target, policy = payload["features"], payload["target"], payload["policy"]
    factors = [PhysicalConstant(k, k, 1.0, catalog.dimensions[k], v["unit"], "observable", "synthetic")
               for k, v in sorted(features.items())]
    neutral_target = PhysicalConstant(target["key"], target["key"], 1.0,
                                      catalog.dimensions[target["key"]], "target", "target", "synthetic")
    surfaces = search_candidates(factors, target=neutral_target,
                                 **{k: policy[k] for k in ("max_factors", "max_abs_power", "max_denominator")})
    grouped = {}
    for candidate in surfaces:
        expanded = catalog.expand_signature(signature(candidate.exponents))
        if not expanded.is_fully_resolved:
            raise ValueError("unresolved candidate provenance")
        cid = class_id(expanded.signature)
        grouped.setdefault(cid, {"signature": expanded.signature, "members": []})["members"].append(candidate.exponents)
    ranking = []
    for cid, group in grouped.items():
        members = sorted(group["members"], key=lambda s: class_id(signature(s)))
        surface = members[0]
        intercept = fit(surface, payload["train"])
        complexity = _exponent_complexity(p for _, p in group["signature"])
        validation = rmse(surface, intercept, payload["validation"])
        ranking.append({"class_id": cid, "expanded": sig_record(group["signature"]), "members": members,
                        "representative": surface, "log_coefficient": intercept, "coefficient": math.exp(intercept),
                        "training_rmse": rmse(surface, intercept, payload["train"]), "validation_rmse": validation,
                        "expanded_complexity": complexity, "rank_score": validation + policy["complexity_lambda"] * complexity,
                        "evidence_class": EVIDENCE, "scientific_significance": "not_assigned"})
    ranking.sort(key=lambda c: (c["rank_score"], c["expanded_complexity"], c["class_id"]))
    for i, candidate in enumerate(ranking, 1):
        candidate["rank"] = i
    top = ranking[0] if ranking else None
    # Mask ALL atomic inputs in turn, never consult oracle irrelevant labels.
    ablations = {}
    for atom in sorted(k for k, v in features.items() if v["definition"] is None):
        removed = sorted(k for k in features if reaches(k, atom, features))
        remaining = [c for c in ranking if any(not set(member).intersection(removed) for member in c["members"])]
        chosen = remaining[0] if remaining else None
        ablations[atom] = {"removed_features": removed, "top_class": chosen["class_id"] if chosen else None,
                           "decision": stable_decision(chosen, policy)}
    groups = {}
    if top:
        for group in sorted({r["group"] for r in payload["train"]}):
            train = [r for r in payload["train"] if r["group"] == group]
            valid = [r for r in payload["validation"] if r["group"] == group]
            local_fit = fit(top["representative"], train)
            groups[group] = {"training_rmse": rmse(top["representative"], top["log_coefficient"], train),
                             "group_fitted_training_rmse": rmse(top["representative"], local_fit, train),
                             "group_fitted_log_coefficient": local_fit,
                             "validation_rmse": rmse(top["representative"], top["log_coefficient"], valid) if valid else None}
    linear = solve_monomial_constraints([NamedFactor(k, catalog.dimensions[k].exponents) for k in sorted(features)],
                                        catalog.dimensions[target["key"]].exponents)
    return {"input_sha256": digest(payload), "evidence_class": EVIDENCE, "ranking": ranking,
            "top_class": top["class_id"] if top else None, "decision": stable_decision(top, policy),
            "equivalence_map": {c["class_id"]: c["members"] for c in ranking},
            "surface_count": len(surfaces), "class_count": len(ranking), "ablations": ablations,
            "group_diagnostics": groups, "dimensional_system": {"rank": linear.rank, "nullity": linear.nullity, "status": linear.status}}
