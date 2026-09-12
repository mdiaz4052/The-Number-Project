"""Small isolated Lean/Comparator controls; no external target imports."""
from pathlib import Path
import json


def generate(root, toolchain):
    root=Path(root)
    sources={
        'clean': ('theorem probe : True := by trivial\n','theorem probe : True := by trivial\n'),
        'reachable_custom': ('theorem probe : True := by trivial\n',
            'axiom usedCustom : True\naxiom unusedCustom : False\ntheorem helper : True := usedCustom\ntheorem probe : True := helper\n'),
        'sorry': ('theorem probe : True := by trivial\n',
            'theorem unusedPlaceholder : False := by sorry\ntheorem probe : True := by sorry\n'),
        'statement_mismatch': ('theorem probe : True := by trivial\n',
            'theorem probe : True ∧ True := ⟨True.intro, True.intro⟩\n')}
    for key,(challenge,solution) in sources.items():
        d=root/key; d.mkdir(parents=True,exist_ok=True)
        (d/'lean-toolchain').write_text(toolchain+'\n')
        (d/'lakefile.toml').write_text('name = "closure_control"\nversion = "0.1.0"\n\n[[lean_lib]]\nname = "Challenge"\n\n[[lean_lib]]\nname = "Solution"\n')
        (d/'Challenge.lean').write_text(challenge)
        (d/'Solution.lean').write_text(solution)
        (d/'config.json').write_text(json.dumps({'challenge_module':'Challenge','solution_module':'Solution','theorem_names':['probe'],
            'permitted_axioms':['propext','Quot.sound','Classical.choice'],'enable_nanoda':True})+'\n')
    return list(sources)
