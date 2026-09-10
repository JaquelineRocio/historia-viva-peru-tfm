"""Inference-only diagnostic of the interrupted/replayed epoch; never selects a model."""
from run_beto_class_weights_v2 import *

def main():
    import torch
    from transformers import AutoTokenizer,AutoModelForSequenceClassification
    torch.set_num_threads(4)
    p=read(ART/'protocol.json');rows=read(OUT/'canonical-dataset.json')['items'];byid={r['segment_id']:r for r in rows}
    fold=p['folds'][0];val=[byid[i] for i in fold['validation']]
    dest=WOUT/'seed-43/fold-1-B_weights_A'
    from safetensors import safe_open
    old=dest/'interrupted-after-epoch-1/checkpoint-2/model.safetensors';new=dest/'checkpoint-2/model.safetensors'
    differences=[]
    with safe_open(str(old),framework='pt',device='cpu') as a,safe_open(str(new),framework='pt',device='cpu') as b:
        assert list(a.keys())==list(b.keys())
        for key in a.keys():
            x=a.get_tensor(key);y=b.get_tensor(key)
            if not torch.equal(x,y):differences.append({'tensor':key,'max_abs':float((x-y).abs().max())})
        del x,y
    before=filehash(old);after=filehash(new)
    persist(WART/'resume-check.json',{'saved_epoch':2,'before_interruption_sha256':before,'after_resume_sha256':after,'identical':before==after,'different_tensors':len(differences),'max_abs_difference':max([d['max_abs'] for d in differences],default=0),'tensors_identical':not differences,'tensor_differences':differences})
    results={}
    for name,path in [('interrupted',dest/'interrupted-after-epoch-1/checkpoint-2'),('resumed',dest/'checkpoint-2')]:
        tok=AutoTokenizer.from_pretrained(path,local_files_only=True)
        model=AutoModelForSequenceClassification.from_pretrained(path,local_files_only=True,use_safetensors=True).cuda()
        batches,keys=loader(val,tok,384);pred=predict(model,batches,keys)
        results[name]={'checkpoint_sha256':filehash(path/'model.safetensors'),'metrics':subsets(val,pred),'predictions':[{'segment_id':r['segment_id'],'truth':r['label'],'predicted':v} for r,v in zip(val,pred)]}
        del model;gc.collect();torch.cuda.empty_cache()
    result=read(dest/'result.json')
    assert results['resumed']['metrics']==result['history'][1]['metrics']
    changes=[{'segment_id':a['segment_id'],'truth':a['truth'],'interrupted':a['predicted'],'resumed':b['predicted']} for a,b in zip(results['interrupted']['predictions'],results['resumed']['predictions']) if a['predicted']!=b['predicted']]
    output={'new_training_runs':0,'purpose':'diagnostic only; epoch/checkpoint selection unchanged','epoch':2,'changed_prediction_count':len(changes),'changes':changes,'results':results,'script_sha256':filehash(__file__)}
    persist(WART/'resume-predictions-check.json',output)
    print(json.dumps({'changed_prediction_count':len(changes),'F1':{k:v['metrics']['combined']['f1_macro'] for k,v in results.items()}},indent=2))

if __name__=='__main__':main()
