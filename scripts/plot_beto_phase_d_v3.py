"""Standalone plots from saved epoch metrics; system Python with matplotlib."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT/'artifacts/beto-v3/phase-d'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def main():
    fig, axes = plt.subplots(2,2,figsize=(12,8),layout='constrained')
    for ax, recipe in zip(axes.flat, ('R0','R1','R2','R3')):
        result = read(ROOT/f'outputs/beto-v3/phase-c/seed-42/{recipe}/result.json')
        history = result['history']
        x = [h['epoch'] for h in history]
        ax.plot(x,[h['train_metrics_eval']['f1_macro'] for h in history],label='Train (evaluación)',color='#176B89')
        ax.plot(x,[h['f1_macro'] for h in history],label='V',color='#BA4A00')
        ax.scatter([result['best_epoch']],[result['metrics']['combined']['f1_macro']],marker='*',s=120,color='#BA4A00',zorder=5)
        ax.set(title=f'{recipe} · semilla 42',xlabel='Época',ylabel='F1 macro (7 clases)',ylim=(0,1.04))
        ax.grid(alpha=.2)
        ax.legend(loc='lower right')
    fig.suptitle('BETO V3 · curvas existentes de C · validación congelada; S cerrada')
    fig.savefig(ART/'curves-C.png',dpi=160)
    plt.close(fig)
    if not (ART/'comparison.json').exists():
        return
    summary = read(ART/'comparison.json')
    fig, axes = plt.subplots(2,2,figsize=(13,8),layout='constrained')
    colors = {42:'#176B89',43:'#BA4A00',44:'#6C3483'}
    for i,recipe in enumerate(('R0','R2')):
        for run in summary['results']:
            if run['recipe']!=recipe:
                continue
            h = run['history']; x=[e['epoch'] for e in h]; seed=run['seed']; color=colors[seed]
            axes[i,0].plot(x,[e['train_metrics_eval']['f1_macro'] for e in h],color=color,linestyle='--',label=f'{seed} train')
            axes[i,0].plot(x,[e['f1_macro'] for e in h],color=color,label=f'{seed} V')
            axes[i,0].scatter([run['best_epoch']],[run['metrics']['f1_macro']],marker='*',s=90,color=color,zorder=5)
            axes[i,1].plot(x,[e['weighted_train_loss'] for e in h],color=color,label=str(seed))
        axes[i,0].set(title=f'{recipe}: F1 train y V (★ checkpoint elegido)',ylabel='F1 macro (7 clases)',ylim=(0,1.04))
        axes[i,1].set(title=f'{recipe}: pérdida ponderada en entrenamiento',ylabel='Pérdida (escala log)',yscale='log')
        for ax in axes[i]:
            ax.set_xlabel('Época'); ax.grid(alpha=.2); ax.legend(fontsize=8,ncol=2)
    fig.suptitle('BETO V3 · seis ejecuciones comparables · R2 conserva 20 épocas')
    fig.savefig(ART/'curves-D.png',dpi=160)
    fig.savefig(ART/'curves-D.pdf')
    plt.close(fig)


if __name__ == '__main__':
    main()
