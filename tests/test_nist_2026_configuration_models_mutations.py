"""Designated independent behavioral assertions; artifact checks never earn kill credit."""
from copy import deepcopy
from fractions import Fraction as F
from pathlib import Path
import unittest
from unittest.mock import patch
from Discovery import nist_2026_configuration_models as d
from Discovery import nist_2026_configuration_models_mutations as m
from tests.test_nist_2026_configuration_models import local_protocol, sample_inputs, mm, mt, inv


class ConfigurationMutationBehaviorTests(unittest.TestCase):
    def test_faulty_calibration(self):
        a=d.certify_display(((F(1),),),(F(3),),(F(1),))
        self.assertEqual(a,{'B':F(6),'E':F(1),'bounds':(F(3),F(16))})

    def test_equivalent_calibration(self):
        self.assertEqual(d.quadratic(((F(2),F(1)),(F(1),F(3))),(F(4),F(-1))),F(27))

    def test_contrast_order(self):
        p=local_protocol();names,L=d.contrast_geometry(p)
        self.assertEqual(d.selected_rows(names,L,p['models'][1]),(L[0],L[2]))
        self.assertEqual(d.selected_rows(names,L,p['models'][2]),(L[1],L[2]))
        self.assertEqual(d.selected_rows(names,L,p['models'][3]),(L[2],))

    def test_full_covariance(self):
        R=((F(1),F(-1),F(0),F(0)),(F(0),F(0),F(1),F(-1)))
        V=sample_inputs().V
        self.assertEqual(d.constrained_covariance(R,V),((F(5),F(-2)),(F(-2),F(9))))

    def test_marginal_covariance(self):
        a=sample_inputs();L=d.contrast_geometry(local_protocol())[1];R=(L[2],)
        C=mm(mm(R,a.V),mt(R));y=sum(z*w for z,w in zip(a.x,R[0]))
        result=d.contrast_state(a.x,a.V,R)
        self.assertEqual(result['C'],C)
        self.assertEqual(result['Q'],y*y/C[0][0])

    def test_rank_df_policy(self):
        p=local_protocol();names,L=d.contrast_geometry(p)
        self.assertEqual([d.model_df(spec,d.selected_rows(names,L,spec)) for spec in p['models']],[3,2,2,1])

    def test_forbidden_input_invariance(self):
        # Exercise the real selector on a valid NIST source container without whole-file hash rejection.
        p=local_protocol();s=deepcopy(p['upstream_records']['source']['fields'])
        source={'experimental_layer':{'table_18':{'diagonal_relative_standard_uncertainty_ppm':['23.2','30.3','37.5','93.9']}},
                'consensus_layer':{'published_table_19':{'dark_uncertainty':'1','terminal':'7'}}}
        path=s['s']['path'];expected=['23.2','30.3','37.5','93.9']
        first=d.select_authorized(source,path)
        source['consensus_layer']['published_table_19']={'dark_uncertainty':'999','terminal':'-9'}
        second=d.select_authorized(source,path)
        self.assertEqual(first,expected);self.assertEqual(second,expected)
        # An actual downstream covariance scalar remains unchanged.
        self.assertEqual(F(first[0])**2,F(second[0])**2)

    def test_saturated_non_test(self):
        out=d.saturated_control(local_protocol())
        self.assertEqual(out['status'],'NOT_TESTABLE_ZERO_RESIDUAL_DF')
        self.assertIs(out['scientific_acceptance'],False)

    def test_display_classification(self):
        p=local_protocol()['decision_policy']
        self.assertEqual(d.classify_display((F(3),F(16)),F(7,2),p),'UNRESOLVED_FROM_CERTIFIED_BOUNDS')
        self.assertEqual(d.classify_display((F(6),F(8)),F(5),p),'FLAGGED_FOR_ALL_DISPLAY_VALUES')
        self.assertEqual(d.classify_display((F(2),F(5)),F(5),p),'NOT_FLAGGED_FOR_ALL_DISPLAY_VALUES')

    def test_frozen_cutoff_policy(self):
        p=local_protocol()
        self.assertEqual([d.cutoff(p,df) for df in (3,2,1)],[F('7.814728'),F('5.991465'),F('3.841459')])
        self.assertEqual(d.midpoint_status(F('5.991465'),d.cutoff(p,2),p['decision_policy']),p['decision_policy']['midpoint_not_flagged'])


class ConfigurationMutationHarnessTests(unittest.TestCase):
    def test_definitions_match_frozen_mapping(self):
        p=local_protocol();source=(d.ROOT/m.MODULE).read_text();m.validate_definitions(source,p)
        changed=deepcopy(p);changed['mutation_requirements'][0]['test']='wrong'
        with self.assertRaises(m.MutationEvidenceError):m.validate_definitions(source,changed)

    def test_only_designated_behavior_failure_scores(self):
        tests=[m.PREFIX+'test_full_covariance']
        good={'runner_status':'completed','tests_run':1,'failing_tests':[], 'error_tests':[],
              'skipped_tests':[],'successful':True,'validated_imports_before':dict(m.IMPORTS),
              'validated_imports_after':dict(m.IMPORTS)}
        self.assertEqual(m.assess_execution(good,tests),'SURVIVED')
        faulty=deepcopy(good);faulty.update(failing_tests=tests,successful=False)
        self.assertEqual(m.assess_execution(faulty,tests),'KILLED')
        for key,value in [('tests_run',True),('tests_run',0),('error_tests',tests),('skipped_tests',tests),
                ('runner_status','failed'),('failing_tests',['unrelated']),('successful',True),
                ('test_output','SyntaxError'),('test_output','ImportError'),('test_output','history_unavailable'),
                ('validated_imports_before',{}),('validated_imports_after',{})]:
            changed=deepcopy(faulty);changed[key]=value
            with self.subTest(key=key,value=value),self.assertRaises(m.MutationEvidenceError):m.assess_execution(changed,tests)

    def test_actual_import_and_syntax_failures_receive_no_credit(self):
        for replacement in ['return F(',"raise ImportError('missing')"]:
            c=m.case('invalid','return dot(x, mv(V, x))',replacement,'test_equivalent_calibration')
            with self.subTest(replacement=replacement),self.assertRaises(m.MutationEvidenceError):m.run_case(d.ROOT,c)


class ConfigurationMutationArtifactTests(unittest.TestCase):
    def test_committed_mutations_current_and_calibrated(self):
        a=m.check_artifact()
        self.assertEqual(a['production_count'],8);self.assertEqual(a['production_killed'],8)
        self.assertIs(a['calibration_valid'],True);self.assertEqual(a['family_status'],'valid')
        self.assertEqual(a['records'][0]['outcome'],'SURVIVED')

    def test_tampered_evidence_rejected_read_only(self):
        original=Path.read_text
        def changed(path,*args,**kwargs):
            text=original(path,*args,**kwargs)
            if path.resolve()==(d.ROOT/m.OUTPUT).resolve():
                a=d._json(text);a['production_killed']=0;return d.serialize_artifact(a)
            return text
        with patch.object(Path,'read_text',changed),self.assertRaises(m.MutationEvidenceError):m.check_artifact()


if __name__=='__main__':unittest.main()
