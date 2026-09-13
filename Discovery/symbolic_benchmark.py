"""Benchmark-0 custody, staged execution, post-seal evaluation and read-only guard."""
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import tempfile
import traceback

from Discovery.symbolic_benchmark_engine import (encoded, digest, prepare, discover, signature,
    class_id, rmse, EVIDENCE)
from Discovery.symbolic_benchmark_worlds import generate
from Discovery.preregistration_history import verify_preregistration_freeze
from Discovery.source_history import verify_committed_source_state

ROOT = Path(__file__).resolve().parents[1]
REL = "Experiments/SymbolicDiscovery/Benchmark0"
ART = ROOT / REL
PRIVATE = ROOT / ".tnp-local/benchmark0-private"
ENGINE_FILES = tuple("Discovery/" + name + ".py" for name in (
    "__init__", "symbolic_benchmark_engine", "constants", "dimensions", "dimensional_search",
    "planck_identities", "dependency_definitions", "monomial_constraints"))
SOURCE_FILES = (*ENGINE_FILES, "Discovery/symbolic_benchmark_worlds.py", "Discovery/symbolic_benchmark.py",
                "Discovery/preregistration_history.py", "Discovery/source_history.py", "tests/test_symbolic_benchmark.py")

# Installed before the staged Discovery import. Same Python execution identity;
# this enforces the honest worker's dataflow boundary, not hostile-code security.
WORKER = r'''
import sys, os, json
stage = os.path.realpath(sys.argv[1])
stdlib = os.path.realpath(os.path.dirname(os.__file__))
reads = set()
def audit(event, args):
    if event == 'open':
        path = args[0]
        if isinstance(path, int):
            if path not in (0, 1, 2):
                raise PermissionError('nonstandard descriptor')
            return
        path = os.path.realpath(os.fsdecode(path))
        mode = args[1]
        if (isinstance(mode, str) and any(k in mode for k in 'wax+')) or args[2] & (os.O_WRONLY | os.O_RDWR):
            raise PermissionError('worker write forbidden')
        if path.startswith(stage + os.sep):
            reads.add('<stage>/' + os.path.relpath(path, stage))
        elif path.startswith(stdlib + os.sep) and 'site-packages' not in path:
            pass
        else:
            raise PermissionError('worker read outside staged code/stdlib')
    if event.startswith(('socket.', 'subprocess.', 'os.system', 'os.exec', 'os.spawn')):
        raise PermissionError('worker external action forbidden')
sys.addaudithook(audit)
sys.path.insert(0, stage)
if len(sys.argv) > 2:
    open(sys.argv[2]).read()
from Discovery.symbolic_benchmark_engine import discover
result = discover(json.load(sys.stdin))
print(json.dumps({'discovery': result, 'staged_reads': sorted(reads),
    'discovery_modules': sorted(k for k in sys.modules if k == 'Discovery' or k.startswith('Discovery.'))},
    sort_keys=True, allow_nan=False))
'''


def read(path):
    return json.loads(Path(path).read_text())


def write_new(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(encoded(data))


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True).strip()


def now():
    return datetime.now(timezone.utc).isoformat()


def staged_discovery(payload, probe=None):
    with tempfile.TemporaryDirectory(prefix="tnp-b0-discovery-") as name:
        stage = Path(name)
        for relative in ENGINE_FILES:
            dest = stage / relative
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, dest)
        manifest = {p: hashlib.sha256((stage / p).read_bytes()).hexdigest() for p in ENGINE_FILES}
        command = [sys.executable, "-I", "-B", "-c", WORKER, str(stage)]
        if probe is not None:
            command.append(str(probe))
        result = subprocess.run(command, input=encoded(payload), cwd=stage,
                                env={"PATH": os.defpath, "PYTHONDONTWRITEBYTECODE": "1"},
                                capture_output=True, timeout=180)
        if result.returncode:
            raise RuntimeError(result.stderr.decode())
        output = json.loads(result.stdout)
        output["staged_source_sha256"] = manifest
        output["worker_sha256"] = hashlib.sha256(WORKER.encode()).hexdigest()
        if any((stage / p).read_bytes() != (ROOT / p).read_bytes() for p in ENGINE_FILES):
            raise ValueError("worker source changed")
        return output


def verify_freeze():
    anchor = read(ART / "anchor.json")
    verify_preregistration_freeze(ROOT, baseline=anchor["base_sha"], commit=anchor["freeze_sha"],
                                 path=REL + "/preregistration.v1.json", sha256=anchor["preregistration_sha256"])
    if anchor["created_at"] <= git("show", "-s", "--format=%cI", anchor["freeze_sha"]).replace("+00:00", "Z"):
        raise ValueError("anchor must follow freeze")
    return anchor


def realize():
    verify_freeze()
    if PRIVATE.exists() or (ART / "commitment.json").exists():
        raise ValueError("realized epoch already exists; no silent rerun")
    if git("status", "--porcelain", "--untracked-files=no"):
        raise ValueError("commit source before realization")
    source_sha = git("rev-parse", "HEAD")
    source_time = datetime.fromisoformat(git("show", "-s", "--format=%cI", source_sha))
    if source_time <= datetime.fromisoformat(read(ART / "anchor.json")["created_at"]):
        raise ValueError("generator source must postdate published anchor")
    prereg = read(ART / "preregistration.v1.json")
    # Persist seed before realization, including if a later step fails.
    seed = secrets.token_hex(32)
    write_new(PRIVATE / "seed.json", {"seed": seed, "source_sha": source_sha, "created_at": now()})
    public, heldout, oracle = generate(prereg, seed)
    write_new(PRIVATE / "heldout.json", heldout)
    write_new(PRIVATE / "oracle.json", oracle)
    write_new(ART / "public.json", public)
    requests, eligibility = {}, {}
    for world, raw in public.items():
        requests[world], eligibility[world] = prepare(raw)
    write_new(ART / "discovery_inputs.json", requests)
    write_new(ART / "eligibility.json", eligibility)
    write_new(ART / "commitment.json", {
        "source_sha": source_sha, "created_at": now(), "oracle_sha256": digest(oracle),
        "heldout_sha256": digest(heldout), "public_sha256": digest(public), "inputs_sha256": digest(requests),
        "eligibility_sha256": digest(eligibility), "preregistration_sha256": hashlib.sha256((ART / "preregistration.v1.json").read_bytes()).hexdigest(),
        "engine_blinded": True, "oracle_revealed": False})
    print("Realized one epoch; oracle and held-out remain private. Publish commitment before discover.")


def require_committed(path):
    relative = str(Path(path).relative_to(ROOT))
    actual = subprocess.check_output(["git", "-C", str(ROOT), "show", "HEAD:" + relative])
    if actual != Path(path).read_bytes():
        raise ValueError("required stage is not committed")


def seal():
    require_committed(ART / "commitment.json")
    commitment = read(ART / "commitment.json")
    verify_committed_source_state(ROOT, commitment["source_sha"], source_paths=SOURCE_FILES, artifact_label="Benchmark 0")
    inputs = read(ART / "discovery_inputs.json")
    if digest(inputs) != commitment["inputs_sha256"]:
        raise ValueError("public inputs differ from commitment")
    # No oracle/heldout read in this stage. Worker receives one anonymous request.
    outputs = {world: staged_discovery(payload) for world, payload in inputs.items()}
    write_new(ART / "sealed_discovery.json", outputs)
    write_new(ART / "selection_seal.json", {"commitment_commit_sha": git("rev-parse", "HEAD"),
        "commitment_sha256": digest(commitment), "selection_sha256": digest(outputs), "sealed_at": now(),
        "oracle_revealed": False, "heldout_accessed": False})
    print("Discovery sealed. Publish selection seal before revealing oracle or held-out.")


def check_bound_data(commitment, selection_seal, outputs, oracle, heldout):
    if digest(commitment) != selection_seal["commitment_sha256"]:
        raise ValueError("commitment changed")
    if digest(outputs) != selection_seal["selection_sha256"]:
        raise ValueError("selection changed after seal")
    if digest(oracle) != commitment["oracle_sha256"] or digest(heldout) != commitment["heldout_sha256"]:
        raise ValueError("oracle or held-out commitment mismatch")


def first_add(path):
    # Full reachable history, not path-simplified first-parent inference.
    introductions = []
    for sha in git("rev-list", "HEAD").splitlines():
        present = subprocess.run(["git", "-C", str(ROOT), "cat-file", "-e", sha + ":" + path], capture_output=True).returncode == 0
        if not present:
            continue
        parents = git("show", "-s", "--format=%P", sha).split()
        if not any(subprocess.run(["git", "-C", str(ROOT), "cat-file", "-e", p + ":" + path], capture_output=True).returncode == 0 for p in parents):
            introductions.append(sha)
    if len(introductions) != 1:
        raise ValueError("expected unique introduction: " + path)
    return introductions[0]


def verify_chronology(commitment, selection, evaluation):
    anchor = read(ART / "anchor.json")
    chain = [anchor["freeze_sha"], commitment["source_sha"], selection["commitment_commit_sha"], evaluation["selection_commit_sha"]]
    for parent, child in zip(chain, chain[1:]):
        if parent == child:
            raise ValueError("custody stages require distinct commits")
        git("merge-base", "--is-ancestor", parent, child)
    source_intro = first_add("Discovery/symbolic_benchmark_worlds.py")
    git("merge-base", "--is-ancestor", anchor["freeze_sha"], source_intro)
    if datetime.fromisoformat(git("show", "-s", "--format=%cI", source_intro)) <= datetime.fromisoformat(anchor["created_at"]):
        raise ValueError("generator introduction predates anchor")
    if first_add(REL + "/commitment.json") != selection["commitment_commit_sha"]:
        raise ValueError("oracle commitment was not anchored before discovery")
    if first_add(REL + "/selection_seal.json") != evaluation["selection_commit_sha"]:
        raise ValueError("selection was not anchored before evaluation")
    for file in ("oracle_reveal.json", "heldout_reveal.json", "evaluation.json"):
        intro = first_add(REL + "/" + file)
        if intro == evaluation["selection_commit_sha"]:
            raise ValueError("truth revealed in selection commit")
        git("merge-base", "--is-ancestor", evaluation["selection_commit_sha"], intro)
    for earlier in chain[:-1]:
        if subprocess.run(["git", "-C", str(ROOT), "cat-file", "-e", earlier + ":" + REL + "/oracle_reveal.json"], capture_output=True).returncode == 0:
            raise ValueError("premature oracle reveal")


def boundary_controls(prereg, public, eligibility, outputs, oracle, heldout, commitment, selection):
    """Real-epoch integrity challenges; no new seed, refit or selection."""
    controls = {}
    baseline = evaluate(prereg, public, eligibility, outputs, oracle, heldout)
    controls["1_leakage"] = baseline["scientific_checks"]["B_leakage"]
    before = digest(outputs)
    changed = copy.deepcopy(heldout)
    for rows in changed.values():
        for row in rows:
            row["target"] *= 10
    altered = evaluate(prereg, public, eligibility, outputs, oracle, changed)
    rejected = False
    try:
        check_bound_data(commitment, selection, outputs, oracle, changed)
    except ValueError:
        rejected = True
    controls["2_heldout_seal"] = rejected and digest(outputs) == before and any(
        baseline["worlds"][w]["heldout_rmse"] != altered["worlds"][w]["heldout_rmse"] for w in outputs)
    controls["3_oracle_separation"] = all(
        set(o["staged_source_sha256"]) == set(ENGINE_FILES) and
        o["worker_sha256"] == hashlib.sha256(WORKER.encode()).hexdigest() and
        all(p in {"<stage>/" + f for f in ENGINE_FILES} for p in o["staged_reads"]) and
        set(o["discovery_modules"]) <= {"Discovery"} | {p[:-3].replace("/", ".") for p in ENGINE_FILES}
        for o in outputs.values())
    controls["4_equivalence"] = all(
        len({c["class_id"] for c in o["discovery"]["ranking"]}) == o["discovery"]["class_count"] and
        o["discovery"]["equivalence_map"] == {c["class_id"]: c["members"] for c in o["discovery"]["ranking"]}
        for o in outputs.values()) and baseline["scientific_checks"]["C_equivalence"]
    controls["5_no_significance_credit"] = all(c["evidence_class"] == EVIDENCE and c["scientific_significance"] == "not_assigned"
        for o in outputs.values() for c in o["discovery"]["ranking"])
    controls["6_negative_pipeline"] = bool(outputs["D"]["discovery"]["ranking"]) and baseline["worlds"]["D"]["paired_input_contradiction"]
    controls["7_metric_oracle"] = all(abs(c["training_rmse"] - math.sqrt(sum(
        (math.log(c["coefficient"] * math.prod(row["features"][k] ** float(v) for k, v in c["representative"].items()) / row["target"])) ** 2
        for row in public[w]["train"]) / len(public[w]["train"]))) < 1e-12
        for w, o in outputs.items() for c in o["discovery"]["ranking"])
    return controls


def finalize():
    import unittest
    suite = unittest.defaultTestLoader.loadTestsFromName("tests.test_symbolic_benchmark")
    runner = unittest.TextTestRunner(verbosity=2)
    executed = runner.run(suite)
    args = [read(ART / p) for p in ("preregistration.v1.json", "public.json", "eligibility.json", "sealed_discovery.json", "oracle_reveal.json", "heldout_reveal.json", "commitment.json", "selection_seal.json")]
    controls = boundary_controls(*args)
    receipt = {"fixture_tests_run": executed.testsRun, "fixture_tests_passed": executed.wasSuccessful(),
               "tests_sha256": hashlib.sha256((ROOT / "tests/test_symbolic_benchmark.py").read_bytes()).hexdigest(),
               "real_epoch_controls": controls, "source_sha": args[-2]["source_sha"], "selection_sha256": args[-1]["selection_sha256"]}
    write_new(ART / "boundary_controls.json", receipt)
    scientific = read(ART / "evaluation.json")["scientific_disposition"]
    final = scientific if executed.wasSuccessful() and all(controls.values()) else "BENCHMARK_0_FAIL"
    write_new(ART / "result.json", {"disposition": final, "scientific_disposition": scientific,
        "integrity_controls_pass": executed.wasSuccessful() and all(controls.values()),
        "review_status": "PROVISIONAL — INDEPENDENT AUDIT PENDING", "evidence_class": EVIDENCE,
        "evaluation_sha256": digest(read(ART / "evaluation.json")), "controls_sha256": digest(receipt),
        "source_sha": receipt["source_sha"], "selection_sha256": receipt["selection_sha256"],
        "scientific_law_claim": False})
    print(final)


def evaluate(prereg, public, eligibility, outputs, oracle, heldout):
    """Post-seal evaluator. Never calls discovery or refits a scored coefficient."""
    thresholds = prereg["thresholds"]
    metrics, checks = {}, {}
    for world, wrapped in outputs.items():
        result, truth = wrapped["discovery"], oracle["worlds"][world]
        ranking = result["ranking"]
        cid = class_id(signature(truth["base_signature"])) if truth["single_family_member"] else None
        true = next((c for c in ranking if c["class_id"] == cid), None)
        top = ranking[0] if ranking else None
        errors = {c["class_id"]: rmse(c["representative"], c["log_coefficient"], heldout[world]) for c in ranking}
        false_positives = [{"class_id": c["class_id"], "expanded": c["expanded"],
            "rank": c["rank"], "validation_rmse": c["validation_rmse"], "heldout_rmse": errors[c["class_id"]],
            "expanded_complexity": c["expanded_complexity"],
            "validation_survives": c["validation_rmse"] <= 0.03, "heldout_survives": errors[c["class_id"]] <= 0.03,
            "reason": "predictive tolerance permits an incorrect structural class; no significance assigned",
            "evidence_class": EVIDENCE} for c in ranking if c["class_id"] != cid and
            (c["validation_rmse"] <= 0.03 or errors[c["class_id"]] <= 0.03)]
        selected_irrelevant = sorted(set(top["expanded"]) & set(truth["irrelevant_atoms"])) if top else []
        ablation_changes = sum(result["ablations"][k]["top_class"] != result["top_class"] for k in truth["irrelevant_atoms"])
        m = {"eligible_true_class_rank": true["rank"] if true else None,
             "true_class_rank_applicability": "in_family" if cid else "no single true class in family",
             "selected_class": result["top_class"], "pre_reveal_decision": result["decision"],
             "dimensional_system": result["dimensional_system"], "eligible_class_count": len(ranking),
             "training_rmse": top["training_rmse"] if top else None,
             "validation_rmse": top["validation_rmse"] if top else None,
             "heldout_rmse": errors[result["top_class"]] if top else None,
             "all_candidate_heldout_rmse": errors,
             "true_class_surface_count": len(true["members"]) if true else 0,
             "surface_count": result["surface_count"], "equivalence_class_count": result["class_count"],
             "irrelevant_ablation_changes": ablation_changes, "selected_irrelevant_atoms": selected_irrelevant,
             "irrelevant_robustness_applicability": bool(truth["irrelevant_atoms"]),
             "false_positives": false_positives, "false_positive_count": len(false_positives),
             "selected_expanded_complexity": top["expanded_complexity"] if top else None,
             "true_expanded_complexity": sum(abs(int(v)) for v in truth["base_signature"].values()) if cid else None,
             "coefficient_relative_error": abs(top["coefficient"] / truth["coefficient"] - 1) if top and cid else None,
             "leakage_rejection": {"applicable": world == "B", "rejected": sorted(k for k, v in eligibility[world].items() if v["status"] == "ineligible")},
             "group_training_validation": result["group_diagnostics"],
             "group_heldout_rmse": {g: rmse(top["representative"], top["log_coefficient"], [r for r in heldout[world] if r["group"] == g]) for g in truth["regime_multipliers"]} if top else {},
             "evidence_class": EVIDENCE, "scientific_law_claim": False}
        if world in "ABC":
            bound = thresholds["clean_rmse_max" if world == "A" else world + "_rmse_max"]
            checks[world + "_recovery"] = bool(top and true and true["rank"] == thresholds["true_class_rank_required"] and
                result["decision"] == "stable_candidate" and max(m["training_rmse"], m["validation_rmse"], m["heldout_rmse"]) <= bound and
                m["coefficient_relative_error"] <= thresholds["coefficient_relative_error_max"] and
                m["selected_expanded_complexity"] == m["true_expanded_complexity"])
        if world == "B":
            # Evaluator-only counterfactual; forbidden to the discovery API.
            leak_train = rmse({"leak": "1"}, 0.0, public[world]["train"])
            leak_valid = rmse({"leak": "1"}, 0.0, public[world]["validation"])
            m["leakage_rejection"].update({"disabled_eligibility_training_rmse": leak_train,
                "disabled_eligibility_validation_rmse": leak_valid,
                "counterfactual_receives_credit": False})
            checks["B_leakage"] = (m["leakage_rejection"]["rejected"] == ["leak", "leak_alias"] and
                not any(set(member) & {"leak", "leak_alias"} for c in ranking for member in c["members"]) and
                true is not None and leak_train < true["training_rmse"] and leak_valid < true["validation_rmse"])
        if world == "C":
            checks["C_equivalence"] = m["true_class_surface_count"] >= thresholds["C_true_class_surface_members_min"]
            checks["C_irrelevant_robustness"] = ablation_changes <= thresholds["C_irrelevant_ablation_top_class_changes_max"] and len(selected_irrelevant) <= thresholds["C_selected_irrelevant_factors_max"]
            m["dimensional_near_miss"] = {"surface": {"velocity": "1"}, "eligible": False,
                "reason": "L T^-1 differs from target L T^-2", "present_in_candidates": any(member == {"velocity": "1"} for c in ranking for member in c["members"])}
        if world == "D":
            pairs = [heldout[world][i:i+2] for i in range(0, len(heldout[world]), 2)]
            contradiction = all(a["features"] == b["features"] and abs(b["target"] / a["target"] - 4) < 1e-12 for a, b in pairs)
            m["paired_input_contradiction"] = contradiction
            m["any_deterministic_predictor_paired_log_rmse_lower_bound"] = math.log(4) / 2
            checks["D_negative"] = bool(top and result["decision"] == thresholds["D_decision_required"] and contradiction and
                m["heldout_rmse"] >= thresholds["D_heldout_rmse_min"] and min(errors.values()) >= thresholds["D_all_classes_heldout_rmse_min"])
        metrics[world] = m
    science_ok = all(checks.values())
    disposition = "BENCHMARK_0_PASS" if science_ok else ("BENCHMARK_0_PARTIAL" if any(checks[k] for k in ("A_recovery", "B_recovery", "C_recovery", "D_negative")) else "BENCHMARK_0_FAIL")
    return {"scientific_disposition": disposition, "scientific_checks": checks, "worlds": metrics,
            "evidence_class": EVIDENCE, "nonclaims": prereg["nonclaims"]}


def reveal():
    require_committed(ART / "selection_seal.json")
    commitment, selection, outputs = (read(ART / p) for p in ("commitment.json", "selection_seal.json", "sealed_discovery.json"))
    # First evaluator access to private truth and held-out outcomes is after seal commit.
    oracle, heldout = read(PRIVATE / "oracle.json"), read(PRIVATE / "heldout.json")
    check_bound_data(commitment, selection, outputs, oracle, heldout)
    write_new(ART / "oracle_reveal.json", oracle)
    write_new(ART / "heldout_reveal.json", heldout)
    result = evaluate(read(ART / "preregistration.v1.json"), read(ART / "public.json"), read(ART / "eligibility.json"), outputs, oracle, heldout)
    result["selection_commit_sha"] = git("rev-parse", "HEAD")
    result["evaluated_at"] = now()
    write_new(ART / "evaluation.json", result)
    print(result["scientific_disposition"] + " — boundary control validation pending")


def check():
    verify_freeze()
    commitment, selection, outputs, oracle, heldout = (read(ART / p) for p in ("commitment.json", "selection_seal.json", "sealed_discovery.json", "oracle_reveal.json", "heldout_reveal.json"))
    check_bound_data(commitment, selection, outputs, oracle, heldout)
    verify_committed_source_state(ROOT, commitment["source_sha"], source_paths=SOURCE_FILES, artifact_label="Benchmark 0")
    public = read(ART / "public.json")
    inputs, eligibility = {}, {}
    for world, raw in public.items():
        inputs[world], eligibility[world] = prepare(raw)
    for name, value in (("public", public), ("inputs", inputs), ("eligibility", eligibility)):
        if digest(value) != commitment[name + "_sha256"]:
            raise ValueError(name + " differs from committed epoch")
    if inputs != read(ART / "discovery_inputs.json") or eligibility != read(ART / "eligibility.json"):
        raise ValueError("staged input/classification artifact altered")
    prereg = read(ART / "preregistration.v1.json")
    # Explicit deterministic reproducibility check, never choose another seed.
    regenerated = generate(prereg, oracle["seed"])
    if tuple(map(digest, regenerated)) != tuple(map(digest, (public, heldout, oracle))):
        raise ValueError("world regeneration mismatch")
    for world, payload in inputs.items():
        actual = staged_discovery(payload)
        if actual != outputs[world]:
            raise ValueError("sealed discovery is not reproducible")
    expected = evaluate(prereg, public, eligibility, outputs, oracle, heldout)
    saved = read(ART / "evaluation.json")
    if expected != {k: v for k, v in saved.items() if k not in ("selection_commit_sha", "evaluated_at")}:
        raise ValueError("evaluation mismatch")
    for path, epoch in (("commitment.json", selection["commitment_commit_sha"]),
                        ("selection_seal.json", saved["selection_commit_sha"])):
        if git("show", epoch + ":" + REL + "/" + path) != (ART / path).read_text().strip():
            raise ValueError("stage absent at recorded commit")
        git("merge-base", "--is-ancestor", epoch, "HEAD")
    verify_chronology(commitment, selection, saved)
    receipt, final = read(ART / "boundary_controls.json"), read(ART / "result.json")
    controls = boundary_controls(prereg, public, eligibility, outputs, oracle, heldout, commitment, selection)
    if receipt["real_epoch_controls"] != controls or receipt["tests_sha256"] != hashlib.sha256((ROOT / "tests/test_symbolic_benchmark.py").read_bytes()).hexdigest():
        raise ValueError("boundary controls stale")
    integrity = receipt["fixture_tests_passed"] and receipt["fixture_tests_run"] == 7 and all(controls.values())
    if (final["evaluation_sha256"] != digest(saved) or final["controls_sha256"] != digest(receipt) or
        final["integrity_controls_pass"] != integrity or
        final["disposition"] != (saved["scientific_disposition"] if integrity else "BENCHMARK_0_FAIL") or
        final["scientific_law_claim"] is not False):
        raise ValueError("final classification/claim boundary inconsistent")
    print("Benchmark 0 commitments, source, blinding replay and evaluation are current.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", nargs="?", choices=("realize", "seal", "reveal", "finalize"))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        check()
    elif args.stage:
        try:
            {"realize": realize, "seal": seal, "reveal": reveal, "finalize": finalize}[args.stage]()
        except Exception as error:
            failed = ART / "failed_epochs" / (args.stage + "-" + git("rev-parse", "HEAD") + ".json")
            if not failed.exists():
                write_new(failed, {"stage": args.stage, "head": git("rev-parse", "HEAD"), "time": now(),
                    "error": type(error).__name__, "detail": str(error), "traceback": traceback.format_exc(),
                    "classification": "operational defect pending diagnosis; no scientific score tuning authorized"})
            raise
    else:
        parser.error("choose a stage or --check")


if __name__ == "__main__":
    main()
