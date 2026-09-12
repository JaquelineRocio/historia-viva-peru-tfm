"""Create a separate manually uploaded multitask Colab. Never run training."""
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT / 'artifacts/beto-v3/colab-hierarchical/beto_jerarquico_colab.ipynb'
OUT = ROOT / 'artifacts/beto-v3/colab-multitask'
source = json.loads(OLD.read_text(encoding='utf-8'))
cells = []

def old(i):
    return ''.join(source['cells'][i]['source'])

def add(s, kind='code'):
    c = {'cell_type': kind, 'metadata': {}, 'id': f'multitask-{len(cells):02d}', 'source': s.strip()+'\n'}
    if kind == 'code':
        ast.parse(s.strip())
        c.update(execution_count=None, outputs=[])
    cells.append(c)

add('''# BETO multitarea — encoder compartido
Notebook nuevo e independiente del baseline plano y del jerárquico.
Activa GPU en Colab y ejecuta todas las celdas. Sube manualmente
`train-experimental.jsonl` (758) y `dev.jsonl` (160), campos `id`, `text`, `label`.
Puedes subir también `flat_beto_results.json` y `hierarchical_beto_results.json`.

Primero usa `RUN_SMOKE_TEST = True`; después cambia a `False` y ejecuta las celdas
desde configuración para las tres semillas. El smoke test no produce resultados científicos.
Un encoder BETO base, dos cabezas, pérdida 1:1 y soft gating. Solo macro-F1 final DEV
selecciona el checkpoint; DEV expuesto no constituye prueba independiente ni gold experto.
No se accede a V/S. No se ejecutó entrenamiento durante la preparación del notebook.
Base y tokenizer fijados a la revisión y hashes comprobados del baseline y jerárquico.
El baseline usa padding fijo y este encargo exige padding dinámico: queda registrado.
''', 'markdown')
add(old(1))
add(old(2).replace('AutoModelForSequenceClassification', 'AutoModel').replace(', time', '').replace(', zipfile', '').replace('from tqdm.auto import tqdm\n', ''))
add(old(3).replace('# 4. CONFIG — mismo protocolo para todas las semillas y ambos modelos', '# Configuración fija de un encoder compartido por semilla') + '\nRUN_SMOKE_TEST = True\n')
add(old(4))
add(old(5))
add(old(6))
add(old(8))
add(old(7))
add(old(9).split('def make_loader')[0] + '''
def make_loader(rows,tokens,shuffle,seed,indices=None):
    if indices is None: indices=range(len(rows))
    items=[{**tokens[i], 'labels':FINAL_TO_ID[rows[i]['label']]} for i in indices]
    return torch.utils.data.DataLoader(items,batch_size=MICRO_BATCH_SIZE,shuffle=shuffle,
        generator=torch.Generator().manual_seed(seed),num_workers=0,collate_fn=collator)

train_y=torch.tensor([FINAL_TO_ID[r['label']] for r in train_rows],device=DEVICE)
FINAL_TO_B=torch.tensor([B_TO_ID.get(l,-100) for l in FINAL_LABELS],device=DEVICE)
def balanced_weights(y,k):
    counts=torch.bincount(y,minlength=k)
    assert bool((counts>0).all())
    return len(y)/(k*counts.float())
weights_A=balanced_weights((train_y!=NR_ID).long(),2)
weights_B=balanced_weights(FINAL_TO_B[train_y[train_y!=NR_ID]],6)
print('Pesos A:',weights_A.tolist(),'Pesos B:',weights_B.tolist())
''')
add('''# Un encoder y dos cabezas sobre el mismo CLS
class MultitaskBETO(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.encoder=AutoModel.from_pretrained(BASE_PATH,local_files_only=True,use_safetensors=False,add_pooling_layer=False)
        h=self.encoder.config.hidden_size
        self.head_a=torch.nn.Sequential(torch.nn.Dropout(0.1),torch.nn.Linear(h,2))
        self.head_b=torch.nn.Sequential(torch.nn.Dropout(0.1),torch.nn.Linear(h,6))
        self.encoder.gradient_checkpointing_enable()
    def forward(self,**inputs):
        cls=self.encoder(**inputs).last_hidden_state[:,0,:]
        return self.head_a(cls),self.head_b(cls)

def loss_numerators(a,b,y):
    mask=y!=NR_ID  # Exclusivamente referencia real; nunca predicción de A.
    rel=torch.nn.functional.cross_entropy(a.float(),mask.long(),weight=weights_A,reduction='sum')
    hist=(torch.nn.functional.cross_entropy(b[mask].float(),FINAL_TO_B[y[mask]],
           weight=weights_B,reduction='sum') if bool(mask.any()) else b.float().sum()*0.0)
    return rel,hist

def loss_denominators(y):
    mask=y!=NR_ID
    return weights_A[mask.long()].sum(),weights_B[FINAL_TO_B[y[mask]]].sum()
''')
add(old(10).split('def evaluate')[0] + old(15))
add('''def evaluate(model,loader):
    model.eval(); aa=[];bb=[];yy=[]
    with torch.inference_mode():
        for batch in loader:
            yy.extend(batch['labels'].tolist())
            a,b=model(**{k:v.to(DEVICE) for k,v in batch.items() if k!='labels'})
            aa.extend(a.float().softmax(-1).cpu().tolist())
            bb.extend(b.float().softmax(-1).cpu().tolist())
    pa=np.asarray(aa);pb=np.asarray(bb);y=np.asarray(yy);p=soft_gate(pa,pb)
    mask=y!=NR_ID
    hist_y=np.asarray([B_TO_ID[FINAL_LABELS[i]] for i in y[mask]])
    return {'metrics':metrics(y,p,FINAL_LABELS),
            'head_a':metrics(mask.astype(int),pa,A_LABELS),
            'head_b':metrics(hist_y,pb[mask],B_LABELS),
            'errors':error_counts(y,p.argmax(1))},p,pa,pb

class EarlyStopping:
    def __init__(self):self.best=-math.inf;self.bad=0;self.best_epoch=None
    def update(self,score,epoch):
        if not math.isfinite(score):raise RuntimeError('Macro-F1 no finito')
        previous=self.best
        improved=score>previous
        if improved:self.best=score;self.best_epoch=epoch
        if score>previous+MIN_DELTA:self.bad=0
        else:self.bad+=1
        return improved,self.bad>=PATIENCE
''')
add('def optimizer_tools'+old(12).split('def optimizer_tools')[1].split('def train_epoch')[0] + '''
def train_epoch(model,loader,optimizer,scheduler,scaler,state,emit,max_attempts=None):
    model.train();optimizer.zero_grad(set_to_none=True)
    sums=np.zeros(4);updates=skips=attempts=0
    iterator=iter(loader)
    while group:=list(islice(iterator,GRADIENT_ACCUMULATION_STEPS)):
        # Normalización por cabeza en el batch efectivo completo, incluida la cola.
        target=torch.cat([batch['labels'] for batch in group]).to(DEVICE)
        da,db=loss_denominators(target)
        group_finite=True
        for batch in group:
            y=batch['labels'].to(DEVICE)
            with torch.autocast('cuda',dtype=torch.float16):
                a,b=model(**{k:v.to(DEVICE) for k,v in batch.items() if k!='labels'})
            na,nb=loss_numerators(a,b,y)
            loss=na/da+(nb/db if bool(db>0) else nb)
            group_finite=group_finite and bool(torch.isfinite(loss))
            scaler.scale(loss).backward()
            if bool(torch.isfinite(na)) and bool(torch.isfinite(nb)):
                ma,mb=loss_denominators(y)
                sums+=np.array([na.detach().item(),nb.detach().item(),ma.item(),mb.item()])
        scaler.unscale_(optimizer)
        params=[p for p in model.parameters() if p.grad is not None]
        finite=all(bool(torch.isfinite(p.grad).all()) for p in params)
        if finite:
            norm=torch.linalg.vector_norm(torch.stack([torch.linalg.vector_norm(p.grad.double()) for p in params]))
            factor=min(1.,GRAD_CLIP/(float(norm)+1e-6))
            for p in params:p.grad.mul_(factor)
        before=scaler.get_scale()
        scaler.step(optimizer);scaler.update()
        skipped=scaler.get_scale()<before
        optimizer.zero_grad(set_to_none=True)
        attempts+=1
        if skipped:skips+=1;state['consecutive_skips']+=1
        else:updates+=1;state['consecutive_skips']=0;scheduler.step()
        emit({'attempt':attempts,'skipped':skipped,'finite_loss':group_finite,
              'finite_gradients':finite,'scale_before':before,'scale_after':scaler.get_scale()})
        if not group_finite and not skipped:raise RuntimeError('Loss no finita sin recuperación AMP')
        if state['consecutive_skips']>=MAX_CONSECUTIVE_AMP_SKIPS:
            raise RuntimeError('NaN/Inf persistentes tras 20 omisiones AMP consecutivas')
        if max_attempts is not None and attempts>=max_attempts:break
    la=sums[0]/sums[2] if sums[2] else 0.
    lb=sums[1]/sums[3] if sums[3] else 0.
    return {'train_total_loss':la+lb,'train_relevance_loss':la,'train_historical_loss':lb,
            'updates':updates,'amp_skips':skips,'learning_rate':optimizer.param_groups[0]['lr']}
''')
add('''# Protocolo y protección de ejecuciones anteriores
protocol={'model':MODEL_NAME,'revision':MODEL_REVISION,'labels':FINAL_LABELS,'head_a':A_LABELS,
 'head_b':B_LABELS,'input_hashes':input_hashes,'train':758,'dev':160,'seeds':SEEDS,
 'max_length':MAX_LENGTH,'padding':'dynamic','lr':LEARNING_RATE,'weight_decay':WEIGHT_DECAY,
 'max_epochs':MAX_EPOCHS,'patience':PATIENCE,'min_delta':MIN_DELTA,'warmup_ratio':WARMUP_RATIO,
 'micro_batch':MICRO_BATCH_SIZE,'accumulation':GRADIENT_ACCUMULATION_STEPS,'grad_clip':GRAD_CLIP,
 'loss_weights':[1,1],'weights_A':weights_A.tolist(),'weights_B':weights_B.tolist(),
 'selection':'strict maximum DEV macro-F1 final 7; ties earliest; patience against previous best',
 'python':platform.python_version(),'torch':torch.__version__,'cuda':torch.version.cuda,
 'gpu':torch.cuda.get_device_name(),'expert_gold':False,'DEV_previously_exposed':True}

def run_seed(seed):
    seed_all(seed)
    loader=make_loader(train_rows,train_tokens,True,seed)
    dev_loader=make_loader(dev_rows,dev_tokens,False,seed)
    destination=CHECKPOINTS/f'seed_{seed}'
    destination.mkdir(parents=True,exist_ok=False)
    model=MultitaskBETO().to(DEVICE)
    optimizer,scheduler,scaler=optimizer_tools(model,loader)
    history=[];stopper=EarlyStopping();state={'consecutive_skips':0}
    try:
        with (RESULTS/f'amp_seed_{seed}.jsonl').open('w',encoding='utf-8') as events:
            for epoch in range(1,MAX_EPOCHS+1):
                def emit(event):
                    events.write(json.dumps({'seed':seed,'epoch':epoch,**event})+'\\n');events.flush()
                    if event['skipped']:print('Recuperación AMP:',event)
                train=train_epoch(model,loader,optimizer,scheduler,scaler,state,emit)
                info,p,pa,pb=evaluate(model,dev_loader)
                score=info['metrics']['macro_f1']
                improved,stop=stopper.update(score,epoch)
                history.append({'epoch':epoch,**train,'dev_macro_f1_7':score,
                    'dev_relevance_f1':info['head_a']['macro_f1'],'dev_historical_f1':info['head_b']['macro_f1']})
                pd.DataFrame(history).to_csv(RESULTS/f'multitask_history_seed_{seed}.csv',index=False)
                if improved:
                    torch.save(model.state_dict(),destination/'model.pt')
                    model.encoder.config.save_pretrained(destination)
                    tokenizer.save_pretrained(destination)
                    save_json(destination/'multitask_config.json',{'protocol':protocol,'seed':seed,'epoch':epoch,
                        'architecture':'AutoModel CLS -> Dropout(.1)/Linear(2), Dropout(.1)/Linear(6)'})
                    best_p=p.copy()
                print('seed',seed,'epoch',epoch,'DEV macro-F1 final',score)
                if stop:break
        if sum(h['updates'] for h in history)==0:raise RuntimeError('Cero updates efectivos')
        model.load_state_dict(torch.load(destination/'model.pt',map_location='cpu',weights_only=True))
        info,p,pa,pb=evaluate(model,dev_loader)
        assert np.allclose(p,best_p,atol=1e-6,rtol=0),'Recarga no reproduce checkpoint'
        pred=p.argmax(1)
        with (RESULTS/f'multitask_seed_{seed}_predictions.jsonl').open('w',encoding='utf-8') as f:
            for i,r in enumerate(dev_rows):
                record={k:r[k] for k in ('family','component','source_id') if k in r}
                record.update(id=r['id'],text_sha256=text_hash(r),reference=r['label'],prediction=FINAL_LABELS[pred[i]],
                  probabilities_7=p[i].tolist(),p_relevant=float(pa[i,1]),p_not_relevant=float(pa[i,0]),
                  probabilities_history_6=pb[i].tolist(),seed=seed)
                f.write(json.dumps(record,ensure_ascii=False,allow_nan=False)+'\\n')
        info.update(seed=seed,selected_epoch=stopper.best_epoch,history=history)
        save_json(RESULTS/f'multitask_seed_{seed}_metrics.json',info)
        for name,labels,m in [('confusion',FINAL_LABELS,info['metrics']),('head_a_confusion',A_LABELS,info['head_a']),
                              ('head_b_confusion',B_LABELS,info['head_b'])]:
            pd.DataFrame(m['confusion_matrix'],index=labels,columns=labels).to_csv(RESULTS/f'multitask_{name}_seed_{seed}.csv')
        return info
    finally:
        del model,optimizer,scheduler,scaler
        release_gpu()
''')
add('''# Smoke: datos reales, sin guardar checkpoints ni métricas científicas
def smoke_update(model,loader,optimizer,scheduler,scaler):
    state={'consecutive_skips':0}
    for attempt in range(1,MAX_CONSECUTIVE_AMP_SKIPS+1):
        before=scheduler.last_epoch
        def emit(event):print({'smoke_attempt':attempt,**event})
        result=train_epoch(model,loader,optimizer,scheduler,scaler,state,emit,max_attempts=1)
        assert scheduler.last_epoch-before==result['updates']
        if result['updates']==1:return result
        assert result['amp_skips']==1,'Smoke sin update ni omisión AMP registrada'
        # Conserva modelo, optimizer y GradScaler: la escala reducida se usa en el siguiente intento.
    raise RuntimeError('Smoke: AMP no se recuperó dentro del límite de persistencia')

def run_smoke_test():
    seed_all(42)
    nr=next(i for i,r in enumerate(train_rows) if r['label']=='no_relevante')
    rel=next(i for i,r in enumerate(train_rows) if r['label']!='no_relevante')
    loader=make_loader(train_rows,train_tokens,False,42,[nr,rel])
    model=MultitaskBETO().to(DEVICE)
    optimizer,scheduler,scaler=optimizer_tools(model,loader)
    try:
        batch=next(iter(loader));y=batch['labels'].to(DEVICE)
        a,b=model(**{k:v.to(DEVICE) for k,v in batch.items() if k!='labels'})
        assert a.shape==(2,2) and b.shape==(2,6)
        na,nb=loss_numerators(a,b,y)
        grad=torch.autograd.grad(nb,b,retain_graph=True)[0]
        assert bool((grad[y==NR_ID]==0).all()) and bool((grad[y!=NR_ID]!=0).any())
        _,zero=loss_numerators(a[:1],b[:1],y[:1]);assert zero.item()==0
        assert bool(torch.isfinite(na+nb))
        smoke_update(model,loader,optimizer,scheduler,scaler)
        # Evaluación completa para incluir las seis referencias históricas.
        info,p,pa,pb=evaluate(model,make_loader(dev_rows,dev_tokens,False,42))
        assert p.shape==(160,7) and np.allclose(p.sum(1),1,atol=2e-6)
        print('Smoke aprobado; no es resultado científico.')
    finally:
        del model,optimizer,scheduler,scaler
        release_gpu()

results_by_seed=[]
if RUN_SMOKE_TEST:
    run_smoke_test()
else:
    if RESULTS.exists() or CHECKPOINTS.exists():
        raise RuntimeError('results/checkpoints ya existen. Descarga la ejecución anterior y usa una sesión Colab nueva.')
    RESULTS.mkdir();CHECKPOINTS.mkdir()
    save_json(RESULTS/'protocol.json',protocol)
    (RESULTS/'environment.txt').write_text(subprocess.check_output([sys.executable,'-m','pip','freeze'],text=True),encoding='utf-8')
    try:
        for seed in SEEDS:results_by_seed.append(run_seed(seed))
    except Exception as exc:
        save_json(RESULTS/'failure.json',{'error':repr(exc),'completed_seeds':[r['seed'] for r in results_by_seed]})
        raise
''')
add('''complete=not RUN_SMOKE_TEST and [r['seed'] for r in results_by_seed]==SEEDS
if complete:
    metrics_table=pd.DataFrame([{'seed':r['seed'],'selected_epoch':r['selected_epoch'],
       'macro_f1':r['metrics']['macro_f1'],'accuracy':r['metrics']['accuracy'],
       'head_a_macro_f1':r['head_a']['macro_f1'],'head_b_macro_f1':r['head_b']['macro_f1'],**r['errors']}
       for r in results_by_seed])
    per_class_table=pd.DataFrame([{'seed':r['seed'],**c} for r in results_by_seed for c in r['metrics']['per_class']])
    metrics_table.to_csv(RESULTS/'multitask_metrics_by_seed.csv',index=False)
    per_class_table.to_csv(RESULTS/'multitask_per_class.csv',index=False)
    summary={'results':results_by_seed,'protocol':protocol,'labels':FINAL_LABELS,
       'macro_f1_mean':float(metrics_table.macro_f1.mean()),'macro_f1_std':float(metrics_table.macro_f1.std(ddof=1)),
       'accuracy_mean':float(metrics_table.accuracy.mean()),'std_ddof':1}
    save_json(RESULTS/'multitask_summary.json',summary)
    display(metrics_table);display(per_class_table)
    print('Macro-F1 media:',summary['macro_f1_mean'],'Std muestral:',summary['macro_f1_std'])
else:
    print('Sin resumen científico: modo smoke o ejecución incompleta.')
''')
add('''if complete:
    for r in results_by_seed:
        seed=r['seed'];h=pd.DataFrame(r['history'])
        fig,axes=plt.subplots(1,2,figsize=(12,4))
        h.plot(x='epoch',y='dev_macro_f1_7',ax=axes[0],title=f'Seed {seed}: DEV final')
        h.plot(x='epoch',y=['train_total_loss','train_relevance_loss','train_historical_loss'],ax=axes[1])
        fig.tight_layout();fig.savefig(RESULTS/f'curves_seed_{seed}.png',dpi=160);plt.show()
        fig,ax=plt.subplots(figsize=(7,6));cm=np.asarray(r['metrics']['confusion_matrix'])
        ax.imshow(cm,cmap='Blues');short=['MIL','COL','IDE','LID','NR','REP','SOC']
        ax.set(xticks=range(7),yticks=range(7),xticklabels=short,yticklabels=short,
               xlabel='Predicción',ylabel='Referencia',title=f'Seed {seed}')
        for i in range(7):
            for j in range(7):ax.text(j,i,str(cm[i,j]),ha='center',va='center',color='white' if cm[i,j]>cm.max()/2 else 'black')
        fig.tight_layout();fig.savefig(RESULTS/f'confusion_seed_{seed}.png',dpi=160);plt.show()
    ax=per_class_table.pivot(index='label',columns='seed',values='f1').reindex(FINAL_LABELS).plot.bar(figsize=(12,6),ylim=(0,1),ylabel='F1')
    ax.figure.tight_layout();ax.figure.savefig(RESULTS/'f1_per_class.png',dpi=160);plt.show()
''')
add('''# Opcional: subir ahora resultados anteriores, o incluirlos en la carga inicial.
# JSON: {"results":[{"seed":42,"metrics":{"macro_f1":0.5,"accuracy":0.5}}, ...]}
# También admite lista de filas {seed,macro_f1,accuracy}. Deben estar las tres seeds.
UPLOAD_COMPARISON = False
if complete:
    optional=dict(uploaded)
    if UPLOAD_COMPARISON:optional.update(files.upload())
    tables={'multitarea':metrics_table[['seed','macro_f1','accuracy']]}
    for name,filename in [('plano','flat_beto_results.json'),('jerárquico','hierarchical_beto_results.json')]:
        if filename not in optional:continue
        obj=json.loads(optional[filename].decode('utf-8-sig'))
        rows=obj if isinstance(obj,list) else obj['results']
        rows=[{'seed':int(r['seed']),'macro_f1':float(r.get('metrics',r)['macro_f1']),
               'accuracy':float(r.get('metrics',r)['accuracy'])} for r in rows]
        table=pd.DataFrame(rows)
        assert len(table)==3 and set(table.seed)==set(SEEDS) and not table.seed.duplicated().any()
        assert np.isfinite(table[['macro_f1','accuracy']]).all().all()
        assert table[['macro_f1','accuracy']].ge(0).all().all() and table[['macro_f1','accuracy']].le(1).all().all()
        if isinstance(obj,dict):
            assert obj.get('labels',FINAL_LABELS)==FINAL_LABELS
            hashes=obj.get('protocol',{}).get('input_hashes')
            if hashes is not None:assert hashes==input_hashes,'Diferentes datos TRAIN/DEV'
        tables[name]=table
    if len(tables)>1:
        print('Comparación descriptiva; sin hashes compatibles no se acredita automáticamente identidad de datos.')
        comparison=pd.DataFrame({name:t.set_index('seed').macro_f1 for name,t in tables.items()}).reindex(SEEDS)
        models=pd.DataFrame([{'Modelo':name,'Macro-F1 medio':t.macro_f1.mean(),'Std':t.macro_f1.std(ddof=1),
                             'Accuracy media':t.accuracy.mean()} for name,t in tables.items()])
        display(models);display(comparison.reindex(columns=['plano','jerárquico','multitarea']))
        models.to_csv(RESULTS/'comparison_models.csv',index=False);comparison.to_csv(RESULTS/'comparison_by_seed.csv')
        ax=comparison.plot.bar(rot=0,ylabel='Macro-F1 DEV',ylim=(0,1))
        ax.figure.tight_layout();ax.figure.savefig(RESULTS/'comparison.png',dpi=160);plt.show()
''')
add('''DOWNLOAD_CHECKPOINTS = False
if complete:
    files.download(shutil.make_archive('/content/multitask_results','zip',RESULTS))
    if DOWNLOAD_CHECKPOINTS:
        files.download(shutil.make_archive('/content/multitask_checkpoints','zip',CHECKPOINTS))
''')

if __name__ == '__main__':
    OUT.mkdir(parents=True,exist_ok=True)
    target=OUT/'beto_multitarea_colab.ipynb'
    notebook={'nbformat':4,'nbformat_minor':5,'metadata':{'colab':{'name':target.name},'accelerator':'GPU',
       'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'language_info':{'name':'python'}},'cells':cells}
    target.write_text(json.dumps(notebook,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(target)
