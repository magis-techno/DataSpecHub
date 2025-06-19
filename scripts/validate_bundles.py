import yaml, semver, pathlib, sys, json
root = pathlib.Path(__file__).resolve().parent.parent
aliases = yaml.safe_load((root/'taxonomy/channel_taxonomy.yaml').read_text())['aliases']
def canon(c): return aliases.get(c, c)
def load(p): return yaml.safe_load(open(p,encoding='utf-8'))
def pick_version(chan_dir, constraint):
    releases=[]
    for y in chan_dir.glob('release-*.yaml'):
        meta=load(y)['meta']; v=meta['version']
        releases.append(v)
    releases.sort(key=semver.VersionInfo.parse)
    for v in reversed(releases):
        if semver.match(v, constraint):
            return v
    return None
def validate_bundle(bpath):
    data=load(bpath)
    defaults=data.get('defaults',{})
    errors=[]
    lock={}
    for ent in data['channels']:
        chan=canon(ent['channel'])
        cdir=root/'channels'/chan
        if not cdir.exists():
            errors.append(f'{bpath}: channel {chan} dir missing'); continue
        ver_constraint=ent.get('version','*')
        sel=pick_version(cdir,ver_constraint) or None
        on_missing=ent.get('on_missing', defaults.get('on_missing','ignore'))
        if sel is None and on_missing=='fail':
            errors.append(f'{bpath}: {chan} satisfying {ver_constraint} not found and on_missing=fail')
        lock[chan]=sel
    if errors: return errors
    lock_path=bpath.with_suffix('.lock.json')
    lock_path.write_text(json.dumps(lock,indent=2))
    return []
errs=[]
for bp in (root/'bundles').rglob('bundle-*.yaml'):
    errs+=validate_bundle(bp)
if errs:
    print('\n'.join(errs)); sys.exit(1)
