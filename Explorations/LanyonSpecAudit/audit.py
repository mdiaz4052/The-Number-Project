"""Spec-adequacy mutation audit of pinned Lanyon AI Lean theorem families.

Each variant is a pinned upstream Lean file, optionally mutated by exact string edits,
followed by the strengthened addendum for that system and, for curated mutants, a
refutation snippet. Lean elaborates every declaration even after an earlier one fails,
so one compile per variant yields a per-declaration pass/fail map.

Run from the repository root:

    python -m Explorations.LanyonSpecAudit.audit --check   # pins and edits only, no Lean
    python -m Explorations.LanyonSpecAudit.audit --run     # needs `lake env lean`
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
BUILD = REPO / ".lake" / "lanyon_audit"
RESULTS = ROOT / "results"

SYSTEMS = {
    "burgers": {
        "upstream": ROOT / "upstream/BurgersEquation/inviscid_burgers_1d.lean",
        "sha256": "d464c06562c7316c0a8f56e1b21d89c36d1581769ad00c9fdb842963d4c8e146",
        "addendum": ROOT / "strengthened/Burgers1D.lean",
    },
    "maxwell": {
        "upstream": ROOT / "upstream/MaxwellEquations/maxwell_1d.lean",
        "sha256": "323ecd0e5f4f0dd2f4cf6894c027ff7849e355aac3c091ee02567be43ae7c86e",
        "addendum": ROOT / "strengthened/Maxwell1D.lean",
    },
}

STRENGTHENED = ("jacobianIsDerivative", "realEigenbasis", "dissipationBound")

# Spec blocks whose nonzero right-hand sides receive systematic single-field sign flips.
FLIP_BLOCKS = ("xFluxExprs", "xFluxJacobianExprs", "xFluxJacobianEigenExprs", "xWaveSpeedExprs")
ZERO_RHS = re.compile(r"^-?\(?\s*0(\.0)?\s*\)?$")


@dataclass(frozen=True)
class Edit:
    old: str
    new: str
    count: int


@dataclass(frozen=True)
class Mutant:
    id: str
    system: str
    description: str
    edits: tuple[Edit, ...]
    # Predicted outcome per suite: "pass" (no failing theorem) or "fail".
    predicted_lanyon: str
    predicted_strengthened: str
    refutation: str | None = None
    family: str = "curated"
    notes: str = ""


def _lam(n: int, old: str, new: str) -> Edit:
    return Edit(f"    lambda{n} := {old}\n", f"    lambda{n} := {new}\n", 1)


BURGERS_FLUX = "flux_f := ((1 / 2 : Real) * f * f)"
BURGERS_FLUX_CUBIC = "flux_f := ((1 / 3 : Real) * f * f * f)"
BURGERS_WAVE_FLUX = "((((1 / 2 : Real) * (f_R * f_R)) - ((1 / 2 : Real) * (f_L * f_L)))"
BURGERS_WAVE_FLUX_CUBIC = (
    "((((1 / 3 : Real) * (f_R * f_R * f_R)) - ((1 / 3 : Real) * (f_L * f_L * f_L)))"
)
BURGERS_AMAX = "(max (abs f_L) (abs f_R))"
BURGERS_JAC = "d_f := ((0.0 * f * f) + ((1 / 2 : Real) * 1 * f) + ((1 / 2 : Real) * f * 1))"

MAXWELL_WAVE_EY = "((((c * c) * Bz_R) - ((c * c) * Bz_L)) / (abs c))"
MAXWELL_WAVE_EY_FLIP = "((-(((c * c) * Bz_R)) - -(((c * c) * Bz_L))) / (abs c))"

CURATED: tuple[Mutant, ...] = (
    Mutant("B0", "burgers", "unmutated control", (), "pass", "pass"),
    Mutant(
        "B1", "burgers", "eigenvalue halved: lambda1 := f/2",
        (_lam(1, "f", "((1 / 2 : Real) * f)"),), "pass", "fail", "B1",
    ),
    Mutant(
        "B2", "burgers", "eigenvalue sign-flipped: lambda1 := -f",
        (_lam(1, "f", "-(f)"),), "pass", "fail", "B2",
    ),
    Mutant(
        "B3", "burgers", "Jacobian wrong: d_f := f*f (eigenvalue left as f)",
        (Edit(BURGERS_JAC, "d_f := (f * f)", 1),), "pass", "fail", "B3",
    ),
    Mutant(
        "B4", "burgers", "flux changed to f^3/3 in the flux only (waves still use f^2/2)",
        (Edit(BURGERS_FLUX, BURGERS_FLUX_CUBIC, 1),), "fail", "fail", "B4",
        notes="positive control: internal inconsistency that the Lanyon family should catch",
    ),
    Mutant(
        "B5", "burgers",
        "different PDE: flux f^3/3 in flux and Lax-Friedrichs waves; Jacobian, eigenvalue, "
        "wave speed left for f^2/2",
        (Edit(BURGERS_FLUX, BURGERS_FLUX_CUBIC, 1),
         Edit(BURGERS_WAVE_FLUX, BURGERS_WAVE_FLUX_CUBIC, 2)),
        "pass", "fail", "B5",
    ),
    Mutant(
        "B6", "burgers", "wave-speed estimate halved: mu1 := f/2",
        (Edit("    mu1 := f\n", "    mu1 := ((1 / 2 : Real) * f)\n", 1),), "fail", "fail", "B6",
        notes="positive control for xWaveStability",
    ),
    Mutant(
        "B7", "burgers",
        "Lax-Friedrichs dissipation speed halved consistently in waves, speeds and hypotheses",
        (Edit(BURGERS_AMAX, f"((1 / 2 : Real) * {BURGERS_AMAX})", 6),), "pass", "fail", "B7",
    ),
    Mutant("M0", "maxwell", "unmutated control", (), "pass", "pass"),
    Mutant(
        "M1", "maxwell", "eigenvalues lambda3, lambda4 := -c (spectrum all -c, -c, -c, -c, 0, 0)",
        (_lam(3, "c", "-(c)"), _lam(4, "c", "-(c)")), "pass", "fail", "M1",
    ),
    Mutant(
        "M2", "maxwell", "Jacobian entry dFlux_Ey/dBz := c instead of c^2",
        (Edit("        d_Bz := (c * c)\n", "        d_Bz := c\n", 1),), "pass", "fail", "M2",
    ),
    Mutant(
        "M3", "maxwell",
        "non-hyperbolic system: flux_Ey sign flipped consistently in flux, waves and Jacobian "
        "(spectrum becomes +-ic); listed eigenvalues unchanged",
        (Edit("flux_Ey := ((c * c) * Bz)", "flux_Ey := -(((c * c) * Bz))", 1),
         Edit(MAXWELL_WAVE_EY, MAXWELL_WAVE_EY_FLIP, 2),
         Edit("        d_Bz := (c * c)\n", "        d_Bz := -((c * c))\n", 1)),
        "pass", "fail", "M3",
    ),
    Mutant(
        "M4", "maxwell", "zero eigenvalue moved: lambda5 := c",
        (_lam(5, "0.0", "c"),), "fail", "fail", "M4",
        notes="positive control for xWaveStability (mu5 = 0)",
    ),
    Mutant(
        "M5", "maxwell",
        "Lax-Friedrichs dissipation speed halved consistently in waves, speeds and hypotheses",
        (Edit("/ (abs c))", "/ ((1 / 2 : Real) * (abs c)))", 12),
         Edit("speed1 := -((abs c))", "speed1 := -(((1 / 2 : Real) * (abs c)))", 1),
         Edit("speed2 := (abs c)", "speed2 := ((1 / 2 : Real) * (abs c))", 1),
         Edit("(-((abs c)) ≠ 0)", "(-(((1 / 2 : Real) * (abs c))) ≠ 0)", 1),
         Edit("((abs c) ≠ 0)", "(((1 / 2 : Real) * (abs c)) ≠ 0)", 1)),
        "pass", "fail", "M5",
    ),
)


def _block_ranges(lines: list[str], name: str) -> tuple[int, int]:
    start = next(i for i, line in enumerate(lines) if f"def {name} " in line)
    end = next(i for i in range(start + 1, len(lines)) if lines[i].startswith(("noncomputable def", "def ", "theorem", "structure")))
    return start, end


def systematic_mutants(system: str, text: str) -> tuple[Mutant, ...]:
    """Every single-field sign flip of a nonzero right-hand side in the FLIP_BLOCKS."""
    lines = text.splitlines(keepends=True)
    out = []
    for block in FLIP_BLOCKS:
        start, end = _block_ranges(lines, block)
        parent = None
        for i in range(start, end):
            m = re.match(r"^(\s+)(\w+) :=\s*(.*?)\s*$", lines[i])
            if not m:
                continue
            indent, fieldname, rhs = m.groups()
            if not rhs:
                parent = fieldname
                continue
            if ZERO_RHS.match(rhs):
                continue
            label = f"{block}.{parent + '.' if block == 'xFluxJacobianExprs' else ''}{fieldname}"
            # Prefix the line with its neighbor to make the edit unique within the file.
            context = lines[i - 1] + lines[i]
            new = lines[i - 1] + f"{indent}{fieldname} := -({rhs})\n"
            if text.count(context) != 1:
                context = "".join(lines[start:i + 1])
                new = "".join(lines[start:i]) + f"{indent}{fieldname} := -({rhs})\n"
            kind = {"xFluxExprs": "flux", "xFluxJacobianExprs": "jacobian",
                    "xFluxJacobianEigenExprs": "eigenvalue", "xWaveSpeedExprs": "wavespeed"}[block]
            pred_l, pred_s = {
                "flux": ("fail", "fail"),
                "jacobian": ("pass", "fail"),
                "eigenvalue": ("pass", "fail"),
                "wavespeed": ("pass", "pass"),
            }[kind]
            out.append(Mutant(
                id=f"{system[0].upper()}S{len(out) + 1:02d}",
                system=system,
                description=f"sign flip of {label}",
                edits=(Edit(context, new, 1),),
                predicted_lanyon=pred_l,
                predicted_strengthened=pred_s,
                family=f"systematic-{kind}",
            ))
    return tuple(out)


def upstream_text(system: str) -> str:
    return SYSTEMS[system]["upstream"].read_text(encoding="utf-8")


def all_mutants() -> tuple[Mutant, ...]:
    return CURATED + systematic_mutants("burgers", upstream_text("burgers")) + systematic_mutants(
        "maxwell", upstream_text("maxwell"))


def apply_edits(text: str, edits: tuple[Edit, ...], mutant_id: str) -> str:
    for edit in edits:
        found = text.count(edit.old)
        if found != edit.count:
            raise ValueError(f"{mutant_id}: expected {edit.count} occurrence(s) of {edit.old!r}, found {found}")
        text = text.replace(edit.old, edit.new)
    return text


def variant_text(mutant: Mutant) -> str:
    spec = apply_edits(upstream_text(mutant.system), mutant.edits, mutant.id)
    parts = [spec, "\n", SYSTEMS[mutant.system]["addendum"].read_text(encoding="utf-8")]
    if mutant.refutation:
        parts += ["\n", (ROOT / "refutations" / f"{mutant.refutation}.lean").read_text(encoding="utf-8")]
    reproof = ROOT / "reproofs" / f"{mutant.id}.lean"
    if reproof.exists():
        parts += ["\n", reproof.read_text(encoding="utf-8")]
    return "".join(parts)


DECL = re.compile(r"^(?:noncomputable\s+)?(theorem|lemma|def|structure|example)\s+([\w.]+)?")


def declaration_starts(text: str) -> list[tuple[int, str, str]]:
    starts = []
    for n, line in enumerate(text.splitlines(), start=1):
        m = DECL.match(line)
        if m:
            starts.append((n, m.group(1), m.group(2) or f"example@{n}"))
    return starts


def qualified_theorems(text: str) -> list[tuple[str, str]]:
    """(short name, fully qualified name) of every theorem, tracking `namespace`/`end`."""
    stack: list[str] = []
    out = []
    for line in text.splitlines():
        if m := re.match(r"^namespace\s+(\S+)", line):
            stack.append(m.group(1))
        elif (m := re.match(r"^end\s+(\S+)", line)) and stack and stack[-1] == m.group(1):
            stack.pop()
        elif (m := DECL.match(line)) and m.group(1) in ("theorem", "lemma"):
            out.append((m.group(2), ".".join(stack + [m.group(2)])))
    return out


def attribute(line: int, starts: list[tuple[int, str, str]]) -> tuple[str, str]:
    owner = ("header", "")
    for n, kind, name in starts:
        if n > line:
            break
        owner = (kind, name)
    return owner


def compile_variant(mutant: Mutant) -> dict:
    text = variant_text(mutant)
    # A failed proof is still added to the environment with `sorry`, so anything that uses it
    # would elaborate cleanly. Every judged theorem must therefore be axiom-checked.
    if not text.endswith("\n"):
        text += "\n"
    probes = qualified_theorems(text)
    first_probe = len(text.splitlines()) + 2
    text += "\n" + "".join(f"#print axioms {q}\n" for _, q in probes)
    BUILD.mkdir(parents=True, exist_ok=True)
    path = BUILD / f"{mutant.id}.lean"
    path.write_text(text, encoding="utf-8")
    proc = subprocess.run(["lake", "env", "lean", "--json", str(path)], cwd=REPO,
                          capture_output=True, text=True, timeout=3600)
    starts = declaration_starts(text)
    failing: dict[str, list[str]] = {}
    for raw in proc.stdout.splitlines():
        try:
            msg = json.loads(raw)
        except json.JSONDecodeError:
            continue
        line = msg["pos"]["line"]
        if line >= first_probe:
            name = probes[line - first_probe][0]
            if "sorryAx" in msg["data"]:
                failing.setdefault(name, []).append("depends on sorryAx")
            continue
        if msg.get("severity") != "error":
            continue
        kind, name = attribute(msg["pos"]["line"], starts)
        failing.setdefault(name, []).append(f"line {msg['pos']['line']}: {msg['data'][:1500]}")
    theorems = [name for _, kind, name in starts if kind in ("theorem", "lemma")]
    upstream_theorems = [name for _, kind, name in declaration_starts(upstream_text(mutant.system))
                         if kind == "theorem"]
    refutations = [name for name in theorems if name.startswith("refute_")]
    reproofs = [name for name in theorems if name.startswith("reprove_")]
    spec_errors = sorted(n for n in failing if n not in theorems)
    lanyon_failed = sorted(n for n in upstream_theorems if n in failing)
    strengthened_failed = sorted(n for n in STRENGTHENED if n in failing)
    return {
        "id": mutant.id,
        "system": mutant.system,
        "family": mutant.family,
        "description": mutant.description,
        "predicted": {"lanyon": mutant.predicted_lanyon, "strengthened": mutant.predicted_strengthened},
        "observed": {
            "lanyon": "fail" if lanyon_failed else "pass",
            "strengthened": "fail" if (lanyon_failed or strengthened_failed) else "pass",
        },
        "lanyon_failed": lanyon_failed,
        "strengthened_failed": strengthened_failed,
        "refutations": {name: name not in failing for name in refutations},
        "reproofs": {name: name not in failing for name in reproofs},
        "non_theorem_errors": spec_errors,
        "messages": {k: v for k, v in sorted(failing.items())},
    }


def check() -> None:
    for system, cfg in SYSTEMS.items():
        digest = hashlib.sha256(cfg["upstream"].read_bytes()).hexdigest()
        if digest != cfg["sha256"]:
            raise SystemExit(f"{system}: pinned upstream hash mismatch {digest}")
    mutants = all_mutants()
    ids = [m.id for m in mutants]
    if len(ids) != len(set(ids)):
        raise SystemExit("duplicate mutant ids")
    for m in mutants:
        variant_text(m)
    print(f"OK: {len(mutants)} variants ({len(CURATED)} curated) apply cleanly to pinned upstream")


def render(results: list[dict]) -> str:
    rows = ["| id | family | mutation | predicted L / L+S | observed L / L+S | failing theorems | refuted | re-proved |",
            "|---|---|---|---|---|---|---|---|"]
    for r in results:
        refuted = ", ".join(n for n, ok in r["refutations"].items() if ok) or "-"
        reproved = ", ".join(n for n, ok in r["reproofs"].items() if ok) or "-"
        failing = ", ".join(r["lanyon_failed"] + r["strengthened_failed"]) or "-"
        if r["non_theorem_errors"]:
            failing += f" (non-theorem errors: {', '.join(r['non_theorem_errors'])})"
        rows.append(
            f"| {r['id']} | {r['family']} | {r['description']} | "
            f"{r['predicted']['lanyon']} / {r['predicted']['strengthened']} | "
            f"{r['observed']['lanyon']} / {r['observed']['strengthened']} | {failing} | {refuted} | {reproved} |")
    return "\n".join(rows) + "\n"


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--only", nargs="*", help="mutant ids to compile, or ALL")
    args = parser.parse_args(argv)
    check()
    if not args.run:
        return
    only = None if not args.only or args.only == ["ALL"] else set(args.only)
    selected = [m for m in all_mutants() if only is None or m.id in only]
    results = []
    for m in selected:
        r = compile_variant(m)
        print(f"{m.id}: L={r['observed']['lanyon']} L+S={r['observed']['strengthened']} "
              f"failing={r['lanyon_failed'] + r['strengthened_failed']} refutations={r['refutations']} "
              f"other={r['non_theorem_errors']}", flush=True)
        if args.verbose:
            for name, msgs in r["messages"].items():
                for text in msgs:
                    print(f"--- {m.id} {name}\n{text}", flush=True)
        results.append(r)
    if only is None:
        RESULTS.mkdir(exist_ok=True)
        (RESULTS / "results.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
        (RESULTS / "table.md").write_text(render(results), encoding="utf-8")
        print("=== table.md ===\n" + render(results), flush=True)
        print("=== results.json ===\n" + json.dumps(results, sort_keys=True), flush=True)


if __name__ == "__main__":
    main(sys.argv[1:])
