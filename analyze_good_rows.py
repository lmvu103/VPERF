import csv
from collections import Counter

with open('E:\\ANTIGRAVITY\\VPERF\\sample_data.csv', 'r') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

# Find good rows - netpay candidates
print('=== ROWS WITH Porosity>0.001, Vshale<0.5, Sw<0.6 ===')
good = []
for r in rows:
    por = float(r['Porosity']) if r['Porosity'] else 0.0
    sw = float(r['Sw']) if r['Sw'] else 1.0
    vsh = float(r['Vshale']) if r['Vshale'] else 1.0
    if por > 0.001 and vsh < 0.5 and sw < 0.6:
        good.append(r)

print(f'Count: {len(good)}')
# Show by zone
zone_good = Counter(r['Zone_Name'] for r in good)
print('\nBy zone (top 20):')
for z, c in zone_good.most_common(20):
    print(f'  {z}: {c} rows')

# Show by well
well_good = Counter(r['Well_Name'] for r in good)
print('\nBy well:')
for w, c in well_good.most_common():
    print(f'  {w}: {c} rows')

# Find contiguous intervals per well
print('\n=== CONTIGUOUS GOOD INTERVALS PER WELL ===')
for well in ['24P', '25P', '33P']:
    well_rows = [r for r in rows if r['Well_Name'] == well]
    intervals = []
    current_start = None
    current_end = None
    current_zone = None
    for r in well_rows:
        por = float(r['Porosity']) if r['Porosity'] else 0.0
        sw = float(r['Sw']) if r['Sw'] else 1.0
        vsh = float(r['Vshale']) if r['Vshale'] else 1.0
        is_good = por > 0.001 and vsh < 0.5 and sw < 0.6
        depth = float(r['Depth'])
        zone = r['Zone_Name']
        if is_good:
            if current_start is None:
                current_start = depth
                current_end = depth
                current_zone = zone
            else:
                current_end = depth
        else:
            if current_start is not None:
                intervals.append((current_zone, current_start, current_end))
                current_start = None
                current_end = None
                current_zone = None
    if current_start is not None:
        intervals.append((current_zone, current_start, current_end))
    
    print(f'\n{well}: {len(intervals)} good intervals')
    total_good = sum(1 for r in well_rows if (float(r['Porosity']) if r['Porosity'] else 0.0) > 0.001 and (float(r['Vshale']) if r['Vshale'] else 1.0) < 0.5 and (float(r['Sw']) if r['Sw'] else 1.0) < 0.6)
    print(f'  Total good rows: {total_good}')
    for i, (zone, start, end) in enumerate(intervals[:10]):
        thickness = end - start
        zone_rows = [r for r in well_rows if float(r['Depth']) >= start and float(r['Depth']) <= end]
        avg_por = sum(float(r['Porosity']) for r in zone_rows if r['Porosity']) / len(zone_rows) if zone_rows else 0
        avg_sw = sum(float(r['Sw']) for r in zone_rows if r['Sw']) / len(zone_rows) if zone_rows else 0
        print(f'  [{i+1}] Zone={zone}, {start:.1f}-{end:.1f} ({thickness:.1f}m), Por_avg={avg_por:.4f}, Sw_avg={avg_sw:.4f}, rows={len(zone_rows)}')
        if i >= 9 and len(intervals) > 10:
            print(f'  ... and {len(intervals)-10} more intervals')
