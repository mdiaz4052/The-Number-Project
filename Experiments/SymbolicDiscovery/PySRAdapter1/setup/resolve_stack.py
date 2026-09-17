import json,os
from pathlib import Path
os.environ.update(json.loads(Path(".tnp-local/engine-env.json").read_text()))
import juliapkg
juliapkg.add("SymbolicRegression", uuid="8254be44-1295-4e6a-a16d-46603ac705cb", version="=1.11.0")
juliapkg.resolve()
