import subprocess,sys,json,hashlib,datetime
from pathlib import Path
label=sys.argv[1]; cmd=sys.argv[2:]
p=Path("Experiments/SymbolicDiscovery/PySRAdapter1/setup")
start=datetime.datetime.now(datetime.timezone.utc).isoformat()
r=subprocess.run(cmd,capture_output=True)
for suffix,b in [("stdout",r.stdout),("stderr",r.stderr)]:
 with (p/(label+"."+suffix)).open("xb") as f:f.write(b)
record={"schema":"np-pysr-adapter/1/setup-step","step":label,"command":cmd,"started_at":start,"finished_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),"returncode":r.returncode,"stdout_sha256":hashlib.sha256(r.stdout).hexdigest(),"stderr_sha256":hashlib.sha256(r.stderr).hexdigest()}
with (p/(label+".json")).open("x") as f:json.dump(record,f,indent=2);f.write("\n")
print(json.dumps(record));print(r.stdout.decode(errors="replace")[-4000:]);print(r.stderr.decode(errors="replace")[-2000:])
