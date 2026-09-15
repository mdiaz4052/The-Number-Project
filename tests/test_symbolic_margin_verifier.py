"""Adversarial schema-envelope fixtures; no scientific regeneration or fitting."""
import ast
import copy
from pathlib import Path
import unittest
from Discovery.symbolic_benchmark_engine import digest
from Discovery import symbolic_margin_verifier as verifier


class ResultEnvelopeTests(unittest.TestCase):
    def test_explicit_schemas_and_exact_payload_binding(self):
        summary = {'schema': 'tnp-margin1/summary-v1', 'disposition': 'FIXTURE_PARTIAL', 'cells': {'a': 1}}
        records, controls = {'r': {'metric': .052}}, {'checked': True}
        result = {**summary, 'schema': 'tnp-margin1/raw-result-v1', 'source_sha': 'source', 'selection_commit_sha': 'selection',
                  'evaluation_sha256': digest(records), 'controls_sha256': digest(controls),
                  'summary_sha256': digest(summary), 'evaluated_at': 'fixture time'}
        verifier.bind_result(summary, result, records, controls)
        for field, value in [('schema', summary['schema']), ('disposition', 'FIXTURE_COMPLETE'), ('cells', {'a': 2}),
                             ('evaluation_sha256', 'wrong'), ('controls_sha256', 'wrong'), ('summary_sha256', 'wrong'), ('extra', 1)]:
            changed = copy.deepcopy(result); changed[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                verifier.bind_result(summary, changed, records, controls)
        changed_summary = {**summary, 'schema': 'unknown'}
        with self.assertRaises(ValueError): verifier.bind_result(changed_summary, result, records, controls)

    def test_reconciliation_never_regenerates_discovers_or_fits(self):
        tree = ast.parse(Path(verifier.__file__).read_text())
        for func in [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in ('reconcile', 'assess', 'verify_science', 'bind_result', 'routes')]:
            calls = {n.func.attr if isinstance(n.func, ast.Attribute) else n.func.id if isinstance(n.func, ast.Name) else ''
                     for n in ast.walk(func) if isinstance(n, ast.Call)}
            self.assertFalse(calls & {'generate', 'discover', 'staged_discovery', 'fit', 'seed', 'make_index'})


if __name__ == '__main__': unittest.main()
