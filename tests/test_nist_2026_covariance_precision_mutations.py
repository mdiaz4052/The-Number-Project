"""Small exact semantic counterexamples; no real-data/provenance guards earn kills."""
import copy
from fractions import Fraction as F
import unittest
from unittest.mock import patch

from Discovery import nist_2026_covariance_precision as n
from Discovery import nist_2026_covariance_precision_mutations as m


def radius_fixture():
    a = (F(1), F(2), F(1), F(1))
    center = (F(10**6), F(500000), F(10**6), F(10**6)) + (F(0),) * 6
    box = tuple((v, v) for v in center)
    box = box[:4] + ((F(-1, 5), F(1, 5)),) + box[5:]
    R = ((F(-1), F(1), F(0), F(0)),)
    return a, center, box, R


def two_leaf_tree():
    box = ((F(0), F(2)),)
    left, right = n.child_boxes(box, 0)
    nodes = {'': {'box': box, 'split_dimension': 0},
             '0': {'box': left, 'split_dimension': None}, '1': {'box': right, 'split_dimension': None}}
    return box, nodes


class PrecisionMutationBehaviorTests(unittest.TestCase):
    def test_precision_width(self):
        self.assertEqual(n.cell('3.2', '0.05'), (F(63, 20), F(13, 4)))

    def test_anchor_scaling(self):
        a = (F(1), F(2), F(3), F(4))
        s = (F(10**6),) * 4
        rho = (F(1, 5),) * 6
        expected = tuple(tuple(a[i] * a[j] * (F(1) if i == j else F(1, 5)) for j in range(4)) for i in range(4))
        V = n.covariance(a, s + rho)
        self.assertEqual(V, expected)
        # One-row cofactor oracle: Q=(x1-x0)^2/(V00+V11-2V01).
        R = ((F(-1), F(1), F(0), F(0)),)
        C = n.mm(n.mm(R, V), n.transpose(R))
        self.assertEqual(n.quadratic(n.inverse(C), n.mv(R, a)), F(5, 21))

    def test_signed_interval(self):
        self.assertEqual(n.interval_product((F(1), F(2)), (F(-3), F(4))), (F(-6), F(8)))

    def test_covariance_radius(self):
        a, center, box, R = radius_fixture()
        proof = n.local_certificate(R, n.covariance_enclosure(a, box), a, (F(0),) * 4)
        # Admissible rho01=+1/5 gives Q=1/(2-2/5)=5/8.
        self.assertGreaterEqual(proof['bounds'][1], F(5, 8))

    def test_inverse_order(self):
        a, center, box, R = radius_fixture()
        proof = n.local_certificate(R, n.covariance_enclosure(a, box), a, (F(0),) * 4)
        self.assertGreaterEqual(proof['bounds'][1], F(5, 8))

    def test_display_remainder(self):
        result = n.display_terms(((F(1),),), (F(0),), (F(1),))
        self.assertGreaterEqual(result['upper'], F(1))

    def test_partition_coverage(self):
        box, nodes = two_leaf_tree()
        with self.assertRaises(n.PrecisionError):
            n.validate_cover(nodes, ['0'], box)

    def test_false_variation(self):
        self.assertEqual(n.classify((F(0), F(2)), F(1), {'not_flagged': {}}), n.UNRESOLVED)

    def test_faulty_calibration(self):
        # Distinct from M6: nonzero center needs the full first-order term.
        self.assertGreaterEqual(n.display_terms(((F(1),),), (F(2),), (F(1),))['upper'], F(9))

    def test_equivalent_control(self):
        self.assertEqual(n.quadratic(((F(2), F(1)), (F(1), F(3))), (F(2), F(-1))), F(7))


class PrecisionMutationEvidenceTests(unittest.TestCase):
    def test_saved_evidence_only(self):
        with patch.object(m, 'run_case', side_effect=AssertionError('saved checker must not execute mutations')):
            result = m.check_artifact()
        self.assertEqual(result['production_killed'], 8)

    def test_invalid_kills_rejected(self):
        test = m.CASES[2]['tests']
        good = {'runner_status': 'completed', 'tests_run': 1, 'failing_tests': test, 'error_tests': [],
                'skipped_tests': [], 'successful': False, 'validated_imports_before': m.IMPORTS,
                'validated_imports_after': m.IMPORTS, 'observed_file_open_paths': sorted(set(m.COPY_PATHS) | {'tests/__init__.py'})}
        self.assertEqual(m.assess_execution(good, test), 'KILLED')
        for key, value in [('runner_status', 'invalid'), ('tests_run', 0), ('error_tests', test),
                           ('skipped_tests', test), ('failing_tests', ['unrelated']), ('successful', True),
                           ('validated_imports_after', {})]:
            modified = copy.deepcopy(good); modified[key] = value
            with self.assertRaises(m.MutationEvidenceError):
                m.assess_execution(modified, test)

    def test_patch_binding_and_tampered_evidence(self):
        source = (n.ROOT / n.MODULE).read_text()
        p = n._json((n.ROOT / n.PREREGISTRATION_PATH).read_bytes())
        m.validate_definitions(source, p)
        artifact = n._json((n.ROOT / m.OUTPUT).read_bytes())
        for key, value in [('applied_source_sha256', '0' * 64), ('outcome', 'KILLED')]:
            records = copy.deepcopy(artifact['records']); records[0][key] = value
            with self.assertRaises(m.MutationEvidenceError):
                m.validate_records(records, source)
