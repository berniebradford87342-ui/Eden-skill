#!/usr/bin/env python3
"""Install selected Skills from a checked-out release; preserve existing directories by default."""
import argparse,datetime,hashlib,json,os,pathlib,shutil,tempfile
ROOT=pathlib.Path(__file__).resolve().parent

def files(root):
    return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--list',action='store_true');p.add_argument('--skill',action='append',default=[])
    p.add_argument('--all',action='store_true',help='Install active Skills; experimental tools remain opt-in')
    p.add_argument('--target',type=pathlib.Path,default=pathlib.Path(os.environ.get('CODEX_HOME',str(pathlib.Path.home()/'.codex')))/'skills')
    p.add_argument('--upgrade',action='store_true',help='Back up and replace requested Skill directories; never touches Obsidian')
    a=p.parse_args();catalog=json.loads((ROOT/'catalog.json').read_text());version=(ROOT/'VERSION').read_text().strip()
    assert version==catalog['version'],'Version mismatch'
    expected=json.loads((ROOT/'checksums.json').read_text())
    for rel,digest in expected.items():
        f=ROOT/rel
        if not f.is_file() or hashlib.sha256(f.read_bytes()).hexdigest()!=digest:raise SystemExit('Release file changed or missing: '+rel)
    entries={x['name']:x for x in catalog['skills']}
    if a.list:
        for x in entries.values():print(x['name']+' | '+x['status']+' | '+x['role'])
        return
    requested=a.skill+([n for n,x in entries.items() if x['status']=='active'] if a.all else [])
    if not requested:requested=['eden-skill']
    chosen={'eden-skill'}
    def add(name):
        if name not in entries:raise SystemExit('Unknown Skill: '+name)
        if name in chosen:return
        chosen.add(name)
        for dep in entries[name]['dependencies']:add(dep)
    for n in requested:add(n)
    target=a.target.expanduser().resolve()
    if target==ROOT/'skills' or target.is_relative_to(ROOT/'skills'):raise SystemExit('Cannot install into the source Skills tree')
    target.mkdir(parents=True,exist_ok=True)
    stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f');result=[]
    for name in sorted(chosen):
        src=ROOT/'skills'/name;dst=target/name
        if dst.exists() and not a.upgrade:result.append({'skill':name,'result':'kept-existing'});continue
        backup=None
        if dst.exists():
            backup=target/'.eden-backups'/stamp/name;backup.parent.mkdir(parents=True,exist_ok=True);shutil.copytree(dst,backup)
        staging=pathlib.Path(tempfile.mkdtemp(prefix='.eden-install-',dir=target))
        try:
            new=staging/name;shutil.copytree(src,new)
            if name=='eden-skill':(new/'SOURCE.json').write_text(json.dumps({'repository':catalog['repository'],'version':version,'checkout':str(ROOT)},ensure_ascii=False,indent=2)+'\n')
            (new/'EDEN_VERSION').write_text(version+'\n')
            if dst.exists():shutil.rmtree(dst)
            shutil.move(str(new),dst)
        except Exception:
            if backup and not dst.exists():shutil.copytree(backup,dst)
            raise
        finally:shutil.rmtree(staging)
        result.append({'skill':name,'result':'upgraded' if backup else 'installed','backup':str(backup) if backup else None})
    print(json.dumps({'version':version,'target':str(target),'skills':result},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
