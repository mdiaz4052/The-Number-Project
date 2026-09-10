"""Only named semantic assertions score production mutations."""
import copy
from fractions import Fraction as F
import unittest
from unittest.mock import patch
from Discovery import nist_2026_torque_response_feasibility as n
from Discovery import nist_2026_torque_response_feasibility_mutations as m
from tests.test_nist_2026_torque_response_feasibility import protocol, value, evidence


class TorqueMutationBehaviorTests(unittest.TestCase):
    def test_peak_difference(self):
        p=protocol();row=p['permitted_input_projection']['campaigns'][0]
        d=value(n.preliminary_response(p)[0]['d_SI'])
        one_side=d*8*F('11.19168')*F('1.150156')*F(row['Gamma_table15'])/(F(row['Rs_mm'])/1000)
        self.assertEqual(one_side-(-one_side),1)

    def test_metric_prefix(self):
        row=n.preliminary_response(protocol())[0]
        self.assertEqual(value(row['d_U_per_pNm'])*10,value(row['d_SI']))

    def test_campaign_geometry(self):
        p=protocol();results=n.preliminary_response(p)
        r0=p['permitted_input_projection']['campaigns'][0];r1=p['permitted_input_projection']['campaigns'][1]
        expected=F(r1['Rs_mm'])/F(r0['Rs_mm'])*F(r0['Gamma_table15'])/F(r1['Gamma_table15'])
        self.assertEqual(value(results[2]['d_SI'])/value(results[0]['d_SI']),expected)

    def test_excluded_invariance(self):
        # Both are valid synthetic context payloads, no history/digest gate is called.
        p=protocol();p['excluded_context']={'G_values':[11],'torque_values':[8]};q=copy.deepcopy(p);q['excluded_context']={'G_values':[19],'torque_values':[21]}
        self.assertEqual(n.preliminary_response(p),n.preliminary_response(q))

    def test_unlicensed_aggregation(self):
        d=tuple(map(F,[1,0,2,0,4,0]))
        self.assertIsNone(n.final_copper_response('unidentified_posterior',d))

    def test_coupled_response(self):
        p=protocol()['synthetic_policy'];H=n.posterior_linear_map(p['design_rows'],p['weights'],p['prior_precision_alternatives'][0])
        self.assertEqual(n.coupled_response(H,tuple(map(F,p['servo_direction'])))[1],F(-111,590))

    def test_subspace_equivalence(self):
        a=(F(1),F(0),F(3),F(0));b=tuple(-5*v+7 for v in a)
        self.assertTrue(n.same_subspace(a,b))

    def test_stage_promotion(self):
        result=n.mapping_disposition(protocol(),evidence(stage='local',domain='local'))
        self.assertEqual(result['disposition'],'CONDITIONAL_MAPPING_ONLY')

    def test_faulty_calibration(self):
        self.assertEqual(n.affine_response(((F(2),F(3)),),(F(5),F(7))),(F(31),))

    def test_equivalent_control(self):
        self.assertEqual(n.coupled_response(((F(2),F(1)),(F(1),F(3))),(F(3),F(4))),(F(10),F(15)))


class TorqueMutationArtifactTests(unittest.TestCase):
    def test_saved_evidence_without_execution(self):
        with patch.object(m,'execute',side_effect=AssertionError('read-only guard must not run family')):
            artifact=m.check_artifact()
        self.assertEqual(artifact['production_killed'],8)

    def test_mapping_and_false_kill_rejection(self):
        source=(n.ROOT/n.MODULE).read_text();m.validate_definitions(source,protocol())
        test=m.CASES[0]['tests'];e={'runner_status':'completed','tests_run':1,'error_tests':[],'skipped_tests':[],
             'failing_tests':test,'successful':False,'validated_imports_before':m.IMPORTS,'validated_imports_after':m.IMPORTS}
        self.assertEqual(m.assess(e,test),'KILLED')
        for key,v in [('runner_status','invalid'),('tests_run',0),('error_tests',test),('skipped_tests',test),('failing_tests',['another.test']),('successful',True),('validated_imports_after',{})]:
            q=copy.deepcopy(e);q[key]=v
            with self.assertRaises(m.MutationEvidenceError):m.assess(q,test)

    def test_evidence_tamper_and_source_binding(self):
        artifact=n._json((n.ROOT/m.OUTPUT).read_bytes());source=(n.ROOT/n.MODULE).read_text()
        for key,v in [('applied_source_sha256','0'*64),('outcome','KILLED')]:
            q=copy.deepcopy(artifact['records']);q[0][key]=v
            with self.assertRaises(m.MutationEvidenceError):m.validate_records(q,source)
