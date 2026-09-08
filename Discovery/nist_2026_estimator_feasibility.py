"""Source-bound feasibility audit for the NIST 2026 G estimator layers."""
from __future__ import annotations

import argparse, hashlib, json, subprocess, sys
from datetime import datetime
from decimal import Decimal, InvalidOperation
from fractions import Fraction
from pathlib import Path

from Discovery.preregistration_history import verify_preregistration_freeze
from Discovery.source_history import SourceVerificationError

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = Path("Experiments/GMeasurements")
PREREGISTRATION_PATH = DIRECTORY / "nist_2026_estimator_feasibility_preregistration_v1.json"
SOURCE_ATTESTATION_PATH = DIRECTORY / "nist_2026_estimator_source_attestation_v1.json"
DEFAULT_OUTPUT = DIRECTORY / "nist_2026_estimator_feasibility_v1.json"
BASELINE = "151b9c920cadb90a9fd02766cc8def7ba9348f61"
PREREGISTRATION_COMMIT = "a4451482ab211df4f5c9ede0e339db9ca25a97cd"
PREREGISTRATION_SHA256 = "32e03cb85102bda3281fef8b0a5b3eee4133de181154526f1f605aa4be182b47"
EXTERNAL_ANCHOR = {
    "event": "draft_pull_request_created",
    "url": "https://github.com/mdiaz4052/The-Number-Project/pull/46",
    "created_at": "2026-09-08T22:57:26Z",
    "preregistration_commit_sha": PREREGISTRATION_COMMIT,
    "outcome_blind": False,
}
SOURCE_PATHS = (
    "Discovery/nist_2026_estimator_feasibility.py",
    "Notes/NIST2026EstimatorFeasibilitySpecification.md",
    "Notes/NIST2026EstimatorFeasibility.md",
    PREREGISTRATION_PATH.as_posix(), SOURCE_ATTESTATION_PATH.as_posix(),
)
E001_FORBIDDEN = (
    "Experiments/GMeasurements/hust_2018_aaf_source_audit_v1.manifest.json",
    "Experiments/GMeasurements/hust_2018_aaf_depth_2b_authorization_v1.json",
    "Experiments/GMeasurements/hust_2018_aaf_depth_2b_authorization_v2.json",
)
INPUT_ORDER = ("copper_servo", "copper_free", "sapphire_servo", "sapphire_free")
TABLE18_SIGMAS = ("23.2", "30.3", "37.5", "93.9")
CONSENSUS_MISSING_IDS = (
    "epsilon_likelihood_distribution", "posterior_sampler_algorithm",
    "posterior_sampling_controls", "robust_estimator_computational_conventions",
    "dark_correlation_matrix_identity",
)

class NISTFeasibilityError(ValueError): pass

def serialize_artifact(v): return json.dumps(v, indent=2, sort_keys=True, allow_nan=False) + "\n"
def digest(b): return hashlib.sha256(b).hexdigest()
def fraction_record(x): return {"numerator": str(x.numerator), "denominator": str(x.denominator)}

def _json(data):
    def unique(pairs):
        out = {}
        for k, v in pairs:
            if k in out: raise NISTFeasibilityError(f"duplicate JSON key: {k}")
            out[k] = v
        return out
    try: return json.loads(data, object_pairs_hook=unique)
    except json.JSONDecodeError as e: raise NISTFeasibilityError("malformed JSON") from e

def decimal_fraction(v):
    if not isinstance(v, str): raise NISTFeasibilityError("authoritative decimal must be a string")
    try: d = Decimal(v)
    except InvalidOperation as e: raise NISTFeasibilityError("malformed authoritative decimal") from e
    if not d.is_finite(): raise NISTFeasibilityError("authoritative decimal must be finite")
    return Fraction(d)

def verify_preregistration(root=ROOT):
    try:
        data = verify_preregistration_freeze(root, baseline=BASELINE, commit=PREREGISTRATION_COMMIT,
            path=PREREGISTRATION_PATH.as_posix(), sha256=PREREGISTRATION_SHA256)
    except SourceVerificationError as e: raise NISTFeasibilityError(str(e)) from e
    p = _json(data)
    if p["intended_base_sha"] != BASELINE or p["known_prior_information"]["outcome_blind"] is not False:
        raise NISTFeasibilityError("frozen NIST protocol identity differs")
    if p.get("restart_provenance", {}).get("abandoned_pr") != 45:
        raise NISTFeasibilityError("replacement freeze must record abandoned PR 45")
    return p

def frozen_correlation_matrix(p):
    u = p["source_projection"]["experimental_layer"]["table_18"]["correlation_upper_triangle"]
    if len(u) != 4 or any(len(r) != 4 for r in u): raise NISTFeasibilityError("frozen correlation triangle malformed")
    m = [[None]*4 for _ in range(4)]
    for i in range(4):
        for j in range(i,4):
            if not isinstance(u[i][j], str): raise NISTFeasibilityError("frozen correlation triangle incomplete")
            m[i][j] = m[j][i] = u[i][j]
    return m

def load_source_attestation(p, root=ROOT):
    a = _json((root / SOURCE_ATTESTATION_PATH).read_bytes())
    src = a.get("source", {})
    if src.get("doi") != p["primary_source"]["doi"] or src.get("nist_pdf") != p["primary_source"]["nist_pdf"]:
        raise NISTFeasibilityError("source identity differs from freeze")
    if src.get("raw_pdf_hash_claim") is not False or src.get("raw_pdf_persisted") is not False:
        raise NISTFeasibilityError("source attestation overclaims raw PDF custody")
    exp = a.get("experimental_layer", {})
    if tuple(exp.get("input_order", ())) != INPUT_ORDER: raise NISTFeasibilityError("input order differs")
    frozen = p["source_projection"]["experimental_layer"]["table_16"]["measurements"]
    att = exp.get("table_16", {}).get("measurements", [])
    if len(frozen) != 4 or len(att) != 4: raise NISTFeasibilityError("Table 16 inventory incomplete")
    for f, s, ident in zip(frozen, att, INPUT_ORDER):
        if (f.get("id"), s.get("id")) != (ident, ident): raise NISTFeasibilityError("Table 16 identity differs")
        if f["G_decimal_in_1e_minus_11_units"] != s["G_decimal_in_1e_minus_11_units"]: raise NISTFeasibilityError("Table 16 G differs")
        if f["relative_standard_uncertainty_ppm"] != s["displayed_relative_standard_uncertainty_ppm"]: raise NISTFeasibilityError("Table 16 uncertainty differs")
        decimal_fraction(s["G_decimal_in_1e_minus_11_units"])
    t18 = exp.get("table_18", {})
    if t18.get("diagonal_relative_standard_uncertainty_ppm") != list(TABLE18_SIGMAS): raise NISTFeasibilityError("Table 18 diagonal differs")
    if t18.get("correlation_matrix") != frozen_correlation_matrix(p): raise NISTFeasibilityError("Table 18 correlation differs")
    missing = a.get("consensus_layer", {}).get("not_uniquely_specified_in_primary_paper", [])
    if tuple(x.get("id") for x in missing) != CONSENSUS_MISSING_IDS: raise NISTFeasibilityError("Bayesian blocker inventory differs")
    if a.get("authority_resolution", {}).get("controlling_scientific_source") != "peer-reviewed journal article PDF served by the NIST local-download endpoint":
        raise NISTFeasibilityError("source authority differs")
    return a

def correlation_matrix(a):
    m = [[decimal_fraction(v) for v in row] for row in a["experimental_layer"]["table_18"]["correlation_matrix"]]
    if len(m) != 4 or any(len(r)!=4 for r in m): raise NISTFeasibilityError("correlation matrix must be 4x4")
    for i in range(4):
        if m[i][i] != 1: raise NISTFeasibilityError("correlation diagonal must be one")
        for j in range(4):
            if m[i][j] != m[j][i] or abs(m[i][j]) > 1: raise NISTFeasibilityError("invalid correlation geometry")
    return m

def relative_covariance_matrix(a):
    s = [decimal_fraction(v) for v in TABLE18_SIGMAS]
    if any(x <= 0 for x in s): raise NISTFeasibilityError("standard uncertainties must be positive")
    r = correlation_matrix(a)
    return [[r[i][j]*s[i]*s[j] for j in range(4)] for i in range(4)]

def determinant(matrix):
    n=len(matrix); w=[row[:] for row in matrix]; out=Fraction(1)
    if not n or any(len(r)!=n for r in matrix): raise NISTFeasibilityError("square matrix required")
    for c in range(n):
        p=next((r for r in range(c,n) if w[r][c]),None)
        if p is None: return Fraction(0)
        if p!=c: w[c],w[p]=w[p],w[c]; out=-out
        pv=w[c][c]; out*=pv
        for r in range(c+1,n):
            f=w[r][c]/pv
            for k in range(c,n): w[r][k]-=f*w[c][k]
    return out

def leading_principal_minors(m): return tuple(determinant([r[:n] for r in m[:n]]) for n in range(1,len(m)+1))

def experimental_covariance_audit(a):
    c=relative_covariance_matrix(a); mins=leading_principal_minors(c)
    if not all(x>0 for x in mins): raise NISTFeasibilityError("experimental covariance is not positive definite")
    return {"verdict":"GO","reason":"source_uniquely_defines_positive_definite_4x4_experimental_covariance",
        "input_order":list(INPUT_ORDER),"standard_uncertainty_ppm":list(TABLE18_SIGMAS),
        "correlation_matrix":[[fraction_record(x) for x in r] for r in correlation_matrix(a)],
        "relative_covariance_matrix_ppm_squared":[[fraction_record(x) for x in r] for r in c],
        "leading_principal_minors":[fraction_record(x) for x in mins],"positive_definite":True,
        "source_precision_policy":a["experimental_layer"]["table_18"]["precision_policy"]}

def bayesian_consensus_audit(p,a):
    missing=a["consensus_layer"]["not_uniquely_specified_in_primary_paper"]
    if tuple(x["id"] for x in missing)!=CONSENSUS_MISSING_IDS: raise NISTFeasibilityError("Bayesian blocker inventory differs")
    req=p["feasibility_questions"]["B_published_bayesian_consensus"]["GO_requirements"]
    if not missing or not req: raise NISTFeasibilityError("Bayesian NO-GO lacks blocker")
    return {"verdict":"NO_GO","reason":"primary_paper_does_not_uniquely_specify_deterministic_equation_64_reproduction",
        "specified":a["consensus_layer"]["specified"],"missing_result_driving_information":missing,"go_requirements":req,
        "nonclaim":"No GLS or conventional Bayesian implementation is substituted for equation (64)."}

def source_authority_audit(a):
    x=a["authority_resolution"]; j=x["journal_pdf_result"]; l=x["landing_page_displayed_result"]
    if j["G_decimal_in_1e_minus_11_units"]==l["G_decimal_in_1e_minus_11_units"]: raise NISTFeasibilityError("source conflict sentinel vanished")
    return {"controlling_source":x["controlling_scientific_source"],"landing_page_numerical_role":x["landing_page_role"],
        "numerical_conflict_present":True,"journal_pdf_result":j,"landing_page_displayed_result":l,
        "resolution":"peer_reviewed_article_pdf_controls_scientific_transcription"}

def _timestamp(s): return datetime.fromisoformat(s.replace("Z","+00:00"))
def verify_implementation_chronology(root=ROOT):
    anchor=_timestamp(EXTERNAL_ANCHOR["created_at"])
    freeze=subprocess.run(["git","-C",str(root),"show","-s","--format=%aI%x00%cI",PREREGISTRATION_COMMIT],capture_output=True,text=True,check=True).stdout.strip().split("\x00")
    if len(freeze)!=2 or any(_timestamp(x)>=anchor for x in freeze): raise NISTFeasibilityError("freeze does not precede anchor")
    lines=subprocess.run(["git","-C",str(root),"log","--diff-filter=A","--reverse","--format=%H%x00%aI%x00%cI","--","Discovery/nist_2026_estimator_feasibility.py"],capture_output=True,text=True,check=True).stdout.strip().splitlines()
    if not lines: raise NISTFeasibilityError("implementation has no committed introduction")
    f=lines[0].split("\x00")
    if len(f)!=3 or any(_timestamp(x)<=anchor for x in f[1:]): raise NISTFeasibilityError("implementation does not postdate anchor")
    if subprocess.run(["git","-C",str(root),"merge-base","--is-ancestor",PREREGISTRATION_COMMIT,f[0]],capture_output=True).returncode:
        raise NISTFeasibilityError("implementation does not descend from freeze")

def source_snapshot(root=ROOT):
    commit=subprocess.run(["git","-C",str(root),"log","-1","--format=%H","--",*SOURCE_PATHS],capture_output=True,text=True,check=True).stdout.strip()
    files=[]
    for path in SOURCE_PATHS:
        cur=(root/path).read_bytes(); rec=subprocess.run(["git","-C",str(root),"show",f"{commit}:{path}"],capture_output=True)
        if rec.returncode or rec.stdout!=cur: raise NISTFeasibilityError("commit result-driving source before artifact emission")
        files.append({"path":path,"sha256":digest(cur)})
    return {"source_commit_sha":commit,"files":files}
def verify_e001_isolation():
    if set(E001_FORBIDDEN)&set(SOURCE_PATHS): raise NISTFeasibilityError("E-001 entered source inventory")

def build_artifact(root=ROOT):
    p=verify_preregistration(root); verify_implementation_chronology(root); a=load_source_attestation(p,root)
    exp=experimental_covariance_audit(a); bay=bayesian_consensus_audit(p,a); auth=source_authority_audit(a)
    return {"schema_version":1,"artifact_id":"nist_2026_estimator_feasibility_v1","kind":"source_and_estimator_reconstructability_audit",
        "integrity":{"baseline_main_sha":BASELINE,"preregistration_commit_sha":PREREGISTRATION_COMMIT,"preregistration_sha256":PREREGISTRATION_SHA256,"external_anchor":EXTERNAL_ANCHOR,"source_snapshot":source_snapshot(root)},
        "known_prior_information":p["known_prior_information"],"restart_provenance":p["restart_provenance"],
        "source":{"doi":p["primary_source"]["doi"],"nist_pdf":p["primary_source"]["nist_pdf"],"source_attestation_path":SOURCE_ATTESTATION_PATH.as_posix(),"raw_pdf_persisted":False,"raw_pdf_hash_claim":False},
        "source_authority":auth,"experimental_covariance_layer":exp,"published_bayesian_consensus_layer":bay,
        "decision":{"experimental_covariance":"GO","published_bayesian_consensus":"NO_GO","authorized_next_step":"preregister_n4_experimental_covariance_correlated_estimator_certificate","common_constant_comparison":"NOT_EVALUATED","equation_64_reproduction":"NOT_AUTHORIZED"},
        "claim_limits":["Deterministic reconstructability is established only for the four-dimensional experimental covariance object.","Equation (64) and the dark-uncertainty posterior are not reproduced.","No NIST-26/BIPM-14/CODATA common-constant comparison is performed.","The peer-reviewed PDF controls over conflicting landing-page numerics.","No HUST AAF E-001 evidence boundary is used."]}

def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__); g=ap.add_mutually_exclusive_group(); g.add_argument("--check",action="store_true"); g.add_argument("--output",type=Path); args=ap.parse_args(argv)
    try:
        art=build_artifact(); text=serialize_artifact(art)
        if args.check:
            verify_e001_isolation(); path=ROOT/DEFAULT_OUTPUT
            if not path.exists() or path.read_text()!=text: raise NISTFeasibilityError("NIST feasibility artifact missing or stale")
            print("NIST 2026 estimator feasibility verified: covariance GO; Bayesian consensus NO-GO")
        elif args.output: args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(text)
        else: print(text,end="")
    except (NISTFeasibilityError,OSError,KeyError,TypeError,subprocess.SubprocessError) as e:
        print(f"nist_2026_estimator_feasibility_invalid: {e}",file=sys.stderr); raise SystemExit(1) from e
if __name__=="__main__": main()
