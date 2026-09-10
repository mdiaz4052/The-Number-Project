"""NIST campaign contrasts: exact uncertainty feasibility, without observed contrasts."""
from __future__ import annotations

import argparse
import copy
from datetime import datetime
from fractions import Fraction as F
import hashlib
import json
import re
from itertools import combinations
from pathlib import Path
import subprocess
import sys

from Discovery.preregistration_history import verify_preregistration_freeze
from Discovery.source_history import verify_committed_source_state, SourceVerificationError

ROOT = Path(__file__).resolve().parents[1]
STEM = 'nist_2026_paired_torque_feasibility'
DIRECTORY = Path('Experiments/GMeasurements')
PREREGISTRATION_PATH = DIRECTORY / (STEM + '_preregistration_v1.json')
ATTESTATION = DIRECTORY / (STEM + '_source_attestation_v1.json')
OUTPUT = DIRECTORY / (STEM + '_v1.json')
MODULE = 'Discovery/' + STEM + '.py'
HELPERS = ('Discovery/preregistration_history.py', 'Discovery/source_history.py')
NOTES = ('Notes/NIST2026PairedTorqueFeasibilitySpecification.md', 'Notes/NIST2026PairedTorqueFeasibility.md', 'Notes/NIST2026PairedTorqueSourceRequest.md')
BASE = '6f722e92a09bc598aa06920e89ba02059bf1e7a4'
FREEZE = '5e104cd4a070167e2354619d473043f2528f169b'
FREEZE_DIGEST = '88be1281c71e2ec952bd9d1f7bf2f88def4a0b3f9d57c3dfe170c4b62225622c'
ANCHOR = {'pr_number': 51, 'created_at': '2026-09-10T13:31:25Z', 'head_sha_at_creation': FREEZE,
          'url': 'https://github.com/mdiaz4052/The-Number-Project/pull/51', 'provider': 'GitHub'}
# The nonnumeric contract is supported exactly; changed policy must fail, not go unused.
SUPPORTED_POLICY_DIGEST = 'ebcc8a39946f969871397f23cca1583494b2df3335112986c1b1898076dc5260'
SOURCE_PATHS = (MODULE, *HELPERS, *NOTES, PREREGISTRATION_PATH.as_posix(), ATTESTATION.as_posix())


class FeasibilityError(ValueError):
    """A contract/evidence error is never a scientific NO-GO."""


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def serialize_artifact(value):
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True, allow_nan=False) + '\n'


def _json(raw):
    def pairs(items):
        result = {}
        for k, v in items:
            if k in result:
                raise FeasibilityError('duplicate JSON key: ' + k)
            result[k] = v
        return result
    def invalid(value):
        raise FeasibilityError('nonfinite JSON: ' + value)
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid, parse_float=invalid)


def rational(value):
    if isinstance(value, bool) or isinstance(value, float) or not isinstance(value, (str, int, F)):
        raise FeasibilityError('finite exact rational input required')
    if isinstance(value, str) and not re.fullmatch(r'[+-]?(?:[0-9]+(?:/[1-9][0-9]*|\.[0-9]+)?|\.[0-9]+)', value):
        raise FeasibilityError('canonical decimal or rational string required')
    try:
        return F(value)
    except (ValueError, ZeroDivisionError) as error:
        raise FeasibilityError('invalid finite rational input') from error


def record(value):
    value = rational(value)
    return {'numerator': value.numerator, 'denominator': value.denominator}


def records(values):
    return [record(v) for v in values]


def validate_protocol(p):
    if not isinstance(p, dict):
        raise FeasibilityError('protocol object required')
    fixed = {k:v for k,v in p.items() if k not in ('source_projection', 'excluded_context')}
    if digest(serialize_artifact(fixed).encode()) != SUPPORTED_POLICY_DIGEST:
        raise FeasibilityError('unsupported or missing frozen policy/source field')
    s = p.get('source_projection')
    if not isinstance(s, dict) or set(s) != {'stage','locator','coverage_factor','uncertainty_scope','reference_role','rows'}:
        raise FeasibilityError('source projection schema differs')
    if (s['stage'] != 'table15_campaign_torque' or s['locator'] != 'S1 p.25 Table 15'
        or type(s['coverage_factor']) is not int or s['coverage_factor'] != 1
        or s['uncertainty_scope'] != 'type_a_marginals_only'
        or s['reference_role'] != 'transcription_context_only_not_used_for_uncertainty_or_verdict'
        or not isinstance(s['rows'], list) or len(s['rows']) != 8):
        raise FeasibilityError('input stage, scope or roles differ')
    for row, label in zip(s['rows'], p['orders']['canonical']):
        if set(row) != {'label','reference_nNm','u_A_nNm'} or row['label'] != label:
            raise FeasibilityError('input order or fields differ')
        if any(not isinstance(row[k],str) or rational(row[k]) <= 0 for k in ('reference_nNm','u_A_nNm')):
            raise FeasibilityError('reported positive decimal strings required')
    return p


def matrix(M, rows=None, cols=None):
    if not isinstance(M, (list,tuple)) or not M or not isinstance(M[0],(list,tuple)) or not M[0]:
        raise FeasibilityError('nonempty matrix required')
    width=len(M[0])
    if any(not isinstance(r,(list,tuple)) or len(r)!=width for r in M):
        raise FeasibilityError('rectangular matrix required')
    if (rows is not None and len(M)!=rows) or (cols is not None and width!=cols):
        raise FeasibilityError('matrix shape differs')
    return tuple(tuple(rational(v) for v in row) for row in M)


def transpose(M):
    return tuple(zip(*matrix(M)))


def mm(X,Y):
    X,Y=matrix(X),matrix(Y)
    if len(X[0]) != len(Y):
        raise FeasibilityError('matrix product dimensions differ')
    return tuple(tuple(sum((a*b for a,b in zip(row,col)),F(0)) for col in transpose(Y)) for row in X)


def eye(n):
    return tuple(tuple(F(i==j) for j in range(n)) for i in range(n))


def scale_matrix(M, scale):
    return tuple(tuple(v*rational(scale) for v in row) for row in matrix(M))


def add(X,Y):
    X,Y=matrix(X),matrix(Y)
    if (len(X),len(X[0])) != (len(Y),len(Y[0])):
        raise FeasibilityError('matrix sum dimensions differ')
    return tuple(tuple(a+b for a,b in zip(x,y)) for x,y in zip(X,Y))


def rref(M):
    M=[list(row) for row in matrix(M)]; pivots=[];r=0
    for c in range(len(M[0])):
        pivot=next((i for i in range(r,len(M)) if M[i][c]),None)
        if pivot is None: continue
        M[r],M[pivot]=M[pivot],M[r];f=M[r][c];M[r]=[v/f for v in M[r]]
        for i in range(len(M)):
            if i!=r:
                f=M[i][c];M[i]=[a-f*b for a,b in zip(M[i],M[r])]
        pivots.append(c);r+=1
        if r==len(M):break
    return tuple(tuple(row) for row in M),tuple(pivots)


def rank(M):
    return len(rref(M)[1])


def nullspace(M):
    reduced,pivots=rref(M);width=len(reduced[0]);out=[]
    for free in range(width):
        if free in pivots:continue
        v=[F(0)]*width;v[free]=F(1)
        for i,c in enumerate(pivots):v[c]=-reduced[i][free]
        out.append(tuple(v))
    return tuple(out)


def determinant(M):
    M=[list(row) for row in matrix(M)];n=len(M)
    if len(M[0])!=n:raise FeasibilityError('square matrix required')
    result=F(1)
    for c in range(n):
        pivot=next((i for i in range(c,n) if M[i][c]),None)
        if pivot is None:return F(0)
        if pivot!=c:M[c],M[pivot]=M[pivot],M[c];result=-result
        p=M[c][c];result*=p
        for i in range(c+1,n):
            f=M[i][c]/p
            for j in range(c+1,n):M[i][j]-=f*M[c][j]
    return result


def covariance_status(V):
    V=matrix(V);n=len(V)
    if len(V[0])!=n:raise FeasibilityError('square covariance required')
    if V!=transpose(V):return 'CONFLICTING_SOURCE'
    # All principal minors, not just the leading minors, characterize PSD.
    for size in range(1,n+1):
        for indexes in combinations(range(n),size):
            if determinant(tuple(tuple(V[i][j] for j in indexes) for i in indexes))<0:
                return 'CONFLICTING_SOURCE'
    return 'POSITIVE_DEFINITE' if rank(V)==n else 'POSITIVE_SEMIDEFINITE_SINGULAR'


def operators(p):
    B=[list(row) for row in matrix(p['operators']['B'],4,8)]
    B[0][1] = F(-1)
    B=matrix(B);R=matrix(p['operators']['R'],3,4);E=matrix(p['operators']['E'],8,4)
    b=matrix([[v] for v in p['operators']['b']],8,1)
    return B,R,E,b,mm(R,B)


def project(P,V):
    return mm(mm(P, V), transpose(P))


def covariance_units(V, scale):
    if rational(scale)<=0:raise FeasibilityError('positive unit scale required')
    factor = rational(scale) ** 2
    return scale_matrix(V,factor)


def annihilates(A,L):
    L=matrix(L,8);image=mm(A,L)
    return all(v == 0 for row in image for v in row)


def matrix_record(M):
    return [[record(v) for v in row] for row in M]


def algebra_certificate(p):
    B,R,E,b,A=operators(p);D=tuple(tuple(row)+tuple(v) for row,v in zip(E,b));one=matrix([[1]]*4)
    identities={'B_E_zero':not any(v for row in mm(B,E) for v in row),'B_b_one':mm(B,b)==one,
                'R_one_zero':not any(v for row in mm(R,one) for v in row),
                'A_E_zero':not any(v for row in mm(A,E) for v in row),'A_b_zero':not any(v for row in mm(A,b) for v in row),
                'rank_B_four':rank(B)==4,'rank_R_three':rank(R)==3,'rank_A_three':rank(A)==3,'rank_Eb_five':rank(D)==5}
    if not all(identities.values()):raise FeasibilityError('failed exact contrast algebra')
    return {'operators':{k:matrix_record(M) for k,M in [('B',B),('R',R),('E',E),('b',b),('A',A)]},
            'identities':identities,'ker_A_equals_col_Eb':True,'kernel_basis_rows':matrix_record(nullspace(A)),
            'kernel_proof':'A[E,b]=0 and rank([E,b])=5=8-rank(A); exact inclusion and equal dimensions.',
            'coordinate_invariance':'For invertible T, ker(T A)=ker(A); covariance transforms as T C T^T.'}


MODEL_KEYS={'comparison_contract','comparison_detail','comparison_locator','essential_access_gaps','candidate_completion_premises',
            'mean_correction_status','correction_rule','matrix','full_matrix_unknown','omitted_effects_exhaustive',
            'uncertainty_interpretation','sampling_calibration','precision_scope','unknown_components'}
OBJECT_KEYS={'route','value','J','unit_scale','coordinates','stage','scope','meaning','source_authorized','locator','origin'}
UNKNOWN_KEYS={'id','kind','loading','locator','missing','non_type_a'}


def validate_model(model):
    if not isinstance(model,dict) or set(model)!=MODEL_KEYS:raise FeasibilityError('uncertainty model fields differ')
    if model['comparison_contract'] not in ('source_described','conditional','unsupported','contradicted','unresolved_access'):
        raise FeasibilityError('unknown comparison status')
    if model['mean_correction_status'] not in ('APPLIED_AT_THIS_STAGE','SPECIFIED_NOT_APPLIED','NOT_NEEDED','UNKNOWN','CONTRADICTED'):
        raise FeasibilityError('unknown correction status')
    for k in ('full_matrix_unknown','omitted_effects_exhaustive'):
        if type(model[k]) is not bool:raise FeasibilityError('explicit boolean required: '+k)
    for k in ('comparison_detail','comparison_locator','uncertainty_interpretation','sampling_calibration','precision_scope'):
        if not isinstance(model[k],str) or not model[k]:raise FeasibilityError('explicit source/meaning field required: '+k)
    for k in ('essential_access_gaps','candidate_completion_premises'):
        if not isinstance(model[k],list) or any(not isinstance(v,str) or not v for v in model[k]):
            raise FeasibilityError('explicit source-linked list required')
    if model['comparison_contract']=='conditional' and not model['candidate_completion_premises']:
        raise FeasibilityError('conditional comparison needs bounded source-linked premises')
    if model['comparison_contract']=='unresolved_access' and not model['essential_access_gaps']:
        raise FeasibilityError('access disposition requires named essential source')
    rule=model['correction_rule']
    if rule is not None and (not isinstance(rule,dict) or set(rule)!={'locator','symbolic_rule','residual_mean_scope'}
        or any(not isinstance(v,str) or not v for v in rule.values())):
        raise FeasibilityError('specified correction requires source rule and residual mean scope')
    if model['mean_correction_status']=='SPECIFIED_NOT_APPLIED' and rule is None:
        raise FeasibilityError('pending correction requires a rule; no actual outcomes are transformed')
    unknown=model['unknown_components']
    if not isinstance(unknown,list):raise FeasibilityError('finite complete unknown list required')
    ids=set()
    for row in unknown:
        if not isinstance(row,dict) or set(row)!=UNKNOWN_KEYS or not row['id'] or row['id'] in ids:
            raise FeasibilityError('unknown effect schema/identity differs')
        ids.add(row['id'])
        if row['kind'] not in ('dependence','uncertainty','mean') or type(row['non_type_a']) is not bool:
            raise FeasibilityError('unknown effect kind differs')
        if not row['locator'] or not row['missing']:raise FeasibilityError('unknown term needs positive source locator and gap')
        if row['loading'] is not None:matrix(row['loading'],8)
    obj=model['matrix']
    if obj is not None:
        if not isinstance(obj,dict) or set(obj)!=OBJECT_KEYS:raise FeasibilityError('matrix evidence fields differ')
        if obj['route'] not in ('direct_C','V_d','V_y','J_U') or obj['scope'] not in ('type_a','combined'):
            raise FeasibilityError('matrix route or scope differs')
        if obj['stage'] not in ('campaign_torque','final_G_summary') or obj['origin'] not in ('published','code'):
            raise FeasibilityError('matrix stage/origin differs')
        if obj['meaning'] not in ('centered_covariance','conservative_uncertainty','second_moment','bound','interval'):
            raise FeasibilityError('uncertainty meaning differs')
        if type(obj['source_authorized']) is not bool or not obj['locator']:raise FeasibilityError('explicit source authority required')
        expected={'direct_C':'z','V_d':'d','V_y':'y','J_U':'inputs'}[obj['route']]
        if obj['coordinates']!=expected:raise FeasibilityError('matrix coordinates differ')
        value=matrix(obj['value']);size={'direct_C':3,'V_d':4,'V_y':8}.get(obj['route'],len(value))
        matrix(value,size,size)
        if obj['route']=='J_U':matrix(obj['J'],8,size)
        elif obj['J'] is not None:raise FeasibilityError('J belongs only to input-model route')
        if rational(obj['unit_scale'])<=0:raise FeasibilityError('positive unit conversion required')
    return model


def project_object(p,obj):
    B,R,E,b,A=operators(p);V=matrix(obj['value']);status=covariance_status(V)
    if status=='CONFLICTING_SOURCE':
        if obj['origin']=='code':raise FeasibilityError('invalid code-produced uncertainty matrix')
        return None,status
    P={'direct_C':eye(3),'V_d':R,'V_y':A}.get(obj['route'])
    if obj['route']=='J_U':P=mm(A,matrix(obj['J']))
    C=covariance_units(project(P,V),obj['unit_scale'])
    status=covariance_status(C)
    if status=='CONFLICTING_SOURCE':raise FeasibilityError('exact projection produced invalid covariance')
    return C,status


def classify(p,model):
    validate_model(model);B,R,E,b,A=operators(p);obj=model['matrix'];unresolved=[];cancelled=[]
    for row in model['unknown_components']:
        if row['loading'] is not None and annihilates(A,row['loading']):
            cancelled.append({'id':row['id'],'A_L_zero':True,'B_L_zero':not any(v for rr in mm(B,row['loading']) for v in rr),
                              'all_admissible':'All variances and cross-covariances on this frozen loading span drop out.'})
        else:
            unresolved.append(row["id"])
    C=None;status='UNIDENTIFIED';reasons=[]
    if obj is not None:
        candidate,status=project_object(p,obj)
        # A Type-A-only object can cover the target when every omitted effect
        # in an explicitly exhaustive inventory is eliminated in contrast space.
        omitted=[r for r in model['unknown_components'] if r['non_type_a']]
        omitted_complete=(model['omitted_effects_exhaustive'] and bool(omitted)
                          and all(r['id'] in {c['id'] for c in cancelled} for r in omitted))
        coverage_ok = obj["scope"] == "combined" or omitted_complete
        meaning_ok=obj['meaning'] in ('centered_covariance','conservative_uncertainty')
        stage_ok=obj['stage']=='campaign_torque' and obj['source_authorized']
        if not coverage_ok:reasons.append('TYPE_A_IS_NOT_COMBINED_COVERAGE')
        if not meaning_ok:reasons.append('UNCERTAINTY_MEANING_NOT_AUTHORIZED_AS_C')
        if not stage_ok:reasons.append('NO_CAMPAIGN_STAGE_AUTHORITY')
        if candidate is not None and coverage_ok and meaning_ok and stage_ok:C=candidate
    else:
        reasons.append('NO_SOURCE_SUPPLIED_JOINT_OBJECT')
    mean_ok = model["mean_correction_status"] in ("APPLIED_AT_THIS_STAGE", "SPECIFIED_NOT_APPLIED", "NOT_NEEDED")
    if not mean_ok:reasons.append('UNRESOLVED_MEAN_CORRECTION_CONTRACT')
    if unresolved:
        C=None;reasons.append('NONCANCELING_OR_UNKNOWN_LOADING_TERMS')
    if not model['omitted_effects_exhaustive']:
        C=None;reasons.append('INCOMPLETE_EFFECT_COVERAGE')
    if C is None and status!='CONFLICTING_SOURCE':status='PARTIALLY_IDENTIFIED' if obj is not None else 'UNIDENTIFIED'
    if model['essential_access_gaps']:
        disposition='UNRESOLVED_SOURCE_ACCESS'
    elif model['comparison_contract'] in ('unsupported','contradicted'):
        disposition='NO_GO_COMPARABILITY'
    elif model['candidate_completion_premises']:
        disposition='CONDITIONAL_ASSUMPTIONS_REQUIRED'
    elif C is None or not mean_ok:
        disposition='NO_GO_CONTRAST_UNCERTAINTY'
    elif rank(C)<3:
        disposition='IDENTIFIED_DEGENERATE_CONTRAST'
    else:
        disposition='GO_CONTRAST_UNCERTAINTY'
    if disposition not in p['decision_policy']['precedence']:raise FeasibilityError('unsupported decision policy')
    return {'disposition':disposition,'comparison_contract':model['comparison_contract'],
            'comparison_detail':model['comparison_detail'],'combined_contrast_uncertainty':status,
            'mean_correction_status':model['mean_correction_status'],'uncertainty_interpretation':model['uncertainty_interpretation'],
            'precision_scope':model['precision_scope'],'sampling_calibration':model['sampling_calibration'],
            'C':matrix_record(C) if C is not None else None,'C_rank':rank(C) if C is not None else None,
            'C_nullspace':matrix_record(nullspace(C)) if C is not None else None,
            'cancelled_unknowns':cancelled,'unresolved_terms':unresolved,'limitations':reasons,
            'essential_access_gaps':model['essential_access_gaps'],'additional_premises':model['candidate_completion_premises']}


def type_a_projection(p):
    """Known marginal contribution plus ALL unspecified off-diagonal coefficients.

    This is a partial matrix expression, never an independence completion.
    No torque reference value is accessed here.
    """
    validate_protocol(p);A=operators(p)[4];scale=rational(p['units']['nNm_to_Nm'])
    marginals=[rational(row['u_A_nNm'])*scale for row in p['source_projection']['rows']]
    diagonal=tuple(tuple(u*u if i==j else F(0) for j in range(8)) for i,u in enumerate(marginals))
    terms=[]
    for i in range(8):
        for j in range(i+1,8):
            coefficient=tuple(tuple(A[r][i]*A[s][j]+A[r][j]*A[s][i] for s in range(3)) for r in range(3))
            if any(v for row in coefficient for v in row):
                terms.append({'indices':[i,j],'labels':[p['orders']['canonical'][i],p['orders']['canonical'][j]],
                              'covariance_SI_squared':None,'coefficient':matrix_record(coefficient)})
    return {'scope':'TYPE_A_PARTIAL_EXPRESSION_NOT_A_COVARIANCE_COMPLETION',
            'representation':'as-published Table 15 y; not an authorized contribution to corrected y_star without a stage map',
            'correction_transfer':'UNRESOLVED',
            'permitted_uncertainty_projection':{'stage':p['source_projection']['stage'],'units':p['units'],
                'rows':[{'label':r['label'],'u_A_nNm':r['u_A_nNm']} for r in p['source_projection']['rows']],
                'torque_reference_role':'context only; no reference values consumed by uncertainty propagation'},
            'u_A_SI':records(marginals),
            'known_diagonal_contribution_not_C':matrix_record(project(A,diagonal)),
            'unresolved_covariance_terms':terms,'C_type_a':None,
            'equation':'C_A = known_diagonal_contribution + sum_{i<j} Cov_A(y_i,y_j) coefficient_ij; all off-diagonal quantities remain unknown.',
            'interpretation':'Marginal standard uncertainties at k=1; evaluation type does not imply independence or a sampling law.'}


def source_model(p):
    model=copy.deepcopy(p['source_contract']);unknown=[]
    for row in p['effect_inventory']:
        if row['stage']=='G_conversion_only':continue
        unknown.append({'id':row['id'],'kind':'dependence' if row['id']=='type_a' else 'uncertainty',
                        'loading':row['loading'],'locator':row['locator'],'missing':row['missing'],
                        'non_type_a':row['id']!='type_a'})
    model['unknown_components']=unknown
    return model


def synthetic_certificate(p):
    A=operators(p)[4];B,R,E,b,_=operators(p)
    V0=eye(8);V1=[list(row) for row in V0];V1[0][1]=V1[1][0]=F(1,2);V1=matrix(V1)
    unequal=matrix([[v] for v in p['synthetic_fixtures']['unequal_shared_loading']])
    differential=matrix([[v] for v in p['synthetic_fixtures']['larger_differential_loading']])
    return {'synthetic_only':True,'same_marginals':True,'V0_status':covariance_status(V0),'V1_status':covariance_status(V1),
            'C0':matrix_record(project(A,V0)),'C1':matrix_record(project(A,V1)),
            'same_marginals_different_C':project(A,V0)!=project(A,V1),
            'unknown_lambda_b_bT':{'A_b_zero':annihilates(A,b),'B_b_nonzero':any(v for row in mm(B,b) for v in row),
                                 'proof':'A b=0 implies A(I+lambda b b^T)A^T=A A^T for every lambda>=0; no sampling of completions.'},
            'unknown_col_E':{'A_E_zero':annihilates(A,E),'B_E_zero':not any(v for row in mm(B,E) for v in row)},
            'unequal_shared_loading_A_L':matrix_record(mm(A,unequal)),
            'larger_differential_loading_B_L':matrix_record(mm(B,differential)),
            'scope':'Generic exact vulnerability and cancellation controls, not fitted or inferred NIST covariances or source-specific completion witnesses.'}


def result_from_inputs(p,attestation):
    validate_protocol(p)
    if (not isinstance(attestation,dict) or set(attestation)!={'schema_version','review_qualification','anchor','freeze_sha256','corpus','source_projection','effect_inventory','source_contract','attribution'}
        or attestation['anchor']!=ANCHOR or attestation['freeze_sha256']!=FREEZE_DIGEST
        or attestation['schema_version']!=p['schema_version'] or attestation['review_qualification']!=p['review_qualification']):
        raise FeasibilityError('source attestation/anchor differs')
    for key in ('corpus','source_projection','effect_inventory','source_contract'):
        if attestation[key]!=p[key]:raise FeasibilityError('post-freeze attestation changed frozen facts: '+key)
    uncertainty=type_a_projection(p);identification=classify(p,source_model(p))
    identification['type_a_uncertainty']='MISSING_DEPENDENCE' if uncertainty['unresolved_covariance_terms'] else 'IDENTIFIED_PROJECTED_CONTRIBUTION'
    return {'identification':identification,'algebra':algebra_certificate(p),'type_a_projection':uncertainty,
            'effect_inventory':p['effect_inventory'],'synthetic_certificate':synthetic_certificate(p),
            'source_requests':[{'effect':r['id'],'locator':r['locator'],'request':r['smallest_repair']} for r in p['effect_inventory'] if r['stage']!='G_conversion_only'],
            'review_qualification':p['review_qualification'],'prohibited_action_flags':p['decision_policy']['flags']}


def git(root, *args):
    completed = subprocess.run(['git', '-C', str(root), *args], capture_output=True, check=True)
    return completed.stdout


def verify_preregistration(root=ROOT):
    raw = verify_preregistration_freeze(root, baseline=BASE, commit=FREEZE,
                                       path=PREREGISTRATION_PATH.as_posix(), sha256=FREEZE_DIGEST)
    p = _json(raw)
    validate_protocol(p)
    return p


def verify_implementation_chronology(root=ROOT, paths=None):
    # Full-history path additions are candidates; first-introduction predicates
    # are checked against all parents. --full-history avoids path simplification.
    found = {}
    for path in (paths if paths is not None else (MODULE, ATTESTATION.as_posix(), NOTES[1], NOTES[2])):
        candidates = git(root, 'log', '--full-history', '--diff-filter=A', '--format=%H', '--', path).decode().splitlines()
        true_additions = []
        for sha in dict.fromkeys(candidates):
            parents = git(root, 'rev-list', '--parents', '-n', '1', sha).decode().split()[1:]
            if not any(subprocess.run(['git', '-C', str(root), 'cat-file', '-e', parent + ':' + path], capture_output=True).returncode == 0 for parent in parents):
                true_additions.append(sha)
        if len(true_additions) != 1:
            raise FeasibilityError('unique full-history first introduction required: ' + path)
        sha = true_additions[0]
        git(root, 'merge-base', '--is-ancestor', FREEZE, sha)
        dates = git(root, 'show', '-s', '--format=%aI%n%cI', sha).decode().splitlines()
        if any(datetime.fromisoformat(t) <= datetime.fromisoformat(ANCHOR['created_at'].replace('Z', '+00:00')) for t in dates):
            raise FeasibilityError('implementation introduction predates draft anchor')
        found[path] = sha
    freeze_time = git(root, 'show', '-s', '--format=%cI', FREEZE).decode().strip()
    if datetime.fromisoformat(freeze_time) > datetime.fromisoformat(ANCHOR['created_at'].replace('Z', '+00:00')):
        raise FeasibilityError('freeze postdates draft anchor')
    return found


def source_snapshot(root, paths=SOURCE_PATHS):
    # Full-history candidates include synthetic/true merges. A commit inheriting
    # the complete relevant state from any parent is not a new source snapshot.
    # A conflict resolution that changes that state against every parent remains
    # a genuine source change and must receive freshly emitted artifacts.
    candidates = git(root, 'log', '--full-history', '--format=%H', '--', *paths).decode().splitlines()
    sha = None
    for candidate in candidates:
        parents = git(root, 'rev-list', '--parents', '-n', '1', candidate).decode().split()[1:]
        inherited = False
        for parent in parents:
            diff = subprocess.run(['git', '-C', str(root), 'diff', '--quiet', parent, candidate, '--', *paths], capture_output=True)
            if diff.returncode not in (0, 1):
                raise FeasibilityError('source-state parent comparison failed')
            if diff.returncode == 0:
                inherited = True
                break
        if not inherited:
            sha = candidate
            break
    if sha is None:
        raise FeasibilityError('no result-driving source introduction found')
    verify_committed_source_state(root, sha, source_paths=paths, artifact_label=STEM)
    hashes = {}
    for path in paths:
        raw = (root / path).read_bytes()
        if raw != git(root, 'show', sha + ':' + path):
            raise FeasibilityError('source blob/current bytes differ: ' + path)
        hashes[path] = digest(raw)
    return {'source_commit_sha': sha, 'source_sha256': hashes}


def build_artifact(root=ROOT):
    p=verify_preregistration(root);chronology=verify_implementation_chronology(root);snapshot=source_snapshot(root)
    for path in HELPERS:
        if snapshot['source_sha256'][path]!=p['dependencies']['code_reuse'][path]:raise FeasibilityError('helper pin differs')
    attestation=_json((root/ATTESTATION).read_bytes());result=result_from_inputs(p,attestation)
    return {'schema_version':p['schema_version'],'experiment_id':p['experiment_id'],'objective':p['objective'],
            'outcome_blind':p['outcome_blind'],'prior_knowledge':p['prior_knowledge'],'corpus':p['corpus'],
            'provenance':{'base':BASE,'freeze_commit':FREEZE,'freeze_sha256':FREEZE_DIGEST,'anchor':ANCHOR,
                          'first_introductions':chronology,**snapshot},
            'read_roles':{'scientific':[PREREGISTRATION_PATH.as_posix(),ATTESTATION.as_posix()],
                          'provenance':[MODULE,*HELPERS,*NOTES]},
            'dependencies':p['dependencies'],'validation_contract':{k:p[k] for k in ('planned_surfaces','focused_requirements','mutation_requirements','acceptance_criteria')},
            'decision_policy':p['decision_policy'],'mean_contract':p['mean_contract'],'uncertainty_policy':p['uncertainty_policy'],**result}


def check_artifact(root=ROOT):
    expected=build_artifact(root);raw=(root/OUTPUT).read_bytes()
    if _json(raw)!=expected or raw!=serialize_artifact(expected).encode():raise FeasibilityError('stale or noncanonical feasibility artifact')
    source=expected['provenance']['source_commit_sha']
    artifact_commit=source_snapshot(root,(OUTPUT.as_posix(),))['source_commit_sha']
    if source==artifact_commit:raise FeasibilityError('artifact must follow committed source snapshot')
    git(root,'merge-base','--is-ancestor',source,artifact_commit)
    return expected


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');args=parser.parse_args(argv)
    try:
        if args.check:
            result=check_artifact();print('NIST paired-torque feasibility verified: '+result['identification']['disposition'])
        else:
            (ROOT/OUTPUT).write_text(serialize_artifact(build_artifact()))
    except (FeasibilityError,SourceVerificationError,OSError,KeyError,TypeError,ValueError,subprocess.SubprocessError) as error:
        print('paired_torque_contract_error: '+str(error),file=sys.stderr);raise SystemExit(1) from error


if __name__=='__main__':
    main()
