"""Eight designated behavioral assertions on valid synthetic fixtures."""
import builtins
import copy
from fractions import Fraction as F
import io
import os
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch
from Discovery import nist_2026_paired_torque_feasibility as n
from Discovery import nist_2026_paired_torque_feasibility_mutations as m
from tests.test_nist_2026_paired_torque_feasibility import protocol, decoded, object_fixture, model_fixture, unknown, hand_project, covariance_fixture


class PairedMutationBehaviorTests(unittest.TestCase):
    def test_method_sign(self):
        B=n.operators(protocol())[0];x=[[F(i+1)] for i in range(8)]
        self.assertEqual(n.mm(B,x),((-1,),(-1,),(-1,),(-1,)))

    def test_covariance_units(self):
        self.assertEqual(n.covariance_units(((4,1),(1,9)),'1/1000'),((F(4,10**6),F(1,10**6)),(F(1,10**6),F(9,10**6))))

    def test_covariance_cross_terms(self):
        expected=hand_project(covariance_fixture())[1]
        actual=n.project(n.operators(protocol())[4],covariance_fixture())
        self.assertEqual(actual,expected)

    def test_shared_loading(self):
        self.assertFalse(n.annihilates(n.operators(protocol())[4],[[1],[0],[2],[0],[3],[0],[4],[0]]))

    def test_minimum_C(self):
        e=model_fixture(matrix=object_fixture('direct_C',value=((4,2,2),(2,4,2),(2,2,4))),full_matrix_unknown=True,
                        unknown_components=[unknown(loading=n.operators(protocol())[3])])
        self.assertEqual(n.classify(protocol(),e)['disposition'],'GO_CONTRAST_UNCERTAINTY')

    def test_type_a_scope(self):
        e=model_fixture(matrix=object_fixture(scope='type_a'))
        self.assertEqual(n.classify(protocol(),e)['disposition'],'NO_GO_CONTRAST_UNCERTAINTY')

    def test_unknown_correction(self):
        self.assertEqual(n.classify(protocol(),model_fixture(mean_correction_status='UNKNOWN'))['disposition'],'NO_GO_CONTRAST_UNCERTAINTY')

    def test_unknown_dependence(self):
        e=model_fixture(unknown_components=[unknown('dependence',n.eye(8),'dependence',False)])
        self.assertEqual(n.classify(protocol(),e)['disposition'],'NO_GO_CONTRAST_UNCERTAINTY')

    def test_faulty_calibration(self):
        self.assertEqual(n.scale_matrix(((1,2),(3,4)),3),((3,6),(9,12)))

    def test_equivalent_control(self):
        self.assertEqual(n.project(((1,-1),),((2,1),(1,3))),((3,),))


class PairedMutationArtifactTests(unittest.TestCase):
    def test_saved_evidence_without_execution(self):
        with patch.object(m,'execute',side_effect=AssertionError('read-only cannot run family')):
            artifact=m.check_artifact()
        self.assertEqual(artifact['production_killed'],8)

    def test_frozen_mapping_and_invalid_kill_rejection(self):
        source=(n.ROOT/n.MODULE).read_text();m.validate_definitions(source,protocol())
        test=m.CASES[0]['tests'];e={'runner_status':'completed','tests_run':1,'error_tests':[],'skipped_tests':[],
            'failing_tests':test,'successful':False,'validated_imports_before':m.IMPORTS,'validated_imports_after':m.IMPORTS}
        self.assertEqual(m.assess(e,test),'KILLED')
        for key,v in [('runner_status','invalid'),('tests_run',0),('error_tests',test),('skipped_tests',test),('failing_tests',['unrelated.test']),('successful',True),('validated_imports_after',{})]:
            q=copy.deepcopy(e);q[key]=v
            with self.assertRaises(m.MutationEvidenceError):m.assess(q,test)

    def test_evidence_tamper_and_source_binding(self):
        artifact=n._json((n.ROOT/m.OUTPUT).read_bytes());source=(n.ROOT/n.MODULE).read_text()
        for key,v in [('applied_source_sha256','0'*64),('outcome','KILLED')]:
            q=copy.deepcopy(artifact['records']);q[0][key]=v
            with self.assertRaises(m.MutationEvidenceError):m.validate_records(q,source)

    def test_observed_verifier_read_closure(self):
        files=set();blobs=set();calls=[];bopen=builtins.open;iopen=io.open;oopen=os.open;run=subprocess.run
        def remember(file):
            if isinstance(file,(str,os.PathLike)):
                path=Path(file).resolve()
                if path.is_relative_to(n.ROOT):files.add(path.relative_to(n.ROOT).as_posix())
        def b(file,*a,**kw):remember(file);return bopen(file,*a,**kw)
        def i(file,*a,**kw):remember(file);return iopen(file,*a,**kw)
        def o(file,*a,**kw):remember(file);return oopen(file,*a,**kw)
        def r(cmd,*a,**kw):
            calls.append(cmd)
            for arg in cmd:
                if ':' in str(arg) and str(arg).split(':',1)[1].startswith(('Discovery/','Experiments/','Notes/','tests/')):blobs.add(str(arg).split(':',1)[1])
            return run(cmd,*a,**kw)
        with patch('builtins.open',b),patch('io.open',i),patch('os.open',o),patch('subprocess.run',r):m.check_artifact()
        self.assertEqual(files,set(m.SOURCE_PATHS)|{m.OUTPUT.as_posix()})
        self.assertEqual(blobs,set(m.SOURCE_PATHS)|{m.OUTPUT.as_posix()})
        self.assertTrue(all(cmd[0]=='git' for cmd in calls))
        artifact=n._json((n.ROOT/m.OUTPUT).read_bytes())
        for record in artifact['records']:
            for phase in ('validated_imports_before','validated_imports_after'):
                imports=record['evidence'][phase]
                self.assertEqual(imports['Discovery.mutation_test_runner'],'Discovery/mutation_test_runner.py')
                self.assertLessEqual(set(imports.values()),set(m.COPY_PATHS)|{'tests/__init__.py'})
