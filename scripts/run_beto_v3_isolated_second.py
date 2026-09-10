"""Pass exact UTF-8 bytes to authorized ChatGPT-authenticated Codex CLI."""
import json, subprocess, shutil, time, hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'outputs/beto-v3/admission-01/isolated-second'
def main():
    prompt=(P/'prompt.txt').read_bytes();json.loads(prompt.decode('utf-8'))
    target=P/'response-utf8.json'
    assert not target.exists(), 'Reuse saved review, do not overwrite it'
    command=[shutil.which('codex'),'exec','--ephemeral','--ignore-user-config','--skip-git-repo-check',
             '--sandbox','read-only','--color','never','--json','-C',str(P),'-o',str(target),'-']
    start=time.perf_counter()
    with (P/'events-utf8.jsonl').open('wb') as out,(P/'stderr-utf8.log').open('wb') as err:
        result=subprocess.run(command,input=prompt,stdout=out,stderr=err,timeout=900)
    receipt={'command':command,'prompt_sha256':hashlib.sha256(prompt).hexdigest(),'stdin_encoding':'utf-8 bytes',
             'exit_code':result.returncode,'wall_seconds':time.perf_counter()-start,'authentication':'existing ChatGPT subscription, login status verified',
             'user_authorization':'Explicit asynchronous approval for this destination and these 30 public-source units',
             'tools_requested':False,'history_passed':False,'model':'CLI default; provider model ID not observed','services_paid_USD':0}
    (P/'receipt-utf8.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(receipt,ensure_ascii=True));raise SystemExit(result.returncode)
if __name__=='__main__':main()
