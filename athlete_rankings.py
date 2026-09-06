"""Count recorded final-round wins and podiums, then plot the leaders.

Run: .venv/Scripts/python.exe athlete_rankings.py
Counts describe this dataset, not complete career records.
"""
import ast
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / 'analysis'
OUTPUT.mkdir(exist_ok=True)
os.environ.setdefault('MPLCONFIGDIR', str(OUTPUT / '.matplotlib'))

import matplotlib
matplotlib.use('Agg')  # Save figures without opening a desktop window.
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import pandas as pd

# The CSV stores Python dictionaries as text. Parse and flatten them.
raw = pd.read_csv(ROOT / 'mongodb_data.csv')
data = pd.json_normalize([
    {column: ast.literal_eval(row[column]) for column in ['event', 'athlete', 'run']}
    for _, row in raw.iterrows()
])

# Explicit labels make the podium definition easy to inspect/change.
# Do not count qualification, Final 1, or overall summaries as extra podiums.
# Never substitute Final 1 when Final 2 is absent from the dataset.
FINAL_LABELS = [
    'Results Final 2',
    'QUALIFICATION RUN 1 RESULTS Final 2',
    'Results Final',
]
finals = data[data['event.level'].isin(FINAL_LABELS)].copy()
event_key = ['event.event', 'event.event_date', 'event.venue', 'event.discipline']
assert not finals.duplicated(event_key + ['athlete.fis_code']).any(), 'Repeated athlete/event: inspect before counting'

finals['win'] = finals['athlete.rank'].eq(1)
finals['podium'] = finals['athlete.rank'].isin([1, 2, 3])  # Wins also count as podiums.

# Use FIS code as identity; attach the name separately.
identity = ['event.discipline', 'athlete.fis_code']
counts = finals.groupby(identity).agg(
    final_appearances=('athlete.rank', 'size'),
    wins=('win', 'sum'),
    podiums=('podium', 'sum'),
).reset_index()
athletes = data[identity + ['athlete.name', 'athlete.nsa_code']].drop_duplicates(identity)
rankings = athletes.merge(counts, on=identity, how='left')
for column in ['final_appearances', 'wins', 'podiums']:
    rankings[column] = rankings[column].fillna(0).astype(int)
rankings = rankings.sort_values(['wins', 'podiums', 'athlete.name'], ascending=[False, False, True])
rankings.to_csv(OUTPUT / 'athlete_rankings.csv', index=False)

# Save every counted row so totals can be checked manually.
audit_columns = event_key + ['event.level', 'athlete.fis_code', 'athlete.name', 'athlete.rank', 'win', 'podium']
finals[audit_columns].to_csv(OUTPUT / 'counted_final_results.csv', index=False)
print('Counted final labels:', FINAL_LABELS)
print('Final event groups:', finals.groupby(event_key).ngroups)
print('Recorded wins:', finals['win'].sum(), '| Recorded podiums:', finals['podium'].sum())

# Separate men and women; show the ten highest counts for each measure.
for discipline, athletes in rankings.groupby('event.discipline'):
    fig, axes = plt.subplots(1, 2, figsize=(13, 6), layout='constrained')
    for ax, metric in zip(axes, ['wins', 'podiums']):
        leaders = athletes.sort_values([metric, 'athlete.name'], ascending=[False, True]).head(10)
        bars = ax.barh(leaders['athlete.name'], leaders[metric])
        ax.invert_yaxis()
        ax.bar_label(bars, padding=3)
        ax.set_title(f'Top 10 by {metric}')
        ax.set_xlabel(f'Recorded {metric}')
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))
        ax.set_xlim(0, max(1, leaders[metric].max()) * 1.2)
    fig.suptitle(f'{discipline}: final-round results in this dataset\nAll competition levels combined; ties ordered alphabetically')
    filename = 'men' if discipline == "Men's Moguls" else 'women'
    fig.savefig(OUTPUT / f'athlete_rankings_{filename}.png', dpi=160)
    plt.close(fig)
    print('\n' + discipline)
    print(athletes[['athlete.name', 'wins', 'podiums', 'final_appearances']].head(10).to_string(index=False))
