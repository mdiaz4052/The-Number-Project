"""Independent numerical oracles, contract tests, and observed repository read closure."""
from contextlib import ExitStack
from copy import deepcopy
from fractions import Fraction as F
from itertools import product, permutations
import builtins
import io
import json
import os
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

from Discovery import bipm_nist_common_constant as d


def det(m):
    # Independent Leibniz/permutation oracle, deliberately not Gaussian elimination.
    n = len(m)
    if not n:
        return F(1)
    answer = F(0)
    for perm in permutations(range(n)):
        term = F((-1)**sum(perm[i] > perm[j] for i in range(n) for j in range(i+1,n)))
        for i,j in enumerate(perm):
            term *= m[i][j]
        answer += term
    return answer


def oracle(x, V):
    k = len(x)
    inverse = [[F((-1)**(i+j)) * det([[V[a][b] for b in range(k) if b != i]
                for a in range(k) if a != j]) / det(V) for j in range(k)] for i in range(k)]
    total = sum(sum(row) for row in inverse)
    w = tuple(sum(row)/total for row in inverse)
    mean = sum(w[i]*x[i] for i in range(k))
    residual = [v-mean for v in x]
    q = sum(residual[i]*inverse[i][j]*residual[j] for i in range(k) for j in range(k))
    return w, mean, q


def fixture():
    return (F(1),F(2),F(4),F(5)), ((F(2),F(1),F(0),F(0)),(F(1),F(3),F(0),F(0)),
                (F(0),F(0),F(4),F(1)),(F(0),F(0),F(1),F(2)))


def local_protocol():
    return d._json((d.ROOT / d.PREREGISTRATION_PATH).read_bytes())


def local_records(p):
    return {key:d._json((d.ROOT/v['path']).read_bytes()) for key,v in p['upstream_records'].items()}


class DiagnosticMathTests(unittest.TestCase):
    def test_q_two_forms_rank_and_independent_oracle(self):
        x,V=fixture();w,mean,q=oracle(x,V)
        actual=d.within_nist(x,V,w,(F(1,10),)*4,F(8))
        self.assertEqual((actual['mean'],actual['Q']),(mean,q))
        self.assertEqual(actual['A_rank'],3)
        self.assertEqual(actual['df'],3)
        self.assertEqual(d.mv(actual['A'],(F(1),)*4),(0,)*4)
        self.assertEqual(q,d.quadratic(actual['A'],x))
        self.assertGreaterEqual(q,0)

    def test_shift_units_permutation_and_covariance(self):
        x,V=fixture();w,_,q=oracle(x,V)
        self.assertEqual(d.within_nist(tuple(t+13 for t in x),V,w,(F(0),)*4,F(8))['Q'],q)
        factor=F(7,3)
        scaled=d.within_nist(tuple(t*factor for t in x),tuple(tuple(v*factor**2 for v in r) for r in V),w,
                             (F(1,10)*factor,)*4,F(8))
        original=d.within_nist(x,V,w,(F(1,10),)*4,F(8))
        self.assertEqual(scaled['Q'],q);self.assertEqual(scaled['display_bound'],original['display_bound'])
        perm=(2,0,3,1)
        self.assertEqual(d.within_nist(tuple(x[i] for i in perm),tuple(tuple(V[i][j] for j in perm) for i in perm),
            tuple(w[i] for i in perm),(F(1,10),)*4,F(8))['display_bound'],original['display_bound'])
        diag=tuple(tuple(V[i][j] if i==j else F(0) for j in range(4)) for i in range(4))
        dw,_,dq=oracle(x,diag)
        self.assertNotEqual(q,dq)
        self.assertEqual(d.within_nist(x,diag,dw,(F(0),)*4,F(8))['Q'],dq)

    def test_display_all_corners_interior_unresolved(self):
        x,V=fixture();w,_,q=oracle(x,V);h=(F(1,5),F(1,10),F(1,4),F(1,8))
        a=d.within_nist(x,V,w,h,q);low,high=a['display_bound']
        self.assertEqual(a['display_status'],'UNRESOLVED_BY_DISPLAY_BOUND')
        # All 16 corners, 81 grid interior/boundary points and an asymmetric interior point.
        offsets=list(product((-1,1),repeat=4))+list(product((-1,F(0),1),repeat=4))+[(F(1,3),F(-2,7),F(1,2),0)]
        for point in offsets:
            xx=tuple(x[i]+h[i]*point[i] for i in range(4))
            expected=oracle(xx,V)[2]
            self.assertLessEqual(low,expected);self.assertLessEqual(expected,high)
        self.assertEqual(d.within_nist(x,V,w,(F(0),)*4,q)['midpoint_status'],'NOT_FLAGGED_UNDER_DECLARED_MODEL')
        self.assertEqual(d.within_nist(x,V,w,(F(0),)*4,q)['display_status'],'NOT_FLAGGED_FOR_ALL_DISPLAY_VALUES')
        self.assertEqual(d.within_nist(x,V,w,(F(0),)*4,q/2)['display_status'],'FLAGGED_FOR_ALL_DISPLAY_VALUES')

    def test_invalid_covariance_and_weights(self):
        x,V=fixture();w,_,q=oracle(x,V)
        for invalid in [((1,2),(0,1)),((1,2),(2,1)),((0,0),(0,1)),((1,),()),((float('nan'),),)]:
            with self.assertRaises(d.DiagnosticError):d.check_covariance(invalid)
        for weights in [(F(1),)*4,tuple(reversed(w))]:
            with self.assertRaises(d.DiagnosticError):d.within_nist(x,V,weights,(F(0),)*4,F(8))

    def test_scaling_conventions_and_signed_weights(self):
        self.assertEqual(d.bipm_absolute_variance(F(3),F(25),10**12),F(225,10**12))
        self.assertEqual(d.linear_enclosure(((F(1),F(2)),(F(4),F(5))),(F(-1),F(2))),(F(6),F(9)))
        V=((F(1),F(2)),(F(2),F(5)));x=(F(3),F(4));w=(F(3,2),F(-1,2))
        cells=((F(2),F(4)),(F(3),F(5)))
        d.validate_summary(x,V,w,F(5,2),F(1,2),cells,(F(1,2),F(9,2)))

    def test_radical_comparison_signs_and_exact_equality(self):
        for a,b,r,expected in [(3,-1,9,0),(-3,1,9,0),(2,-1,9,-1),(-2,1,9,1),
                (-4,-1,2,-1),(4,1,2,1),(0,-2,5,-1),(1,-2,0,1),(1,-1,2,-1)]:
            self.assertEqual(d.radical_sign(F(a),F(b),F(r)),expected)
        tiny=F(1,10**100)
        self.assertEqual(d.radical_sign(F(1)+tiny,F(-1),F(1)),1)
        self.assertEqual(d.radical_sign(F(1)-tiny,F(-1),F(1)),-1)
        a=d.algebraic_statistic(F(9),F(1),F(4),F(-1),F(1))
        self.assertEqual(a['cutoff_comparison'],0)
        self.assertEqual(a['status'],'NOT_FLAGGED_UNDER_DECLARED_MODEL')

    def test_difference_zero_crossing_and_rho_dispositions(self):
        self.assertEqual(d.difference_interval((F(1),F(3)),(F(2),F(4))),(F(-3),F(1)))
        for bounds,answer in [((-3,-1),(1,3)),((-3,1),(0,3)),((1,3),(1,3)),((0,0),(0,0))]:
            self.assertEqual(d.absolute_extrema(tuple(map(F,bounds))),answer)
        for interval,status in [((7,8),'FLAGGED_FOR_ALL_RHO_AND_DISPLAY_VALUES'),
            ((0,1),'NOT_FLAGGED_FOR_ALL_RHO_AND_DISPLAY_VALUES'),((3,3),'RHO_OR_DISPLAY_DEPENDENT')]:
            self.assertEqual(d.rho_family(tuple(map(F,interval)),F(1),F(4),F(4))['status'],status)
        # Correlation or display ambiguity can each change disposition.
        contrast=d.aggregate_contrast(F(3),F(0),(F(1),F(5)),(F(0),F(0)),F(1),F(4),F(4))
        self.assertEqual(contrast['rho_zero_reference']['display_status'],'DISPLAY_DEPENDENT')
        self.assertEqual(contrast['midpoint_all_rho']['status'],'RHO_OR_DISPLAY_DEPENDENT')
        self.assertEqual(contrast['all_rho_all_display']['status'],'RHO_OR_DISPLAY_DEPENDENT')

    def test_analytic_rho_extrema_monotonicity_and_singular(self):
        # sqrt(1*4)=2: independent ordinary-rational oracle for the entire formula.
        for rho in (F(-1),F(-3,4),F(0),F(1,3),F(1)):
            actual=d.algebraic_statistic(F(9),F(1),F(4),rho,F(4))
            self.assertEqual(actual['cutoff_comparison'],d.sign(F(9)/(5-4*rho)-4))
        family=d.rho_family((F(2),F(3)),F(1),F(4),F(4))
        self.assertEqual(family['T_min']['rho'],-1);self.assertEqual(family['T_max']['rho'],1)
        for delta in (F(0),F(3)):
            c=d.aggregate_contrast(delta,F(0),(delta,delta),(F(0),F(0)),F(1),F(1),F(4))
            self.assertEqual(c['all_rho_all_display']['status'],'UNRESOLVED_SINGULAR_ENDPOINT')
            self.assertIn('midpoint',c['rho_zero_reference'])
        for vb,vn,rho in [(0,1,0),(-1,1,0),(1,1,2),(1,1,1)]:
            with self.assertRaises(d.DiagnosticError):d.algebraic_statistic(F(1),F(vb),F(vn),F(rho),F(4))


class DiagnosticContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol=local_protocol();cls.records=local_records(cls.protocol)

    def test_projection_validates_both_existing_models(self):
        p=d.validate_protocol(self.protocol)
        s=d.project_records(p,self.records)
        self.assertEqual(s.x,tuple(map(F,('6.673642','6.674021','6.672637','6.673636'))))
        self.assertEqual(s.v_b,s.b**2*F(6524036,10797)/10**12)
        self.assertEqual(s.V[0][1],F('0.42')*(s.x[0]*F('23.2')/10**6)*(s.x[1]*F('30.3')/10**6))
        self.assertEqual(d.cutoff(p,'within_nist'),(3,F('7.814728')))
        self.assertEqual(d.cutoff(p,'aggregate_contrast'),(1,F('3.841459')))

    def test_forbidden_fields_behavior_distinct_from_digests(self):
        expected=d.project_records(self.protocol,self.records)
        altered=deepcopy(self.records)
        altered['b_result']['comparison_only']={'published_combined_G_decimal_in_1e_minus_11_units':'900',
                    'printed_combined_relative_uncertainty_ppm':'999'}
        altered['b_result']['representation']['intersection_in_1e_minus_11_units']={'low':'junk','high':'junk'}
        altered['b_result']['representation']['published_combined_cell_in_1e_minus_11_units']='forbidden'
        altered['b_protocol']['source_projection']['comparison_only']='forbidden'
        altered['b_attestation']['transcription']['comparison_only']='forbidden'
        altered['n_attestation']['authority_resolution']='forbidden'
        altered['n_attestation']['published_bayesian_consensus_layer']='forbidden'
        for row in altered['n_attestation']['experimental_layer']['table_16']['measurements']:
            row['displayed_relative_standard_uncertainty_ppm']='12345'
        for rec in altered.values():
            rec['CODATA']='injected';rec['dark_uncertainty']='injected'
        self.assertEqual(d.project_records(self.protocol,altered),expected)

    def test_changed_authorized_inputs_and_unauthorized_states_reject(self):
        for role,path,value in [('n_result',['estimator','input_order'],['x']*4),
            ('n_result',['schema_version'],2),('n_result',['decision','common_constant_comparison'],'APPROVED'),
            ('n_feasibility',['decision','published_bayesian_consensus'],'GO'),
            ('b_result',['source','doi'],'wrong'),('n_attestation',['experimental_layer','table_18','diagonal_relative_standard_uncertainty_ppm'],['23','30','38','94'])]:
            changed=deepcopy(self.records);parent=changed[role]
            for k in path[:-1]:parent=parent[k]
            parent[path[-1]]=value
            with self.subTest(role=role,path=path),self.assertRaises(d.DiagnosticError):d.project_records(self.protocol,changed)

    def test_every_result_driving_protocol_policy_rejects_mutation(self):
        for key in self.protocol['model']:
            changed=deepcopy(self.protocol);changed['model'][key]='invalid'
            with self.subTest(key=key),self.assertRaises(d.DiagnosticError):d.validate_protocol(changed)
        for key in self.protocol['claim_limits']:
            changed=deepcopy(self.protocol);changed['claim_limits'][key]=False
            with self.subTest(key=key),self.assertRaises(d.DiagnosticError):d.validate_protocol(changed)
        for key,value in [('unit',{'symbol':'SI'}),('decisions',{}),('planned_surfaces',{}),('mutation_requirements',[])]:
            changed=deepcopy(self.protocol);changed[key]=value
            with self.subTest(key=key),self.assertRaises(d.DiagnosticError):d.validate_protocol(changed)

    def test_duplicate_nonfinite_malformed_and_rational_schema(self):
        for text in ['{"a":1,"a":2}','{"a":NaN}','{"a":Infinity}','{"a":']:
            with self.assertRaises(d.DiagnosticError):d._json(text)
        for value in [{'numerator':'1','denominator':'0'},{'numerator':'NaN','denominator':'1'},
                {'numerator':'2','denominator':'2'},{'numerator':True,'denominator':'1'}]:
            with self.assertRaises(d.DiagnosticError):d.rational(value)
        for value in ['NaN','Infinity',float('nan'),True]:
            with self.assertRaises(d.DiagnosticError):d.decimal_rational(value)

    def test_inherited_provisional_and_nominal_claims(self):
        for flagged in (True,False):
            c=d.claim_boundary(self.protocol,flagged)
            self.assertEqual(c['status'],d.PROVISIONAL);self.assertIs(c['conditional_only'],True)
            self.assertIs(c['within_model_challenged'],flagged)
        c=d.claim_boundary(self.protocol,True)
        self.assertIn('not independent confirmation',c['interpretation'])


class DiagnosticArtifactTests(unittest.TestCase):
    def test_committed_artifact_and_pins(self):
        p=d.verify_preregistration();a=d.check_artifact()
        self.assertEqual(a['integrity']['preregistration_sha256'],d.PREREGISTRATION_SHA256)
        self.assertEqual(a['audit_status_at_freeze']['status'],d.PROVISIONAL)
        # A deterministic clean rebuild is the new guard's own comparison.
        self.assertNotIn(d.OUTPUT.as_posix(),d.source_paths(p))

    def test_changed_pin_and_stale_artifact_fail_read_only(self):
        p=local_protocol();changed=deepcopy(p);changed['upstream_records']['b_result']['sha256']='0'*64
        with self.assertRaises(d.DiagnosticError):d.load_records(changed)
        original=Path.read_text
        def substitute(path,*args,**kwargs):
            if path.resolve()==(d.ROOT/d.OUTPUT).resolve():return '{"schema_version":99}\n'
            return original(path,*args,**kwargs)
        with patch.object(Path,'read_text',substitute),self.assertRaises(d.DiagnosticError):d.check_artifact()

    def test_actual_file_and_git_read_closure(self):
        root=d.ROOT.resolve();seen=set();git_paths=set();commands=[]
        def record(path):
            if not isinstance(path,(str,bytes,os.PathLike)):return
            resolved=Path(os.fsdecode(path)).resolve()
            if resolved.is_relative_to(root):
                rel=resolved.relative_to(root).as_posix()
                if rel!='.git' and not rel.startswith('.git/'):seen.add(rel)
        def tracked(method):
            def run(path,*args,**kwargs):record(path);return method(path,*args,**kwargs)
            return run
        real_run=subprocess.run
        def tracked_run(args,*more,**kwargs):
            commands.append(args)
            for arg in args:
                if isinstance(arg,str) and ':' in arg:
                    ref,path=arg.split(':',1)
                    if len(ref)==40 and all(c in '0123456789abcdef' for c in ref):git_paths.add(path)
            return real_run(args,*more,**kwargs)
        with ExitStack() as stack:
            for owner,name in [(Path,'read_bytes'),(Path,'read_text'),(builtins,'open'),(io,'open'),(os,'open')]:
                stack.enter_context(patch.object(owner,name,tracked(getattr(owner,name))))
            stack.enter_context(patch.object(subprocess,'run',tracked_run))
            d.build_artifact()
        expected=set(d.source_paths(local_protocol()))
        self.assertEqual(seen,expected)
        self.assertEqual(git_paths,expected)
        for command in commands:
            self.assertEqual(command[:3],['git','-C',str(root)])
            self.assertIn(command[3],{'show','log','merge-base','rev-parse','rev-list','diff','cat-file'})
            if command[3] == 'show' and '-s' not in command:
                self.assertIn(':', command[-1])
                self.assertIn(command[-1].split(':', 1)[1], expected)
            if command[3] == 'log':
                self.assertIn('--', command)
                allowed = expected | {d.OUTPUT.as_posix(), 'Experiments/GMeasurements/bipm_nist_common_constant_mutations_v1.json'}
                self.assertLessEqual(set(command[command.index('--') + 1:]), allowed)
            for arg in command:
                self.assertNotIn('hust',str(arg).lower())
        imports={name for name in d.__dict__ if name in ['solve_exact','determinant','linear_enclosure']}
        self.assertEqual(imports,{'solve_exact','determinant','linear_enclosure'})


if __name__=='__main__':unittest.main()
