"""Detached operational correction of Benchmark-0 open-attempt receipt semantics.

The original runner, worlds, rankings, metrics and FAIL record are immutable.
This module neither imports the generator nor calls discovery/evaluation.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

from Discovery.symbolic_benchmark_engine import digest, encoded
from Discovery.source_history import verify_committed_source_state

ROOT = Path(__file__).resolve().parents[1]
REL = "Experiments/SymbolicDiscovery/Benchmark0"
ART = ROOT / REL
RAW_EPOCH = "b01c01af1a30bbf8726842d3b05905a350cd5c1f"
SOURCE_PATHS = ("Discovery/symbolic_benchmark_receipt.py", "tests/test_symbolic_benchmark_receipt.py")
MODULES = ("__init__", "symbolic_benchmark_engine", "constants", "dimensions", "dimensional_search",
           "planck_identities", "dependency_definitions", "monomial_constraints")
RAW_PATHS = tuple(REL + "/" + p for p in (
    "preregistration.v1.json", "anchor.json", "commitment.json", "public.json", "discovery_inputs.json",
    "eligibility.json", "sealed_discovery.json", "selection_seal.json", "oracle_reveal.json",
    "heldout_reveal.json", "evaluation.json", "boundary_controls.json", "result.json", "operational_defect.json"))
PROBE = r'''
import sys, os, json
path = sys.argv[1]
attempts = []
def hook(event, args):
    if event == 'open' and args[0] == path:
        attempts.append('open_event')
sys.addaudithook(hook)
error = None
try:
    open(path, 'rb')
except FileNotFoundError as caught:
    error = caught.errno
print(json.dumps({'open_attempts': attempts, 'errno': error, 'exists': os.path.exists(path)}))
'''


def read(name):
    return json.loads((ART / name).read_text())


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args])


def probe():
    with tempfile.TemporaryDirectory(prefix="tnp-b0-cache-probe-") as directory:
        path = str(Path(directory) / "nonexistent.pyc")
        result = subprocess.run([sys.executable, "-I", "-B", "-c", PROBE, path], check=True, capture_output=True, text=True)
        observation = json.loads(result.stdout)
    return {"observation": observation, "probe_sha256": hashlib.sha256(PROBE.encode()).hexdigest(),
            "python_cache_tag": sys.implementation.cache_tag, "target_data_used": False}


def reconcile_trace(output, source_hashes, cache_tag):
    """Exact allowlist: only staged sources and their absent-cache open attempts."""
    py_paths = {"<stage>/Discovery/" + module + ".py" for module in MODULES}
    cache_paths = {"<stage>/Discovery/__pycache__/" + module + "." + cache_tag + ".pyc" for module in MODULES}
    if set(output["staged_reads"]) != py_paths | cache_paths:
        raise ValueError("unexpected or incomplete source/cache attempt trace")
    allowed_modules = {"Discovery"} | {"Discovery." + m for m in MODULES if m != "__init__"}
    if set(output["discovery_modules"]) != allowed_modules:
        raise ValueError("unexpected module import")
    if output["staged_source_sha256"] != source_hashes:
        raise ValueError("staged source manifest differs from immutable source")
    return {"source_paths": sorted(py_paths), "absent_cache_attempt_paths": sorted(cache_paths),
            "forbidden_path_or_module_observed": False}


def assess(probe_record):
    if probe_record != {"observation": {"open_attempts": ["open_event"], "errno": 2, "exists": False},
                        "probe_sha256": hashlib.sha256(PROBE.encode()).hexdigest(),
                        "python_cache_tag": "cpython-312", "target_data_used": False}:
        raise ValueError("missing cache-attempt semantic control or changed Python runtime")
    controls, raw, evaluation = read("boundary_controls.json"), read("result.json"), read("evaluation.json")
    expected_controls = {f"{i}_{name}": i != 3 for i, name in enumerate((
        "leakage", "heldout_seal", "oracle_separation", "equivalence", "no_significance_credit", "negative_pipeline", "metric_oracle"), 1)}
    if (controls["real_epoch_controls"] != expected_controls or controls["fixture_tests_run"] != 7 or
        controls["fixture_tests_passed"] is not True or raw["disposition"] != "BENCHMARK_0_FAIL"):
        raise ValueError("raw failure is not the diagnosed single receipt defect")
    source = read("commitment.json")["source_sha"]
    hashes = {"Discovery/" + m + ".py": hashlib.sha256(git("show", source + ":Discovery/" + m + ".py")).hexdigest() for m in MODULES}
    traces = {world: reconcile_trace(output, hashes, probe_record["python_cache_tag"])
              for world, output in read("sealed_discovery.json").items()}
    if set(traces) != {"A", "B", "C", "D"}:
        raise ValueError("four trace records required")
    return {"final_disposition": evaluation["scientific_disposition"], "raw_disposition": raw["disposition"],
        "raw_epoch_sha": RAW_EPOCH, "correction_class": "OPERATIONAL RECEIPT INTERPRETATION",
        "corrected_control": "3_oracle_separation", "corrected_control_pass": True,
        "world_traces": traces, "scientific_checks_unchanged": evaluation["scientific_checks"],
        "raw_record_sha256": {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in RAW_PATHS},
        "mechanism": "The audit hook runs on open attempts, before FileNotFoundError. Staging copies exactly the eight recorded .py files into a new empty directory; -B and the write-denying hook prohibit cache creation. Exact paired cache-miss attempts are not oracle access.",
        "no_new_realization_or_selection": True, "metrics_or_thresholds_changed": False,
        "review_status": "PROVISIONAL — INDEPENDENT AUDIT PENDING", "scientific_law_claim": False}


def check():
    record = read("receipt_reconciliation.json")
    verify_committed_source_state(ROOT, RAW_EPOCH, source_paths=RAW_PATHS, artifact_label="Benchmark 0 original failed epoch")
    verify_committed_source_state(ROOT, record["reconciliation_source_sha"], source_paths=SOURCE_PATHS, artifact_label="Benchmark 0 receipt reconciliation")
    expected = assess(read("cache_attempt_probe.json"))
    if expected != {k: v for k, v in record.items() if k != "reconciliation_source_sha"}:
        raise ValueError("receipt reconciliation stale or overbroad")
    print(record["final_disposition"] + "; raw failed epoch preserved; no scientific rerun.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        check()
        return
    if git("status", "--porcelain", "--untracked-files=no").strip():
        raise ValueError("commit reconciliation source before receipt")
    observed = probe()
    record = assess(observed)
    record["reconciliation_source_sha"] = git("rev-parse", "HEAD").decode().strip()
    for name, value in (("cache_attempt_probe.json", observed), ("receipt_reconciliation.json", record)):
        with (ART / name).open("xb") as output:
            output.write(encoded(value))
    print(record["final_disposition"] + "; detached operational correction only")


if __name__ == "__main__":
    main()
