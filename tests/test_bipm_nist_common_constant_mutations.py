"""Hand-checkable behavioral mutation targets; artifact tests are separate."""
from copy import deepcopy
from fractions import Fraction as F
from pathlib import Path
import unittest
from unittest.mock import patch

from Discovery import bipm_nist_common_constant as d
from Discovery import bipm_nist_common_constant_mutations as m


class DiagnosticMutationBehaviorTests(unittest.TestCase):
    def test_difference_calibration(self):
        self.assertEqual(d.difference_interval((F(2),F(4)),(F(1),F(3))),(F(-1),F(3)))

    def test_equivalent_calibration(self):
        self.assertEqual(d.bipm_absolute_variance(F(2),F(9),10**12),F(36,10**12))

    def test_covariance(self):
        self.assertEqual(d.inverse_matrix(((F(2),F(1)),(F(1),F(2)))),
                         ((F(2,3),F(-1,3)),(F(-1,3),F(2,3))))

    def test_bipm_scaling(self):
        self.assertEqual(d.bipm_absolute_variance(F(3),F(25),10**12),F(225,10**12))

    def test_rho_sign(self):
        low=d.algebraic_statistic(F(9),F(1),F(4),F(-1),F(4))
        high=d.algebraic_statistic(F(9),F(1),F(4),F(1),F(4))
        self.assertEqual(low['cutoff_comparison'],-1)
        self.assertEqual(high['cutoff_comparison'],1)
        self.assertEqual(low['denominator']['sqrt_coefficient'],F(2))

    def test_display_bound(self):
        identity=tuple(tuple(F(i==j) for j in range(4)) for i in range(4))
        a=d.within_nist((F(0),F(0),F(0),F(4)),identity,(F(1,4),)*4,(F(1,10),)*4,F(12))
        # A=I-J/4; Ax=(-1,-1,-1,3); Q=12, L=6/5, E=3/50.
        self.assertEqual(a['L'],F(6,5))
        self.assertEqual(a['E'],F(3,50))
        self.assertEqual(a['display_bound'],(F(54,5),F(663,50)))

    def test_cutoff_mapping(self):
        p={'calibration':{'cutoffs':{'within_nist':{'df':3,'value':'7.814728'},
            'aggregate_contrast':{'df':1,'value':'3.841459'}}}}
        self.assertEqual(d.cutoff(p,'within_nist'),(3,F('7.814728')))
        self.assertEqual(d.cutoff(p,'aggregate_contrast'),(1,F('3.841459')))
        self.assertEqual(d.midpoint_status(F('7.814728'),F('7.814728')),'NOT_FLAGGED_UNDER_DECLARED_MODEL')

    def test_mean_fitting(self):
        self.assertEqual(d.fitted_residual((F(1),F(2),F(3),F(4)),F(5,2)),
                         (F(-3,2),F(-1,2),F(1,2),F(3,2)))

    def test_terminal_invariance(self):
        source={'representation':{'midpoint_aggregate_in_1e_minus_11_units':d.record(F(3))},
            'comparison_only':{'published_combined_G_decimal_in_1e_minus_11_units':'7'}}
        path=['representation','midpoint_aggregate_in_1e_minus_11_units']
        a=d.select_authorized(source,path)
        source['comparison_only']['published_combined_G_decimal_in_1e_minus_11_units']='900'
        b=d.select_authorized(source,path)
        self.assertEqual(a,d.record(F(3)));self.assertEqual(b,a)

    def test_claim_boundary(self):
        p={'claim_limits':dict(d.SUPPORTED_LIMITS),'calibration':{'label':'nominal 5%'}}
        a=d.claim_boundary(p,True)
        self.assertEqual(a['status'],'PROVISIONAL — INDEPENDENT AUDIT PENDING')
        self.assertIs(a['conditional_only'],True)
        self.assertIn('not independent confirmation',a['interpretation'])


class DiagnosticMutationHarnessTests(unittest.TestCase):
    def test_definitions_match_frozen_mapping(self):
        p=d._json((d.ROOT/d.PREREGISTRATION_PATH).read_bytes())
        source=(d.ROOT/m.MODULE).read_text()
        m.validate_definitions(source,p)
        changed=deepcopy(p);changed['mutation_requirements'][0]['test']='wrong'
        with self.assertRaises(m.MutationEvidenceError):m.validate_definitions(source,changed)

    def test_only_designated_behavior_failure_scores(self):
        tests=[m.PREFIX+'test_covariance']
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
        for replacement in ['return F(', "raise ImportError('missing')"]:
            c=m.case('invalid', 'return b * b * r / denominator',replacement,'test_bipm_scaling')
            with self.subTest(replacement=replacement),self.assertRaises(m.MutationEvidenceError):m.run_case(d.ROOT,c)


class DiagnosticMutationArtifactTests(unittest.TestCase):
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
