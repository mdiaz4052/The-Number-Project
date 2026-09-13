"""Trusted Benchmark-0 oracle. Never staged in the discovery worker."""
from __future__ import annotations

import hashlib
import math


class Stream:
    def __init__(self, seed, name):
        self.seed, self.name, self.counter = seed, name, 0

    def uniform(self, low=0.0, high=1.0):
        raw = hashlib.sha256(f"{self.seed}:{self.name}:{self.counter}".encode()).digest()
        self.counter += 1
        u = int.from_bytes(raw[:8], "big") / 2**64
        return low + (high - low) * u

    def choice(self, items):
        return items[min(int(self.uniform() * len(items)), len(items) - 1)]


def policy_from(prereg):
    return {**{k: prereg["grammar"][k] for k in ("max_factors", "max_abs_power", "max_denominator")},
            **{k: prereg["scoring"][k] for k in ("complexity_lambda", "acceptance_validation_rmse")}}


def metadata(prereg, world):
    template, generation = prereg["worlds"][world], prereg["generation"]
    dimensions = {"acc": {"L": 1, "T": -2}, "z2": {}, "velocity": {"L": 1, "T": -1},
                  "leak": {"L": 1, "T": -2}, "leak_alias": {"L": 1, "T": -2}}
    units = {"acc": "m s^-2", "z2": "1", "velocity": "m s^-1", "leak": "m s^-2", "leak_alias": "m s^-2"}
    specs = {}
    for key in template["features"]:
        if key in generation["base_observables"]:
            item = generation["base_observables"][key]
        elif key in template.get("irrelevant", {}):
            item = template["irrelevant"][key]
        else:
            item = {"dimension": dimensions[key], "unit": units[key]}
        specs[key] = {"dimension": item["dimension"], "unit": item["unit"],
                      "definition": template.get("definitions", {}).get(key)}
    return specs


def generate(prereg, seed):
    """Exactly one frozen realization. No retry, rejection sampling, or fitting."""
    if len(seed) != 64 or any(c not in "0123456789abcdef" for c in seed):
        raise ValueError("seed must be 256-bit lowercase hex")
    public, heldout, truths = {}, {}, {}
    for world, template in prereg["worlds"].items():
        law_stream = Stream(seed, world + ":law")
        domain = prereg["generation"]["world_C_exponent_domain" if world == "C" else "law_exponent_domain"]
        exponent = law_stream.choice(domain)
        coefficient = law_stream.choice(prereg["generation"]["coefficient_domain"])
        splits = {}
        for split in ("train", "validation", "held_out"):
            count = template[split]
            stream = Stream(seed, world + ":" + split + ":inputs")
            noise = Stream(seed, world + ":" + split + ":noise")
            nuisance = Stream(seed, world + ":" + split + ":nuisance")
            ranges = prereg["generation"]["held_out_base_log_ranges"] if split == "held_out" else {
                k: v["log_uniform"] for k, v in prereg["generation"]["base_observables"].items()}
            paired = world == "D" and split != "train"
            rows = []
            for i in range(count // 2 if paired else count):
                values = {k: math.exp(stream.uniform(*ranges[k])) for k in ("x", "t", "z")}
                clean = coefficient * values["x"] * values["t"] ** -2 * values["z"] ** exponent
                groups = ("g0", "g1") if paired else ("g1" if world == "D" and i >= template["train_groups"]["g0"] else "g0",)
                for group in groups:
                    target = clean * (4 if group == "g1" else 1) * math.exp(noise.uniform(-template["log_noise_half_width"], template["log_noise_half_width"]))
                    features = dict(values)
                    for key, spec in template.get("irrelevant", {}).items():
                        features[key] = math.exp(nuisance.uniform(*spec["log_uniform"]))
                    # Definitions are operational relations, never the governing law.
                    pending = dict(template.get("definitions", {}))
                    known = {**features, "y": target}
                    while pending:
                        ready = [k for k, v in pending.items() if set(v) <= set(known)]
                        if not ready:
                            raise ValueError("unresolved generator definition")
                        for key in ready:
                            features[key] = math.prod(known[k] ** power for k, power in pending.pop(key).items())
                            known[key] = features[key]
                    rows.append({"features": features, "target": target, "group": group})
            splits[split] = rows
        public[world] = {"features": metadata(prereg, world),
                         "target": {"key": "y", "dimension": prereg["grammar"]["target_dimension"]},
                         "train": splits["train"], "validation": splits["validation"], "policy": policy_from(prereg)}
        heldout[world] = splits["held_out"]
        truths[world] = {"base_signature": {"x": "1", "t": "-2", "z": str(exponent)}, "coefficient": coefficient,
                         "regime_multipliers": {"g0": 1, "g1": 4} if world == "D" else {"g0": 1},
                         "single_family_member": world != "D", "irrelevant_atoms": sorted(template.get("irrelevant", {})),
                         "noise_log_half_width": template["log_noise_half_width"]}
    oracle = {"generator_version": prereg["generation"]["version"], "seed": seed, "worlds": truths}
    return public, heldout, oracle
