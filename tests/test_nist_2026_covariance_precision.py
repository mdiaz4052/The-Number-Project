"""Exact independent algebra/coverage oracles and bounded provenance integration."""
import builtins
import copy
from dataclasses import replace
from fractions import Fraction as F
from itertools import combinations, permutations, product
import io
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from Discovery import nist_2026_covariance_precision as n


def protocol():
    return n._json((n.ROOT / n.PREREGISTRATION_PATH).read_bytes())


def records(p):
    return {k: n._json((n.ROOT / v['path']).read_bytes()) for k, v in p['upstream_records'].items()}


def real_family():
    p = protocol()
    return n.family_from_projection(p, n.project_records(p, records(p)))


def det_cofactor(A):
    if len(A) == 1:
        return A[0][0]
    return sum(((-1) ** j * A[0][j] * det_cofactor(tuple(tuple(row[k] for k in range(len(A)) if k != j) for row in A[1:]))
                for j in range(len(A))), F(0))


def adjugate_inverse(A):
    d = det_cofactor(A)
    if len(A) == 1:
        return ((1 / d,),)
    return tuple(tuple((-1) ** (i + j) * det_cofactor(tuple(tuple(A[r][c] for c in range(len(A)) if c != i)
                for r in range(len(A)) if r != j)) / d for j in range(len(A))) for i in range(len(A)))


def oracle_Q(R, V, x):
    y = n.mv(R, x)
    return n.quadratic(adjugate_inverse(n.mm(n.mm(R, V), n.transpose(R))), y)


def oracle_profile(X, V, x):
    W = adjugate_inverse(V)
    XtW = n.mm(n.transpose(X), W)
    beta = n.mv(adjugate_inverse(n.mm(XtW, X)), n.mv(XtW, x))
    residual = tuple(a - b for a, b in zip(x, n.mv(X, beta)))
    return n.quadratic(W, residual)


def psd(A):
    return all(det_cofactor(tuple(tuple(A[i][j] for j in inds) for i in inds)) >= 0
               for k in range(1, len(A) + 1) for inds in combinations(range(len(A)), k))


def subtract(A, B):
    return tuple(tuple(a - b for a, b in zip(row, other)) for row, other in zip(A, B))


def fixture(cutoff=F(1), h=F(0), width=F(0)):
    a = (F(1), F(2), F(3), F(4))
    center = (F(10**6), F(500000), F(10**6, 3), F(250000)) + (F(0),) * 6
    box = tuple(n.cell(v, width if i >= 4 else F(0)) for i, v in enumerate(center))
    R = ((F(-1), F(1), F(0), F(0)),)
    model = {'id': 'synthetic', 'R': R, 'X': n.transpose(((F(1),) * 4,)), 'df': 1, 'cutoff': cutoff}
    return n.Family(a, (h,) * 4, box, (model,))


class InputTests(unittest.TestCase):
    def test_projection_and_precisions(self):
        p = protocol(); f = real_family()
        self.assertEqual(p['family']['dimension'], 14)
        self.assertEqual(len(f.box), 10)
        self.assertEqual(f.h, (F(1, 2000000),) * 4)
        self.assertEqual([hi - lo for lo, hi in f.box], [F(1, 10)] * 4 + [F(1, 100)] * 6)
        midpoint = tuple((lo + hi) / 2 for lo, hi in f.box)
        self.assertEqual(midpoint[6:8], (F(3, 25), F(23, 100)))
        self.assertEqual(n.correlation(midpoint[4:]), n.transpose(n.correlation(midpoint[4:])))
        self.assertTrue(all(n.correlation(midpoint[4:])[i][i] == 1 for i in range(4)))

    def test_strict_missing_duplicate_nonfinite_schema(self):
        for raw in ['{"a":1,"a":2}', '{"a":NaN}', '{"a":Infinity}', 'oops']:
            with self.assertRaises(ValueError): n._json(raw)
        for value in [1.2, True, None, 'nan', {'numerator': '2', 'denominator': '4'}]:
            with self.assertRaises(ValueError): n.rational(value)
        p = protocol()
        for key in ['family', 'refinement', 'source_evidence']:
            changed = copy.deepcopy(p); del changed[key]
            with self.assertRaises(n.PrecisionError): n.validate_protocol(changed)
        changed = copy.deepcopy(p); changed['extra'] = 1
        with self.assertRaises(n.PrecisionError): n.validate_protocol(changed)
        rec = records(p); del rec['certificate']['estimator']['correlation_matrix']
        with self.assertRaises(n.PrecisionError): n.project_records(p, rec)

    def test_behavior_consumption_and_excluded_fields(self):
        p = protocol(); rec = records(p)
        before = n.family_from_projection(p, n.project_records(p, rec))
        rec['certificate']['estimator']['estimate'] = 'forbidden'
        rec['source']['consensus_layer'] = {'terminal_dark': 'not numerical input'}
        rec['models']['upstream_records'] = {'BIPM_or_48': 'not consumed'}
        rec['models']['audit_status_at_freeze'] = 'not scientific input'
        rec['authorization']['published_bayesian_consensus_layer'] = None
        self.assertEqual(before, n.family_from_projection(p, n.project_records(p, rec)))
        a = (F(1), F(2), F(3), F(4)); center = (F(10**6),) * 4 + (F(0),) * 6
        V = n.covariance(a, center)
        self.assertNotEqual(V, n.covariance((F(2), *a[1:]), center))
        basebox = tuple(n.cell(v, F(0)) for v in center)
        sbox = (n.cell(center[0], F(100)), *basebox[1:])
        rbox = (*basebox[:4], n.cell(F(0), F(1, 10)), *basebox[5:])
        self.assertNotEqual(n.covariance_enclosure(a, sbox)['E'], n.covariance_enclosure(a, basebox)['E'])
        self.assertNotEqual(n.covariance_enclosure(a, rbox)['E'], n.covariance_enclosure(a, basebox)['E'])
        self.assertNotEqual(n.display_terms(n.eye(4), a, (F(0),) * 4), n.display_terms(n.eye(4), a, (F(1),) * 4))
        f = fixture(h=F(1, 10)); model = f.models[0]
        center = tuple((lo+hi)/2 for lo,hi in f.box)
        s1 = n.point_state(f, model, center, f.a)
        s2 = n.point_state(f, model, center, tuple(a + F(1, 10) for a in f.a))
        self.assertEqual(s1['V'], s2['V'])


class MatrixTests(unittest.TestCase):
    def test_corner_convexity_inventory_and_nonpd(self):
        f = fixture(width=F(1, 20))
        v = n.family_validity(f.box)
        self.assertEqual(len(v['corners']), 64)
        self.assertEqual(v['status'], 'POSITIVE_DEFINITE_FULL_BOX')
        for row in v['corners']:
            self.assertEqual(row['leading_principal_minors'], tuple(det_cofactor(tuple(r[:k] for r in row['P'][:k])) for k in range(1, 5)))
        box = f.box[:4] + ((F(-3, 5), F(3, 5)),) * 6
        self.assertTrue(all(v > 0 for v in n.minors(n.correlation((F(0),) * 6))))
        bad = n.evaluate(replace(f, box=box))
        self.assertEqual(bad['models']['synthetic']['disposition'], n.DOMAIN)
        self.assertTrue(bad['family_validity']['offending_corners'])
        singular = f.box[:4] + ((F(0), F(1)),) + ((F(0), F(0)),) * 5
        self.assertEqual(n.family_validity(singular)['status'], 'BOX_CONTAINS_NON_PD')
        with self.assertRaises(n.PrecisionError): n.inverse(((F(1), F(1)), (F(1), F(1))))
        with self.assertRaises(n.PrecisionError): n.family_validity(((F(0), F(1)),) + f.box[1:])
        with self.assertRaises(n.PrecisionError): n.family_validity(f.box[:4] + ((F(-2), F(0)),) + f.box[5:])

    def test_signed_intervals_positive_squares_midpoint_distinction(self):
        for left, right in [((F(-2), F(3)), (F(-5), F(7))), ((F(-4), F(-2)), (F(1), F(3)))]:
            lo, hi = n.interval_product(left, right)
            for a, b in product((left[0], sum(left)/2, left[1]), (right[0], sum(right)/2, right[1])):
                self.assertTrue(lo <= a*b <= hi)
        f = fixture(width=F(1, 20)); box = list(f.box)
        box[0] = (F(900000), F(1100000))
        enc = n.covariance_enclosure(f.a, tuple(box))
        self.assertEqual(enc['V_minus'][0][0], F(81, 100))
        self.assertEqual(enc['V_plus'][0][0], F(121, 100))
        self.assertNotEqual(enc['Vc'][0][0], (enc['V_minus'][0][0]+enc['V_plus'][0][0])/2)
        for bits in [(0,) * 10, (1,) * 10, tuple(i % 2 for i in range(10))]:
            V = n.covariance(f.a, tuple(box[k][b] for k,b in enumerate(bits)))
            for i,j in product(range(4), repeat=2):
                self.assertTrue(enc['V_minus'][i][j] <= V[i][j] <= enc['V_plus'][i][j])
        # Entrywise extrema can conflict: V00 at high fixes s0 high, while
        # positive V01 minimum requires s0 low. They need not coexist.
        a=(F(1),)*4; b=((F(1),F(2)),)*4+((F(1,10),F(1,10)),)*6
        e=n.covariance_enclosure(a,b)
        self.assertNotEqual(e['V_minus'][0][1], n.covariance(a,(F(2),F(1),F(1),F(1))+(F(1,10),)*6)[0][1])

    def test_ldl_sandwich_cross_terms_and_inverse_order(self):
        V = ((F(4),F(1),F(0)),(F(1),F(3),F(1)),(F(0),F(1),F(2)))
        L,d,T=n.ldl(V)
        self.assertEqual(n.mm(n.mm(L,n.diag(d)),n.transpose(L)), V)
        self.assertEqual(n.inverse(V), adjugate_inverse(V))
        R=((F(1),F(-1),F(1)),(F(0),F(1),F(-1)))
        E=((F(1,10),F(1,30),F(1,40)),(F(1,30),F(1,10),F(1,50)),(F(1,40),F(1,50),F(1,10)))
        cert=n.sandwich(R,V,E)
        Z=cert['Z']
        for i,j in product(range(2),repeat=2):
            oracle=sum(abs(Z[i][k])*E[k][l]*abs(Z[j][l]) for k,l in product(range(3),repeat=2))
            self.assertEqual(cert['F'][i][j],oracle)
        for sign in (-1,1):
            W=tuple(tuple(sign*v for v in row) for row in cert['F'])
            self.assertTrue(psd(subtract(n.diag(cert['g']),W)))
        actual=n.mm(n.mm(n.transpose(R),adjugate_inverse(n.mm(n.mm(R,V),n.transpose(R)))),R)
        self.assertTrue(psd(subtract(actual,cert['H_lower'])))
        self.assertTrue(psd(subtract(cert['H_upper'],actual)))
        x=(F(1),F(2),F(-3)); y=n.mv(n.mm(T,n.eye(3)),x)
        self.assertEqual(n.quadratic(n.inverse(V),x),n.quadratic(n.inverse(n.mm(n.mm(T,V),n.transpose(T))),y))

    def test_valid_family_unavailable_upper(self):
        f=fixture(width=F(1,5)); enc=n.covariance_enclosure(f.a,f.box)
        # A valid covariance box can have a poorly conditioned contrast basis.
        R=((F(1),F(-1),F(0),F(0)),(F(1),F(-1),F(1,1000),F(-1,1000)))
        proof=n.local_certificate(R,enc,f.a,f.h)
        self.assertEqual(n.family_validity(f.box)['status'],'POSITIVE_DEFINITE_FULL_BOX')
        self.assertIsNone(proof['bounds'][1])
        self.assertGreaterEqual(proof['bounds'][0],0)
        self.assertTrue(all(v>0 for v in n.minors(n.mm(n.mm(R,enc['Vc']),n.transpose(R)))))


class ModelTests(unittest.TestCase):
    def test_independent_mean_space_and_marginal(self):
        models=n.model_geometry(protocol())
        V=((F(3),F(1),F(0),F(0)),(F(1),F(4),F(1),F(0)),(F(0),F(1),F(5),F(1)),(F(0),F(0),F(1),F(6)))
        x=(F(2),F(-1),F(3),F(4))
        for model in models:
            Q=oracle_Q(model['R'],V,x)
            self.assertEqual(Q,oracle_profile(model['X'],V,x))
            self.assertEqual(model['df']+len(model['X'][0]),4)
            self.assertEqual(Q,oracle_Q(model['R'],V,tuple(v+100 for v in x)))
        R=models[2]['R']; omitted=models[0]['R'][:1]
        C=n.mm(n.mm(R,V),n.transpose(R)); cross=n.mm(n.mm(R,V),n.transpose(omitted))
        cond=subtract(C,n.mm(n.mm(cross,adjugate_inverse(n.mm(n.mm(omitted,V),n.transpose(omitted)))),n.transpose(cross)))
        self.assertNotEqual(n.quadratic(adjugate_inverse(C),n.mv(R,x)),n.quadratic(adjugate_inverse(cond),n.mv(R,x)))

    def test_units_permutation_and_fixed_common_shift(self):
        f=real_family(); parameters=tuple((lo+hi)/2 for lo,hi in f.box); V=n.covariance(f.a,parameters)
        for model in f.models:
            R=model['R']; Q=oracle_Q(R,V,f.a)
            scale=F(1000)
            Vs=n.covariance(tuple(scale*a for a in f.a),parameters)
            self.assertEqual(Vs,tuple(tuple(scale**2*v for v in row) for row in V))
            self.assertEqual(Q,oracle_Q(R,Vs,tuple(scale*a for a in f.a)))
            self.assertEqual(Q,oracle_Q(R,V,tuple(a+123 for a in f.a)))
            perm=(2,0,3,1); P=n.correlation(parameters[4:])
            newrho=tuple(P[perm[i]][perm[j]] for i,j in n.PAIRS)
            anew=tuple(f.a[i] for i in perm); snew=tuple(parameters[i] for i in perm)
            Vnew=n.covariance(anew,snew+newrho)
            Rnew=tuple(tuple(row[i] for i in perm) for row in R)
            self.assertEqual(Q,oracle_Q(Rnew,Vnew,anew))
        changed=copy.deepcopy(protocol()); changed['models'][0]['residual_df']=2
        with self.assertRaises(n.PrecisionError):n.model_geometry(changed)

    def test_midpoint_and_zero_radius_parity(self):
        f=real_family(); old=n._json((n.ROOT/'Experiments/GMeasurements/nist_2026_configuration_models_v1.json').read_bytes())
        center=tuple((lo+hi)/2 for lo,hi in f.box)
        enc=n.covariance_enclosure(f.a,tuple((v,v) for v in center))
        rows={row['id']:row for row in old['results']['models']}
        for model in f.models:
            row=rows[model['id']]; proof=n.local_certificate(model['R'],enc,f.a,f.h)
            self.assertEqual(oracle_Q(model['R'],enc['Vc'],f.a),n.rational(row['Q']))
            self.assertEqual(proof['bounds'],tuple(map(n.rational,row['display']['bounds'])))
            zero=n.local_certificate(model['R'],enc,f.a,(F(0),)*4)
            self.assertEqual(zero['bounds'],(n.rational(row['Q']),)*2)

    def test_display_entire_box_and_lower_truncation(self):
        H=((F(1),F(-1)),(F(-1),F(1))); a=(F(0),F(0)); h=(F(1),F(1))
        proof=n.display_terms(H,a,h)
        self.assertEqual(proof['upper'],F(4));self.assertEqual(proof['lower'],0)
        for x in product((F(-1),F(0),F(1)),repeat=2):
            self.assertTrue(proof['lower']<=n.quadratic(H,x)<=proof['upper'])
        self.assertEqual(n.display_terms(((F(1),),),(F(1),),(F(2),))['lower'],0)


class DecisionCoverageTests(unittest.TestCase):
    def test_equality_variation_and_outer_bound_semantics(self):
        self.assertEqual(n.classify((F(0),F(1)),F(1),{}),n.NONFLAG)
        self.assertEqual(n.classify((F(1),F(2)),F(1),{}),n.UNRESOLVED)
        self.assertEqual(n.classify((F(2),None),F(1),{}),n.FLAG)
        self.assertEqual(n.classify((F(0),None),F(1),{}),n.UNRESOLVED)
        self.assertEqual(n.classify((F(0),F(2)),F(1),{'flagged':1,'not_flagged':2}),n.VARIATION)
        with self.assertRaises(n.PrecisionError):n.classify((F(2),F(3)),F(1),{'not_flagged':1})
        f=fixture(cutoff=F(1,2),h=F(1,2)); result=n.evaluate(f,0)
        self.assertEqual(result['models']['synthetic']['disposition'],n.VARIATION)
        for w in result['models']['synthetic']['witnesses'].values():n.verify_witness(f,f.models[0],w)
        bad=copy.deepcopy(next(iter(result['models']['synthetic']['witnesses'].values())))
        bad['V']=n.eye(4);bad['Q']=F(-1)
        with self.assertRaises(n.PrecisionError):n.verify_witness(f,f.models[0],bad)
        # Convex quadratic corners are all flagged but interior is not.
        self.assertTrue(all(x*x>F(1,2) for x in (F(-1),F(1))))
        self.assertFalse(F(0)**2>F(1,2))

    def test_cover_and_normalized_ties_inheritance(self):
        box=((F(0),F(2)),(F(0),F(200)))
        self.assertEqual(n.splittable_dimension(box,box),0)
        left,right=n.child_boxes(box,0)
        self.assertEqual(left[0][1],right[0][0])
        self.assertEqual(n.splittable_dimension(left,box),1)
        nodes={'':{'box':box,'split_dimension':0},'0':{'box':left,'split_dimension':None},'1':{'box':right,'split_dimension':None}}
        self.assertTrue(n.validate_cover(nodes,['1','0'],box))
        with self.assertRaises(n.PrecisionError):n.validate_cover(nodes,['0'],box)
        broken=copy.deepcopy(nodes);del broken['1']
        with self.assertRaises(n.PrecisionError):n.validate_cover(broken,['0'],box)
        self.assertEqual(n.ordered_paths(['10','1','00','0']),['0','1','00','10'])
        self.assertEqual(n.intersect_bounds((F(1),None),(F(2),F(4))),(F(2),F(4)))
        with self.assertRaises(n.PrecisionError):n.intersect_bounds((F(5),None),(F(2),F(4)))

    def test_shared_budget_unresolved_determinism_and_unsplit_siblings(self):
        # Zero-width x fixes Q at centers; loose interval proof straddles cutoff,
        # but the restricted witness family has no flagged example at this budget.
        f=fixture(cutoff=F(51,100),width=F(1,20))
        one=n.evaluate(f,0)
        self.assertEqual(one['models']['synthetic']['disposition'],n.UNRESOLVED)
        self.assertEqual(one['stop_reason'],'frozen_split_budget_exhausted')
        a=n.evaluate(f,3); b=n.evaluate(f,3)
        self.assertEqual(n.serialize_artifact(n.exact_tree(a)),n.serialize_artifact(n.exact_tree(b)))
        self.assertLessEqual(a['splits'],3);self.assertEqual(a['evaluated_nodes'],2*a['splits']+1)
        self.assertEqual(len(a['frontier']),a['splits']+1)
        self.assertTrue(n.validate_cover(a['nodes'],a['frontier'],f.box))
        for path,node in a['nodes'].items():
            if path:
                bounds=node['models']['synthetic']['effective_bounds']; parent=a['nodes'][path[:-1]]['models']['synthetic']['effective_bounds']
                self.assertGreaterEqual(bounds[0],parent[0])
                if parent[1] is not None:self.assertLessEqual(bounds[1],parent[1])
        with self.assertRaises(n.PrecisionError):n.evaluate(f,256)
        with self.assertRaises(n.PrecisionError):n.evaluate(f,True)


class SourceEvidenceTests(unittest.TestCase):
    def test_receipt_provenance_and_field_rejection(self):
        p=protocol();att=n._json((n.ROOT/n.ATTESTATION).read_bytes())
        receipt=(n.ROOT/n.RECEIPT).read_bytes();image=(n.ROOT/n.IMAGE).read_bytes()
        self.assertTrue(n.validate_evidence(p,att,receipt,image))
        r=att['source_evidence']['receipt']
        self.assertIn('Copper servo / Sapphire free: 0.23',r['original_nist_report_text'])
        self.assertIn('Copper free / Sapphire servo: 0.12',r['original_nist_report_text'])
        self.assertFalse(r['human_report']['explicit_human_correction_of_typed_pairs_received'])
        self.assertIsNone(r['human_report']['reading_timezone'])
        self.assertFalse(r['source_identity_inherited_not_visible_in_crop']['original_pdf_authenticated'])
        self.assertFalse(att['source_rounding_convention_verified'])
        for keys,value in [(('source_evidence','access_method_as_reported'),'unknown'),
                           (('source_evidence','receipt','human_report','printed_page_as_reported'),27),
                           (('source_rounding_convention_verified',),True),
                           (('source_evidence','receipt','image','hash_scope'),'original PDF')]:
            changed=copy.deepcopy(att);target=changed
            for key in keys[:-1]:target=target[key]
            target[keys[-1]]=value
            with self.assertRaises(n.PrecisionError):n.validate_evidence(p,changed,receipt,image)
        with self.assertRaises(n.PrecisionError):n.validate_evidence(p,att,receipt,image+b'x')


class ChronologyTests(unittest.TestCase):
    def git_fixture(self, root, *args):
        return subprocess.run(['git','-C',str(root),*args],check=True,capture_output=True,text=True).stdout.strip()

    def initialize(self, root):
        self.git_fixture(root,'init','-b','main')
        self.git_fixture(root,'config','user.name','Synthetic chronology fixture')
        self.git_fixture(root,'config','user.email','fixture@example.invalid')
        (root/'source').write_text('first')
        self.git_fixture(root,'add','source');self.git_fixture(root,'commit','-m','initial')
        return self.git_fixture(root,'rev-parse','HEAD')

    def test_merge_inheritance_and_changed_resolution(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp);base=self.initialize(root)
            self.git_fixture(root,'checkout','-b','left')
            (root/'source').write_text('left')
            self.git_fixture(root,'commit','-am','left source')
            left=self.git_fixture(root,'rev-parse','HEAD')
            self.git_fixture(root,'checkout','main')
            (root/'unrelated').write_text('other')
            self.git_fixture(root,'add','unrelated');self.git_fixture(root,'commit','-m','unrelated')
            self.git_fixture(root,'merge','--no-ff','left','-m','pure inherited merge')
            self.assertEqual(n.source_snapshot(root,('source',))['source_commit_sha'],left)
            # A merge with relevant bytes different from every parent creates a
            # new snapshot, even if a later merge inherits that resolution.
            parent=self.git_fixture(root,'rev-parse','HEAD')
            (root/'source').write_text('resolved new source')
            self.git_fixture(root,'add','source');tree=self.git_fixture(root,'write-tree')
            merge=self.git_fixture(root,'commit-tree',tree,'-p',parent,'-p',base,'-m','changed resolution')
            self.git_fixture(root,'reset','--hard',merge)
            self.assertEqual(n.source_snapshot(root,('source',))['source_commit_sha'],merge)
            (root/'source').write_text('uncommitted')
            with self.assertRaises((n.PrecisionError,n.SourceVerificationError)):n.source_snapshot(root,('source',))
            (root/'source').unlink()
            with self.assertRaises((OSError,n.SourceVerificationError)):n.source_snapshot(root,('source',))

    def test_strict_freeze_full_history_and_anchor(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp);base=self.initialize(root)
            (root/'freeze.json').write_text('{}\n');self.git_fixture(root,'add','freeze.json');self.git_fixture(root,'commit','-m','freeze alone')
            freeze=self.git_fixture(root,'rev-parse','HEAD');sha=n.digest(b'{}\n')
            self.assertEqual(n.verify_preregistration_freeze(root,baseline=base,commit=freeze,path='freeze.json',sha256=sha),b'{}\n')
            with self.assertRaises(n.SourceVerificationError):n.verify_preregistration_freeze(root,baseline=freeze,commit=freeze,path='freeze.json',sha256=sha)
            anchor={'created_at':'2100-01-01T00:00:00Z','event':'draft_pull_request_created','freeze_head':freeze,'outcome_blind':False}
            (root/'evaluator').write_text('premature for synthetic future anchor')
            self.git_fixture(root,'add','evaluator');self.git_fixture(root,'commit','-m','evaluator')
            with self.assertRaises(n.PrecisionError):n.first_introductions(root,('evaluator',),freeze,anchor)
            self.git_fixture(root,'checkout','-b','tamper')
            (root/'freeze.json').write_text('{"changed":1}\n');self.git_fixture(root,'commit','-am','alter freeze')
            (root/'freeze.json').write_text('{}\n');self.git_fixture(root,'commit','-am','restore freeze')
            self.git_fixture(root,'checkout','main');self.git_fixture(root,'merge','--no-ff','tamper','-m','side-history merge')
            with self.assertRaises(n.SourceVerificationError):n.verify_preregistration_freeze(root,baseline=base,commit=freeze,path='freeze.json',sha256=sha)

    def test_real_anchor_and_source_before_outputs(self):
        p=n.verify_preregistration();self.assertFalse(p['outcome_blind'])
        self.assertEqual(n.git(n.ROOT,'rev-list','--parents','-n','1',n.FREEZE).decode().split(),[n.FREEZE,n.BASE])
        self.assertEqual(n.ANCHOR['created_at'],'2026-09-11T19:01:42Z')
        chronology=n.verify_implementation_chronology()
        self.assertEqual(set(chronology),{n.MODULE,n.MUTATOR,*n.TESTS,n.ATTESTATION.as_posix(),n.IMAGE,n.RECEIPT,n.SPEC})
        snapshot=n.source_snapshot(n.ROOT,n.SOURCE_PATHS)
        n.verify_output_chronology(n.ROOT,snapshot['source_commit_sha'],(n.OUTPUT.as_posix(),n.NOTE,n.MUTATION_OUTPUT.as_posix()))


# Observe actual file APIs and Git arguments without replacing computation.
def observed(operation):
    files,blobs,calls=set(),set(),[]
    bopen,iopen,oopen,run=builtins.open,io.open,os.open,subprocess.run
    def remember(file):
        if isinstance(file,(str,os.PathLike)):
            path=Path(file).resolve()
            if path.is_relative_to(n.ROOT):files.add(path.relative_to(n.ROOT).as_posix())
    def b(file,*a,**kw):remember(file);return bopen(file,*a,**kw)
    def i(file,*a,**kw):remember(file);return iopen(file,*a,**kw)
    def o(file,*a,**kw):
        resolved=Path(os.readlink('/proc/self/fd/'+str(kw['dir_fd']))) / file if kw.get('dir_fd') is not None and not Path(file).is_absolute() else file
        remember(resolved)
        return oopen(file,*a,**kw)
    def r(cmd,*a,**kw):
        calls.append(cmd)
        for arg in cmd:
            if ':' in str(arg):
                path=str(arg).split(':',1)[1]
                if path.startswith(('Discovery/','Experiments/','Notes/','tests/')):blobs.add(path)
        return run(cmd,*a,**kw)
    with patch('builtins.open',b),patch('io.open',i),patch('os.open',o),patch('subprocess.run',r):
        result=operation()
    return files,blobs,calls,result


class ArtifactIsolationTests(unittest.TestCase):
    def test_builder_and_main_check_read_closure(self):
        files,blobs,calls,result=observed(n.build_artifact)
        self.assertEqual(files,set(n.SOURCE_PATHS));self.assertEqual(blobs,set(n.SOURCE_PATHS))
        self.assertTrue(all(cmd[0]=='git' for cmd in calls))
        with patch.object(n,'build_artifact',return_value=result):
            # The builder above was observed in full; observe the additional
            # main/check reads independently without duplicating its computation.
            files,blobs,calls,_=observed(lambda:n.main(['--check']))
        self.assertEqual(files,{n.OUTPUT.as_posix(),n.NOTE})
        self.assertEqual(blobs,{n.OUTPUT.as_posix(),n.NOTE})
        self.assertTrue(all(cmd[0]=='git' for cmd in calls))
        bootstrap="import json,sys;sys.path.insert(0,sys.argv[1]);from Discovery import nist_2026_covariance_precision;print(json.dumps({k:v.__file__ for k,v in sys.modules.items() if (k=='Discovery' or k.startswith('Discovery.')) and hasattr(v,'__file__')}))"
        imports=json.loads(subprocess.run([sys.executable,'-I','-B','-c',bootstrap,str(n.ROOT)],check=True,capture_output=True,text=True).stdout)
        self.assertEqual(set(imports),set(protocol()['closure']['result_project_imports']))
        self.assertTrue(all(Path(v).is_relative_to(n.ROOT) for v in imports.values()))

    def test_mutation_saved_checker_read_closure(self):
        from Discovery import nist_2026_covariance_precision_mutations as m
        files,blobs,calls,result=observed(m.check_artifact)
        self.assertEqual(files,set(n.SOURCE_PATHS)|{n.MUTATION_OUTPUT.as_posix()})
        self.assertEqual(blobs,set(n.SOURCE_PATHS)|{n.MUTATION_OUTPUT.as_posix()})
        self.assertTrue(all(cmd[0]=='git' for cmd in calls))
        for record in result['records']:
            for phase in ('validated_imports_before','validated_imports_after'):
                self.assertEqual(record['evidence'][phase],m.IMPORTS)
            self.assertLessEqual(set(m.COPY_PATHS),set(record['evidence']['observed_file_open_paths']))

    def test_saved_certificate_bounds_witness_and_coverage_tamper(self):
        raw=(n.ROOT/n.OUTPUT).read_bytes();artifact=n._json(raw)
        # Existing canonical artifact is the immutable expected certificate;
        # target each independently meaningful saved proof surface.
        changes=[]
        bad=copy.deepcopy(artifact);bad['results']['models']['M0']['bounds'][0]={'numerator':'0','denominator':'1'};changes.append(bad)
        bad=copy.deepcopy(artifact);bad['results']['frontier']=[];changes.append(bad)
        bad=copy.deepcopy(artifact);w=next(iter(bad['results']['models']['M0']['witnesses'].values()));w['Q']={'numerator':'0','denominator':'1'};changes.append(bad)
        read_bytes=Path.read_bytes
        for changed in changes:
            replacement=n.serialize_artifact(changed).encode()
            def fake(path):return replacement if path==n.ROOT/n.OUTPUT else read_bytes(path)
            with patch.object(n,'build_artifact',return_value=artifact),patch.object(Path,'read_bytes',fake):
                with self.assertRaises(n.PrecisionError):n.check_artifact()
        # Noncanonical but equivalent JSON fails as well.
        def fake(path):return json.dumps(artifact).encode() if path==n.ROOT/n.OUTPUT else read_bytes(path)
        with patch.object(n,'build_artifact',return_value=artifact),patch.object(Path,'read_bytes',fake):
            with self.assertRaises(n.PrecisionError):n.check_artifact()
