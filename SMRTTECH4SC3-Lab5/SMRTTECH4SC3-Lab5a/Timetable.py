import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib.cm as cm
import numpy as np
from matplotlib.lines import Line2D
import os

# ── CONFIG ──────────────────────────────────────────────────────────────
XML_FILE  = "Result.xml"
STATIONS  = ['S1', 'S2', 'S3', 'S4']
STATION_MAP = {'ts_0':'S1', 'ts_1':'S2', 'ts_2':'S3', 'ts_3':'S4'}

INT_FMT = ticker.FuncFormatter(lambda x, _: f"{int(x)}")
# ────────────────────────────────────────────────────────────────────────

if not os.path.exists(XML_FILE):
    XML_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), XML_FILE)

tree = ET.parse(XML_FILE)
root = tree.getroot()

# Parse stop output — compute until = ended - delay directly from XML
trains = {}
for stop in root.findall('stopinfo'):
    tid     = stop.get('id')
    station = STATION_MAP.get(stop.get('busStop'), stop.get('busStop'))
    started = float(stop.get('started', 0))
    ended   = float(stop.get('ended',   0))
    delay   = float(stop.get('delay',   0))
    until   = ended - delay          # until = scheduled departure

    if tid not in trains:
        trains[tid] = {}
    trains[tid][station] = {
        'started': started,
        'ended':   ended,
        'delay':   delay,
        'until':   until,
    }

sorted_trains = sorted(trains.keys())
MATLAB_COLORS = ['#0072BD', '#D95319', '#EDB120', '#7E2F8E', '#77AC30', '#4DBEEE', '#A2142F']
color_map = {tid: MATLAB_COLORS[i % len(MATLAB_COLORS)] for i, tid in enumerate(sorted_trains)}
x_pos = list(range(len(STATIONS)))

# ── CHART 1: Schedule Overview (Arrivals + Departures + Dwell) ───────────
fig1, ax1 = plt.subplots(figsize=(15, 9))
for tid in sorted_trains:
    d     = trains[tid]
    color = color_map[tid]
    xs = [i for i, s in enumerate(STATIONS) if s in d]
    ys = [d[s]['started'] for s in STATIONS if s in d]
    ye = [d[s]['ended']   for s in STATIONS if s in d]

    ax1.plot(xs, ys, color=color, linestyle='-',  marker='o',
             markersize=7, linewidth=2, label=tid)
    ax1.plot(xs, ye, color=color, linestyle='--', marker='s',
             markersize=4, linewidth=1.2)
    for i, s in enumerate(STATIONS):
        if s in d:
            ax1.plot([i, i], [d[s]['started'], d[s]['ended']],
                     color=color, linewidth=3, alpha=0.5)

    for x, y_arr, y_dep in zip(xs, ys, ye):
        ax1.annotate(f"{int(round(y_arr))}",
                     xy=(x, y_arr), xytext=(7, -10),
                     textcoords='offset points',
                     ha='left', va='top',
                     fontsize=8, color=color, fontweight='bold')
        ax1.annotate(f"{int(round(y_dep))}",
                     xy=(x, y_dep), xytext=(7, 7),
                     textcoords='offset points',
                     ha='left', va='bottom',
                     fontsize=8, color=color, fontweight='bold')

ax1.set_xticks(x_pos)
ax1.set_xticklabels(STATIONS, fontsize=15)
ax1.set_xlabel('Station', fontsize=18)
ax1.set_ylabel('Time (s)', fontsize=18)
ax1.set_title('Chart 1 — Train Schedule: Arrivals, Departures & Dwell Time',
              fontsize=16)
ax1.yaxis.grid(True, linestyle='--', alpha=0.4)
ax1.tick_params(axis='y', labelsize=16)
ax1.yaxis.set_major_formatter(INT_FMT)
legend_handles = [
    Line2D([0],[0], linestyle='-',  marker='o', color='gray',
           markersize=7, label='Arrival'),
    Line2D([0],[0], linestyle='--', marker='s', color='gray',
           markersize=4, label='Departure'),
    Line2D([0],[0], linestyle='-',  linewidth=3, color='gray',
           alpha=0.5, label='Dwell time'),
]
for tid in sorted_trains:
    legend_handles.append(
        Line2D([0],[0], linestyle='-', marker='o',
               color=color_map[tid], markersize=6, label=tid)
    )
ax1.legend(handles=legend_handles, fontsize=10, loc='upper left')
ax1.margins(y=0.15)
plt.tight_layout()
plt.savefig('chart1_schedule.png', dpi=150, bbox_inches='tight')
print("Saved: chart1_schedule.png")

# ── CHART 2: Schedule + Until (Arrivals + Departures + Dwell + Scheduled Until) ──
fig2, ax2 = plt.subplots(figsize=(15, 9))
for tid in sorted_trains:
    d     = trains[tid]
    color = color_map[tid]
    xs = [i for i, s in enumerate(STATIONS) if s in d]
    ys = [d[s]['started'] for s in STATIONS if s in d]
    ye = [d[s]['ended']   for s in STATIONS if s in d]
    yu = [d[s]['until']   for s in STATIONS if s in d]

    # Arrival line
    ax2.plot(xs, ys, color=color, linestyle='-',  marker='o',
             markersize=7, linewidth=2, label=tid)
    # Departure line
    ax2.plot(xs, ye, color=color, linestyle='--', marker='s',
             markersize=4, linewidth=1.2)
    # Dwell bar
    for i, s in enumerate(STATIONS):
        if s in d:
            ax2.plot([i, i], [d[s]['started'], d[s]['ended']],
                     color=color, linewidth=3, alpha=0.5)
    # Scheduled until line
    ax2.plot(xs, yu, color=color, linestyle=':', marker='^',
             markersize=6, linewidth=1.5, alpha=0.85)

    # Labels — arrival bottom-right, departure top-right, until italic left
    for x, y_arr, y_dep, y_u in zip(xs, ys, ye, yu):
        ax2.annotate(f"{int(round(y_arr))}",
                     xy=(x, y_arr), xytext=(7, -10),
                     textcoords='offset points',
                     ha='left', va='top',
                     fontsize=8, color=color, fontweight='bold')
        ax2.annotate(f"{int(round(y_dep))}",
                     xy=(x, y_dep), xytext=(7, 7),
                     textcoords='offset points',
                     ha='left', va='bottom',
                     fontsize=8, color=color, fontweight='bold')
        ax2.annotate(f"{int(round(y_u))}",
                     xy=(x, y_u), xytext=(-7, 7),
                     textcoords='offset points',
                     ha='right', va='bottom',
                     fontsize=8, color=color, fontweight='bold',
                     style='italic')

ax2.set_xticks(x_pos)
ax2.set_xticklabels(STATIONS, fontsize=15)
ax2.set_xlabel('Station', fontsize=18)
ax2.set_ylabel('Time (s)', fontsize=18)
ax2.set_title('Chart 2 — Train Schedule: Arrivals, Departures, Dwell & Scheduled Time\n'
              ,
              fontsize=16)
ax2.yaxis.grid(True, linestyle='--', alpha=0.4)
ax2.tick_params(axis='y', labelsize=16)
ax2.yaxis.set_major_formatter(INT_FMT)
legend_handles2 = [
    Line2D([0],[0], linestyle='-',  marker='o',  color='gray',
           markersize=7, label='Arrival'),
    Line2D([0],[0], linestyle='--', marker='s',  color='gray',
           markersize=4, label='Departure'),
    Line2D([0],[0], linestyle='-',  linewidth=3, color='gray',
           alpha=0.5,   label='Dwell time'),
    Line2D([0],[0], linestyle=':',  marker='^',  color='gray',
           markersize=6, label='Scheduled'),
]
for tid in sorted_trains:
    legend_handles2.append(
        Line2D([0],[0], linestyle='-', marker='o',
               color=color_map[tid], markersize=6, label=tid)
    )
ax2.legend(handles=legend_handles2, fontsize=10, loc='upper left')
ax2.margins(y=0.15)
plt.tight_layout()
plt.savefig('chart2_schedule_detailed.png', dpi=150, bbox_inches='tight')
print("Saved: chart2_schedule_detailed.png")

plt.show()
print("\nBoth charts generated successfully.")