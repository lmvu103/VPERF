import csv
from collections import Counter

with open('E:\\ANTIGRAVITY\\VPERF\\sample_data.csv', 'r') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

print(f'Total rows: {len(rows)}')
print(f'Columns: {list(rows[0].keys())}')

print()
print('=== ALL DATA STATS ===')
por_vals = []
sw_vals = []
vsh_vals = []
for r in rows:
    por = float(r['Porosity']) if r['Porosity'] else 0.0
    sw = float(r['Sw']) if r['Sw'] else 1.0
    vsh = float(r['Vshale']) if r['Vshale'] else 1.0
    por_vals.append(por)
    sw_vals.append(sw)
    vsh_vals.append(vsh)

print(f'Porosity range: {min(por_vals):.4f} - {max(por_vals):.4f}')
print(f'Sw range: {min(sw_vals):.4f} - {max(sw_vals):.4f}')
print(f'Vshale range: {min(vsh_vals):.4f} - {max(vsh_vals):.4f}')

print()
print('=== ROWS WITH Porosity>0.001, Vshale<0.5, Sw<0.6 ===')
good = []
for r in rows:
    por = float(r['Porosity']) if r['Porosity'] else 0.0
    sw = float(r['Sw']) if r['Sw'] else 1.0
    vsh = float(r['Vshale']) if r['Vshale'] else 1.0
    if por > 0.001 and vsh < 0.5 and sw < 0.6:
        good.append(r)

print(f'Count: {len(good)}')
if good:
    print('First 10 samples:')
    for r in good[:10]:
        print(f"  Well={r['Well_Name']}, Depth={r['Depth']}, Zone={r['Zone_Name']}, Por={r['Porosity']}, Sw={r['Sw']}, Vshale={r['Vshale']}, Class={r['Production_Class']}")

print()
print('=== CURRENT Perforated rows ===')
perf_rows = [r for r in rows if r['Is_Perforated'] == 'True']
print(f'Count: {len(perf_rows)}')
for r in perf_rows:
    por = float(r['Porosity']) if r['Porosity'] else 0.0
    sw = float(r['Sw']) if r['Sw'] else 1.0
    vsh = float(r['Vshale']) if r['Vshale'] else 1.0
    print(f"  Depth={float(r['Depth']):.1f}, Zone={r['Zone_Name']}, Por={por:.4f}, Sw={sw:.4f}, Vshale={vsh:.4f}, Rate={r['Initial_Rate']}, Class={r['Production_Class']}")

print()
print('=== ZONE COUNTS (top 20) ===')
zone_counts = Counter(r['Zone_Name'] for r in rows)
for zone, count in zone_counts.most_common(20):
    print(f'  {zone}: {count} rows')

print()
print('=== PERFORATED BY ZONE ===')
perf_zones = Counter(r['Zone_Name'] for r in perf_rows)
for zone, count in perf_zones.most_common(20):
    print(f'  {zone}: {count} rows')

print()
print('=== WELL COUNTS ===')
well_counts = Counter(r['Well_Name'] for r in rows)
for well, count in well_counts.most_common(20):
    print(f'  {well}: {count} rows')
