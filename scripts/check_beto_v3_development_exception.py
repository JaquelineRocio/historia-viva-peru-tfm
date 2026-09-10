"""Exercise narrow exception and reject violations against real frozen inputs."""
from copy import deepcopy
from unittest.mock import patch
import run_beto_phase_c_v3 as r

def main():
    freeze, rows=r.frozen_inputs()
    contract_path=(r.ROOT/freeze['development_contract']['path']).resolve()
    original_read=r.read
    contract=original_read(contract_path)
    for key,value in [('scope',['C','D','G']),('S_closed',False),
                       ('minimum_overrides',{'contexto_colonial_antecedentes':22}),
                       ('original_budget',{}),('original_success',{}),
                       ('reference_coverage',{'V':.89})]:
        changed=deepcopy(contract);changed[key]=value
        def fake_read(path):
            return changed if path.resolve()==contract_path else original_read(path)
        with patch.object(r,'read',side_effect=fake_read):
            try:r.frozen_inputs()
            except ValueError:pass
            else:raise AssertionError('Invalid exception accepted: '+key)
    vpath=(r.ROOT/freeze['datasets']['V']['path']).resolve()
    original_v=original_read(vpath)
    # Removing one colonial reference violates the scoped minimum of 23.
    changed=deepcopy(original_v)
    item=next(x for x in changed['items'] if x['accepted_label']=='contexto_colonial_antecedentes')
    changed['items'].remove(item)
    with patch.object(r,'read',side_effect=lambda p:changed if p.resolve()==vpath else original_read(p)):
        try:r.frozen_inputs()
        except ValueError as e:assert 'coverage' in str(e)
        else:raise AssertionError('22 colonial references accepted')
    print('PASS: frozen 23+23 accepted; scope, S, quotas, budget, success and coverage violations rejected. No training or S content.')

if __name__=='__main__':main()
