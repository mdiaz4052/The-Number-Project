"""Fresh-job data-only evidence validation and deterministic sealing."""
from __future__ import annotations
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import stat
import tarfile
import sys
from closure import read_json, require, write_json, digest

ROOT=Path(__file__).resolve().parents[1]
P=read_json((ROOT/'preregistration.v1.json').read_text())
REQUIRED=['run_manifest.json','identity.json','commands.ndjson','controls.json','targets.json','axioms.json','dependency_summary.json','stopping_boundaries.json','final_report.md']
REQUIRED += [f'{directory}/{target}.{suffix}' for target in ('R3','periodic') for directory,suffix in [('graphs','nodes.ndjson.gz'),('graphs','edges.ndjson.gz'),('exports','export.ndjson.gz'),('statements','txt')]]


def schema_validate(value, schema, root=None):
    """Validate precisely the JSON Schema subset used by the frozen result schema."""
    root=schema if root is None else root
    if '$ref' in schema:
        ref=root
        for part in schema['$ref'].removeprefix('#/').split('/'):ref=ref[part]
        schema_validate(value,ref,root);return
    if 'enum' in schema:require(value in schema['enum'],'schema enum')
    if 'type' in schema:
        kinds=schema['type'] if isinstance(schema['type'],list) else [schema['type']]
        actual='null' if value is None else 'boolean' if type(value) is bool else 'object' if type(value) is dict else 'array' if type(value) is list else 'string' if type(value) is str else 'number'
        require(actual in kinds,'schema type')
    if isinstance(value,dict):
        require(set(schema.get('required',[]))<=set(value),'schema required fields')
        props=schema.get('properties',{})
        if schema.get('additionalProperties') is False:require(set(value)<=set(props),'schema extra properties')
        for k in set(value)&set(props):schema_validate(value[k],props[k],root)


def inventory(root):
    result=[]
    for p in sorted(root.rglob('*')):
        mode=p.lstat().st_mode
        require(not stat.S_ISLNK(mode),'symlink forbidden: '+str(p))
        require(stat.S_ISDIR(mode) or stat.S_ISREG(mode),'nonregular input')
        rel=p.relative_to(root).as_posix()
        require('..' not in Path(rel).parts and not rel.startswith('/') and '\n' not in rel and '\\' not in rel,'unsafe path')
        if p.is_file():result.append(rel)
    require(len(result)==len(set(result)),'duplicate path')
    return result


def validate(root):
    root=Path(root); names=inventory(root)
    require(set(REQUIRED)<=set(names),'missing required files: '+str(set(REQUIRED)-set(names)))
    schema=read_json((ROOT/'schema/result.schema.json').read_text())
    for file in REQUIRED:
        if file.endswith('.json'):read_json((root/file).read_text())
    manifest=read_json((root/'run_manifest.json').read_text())
    require(manifest['outcome_blind'] is False and manifest['external']==P['external'],'manifest identity')
    require(manifest['preregistration_sha256']==digest((ROOT/'preregistration.v1.json').read_bytes()),'freeze digest')
    require(manifest['schema_sha256']==digest((ROOT/'schema/result.schema.json').read_bytes()),'schema identity')
    targets=read_json((root/'targets.json').read_text())
    require(set(targets)=={'R3','periodic'},'exact target records')
    for key,expected in zip(('R3','periodic'),P['targets']):
        t=targets[key]
        schema_validate(t,schema)
        require(t['name']==expected,'target name')
        require(t['primary_disposition'] in P['primary_dispositions'],'invalid disposition')
        require(set(t['axes'])==set(P['result_axes']),'result axes')
        for axis,value in t['axes'].items():
            require(set(value)=={'status','reason','failure_class'},'axis schema')
            require(value['status'] in schema['$defs']['axis']['properties']['status']['enum'],'axis status')
            require(value['failure_class'] is None or value['failure_class'] in P['failure_classes'],'failure class')
            require(value['status']=='PASS' or value['reason'] is not None,'unrun/failure needs reason')
        if t['primary_disposition']=='REPLAY_AND_CLOSURE_ESTABLISHED':
            require(all(t['axes'][a]['status']=='PASS' for a in P['result_axes'] if a!='package2_boundary_narrowing'),'success axes incomplete')
        ax=read_json((root/'axioms.json').read_text())[key]
        if t['axes']['axiom_closure']['status']=='PASS':
            require(ax['status']=='MEASURED' and isinstance(ax['measured_axioms'],list) and ax['agreement'] is True,'unmeasured closure success')
        for suffix in ('nodes','edges'):
            with gzip.open(root/'graphs'/(key+'.'+suffix+'.ndjson.gz'),'rt') as f:
                first=f.readline();require(first,'empty graph artifact');row=read_json(first)
                if row.get('status')=='NOT_PRODUCED':require(t['axes']['dependency_graph']['status']!='PASS','graph sentinel claimed as success')
        with gzip.open(root/'exports'/(key+'.export.ndjson.gz'),'rt') as f:
            first=f.readline();require(first,'empty export artifact');row=read_json(first)
            if row.get('status')=='NOT_PRODUCED':require(t['axes']['axiom_closure']['status']!='PASS','export sentinel claimed as success')
    boundaries=read_json((root/'stopping_boundaries.json').read_text())
    require(len(boundaries)==7 and all(set(r['targets'])=={'R3','periodic'} for r in boundaries),'seven per-target boundaries')
    ids=set()
    for line in (root/'commands.ndjson').read_text().splitlines():
        c=read_json(line);require(c['command_id'] not in ids,'duplicate command');ids.add(c['command_id'])
        require(c['exit_code'] is not None and c['start_utc'] and c['end_utc'],'incomplete command record')
        for stream in ('stdout','stderr'):
            require(c[stream] in names,'missing command log')
            require(digest((root/c[stream]).read_bytes())==c[stream+'_sha256'],'command log checksum mismatch')
    return names


def seal(root,out):
    root=Path(root);out=Path(out);out.mkdir(parents=True,exist_ok=True)
    names=validate(root)
    require('SHA256SUMS' not in names,'raw input must not supply seal')
    checksum=''.join(digest((root/n).read_bytes())+'  '+n+'\n' for n in names)
    (root/'SHA256SUMS').write_text(checksum)
    for line in checksum.splitlines():
        h,n=line.split('  ',1);require(digest((root/n).read_bytes())==h,'seal readback mismatch')
    archive=out/'external-ns-sealed.tar.gz'
    with archive.open('wb') as raw:
        with gzip.GzipFile(fileobj=raw,mode='wb',mtime=0,filename='') as z:
            with tarfile.open(fileobj=z,mode='w') as tar:
                for n in sorted(names+['SHA256SUMS']):
                    p=root/n; info=tar.gettarinfo(str(p),arcname=n)
                    info.uid=info.gid=0;info.uname=info.gname='';info.mtime=0;info.mode=0o644
                    with p.open('rb') as f:tar.addfile(info,f)
    require(archive.stat().st_size<=P['resource_limits']['sealed_compressed_bytes'],'sealed bundle cap')
    receipt={'status':'SEALED','archive':archive.name,'sha256':digest(archive.read_bytes()),'bytes':archive.stat().st_size,
        'sha256sums_sha256':digest((root/'SHA256SUMS').read_bytes()),'file_count':len(names)+1,
        'runner_code_commit':read_json((root/'run_manifest.json').read_text())['runner_code_commit'],
        'sealing_method':'fresh hosted job; data-only validator from immutable runner commit; no downloaded content executed'}
    write_json(out/'seal_receipt.json',receipt)
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['validate','seal']);ap.add_argument('root');ap.add_argument('output',nargs='?');a=ap.parse_args()
    if a.mode=='validate':print('validated',len(validate(a.root)),'files')
    else:seal(a.root,a.output)
