"""Bounded pre-outcome mutations of new production source, each restored immediately.

Run only before the frozen source/seed epoch. Not a source repair or new realization.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from Discovery import symbolic_margin as run

CASES = [
    ('threshold_equality', "'inadequate': error > bound", "'inadequate': error >= bound", 'MarginMathTests.test_exact_threshold_equality_and_flip'),
    ('stale_multiplier', "m, delta = scoring['adequacy_noise_multiplier'], scoring['numeric_floor']", "m, delta = 2.0, scoring['numeric_floor']", 'MarginMathTests.test_policy_values_not_stale_literals'),
    ('noise_not_varied', 'clean + epsilon * noise', 'clean + 0.02 * noise', 'GeneratorAndEvaluationTests.test_independent_formula_matching_strata_streams_and_changed_noise'),
    ('curvature_removed', "else g['curvature_beta']", "else 0.0", 'GeneratorAndEvaluationTests.test_independent_formula_matching_strata_streams_and_changed_noise'),
    ('block_seed_reused', "f'{seed}:margin1:block:{block}'", "f'{seed}:margin1:block:0'", 'GeneratorAndEvaluationTests.test_independent_formula_matching_strata_streams_and_changed_noise'),
    ('wrong_law_credited', "candidates[0]['scientific_credit'] = credit", "candidates[0]['scientific_credit'] = True", 'GeneratorAndEvaluationTests.test_wrong_predictive_stable_selection_gets_no_structural_credit'),
    ('rank1_substituted_for_family', "family = min(c['validation_rmse'] for c in ranking)", "family = ranking[0]['validation_rmse']", 'MarginMathTests.test_retrospective_family_and_rank1_are_distinct'),
    ('adverse_outcomes_fail_completion', "'COMPLETE' if set(records) == set(expected)", "'COMPLETE' if not any(v['unjustified_family_rejection'] for v in records.values()) and set(records) == set(expected)", 'CustodyAndAggregationTests.test_adverse_performance_complete_partial_failure_and_nonmonotonic'),
]


def main():
    if (run.ART / 'seed_commitment.json').exists():
        raise ValueError('preflight mutations prohibited after seed commitment')
    path = run.ROOT / 'Discovery/symbolic_margin_science.py'
    original = path.read_bytes(); source = original.decode()
    previous_path = run.ART / 'mutation_preflight.attempt1.json'
    previous = run.read(previous_path) if previous_path.exists() else None
    if previous and previous['production_source_sha256'] != hashlib.sha256(original).hexdigest():
        raise ValueError('cannot reuse prior mutation checks across changed production source')
    rows = []
    for name, old, new, test in CASES:
        prior = next((r for r in previous['cases'] if r['name'] == name and r['old'] == old and r['new'] == new and r['test'] == test and r['killed_by_assertion']), None) if previous else None
        if prior:
            rows.append(prior)
            continue
        if source.count(old) != 1:
            raise ValueError('mutation location not unique: ' + name)
        try:
            path.write_text(source.replace(old, new))
            for cache in (run.ROOT / 'Discovery/__pycache__').glob('symbolic_margin_science.*.pyc'):
                cache.unlink()
            result = subprocess.run([sys.executable, '-B', '-m', 'unittest', 'tests.test_symbolic_margin.' + test, '-v'],
                                    cwd=run.ROOT, capture_output=True, text=True)
            log = result.stdout + result.stderr
            killed = result.returncode != 0 and 'AssertionError' in log and 'SyntaxError' not in log and 'ImportError' not in log
            rows.append({'name': name, 'old': old, 'new': new, 'test': test, 'returncode': result.returncode,
                         'killed_by_assertion': killed, 'mutant_sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'output': log})
        finally:
            path.write_bytes(original)
            for cache in (run.ROOT / 'Discovery/__pycache__').glob('symbolic_margin_science.*.pyc'):
                cache.unlink()
    record = {'schema': 'tnp-margin1/mutation-preflight-v1', 'production_source_sha256': hashlib.sha256(original).hexdigest(),
              'before_target_seed': True, 'prior_calibration_attempt_sha256': run.sha_file(previous_path) if previous else None,
              'calibration_note': 'Initial credit mutant raised TypeError before reaching its intended assertion. Retained as attempt1; only that mutant recalibrated. Seven successful cases reused at unchanged production-source bytes.' if previous else None, 'all_killed': all(r['killed_by_assertion'] for r in rows), 'cases': rows}
    run.write_new(run.ART / 'mutation_preflight.json', record)
    print(json.dumps({'all_killed': record['all_killed'], 'cases': [(r['name'], r['killed_by_assertion']) for r in rows]}))
    if not record['all_killed']:
        raise ValueError('mutation survived or failed for wrong reason')


if __name__ == '__main__':
    main()
