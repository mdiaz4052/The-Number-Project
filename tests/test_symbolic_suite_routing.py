"""Focused schema correction tests, including real immutable Benchmark0 keys."""
import ast
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from Discovery import symbolic_suite_routing as routing


class RoutingCorrectionTests(unittest.TestCase):
    def test_actual_accepted_baseline_keys(self):
        raw=routing.raw.read(routing.B0/'result.json')
        corrected=routing.raw.read(routing.B0/'receipt_reconciliation.json')
        self.assertEqual(raw['disposition'],'BENCHMARK_0_FAIL')
        self.assertNotIn('disposition',corrected)
        self.assertEqual(corrected['final_disposition'],'BENCHMARK_0_PASS')
        entry=routing.route(routing.B0/'receipt_reconciliation.json','final_disposition','a1016953d5289dd9eca211c8b736d8d08f1a6153')
        self.assertEqual(entry['disposition'],'BENCHMARK_0_PASS')
        with self.assertRaises(ValueError): routing.route(routing.B0/'receipt_reconciliation.json','disposition',entry['source_commit_sha'])

    def test_correction_delegates_to_frozen_evaluation_without_discovery(self):
        module=ast.parse(Path(routing.__file__).read_text())
        for name in ('verify_raw_science','assess','reconcile'):
            function=next(n for n in module.body if isinstance(n,ast.FunctionDef) and n.name==name)
            calls={n.func.attr if isinstance(n.func,ast.Attribute) else n.func.id if isinstance(n.func,ast.Name) else '' for n in ast.walk(function) if isinstance(n,ast.Call)}
            self.assertFalse(calls & {'generate','discover','staged_discovery','fit','seed'})
        function=next(n for n in module.body if isinstance(n,ast.FunctionDef) and n.name=='verify_raw_science')
        calls={n.func.attr for n in ast.walk(function) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)}
        self.assertTrue({'evaluate_realization','aggregate','boundary_controls','verify_chronology'}<=calls)

    def test_explicit_route_does_not_guess_between_multiple_keys(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); p=root/'result.json'
            routing.raw.write_new(p,{'disposition':'RAW_FAIL','final_disposition':'CORRECTED_PASS'})
            with patch.object(routing.raw,'ROOT',root):
                self.assertEqual(routing.route(p,'disposition','fixture')['disposition'],'RAW_FAIL')
                self.assertEqual(routing.route(p,'final_disposition','fixture')['disposition'],'CORRECTED_PASS')
                with self.assertRaises(ValueError): routing.route(p,'inferred','fixture')

    def test_adapter_cannot_excuse_another_operational_failure(self):
        result={'selection_commit_sha':'fixture','integrity_controls_pass':True}
        failure={'stage':'reveal','error':'PermissionError: oracle leaked','head_sha':'fixture',
            'disposition':'BENCHMARK_SUITE_1_NO_GO_CAPABILITY'}
        with patch.object(routing,'verify_raw_science',return_value=result), patch.object(routing.raw,'committed'), patch.object(routing.raw,'read',return_value=failure):
            with self.assertRaisesRegex(ValueError,'does not match'): routing.assess()

    def test_full_index_rejects_wrong_keys_hashes_and_authority(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); b0=root/'Benchmark0'; art=root/'Suite1'; recon=art/'routing_reconciliation.json'
            producer='f'*40
            values=[(b0/'result.json',{'disposition':'BENCHMARK_0_FAIL'}),
                (b0/'receipt_reconciliation.json',{'final_disposition':'BENCHMARK_0_PASS'}),
                (art/'result.json',{'disposition':'BENCHMARK_SUITE_1_PASS'}),
                (art/'evaluation_summary.json',{'disposition':'BENCHMARK_SUITE_1_PASS'}),
                (recon,{'disposition':'BENCHMARK_SUITE_1_PASS','correction_source_sha':producer}),
                (art/'failure.json',{'disposition':'BENCHMARK_SUITE_1_NO_GO_CAPABILITY'})]
            for p,v in values: routing.raw.write_new(p,v)
            with patch.object(routing.raw,'ROOT',root),patch.object(routing.raw,'ART',art),patch.object(routing,'B0',b0),patch.object(routing,'RECONCILIATION',recon),patch.object(routing,'FAILURE',art/'failure.json'),patch.object(routing.raw,'committed'):
                index=routing.index(producer); routing.validate_index(index)
                bad=copy.deepcopy(index); bad['Benchmark0']['authoritative']='raw_epoch'
                with self.assertRaises(ValueError): routing.validate_index(bad)
                bad=copy.deepcopy(index); bad['Benchmark0']['reconciliation']['disposition_key']='disposition'
                with self.assertRaises(ValueError): routing.validate_index(bad)
                bad=copy.deepcopy(index); bad['BenchmarkSuite1']['raw_epoch']['sha256']='0'*64
                with self.assertRaises(ValueError): routing.validate_index(bad)
                bad=copy.deepcopy(index); bad['BenchmarkSuite1']['reconciliation']['binding_kind']='artifact_state'
                with self.assertRaises(ValueError): routing.validate_index(bad)
