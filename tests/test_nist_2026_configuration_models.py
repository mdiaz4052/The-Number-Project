"""Independent exact oracles, mathematical controls, and production read closure."""
import ast
import builtins
from contextlib import ExitStack
from copy import deepcopy
from fractions import Fraction as F
from itertools import permutations, product
import io
import os
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

from Discovery import nist_2026_configuration_models as d


def local_protocol():
    return d._json((d.ROOT / d.PREREGISTRATION_PATH).read_bytes())


def records(p):
    return {role: d._json((d.ROOT / spec['path']).read_bytes()) for role, spec in p['upstream_records'].items()}


# Oracle uses Leibniz determinants and adjugates, independent of Gaussian elimination.
def det(M):
    n = len(M)
    result = F(0)
    for p in permutations(range(n)):
        value = F((-1)**sum(p[i] > p[j] for i in range(n) for j in range(i+1, n)))
        for i in range(n):
            value *= M[i][p[i]]
        result += value
    return result


def inv(M):
    z = det(M)
    if z == 0:
        raise ValueError('singular oracle')
    return tuple(tuple(F((-1)**(i+j)) * det(tuple(tuple(M[a][b] for b in range(len(M)) if b != i)
                   for a in range(len(M)) if a != j)) / z for j in range(len(M))) for i in range(len(M)))


def mt(M):
    return tuple(zip(*M))


def mm(A, B):
    return tuple(tuple(sum((a*b for a,b in zip(row,col)), F(0)) for col in mt(B)) for row in A)


def gls_oracle(x, V, X):
    W = inv(V)
    y = tuple((z,) for z in x)
    beta = mm(mm(inv(mm(mm(mt(X), W), X)), mm(mt(X), W)), y)
    residual = tuple((a[0]-b[0],) for a,b in zip(y, mm(X, beta)))
    return mm(mm(mt(residual), W), residual)[0][0]


def sample_inputs(x=(F(1), F(4), F(2), F(8)), V=None, h=F(1,20)):
    p = local_protocol()
    if V is None:
        V = ((F(3),F(1),F(0),F(1)),(F(1),F(4),F(1),F(0)),
             (F(0),F(1),F(5),F(2)),(F(1),F(0),F(2),F(8)))
    return d.Inputs(tuple(x), V, tuple((z-h,z+h) for z in x), tuple(p['input_order']))


class ConfigurationBehaviorTests(unittest.TestCase):
    def test_rank_nullspaces_and_contrast_sign_scale(self):
        p=local_protocol();names,L=d.contrast_geometry(p)
        self.assertEqual(names, ('material','method','interaction'))
        self.assertEqual(L, ((F(1,2),F(1,2),F(-1,2),F(-1,2)),
                            (F(-1,2),F(1,2),F(-1,2),F(1,2)),(F(-1),F(1),F(1),F(-1))))
        self.assertEqual(det(mm(L, mt(L))), F(4))
        self.assertEqual(d.mv(L, (F(1),)*4), (F(0),)*3)
        self.assertEqual(d.mv(L, (F(0),F(1),F(0),F(0))), (F(1,2),F(1,2),F(1)))
        for m in p['models']:
            R=d.selected_rows(names,L,m)
            X=mt(tuple(tuple(map(F,p['allowed_mean_columns'][n])) for n in m['allowed_columns']))
            self.assertEqual(mm(R,X),tuple((F(0),)*len(m['allowed_columns']) for _ in R))
            self.assertGreater(det(mm(mt(X),X)),0)
            self.assertEqual(len(R)+len(m['allowed_columns']),4)

    def test_positive_definiteness_and_invalid_rank_are_errors(self):
        for V in [((F(1),F(2)),(F(0),F(1))), ((F(1),F(1)),(F(1),F(1))),
                  ((F(-1),F(0)),(F(0),F(-1))), ((1.0,0),(0,1.0))]:
            with self.subTest(V=V),self.assertRaises(d.DiagnosticError):d.check_covariance(V)
        with self.assertRaises(d.DiagnosticError):d.contrast_state((F(1),F(2)),d.identity(2),((F(1),F(-1)),)*2)
        with self.assertRaises(d.DiagnosticError):d.contrast_state((F(1),F(2)),d.identity(2),((F(1),F(1)),))
        with self.assertRaises(d.DiagnosticError):d.contrast_state((1.0,2.0),d.identity(2),((F(1),F(-1)),))

    def test_independent_GLS_cofactor_oracle_synthetic_and_real(self):
        p=local_protocol()
        for a in [sample_inputs(),d.project_records(p,records(p))]:
            result=d.evaluate(p,a)
            for spec,m in zip(p['models'],result['models']):
                X=mt(tuple(tuple(map(F,p['allowed_mean_columns'][n])) for n in spec['allowed_columns']))
                self.assertEqual(m['Q'],gls_oracle(a.x,a.V,X))
                R=d.selected_rows(*d.contrast_geometry(p),spec)
                C=mm(mm(R,a.V),mt(R));y=mm(R,tuple((z,) for z in a.x))
                self.assertEqual(m['Q'],mm(mm(mt(y),inv(C)),y)[0][0])
                self.assertEqual(m['C'],C)
                A=m['A']
                self.assertEqual(mm(mm(A,a.V),A),A)  # Whitening projection identity without numerical roots.
                self.assertEqual(sum(mm(A,a.V)[i][i] for i in range(4)),m['residual_df'])

    def test_full_propagated_covariance_not_marginal_square_sum(self):
        p=local_protocol();a=sample_inputs();out=d.evaluate(p,a);c=out['contrasts']
        self.assertEqual(c['S'],mm(mm(c['L'],a.V),mt(c['L'])))
        self.assertTrue(any(c['S'][i][j] != 0 for i in range(3) for j in range(3) if i!=j))
        naive=sum(c['d'][i]**2/c['S'][i][i] for i in range(3))
        self.assertNotEqual(out['models'][0]['Q'],naive)
        diagonal=tuple(tuple(z if i==j else F(0) for j,z in enumerate(row)) for i,row in enumerate(a.V))
        self.assertNotEqual(out['models'][0]['Q'],d.evaluate(p,d.Inputs(a.x,diagonal,a.cells,a.order))['models'][0]['Q'])

    def test_profiled_nuisance_is_not_conditioned(self):
        p=local_protocol();a=sample_inputs();out=d.evaluate(p,a);S=out['contrasts']['S']
        conditional=S[2][2]-mm(mm((S[2][:2],),inv(tuple(row[:2] for row in S[:2]))),((S[0][2],),(S[1][2],)))[0][0]
        self.assertNotEqual(conditional,S[2][2])
        self.assertEqual(out['models'][3]['Q'],out['contrasts']['d'][2]**2/S[2][2])
        self.assertNotEqual(out['models'][3]['Q'],out['contrasts']['d'][2]**2/conditional)

    def test_unit_scaling(self):
        p=local_protocol();a=sample_inputs();old=d.evaluate(p,a)
        scale=F(1,10**11)
        b=d.Inputs(tuple(z*scale for z in a.x),tuple(tuple(z*scale**2 for z in row) for row in a.V),
                   tuple((lo*scale,hi*scale) for lo,hi in a.cells),a.order)
        new=d.evaluate(p,b)
        self.assertEqual([m['Q'] for m in old['models']],[m['Q'] for m in new['models']])
        self.assertEqual([m['display'] for m in old['models']],[m['display'] for m in new['models']])
        self.assertEqual(new['contrasts']['d'],tuple(z*scale for z in old['contrasts']['d']))
        self.assertEqual(new['contrasts']['S'],tuple(tuple(z*scale**2 for z in row) for row in old['contrasts']['S']))

    def test_all_label_preserving_permutations(self):
        p=local_protocol();a=sample_inputs();names,L=d.contrast_geometry(p)
        for perm in permutations(range(4)):
            x=tuple(a.x[i] for i in perm);V=tuple(tuple(a.V[i][j] for j in perm) for i in perm)
            for spec in p['models']:
                R=d.selected_rows(names,L,spec);Rp=tuple(tuple(row[i] for i in perm) for row in R)
                old=d.contrast_state(a.x,a.V,R);new=d.contrast_state(x,V,Rp)
                self.assertEqual(old['Q'],new['Q']);self.assertEqual(old['y'],new['y']);self.assertEqual(old['C'],new['C'])

    def test_nested_models_nonincreasing_Q(self):
        p=local_protocol()
        for x in product((F(-2),F(3)),repeat=4):
            q={m['id']:m['Q'] for m in d.evaluate(p,sample_inputs(x=x))['models']}
            self.assertGreaterEqual(q['M0'],q['M_method']);self.assertGreaterEqual(q['M0'],q['M_material'])
            self.assertGreaterEqual(q['M_method'],q['M_additive']);self.assertGreaterEqual(q['M_material'],q['M_additive'])

    def test_synthetic_common_method_material_interaction(self):
        p=local_protocol()
        cases=[((F(8),)*4,[True,True,True,True]),
               ((F(0),F(4),F(0),F(4)),[False,True,False,True]),
               ((F(4),F(4),F(0),F(0)),[False,False,True,True]),
               ((F(-1),F(1),F(1),F(-1)),[False,False,False,False])]
        for x,expected in cases:
            r=d.evaluate(p,sample_inputs(x=x,V=d.identity(4)))
            self.assertEqual([m['Q']==0 for m in r['models']],expected)

    def test_common_shift_and_common_covariance_algebra(self):
        p=local_protocol();a=sample_inputs();old=d.evaluate(p,a)
        for shift,t in [(F(900),F(0)),(F(-7,3),F(12)),(F(0),F(100000))]:
            b=d.Inputs(tuple(z+shift for z in a.x),tuple(tuple(z+t for z in row) for row in a.V),
                       tuple((lo+shift,hi+shift) for lo,hi in a.cells),a.order)
            new=d.evaluate(p,b)
            self.assertEqual(new,old)
        # A shared effect with unequal loadings is expressly outside the invariance.
        v=(F(1),F(0),F(0),F(0));V=tuple(tuple(a.V[i][j]+v[i]*v[j] for j in range(4)) for i in range(4))
        self.assertNotEqual(d.evaluate(p,d.Inputs(a.x,V,a.cells,a.order))['contrasts']['S'],old['contrasts']['S'])

    def test_global_display_bound_has_exact_PSD_proof(self):
        p=local_protocol();a=sample_inputs();h=tuple((hi-lo)/2 for lo,hi in a.cells)
        for m in d.evaluate(p,a)['models']:
            A=m['A'];Q=m['Q'];bd=m['display']
            self.assertEqual(bd['B'],2*sum(h[i]*abs(sum(A[i][j]*a.x[j] for j in range(4))) for i in range(4)))
            self.assertEqual(bd['E'],sum(h[i]*h[j]*abs(A[i][j]) for i in range(4) for j in range(4)))
            self.assertEqual(bd['bounds'],(max(F(0),Q-bd['B']),Q+bd['B']+bd['E']))
            # Every principal minor is >=0: A is PSD, proving delta^T A delta >=0 globally.
            for mask in range(1,16):
                indices=[i for i in range(4) if mask&(1<<i)]
                self.assertGreaterEqual(det(tuple(tuple(A[i][j] for j in indices) for i in indices)),0)
            # These interior/corner controls supplement, rather than establish, the global proof.
            for delta in product((F(-1),F(0),F(1,3),F(1)),repeat=4):
                moved=tuple(a.x[i]+h[i]*delta[i] for i in range(4))
                q=d.quadratic(A,moved)
                self.assertLessEqual(bd['bounds'][0],q);self.assertLessEqual(q,bd['bounds'][1])

    def test_signed_linear_enclosures(self):
        cells=((F(-1),F(2)),(F(0),F(4)),(F(-3),F(1)),(F(2),F(3)))
        for row in d.contrast_geometry(local_protocol())[1]:
            values=[sum(z*w for z,w in zip(point,row)) for point in product(*cells)]
            self.assertEqual(d.linear_enclosure(cells,row),(min(values),max(values)))

    def test_display_classes_equality_and_unresolved_are_conservative(self):
        policy=local_protocol()['decision_policy'];c=F(5)
        self.assertEqual(d.classify_display((F(6),F(8)),c,policy),policy['display_flagged'])
        self.assertEqual(d.classify_display((F(1),F(5)),c,policy),policy['display_not_flagged'])
        self.assertEqual(d.classify_display((F(5),F(8)),c,policy),policy['display_unresolved'])
        self.assertEqual(d.midpoint_status(c,c,policy),policy['midpoint_not_flagged'])
        # PSD Q=x^2 with x=3,h=1: actual minimum 4, conservative lower 3.
        b=d.certify_display(((F(1),),),(F(3),),(F(1),))
        self.assertEqual(b['bounds'],(F(3),F(16)))
        self.assertEqual(d.classify_display(b['bounds'],F(7,2),policy),policy['display_unresolved'])
        self.assertGreater(F(2)**2,F(7,2))  # No attainable non-flagged point despite straddling outer bounds.
        for bounds in [(F(3),F(2)),(F(-1),F(2))]:
            with self.assertRaises(d.DiagnosticError):d.classify_display(bounds,c,policy)

    def test_saturated_fit_is_not_a_scientific_acceptance(self):
        p=local_protocol();out=d.saturated_control(p)
        self.assertEqual(out['Q'],0);self.assertEqual(out['residual_df'],0)
        self.assertEqual(out['status'],'NOT_TESTABLE_ZERO_RESIDUAL_DF');self.assertIs(out['scientific_acceptance'],False)
        self.assertEqual(d.gls_profile((F(1),F(7),F(-3),F(9)),sample_inputs().V,d.identity(4)),0)

    def test_frozen_verdict_fields_are_consumed_or_rejected(self):
        p=local_protocol();d.validate_protocol(p)
        changes=[('models',0,'residual_df',2),('models',1,'constraints',['method','interaction']),
                 ('contrasts',0,'row',['1','1','-1','-1'])]
        for key,index,field,value in changes:
            bad=deepcopy(p);bad[key][index][field]=value
            with self.assertRaises(d.DiagnosticError):d.validate_protocol(bad)
        for key in ['decision_policy','mathematical_policy','calibration','claim_limits','source_review',
                    'audit_status_at_freeze','serialization','planned_surfaces','verification_only_baseline']:
            bad=deepcopy(p);bad[key]={}
            with self.subTest(key=key),self.assertRaises(d.DiagnosticError):d.validate_protocol(bad)
        bad=deepcopy(p);bad['calibration']['cutoffs_by_df']['2']='999'
        self.assertEqual(d.cutoff(bad,2),999)  # Numerical kernel consumes passed cutoff, wrapper rejects unapproved policy.
        with self.assertRaises(d.DiagnosticError):d.validate_protocol(bad)
        bad=deepcopy(p);bad['contrasts'][0]['row']=['1','1','-1','-1']
        self.assertEqual(d.contrast_geometry(bad)[1][0],(F(1),F(1),F(-1),F(-1)))

    def test_input_fields_and_authorization_fail_closed(self):
        p=local_protocol();source=records(p)
        for role,spec in p['upstream_records'].items():
            for key,entry in spec['fields'].items():
                altered=deepcopy(source);target=altered[role]
                for component in entry['path'][:-1]:target=target[component]
                target[entry['path'][-1]]=None
                with self.subTest(role=role,key=key),self.assertRaises(d.DiagnosticError):d.project_records(p,altered)
        bad=deepcopy(p);bad['upstream_records']['source']['fields']['s']['path']=['consensus_layer']
        with self.assertRaises(d.DiagnosticError):d.validate_protocol(bad)

    def test_excluded_terminal_dark_fields_are_numerically_inert(self):
        p=local_protocol();source=records(p);reference=d.evaluate(p,d.project_records(p,source))
        for val in ['1','900','-300']:
            altered=deepcopy(source)
            # Source container really contains consensus_layer; preserve container types and mutate leaves.
            def replace_leaves(value):
                if isinstance(value,dict):return {k:replace_leaves(v) for k,v in value.items()}
                if isinstance(value,list):return [replace_leaves(v) for v in value]
                return val if isinstance(value,str) else value
            altered['source']['consensus_layer']=replace_leaves(altered['source']['consensus_layer'])
            altered['certificate']['estimator']['point_estimate_decimal']=val
            altered['certificate']['estimator']['weights']=[d.record(F(val))]*4
            altered['certificate']['estimator']['combined_relative_standard_uncertainty_ppm_decimal']=val
            altered['certificate']['comparison_only']={'terminal':val,'dark_uncertainty':val}
            self.assertEqual(d.evaluate(p,d.project_records(p,altered)),reference)

    def test_noncanonical_rationals_and_JSON_are_errors(self):
        for value in [{'numerator':'2','denominator':'2'},{'numerator':'1','denominator':'0'},
                      {'numerator':1,'denominator':'2'},{'numerator':'01','denominator':'2'}]:
            with self.assertRaises(d.DiagnosticError):d.rational(value)
        for value in ['{"x":1,"x":2}','{"x":NaN}']:
            with self.assertRaises(d.DiagnosticError):d._json(value)


class ConfigurationArtifactTests(unittest.TestCase):
    def test_artifact_is_current(self):
        a=d.check_artifact();self.assertEqual(len(a['results']['models']),4)
        self.assertEqual(a['audit_status_at_freeze']['status'],d.PROVISIONAL)
        self.assertIs(a['known_prior_information']['outcome_blind'],False)
        self.assertTrue(all(a['claim_limits'].values()))

    def test_M0_retains_PR48_baseline_verification_only(self):
        p=local_protocol();ref=p['verification_only_baseline'];data=(d.ROOT/ref['path']).read_bytes()
        self.assertEqual(d.digest(data),ref['sha256'])
        expected=d.at(d._json(data),ref['field']);self.assertEqual(expected,ref['value'])
        out=d.evaluate(p,d.project_records(p,records(p)))
        self.assertEqual(out['models'][0]['Q'],d.rational(expected))
        self.assertNotIn(ref['path'],d.source_paths(p))

    def test_corrupt_output_or_source_is_rejected_read_only(self):
        original=Path.read_text
        def bad(path,*args,**kwargs):
            if path.resolve()==(d.ROOT/d.OUTPUT).resolve():return '{"schema_version":999}\n'
            return original(path,*args,**kwargs)
        with patch.object(Path,'read_text',bad),self.assertRaises(d.DiagnosticError):d.check_artifact()
        original_bytes=Path.read_bytes
        def changed(path,*args,**kwargs):
            b=original_bytes(path,*args,**kwargs)
            return b+b' ' if path.resolve()==(d.ROOT/d.MODULE).resolve() else b
        with patch.object(Path,'read_bytes',changed),self.assertRaises(d.DiagnosticError):d.build_artifact()

    def test_actual_production_file_and_git_read_closure(self):
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
            commands.append((args,kwargs.get('cwd')))
            for arg in args:
                if isinstance(arg,str) and ':' in arg:
                    ref,path=arg.split(':',1)
                    if len(ref)==40 and all(c in '0123456789abcdef' for c in ref):git_paths.add(path)
            return real_run(args,*more,**kwargs)
        p=local_protocol()
        with ExitStack() as stack:
            for owner,name in [(Path,'read_bytes'),(Path,'read_text'),(builtins,'open'),(io,'open'),(os,'open')]:
                stack.enter_context(patch.object(owner,name,tracked(getattr(owner,name))))
            stack.enter_context(patch.object(subprocess,'run',tracked_run))
            d.build_artifact()
        expected=set(d.source_paths(p));self.assertEqual(seen,expected);self.assertEqual(git_paths,expected)
        for command,cwd in commands:
            if command[1]!='-C':
                self.assertIn(command,[['git','rev-parse','--show-toplevel'],['git','rev-parse','--is-shallow-repository']])
                self.assertEqual(Path(cwd).resolve(),root);continue
            self.assertEqual(command[:3],['git','-C',str(root)])
            self.assertIn(command[3],{'show','log','merge-base','rev-parse','rev-list','diff','cat-file'})
            if command[3]=='show' and '-s' not in command:
                self.assertIn(command[-1].split(':',1)[1],expected)
            if command[3]=='log':
                self.assertIn('--',command)
                self.assertLessEqual(set(command[command.index('--')+1:]),expected|{d.OUTPUT.as_posix(),d.MUTATION_OUTPUT.as_posix()})
            self.assertFalse(any('hust' in str(arg).lower() or 'bipm' in str(arg).lower() for arg in command))
        # Verify the static repository import closure too, including imports in helper functions.
        closure=set();pending=[d.MODULE]
        while pending:
            path=pending.pop()
            if path in closure:continue
            closure.add(path)
            tree=ast.parse((root/path).read_text())
            for node in ast.walk(tree):
                if isinstance(node,ast.ImportFrom) and node.module and node.module.startswith('Discovery.'):
                    pending.append(node.module.replace('.','/')+'.py')
        self.assertEqual(closure,{d.MODULE,'Discovery/nist_2026_n4_experimental_estimator.py',
                                 'Discovery/preregistration_history.py','Discovery/source_history.py'})


if __name__=='__main__':unittest.main()
