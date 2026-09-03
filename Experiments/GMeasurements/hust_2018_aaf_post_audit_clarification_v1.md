# HUST 2018 AAF post-audit clarification v1

Status: POST-AUDIT SEMANTIC CLARIFICATION; ORIGINAL PREREGISTRATION UNCHANGED

This clarification records corrections identified after independent audit of the HUST 2018 AAF source-availability implementation. It does not alter the frozen preregistration bytes or retroactively change the GO criterion.

## Replication-depth label

The preregistration used the field name `maximum_supported_replication_depth`. That wording is too strong when some listed public Source Data files were not successfully retrieved and therefore deeper levels were not assessed.

The current audit output uses `maximum_assessed_replication_depth`.

For the retrieved evidence set, the assessed depth is `2a`. Depths above `2a` are recorded as `not_assessed` rather than asserted unsupported. The original preregistration remains historical evidence of the stronger label that was initially chosen.

## Classifier sensitivity

A contaminated or unavailable result-driving path removes the affected AAF determination from authorization. The overall decision falls to `PARTIAL` only when no AAF-I/II/III determination retains a target-clean depth-2a path.

Therefore `GO / 2a` is always accompanied by an explicit authorized count and list.

## Semantic-source review

The machine guard verifies bytes, metadata, graph structure, and deterministic arithmetic. It does not understand a PDF semantically. A separate second-reader record now pins the human verification of the three highest-risk source claims: the target-clean `P_g,l,m` definition, the positive magnetic-damper correction direction, and the AAF-I/II/III Table-3 transcription/air-density statement.

## Workflow rule

Any future temporary workflow with `contents: write` must include both a bot-loop guard and an exact branch/head-ref guard. The permanent test suite enforces this repository rule.
