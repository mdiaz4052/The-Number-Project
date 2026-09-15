"""Post-seal, known-truth Suite 1 evaluation; no discovery or coefficient refit."""
import math
from Discovery.symbolic_benchmark_engine import class_id, signature, rmse, EVIDENCE


def pair_diagnostic(rows, multiplier, tolerance):
    if not rows or len(rows)%2: return False
    return all(a['features']==b['features'] and a['group']=='g0' and b['group']=='g1' and
        abs(b['target']/a['target']-multiplier)<=tolerance for a,b in zip(rows[::2],rows[1::2]))


def candidate_metrics(candidate, rows, truth, policy):
    error=rmse(candidate['representative'],candidate['log_coefficient'],rows)
    correct=truth['in_family'] and candidate['class_id']==class_id(signature(truth['base_signature']))
    nuisance=sorted(set(candidate['expanded']) & set(truth['irrelevant_atoms']))
    leaked=any(set(m)&set(truth['forbidden_features']) for m in candidate['members']) or 'y' in candidate['expanded']
    direct=signature(candidate['representative'])==signature(truth['base_signature'])
    valid_approx=candidate['validation_rmse']<=policy['approximation_rmse_max']
    held_approx=error<=policy['approximation_rmse_max']
    classification=('leakage_contaminated' if leaked else 'nuisance_contaminated' if nuisance else
        ('true_structural_recovery' if direct else 'algebraically_equivalent_recovery') if correct else
        'predictive_but_structurally_wrong' if valid_approx and held_approx else 'structurally_wrong')
    return {'class_id':candidate['class_id'],'rank':candidate['rank'],'expanded':candidate['expanded'],
        'validation_rmse':candidate['validation_rmse'],'heldout_rmse':error,
        'validation_adequate':candidate['validation_rmse']<=policy['acceptance_validation_rmse'],
        'heldout_adequate':error<=policy['acceptance_validation_rmse'],
        'validation_approximation':valid_approx,'heldout_approximation':held_approx,
        'oracle_structural_match':bool(correct),'nuisance_atoms':nuisance,'leakage_contaminated':leaked,
        'classification':classification,'scientific_credit':False,'evidence_class':EVIDENCE}


def evaluate_realization(prereg, public, eligibility, wrapped, truth, heldout):
    result=wrapped['discovery']; ranking=result['ranking']; policy=public['policy']; s=prereg['scoring']
    candidates=[candidate_metrics(c,heldout,truth,policy) for c in ranking]
    top=ranking[0] if ranking else None; scored=candidates[0] if candidates else None
    selected=result['top_class']; cid=class_id(signature(truth['base_signature'])) if truth['in_family'] else None
    true=next((c for c in ranking if c['class_id']==cid),None)
    rejected=sorted(k for k,v in eligibility.items() if v['status']=='ineligible')
    leakage_safe=(rejected==sorted(truth['forbidden_features']) and not any(c['leakage_contaminated'] for c in candidates))
    relative=abs(top['coefficient']/truth['coefficient']-1) if top and truth['in_family'] else None
    recovery=bool(top and true and selected==cid and true['rank']==1 and result['decision']=='stable_candidate'
        and max(top['training_rmse'],top['validation_rmse'],scored['heldout_rmse'])<=policy['acceptance_validation_rmse']
        and relative<=s['coefficient_relative_error_max'] and
        top['expanded_complexity']==sum(abs(float(v)) for v in truth['base_signature'].values()))
    cell=truth['cell']; checks={'leakage_safe':leakage_safe}; diagnostics={}
    if truth['in_family']: checks['selected_recovery']=recovery
    if cell=='leakage':
        counterfactuals={name:{split:rmse(surface,0.,public[split]) for split in ('train','validation')}
            for name,surface in [('direct',{'leak':1}),('transitive',{'leak_alias':1}),
                ('reconstructive',{'leak_transform':1,'z':-1}),('powered',{'leak_power':'1/2'})]}
        diagnostics['leakage_counterfactuals']={'errors':counterfactuals,'scientific_credit':False,
            'powered_outside_candidate_grammar':True}
        checks['leakage_temptation']=all(e<=s['independent_metric_tolerance'] for d in counterfactuals.values() for e in d.values())
    if cell=='nuisance':
        ablations={k:result['ablations'][k] for k in truth['irrelevant_atoms']}
        checks['nuisance_robustness']=bool(scored and not scored['nuisance_atoms'] and
            all(a['top_class']==selected and a['decision']=='stable_candidate' for a in ablations.values()))
        checks['equivalence']=bool(true and len(true['members'])>=s['equivalent_surface_min_nuisance'])
        survivors=[c for c in candidates if c['nuisance_atoms'] and c['validation_approximation']]
        checks['nuisance_temptation']=bool(survivors)
        diagnostics.update(irrelevant_ablations=ablations,nuisance_validation_survivors=len(survivors))
    abstention=bool(ranking and result['decision']=='no_stable_law' and result['family_assessment']=='family_inadequate_on_validation')
    if cell=='regime':
        m=truth['regime_multiplier']; floor=math.log(m)/2
        contradiction=pair_diagnostic(heldout,m,s['pair_ratio_tolerance'])
        checks['regime_abstention']=abstention and contradiction and all(c['heldout_rmse']+s['numeric_floor']>=floor for c in candidates)
        diagnostics.update(paired_input_contradiction=contradiction,paired_log_rmse_lower_bound=floor,
            realized_regime_multiplier=m)
    if cell in ('wrong_power','wrong_curve'):
        g=prereg['generation']
        proof=(truth['exponent']==g['wrong_power_exponent'] and prereg['grammar']['max_denominator']==1 and
               not float(truth['exponent']).is_integer()) if cell=='wrong_power' else (
               g['curve_beta_range'][0]<=truth['curve_beta']<=g['curve_beta_range'][1] and truth['curve_beta']!=0)
        proof=proof and truth['wrong_grammar_proof']==prereg['cells'][cell]['proof'] and set(public['features'])=={'x','t','z'}
        checks['misspecification_recognition']=bool(abstention and proof and not true and
            all(not c['heldout_adequate'] for c in candidates))
        diagnostics.update(oracle_wrong_grammar_proof=truth['wrong_grammar_proof'],
            proof_conditions_verified=proof,log_curvature=2*truth['curve_beta'],
            family_rejection_meaning='Finite-data inadequacy before reveal; known generator establishes grammar misspecification after reveal.')
        if cell=='wrong_curve':
            checks['good_approximation_denied_recovery']=bool(scored and scored['validation_approximation'] and
                scored['heldout_approximation'] and not scored['oracle_structural_match'] and
                result['approximation_status']=='predictive_approximation' and abstention)
    if truth['in_family'] and recovery and all(checks.values()):
        candidates[0]['scientific_credit']=True
    classification=(scored['classification'] if recovery else 'hypothesis_family_misspecification' if
        cell in ('wrong_power','wrong_curve') and abstention else 'no_stable_law' if abstention else
        scored['classification'] if scored else 'no_candidate_capability')
    false_selection=bool(scored and result['decision']=='stable_candidate' and not scored['oracle_structural_match'])
    success=bool(ranking and all(checks.values()))
    return {'cell':cell,'replicate':truth['replicate'],'success':success,'checks':checks,
        'classification':classification,'pre_reveal_decision':result['decision'],
        'pre_reveal_family_assessment':result['family_assessment'],'pre_reveal_approximation_status':result['approximation_status'],
        'selected_class':selected,'true_class_rank':true['rank'] if true else None,
        'true_class_surfaces':len(true['members']) if true else 0,'selected_surface':top['representative'] if top else None,
        'selected_training_rmse':top['training_rmse'] if top else None,
        'selected_validation_rmse':top['validation_rmse'] if top else None,
        'selected_heldout_rmse':scored['heldout_rmse'] if scored else None,
        'coefficient_relative_error':relative,'selected_expanded_complexity':top['expanded_complexity'] if top else None,
        'false_positive_selection':false_selection,'justified_abstention':abstention and not truth['in_family'],
        'grammar_recognition':checks.get('misspecification_recognition',False),
        'rejected_features':rejected,'policy':policy,'candidate_count':len(candidates),'surface_count':result['surface_count'],
        'predictively_surviving_wrong_classes':sum(not c['oracle_structural_match'] and c['validation_approximation'] and c['heldout_approximation'] for c in candidates),
        'candidates':candidates,'diagnostics':diagnostics,'evidence_class':EVIDENCE,'scientific_law_claim':False}


def aggregate(prereg, evaluations, integrity):
    cells={}
    expected=prereg['design']['replicates_per_cell']
    for cell in prereg['design']['cells']:
        found=[v for v in evaluations.values() if v['cell']==cell]
        good=sum(v['success'] for v in found)
        cells[cell]={'expected':expected,'evaluated':len(found),'successes':good,
            'consistency':'consistent_success' if good==expected else 'occasional_success' if good else 'systematic_failure_in_this_suite',
            'false_positive_selections':sum(v['false_positive_selection'] for v in found),
            'justified_abstentions':sum(v['justified_abstention'] for v in found),
            'grammar_recognitions':sum(v['grammar_recognition'] for v in found)}
    total=sum(v['successes'] for v in cells.values())
    if not evaluations: label='NO_GO_CAPABILITY'
    elif not integrity or any(not v['checks']['leakage_safe'] for v in evaluations.values()): label='FAIL'
    elif total==prereg['design']['total_realizations'] and len(evaluations)==total: label='PASS'
    elif total: label='PARTIAL'
    else: label='FAIL'
    return {'disposition':prereg['evaluation']['labels'][label],
        'expected_realizations':prereg['design']['total_realizations'],'evaluated_realizations':len(evaluations),
        'successful_realizations':total,'cells':cells,'integrity_controls_pass':integrity,
        'interpretation':'Counts over this prespecified synthetic suite, not a general false-positive rate.',
        'review_status':'PROVISIONAL — INDEPENDENT AUDIT PENDING','scientific_law_claim':False,
        'nonclaims':prereg['nonclaims']}
