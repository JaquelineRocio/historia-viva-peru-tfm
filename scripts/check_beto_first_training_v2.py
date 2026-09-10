"""Meaningful local checks, without a complete BETO fine-tuning run."""
import tempfile
from types import SimpleNamespace
from run_beto_first_training_v2 import *

def main():
    import torch
    from transformers import BertConfig,BertForSequenceClassification,AutoModelForSequenceClassification,AutoTokenizer,set_seed
    from beto_effective_batch_loss import accumulation_batches
    torch.set_num_threads(4)
    checks=[]
    train=[{'label':l,'family_id':'train','text_sha256':str(i),'training_eligible':True,'role':'historical_train'} for i,l in enumerate(LABELS)]
    val=[{**train[0],'family_id':'val','text_sha256':'val'}]
    validate(train,val)
    for name,tr,va in [('missing_train',[],val),('missing_val',train,[]),('missing_class',train[:-1],val),('family_leak',train,[{**val[0],'family_id':'train'}]),('text_leak',train,[{**val[0],'text_sha256':'0'}]),('ineligible',train,[{**val[0],'training_eligible':False}])]:
        try:validate(tr,va)
        except ValueError:checks.append(name+' rejected')
        else:raise AssertionError(name)
    assert metrics(val,[LABELS[0]])['f1_macro']==1/7
    assert len(metrics(val,[LABELS[0]])['per_class'])==7
    checks.append('Seven explicit metric labels even with one supported class')
    loss_checks=[]
    for targets in [[0,0,1,1,2,2],[0,1,2,0,2,1,0,0,2,1,2]]:
        y=torch.tensor(targets);torch.manual_seed(42)
        logits=torch.randn(len(y),3,dtype=torch.float64,requires_grad=True)
        ref=logits.detach().clone().requires_grad_();w=torch.tensor([.3,2.,5.],dtype=torch.float64)
        dl=torch.utils.data.DataLoader(torch.utils.data.TensorDataset(torch.arange(len(y)),y),batch_size=2)
        accum=0.
        for _,batch,den in accumulation_batches(dl,4,w):
            loss=torch.nn.functional.cross_entropy(logits[batch[0]],batch[-1],weight=w,reduction='sum')/den
            accum+=loss.item();loss.backward()
        full=0.
        for start in range(0,len(y),8):
            loss=torch.nn.functional.cross_entropy(ref[start:start+8],y[start:start+8],weight=w)
            full+=loss.item();loss.backward()
        torch.testing.assert_close(logits.grad,ref.grad,rtol=1e-12,atol=1e-12)
        assert abs(accum-full)<1e-12
        loss_checks.append({'n':len(y),'accumulated_loss':accum,'full_batch_loss':full,'max_gradient_absolute_error':(logits.grad-ref.grad).abs().max().item(),'partial_groups_tested':True})
    config=BertConfig(vocab_size=31,hidden_size=16,num_hidden_layers=1,num_attention_heads=2,intermediate_size=32,num_labels=7,id2label=dict(enumerate(LABELS)),label2id=dict(zip(LABELS,range(7))))
    set_seed(42);model=BertForSequenceClassification(config).eval()
    set_seed(42);other=BertForSequenceClassification(config).eval()
    torch.testing.assert_close(model.classifier.weight,other.classifier.weight,rtol=0,atol=0)
    mapping(model.config)
    try:mapping(SimpleNamespace(label2id=dict(zip(reversed(LABELS),range(7))),id2label=dict(enumerate(LABELS))))
    except ValueError:checks.append('Permuted checkpoint labels rejected')
    else:raise AssertionError('mapping check')
    temp=Path(tempfile.mkdtemp(prefix='beto-v2-preflight-',dir=ROOT/'outputs'))
    model.save_pretrained(temp,safe_serialization=True)
    reload=AutoModelForSequenceClassification.from_pretrained(temp,local_files_only=True).eval();mapping(reload.config)
    with torch.inference_mode():
        inputs={'input_ids':torch.tensor([[1,2,3,0]]),'attention_mask':torch.tensor([[1,1,1,0]])}
        torch.testing.assert_close(model(**inputs).logits,reload(**inputs).logits,rtol=1e-5,atol=1e-8)
    tok=AutoTokenizer.from_pretrained(BASE,revision=REV,local_files_only=True)
    long='La soberanía de la nación. '*600
    batches,keys=loader([{'text':'Perú.','label':LABELS[0]},{'text':long,'label':LABELS[1]}],tok,384)
    b=next(iter(batches));assert b[0].shape==(2,384)
    assert b[keys.index('attention_mask')][0].sum()<384 and b[keys.index('attention_mask')][1].sum()==384
    assert b[0][1,-1]==tok.sep_token_id
    checks += ['Seed before initialization reproducibly fixes classifier head','Tiny BERT safetensors save/reload logits within1e-8 absolute /1e-5 relative and exact mappings; attention kernels can round differently','Explicit fixed padding and truncation at384 with SEP preserved']
    # Test RNG restoration used by the epoch resume protocol.
    set_seed(42);rng=torch.get_rng_state();expected=torch.rand(5);torch.set_rng_state(rng)
    torch.testing.assert_close(torch.rand(5),expected,rtol=0,atol=0)
    save(ART/'preflight.json',{'status':'passed','checks':checks,'weighted_accumulation':loss_checks,'fixture':'tiny randomly initialized BERT; zero full BETO trainings','fixture_directory':temp.relative_to(ROOT).as_posix(),'resume_limit':'epoch-boundary state serialization implemented; end-to-end interrupted BETO trajectory not separately trained to preserve six-run budget'})
    save(ART/'guide-compatibility.json',{'historical_guide':{'path':'docs/guia-etiquetado-1780-1842.md','sha256':filehash(ROOT/'docs/guia-etiquetado-1780-1842.md')},'v2_guide':{'path':'docs/beto-v2/guia-etiquetado-v2.md','sha256':filehash(ROOT/'docs/beto-v2/guia-etiquetado-v2.md')},'compatible_core':['Same seven semantic labels and1780–1842 scope','Dominant historical argument rather than keyword voting','Ambiguous is review state, not an eighth label','Operations versus diplomacy and projects versus implemented institutions retained'], 'conflicts':[{'rule':'historical no_relevante includes extraction noise; v2 treats undecidable extraction as pending','resolution':'Use reviewed-v4 after documented quarantine; unresolved source identity removed; no automatic conversion of poor text to negative. Remaining historical OCR quality inherited and explicitly limited.'},{'rule':'v2 explicitly distinguishes substantive historiography from exclusively academic discussion','resolution':'Reuse existing v4 adjudication that implements this boundary, including snapshot49 relabel; preserve old decisions in originals-and-decisions.json. No relabel using current predictions.'},{'rule':'historical120–250 words versus v2 complete paragraphs/sentences','resolution':'Allow v2 reviewed paragraph units per user request; preserve exact text and token lengths, note length/format distribution confound.'},{'rule':'ideal historical human review vs actual AI reviews; v2 two isolated AI passes','resolution':'Keep annotation_origin per row; no assertion of uniform human gold or independent annotator accuracy.'}], 'selected_historical_version':'outputs/corpus-snapshot-v4/reviewed-export.json original train only; existing reviewed corrections and six quarantines preserved','global_semantic_readjudication':False,'limits':'Guide compatibility is operational, not proof every inherited historical label is correct. No18-snapshot union.'})
    print('All preflight checks passed')

if __name__=='__main__':main()
