"""Pre-fit metadata correction, preserving the initial frozen draft."""
from run_beto_first_training_v2 import *
assert not (OUT/'runs').exists(), 'No amendment after any fit'
p=read(ART/'protocol.json')
save(ART/'protocol-initial-draft.json',p)
p['fold_rule']='GroupKFold(3) on historical families by row count; already-linked new rows inherit family fold; new-only families assigned decreasing size to fold with fewest AI rows (fold ID tie). No labels or predictions used for assignment. All train classes validated, no performance-based retries.'
p['pre_fit_amendment']='Correct fold algorithm description to match actual frozen row IDs. Initial all-row GroupKFold preparation rejected because one validation had no new AI examples; no classifier was fitted.'
p['input_hashes']['scripts/freeze_beto_first_training_v2.py']=filehash(ROOT/'scripts/freeze_beto_first_training_v2.py')
p['input_hashes']['scripts/check_beto_first_training_v2.py']=filehash(ROOT/'scripts/check_beto_first_training_v2.py')
(ART/'protocol.json').write_text(json.dumps(p,ensure_ascii=False,indent=2),encoding='utf-8')
print('Metadata corrected before any fit; initial draft preserved')
