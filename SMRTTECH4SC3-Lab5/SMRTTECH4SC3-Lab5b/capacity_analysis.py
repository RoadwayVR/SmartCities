import xml.etree.ElementTree as ET
import sys
sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None
import matplotlib.pyplot as plt
import numpy as np
import os

# -- CONFIG --------------------------------------------------------------
SCENARIOS = {
    'Scenario 1': 'Result_Scenario1.xml',
    'Scenario 2': 'Result_Scenario2.xml',
    'Scenario 3': 'Result_Scenario3.xml',
    'Scenario 4': 'Result_Scenario4.xml',
}

COUNT_WINDOW  = 600
FINAL_STATION = 'S4'
STATION_MAP   = {'ts_0':'S1', 'ts_1':'S2', 'ts_2':'S3', 'ts_3':'S4'}
STATIONS      = ['S1', 'S2', 'S3', 'S4']
MATLAB_COLORS = ['#0072BD', '#D95319', '#EDB120', '#7E2F8E']
# ------------------------------------------------------------------------

def parse_stop_file(filepath):
    if not os.path.exists(filepath):
        filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), filepath)
    tree = ET.parse(filepath)
    root = tree.getroot()
    trains = {}
    for stop in root.findall('stopinfo'):
        tid     = stop.get('id')
        station = STATION_MAP.get(stop.get('busStop'), stop.get('busStop'))
        started = float(stop.get('started', 0))
        ended   = float(stop.get('ended',   0))
        delay   = float(stop.get('delay',   0))
        if tid not in trains:
            trains[tid] = {}
        trains[tid][station] = {'started': started, 'ended': ended, 'delay': delay}
    return trains

def compute_capacity(trains):
    return [tid for tid, stops in trains.items()
            if FINAL_STATION in stops
            and stops[FINAL_STATION]['started'] <= COUNT_WINDOW]

def compute_avg_dwell(trains):
    dwells = []
    for stops in trains.values():
        for s in STATIONS:
            if s in stops:
                dwells.append(stops[s]['ended'] - stops[s]['started'])
    return round(np.mean(dwells), 1) if dwells else 0

def compute_avg_running_time(trains):
    rts = []
    for stops in trains.values():
        for i in range(1, len(STATIONS)):
            sp, sc = STATIONS[i-1], STATIONS[i]
            if sp in stops and sc in stops:
                rt = stops[sc]['started'] - stops[sp]['ended']
                if rt > 0:
                    rts.append(rt)
    return round(np.mean(rts), 1) if rts else 0

def compute_avg_delay(trains):
    delays = []
    for stops in trains.values():
        for s in STATIONS:
            if s in stops:
                delays.append(stops[s]['delay'])
    return round(np.mean(delays), 1) if delays else 0

# -- MAIN -----------------------------------------------------------------
results = {}

print("=" * 60)
print(f"CAPACITY ANALYSIS — trains reaching S4 within {COUNT_WINDOW}s")
print("=" * 60)

for scenario, filepath in SCENARIOS.items():
    fp = filepath
    if not os.path.exists(fp):
        fp = os.path.join(os.path.dirname(os.path.abspath(__file__)), filepath)
    if not os.path.exists(fp):
        print(f"\n  [{scenario}] File not found: {filepath} — skipping")
        continue

    trains    = parse_stop_file(fp)
    completed = compute_capacity(trains)
    capacity  = len(completed)
    avg_dwell = compute_avg_dwell(trains)
    avg_rt    = compute_avg_running_time(trains)
    avg_delay = compute_avg_delay(trains)

    results[scenario] = {
        'capacity':       capacity,
        'avg_dwell':      avg_dwell,
        'avg_rt':         avg_rt,
        'avg_delay':      avg_delay,
        'total_inserted': len(trains),
    }

    print(f"\n  Scenario       : {scenario}")
    print(f"  -------------------------------------")
    print(f"  Total trains inserted    : {len(trains)}")
    print(f"  Trains at S4 within {COUNT_WINDOW}s : {capacity}")
    print(f"  Avg dwell time           : {avg_dwell}s")
    print(f"  Avg running time/segment : {avg_rt}s")
    print(f"  Avg delay                : {avg_delay}s")

print("\n" + "=" * 60)

# -- BAR CHART -------------------------------------------------------------
if results:
    scenario_names = list(results.keys())
    colors = MATLAB_COLORS[:len(scenario_names)]
    x = np.arange(len(scenario_names))
    bar_w = 0.55

    fig, axes = plt.subplots(1, 3, figsize=(15, 6))

    # Capacity
    caps  = [results[s]['capacity'] for s in scenario_names]
    bars1 = axes[0].bar(x, caps, color=colors, width=bar_w, edgecolor='white')
    axes[0].set_title(f'Capacity\n(trains reaching S4)', fontsize=13)
    axes[0].set_ylabel('Trains', fontsize=12)
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(scenario_names, fontsize=10, rotation=15, ha='right')
    axes[0].yaxis.set_major_locator(plt.MaxNLocator(integer=True))
    axes[0].margins(y=0.25)
    for b, v in zip(bars1, caps):
        axes[0].text(b.get_x()+b.get_width()/2, b.get_height()+0.05,
                     str(v), ha='center', va='bottom', fontsize=12, fontweight='bold')

    # Avg Dwell
    dwells = [results[s]['avg_dwell'] for s in scenario_names]
    bars2  = axes[1].bar(x, dwells, color=colors, width=bar_w, edgecolor='white')
    axes[1].set_title('Avg Dwell Time\n(all stations)', fontsize=13)
    axes[1].set_ylabel('Seconds', fontsize=12)
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(scenario_names, fontsize=10, rotation=15, ha='right')
    axes[1].margins(y=0.2)
    for b, v in zip(bars2, dwells):
        axes[1].text(b.get_x()+b.get_width()/2, b.get_height()+0.3,
                     str(v), ha='center', va='bottom', fontsize=12, fontweight='bold')

    # Avg Running Time
    rts   = [results[s]['avg_rt'] for s in scenario_names]
    bars3 = axes[2].bar(x, rts, color=colors, width=bar_w, edgecolor='white')
    axes[2].set_title('Avg Running Time\n(per segment)', fontsize=13)
    axes[2].set_ylabel('Seconds', fontsize=12)
    axes[2].set_xticks(x)
    axes[2].set_xticklabels(scenario_names, fontsize=10, rotation=15, ha='right')
    axes[2].margins(y=0.2)
    for b, v in zip(bars3, rts):
        axes[2].text(b.get_x()+b.get_width()/2, b.get_height()+0.3,
                     str(v), ha='center', va='bottom', fontsize=12, fontweight='bold')

    for ax in axes:
        ax.yaxis.grid(True, linestyle='--', alpha=0.4)
        ax.set_axisbelow(True)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.tick_params(axis='y', labelsize=11)

    plt.suptitle(
        f'Capacity Analysis — All Scenarios\n(measurement window: {COUNT_WINDOW}s)',
        fontsize=13, fontweight='bold', y=1.02
    )
    plt.tight_layout()
    plt.savefig('capacity_analysis.png', dpi=150, bbox_inches='tight')
    print("Saved: capacity_analysis.png")
    plt.show()

print("\nDone.")