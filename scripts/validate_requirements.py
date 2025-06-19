import yaml, sys, semver, pathlib, os, json
root = pathlib.Path(__file__).resolve().parent.parent
def load(p): return yaml.safe_load(pathlib.Path(p).read_text())
taxonomy = load(root/'taxonomy/channel_taxonomy.yaml')
aliases = taxonomy.get('aliases', {})
def canon(c): return aliases.get(c, c)
def check_consumer(path):
    data=load(path)
    errors=[]
    for req in data.get('requirements',[]):
        chan=canon(req['channel'])
        chan_dir=root/f'channels/{chan}'
        if not chan_dir.exists():
            errors.append(f'{path}: channel {chan} not found')
    return errors
errs=[]
for cf in (root/'consumers').glob('*.yaml'):
    errs+=check_consumer(cf)
if errs:
    print('\n'.join(errs))
    sys.exit(1)
