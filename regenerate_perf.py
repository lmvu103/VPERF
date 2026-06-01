import csv

INPUT = 'E:\\ANTIGRAVITY\\VPERF\\sample_data.csv'
OUTPUT = 'E:\\ANTIGRAVITY\\VPERF\\sample_data.csv'

with open(INPUT, 'r') as f:
    reader = csv.DictReader(f)
    rows = list(reader)
    fieldnames = reader.fieldnames

print(f'Read {len(rows)} rows')

# Criteria for netpay
def is_netpay(r):
    por = float(r['Porosity']) if r['Porosity'] else 0.0
    sw = float(r['Sw']) if r['Sw'] else 1.0
    vsh = float(r['Vshale']) if r['Vshale'] else 1.0
    return por > 0.001 and vsh < 0.5 and sw < 0.6

def calc_rate(por, sw, vsh):
    """Assign rate based on reservoir quality"""
    # Higher porosity and lower Sw = better quality
    quality = por * (1.0 - sw) * (1.0 - vsh)
    if quality > 0.08:
        return 179.4, 'BEST'
    elif quality > 0.04:
        return 44.3, 'GOOD'
    elif quality > 0.02:
        return 11.4, 'GOOD'
    elif quality > 0.01:
        return 4.2, 'POOR'
    else:
        return 2.8, 'POOR'

# Find contiguous netpay intervals per well
intervals = {}
for well in ['24P', '25P', '33P']:
    well_rows = [r for r in rows if r['Well_Name'] == well and is_netpay(r)]
    intervals[well] = []
    for r in well_rows:
        intervals[well].append({
            'depth': float(r['Depth']),
            'por': float(r['Porosity']),
            'sw': float(r['Sw']),
            'vsh': float(r['Vshale']),
        })

# For each well, group contiguous rows into intervals
# A gap of > 0.2m means a new interval
well_intervals = {}
for well in ['24P', '25P', '33P']:
    well_rows = [r for r in rows if r['Well_Name'] == well]
    current_interval = []
    well_intervals[well] = []
    for r in well_rows:
        if is_netpay(r):
            current_interval.append(r)
        else:
            if current_interval:
                well_intervals[well].append(current_interval)
                current_interval = []
    if current_interval:
        well_intervals[well].append(current_interval)

# Now we want to mark the PERFORATED rows
# Strategy: For each netpay interval that is at least 3 rows thick and has decent quality,
# mark a subset as perforated (not all rows - maybe a continuous segment within)
# to simulate realistic perf intervals

import random
random.seed(42)

def get_interval_quality(interval_rows):
    """Calculate average quality of an interval"""
    total_quality = 0
    for r in interval_rows:
        por = float(r['Porosity']) if r['Porosity'] else 0.0
        sw = float(r['Sw']) if r['Sw'] else 1.0
        vsh = float(r['Vshale']) if r['Vshale'] else 1.0
        quality = por * (1.0 - sw) * (1.0 - vsh)
        total_quality += quality
    return total_quality / len(interval_rows) if interval_rows else 0

# For each well, select the best intervals to perforate
perf_count = 0
for well in ['24P', '25P', '33P']:
    intervals = well_intervals[well]
    # Sort intervals by quality descending
    intervals_with_quality = [(i, get_interval_quality(i)) for i in intervals]
    intervals_with_quality.sort(key=lambda x: x[1], reverse=True)
    
    # Pick top intervals representing ~20-30% of total netpay rows
    total_netpay_rows = sum(len(i) for i in intervals)
    target_perf = int(total_netpay_rows * 0.25)  # perforate ~25% of netpay
    
    perf_candidates = []
    for interval, quality in intervals_with_quality:
        if len(perf_candidates) >= target_perf:
            break
        # Take all rows from this interval
        perf_candidates.extend(interval)
    
    # Mark these as perforated
    perf_depths = set(float(r['Depth']) for r in perf_candidates)
    for r in rows:
        if r['Well_Name'] == well:
            depth = float(r['Depth'])
            if depth in perf_depths:
                r['Is_Perforated'] = 'True'
                por = float(r['Porosity']) if r['Porosity'] else 0.0
                sw = float(r['Sw']) if r['Sw'] else 1.0
                vsh = float(r['Vshale']) if r['Vshale'] else 1.0
                rate, pclass = calc_rate(por, sw, vsh)
                r['Initial_Rate'] = str(rate)
                r['Production_Class'] = pclass
                perf_count += 1
            else:
                r['Is_Perforated'] = 'False'
                r['Initial_Rate'] = ''
                r['Production_Class'] = ''

print(f'\nSet {perf_count} rows as perforated (netpay only)')

# Write output
with open(OUTPUT, 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f'Written to {OUTPUT}')

# Verify
print('\n=== VERIFICATION ===')
with open(OUTPUT, 'r') as f:
    reader = csv.DictReader(f)
    new_rows = list(reader)
    
perf_rows = [r for r in new_rows if r['Is_Perforated'] == 'True']
print(f'Total perforated rows: {len(perf_rows)}')

# Check perforated rows quality
bad_perf = 0
for r in perf_rows:
    por = float(r['Porosity']) if r['Porosity'] else 0.0
    sw = float(r['Sw']) if r['Sw'] else 1.0
    vsh = float(r['Vshale']) if r['Vshale'] else 1.0
    if vsh >= 0.5 or sw >= 0.6 or por <= 0.001:
        bad_perf += 1
        print(f'  BAD PERF: Well={r["Well_Name"]}, Depth={r["Depth"]}, Por={por:.4f}, Sw={sw:.4f}, Vshale={vsh:.4f}')
        
if bad_perf == 0:
    print('  All perforated rows satisfy netpay criteria!')
else:
    print(f'  WARNING: {bad_perf} perforated rows do NOT satisfy netpay criteria')

# Count by production class
from collections import Counter
class_counts = Counter(r['Production_Class'] for r in perf_rows)
print(f'  By class: {dict(class_counts)}')

# By well
well_counts = Counter(r['Well_Name'] for r in perf_rows)
print(f'  By well: {dict(well_counts)}')
