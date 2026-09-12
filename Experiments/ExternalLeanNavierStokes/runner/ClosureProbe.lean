import Lean

open Lean Elab Command in
elab "#closure_probe " n:ident : command => do
  let name := n.getId
  let env ← getEnv
  let some info := env.find? name | throwError "missing exact theorem {name}"
  unless (match info with | .thmInfo _ => true | _ => false) do
    throwError "requested declaration is not a theorem: {name}"
  let text ← liftTermElabM do
    withOptions (fun o => o.setBool `pp.universes true |>.setBool `pp.explicit true
      |>.setBool `pp.fullNames true |>.setBool `pp.proofs true) do
      return (← Meta.ppExpr info.type).pretty
  let data := Json.mkObj [
    ("name", toJson name.toString),
    ("kind", toJson "theorem"),
    ("universe_parameters", toJson (info.levelParams.map Name.toString)),
    ("elaborated_type", toJson text),
    ("structural_identity", toJson "computed from pinned lean4export expression by closure.py")]
  logInfo m!"TNP_STATEMENT_JSON {data.compress}"
