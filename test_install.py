import json,pathlib,subprocess,sys,tempfile,unittest,shutil,zipfile
ROOT=pathlib.Path(__file__).resolve().parent
class InstallationTest(unittest.TestCase):
 def test_select_dependencies_preserve_and_backup(self):
  with tempfile.TemporaryDirectory() as temp:
   target=pathlib.Path(temp)/'skills'
   def run(*extra):
    r=subprocess.run([sys.executable,str(ROOT/'install.py'),'--skill','eden-topic-research','--target',str(target),*extra],capture_output=True,text=True)
    self.assertEqual(r.returncode,0,r.stderr);return json.loads(r.stdout)
   run();self.assertEqual(len([p for p in target.iterdir() if p.is_dir()]),6)
   self.assertFalse((target/'xiaohongshu-similar-account').exists())
   note=target/'eden-topic-research/SKILL.md';note.write_text(note.read_text()+'\n用户本地修改\n');before=note.read_bytes()
   run();self.assertEqual(note.read_bytes(),before)
   result=run('--upgrade');saved=next(x['backup'] for x in result['skills'] if x['skill']=='eden-topic-research')
   self.assertEqual((pathlib.Path(saved)/'SKILL.md').read_bytes(),before)
   self.assertEqual((target/'eden-topic-research/EDEN_VERSION').read_text().strip(),(ROOT/'VERSION').read_text().strip())
 def test_complete_bundle_and_hub_have_distinct_names(self):
  with tempfile.TemporaryDirectory() as temp:
   source=pathlib.Path(temp)/'source';shutil.copytree(ROOT,source,ignore=shutil.ignore_patterns('dist','__pycache__','.git'))
   r=subprocess.run([sys.executable,str(source/'release.py'),'--build'],capture_output=True,text=True)
   self.assertEqual(r.returncode,0,r.stderr)
   version=(source/'VERSION').read_text().strip();archives=list((source/'dist').glob('*.zip'))
   self.assertEqual(len(archives),8);self.assertEqual(len({p.name.lower() for p in archives}),8)
   with zipfile.ZipFile(source/'dist'/f'Eden-skill-v{version}.zip') as z:
    expected=set(json.loads((source/'checksums.json').read_text()))|{'checksums.json'}
    self.assertEqual(set(z.namelist()),{'Eden-skill/'+p for p in expected})
if __name__=='__main__':unittest.main()
