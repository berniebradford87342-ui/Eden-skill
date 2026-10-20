"""Verified TLS curl transport. Credentials are provided via stdin, never argv."""
import json,subprocess
from urllib.parse import urlparse
def post_json(url,body,headers,timeout=30):
 if urlparse(url).scheme!='https' or urlparse(url).hostname!='redfox.hk':
  raise ValueError('Only documented redfox.hk HTTPS endpoints are allowed')
 config=['url = '+json.dumps(url),'request = "POST"','header = "Content-Type: application/json"']
 for k,v in (headers or {}).items():
  if '\r' in str(v) or '\n' in str(v): raise ValueError('Invalid header')
  config.append('header = '+json.dumps(k+': '+v))
 config.append('data = '+json.dumps(json.dumps(body,ensure_ascii=False),ensure_ascii=False))
 proc=subprocess.run(['curl','--silent','--show-error','--fail-with-body','--max-time',str(timeout),'--config','-'],input='\n'.join(config),text=True,capture_output=True)
 if proc.returncode: raise RuntimeError('curl exit '+str(proc.returncode)+': '+proc.stderr[:500])
 return json.loads(proc.stdout)
