"""Seven bounded adversarial contracts; fixtures are not realized benchmark worlds."""
import copy
import inspect
import math
from pathlib import Path
import tempfile
import unittest

from Discovery import symbolic_benchmark_engine as engine
from Discovery import symbolic_benchmark as harness


def fixture(*, redundant=False, leaked=False, regimes=False):
    features = {"x": {"dimension": {"L": 1}, "definition": None, "unit": "m"},
                "t": {"dimension": {"T": 1}, "definition": None, "unit": "s"},
                "z": {"dimension": {}, "definition": None, "unit": "1"}}
    if redundant:
        features.update({"acc": {"dimension": {"L": 1, "T": -2}, "definition": {"x": 1, "t": -2}, "unit": "m s^-2"},
                         "z2": {"dimension": {}, "definition": {"z": 2}, "unit": "1"},
                         "n": {"dimension": {}, "definition": None, "unit": "1"},
                         "velocity": {"dimension": {"L": 1, "T": -1}, "definition": {"x": 1, "t": -1}, "unit": "m s^-1"}})
    if leaked:
        features.update({"leak": {"dimension": {"L": 1, "T": -2}, "definition": {"y": 1}, "unit": "m s^-2"},
                         "alias": {"dimension": {"L": 1, "T": -2}, "definition": {"leak": 1}, "unit": "m s^-2"},
                         "cancel": {"dimension": {}, "definition": {"leak": 1, "y": -1}, "unit": "1"}})
    splits = {}
    for split, offset in (("train", 0), ("validation", 21)):
        rows = []
        for i in range(1, 21):
            j = i + offset
            x, t, z = 0.6 + (j * 7 % 19) / 9, 0.7 + (j * 3 % 17) / 13, 0.5 + (j * 5 % 23) / 11
            for g in ("g0", "g1") if regimes else ("g0",):
                y = 2 * x / t**2 * z**2 * (4 if g == "g1" else 1)
                if leaked:
                    y *= math.exp(0.003 * (-1)**j)
                values = {"x": x, "t": t, "z": z}
                if redundant:
                    values.update(acc=x/t**2, z2=z**2, n=math.exp(0.002 * (-1)**j), velocity=x/t)
                if leaked:
                    values.update(leak=y, alias=y, cancel=1)
                rows.append({"features": values, "target": y, "group": g})
        splits[split] = rows
    return {"features": features, "target": {"key": "y", "dimension": {"L": 1, "T": -2}}, **splits,
            "policy": {"max_factors": 3, "max_abs_power": 2, "max_denominator": 1,
                       "complexity_lambda": 0.001, "acceptance_validation_rmse": 0.03}}


class BenchmarkBoundaryTests(unittest.TestCase):
    def test_1_leakage_precedes_scoring_and_cancellation_cannot_hide_path(self):
        raw = fixture(leaked=True)
        # A poison value must never be inspected by the eligibility gate or engine.
        for split in ("train", "validation"):
            for row in raw[split]:
                for key in ("leak", "alias", "cancel"):
                    row["features"][key] = object()
        payload, classifications = engine.prepare(raw)
        self.assertEqual({k for k, c in classifications.items() if c["status"] == "ineligible"}, {"leak", "alias", "cancel"})
        output = engine.discover(payload)
        self.assertEqual(output["top_class"], "t:-2|x:1|z:2")
        self.assertGreater(output["ranking"][0]["validation_rmse"], 0)
        original = fixture(leaked=True)
        self.assertEqual(engine.rmse({"leak": 1}, 0, original["validation"]), 0)
        with self.assertRaisesRegex(ValueError, "ineligible"):
            engine.discover(original)
        self.assertFalse(any(set(m) & {"leak", "alias", "cancel"} for c in output["ranking"] for m in c["members"]))

    def test_2_heldout_cannot_change_sealed_selection_and_tampering_fails(self):
        payload = fixture()
        with tempfile.TemporaryDirectory() as name:
            held = Path(name) / "heldout.json"
            held.write_text('{"target":1}')
            first = harness.staged_discovery(payload)
            held.write_text('{"target":999999}')
            second = harness.staged_discovery(payload)
        self.assertEqual(engine.encoded(first), engine.encoded(second))
        oracle, heldout = {"truth": 2}, [{"target": 1}]
        commitment = {"oracle_sha256": engine.digest(oracle), "heldout_sha256": engine.digest(heldout)}
        seal = {"selection_sha256": engine.digest(first), "commitment_sha256": engine.digest(commitment)}
        harness.check_bound_data(commitment, seal, first, oracle, heldout)
        for changed in ("selection", "oracle", "heldout"):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                harness.check_bound_data(commitment, seal, {} if changed == "selection" else first,
                                        {} if changed == "oracle" else oracle, [] if changed == "heldout" else heldout)
        selection = first["discovery"]["ranking"][0]
        rows = payload["validation"]
        changed_rows = copy.deepcopy(rows)
        for row in changed_rows:
            row["target"] *= 10
        self.assertGreater(engine.rmse(selection["representative"], selection["log_coefficient"], changed_rows), 2)
        self.assertLess(engine.rmse(selection["representative"], selection["log_coefficient"], rows), 1e-10)

    def test_3_oracle_api_and_worker_file_import_boundaries(self):
        self.assertEqual(list(inspect.signature(engine.discover).parameters), ["payload"])
        for forbidden in ("seed", "oracle", "heldout", "truth", "law", "world"):
            payload = fixture()
            payload[forbidden] = "hidden"
            with self.subTest(forbidden=forbidden), self.assertRaisesRegex(ValueError, "API fields"):
                engine.discover(payload)
        with tempfile.TemporaryDirectory() as name:
            oracle = Path(name) / "oracle.json"
            oracle.write_text("secret fixture")
            with self.assertRaisesRegex(RuntimeError, "outside staged"):
                harness.staged_discovery(fixture(), probe=oracle)
        result = harness.staged_discovery(fixture())
        self.assertEqual(set(result["staged_source_sha256"]), set(harness.ENGINE_FILES))
        self.assertNotIn("Discovery.symbolic_benchmark_worlds", result["discovery_modules"])
        self.assertNotIn("Discovery.symbolic_benchmark", result["discovery_modules"])
        self.assertTrue(all("oracle" not in p and "heldout" not in p for p in result["staged_reads"]))

    def test_4_exact_equivalence_and_dimensional_near_miss(self):
        payload = fixture(redundant=True)
        output = engine.discover(payload)
        c = output["ranking"][0]
        self.assertEqual(c["class_id"], "t:-2|x:1|z:2")
        self.assertGreaterEqual(len(c["members"]), 3)
        self.assertEqual(c["expanded_complexity"], 5)
        self.assertLess(output["class_count"], output["surface_count"])
        self.assertFalse(any(m == {"velocity": "1"} for c in output["ranking"] for m in c["members"]))
        payload["features"]["acc"]["dimension"] = {"L": 1, "T": -1}
        with self.assertRaisesRegex(ValueError, "dimensionally inconsistent"):
            engine.discover(payload)

    def test_5_irrelevant_ablation_and_no_significance_from_fit(self):
        payload = fixture(redundant=True)
        output = engine.discover(payload)
        self.assertEqual(output["top_class"], output["ablations"]["n"]["top_class"])
        self.assertNotIn("n", output["ranking"][0]["expanded"])
        survivors = [c for c in output["ranking"] if "n" in c["expanded"] and c["validation_rmse"] < 0.03]
        self.assertTrue(survivors)  # predictive false positives are possible and visible
        self.assertTrue(all(c["scientific_significance"] == "not_assigned" and c["evidence_class"] == engine.EVIDENCE for c in survivors))
        for atom, ablation in output["ablations"].items():
            removed = set(ablation["removed_features"])
            masked = copy.deepcopy(payload)
            masked["features"] = {k: v for k, v in masked["features"].items() if k not in removed}
            for split in ("train", "validation"):
                for row in masked[split]:
                    row["features"] = {k: v for k, v in row["features"].items() if k not in removed}
            self.assertEqual(engine.discover(masked)["top_class"], ablation["top_class"])

    def test_6_wrong_regime_world_can_abstain_without_pipeline_failure(self):
        output = engine.discover(fixture(regimes=True))
        self.assertEqual(output["decision"], "no_stable_law")
        self.assertTrue(output["ranking"])
        self.assertTrue(all(c["validation_rmse"] >= math.log(4)/2 - 1e-12 for c in output["ranking"]))
        self.assertLess(output["group_diagnostics"]["g0"]["group_fitted_training_rmse"], 1e-10)
        self.assertGreater(output["group_diagnostics"]["g0"]["training_rmse"], 0.3)

    def test_7_independent_metric_coefficient_and_threshold_oracles(self):
        rows = [{"features": {"a": 2}, "target": 4, "group": "g0"},
                {"features": {"a": 4}, "target": 32, "group": "g0"}]
        # Multipliers 2 and 8: best log-space constant is geometric mean 4.
        intercept = engine.fit({"a": "1"}, rows)
        self.assertAlmostEqual(math.exp(intercept), 4)
        self.assertAlmostEqual(engine.rmse({"a": "1"}, intercept, rows), math.log(2))
        policy = {"acceptance_validation_rmse": 0.03}
        self.assertEqual(engine.stable_decision({"validation_rmse": 0.03}, policy), "stable_candidate")
        self.assertEqual(engine.stable_decision({"validation_rmse": math.nextafter(0.03, math.inf)}, policy), "no_stable_law")
        output = engine.discover(fixture())
        self.assertEqual(output["dimensional_system"]["rank"], 2)
        self.assertEqual(output["dimensional_system"]["nullity"], 1)
        self.assertAlmostEqual(output["ranking"][0]["rank_score"], 0.005)
        malformed = fixture()
        malformed["train"][0]["target"] = float("nan")
        with self.assertRaises(ValueError):
            engine.discover(malformed)


if __name__ == "__main__":
    unittest.main()
