"""Independent behavior oracles separated from artifact/history checks."""
import ast
import builtins
import copy
from fractions import Fraction as F
import io
import json
import os
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from Discovery import nist_2026_torque_response_feasibility as n


def protocol():
    return n._json((n.ROOT / n.PREREGISTRATION_PATH).read_bytes())


def value(record):
    return F(record['numerator'], record['denominator'])


def evidence(**updates):
    e = {'essential_access': True, 'locators': ['synthetic contract, fixture'], 'stage': 'final',
         'domain': 'global', 'source_authorized': True, 'all_admissible_same': True,
         'representatives': [(F(1), F(0), F(3), F(0))], 'absolute_identified': True, 'obstruction': ''}
    e.update(updates)
    return e


class TorqueBehaviorTests(unittest.TestCase):
    def test_independent_forward_difference_identity(self):
        p = protocol()
        for k, row in enumerate(p['permitted_input_projection']['campaigns']):
            # Forward two-position torque, independently expressed in original units.
            ms = F(p['permitted_input_projection']['source_masses_g'][row['material']]) / 1000
            mt = F('1150.156') / 1000
            radius = F(row['Rs_mm']) / 1000
            gamma = F(row['Gamma_table15'])
            result = n.preliminary_response(p)[2*k]
            for tau in (F(-7,3), F(0), F(5,11)):
                delta_g = tau * value(result['d_SI'])
                plus = delta_g * 8 * ms * mt * gamma / radius
                minus = delta_g * 8 * ms * mt * (-gamma) / radius
                self.assertEqual(plus - minus, tau)
            self.assertEqual(value(n.preliminary_response(p)[2*k+1]['d_SI']), 0)

    def test_prefix_and_unit_dimensions(self):
        p = protocol()
        for r in n.preliminary_response(p):
            self.assertEqual(value(r['d_U_per_pNm']), value(r['d_SI']) / 10)
        self.assertEqual(F(p['units']['pNm_to_Nm']) * 1000, F(p['units']['nNm_to_Nm']))
        # Torque (L² M T^-2) / K (M²/L) yields G (L³ M^-1 T^-2).
        self.assertEqual(tuple(a-b for a,b in zip((2,1,-2),(-1,2,0))), (3,-1,-2))

    def test_orders(self):
        p = protocol()
        labels = p['orders']['preliminary']
        paper = p['orders']['paper_table15_row_major']
        self.assertEqual([paper[i] for i in p['orders']['canonical_to_paper_indices']], labels)
        self.assertEqual([r['preliminary_label'] for r in n.preliminary_response(p)], labels)
        self.assertEqual(p['orders']['configuration'], ['copper_servo','copper_free','sapphire_servo','sapphire_free'])

    def test_coefficient_consumption_without_digest_gate(self):
        p = protocol(); old = n.preliminary_response(p)
        for k in range(4):
            q = copy.deepcopy(p); q['permitted_input_projection']['campaigns'][k]['Rs_mm'] = str(2*F(q['permitted_input_projection']['campaigns'][k]['Rs_mm']))
            new = n.preliminary_response(q)
            for i in range(8):
                self.assertEqual(value(new[i]['d_SI']), value(old[i]['d_SI']) * (2 if i//2 == k else 1))
        for field in ('Gamma_table15',):
            q=copy.deepcopy(p); q['permitted_input_projection']['campaigns'][1][field]='1'
            self.assertNotEqual(n.preliminary_response(q)[2]['d_SI'],old[2]['d_SI'])
        q=copy.deepcopy(p);q['permitted_input_projection']['test_mass_g']='2300.312'
        self.assertEqual(value(n.preliminary_response(q)[0]['d_SI']),value(old[0]['d_SI'])/2)
        q=copy.deepcopy(p);q['permitted_input_projection']['source_masses_g']['copper']='22383.36'
        self.assertEqual(value(n.preliminary_response(q)[0]['d_SI']),value(old[0]['d_SI'])/2)
        self.assertEqual(n.preliminary_response(q)[6],old[6])

    def test_excluded_invariance_without_digest_gate(self):
        p=protocol();q=copy.deepcopy(p)
        q['excluded_context']={'torque_values':[9,8,7,6,5,4,3,2],'G_values':[100,200,300,400],'prior_results':{'Q':999}}
        self.assertEqual(n.preliminary_response(q),n.preliminary_response(p))
        a=n._json((n.ROOT/n.ATTESTATION).read_bytes())
        self.assertEqual(n.result_from_inputs(q,a),n.result_from_inputs(p,a))

    def test_frozen_sections_consumed_or_rejected(self):
        p=protocol()
        for key in p:
            if key in ('permitted_input_projection','excluded_context'):continue
            q=copy.deepcopy(p);q[key]={'unsupported_mutation':True}
            with self.assertRaises(n.FeasibilityError,msg=key):n.validate_protocol(q)
        for key in p['mathematical_policy']:
            q=copy.deepcopy(p);q['mathematical_policy'][key]='changed'
            with self.assertRaises(n.FeasibilityError):n.validate_protocol(q)

    def test_nonfinite_and_invalid_coefficients(self):
        for v in ('NaN','Infinity','1/0',0,-1,True,float('nan')):
            p=protocol();p['permitted_input_projection']['test_mass_g']=v
            with self.assertRaises(n.FeasibilityError):n.preliminary_response(p)
        p=protocol();p['permitted_input_projection']['campaigns'].reverse()
        with self.assertRaises(n.FeasibilityError):n.preliminary_response(p)

    def test_affine_global_response_with_constant(self):
        H=((F(1),F(2)),(F(-3),F(1)));g=(F(2),F(7));d=(F(4),F(-1));c=(F(5),F(-2))
        a=n.affine_response(H,d)
        for tau in (F(-7),F(0),F(5,3)):
            base=tuple(x+y for x,y in zip(n.mv(H,g),c));new=tuple(x+y for x,y in zip(n.mv(H,tuple(x+tau*y for x,y in zip(g,d))),c))
            self.assertEqual(tuple(x-y for x,y in zip(new,base)),tuple(tau*x for x in a))

    def test_coupled_posterior_normal_equations(self):
        p=protocol()['synthetic_policy'];X=tuple(tuple(F(v) for v in row) for row in p['design_rows']);w=tuple(map(F,p['weights']));d=tuple(map(F,p['servo_direction']))
        for prior in p['prior_precision_alternatives']:
            lam=tuple(map(F,prior));H=n.posterior_linear_map(X,w,lam);a=n.coupled_response(H,d)
            # Independent stationarity oracle, no production inverse or mm.
            residual=[sum(X[i][j]*a[j] for j in range(4))-d[i] for i in range(6)]
            for j in range(4):
                self.assertEqual(sum(w[i]*X[i][j]*residual[i] for i in range(6))+lam[j]*a[j],0)
            self.assertNotEqual(a[1],0)
            self.assertNotEqual(a[0],sum(d[::2])/3)

    def test_genuine_equivariance_without_sampler(self):
        p=protocol()['synthetic_policy'];X=tuple(tuple(F(v) for v in row) for row in p['design_rows'])
        for prior in p['prior_precision_alternatives']:
            H=n.posterior_linear_map(X,p['weights'],prior)
            # Constant servo input equals a model intercept column; nuisance priors unchanged.
            self.assertEqual(n.coupled_response(H,(1,0,1,0,1,0)),(1,0,0,0))
            self.assertEqual(n.coupled_response(H,(1,1,1,1,1,1)),(1,1,0,0))

    def test_subspace_rank_equivalence_and_obstruction(self):
        a=(F(1),F(0),F(3),F(0));b=tuple(-4*x+7 for x in a)
        self.assertTrue(n.same_subspace(a,b))
        self.assertFalse(n.same_subspace(a,(1,0,4,0)))
        self.assertEqual(len(n.mean_subspace(a)),2)
        for a in ((0,0,0,0),(2,2,2,2)):
            self.assertEqual(len(n.mean_subspace(a)),1)
            result=n.mapping_disposition(protocol(),evidence(representatives=[a]))
            self.assertEqual(result['contrast_status'],'NOT_TESTABLE_AS_INTERNAL_CONTRAST')

    def test_all_dispositions(self):
        p=protocol()
        self.assertEqual(n.mapping_disposition(p,evidence())['disposition'],'GO_FULL_RESPONSE')
        a=(1,0,3,0);b=tuple(2*x+7 for x in a)
        e=evidence(representatives=[a,b],absolute_identified=False)
        self.assertEqual(n.mapping_disposition(p,e)['disposition'],'GO_MEAN_SUBSPACE_ONLY')
        for stage in ('preliminary','local','assumed','family'):
            self.assertEqual(n.mapping_disposition(p,evidence(stage=stage))['disposition'],'CONDITIONAL_MAPPING_ONLY')
        self.assertEqual(n.mapping_disposition(p,evidence(domain='bounded'))['disposition'],'CONDITIONAL_MAPPING_ONLY')
        self.assertEqual(n.mapping_disposition(p,evidence(essential_access=False))['disposition'],'UNRESOLVED_SOURCE_ACCESS')
        self.assertEqual(n.mapping_disposition(p,evidence(representatives=[],source_authorized=False,all_admissible_same=False,absolute_identified=False,obstruction='Not specified in reviewed section'))['disposition'],'NO_GO_IDENTIFIABILITY')
        self.assertEqual(n.mapping_disposition(p,evidence(representatives=[a,(1,0,4,0)],all_admissible_same=False,absolute_identified=False))['disposition'],'NO_GO_IDENTIFIABILITY')

    def test_evidence_errors_are_not_no_go(self):
        for updates in ({'locators':[]},{'representatives':[]},{'stage':'garbage'},{'essential_access':'false'},{'representatives':[(1,0,3,0),(1,0,4,0)]}):
            with self.assertRaises(n.FeasibilityError):n.mapping_disposition(protocol(),evidence(**updates))

    def test_local_jacobian_not_global(self):
        # f(x)=x²: local derivative 2 at x=1 misses tau² for finite tau.
        tau=F(2);self.assertNotEqual((1+tau)**2-1,2*tau)
        result=n.mapping_disposition(protocol(),evidence(stage='local',domain='local'))
        self.assertIsNone(result['response']);self.assertIsNone(result['subspace'])

    def test_actual_source_verdict_and_absence_limits(self):
        p=protocol();a=n._json((n.ROOT/n.ATTESTATION).read_bytes());r=n.result_from_inputs(p,a)
        self.assertEqual(r['identification']['disposition'],'NO_GO_IDENTIFIABILITY')
        self.assertIsNone(r['identification']['response']);self.assertIsNone(r['identification']['subspace'])
        self.assertTrue(r['synthetic_certificate']['different_mean_subspaces'])
        self.assertTrue(all(v is False for v in r['prohibited_action_flags'].values()))
        self.assertIn('not reviewed',p['corpus']['associated_material_check'])
        for row in r['aggregation_findings']:
            self.assertTrue(row['locator']);self.assertTrue(row['supplies']);self.assertTrue(row['unspecified'])

    def test_canonical_json(self):
        for raw in ('{"x":1,"x":2}','{"x":NaN}','{"x":Infinity}','{"x":1e400}'):
            with self.assertRaises(n.FeasibilityError):n._json(raw)
        with self.assertRaises(ValueError):n.serialize_artifact({'x':float('nan')})
        self.assertEqual(n.record(F(-2,4)),{'numerator':-1,'denominator':2})


class TorqueArtifactTests(unittest.TestCase):
    def test_freshness(self):
        n.check_artifact()

    def test_stale_artifact_and_future_anchor_rejected(self):
        original=Path.read_bytes
        def changed(path):
            raw=original(path)
            if path == n.ROOT/n.OUTPUT:
                payload=n._json(raw);payload['identification']['disposition']='GO_FULL_RESPONSE'
                return n.serialize_artifact(payload).encode()
            return raw
        with patch.object(Path,'read_bytes',changed):
            with self.assertRaises(n.FeasibilityError):n.check_artifact()
        with patch.object(n,'ANCHOR',{**n.ANCHOR,'created_at':'2100-01-01T00:00:00Z'}):
            with self.assertRaises(n.FeasibilityError):n.verify_implementation_chronology()

    def test_source_snapshot_binding(self):
        result=n.build_artifact()
        self.assertEqual(result['provenance']['source_sha256'][n.PREREGISTRATION_PATH.as_posix()],n.FREEZE_DIGEST)
        with patch.object(n,'SOURCE_PATHS',n.SOURCE_PATHS):
            self.assertTrue(result['provenance']['first_introductions'])

    def test_actual_read_and_import_closure(self):
        paths=set();blobs=set();calls=[]
        original_builtin=builtins.open; original_io=io.open; original_os=os.open; original_run=subprocess.run
        def remember(file):
            if isinstance(file,(str,os.PathLike)):
                path=Path(file).resolve()
                if path.is_relative_to(n.ROOT):paths.add(path.relative_to(n.ROOT).as_posix())
        def bopen(file,*args,**kw):remember(file);return original_builtin(file,*args,**kw)
        def iopen(file,*args,**kw):remember(file);return original_io(file,*args,**kw)
        def oopen(file,*args,**kw):remember(file);return original_os(file,*args,**kw)
        def run(cmd,*args,**kw):
            calls.append(cmd)
            if cmd[0]=='git':
                for arg in cmd:
                    if ':' in str(arg) and str(arg).split(':',1)[1].startswith(('Discovery/','Experiments/','Notes/')):
                        blobs.add(str(arg).split(':',1)[1])
            return original_run(cmd,*args,**kw)
        with patch('builtins.open',bopen),patch('io.open',iopen),patch('os.open',oopen),patch('subprocess.run',run):n.build_artifact()
        self.assertEqual(paths,set(n.SOURCE_PATHS))
        self.assertEqual(blobs,set(n.SOURCE_PATHS))
        self.assertTrue(calls);self.assertTrue(all(c[0]=='git' for c in calls))
        # Transitive repository import closure, including helpers, excludes all measurement engines.
        seen=set();queue=[n.MODULE]
        while queue:
            path=queue.pop()
            if path in seen:continue
            seen.add(path);tree=ast.parse((n.ROOT/path).read_text())
            for node in ast.walk(tree):
                if isinstance(node,ast.ImportFrom) and node.module and node.module.startswith('Discovery.'):
                    queue.append(node.module.replace('.','/')+'.py')
                if isinstance(node,ast.Import):
                    for alias in node.names:
                        if alias.name.startswith('Discovery.'):queue.append(alias.name.replace('.','/')+'.py')
        self.assertEqual(seen,{n.MODULE,*n.HELPERS})

    def test_changed_attestation_rejected(self):
        p=protocol();a=n._json((n.ROOT/n.ATTESTATION).read_bytes());a['anchor']['created_at']='2000-01-01T00:00:00Z'
        with self.assertRaises(n.FeasibilityError):n.result_from_inputs(p,a)

    def test_freeze_sole_file_and_anchor(self):
        n.verify_preregistration()
        self.assertEqual(n.git(n.ROOT,'diff','--name-only',n.BASE,n.FREEZE).decode().splitlines(),[n.PREREGISTRATION_PATH.as_posix()])
        n.verify_implementation_chronology()

    def test_history_fixtures(self):
        # Minimal real Git histories exercise chronology and strict freeze without full project fixtures.
        with TemporaryDirectory() as temp:
            root=Path(temp)
            def git(*args):return subprocess.run(['git','-C',str(root),*args],check=True,capture_output=True).stdout.decode().strip()
            git('init');git('config','user.name','Test');git('config','user.email','test@example.invalid')
            (root/'base').write_text('base');git('add','.');git('commit','-m','base');base=git('rev-parse','HEAD')
            (root/'freeze.json').write_text('{}');git('add','.');git('commit','-m','freeze');freeze=git('rev-parse','HEAD')
            from Discovery.preregistration_history import verify_preregistration_freeze
            verify_preregistration_freeze(root,baseline=base,commit=freeze,path='freeze.json',sha256=n.digest(b'{}'))
            (root/'freeze.json').write_text('{"change":1}');git('add','.');git('commit','-m','changed')
            (root/'freeze.json').write_text('{}');git('add','.');git('commit','-m','reverted')
            with self.assertRaises(n.SourceVerificationError):verify_preregistration_freeze(root,baseline=base,commit=freeze,path='freeze.json',sha256=n.digest(b'{}'))
