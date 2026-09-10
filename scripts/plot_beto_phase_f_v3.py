"""Plot saved F metrics with existing system matplotlib; no ML dependencies."""
import os
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
CACHE=ROOT/'outputs/beto-v3/phase-f/process-cache'
for key,sub in {'MPLCONFIGDIR':'matplotlib','TEMP':'tmp','TMP':'tmp','XDG_CACHE_HOME':'xdg'}.items():
    os.environ[key]=str(CACHE/sub)
A=ROOT/'artifacts/beto-v3/phase-f'
summary=json.loads((A/'comparison.json').read_text(encoding='utf-8'))
lookup={(x['condition'],x['seed']):x for x in summary['records']}
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig,axes=plt.subplots(2,3,figsize=(13,7),sharex=True)
for col,seed in enumerate((42,43,44)):
    for condition,color in [('H+T','#2764ad'),('T','#c65e24')]:
        history=lookup[condition,seed]['history']
        epochs=[h['epoch'] for h in history]
        axes[0,col].plot(epochs,[h['f1_macro'] for h in history],label=condition+' V',color=color)
        axes[0,col].plot(epochs,[h['train_metrics_eval']['f1_macro'] for h in history],label=condition+' train',color=color,linestyle='--',alpha=.65)
        axes[1,col].plot(epochs,[h['weighted_train_loss'] for h in history],label=condition,color=color)
    axes[0,col].set(title=f'Semilla {seed}',ylim=(0,1.03),ylabel='F1 macro (7 clases)')
    axes[1,col].set(xlabel='Época',ylabel='Pérdida train ponderada',yscale='log')
    for ax in axes[:,col]: ax.grid(alpha=.2);ax.legend(fontsize=8)
fig.suptitle('F: sólo T frente a R2 H+T — mismas semillas y V congelada')
fig.tight_layout()
fig.savefig(A/'curves-F.png',dpi=160);fig.savefig(A/'curves-F.pdf');plt.close(fig)
