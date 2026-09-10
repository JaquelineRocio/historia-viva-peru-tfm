"""Phase A only: inference of retained seed-42 A/B training curves, no fitting."""
import gc
import json
import time
from pathlib import Path

import run_beto_first_training_v2 as b
from prepare_beto_v3 import ART, OUT, ROOT, read, sha, write

def main():
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    if not torch.cuda.is_available():
        raise RuntimeError('CUDA unavailable for local checkpoint inference')
    torch.set_num_threads(4)
    protocol = read(ROOT/'artifacts/beto-v2/first-training/protocol.json')
    byid = {r['segment_id']:r for r in read(ROOT/'outputs/beto-v2/first-training/canonical-dataset.json')['items']}
    out = OUT/'prior-train-inference'
    records = []
    for fold in protocol['folds']:
        for condition in ['A','B']:
            run = ROOT/'outputs/beto-v2/first-training/runs'/(fold['id']+'-'+condition)
            rows = [byid[i] for i in fold['train_'+condition]]
            result = read(run/'result.json')
            for h in result['history']:
                epoch = h['epoch']
                dest = out/(run.name+f'-epoch-{epoch}.json')
                if dest.exists():
                    record = read(dest)
                    assert record['rows_hash'] == b.fingerprint(rows)
                    records.append(record)
                    continue
                checkpoint = run/f'checkpoint-{epoch}'
                started = time.perf_counter()
                # Resume states cover non-best epochs without creating or training a model.
                model_path = checkpoint if checkpoint.exists() else run/f"checkpoint-{result['best_epoch']}"
                model = AutoModelForSequenceClassification.from_pretrained(model_path,local_files_only=True).cuda()
                tok = AutoTokenizer.from_pretrained(model_path,local_files_only=True)
                state_path = run/f'resume-epoch-{epoch}.pt'
                if not checkpoint.exists():
                    state = torch.load(state_path,map_location='cpu',weights_only=False)
                    assert state['epoch'] == epoch
                    model.load_state_dict(state['model'])
                    del state
                batches, keys = b.loader(rows,tok,384)
                predictions = b.predict(model,batches,keys)
                record = {'run':run.name,'epoch':epoch,'rows_hash':b.fingerprint(rows),
                    'checkpoint':str(model_path.relative_to(ROOT)),
                    'weights_source':str((checkpoint/'model.safetensors' if checkpoint.exists() else state_path).relative_to(ROOT)),
                    'weighted_train_loss':h['weighted_train_loss'], 'train_metrics_eval':b.metrics(rows,predictions),
                    'val_metrics':h['metrics']['combined'],'seconds':time.perf_counter()-started,
                    'predictions':[{'segment_id':r['segment_id'],'truth':r['label'],'predicted':p} for r,p in zip(rows,predictions)]}
                write(dest,record)
                records.append(record)
                print(run.name,epoch,round(record['train_metrics_eval']['f1_macro'],6),flush=True)
                del model,batches
                gc.collect()
                torch.cuda.empty_cache()
    write(ART/'prior-train-curves.json', [{k:v for k,v in r.items() if k!='predictions'} for r in records])

if __name__ == '__main__':
    main()
