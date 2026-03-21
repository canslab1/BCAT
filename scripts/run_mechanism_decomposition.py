#!/usr/bin/env python3
"""
Mechanism Decomposition Experiments for BCAT Model (R1-2 Response)

Three experiments to disentangle the opinion clustering channel
and the coordination failure channel in the opinion-adoption gap.

MD-A: Coordination Failure Channel Isolated (opinion dynamics disabled)
MD-B: Opinion Clustering Channel Isolated (adoption dynamics disabled)
MD-C: Full BCAT Baseline (both channels active)

Output: CSV files + matplotlib figures saved to PLOS-BCAT/figures/
"""

import sys
import os
import time
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # headless
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

# ── paths ──────────────────────────────────────────────────────
BCAT_DIR  = os.path.expanduser(
    "~/Dropbox/文件/我的程式/Github/BCAT")
PLOS_DIR  = os.path.expanduser(
    "~/Dropbox/文件/我的程式/Github/PLOS-BCAT")
OUT_DIR   = os.path.join(PLOS_DIR, "data", "mechanism_decomposition")
FIG_DIR   = os.path.join(PLOS_DIR, "figures")

os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(FIG_DIR, exist_ok=True)

sys.path.insert(0, BCAT_DIR)
os.environ['TK_SILENCE_DEPRECATION'] = '1'
from BCAT import OpinionAdoptionModel

# ── experiment parameters ──────────────────────────────────────
THRESHOLD_SWEEP = [10, 20, 30, 40, 50, 60, 70]
N_EXPERIMENTS   = 1000
MAX_TIME        = 300
NETWORK_TYPE    = "SWN/RN/CA"   # regular lattice when rewiring=0
REWIRING_PROB   = 0.00

# small-world comparison
REWIRING_PROB_SW = 0.10


# ── helper ─────────────────────────────────────────────────────
def run_batch(params: dict, label: str, n_exp: int = N_EXPERIMENTS):
    """
    Run n_exp simulations with given params.
    Returns list of dicts with per-run FRI and GSI at final tick.
    """
    records = []
    t0 = time.time()
    for i in range(n_exp):
        m = OpinionAdoptionModel()
        # apply params
        for k, v in params.items():
            setattr(m, k, v)
        m.max_time = MAX_TIME
        m.setup()
        result = m.go(exp_id=i)   # list of (adopters, non_adopters, mean_att, std_att)

        states = m._states
        N = states.shape[0]
        fri = float(np.sum(states[:, 0] > 50)) / N
        gsi = float(np.sum(states[:, 2] != 0.0)) / N
        adopters_final = result[-1][0] if result else 0

        records.append({
            'experiment': i,
            'fri': fri,
            'gsi': gsi,
            'adopters': adopters_final,
            'N': N,
        })
        if (i + 1) % 100 == 0:
            elapsed = time.time() - t0
            print(f"  {label}: {i+1}/{n_exp}  ({elapsed:.1f}s)")

    elapsed = time.time() - t0
    print(f"  {label}: done in {elapsed:.1f}s  "
          f"(mean FRI={np.mean([r['fri'] for r in records]):.4f}, "
          f"mean GSI={np.mean([r['gsi'] for r in records]):.4f})")
    return records


# ══════════════════════════════════════════════════════════════
#  EXPERIMENT MD-A : Coordination Failure Isolated
#  - All non-pioneers: att = 80 (clipped), FRI = 1.0 guaranteed
#  - bounded_confidence = 10 → no effective opinion exchange
#  - Sweep avg_of_thresholds
# ══════════════════════════════════════════════════════════════
def run_md_a(rewiring=REWIRING_PROB, tag="lattice"):
    print(f"\n{'='*60}")
    print(f"MD-A: Coordination Failure Isolated  ({tag})")
    print(f"{'='*60}")
    all_records = []
    for thr in THRESHOLD_SWEEP:
        params = dict(
            avg_of_attitudes   = 80,
            std_of_attitudes   = 0,
            bounded_confidence = 10,      # slider minimum
            no_of_pioneers     = 5,
            clustered_pioneers = True,
            avg_of_thresholds  = thr,
            std_of_thresholds  = 10,
            network_type       = NETWORK_TYPE,
            rewiring_probability = rewiring,
        )
        label = f"MD-A thr={thr}"
        recs = run_batch(params, label)
        for r in recs:
            r['avg_of_thresholds'] = thr
            r['experiment_id'] = 'MD-A'
            r['topology'] = tag
        all_records.extend(recs)
    return pd.DataFrame(all_records)


# ══════════════════════════════════════════════════════════════
#  EXPERIMENT MD-B : Opinion Clustering Isolated
#  - no_of_pioneers = 0 → GSI = 0 throughout
#  - Records FRI at t=300 as the opinion clustering effect
# ══════════════════════════════════════════════════════════════
def run_md_b(rewiring=REWIRING_PROB, tag="lattice"):
    print(f"\n{'='*60}")
    print(f"MD-B: Opinion Clustering Isolated  ({tag})")
    print(f"{'='*60}")
    params = dict(
        avg_of_attitudes   = 50,
        std_of_attitudes   = 15,
        bounded_confidence = 50,
        no_of_pioneers     = 0,
        clustered_pioneers = True,
        avg_of_thresholds  = 30,     # irrelevant (no adoption)
        std_of_thresholds  = 10,
        network_type       = NETWORK_TYPE,
        rewiring_probability = rewiring,
    )
    label = "MD-B"
    recs = run_batch(params, label)
    for r in recs:
        r['avg_of_thresholds'] = 0   # N/A
        r['experiment_id'] = 'MD-B'
        r['topology'] = tag
    return pd.DataFrame(recs)


# ══════════════════════════════════════════════════════════════
#  EXPERIMENT MD-C : Full BCAT Baseline
#  - Same opinion params as MD-B, plus pioneers
#  - Records both FRI and GSI
# ══════════════════════════════════════════════════════════════
def run_md_c(rewiring=REWIRING_PROB, tag="lattice"):
    print(f"\n{'='*60}")
    print(f"MD-C: Full BCAT Baseline  ({tag})")
    print(f"{'='*60}")
    all_records = []
    for thr in THRESHOLD_SWEEP:
        params = dict(
            avg_of_attitudes   = 50,
            std_of_attitudes   = 15,
            bounded_confidence = 50,
            no_of_pioneers     = 5,
            clustered_pioneers = True,
            avg_of_thresholds  = thr,
            std_of_thresholds  = 10,
            network_type       = NETWORK_TYPE,
            rewiring_probability = rewiring,
        )
        label = f"MD-C thr={thr}"
        recs = run_batch(params, label)
        for r in recs:
            r['avg_of_thresholds'] = thr
            r['experiment_id'] = 'MD-C'
            r['topology'] = tag
        all_records.extend(recs)
    return pd.DataFrame(all_records)


# ══════════════════════════════════════════════════════════════
#  PLOTTING
# ══════════════════════════════════════════════════════════════
def plot_results(df_a, df_b, df_c, tag="lattice"):
    """Create two-panel decomposition figure."""

    # ── aggregate ──
    agg_a = df_a.groupby('avg_of_thresholds').agg(
        gsi_mean=('gsi', 'mean'), gsi_std=('gsi', 'std'),
        fri_mean=('fri', 'mean')).reset_index()

    fri_b_mean = df_b['fri'].mean()
    fri_b_std  = df_b['fri'].std()

    agg_c = df_c.groupby('avg_of_thresholds').agg(
        gsi_mean=('gsi', 'mean'), gsi_std=('gsi', 'std'),
        fri_mean=('fri', 'mean'), fri_std=('fri', 'std')).reset_index()

    # ── figure ──
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5), dpi=150)
    fig.subplots_adjust(wspace=0.30, top=0.88)

    thr_vals = agg_a['avg_of_thresholds'].values

    # ── Panel (a): MD-A — coordination failure profile ──
    ax1.errorbar(thr_vals, agg_a['gsi_mean'], yerr=agg_a['gsi_std'],
                 fmt='s-', color='#2166AC', capsize=4, linewidth=2,
                 markersize=7, label='GSI (MD-A)')
    ax1.axhline(1.0, color='#B2182B', linestyle='--', linewidth=1.5,
                label='FRI = 1.0 (by construction)')
    # shade coordination failure
    ax1.fill_between(thr_vals, agg_a['gsi_mean'], 1.0,
                     alpha=0.15, color='#2166AC',
                     label='Coordination failure gap')
    ax1.set_xlabel('avg-of-thresholds', fontsize=12)
    ax1.set_ylabel('Index value', fontsize=12)
    ax1.set_title('(a) MD-A: Coordination Failure Channel Isolated',
                  fontsize=11, fontweight='bold')
    ax1.set_ylim(-0.02, 1.05)
    ax1.set_xlim(5, 75)
    ax1.xaxis.set_major_locator(MultipleLocator(10))
    ax1.legend(loc='lower left', fontsize=9)
    ax1.grid(True, alpha=0.3)

    # ── Panel (b): MD-C — full decomposition ──
    opinion_gap = 1.0 - agg_c['fri_mean'].values
    coord_gap   = agg_c['fri_mean'].values - agg_c['gsi_mean'].values

    ax2.fill_between(thr_vals, 0, opinion_gap,
                     alpha=0.5, color='#D6604D',
                     label=f'Opinion clustering (1−FRI)')
    ax2.fill_between(thr_vals, opinion_gap, opinion_gap + coord_gap,
                     alpha=0.5, color='#4393C3',
                     label='Coordination failure (FRI−GSI)')
    ax2.plot(thr_vals, opinion_gap + coord_gap,
             'ko-', linewidth=2, markersize=6,
             label='Total gap (1−GSI)')
    # FRI from MD-B as reference
    ax2.axhline(1.0 - fri_b_mean, color='#D6604D', linestyle=':',
                linewidth=1.5,
                label=f'MD-B opinion gap = {1-fri_b_mean:.3f}')
    ax2.set_xlabel('avg-of-thresholds', fontsize=12)
    ax2.set_ylabel('Adoption gap (1 − index)', fontsize=12)
    ax2.set_title('(b) MD-C: Decomposition of Total Adoption Gap',
                  fontsize=11, fontweight='bold')
    ax2.set_ylim(-0.02, 1.05)
    ax2.set_xlim(5, 75)
    ax2.xaxis.set_major_locator(MultipleLocator(10))
    ax2.legend(loc='upper left', fontsize=9)
    ax2.grid(True, alpha=0.3)

    topology_label = "Regular Lattice" if tag == "lattice" else "Small-World (p=0.10)"
    fig.suptitle(
        f'Mechanism Decomposition: Opinion Clustering vs. Coordination Failure\n'
        f'({topology_label}, N=400, 1000 runs per point, 300 ticks)',
        fontsize=13, fontweight='bold')

    outpath = os.path.join(FIG_DIR, f"fig_mechanism_decomposition_{tag}.png")
    fig.savefig(outpath, bbox_inches='tight', dpi=150)
    print(f"\n  Figure saved: {outpath}")
    plt.close(fig)
    return outpath


def print_summary_table(df_a, df_b, df_c, tag="lattice"):
    """Print a summary for manuscript insertion."""
    fri_b = df_b['fri'].mean()
    print(f"\n{'='*70}")
    print(f"SUMMARY TABLE — {tag}")
    print(f"{'='*70}")
    print(f"MD-B: FRI_final = {fri_b:.4f}  (opinion clustering alone)")
    print(f"      Opinion gap = {1-fri_b:.4f}")
    print(f"\n{'─'*70}")
    print(f"{'Threshold':>10} │ {'MD-A GSI':>10} │ {'MD-C FRI':>10} │ {'MD-C GSI':>10} │ "
          f"{'OpinGap':>8} │ {'CoordGap':>9} │ {'TotalGap':>9}")
    print(f"{'─'*70}")
    agg_a = df_a.groupby('avg_of_thresholds')['gsi'].mean()
    agg_c = df_c.groupby('avg_of_thresholds').agg({'gsi': 'mean', 'fri': 'mean'})
    for thr in THRESHOLD_SWEEP:
        gsi_a = agg_a.get(thr, 0)
        fri_c = agg_c.loc[thr, 'fri'] if thr in agg_c.index else 0
        gsi_c = agg_c.loc[thr, 'gsi'] if thr in agg_c.index else 0
        opin_gap  = 1.0 - fri_c
        coord_gap = fri_c - gsi_c
        total_gap = 1.0 - gsi_c
        print(f"{thr:>10} │ {gsi_a:>10.4f} │ {fri_c:>10.4f} │ {gsi_c:>10.4f} │ "
              f"{opin_gap:>8.4f} │ {coord_gap:>9.4f} │ {total_gap:>9.4f}")
    print(f"{'─'*70}")


# ══════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    total_start = time.time()

    # ── Regular Lattice (primary) ──
    df_a_lat = run_md_a(rewiring=0.00, tag="lattice")
    df_b_lat = run_md_b(rewiring=0.00, tag="lattice")
    df_c_lat = run_md_c(rewiring=0.00, tag="lattice")

    # save CSV
    df_a_lat.to_csv(os.path.join(OUT_DIR, "md_a_lattice.csv"), index=False)
    df_b_lat.to_csv(os.path.join(OUT_DIR, "md_b_lattice.csv"), index=False)
    df_c_lat.to_csv(os.path.join(OUT_DIR, "md_c_lattice.csv"), index=False)

    print_summary_table(df_a_lat, df_b_lat, df_c_lat, "lattice")
    fig1 = plot_results(df_a_lat, df_b_lat, df_c_lat, "lattice")

    # ── Small-World (robustness check) ──
    df_a_sw = run_md_a(rewiring=0.10, tag="smallworld")
    df_b_sw = run_md_b(rewiring=0.10, tag="smallworld")
    df_c_sw = run_md_c(rewiring=0.10, tag="smallworld")

    df_a_sw.to_csv(os.path.join(OUT_DIR, "md_a_smallworld.csv"), index=False)
    df_b_sw.to_csv(os.path.join(OUT_DIR, "md_b_smallworld.csv"), index=False)
    df_c_sw.to_csv(os.path.join(OUT_DIR, "md_c_smallworld.csv"), index=False)

    print_summary_table(df_a_sw, df_b_sw, df_c_sw, "smallworld")
    fig2 = plot_results(df_a_sw, df_b_sw, df_c_sw, "smallworld")

    total_elapsed = time.time() - total_start
    print(f"\n{'='*60}")
    print(f"ALL EXPERIMENTS COMPLETE in {total_elapsed:.0f}s "
          f"({total_elapsed/60:.1f} min)")
    print(f"  CSV data:  {OUT_DIR}/")
    print(f"  Figures:   {FIG_DIR}/")
    print(f"{'='*60}")
