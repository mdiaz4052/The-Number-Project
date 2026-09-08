"""Behavioral oracles are separate from committed-artifact freshness tests."""

import ast
from copy import deepcopy
from itertools import product
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from Discovery import g_measurement_joint_inference as j


def synthetic(verdicts=('compatible', 'compatible', 'compatible'), indices=(1, 1, 0)):
    """Minimal certificate semantics, with no historical computations or source access."""
    candidates = [{'parameter': {'numerator': '0', 'denominator': '1'}},
                  {'parameter': {'numerator': '-1', 'denominator': '8'}}]
    schedule = {'parameters': ['0', '-1/8']}
    def decision(verdict, index, key):
        return {'outcome': verdict, 'witness':
                {'candidate_index': index, key: True} if verdict == 'compatible' else None}
    h = {'schema_version': 1, 'artifact_id': j.ARTIFACT_IDS[0],
         'decision': decision(verdicts[0], indices[0], 'input_and_comparison_membership_verified'),
         'calculation': {'candidates': deepcopy(candidates)}, 'candidate_schedule': schedule}
    s = {'schema_version': 1, 'artifact_id': j.ARTIFACT_IDS[1],
         'scope_order': ['statistical', 'systematic'], 'candidate_schedule': schedule,
         'terminal_decisions': {scope: decision(verdicts[i+1], indices[i+1], 'membership_verified')
                                for i, scope in enumerate(j.REQUIRED_SCOPES[1])},
         'calculations': {scope: {'candidates': deepcopy(candidates)} for scope in j.REQUIRED_SCOPES[1]}}
    return {j.ARTIFACT_IDS[0]: h, j.ARTIFACT_IDS[1]: s}


class JointBehaviorTests(unittest.TestCase):
    def test_all_27_verdict_combinations(self):
        seen = set()
        for verdicts in product(('compatible', 'incompatible', 'unresolved'), repeat=3):
            with self.subTest(verdicts=verdicts):
                pubs, joint = j.compose(synthetic(verdicts))
                expected = ('not_all_representable' if 'incompatible' in verdicts else
                            'undetermined' if 'unresolved' in verdicts else
                            'all_representable_under_separate_declared_models')
                self.assertEqual(joint['status'], expected)
                seen.add(joint['status'])
                for publication, inputs in zip(pubs, (verdicts[:1], verdicts[1:])):
                    expected_pub = ('not_representable' if 'incompatible' in inputs else
                                    'undetermined' if 'unresolved' in inputs else 'representable')
                    self.assertEqual(publication['status'], expected_pub)
                    self.assertEqual(len(publication['reasoning_trace']['operands']), len(inputs))
        self.assertEqual(seen, {'all_representable_under_separate_declared_models',
                               'not_all_representable', 'undetermined'})

    def test_exact_parameter_decoding(self):
        from fractions import Fraction
        self.assertEqual(j.parameter({"numerator": "-1", "denominator": "8"}), Fraction(-1, 8))
        self.assertEqual(j.parameter({"numerator": "0", "denominator": "1"}), Fraction(0))

    def test_scope_mapping_and_invalid_verdicts(self):
        for verdict, status in [('compatible', 'representable'), ('incompatible', 'not_representable'),
                                ('unresolved', 'undetermined')]:
            self.assertEqual(j.scope_status(verdict), status)
        for verdict in ('', 'unknown', None, True, [], 'representable'):
            with self.assertRaises(j.InferenceError): j.scope_status(verdict)

    def test_both_publications_are_required_and_used(self):
        for verdicts in [('incompatible', 'compatible', 'compatible'),
                         ('compatible', 'incompatible', 'compatible'),
                         ('compatible', 'compatible', 'incompatible')]:
            pubs, joint = j.compose(synthetic(verdicts))
            self.assertEqual(len(pubs), 2)
            self.assertEqual(joint['status'], 'not_all_representable')
        for missing in j.ARTIFACT_IDS:
            data = synthetic(); del data[missing]
            with self.assertRaises(j.InferenceError): j.compose(data)
        with self.assertRaises(j.InferenceError): j.joint_decision([])
        pubs, _ = j.compose(synthetic())
        with self.assertRaises(j.InferenceError): j.joint_decision([pubs[0], pubs[0]])

    def test_required_scope_projection_and_missing_scope(self):
        data = synthetic(); identifier = j.ARTIFACT_IDS[1]
        p = j.project_publication(data[identifier], identifier)
        self.assertEqual(set(p['scopes']), {'statistical', 'systematic'})
        for field in ('terminal_decisions', 'calculations'):
            for scope in ('statistical', 'systematic'):
                bad = deepcopy(data[identifier]); del bad[field][scope]
                with self.assertRaises(j.InferenceError): j.project_publication(bad, identifier)
        del p['scopes']['systematic']
        with self.assertRaises(j.InferenceError): j.publication_decision(p)

    def test_midpoint_characterization_and_truth_invariance(self):
        for indices in product((0, 1), repeat=3):
            pubs, joint = j.compose(synthetic(indices=indices))
            scopes = [pubs[0]['scopes']['combined'], pubs[1]['scopes']['statistical'],
                      pubs[1]['scopes']['systematic']]
            for scope, index in zip(scopes, indices):
                self.assertEqual(scope['unshifted_midpoint_consistent'], index == 0)
                self.assertEqual(scope['witness_kind'], 'unshifted_midpoint' if index == 0 else 'shifted_scheduled')
                self.assertEqual(scope['witness']['candidate_index'], index)
            self.assertEqual(joint['status'], 'all_representable_under_separate_declared_models')
            for pub in pubs:
                before = j.publication_decision(pub)['status']
                changed = deepcopy(pub)
                for scope in changed['scopes'].values():
                    scope['unshifted_midpoint_consistent'] = 'irrelevant'
                    scope['witness_kind'] = 'irrelevant'
                self.assertEqual(j.publication_decision(changed)['status'], before)
        pubs, _ = j.compose(synthetic(('unresolved', 'incompatible', 'unresolved')))
        for pub in pubs:
            for scope in pub['scopes'].values():
                self.assertIsNone(scope['witness'])
                self.assertIsNone(scope['witness_kind'])
                self.assertIsNone(scope['unshifted_midpoint_consistent'])

    def test_malformed_witness_identity_fails(self):
        h = synthetic()[j.ARTIFACT_IDS[0]]
        for field, value in [('candidate_index', -1), ('candidate_index', True),
                             ('candidate_index', 99), ('input_and_comparison_membership_verified', False)]:
            bad = deepcopy(h); bad['decision']['witness'][field] = value
            with self.assertRaises(j.InferenceError): j.project_publication(bad, j.ARTIFACT_IDS[0])
        bad = deepcopy(h); bad['calculation']['candidates'][1]['parameter']['numerator'] = '0'
        with self.assertRaises(j.InferenceError): j.project_publication(bad, j.ARTIFACT_IDS[0])
        bad = deepcopy(h); bad['decision']['outcome'] = 'unresolved'
        with self.assertRaises(j.InferenceError): j.project_publication(bad, j.ARTIFACT_IDS[0])

    def test_e001_path_allowlist(self):
        for path in j.INPUT_PATHS: self.assertTrue(j.input_path_allowed(path))
        forbidden = ['hust_2018_aaf_source_audit_v1.manifest.json',
                     'hust_2018_aaf_depth_2b_authorization_v1.json',
                     'hust_2018_aaf_depth_2b_authorization_v2.json',
                     'hust_2018_aaf_combined_measurement_model_v1.json']
        for filename in forbidden:
            path = str(j.DIRECTORY / filename)
            self.assertFalse(j.input_path_allowed(path))
            with patch.object(Path, 'read_bytes', side_effect=AssertionError('forbidden read')):
                with self.assertRaises(j.InferenceError): j.load_certificate(j.ROOT, path, {'path': path})
        for path in ('./'+j.INPUT_PATHS[0], '/'+j.INPUT_PATHS[0], 'other.json'):
            self.assertFalse(j.input_path_allowed(path))

    def test_central_values_cannot_affect_truth_or_projection(self):
        original = synthetic(); expected = j.compose(original)
        for value in (-10**100, 0, 1, 10**100):
            data = deepcopy(original)
            for certificate in data.values():
                certificate.update(central_G=value, absolute_standard_uncertainty=value,
                                   covariance=[[value]], weights=[value], probability=value)
            self.assertEqual(j.compose(data), expected)
            p = j.project_publication(data[j.ARTIFACT_IDS[1]], j.ARTIFACT_IDS[1])
            before = j.publication_decision(p)['status']
            for scope in p['scopes'].values():
                scope.update(central_G=value, uncertainty=value, covariance=[[value]], evidence_score=value)
            self.assertEqual(j.publication_decision(p)['status'], before)

    def test_pure_composition_never_retrieves_sources(self):
        with patch.object(Path, 'read_bytes', side_effect=AssertionError('filesystem retrieval')), \
             patch.object(j.subprocess, 'run', side_effect=AssertionError('external retrieval')):
            pubs, joint = j.compose(synthetic())
        self.assertEqual(len(pubs), 2)
        self.assertEqual(joint['logical_operator'], 'conjunction')

    def test_projection_keys_exclude_numerical_and_statistical_fields(self):
        pubs, joint = j.compose(synthetic())
        fields = {'scope', 'original_verdict', 'scope_status', 'witness',
                  'unshifted_midpoint_consistent', 'witness_kind'}
        for p in pubs:
            for s in p['scopes'].values():
                self.assertEqual(set(s), fields)
                self.assertEqual(set(s['witness']), {'candidate_index', 'parameter',
                                                   'membership_verified', 'candidate_pointer'})
        self.assertEqual(set(joint), {'status', 'logical_operator', 'domains', 'reasoning_trace'})
        self.assertEqual(joint['domains'], 'source_specific_and_uncoupled')


class JointArtifactTests(unittest.TestCase):
    def certificates(self):
        protocol = j.load_protocol()
        return {p['artifact_id']: j.load_certificate(j.ROOT, p['path'], p) for p in protocol['inputs']}

    def test_input_pins_ancestry_freeze_and_preservation(self):
        p = j.verify_preregistration()
        self.assertEqual(tuple(x['path'] for x in p['inputs']), j.INPUT_PATHS)
        self.assertEqual(tuple(x['sha256'] for x in p['inputs']), (
            'd04a1837ba66514930668303eb059442bde237c83f0bb6a3a274f1eea3af99b5',
            '9ab2dc127cd6dc7cbb56192fab28527f6a5ad9dde10c54c53ded5c656c7600e3'))
        j.verify_inputs(j.ROOT, p)
        j.verify_preserved_files()
        bad = deepcopy(p); bad['inputs'][0]['generating_verification_epoch'] = '0'*40
        with self.assertRaises(j.subprocess.CalledProcessError): j.verify_inputs(j.ROOT, bad)

    def test_wrong_missing_and_substituted_inputs(self):
        pin = j.load_protocol()['inputs'][0]
        with TemporaryDirectory() as temp:
            root = Path(temp); target = root / pin['path']; target.parent.mkdir(parents=True)
            with self.assertRaises(OSError): j.load_certificate(root, pin['path'], pin)
            for data in (b'{}', (j.ROOT/j.INPUT_PATHS[1]).read_bytes(),
                         (j.ROOT/pin['path']).read_bytes()+b' '):
                target.write_bytes(data)
                with self.assertRaises(j.InferenceError): j.load_certificate(root, pin['path'], pin)
            target.unlink(); target.symlink_to(j.ROOT/pin['path'])
            with self.assertRaises(j.InferenceError): j.load_certificate(root, pin['path'], pin)
        cert = self.certificates()[j.ARTIFACT_IDS[0]]; cert['artifact_id'] = j.ARTIFACT_IDS[1]
        with self.assertRaises(j.InferenceError): j.project_publication(cert, j.ARTIFACT_IDS[0])
        for data in (b'{"x":1,"x":2}', b'{"x":NaN}'):
            with self.assertRaises(j.InferenceError): j.read_json(data)

    def test_current_characterization_derived_from_existing_witnesses(self):
        pubs, _ = j.compose(self.certificates())
        scopes = [pubs[0]['scopes']['combined'], pubs[1]['scopes']['statistical'],
                  pubs[1]['scopes']['systematic']]
        self.assertEqual([s['unshifted_midpoint_consistent'] for s in scopes], [False, False, True])
        self.assertEqual([s['witness_kind'] for s in scopes],
                         ['shifted_scheduled', 'shifted_scheduled', 'unshifted_midpoint'])

    def test_only_allowed_files_opened_and_no_numerical_projection(self):
        protocol = j.load_protocol(); opened = []
        real = Path.read_bytes
        def read(path):
            opened.append(path.relative_to(j.ROOT).as_posix())
            return real(path)
        with patch.object(Path, 'read_bytes', read):
            certs = {p['artifact_id']: j.load_certificate(j.ROOT, p['path'], p) for p in protocol['inputs']}
            projected = j.compose(certs)
        self.assertEqual(opened, list(j.INPUT_PATHS))
        text = j.serialize_artifact(projected)
        for field in protocol['forbidden_projection_fields']:
            self.assertNotIn('"'+field+'":', text)
        # Hostile numerical fields anywhere in the full certificates cannot enter projection.
        def contaminate(value):
            if isinstance(value, dict):
                for key in list(value):
                    if key in {'combined_central_value', 'central_value', 'weights',
                               'propagation_coefficients', 'relative_uncertainty_ppm'}:
                        value[key] = {'hostile': 'not a number'}
                    else: contaminate(value[key])
            elif isinstance(value, list):
                for item in value: contaminate(item)
        contaminate(certs)
        self.assertEqual(j.compose(certs), projected)

    def test_dependency_graph_excludes_historical_calculators_and_e001(self):
        pending = ['Discovery/g_measurement_joint_inference.py']; seen = set()
        allowed = {'Discovery/g_measurement_joint_inference.py',
                   'Discovery/preregistration_history.py', 'Discovery/source_history.py'}
        while pending:
            path = pending.pop()
            if path in seen: continue
            seen.add(path)
            tree = ast.parse((j.ROOT/path).read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith('Discovery.'):
                    pending.append(node.module.replace('.', '/')+'.py')
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self.assertNotIn(alias.name.split('.')[0], {'requests','urllib','http','socket'})
                        if alias.name.startswith('Discovery.'):
                            pending.append(alias.name.replace('.', '/')+'.py')
        self.assertEqual(seen, allowed)
        # HUST projection requires only its established result, without its source files.
        h = self.certificates()[j.ARTIFACT_IDS[0]]
        with patch.object(Path, 'read_bytes', side_effect=AssertionError('source access')):
            p = j.project_publication(h, j.ARTIFACT_IDS[0])
        self.assertEqual(p['required_scopes'], ['combined'])

    def test_result_freshness_schema_and_trace(self):
        artifact = j.build_artifact()
        self.assertEqual(j.serialize_artifact(artifact), (j.ROOT/j.DEFAULT_OUTPUT).read_text())
        protocol = j.load_protocol()
        self.assertEqual(set(artifact), set(protocol['output_schema']['top_level_fields']))
        pubs, expected = j.compose(self.certificates())
        self.assertEqual(artifact['publications'], pubs)
        self.assertEqual(artifact['joint_decision'], expected)
        self.assertEqual(artifact['nonclaims'], protocol['claim_limits'])
        for p in pubs:
            self.assertEqual(set(p), set(protocol['output_schema']['publication_fields']))


if __name__ == '__main__':
    unittest.main()
