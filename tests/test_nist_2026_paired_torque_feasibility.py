"""Independent hand-expanded algebra and staged evidence controls; no observed contrasts."""
import ast
import builtins
import copy
from fractions import Fraction as F
import io
import os
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from Discovery import nist_2026_paired_torque_feasibility as n


def protocol():
    return n._json((n.ROOT/n.PREREGISTRATION_PATH).read_bytes())


def value(r):
    return F(r['numerator'],r['denominator'])


def decoded(M):
    return tuple(tuple(value(v) for v in row) for row in M)


def covariance_fixture():
    V=[[F(i==j) for j in range(8)] for i in range(8)]
    V[0][1]=V[1][0]=F(1,2)
    # Additional cross-campaign term; strict diagonal dominance proves PD.
    V[0][2]=V[2][0]=F(1,4)
    return tuple(tuple(row) for row in V)


def object_fixture(route='V_y',scope='combined',**updates):
    obj={'route':route,'value':covariance_fixture(),'J':None,'unit_scale':'1','coordinates':{'V_y':'y','V_d':'d','direct_C':'z','J_U':'inputs'}[route],
         'stage':'campaign_torque','scope':scope,'meaning':'centered_covariance','source_authorized':True,'locator':'synthetic source contract','origin':'code'}
    obj.update(updates);return obj


def unknown(id='missing',loading=None,kind='uncertainty',non_type_a=True):
    return {'id':id,'kind':kind,'loading':loading,'locator':'synthetic named source gap','missing':'joint uncertainty or signed loading unspecified','non_type_a':non_type_a}


def model_fixture(**updates):
    e={'comparison_contract':'source_described','comparison_detail':'same synthetic campaign signal',
       'comparison_locator':'synthetic stage contract','essential_access_gaps':[],'candidate_completion_premises':[],
       'mean_correction_status':'NOT_NEEDED','correction_rule':None,'matrix':object_fixture(),
       'full_matrix_unknown':False,'omitted_effects_exhaustive':True,'uncertainty_interpretation':'synthetic centered covariance',
       'sampling_calibration':'NOT_ESTABLISHED','precision_scope':'exact synthetic quantities','unknown_components':[]}
    e.update(updates);return e


def hand_project(V):
    # Independent covariance sums: pair subtraction first, then subtract sapphire.
    D=[[V[2*i][2*j]-V[2*i][2*j+1]-V[2*i+1][2*j]+V[2*i+1][2*j+1] for j in range(4)] for i in range(4)]
    C=[[D[i][j]-D[i][3]-D[3][j]+D[3][3] for j in range(3)] for i in range(3)]
    return tuple(map(tuple,D)),tuple(map(tuple,C))


class PairedBehaviorTests(unittest.TestCase):
    def test_labeled_hand_expansion_and_mean_kernel(self):
        p=protocol();B,R,E,b,A=n.operators(p)
        y=(F(2),F(-3),F(7),F(1),F(-4),F(5),F(11),F(6)) # synthetic only
        d=(y[0]-y[1],y[2]-y[3],y[4]-y[5],y[6]-y[7])
        z=(d[0]-d[3],d[1]-d[3],d[2]-d[3])
        self.assertEqual(tuple(row[0] for row in n.mm(B,[[v] for v in y])),d)
        self.assertEqual(tuple(row[0] for row in n.mm(A,[[v] for v in y])),z)
        for campaign in range(4):
            self.assertEqual(tuple(row[0] for row in n.mm(B,[[r[campaign]] for r in E])),(0,0,0,0))
        self.assertEqual(n.mm(B,b),((1,),(1,),(1,),(1,)))
        self.assertTrue(all(n.algebra_certificate(p)['identities'].values()))
        self.assertEqual((n.rank(B),n.rank(R),n.rank(A)),(4,3,3))
        self.assertEqual(len(n.nullspace(A)),5)
        for vector in n.nullspace(A):
            self.assertEqual(vector[0]-vector[1],vector[2]-vector[3])
            self.assertEqual(vector[2]-vector[3],vector[4]-vector[5])
            self.assertEqual(vector[4]-vector[5],vector[6]-vector[7])

    def test_invertible_contrast_coordinates(self):
        A=n.operators(protocol())[4];T=((1,2,0),(0,1,1),(0,0,-2));TA=n.mm(T,A)
        self.assertNotEqual(n.determinant(T),0)
        self.assertEqual(n.nullspace(A),n.nullspace(TA))
        V=covariance_fixture()
        self.assertEqual(n.project(T,n.project(A,V)),n.project(TA,V))

    def test_order_units_and_covariance_conversion(self):
        p=protocol();o=p['orders']
        self.assertEqual([o['paper_row_major'][i] for i in o['canonical_to_paper']],o['canonical'])
        self.assertEqual(n.covariance_units(((4,1),(1,9)),'1/1000'),((F(4,10**6),F(1,10**6)),(F(1,10**6),F(9,10**6))))
        self.assertEqual([2*x for x in p['units']['torque_MLT']],p['units']['covariance_MLT'])

    def test_all_projection_routes_hand_expanded(self):
        p=protocol();V=covariance_fixture();D,C=hand_project(V)
        fixtures=[object_fixture(),object_fixture('V_d',value=D),object_fixture('direct_C',value=C),object_fixture('J_U',value=V,J=n.eye(8))]
        for obj in fixtures:
            result=n.classify(p,model_fixture(matrix=obj))
            self.assertEqual(result['disposition'],'GO_CONTRAST_UNCERTAINTY')
            self.assertEqual(decoded(result['C']),C)
        self.assertEqual(C,((3,F(9,4),2),(F(9,4),4,2),(2,2,4)))

    def test_same_marginals_different_C(self):
        A=n.operators(protocol())[4];V0=n.eye(8);V1=[list(r) for r in V0];V1[0][1]=V1[1][0]=F(1,2)
        self.assertEqual([V0[i][i] for i in range(8)],[V1[i][i] for i in range(8)])
        self.assertEqual(n.covariance_status(V1),'POSITIVE_DEFINITE')
        self.assertEqual(n.project(A,V0)[0][0]-n.project(A,V1)[0][0],1)

    def test_all_admissible_unknowns_cancel_in_minimum_C(self):
        p=protocol();B,R,E,b,A=n.operators(p);C=((4,2,2),(2,4,2),(2,2,4))
        rows=[unknown('common_method',b),unknown('campaign_common',E)]
        model=model_fixture(matrix=object_fixture('direct_C',value=C),unknown_components=rows,full_matrix_unknown=True)
        result=n.classify(p,model)
        self.assertEqual(result['disposition'],'GO_CONTRAST_UNCERTAINTY')
        self.assertEqual(decoded(result['C']),C)
        self.assertFalse(result['cancelled_unknowns'][0]['B_L_zero'])
        self.assertTrue(result['cancelled_unknowns'][1]['B_L_zero'])
        # Symbolic coefficient of lambda is identically zero. Also cross terms
        # with arbitrary retained loading K vanish without assuming independence.
        self.assertEqual(n.project(A,n.mm(b,n.transpose(b))),((0,0,0),)*3)
        K=tuple((F(i+1),) for i in range(8))
        cross=n.add(n.mm(b,n.transpose(K)),n.mm(K,n.transpose(b)))
        self.assertEqual(n.project(A,cross),((0,0,0),)*3)
        self.assertEqual(n.project(B,n.mm(b,n.transpose(b))),((1,1,1,1),)*4)

    def test_common_correlation_does_not_cancel_unequal_loadings(self):
        p=protocol();A=n.operators(p)[4]
        L=[[1],[0],[2],[0],[3],[0],[4],[0]]
        self.assertFalse(n.annihilates(A,L));self.assertEqual(n.mm(A,L),((-3,),(-2,),(-1,)))
        self.assertEqual(n.classify(p,model_fixture(unknown_components=[unknown(loading=L)]))['disposition'],'NO_GO_CONTRAST_UNCERTAINTY')
        L=[[-2],[2],[-3],[3],[-4],[4],[-5],[5]]
        self.assertEqual(n.mm(n.operators(p)[0],L),((-4,),(-6,),(-8,),(-10,)))
        self.assertGreater(abs(-2-2),max(abs(-2),abs(2)))

    def test_type_a_and_later_stage_never_promoted(self):
        p=protocol()
        self.assertEqual(n.classify(p,model_fixture(matrix=object_fixture(scope='type_a')))['disposition'],'NO_GO_CONTRAST_UNCERTAINTY')
        self.assertEqual(n.classify(p,model_fixture(matrix=object_fixture(stage='final_G_summary')))['disposition'],'NO_GO_CONTRAST_UNCERTAINTY')
        # An exhaustive source-declared omitted component truly eliminated by A
        # makes the Type-A projection sufficient; it is not numerical full-V GO.
        e=model_fixture(matrix=object_fixture(scope='type_a'),unknown_components=[unknown(loading=n.operators(p)[3])])
        self.assertEqual(n.classify(p,e)['disposition'],'GO_CONTRAST_UNCERTAINTY')
        e['unknown_components'].append(unknown('additional_unknown',None))
        self.assertEqual(n.classify(p,e)['disposition'],'NO_GO_CONTRAST_UNCERTAINTY')

    def test_mean_and_uncertainty_meaning(self):
        p=protocol()
        for meaning in ('second_moment','bound','interval'):
            result=n.classify(p,model_fixture(matrix=object_fixture(meaning=meaning)))
            self.assertEqual(result['disposition'],'NO_GO_CONTRAST_UNCERTAINTY');self.assertIsNone(result['C'])
        second=((5,2),(2,2));mean=((2,),(1,));cov=((1,0),(0,1))
        self.assertEqual(n.add(cov,n.mm(mean,n.transpose(mean))),second)
        e=model_fixture(mean_correction_status='UNKNOWN')
        self.assertEqual(n.classify(p,e)['disposition'],'NO_GO_CONTRAST_UNCERTAINTY')
        e['mean_correction_status']='SPECIFIED_NOT_APPLIED'
        with self.assertRaises(n.FeasibilityError):n.classify(p,e)
        e['correction_rule']={'locator':'synthetic source rule','symbolic_rule':'y_star=y-mu','residual_mean_scope':'centered after specified correction'}
        self.assertEqual(n.classify(p,e)['disposition'],'GO_CONTRAST_UNCERTAINTY')
        e['matrix']['meaning']='conservative_uncertainty';e['uncertainty_interpretation']='declared conservative metrological assignment'
        r=n.classify(p,e);self.assertEqual(r['disposition'],'GO_CONTRAST_UNCERTAINTY');self.assertEqual(r['sampling_calibration'],'NOT_ESTABLISHED')

    def test_unknown_dependence_is_not_zero(self):
        e=model_fixture(unknown_components=[unknown('dependence',n.eye(8),'dependence',False)])
        result=n.classify(protocol(),e)
        self.assertIsNone(result['C']);self.assertIn('dependence',result['unresolved_terms'])
        self.assertEqual(result['disposition'],'NO_GO_CONTRAST_UNCERTAINTY')

    def test_dispositions_precedence_and_singular(self):
        p=protocol();e=model_fixture()
        self.assertEqual(n.classify(p,e)['disposition'],'GO_CONTRAST_UNCERTAINTY')
        e['matrix']=object_fixture('direct_C',value=((1,0,0),(0,1,0),(0,0,0)))
        r=n.classify(p,e);self.assertEqual(r['disposition'],'IDENTIFIED_DEGENERATE_CONTRAST');self.assertEqual(r['C_rank'],2)
        self.assertEqual(decoded(r['C_nullspace']),((0,0,1),))
        e['matrix']=None
        self.assertEqual(n.classify(p,e)['disposition'],'NO_GO_CONTRAST_UNCERTAINTY')
        e['candidate_completion_premises']=['synthetic source section X: proposed fixed stage map requires confirmation']
        self.assertEqual(n.classify(p,e)['disposition'],'CONDITIONAL_ASSUMPTIONS_REQUIRED')
        for status in ('unsupported','contradicted'):
            e['comparison_contract']=status;self.assertEqual(n.classify(p,e)['disposition'],'NO_GO_COMPARABILITY')
        e['essential_access_gaps']=['named essential supplement and reason']
        self.assertEqual(n.classify(p,e)['disposition'],'UNRESOLVED_SOURCE_ACCESS')

    def test_exact_PSD_and_source_conflict_vs_code_error(self):
        self.assertEqual(n.covariance_status(((0,0),(0,1))),'POSITIVE_SEMIDEFINITE_SINGULAR')
        self.assertEqual(n.covariance_status(((1,2),(2,1))),'CONFLICTING_SOURCE')
        # All leading determinants are zero but a non-leading principal minor is negative.
        bad=((0,0,0),(0,1,2),(0,2,1));self.assertEqual(n.covariance_status(bad),'CONFLICTING_SOURCE')
        self.assertEqual(n.covariance_status(((F(1,10**60),0),(0,1))),'POSITIVE_DEFINITE')
        p=protocol();obj=object_fixture('direct_C',value=bad)
        with self.assertRaises(n.FeasibilityError):n.classify(p,model_fixture(matrix=obj))
        obj['origin']='published';r=n.classify(p,model_fixture(matrix=obj))
        self.assertEqual(r['combined_contrast_uncertainty'],'CONFLICTING_SOURCE');self.assertEqual(r['disposition'],'NO_GO_CONTRAST_UNCERTAINTY')

    def test_source_projection_consumption_and_context_invariance(self):
        p=protocol();old=n.type_a_projection(p);q=copy.deepcopy(p)
        q['source_projection']['rows'][0]['u_A_nNm']='0.0008';new=n.type_a_projection(q)
        self.assertEqual(value(new['u_A_SI'][0]),2*value(old['u_A_SI'][0]))
        self.assertNotEqual(new['known_diagonal_contribution_not_C'],old['known_diagonal_contribution_not_C'])
        q=copy.deepcopy(p)
        for row in q['source_projection']['rows']:row['reference_nNm']='999'
        q['excluded_context']={'final_G':[99],'dark_uncertainty':123,'published_offsets':[456],'unrelated_artifact':{'Q':777}}
        a=n._json((n.ROOT/n.ATTESTATION).read_bytes());other=copy.deepcopy(a);other['source_projection']=q['source_projection']
        self.assertEqual(n.result_from_inputs(p,a),n.result_from_inputs(q,other))
        self.assertEqual(n.type_a_projection(q),old)

    def test_no_off_diagonal_is_defaulted_and_positive_coefficient(self):
        r=n.type_a_projection(protocol());self.assertIsNone(r['C_type_a']);self.assertEqual(len(r['unresolved_covariance_terms']),28)
        term=next(t for t in r['unresolved_covariance_terms'] if t['indices']==[0,1])
        self.assertEqual(decoded(term['coefficient']),((-2,0,0),(0,0,0),(0,0,0)))
        self.assertTrue(all(t['covariance_SI_squared'] is None for t in r['unresolved_covariance_terms']))

    def test_protocol_fields_rejected_or_consumed(self):
        p=protocol()
        for key in p:
            if key in ('source_projection','excluded_context'):continue
            q=copy.deepcopy(p);q[key]=None
            with self.assertRaises(n.FeasibilityError,msg=key):n.validate_protocol(q)
        for key,v in [('stage','final_G_summary'),('coverage_factor',True),('rows',[]),('reference_role','outcome')]:
            q=copy.deepcopy(p);q['source_projection'][key]=v
            with self.assertRaises(n.FeasibilityError):n.validate_protocol(q)
        q=copy.deepcopy(p);q['source_projection']['rows'].reverse()
        with self.assertRaises(n.FeasibilityError):n.validate_protocol(q)
        p['effect_inventory'][0]['loading']=None
        with self.assertRaises(n.FeasibilityError):n.validate_protocol(p)

    def test_strict_json_numbers_dimensions_and_evidence_errors(self):
        for raw in ('{"x":1,"x":2}','{"x":NaN}','{"x":1e400}','{"x":0.1}'):
            with self.assertRaises(n.FeasibilityError):n._json(raw)
        for number in (True,1.2,'NaN','Infinity','1/0',' 1','1_000',None):
            with self.assertRaises(n.FeasibilityError):n.rational(number)
        for M in ([],[[]],[[1],[1,2]],[[True]]):
            with self.assertRaises(n.FeasibilityError):n.matrix(M)
        self.assertEqual(n.serialize_artifact(n._json('{"z":1,"a":"1/3"}')),'{\n  "a": "1/3",\n  "z": 1\n}\n')
        for updates in ({'comparison_contract':'garbage'},{'full_matrix_unknown':None},{'essential_access_gaps':None},{'comparison_contract':'conditional'}):
            with self.assertRaises(n.FeasibilityError):n.classify(protocol(),model_fixture(**updates))
        for updates in ({'coordinates':'wrong'},{'unit_scale':0},{'value':[[1]]},{'source_authorized':None}):
            with self.assertRaises(n.FeasibilityError):n.classify(protocol(),model_fixture(matrix=object_fixture(**updates)))

    def test_actual_source_boundaries_and_attestation(self):
        p=protocol();a=n._json((n.ROOT/n.ATTESTATION).read_bytes());r=n.result_from_inputs(p,a)
        self.assertEqual(r['identification']['disposition'],'NO_GO_CONTRAST_UNCERTAINTY')
        self.assertEqual(r['identification']['comparison_contract'],'source_described')
        self.assertEqual(r['identification']['mean_correction_status'],'UNKNOWN');self.assertIsNone(r['identification']['C'])
        self.assertEqual(r['identification']['combined_contrast_uncertainty'],'UNIDENTIFIED')
        self.assertEqual(r['type_a_projection']['correction_transfer'],'UNRESOLVED')
        self.assertIn('as-published',r['type_a_projection']['representation'])
        self.assertTrue(all(v is False for v in r['prohibited_action_flags'].values()))
        self.assertTrue(all(row['locator'] and row['supplies'] and row['missing'] and row['smallest_repair'] for row in r['effect_inventory']))
        a['anchor']['created_at']='2000-01-01T00:00:00Z'
        with self.assertRaises(n.FeasibilityError):n.result_from_inputs(p,a)


class PairedArtifactTests(unittest.TestCase):
    def test_artifact_freshness_and_no_writes(self):
        with patch.object(Path,'write_text',side_effect=AssertionError('read-only')),patch.object(Path,'write_bytes',side_effect=AssertionError('read-only')):
            n.check_artifact()
        raw=(n.ROOT/n.OUTPUT).read_bytes();original=Path.read_bytes
        def altered(path):
            return raw+b' ' if path==n.ROOT/n.OUTPUT else original(path)
        with patch.object(Path,'read_bytes',altered),self.assertRaises(n.FeasibilityError):n.check_artifact()

    def test_observed_read_git_and_import_closure(self):
        paths=set();blobs=set();calls=[];bopen=builtins.open;iopen=io.open;oopen=os.open;run=subprocess.run
        def remember(file):
            if isinstance(file,(str,os.PathLike)):
                path=Path(file).resolve()
                if path.is_relative_to(n.ROOT):paths.add(path.relative_to(n.ROOT).as_posix())
        def b(file,*a,**kw):remember(file);return bopen(file,*a,**kw)
        def i(file,*a,**kw):remember(file);return iopen(file,*a,**kw)
        def o(file,*a,**kw):remember(file);return oopen(file,*a,**kw)
        def r(cmd,*a,**kw):
            calls.append(cmd)
            for arg in cmd:
                if ':' in str(arg) and str(arg).split(':',1)[1].startswith(('Discovery/','Experiments/','Notes/')):blobs.add(str(arg).split(':',1)[1])
            return run(cmd,*a,**kw)
        with patch('builtins.open',b),patch('io.open',i),patch('os.open',o),patch('subprocess.run',r):n.build_artifact()
        self.assertEqual(paths,set(n.SOURCE_PATHS));self.assertEqual(blobs,set(n.SOURCE_PATHS))
        self.assertTrue(calls);self.assertTrue(all(c[0]=='git' for c in calls))
        # Path-limited Git scans are observed as well as blob reads.
        for cmd in calls:
            if '--' in cmd:
                self.assertLessEqual(set(cmd[cmd.index('--')+1:]),set(n.SOURCE_PATHS)|{'Discovery/'+n.STEM+'_mutations.py','tests/test_'+n.STEM+'.py','tests/test_'+n.STEM+'_mutations.py'})
        seen=set();queue=[n.MODULE]
        while queue:
            path=queue.pop()
            if path in seen:continue
            seen.add(path)
            for node in ast.walk(ast.parse((n.ROOT/path).read_text())):
                if isinstance(node,ast.ImportFrom) and node.module and node.module.startswith('Discovery.'):
                    queue.append(node.module.replace('.','/')+'.py')
                if isinstance(node,ast.Import):
                    queue.extend(a.name.replace('.','/')+'.py' for a in node.names if a.name.startswith('Discovery.'))
        self.assertEqual(seen,{n.MODULE,*n.HELPERS})
        self.assertFalse(any(isinstance(node,ast.FunctionDef) and any(t in node.name for t in ('fit_tau','observed_difference','statistic','p_value')) for node in ast.walk(ast.parse((n.ROOT/n.MODULE).read_text()))))

    def test_freeze_sole_file_anchor_and_introductions(self):
        n.verify_preregistration();intro=n.verify_implementation_chronology()
        self.assertEqual(n.git(n.ROOT,'diff','--name-only',n.BASE,n.FREEZE).decode().splitlines(),[n.PREREGISTRATION_PATH.as_posix()])
        self.assertEqual(len(intro),4)

    def test_early_anchor_rejected(self):
        with patch.dict(n.ANCHOR,created_at='2099-01-01T00:00:00Z'),self.assertRaises(n.FeasibilityError):n.verify_implementation_chronology()

    def test_source_snapshot_inherited_and_changed_merge(self):
        with TemporaryDirectory() as temp:
            root=Path(temp)
            def git(*args):return subprocess.run(['git','-C',str(root),*args],check=True,capture_output=True).stdout.decode().strip()
            git('init');git('config','user.name','Test');git('config','user.email','test@example.invalid')
            (root/'base').write_text('base');git('add','.');git('commit','-m','base');base=git('rev-parse','HEAD')
            git('checkout','-b','feature');(root/'source').write_text('source');git('add','.');git('commit','-m','source');source=git('rev-parse','HEAD')
            git('checkout','-b','integration',base);(root/'other').write_text('other');git('add','.');git('commit','-m','other')
            git('merge','--no-ff','feature','-m','merge')
            self.assertEqual(n.source_snapshot(root,('source',))['source_commit_sha'],source)
            (root/'source').write_text('resolved');git('add','.');tree=git('write-tree')
            merged=git('commit-tree',tree,'-p',base,'-p',source,'-m','resolution');git('update-ref','HEAD',merged)
            self.assertEqual(n.source_snapshot(root,('source',))['source_commit_sha'],merged)
            (root/'source').write_text('uncommitted')
            with self.assertRaises(n.SourceVerificationError):n.source_snapshot(root,('source',))

    def test_full_history_rejects_changed_then_reverted_freeze(self):
        with TemporaryDirectory() as temp:
            root=Path(temp)
            def git(*args):return subprocess.run(['git','-C',str(root),*args],check=True,capture_output=True).stdout.decode().strip()
            git('init');git('config','user.name','Test');git('config','user.email','test@example.invalid')
            (root/'base').write_text('base');git('add','.');git('commit','-m','base');base=git('rev-parse','HEAD')
            (root/'freeze.json').write_text('{}');git('add','.');git('commit','-m','freeze');freeze=git('rev-parse','HEAD')
            n.verify_preregistration_freeze(root,baseline=base,commit=freeze,path='freeze.json',sha256=n.digest(b'{}'))
            git('checkout','-b','side');(root/'freeze.json').write_text('{"x":1}');git('add','.');git('commit','-m','change')
            (root/'freeze.json').write_text('{}');git('add','.');git('commit','-m','revert')
            side=git('rev-parse','HEAD');git('checkout','-b','join',freeze);git('merge','--no-ff',side,'-m','merge reverted side')
            with self.assertRaises(n.SourceVerificationError):n.verify_preregistration_freeze(root,baseline=base,commit=freeze,path='freeze.json',sha256=n.digest(b'{}'))
