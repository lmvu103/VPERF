import pandas as pd

df = pd.read_csv('e:/ANTIGRAVITY/VPERF/sample_data.csv')
perf = df[df['Is_Perforated'] == True]

print('=== Training Data Quality Check ===')
print(f'Total perforated rows: {len(perf)}')
print()

print('By well:')
for well in sorted(df['Well_Name'].unique()):
    wp = perf[perf['Well_Name'] == well]
    cls_counts = wp['Production_Class'].value_counts().to_dict()
    print(f'  {well}: {len(wp)} rows | {cls_counts}')

print()
print('Total by class:')
print(dict(perf['Production_Class'].value_counts()))

print()
print('=== ML Requirement Check ===')
for well in sorted(df['Well_Name'].unique()):
    wp = perf[perf['Well_Name'] == well]
    ok = len(wp) >= 15
    print(f'  {well}: {len(wp)} perf rows (need >= 15): {"OK" if ok else "FAIL"}')

has_rate = perf[perf['Initial_Rate'].notna()]
print(f'Total with Initial_Rate >= 10 for production model: {"OK" if len(has_rate) >= 10 else "FAIL"} ({len(has_rate)} rows)')

print()
print('=== MEDIUM class presence ===')
medium = perf[perf['Production_Class'] == 'MEDIUM']
print(f'MEDIUM rows: {len(medium)}')
by_well = dict(medium.groupby('Well_Name').size())
print(f'By well: {by_well}')
rates = medium['Initial_Rate'].astype(float)
print(f'Rate range: {rates.min():.1f} - {rates.max():.1f} BOPD (mean={rates.mean():.1f})')
