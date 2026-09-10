"""Identity and seed contract checks without any additional BETO fit."""
import ast
import copy
from run_beto_first_training_v2 import *

def main():
    import torch
    from transformers import BertConfig,BertForSequenceClassification,set_seed
    p,byid=inputs();checks=[]
    original=(ROOT/'artifacts/beto-v2/stability/runner-seed42-original.py').read_text(encoding='utf-8')
    expected=original.replace('    set_seed(42);torch.set_num_threads(4)',
        "    seed=protocol.get('execution',{}).get('seed',42)\n    set_seed(seed);torch.set_num_threads(4)").replace(
        "loader(train,tok,protocol['max_length'],True,42+epoch)","loader(train,tok,protocol['max_length'],True,seed+epoch)")
    def fn(src,name):return ast.dump(next(x for x in ast.parse(src).body if isinstance(x,ast.FunctionDef) and x.name==name))
    current=(ROOT/'artifacts/beto-v2/stability/runner-stability-original.py').read_text(encoding='utf-8')
    for name in ('train_run','loader','predict','metrics','subsets','validate','mapping'):
        assert fn(expected,name)==fn(current,name),name
    checks.append('Training/evaluation AST identical to original except seed initialization and seed+epoch shuffle')
    assert len(byid)==591
    fold=p['folds'][0];val=[byid[i] for i in fold['validation']];dest=OUT/'runs'/(fold['id']+'-A')
    verify_result(dest,p,val)
    for name,config,rows in [('wrong_seed',{**p,'execution':{'seed':43}},val),
                             ('validation_reordered',p,list(reversed(val))),
                             ('changed_label',p,[{**val[0],'label':LABELS[(LABELS.index(val[0]['label'])+1)%7]},*val[1:]])]:
        try:verify_result(dest,config,rows)
        except ValueError:checks.append(name+' rejected')
        else:raise AssertionError(name)
    torch.set_num_threads(2)
    config=BertConfig(vocab_size=31,hidden_size=16,num_hidden_layers=1,num_attention_heads=2,intermediate_size=32,num_labels=7)
    heads={}
    for seed in (42,43,44):
        set_seed(seed);heads[seed]=BertForSequenceClassification(config).classifier.weight.detach().clone()
        set_seed(seed);assert torch.equal(heads[seed],BertForSequenceClassification(config).classifier.weight)
    assert not torch.equal(heads[42],heads[43]) and not torch.equal(heads[43],heads[44])
    checks.append('Tiny CPU BERT heads repeat within seed and differ across seeds; zero BETO fits')
    class Tokenizer:
        def __call__(self,texts,**kwargs):return {'input_ids':torch.tensor([[int(t)] for t in texts])}
    rows=[{'text':str(i),'label':LABELS[i%7]} for i in range(21)]
    def order(seed):return torch.cat([b[0].flatten() for b in loader(rows,Tokenizer(),384,True,seed)[0]]).tolist()
    for seed in (42,43,44):
        assert order(seed+1)==order(seed+1) and order(seed+1)!=order(seed+2)
    checks.append('Loader shuffle repeats for seed+epoch and changes on adjacent epoch')
    save(ROOT/'artifacts/beto-v2/stability/checks.json',{'checks':checks,'new_beto_fits':0})
    print('\n'.join(checks))

if __name__=='__main__':main()
