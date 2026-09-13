import copy
import unittest

from Discovery import symbolic_benchmark_receipt as receipt


class ReceiptCorrectionTests(unittest.TestCase):
    def test_open_event_precedes_failed_read(self):
        self.assertEqual(receipt.probe()["observation"], {"open_attempts": ["open_event"], "errno": 2, "exists": False})

    def test_exact_known_cache_attempts_only_and_manifest_binding(self):
        modules = receipt.MODULES
        hashes = {"Discovery/" + m + ".py": "fixture" for m in modules}
        fixture = {"staged_source_sha256": hashes,
            "discovery_modules": ["Discovery"] + ["Discovery." + m for m in modules if m != "__init__"],
            "staged_reads": ["<stage>/Discovery/" + m + ".py" for m in modules] +
                            ["<stage>/Discovery/__pycache__/" + m + ".cpython-312.pyc" for m in modules]}
        receipt.reconcile_trace(fixture, hashes, "cpython-312")
        for extra in ("<stage>/oracle.json", "<stage>/Discovery/__pycache__/oracle.cpython-312.pyc", "/tmp/heldout.json"):
            changed = copy.deepcopy(fixture)
            changed["staged_reads"].append(extra)
            with self.subTest(extra=extra), self.assertRaises(ValueError):
                receipt.reconcile_trace(changed, hashes, "cpython-312")
        changed = copy.deepcopy(fixture)
        changed["discovery_modules"].append("Discovery.symbolic_benchmark_worlds")
        with self.assertRaises(ValueError):
            receipt.reconcile_trace(changed, hashes, "cpython-312")
        changed = copy.deepcopy(fixture)
        changed["staged_source_sha256"]["Discovery/constants.py"] = "tampered"
        with self.assertRaises(ValueError):
            receipt.reconcile_trace(changed, hashes, "cpython-312")

    def test_correction_module_has_no_discovery_or_generator_execution_import(self):
        import ast
        import inspect
        tree = ast.parse(inspect.getsource(receipt))
        imports = [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
        self.assertNotIn("Discovery.symbolic_benchmark_worlds", imports)
        self.assertNotIn("Discovery.symbolic_benchmark", imports)
        called = {n.func.id for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
        self.assertNotIn("discover", called)
        self.assertNotIn("generate", called)
        self.assertNotIn("evaluate", called)
