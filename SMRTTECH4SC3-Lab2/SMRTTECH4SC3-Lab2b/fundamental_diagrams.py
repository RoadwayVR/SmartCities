# -*- coding: utf-8 -*-
"""
SUMO Fundamental Diagram Plotter - Greenshields Model
======================================================
Accepts a SUMO edgeData XML output file (meandata format) and produces
Greenshields fundamental diagrams either:
  - Per-edge (one row of 3 diagrams per edge) [default]
  - All edges combined (--combine)
  - Specific edges only (--edges E3 E7)

Three diagrams per edge/group:
  1. Speed-Density  (v-k)   <- R2 shown here
  2. Flow-Density   (q-k)
  3. Speed-Flow     (v-q)   <- v on y-axis, q on x-axis

Usage:
    Just press Run in VS Code - edit the CONFIG section below to change settings.
"""

import xml.etree.ElementTree as ET
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
import os
import sys
from collections import defaultdict

# Fix Windows terminal encoding
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ==============================================================================
# CONFIG - edit these to change behaviour
# ==============================================================================
XML_FILE   = "DiagramsBaseScenario.xml"           # XML file name (must be in the same folder as this script)
EDGES      = []  # set to [] for all edges
COMBINE    = False              # True = one combined diagram, False = per-edge rows
OUTPUT     = "fundamental_diagrams_output.png"  # output image filename
# ==============================================================================

# Styling
SCATTER_COLOR = "#378ADD"
FIT_COLOR     = "#D85A30"
CRIT_COLOR    = "#1D9E75"
GRID_COLOR    = "#DDDDDD"
FIG_BG        = "#FAFAFA"

plt.rcParams.update({
    "font.family":       "DejaVu Sans",
    "axes.spines.top":   False,
    "axes.spines.right": False,
    "axes.grid":         True,
    "grid.color":        GRID_COLOR,
    "grid.linewidth":    0.6,
    "figure.facecolor":  FIG_BG,
    "axes.facecolor":    FIG_BG,
})

# XML Parser
def parse_edgedata(filepath, edge_filter=None):
    tree = ET.parse(filepath)
    root = tree.getroot()
    data = defaultdict(lambda: {"k": [], "v": [], "q": []})

    for interval in root.findall("interval"):
        for edge in interval.findall("edge"):
            eid = edge.get("id")
            if edge_filter and eid not in edge_filter:
                continue
            k = float(edge.get("density", 0))
            v = float(edge.get("speed",   0))
            q = float(edge.get("flow",    0))
            if k <= 0 or v <= 0:
                continue
            data[eid]["k"].append(k)
            data[eid]["v"].append(v)
            data[eid]["q"].append(q)

    result = {}
    for eid, d in data.items():
        if len(d["k"]) >= 3:
            result[eid] = {
                "k": np.array(d["k"]),
                "v": np.array(d["v"]),
                "q": np.array(d["q"]),
            }
    return result

# Greenshields Fit
def greenshields_fit(k, v):
    slope, intercept, r, p, se = stats.linregress(k, v)
    vf = intercept
    kj = -vf / slope if slope != 0 else np.nan
    r2 = r ** 2
    return vf, kj, r2

def greenshields_curve(vf, kj, n=300):
    k_c = np.linspace(0, max(kj, 0.01), n)
    v_c = np.maximum(0, vf * (1 - k_c / kj))
    q_c = v_c * k_c
    return k_c, v_c, q_c

# Single Row of 3 Diagrams
def draw_row(axes, k, v, q, vf, kj, r2, edge_label):
    kc   = kj / 2
    vc   = vf / 2
    qmax = vf * kj / 4
    k_curve, v_curve, q_curve = greenshields_curve(vf, kj)

    scatter_kw = dict(color=SCATTER_COLOR, alpha=0.55, s=22, zorder=3, label="Observations")
    fit_kw     = dict(color=FIT_COLOR, lw=2, label="Greenshields fit")
    crit_kw    = dict(color=CRIT_COLOR, s=80, zorder=5, marker="^")

    # 1. Speed-Density (v-k)
    ax = axes[0]
    ax.scatter(k, v, **scatter_kw)
    ax.plot(k_curve, v_curve, **fit_kw)
    ax.scatter([kc], [vc], **crit_kw,
               label=f"Critical  $k_c$={kc:.0f}, $v_c$={vc:.1f}")
    ax.axvline(kc, color=CRIT_COLOR, lw=0.7, ls="--", alpha=0.5)
    ax.axhline(vc, color=CRIT_COLOR, lw=0.7, ls="--", alpha=0.5)
    ax.set_xlabel("Density  $k$  (veh/km)", fontsize=9)
    ax.set_ylabel("Speed  $v$  (m/s)", fontsize=9)
    ax.set_title(
        f"{edge_label} - Speed-Density  ($v$-$k$)\n"
        f"R2={r2:.3f}  |  $v_f$={vf:.1f} m/s  |  $k_j$={kj:.0f} veh/km",
        fontsize=9, pad=4
    )
    ax.legend(fontsize=7)

    # 2. Flow-Density (q-k)
    ax = axes[1]
    ax.scatter(k, q, **scatter_kw)
    ax.plot(k_curve, q_curve, **fit_kw)
    ax.scatter([kc], [qmax], **crit_kw,
               label=f"Capacity  $q_{{max}}$={qmax:.0f}")
    ax.axvline(kc, color=CRIT_COLOR, lw=0.7, ls="--", alpha=0.5)
    ax.axhline(qmax, color=CRIT_COLOR, lw=0.7, ls="--", alpha=0.5)
    ax.set_xlabel("Density  $k$  (veh/km)", fontsize=9)
    ax.set_ylabel("Flow  $q$  (veh/h)", fontsize=9)
    ax.set_title("Flow-Density  ($q$-$k$)", fontsize=9, pad=4)
    ax.legend(fontsize=7)

    # 3. Speed-Flow (v-q)
    ax = axes[2]
    ax.scatter(q, v, **scatter_kw)
    ax.plot(q_curve, v_curve, **fit_kw)
    ax.scatter([qmax], [vc], **crit_kw,
               label=f"Capacity  $q_{{max}}$={qmax:.0f}, $v_c$={vc:.1f}")
    ax.axvline(qmax, color=CRIT_COLOR, lw=0.7, ls="--", alpha=0.5)
    ax.axhline(vc,   color=CRIT_COLOR, lw=0.7, ls="--", alpha=0.5)
    ax.set_xlabel("Flow  $q$  (veh/h)", fontsize=9)
    ax.set_ylabel("Speed  $v$  (m/s)", fontsize=9)
    ax.set_title("Speed-Flow  ($v$-$q$)", fontsize=9, pad=4)
    ax.legend(fontsize=7)

# Per-Edge Figure
def plot_per_edge(edge_data, output_path, xml_name):
    edge_ids = sorted(edge_data.keys())
    n_edges  = len(edge_ids)

    fig, axes = plt.subplots(
        n_edges, 3,
        figsize=(15, 4.2 * n_edges),
        facecolor=FIG_BG,
        squeeze=False
    )
    fig.suptitle(
        f"Greenshields Fundamental Diagrams - Per Edge\n{xml_name}",
        fontsize=13, y=1.002
    )

    print(f"\n{'Edge':<6}  {'vf (m/s)':>10}  {'kj (v/km)':>10}  {'kc (v/km)':>10}  {'qmax (v/h)':>11}  {'R2':>7}")
    print("-" * 64)

    for i, eid in enumerate(edge_ids):
        d = edge_data[eid]
        k, v, q = d["k"], d["v"], d["q"]
        vf, kj, r2 = greenshields_fit(k, v)
        kc   = kj / 2
        qmax = vf * kj / 4
        print(f"{eid:<6}  {vf:>10.2f}  {kj:>10.1f}  {kc:>10.1f}  {qmax:>11.0f}  {r2:>7.4f}")
        draw_row(axes[i], k, v, q, vf, kj, r2, edge_label=f"Edge {eid}")

    plt.tight_layout()
    plt.savefig(output_path, dpi=160, bbox_inches="tight")
    print(f"\nOK Saved: {output_path}")
    plt.show()

# Combined Figure
def plot_combined(edge_data, output_path, xml_name):
    k = np.concatenate([d["k"] for d in edge_data.values()])
    v = np.concatenate([d["v"] for d in edge_data.values()])
    q = np.concatenate([d["q"] for d in edge_data.values()])

    vf, kj, r2 = greenshields_fit(k, v)
    kc   = kj / 2
    qmax = vf * kj / 4

    fig, axes = plt.subplots(1, 3, figsize=(15, 5), facecolor=FIG_BG)
    fig.suptitle(
        f"Greenshields Fundamental Diagrams - All Edges Combined\n{xml_name}\n"
        f"$v_f$={vf:.2f} m/s  |  $k_j$={kj:.1f} veh/km  |  "
        f"$q_{{max}}$={qmax:.0f} veh/h  |  $k_c$={kc:.1f} veh/km  |  R2={r2:.3f}",
        fontsize=11, y=1.02
    )
    draw_row(axes, k, v, q, vf, kj, r2, edge_label="All edges")
    plt.tight_layout()
    plt.savefig(output_path, dpi=160, bbox_inches="tight")
    print(f"OK Saved: {output_path}")
    plt.show()

# Run
if __name__ == "__main__":
    # Resolve XML path relative to this script's folder
    script_dir = os.path.dirname(os.path.abspath(__file__))
    xml_path   = os.path.join(script_dir, XML_FILE)
    out_path   = os.path.join(script_dir, OUTPUT)

    if not os.path.exists(xml_path):
        print(f"Error: could not find '{XML_FILE}' in {script_dir}")
        print("Make sure aa.xml is in the same folder as this script.")
        raise SystemExit(1)

    edge_filter = set(EDGES) if EDGES else None
    edge_data   = parse_edgedata(xml_path, edge_filter)

    if not edge_data:
        print("Error: no valid data found. Check EDGES list or XML file.")
        raise SystemExit(1)

    total_obs = sum(len(d["k"]) for d in edge_data.values())
    print(f"OK Loaded {total_obs} observations across {len(edge_data)} edges from {XML_FILE}")

    xml_name = os.path.basename(xml_path)
    if COMBINE:
        plot_combined(edge_data, out_path, xml_name)
    else:
        plot_per_edge(edge_data, out_path, xml_name)