#!/usr/bin/env python3
"""Manage one collection version and build per-Skill/full ZIP downloads. Does not publish."""
import argparse,hashlib,json,pathlib,re,zipfile
ROOT=pathlib.Path(__file__).resolve().parent
EXCLUDE={'.git','__pycache__','dist','.venv','.DS_Store'}
def included(p):
    return p.is_file() and not any(x in EXCLUDE for x in p.relative_to(ROOT).parts) and p.suffix!='.pyc' and p.name!='checksums.json'
def refresh():
    hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(ROOT.rglob('*')) if included(p)}
    (ROOT/'checksums.json').write_text(json.dumps(hashes,ensure_ascii=False,indent=2)+'\n')
    return hashes
def main():
    p=argparse.ArgumentParser();p.add_argument('--set-version');p.add_argument('--build',action='store_true');p.add_argument('--refresh',action='store_true');a=p.parse_args()
    current=(ROOT/'VERSION').read_text().strip()
    if a.set_version:
        if not re.fullmatch(r'\d+\.\d+\.\d+',a.set_version):raise SystemExit('Use MAJOR.MINOR.PATCH')
        if tuple(map(int,a.set_version.split('.')))<=tuple(map(int,current.split('.'))):raise SystemExit('New release version must increase')
        current=a.set_version;(ROOT/'VERSION').write_text(current+'\n')
        for f in [ROOT/'catalog.json',ROOT/'skills/eden-skill/references/catalog.json']:
            d=json.loads(f.read_text());d['version']=current;f.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
    hashes=refresh()
    if a.build:
        out=ROOT/'dist';out.mkdir(exist_ok=True)
        with zipfile.ZipFile(out/f'Eden-skill-v{current}.zip','w',zipfile.ZIP_DEFLATED) as z:
            for name in [*hashes,'checksums.json']:z.write(ROOT/name,'Eden-skill/'+name)
        for skill in (ROOT/'skills').iterdir():
            if not skill.is_dir():continue
            with zipfile.ZipFile(out/f'skill-{skill.name}-v{current}.zip','w',zipfile.ZIP_DEFLATED) as z:
                for f in skill.rglob('*'):
                    if included(f):z.write(f,str(f.relative_to(ROOT/'skills')))
                z.writestr(skill.name+'/EDEN_VERSION',current+'\n')
    print(json.dumps({'version':current,'checked_files':len(hashes),'built':a.build}))
if __name__=='__main__':main()
