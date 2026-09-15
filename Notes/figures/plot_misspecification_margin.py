"""Render committed condition results as unconnected points; no interpolation."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter

ROOT = Path(__file__).resolve().parents[2]
ART = ROOT / 'Experiments/SymbolicDiscovery/MisspecificationMargin1'
records = json.loads((ART / 'evaluation.json').read_text())
summary = json.loads((ART / 'summary.json').read_text())
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'svg.hashsalt': 'NP-MISSPEC-MARGIN-01-r1'})
fig, (left, right) = plt.subplots(1, 2, figsize=(10.5, 4.4), gridspec_kw={'width_ratios': [1, 1.5]})
fig.subplots_adjust(left=.075, right=.98, bottom=.22, top=.77, wspace=.3)
fig.suptitle('Known noise obscures a fixed departure from the grammar', x=.075, y=.97, ha='left', fontsize=16, fontweight='bold')
fig.text(.075,.86,'24 datasets · 4 independent blocks · 6 matched conditions per block',fontsize=11,color='#475569')
noise = [.0001,.0016,.005]
recognized = [summary['cells'][f'curved-n{i+1}']['recognized_inadequacy'] for i in range(3)]
left.scatter(noise, recognized, s=78, color='#b54a24', zorder=3)
for x,y in zip(noise,recognized): left.annotate(f'{y}/4',(x,y),xytext=(0,10),textcoords='offset points',ha='center',color='#89381d',fontweight='bold')
left.set_xscale('log'); left.set_ylim(-.5,4.7); left.set_yticks(range(5)); left.set_ylabel('Blocks recognizing inadequacy')
left.set_title('Curved law: pre-reveal recognition',fontsize=11,loc='left')
colors=['#2166ac','#1b9e77','#8654a2','#d18a17']
for b,color in enumerate(colors):
    for condition,marker,filled in [('curved','o',True),('adequate','s',False)]:
        values=[records[f'b{b+1:02d}-{condition}-n{i+1}']['family']['error_bound_ratio'] for i in range(3)]
        right.scatter(noise,values,marker=marker,s=52,facecolor=color if filled else 'none',edgecolor=color,label=f'Block {b+1}' if condition=='curved' else None,zorder=3)
right.axhline(1,color='#64748b',ls='--',lw=1)
right.text(.00008,1.13,'Inadequacy boundary',color='#475569',fontsize=9)
right.set_xscale('log'); right.set_yscale('log'); right.set_ylim(.2,25)
right.set_ylabel('Family validation error / bound')
right.set_title('Filled circles: curved law · open squares: adequate control',fontsize=10,loc='left')
right.legend(loc='upper right',frameon=False,ncol=2,fontsize=8)
for ax in (left,right):
    ax.set_xlim(.000075,.007); ax.set_xticks(noise);ax.set_xticklabels(['0.0001','0.0016','0.005'])
    ax.set_xlabel('Known uniform log-noise half-width, ε')
    ax.spines[['top','right']].set_visible(False); ax.grid(axis='y',alpha=.16,zorder=0)
fig.text(.075,.06,'Rule held fixed: error > 2ε + 10⁻⁹. Points are observed conditions; no continuous curve or population rate is inferred.',fontsize=9,color='#475569')
fig.savefig(Path(__file__).with_name('misspecification_margin.svg'),metadata={'Date':None},facecolor='white')
fig.savefig(ROOT / '.tnp-local/misspecification_margin.png',dpi=160,facecolor='white')
