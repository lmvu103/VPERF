"""
generate_sample_data.py
========================
Generate comprehensive sample data for testing the Streamlit Perforation Dashboard.
Produces everything needed for all 7 pages:
  - sample_data.csv          -> main well log data (Data Upload → all pages)
  - sample_production_history.csv  -> Decline Analysis page
  - sample_PLT.csv           -> Decline Analysis page (DCA & PLT Matching)
  - sample_econ_layers.csv   -> Economic Analysis page (pre-computed proposals)

All files share the same wells (24P, 25P, 33P) and depth ranges for consistency.
"""

import csv
import random
import math
import os
from collections import Counter

random.seed(12345)

# =============================================================================
# CONFIGURATION
# =============================================================================
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

WELLS = {
    '24P': {'depth_start': 2810.0, 'depth_end': 3400.0, 'zone': '5.1'},
    '25P': {'depth_start': 2720.0, 'depth_end': 3310.0, 'zone': '5.1'},
    '33P': {'depth_start': 2780.0, 'depth_end': 3420.0, 'zone': '5.2'},
}

# Zone sub-units for each well
ZONE_UNITS = ['020', '040', '050', '060', '070', '080', '090', '100', '110', '120',
              '130', '140', '150', '160', '170', '180', '190', '200']

# Petrophysical parameter ranges per rock quality class
ROCK_CLASSES = {
    'reservoir_good':   {'por': (0.10, 0.28), 'sw': (0.10, 0.50), 'vsh': (0.01, 0.30), 'perm': (5.0, 200.0)},
    'reservoir_fair':   {'por': (0.05, 0.18), 'sw': (0.30, 0.65), 'vsh': (0.15, 0.45), 'perm': (0.5, 20.0)},
    'reservoir_poor':   {'por': (0.02, 0.10), 'sw': (0.50, 0.85), 'vsh': (0.30, 0.55), 'perm': (0.1, 5.0)},
    'non_reservoir':    {'por': (0.001, 0.05), 'sw': (0.70, 1.0), 'vsh': (0.40, 1.0), 'perm': (0.01, 0.5)},
}

# Production class assignment based on reservoir quality
# Matches the 4-class system used in ML Advisor: BEST, GOOD, MEDIUM, POOR
def assign_production_class(por, sw, vsh, perm):
    quality = por * (1.0 - sw) * (1.0 - vsh)
    if quality > 0.10 and perm > 20:
        return 'BEST'
    elif quality > 0.06 and perm > 5:
        return 'GOOD'
    elif quality > 0.03 and perm > 0.5:
        return 'MEDIUM'
    else:
        return 'POOR'

def assign_initial_rate(por, sw, vsh, perm, prod_class):
    """Calculate initial rate based on rock quality."""
    if prod_class == 'BEST':
        base = random.gauss(900, 200)   # ~700-1100 BOPD
    elif prod_class == 'GOOD':
        base = random.gauss(450, 120)   # ~330-570 BOPD
    elif prod_class == 'MEDIUM':
        base = random.gauss(180, 60)    # ~120-240 BOPD
    else:  # POOR
        base = random.gauss(40, 20)     # ~20-60 BOPD
    base = max(1, base)
    return round(base, 1)

# =============================================================================
# 1. GENERATE MAIN WELL LOG DATA (sample_data.csv)
# =============================================================================
def generate_well_log_data():
    """
    Create realistic well log data with:
    - 0.1m sampling per depth
    - Realistic interleaving of reservoir and non-reservoir intervals
    - Zone assignments based on depth
    """
    columns = [
        'Well_Name', 'Zone_Name', 'Depth', 'Top_Depth', 'Bottom_Depth',
        'Porosity', 'Sw', 'Permeability', 'Vshale',
        'Distance_to_OWC', 'Reservoir_Pressure', 'TVD_Depth',
        'Is_Perforated', 'Initial_Rate', 'Production_Class'
    ]
    rows = []

    for well_name, cfg in WELLS.items():
        depth = cfg['depth_start']
        step = 0.1  # metre sampling
        zone_idx = 0

        while depth <= cfg['depth_end']:
            # Determine rock class for this interval (simulate layered geology)
            # Use a random walk approach
            if depth == cfg['depth_start']:
                current_class = random.choice(['reservoir_good', 'reservoir_fair', 'non_reservoir'])
                interval_remaining = random.uniform(2.0, 15.0)
                zone_unit = random.choice(ZONE_UNITS)
            else:
                interval_remaining -= step
                if interval_remaining <= 0:
                    # Transition to a new interval
                    # Probabilities: 25% good, 30% fair, 20% poor, 25% non-res
                    current_class = random.choices(
                        ['reservoir_good', 'reservoir_fair', 'reservoir_poor', 'non_reservoir'],
                        weights=[0.25, 0.30, 0.20, 0.25]
                    )[0]
                    interval_remaining = random.uniform(1.0, 20.0)
                    # Occasionally change zone unit
                    if random.random() < 0.3:
                        zone_unit = random.choice(ZONE_UNITS)

            # Get rock parameters
            params = ROCK_CLASSES[current_class]
            por = round(random.uniform(*params['por']), 4)
            sw = round(random.uniform(*params['sw']), 4)
            vsh = round(random.uniform(*params['vsh']), 4)
            perm = round(random.uniform(*params['perm']), 2)

            # Zone name: e.g. "5.1_060"
            zone_name = f"{cfg['zone']}_{zone_unit}"

            # Derived columns
            distance_to_owc = round(random.uniform(0, 40), 1) if por > 0.02 else 0.0
            # Reservoir pressure: ~0.1 psi/ft gradient + noise (converted to psi)
            res_pressure = round(random.gauss(depth * 0.052, 200), 1)
            tvd = round(depth * random.uniform(0.95, 0.99), 1)

            top_depth = round(depth - step/2, 4)
            bottom_depth = round(depth + step/2, 4)

            # Initially not perforated
            is_perf = 'False'
            initial_rate = ''
            prod_class = ''

            rows.append({
                'Well_Name': well_name,
                'Zone_Name': zone_name,
                'Depth': round(depth, 4),
                'Top_Depth': top_depth,
                'Bottom_Depth': bottom_depth,
                'Porosity': por,
                'Sw': sw,
                'Permeability': perm if perm > 0 else 0.01,
                'Vshale': vsh,
                'Distance_to_OWC': distance_to_owc,
                'Reservoir_Pressure': res_pressure,
                'TVD_Depth': tvd,
                'Is_Perforated': is_perf,
                'Initial_Rate': initial_rate,
                'Production_Class': prod_class
            })

            depth += step

    return columns, rows


# =============================================================================
# 2. ASSIGN PERFORATIONS (netpay intervals)
# =============================================================================
def is_netpay(row):
    por = float(row['Porosity'])
    sw = float(row['Sw'])
    vsh = float(row['Vshale'])
    return por > 0.001 and vsh < 0.5 and sw < 0.6

def assign_perforations(rows):
    """
    Select netpay intervals to perforate with realistic class diversity:
    - Find ALL contiguous netpay intervals per well
    - Group them into quality tiers: BEST / GOOD / MEDIUM / POOR
    - Perforate representative samples from each tier so the ML model
      has sufficient labeled training data across all 4 classes.
    - Target: ~25% of total netpay rows perforated, with class distribution:
      BEST ~25%, GOOD ~35%, MEDIUM ~25%, POOR ~15%
    """
    well_rows = {}
    for r in rows:
        well_rows.setdefault(r['Well_Name'], []).append(r)

    perf_count = 0
    for well_name, well_data in well_rows.items():
        # Find contiguous netpay intervals
        intervals = []
        current = []
        for r in well_data:
            if is_netpay(r):
                current.append(r)
            else:
                if current:
                    intervals.append(current)
                    current = []
        if current:
            intervals.append(current)

        if not intervals:
            continue

        # Score each interval by average quality
        def interval_quality(intv):
            scores = []
            for r in intv:
                por = float(r['Porosity'])
                sw = float(r['Sw'])
                vsh = float(r['Vshale'])
                scores.append(por * (1.0 - sw) * (1.0 - vsh))
            return sum(scores) / len(scores) if scores else 0

        # Assign quality class to each interval
        def interval_class(intv):
            q = interval_quality(intv)
            avg_perm = sum(float(r['Permeability']) for r in intv) / len(intv)
            if q > 0.10 and avg_perm > 20:
                return 'BEST'
            elif q > 0.06 and avg_perm > 5:
                return 'GOOD'
            elif q > 0.03 and avg_perm > 0.5:
                return 'MEDIUM'
            else:
                return 'POOR'

        # Bucket intervals by class
        class_buckets = {'BEST': [], 'GOOD': [], 'MEDIUM': [], 'POOR': []}
        for iv in intervals:
            cls = interval_class(iv)
            class_buckets[cls].append(iv)

        # Sort each bucket by quality descending
        for cls in class_buckets:
            class_buckets[cls].sort(key=interval_quality, reverse=True)

        # Pick intervals to perforate ensuring class diversity
        total_netpay = sum(len(iv) for iv in intervals)
        total_target = max(30, int(total_netpay * 0.25))

        # Target row counts per class
        target_per_class = {
            'BEST':   max(8, int(total_target * 0.25)),
            'GOOD':   max(8, int(total_target * 0.35)),
            'MEDIUM': max(8, int(total_target * 0.25)),
            'POOR':   max(5, int(total_target * 0.15)),
        }

        perf_depths = set()
        # Fill each class bucket up to its target
        for cls, tgt in target_per_class.items():
            count = 0
            for iv in class_buckets[cls]:
                for r in iv:
                    if count >= tgt:
                        break
                    perf_depths.add(float(r['Depth']))
                    count += 1
                if count >= tgt:
                    break

        # Mark rows as perforated and assign rates
        for r in well_data:
            depth = float(r['Depth'])
            if depth in perf_depths:
                por = float(r['Porosity'])
                sw = float(r['Sw'])
                vsh = float(r['Vshale'])
                perm = float(r['Permeability'])
                pclass = assign_production_class(por, sw, vsh, perm)
                rate = assign_initial_rate(por, sw, vsh, perm, pclass)
                r['Is_Perforated'] = 'True'
                r['Production_Class'] = pclass
                r['Initial_Rate'] = str(rate)
                perf_count += 1

    print(f"  Perforated {perf_count} rows")
    return rows


# =============================================================================
# 3. GENERATE PRODUCTION HISTORY (sample_production_history.csv)
# =============================================================================
def generate_production_history(rows):
    """
    Generate monthly production history (2020-2024) for each well.
    Initial rate is derived from representative perforated intervals, not raw sum.
    Typical well initial rate: 300-1500 BOPD declining over 5 years.
    """
    # Calculate well initial rate: average of top-N perforated interval rates
    # multiplied by a realistic scale factor (not the raw petrophys row count)
    perf_by_well = {}
    for r in rows:
        if r['Is_Perforated'] == 'True' and r['Initial_Rate']:
            perf_by_well.setdefault(r['Well_Name'], []).append(
                float(r['Initial_Rate'])
            )

    history_rows = []
    # Production from Jan 2020 to Dec 2024 (60 months)
    months = []
    year = 2020
    month = 1
    for _ in range(60):
        months.append(f"{year}-{month:02d}-28")
        month += 1
        if month > 12:
            month = 1
            year += 1

    # Realistic initial rates per well (BOPD), not simple sum
    well_init_rates = {
        '24P': random.gauss(1100, 150),
        '25P': random.gauss(950, 120),
        '33P': random.gauss(1350, 200),
    }

    decline_rates = {
        '24P': 0.14,
        '25P': 0.18,
        '33P': 0.12,
    }

    for well_name in perf_by_well.keys():
        qi = max(100, well_init_rates.get(well_name, 800))
        d = decline_rates.get(well_name, 0.15)
        for i, date_str in enumerate(months):
            t_years = i / 12.0
            rate = qi * math.exp(-d * t_years)
            rate += random.gauss(0, rate * 0.04)  # 4% noise
            rate = max(1, round(rate, 1))
            history_rows.append({
                'Well_Name': well_name,
                'Date': date_str,
                'Oil_Rate': rate
            })

    return history_rows


# =============================================================================
# 4. GENERATE PLT DATA (sample_PLT.csv)
# =============================================================================
def generate_plt_data(rows):
    """
    Generate PLT (Production Logging Tool) measurements at 2-3 time points
    per well, with contribution percentages for each perforated interval.
    """
    # Find perforated intervals per well
    well_perfs = {}
    for r in rows:
        if r['Is_Perforated'] == 'True':
            well_perfs.setdefault(r['Well_Name'], []).append({
                'depth': float(r['Depth']),
                'perm': float(r['Permeability']),
                'por': float(r['Porosity'])
            })

    plt_rows = []
    # PLT measurement dates
    plt_dates = ['2021-06-15', '2022-06-15', '2023-06-15']

    for well_name, perfs in well_perfs.items():
        if len(perfs) < 3:
            continue

        # Sort by depth
        perfs.sort(key=lambda x: x['depth'])

        # Group contiguous depths into intervals (gap < 2m)
        intervals = []
        current = [perfs[0]]
        for p in perfs[1:]:
            if p['depth'] - current[-1]['depth'] < 2.0:
                current.append(p)
            else:
                intervals.append(current)
                current = [p]
        if current:
            intervals.append(current)

        if not intervals:
            continue

        # For each PLT date, assign contribution based on KH (perm * thickness)
        for date_str in plt_dates:
            total_kh = 0
            kh_values = []
            for iv in intervals:
                # Thickness ~ number of points in interval
                thick = len(iv) * 0.1
                avg_perm = sum(p['perm'] for p in iv) / len(iv)
                kh = avg_perm * thick
                kh_values.append(kh)
                total_kh += kh

            for iv, kh in zip(intervals, kh_values):
                if total_kh > 0:
                    # Add noise and time-variation
                    time_factor = 1.0
                    if date_str == '2022-06-15':
                        time_factor = random.uniform(0.7, 1.0)
                    elif date_str == '2023-06-15':
                        time_factor = random.uniform(0.5, 0.9)

                    pct = (kh / total_kh) * 100 * time_factor
                    # Normalize to sum to 100%
                else:
                    pct = 0

                # Round contribution
                pct = round(pct, 1)

                top = round(min(p['depth'] for p in iv), 2)
                base = round(max(p['depth'] for p in iv), 2)

                plt_rows.append({
                    'Well_Name': well_name,
                    'Date': date_str,
                    'Top': top,
                    'Base': base,
                    'Contribution_Pct': pct
                })

        # Normalize percentages per date so they sum to ~100%
        # This handles the time_factor randomization
        for date_str in plt_dates:
            date_rows = [r for r in plt_rows if r['Well_Name'] == well_name and r['Date'] == date_str]
            total_pct = sum(r['Contribution_Pct'] for r in date_rows)
            if total_pct > 0:
                for r in date_rows:
                    r['Contribution_Pct'] = round(r['Contribution_Pct'] / total_pct * 100, 1)

    return plt_rows


# =============================================================================
# 5. GENERATE ECONOMIC REFERENCE DATA (sample_econ_layers.csv)
# =============================================================================
def generate_econ_layers(rows):
    """
    Generate pre-computed economic analysis layers for the Economics page.
    Only include quality unperforated netpay intervals (BEST or GOOD).
    This mirrors what the ML Advisor would produce after training.
    """
    from collections import defaultdict

    well_netpay = defaultdict(list)
    for r in rows:
        # Only include unperforated rows that are quality netpay
        if r['Is_Perforated'] == 'False':
            por = float(r['Porosity'])
            sw = float(r['Sw'])
            vsh = float(r['Vshale'])
            perm = float(r['Permeability'])
            prod_class = assign_production_class(por, sw, vsh, perm)
            # Only consider BEST and GOOD classes for economic proposals
            if prod_class in ('BEST', 'GOOD') and is_netpay(r):
                well_netpay[r['Well_Name']].append({
                    'depth': float(r['Depth']),
                    'por': por,
                    'sw': sw,
                    'vsh': vsh,
                    'perm': perm,
                    'class': prod_class
                })

    econ_rows = []
    for well_name, points in well_netpay.items():
        points.sort(key=lambda x: x['depth'])

        # Group contiguous depths into intervals
        intervals = []
        current = [points[0]]
        for p in points[1:]:
            if p['depth'] - current[-1]['depth'] < 1.0:
                current.append(p)
            else:
                intervals.append(current)
                current = [p]
        if current:
            intervals.append(current)

        for iv in intervals:
            top = round(min(p['depth'] for p in iv), 2)
            base = round(max(p['depth'] for p in iv), 2)
            netpay = round(base - top, 2)
            if netpay < 0.5:
                continue  # Skip very thin layers

            # Get best class and average confidence
            classes = [p['class'] for p in iv]
            best_class = max(set(classes), key=classes.count)

            avg_por = sum(p['por'] for p in iv) / len(iv)
            avg_sw = sum(p['sw'] for p in iv) / len(iv)

            # Simulated confidence
            confidence = round(random.uniform(0.70, 0.98), 2)

            # Predicted Qo based on average quality
            quality = avg_por * (1.0 - avg_sw)
            if best_class == 'BEST':
                pred_qo = round(random.gauss(quality * 5000, 100), 1)
            elif best_class == 'GOOD':
                pred_qo = round(random.gauss(quality * 3000, 80), 1)
            else:
                pred_qo = round(random.gauss(quality * 1000, 50), 1)
            pred_qo = max(1, pred_qo)

            econ_rows.append({
                'Well_Name': well_name,
                'Top': top,
                'Base': base,
                'Predicted_Class': best_class,
                'Net_Pay': netpay,
                'Avg_Confidence': confidence,
                'Predicted_Qo': pred_qo
            })

    return econ_rows


# =============================================================================
# MAIN — Generate everything
# =============================================================================
if __name__ == '__main__':
    print("=" * 60)
    print("  GENERATING SAMPLE DATA FOR STREAMLIT DASHBOARD")
    print("=" * 60)

    # Step 1: Well log data
    print("\n[1/5] Generating well log data...")
    columns, rows = generate_well_log_data()
    print(f"  Created {len(rows)} rows for {len(WELLS)} wells")

    # Step 2: Assign perforations
    print("\n[2/5] Assigning perforations...")
    rows = assign_perforations(rows)

    # Stats
    perf_rows = [r for r in rows if r['Is_Perforated'] == 'True']
    print(f"  Total perforated: {len(perf_rows)}")
    print(f"  By class: {dict(Counter(r['Production_Class'] for r in perf_rows))}")
    print(f"  By well: {dict(Counter(r['Well_Name'] for r in perf_rows))}")

    # Write main CSV
    out_path = os.path.join(OUTPUT_DIR, 'sample_data.csv')
    with open(out_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    print(f"\n  [OK] Written: {out_path} ({os.path.getsize(out_path)/1024:.0f} KB)")

    # Step 3: Production history
    print("\n[3/5] Generating production history...")
    history_rows = generate_production_history(rows)
    hist_path = os.path.join(OUTPUT_DIR, 'sample_production_history.csv')
    with open(hist_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['Well_Name', 'Date', 'Oil_Rate'])
        writer.writeheader()
        writer.writerows(history_rows)
    print(f"  Created {len(history_rows)} monthly records")
    print(f"  [OK] Written: {hist_path}")

    # Step 4: PLT data
    print("\n[4/5] Generating PLT data...")
    plt_rows = generate_plt_data(rows)
    plt_path = os.path.join(OUTPUT_DIR, 'sample_PLT.csv')
    with open(plt_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['Well_Name', 'Date', 'Top', 'Base', 'Contribution_Pct'])
        writer.writeheader()
        writer.writerows(plt_rows)
    print(f"  Created {len(plt_rows)} PLT measurements")
    print(f"  [OK] Written: {plt_path}")

    # Step 5: Economic layers (pre-computed proposals)
    print("\n[5/5] Generating economic analysis layers...")
    econ_rows = generate_econ_layers(rows)
    econ_path = os.path.join(OUTPUT_DIR, 'sample_econ_layers.csv')
    with open(econ_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'Well_Name', 'Top', 'Base', 'Predicted_Class',
            'Net_Pay', 'Avg_Confidence', 'Predicted_Qo'
        ])
        writer.writeheader()
        writer.writerows(econ_rows)
    print(f"  Created {len(econ_rows)} potential layers")
    print(f"  [OK] Written: {econ_path}")

    # Summary
    print("\n" + "=" * 60)
    print("  GENERATION COMPLETE")
    print("=" * 60)
    print(f"  sample_data.csv               : {len(rows):>6} rows  (main well log data)")
    print(f"  sample_production_history.csv  : {len(history_rows):>6} rows  (monthly production)")
    print(f"  sample_PLT.csv                 : {len(plt_rows):>6} rows  (PLT measurements)")
    print(f"  sample_econ_layers.csv         : {len(econ_rows):>6} rows  (pre-computed proposals)")
    print()
    print(f"  All files at: {OUTPUT_DIR}")
