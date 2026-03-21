#!/usr/bin/env python3
"""
Compute Table 2 values and generate Figs 7, 8, 9 for the PLOS-BCAT manuscript.
Uses sheet "表三" from sensitivity analysis Excel files.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

matplotlib.rcParams['font.size'] = 10
matplotlib.rcParams['font.family'] = 'sans-serif'

# --- Configuration ---
DATA_DIR = "/Users/gscott/Dropbox/文件/我的程式/Github/BCAT/data/sensitivity_analysis"
OUTPUT_DIR = "/Users/gscott/Dropbox/文件/我的程式/Github/PLOS-BCAT/figures"

FILES = {
    'Regular lattice': 'sensitivity_analysis_regular_lattice.xlsx',
    'Small-world': 'sensitivity_analysis_small_world.xlsx',
    'Random': 'sensitivity_analysis_random.xlsx',
    'Scale-free': 'sensitivity_analysis_scale_free.xlsx',
}

PARAMS = ['max-opinion-distance', 'avg-of-attitudes', 'std-of-attitudes',
          'avg-of-thresholds', 'std-of-thresholds']
PARAM_DISPLAY = ['bounded-\nconfidence', 'avg-of-\nattitudes', 'std-of-\nattitudes',
                 'avg-of-\nthresholds', 'std-of-\nthresholds']
PARAM_SHORT = ['BC', 'avg-att', 'std-att', 'avg-thr', 'std-thr']
TARGET = '採用人數比例的平均值'

NET_ORDER = ['All', 'Regular lattice', 'Small-world', 'Random', 'Scale-free']
NET_COLORS = {
    'Regular lattice': '#d62728',
    'Small-world': '#ff7f0e',
    'Random': '#2ca02c',
    'Scale-free': '#1f77b4',
}
METHOD_NAMES = ['Feature Importance', 'Multivariate Regression',
                'Partial Correlation', 'Standardized Regression',
                'Parameter Importance']


def load_data():
    dfs = {}
    for name, fname in FILES.items():
        path = f"{DATA_DIR}/{fname}"
        df = pd.read_excel(path, sheet_name='表三')
        dfs[name] = df
        print(f"  Loaded {name}: {len(df)} rows")
    return dfs


def compute_feature_importance(X, y):
    rf = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    rf.fit(X, y)
    return rf.feature_importances_


def compute_multivariate_regression(X, y):
    X_with_const = np.column_stack([np.ones(len(X)), X])
    coef, _, _, _ = np.linalg.lstsq(X_with_const, y, rcond=None)
    return coef[1:]


def compute_partial_correlation(X, y):
    n_params = X.shape[1]
    partial_corrs = []
    for i in range(n_params):
        others = np.delete(X, i, axis=1)
        others_c = np.column_stack([np.ones(len(others)), others])
        coef_x, _, _, _ = np.linalg.lstsq(others_c, X[:, i], rcond=None)
        resid_x = X[:, i] - others_c @ coef_x
        coef_y, _, _, _ = np.linalg.lstsq(others_c, y, rcond=None)
        resid_y = y - others_c @ coef_y
        r, _ = stats.pearsonr(resid_x, resid_y)
        partial_corrs.append(r)
    return np.array(partial_corrs)


def compute_standardized_regression(X, y):
    scaler = StandardScaler()
    X_std = scaler.fit_transform(X)
    y_std = (y - y.mean()) / y.std()
    X_with_const = np.column_stack([np.ones(len(X_std)), X_std])
    coef, _, _, _ = np.linalg.lstsq(X_with_const, y_std, rcond=None)
    return coef[1:]


def compute_parameter_importance(X, y):
    importances = []
    for i in range(X.shape[1]):
        r, _ = stats.pearsonr(X[:, i], y)
        importances.append(r)
    return np.array(importances)


def run_all_analyses(dfs):
    results = {}
    methods = [
        ('Feature Importance', compute_feature_importance),
        ('Multivariate Regression', compute_multivariate_regression),
        ('Partial Correlation', compute_partial_correlation),
        ('Standardized Regression', compute_standardized_regression),
        ('Parameter Importance', compute_parameter_importance),
    ]

    for net_name, df in dfs.items():
        df_clean = df[PARAMS + [TARGET]].dropna()
        X = df_clean[PARAMS].values.astype(float)
        y = df_clean[TARGET].values.astype(float)
        print(f"  {net_name}: {len(df_clean)} clean rows")
        results[net_name] = {}
        for method_name, method_func in methods:
            results[net_name][method_name] = method_func(X, y)

    all_df = pd.concat(dfs.values(), ignore_index=True)
    all_clean = all_df[PARAMS + [TARGET]].dropna()
    X_all = all_clean[PARAMS].values.astype(float)
    y_all = all_clean[TARGET].values.astype(float)
    print(f"  All (aggregated): {len(all_clean)} clean rows")
    results['All'] = {}
    for method_name, method_func in methods:
        results['All'][method_name] = method_func(X_all, y_all)

    return results


def print_table2(results):
    print("\n" + "=" * 90)
    print("TABLE 2: Results from statistical analysis of primary model-related parameters")
    print("=" * 90)

    for method in METHOD_NAMES:
        print(f"\n--- {method} ---")
        print(f"{'Network':<18s} {'BC':>8s} {'avg-att':>8s} {'std-att':>8s} {'avg-thr':>8s} {'std-thr':>8s}")
        print("-" * 58)
        for net in NET_ORDER:
            vals = results[net][method]
            print(f"{net:<18s} {vals[0]:>8.2f} {vals[1]:>8.2f} {vals[2]:>8.2f} {vals[3]:>8.2f} {vals[4]:>8.2f}")


def verify_manuscript_values(results):
    """Compare computed values to what's in the manuscript."""
    # Manuscript values (from lines 498-522)
    manuscript = {
        'Feature Importance': {
            'All': [0.16, 0.20, 0.04, 0.54, 0.05],
            'Regular lattice': [0.21, 0.18, 0.05, 0.55, 0.01],
            'Small-world': [0.20, 0.18, 0.04, 0.57, 0.01],
            'Random': [0.15, 0.16, 0.04, 0.53, 0.11],
            'Scale-free': [0.13, 0.25, 0.04, 0.51, 0.08],
        },
        'Multivariate Regression': {
            'All': [0.34, 0.55, 0.23, -1.31, 0.43],
            'Regular lattice': [0.42, 0.53, 0.17, -1.40, -0.11],
            'Small-world': [0.39, 0.53, 0.19, -1.40, 0.11],
            'Random': [0.31, 0.50, 0.20, -1.32, 0.71],
            'Scale-free': [0.30, 0.58, 0.27, -1.26, 0.61],
        },
        'Partial Correlation': {
            'All': [0.20, 0.27, 0.05, -0.65, 0.09],
            'Regular lattice': [0.36, 0.35, 0.05, -0.71, -0.03],
            'Small-world': [0.35, 0.36, 0.06, -0.72, 0.04],
            'Random': [0.28, 0.35, 0.06, -0.70, 0.22],
            'Scale-free': [0.22, 0.40, 0.09, -0.69, 0.19],
        },
        'Standardized Regression': {
            'All': [0.20, 0.27, 0.05, -0.65, 0.09],
            'Regular lattice': [0.26, 0.25, 0.03, -0.66, -0.02],
            'Small-world': [0.24, 0.25, 0.04, -0.67, 0.02],
            'Random': [0.20, 0.25, 0.04, -0.65, 0.15],
            'Scale-free': [0.15, 0.29, 0.06, -0.64, 0.13],
        },
    }

    print("\n" + "=" * 90)
    print("VERIFICATION: Comparing computed values to manuscript")
    print("=" * 90)

    for method in ['Feature Importance', 'Multivariate Regression',
                   'Partial Correlation', 'Standardized Regression']:
        print(f"\n--- {method} ---")
        for net in NET_ORDER:
            computed = results[net][method]
            ms_vals = manuscript[method][net]
            diffs = [abs(c - m) for c, m in zip(computed, ms_vals)]
            max_diff = max(diffs)
            status = "OK" if max_diff <= 0.03 else f"FLAGGED (max diff={max_diff:.3f})"
            if max_diff > 0.03:
                print(f"  {net:<18s} {status}")
                print(f"    Computed:   {[f'{v:.2f}' for v in computed]}")
                print(f"    Manuscript: {[f'{v:.2f}' for v in ms_vals]}")
            else:
                print(f"  {net:<18s} {status}")


# ---- Figure Generation ----

def plot_fig7(dfs):
    """Fig 7: 2x2 correlation heatmaps."""
    fig, axes = plt.subplots(2, 2, figsize=(16, 13))
    net_names = ['Regular lattice', 'Small-world', 'Random', 'Scale-free']
    panel_titles = ['(a) Regular Lattice', '(b) Small-world Network',
                    '(c) Random Network', '(d) Scale-free Network']
    display_names = ['bounded-confidence', 'avg-of-attitudes', 'std-of-attitudes',
                     'avg-of-thresholds', 'std-of-thresholds', 'good-sales']

    for idx, (net_name, title) in enumerate(zip(net_names, panel_titles)):
        ax = axes[idx // 2, idx % 2]
        df = dfs[net_name]
        cols = PARAMS + [TARGET]
        df_clean = df[cols].dropna()
        corr = df_clean.corr()

        im = ax.imshow(corr.values, cmap='RdBu_r', vmin=-1, vmax=1, aspect='auto')

        ax.set_xticks(range(len(display_names)))
        ax.set_yticks(range(len(display_names)))
        ax.set_xticklabels(display_names, rotation=45, ha='right', fontsize=8, color='green')
        ax.set_yticklabels(display_names, fontsize=8, color='blue')

        for i in range(len(display_names)):
            for j in range(len(display_names)):
                val = corr.values[i, j]
                color = 'white' if abs(val) > 0.5 else 'black'
                ax.text(j, i, f'{val:.2f}', ha='center', va='center',
                        fontsize=8, color=color, fontweight='bold')

        ax.set_title(f'{title}', fontweight='bold', fontsize=12)
        ax.text(0.5, 1.02, 'Correlation Matrix', transform=ax.transAxes,
                ha='center', va='bottom', fontsize=9)

    # Add colorbar with more padding
    fig.subplots_adjust(right=0.88)
    cbar_ax = fig.add_axes([0.90, 0.15, 0.02, 0.7])
    fig.colorbar(im, cax=cbar_ax)

    plt.tight_layout(rect=[0, 0, 0.88, 1])
    plt.savefig(f'{OUTPUT_DIR}/Fig7-combined.png', dpi=300, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    print("  Saved Fig7-combined.png")


def plot_fig8(dfs):
    """Fig 8: 5x2 sensitivity analysis plots (mean +/- std)."""
    fig, axes = plt.subplots(5, 2, figsize=(14, 24))
    net_names = ['Regular lattice', 'Small-world', 'Random', 'Scale-free']
    colors_list = ['#d62728', '#ff7f0e', '#2ca02c', '#1f77b4']
    labels_all = [
        ['(a)', '(b)'], ['(c)', '(d)'], ['(e)', '(f)'],
        ['(g)', '(h)'], ['(i)', '(j)']
    ]
    param_titles = ['bounded-confidence', 'avg-of-attitudes', 'std-of-attitudes',
                    'avg-of-thresholds', 'std-of-thresholds']

    # Combine all data
    all_df = pd.concat(dfs.values(), ignore_index=True)

    for p_idx, param in enumerate(PARAMS):
        ax_left = axes[p_idx, 0]
        ax_right = axes[p_idx, 1]

        # LEFT: by network type
        for n_idx, net_name in enumerate(net_names):
            df = dfs[net_name]
            df_clean = df[[param, TARGET]].dropna()
            grouped = df_clean.groupby(param)[TARGET]
            means = grouped.mean()
            stds = grouped.std()

            ax_left.plot(means.index, means.values, '-o', color=colors_list[n_idx],
                        label=net_name, markersize=3, linewidth=1.5)
            ax_left.fill_between(means.index, means.values - stds.values,
                                means.values + stds.values,
                                color=colors_list[n_idx], alpha=0.15)

        ax_left.set_title(f'{labels_all[p_idx][0]}', fontweight='bold', fontsize=12, loc='left')
        ax_left.set_xlabel(param_titles[p_idx])
        ax_left.set_ylabel('GSI (adoption ratio)')
        ax_left.legend(fontsize=7, title='Network Type', title_fontsize=8)

        # Add centered title above
        ax_left.text(0.5, 1.05, param_titles[p_idx], transform=ax_left.transAxes,
                    ha='center', va='bottom', fontsize=11, fontweight='bold')

        # RIGHT: aggregated
        df_agg = all_df[[param, TARGET]].dropna()
        grouped_all = df_agg.groupby(param)[TARGET]
        means_all = grouped_all.mean()
        stds_all = grouped_all.std()

        ax_right.plot(means_all.index, means_all.values, '-o', color='steelblue',
                     markersize=4, linewidth=2)
        ax_right.fill_between(means_all.index, means_all.values - stds_all.values,
                             means_all.values + stds_all.values,
                             color='steelblue', alpha=0.2)

        ax_right.set_title(f'{labels_all[p_idx][1]}', fontweight='bold', fontsize=12, loc='left')
        ax_right.set_xlabel(param_titles[p_idx])
        ax_right.set_ylabel('GSI (adoption ratio)')
        ax_right.text(0.5, 1.05, 'All', transform=ax_right.transAxes,
                     ha='center', va='bottom', fontsize=11, fontweight='bold')

    plt.tight_layout(h_pad=3.0)
    plt.savefig(f'{OUTPUT_DIR}/Fig8-combined.png', dpi=300, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    print("  Saved Fig8-combined.png")


def plot_fig9(results):
    """Fig 9: 5x2 bar charts for statistical analysis methods."""
    net_names = ['Regular lattice', 'Small-world', 'Random', 'Scale-free']
    colors_list = ['#d62728', '#ff7f0e', '#2ca02c', '#1f77b4']
    labels_all = [
        ['(a)', '(b)'], ['(c)', '(d)'], ['(e)', '(f)'],
        ['(g)', '(h)'], ['(i)', '(j)']
    ]
    method_titles = ['Feature Importance', 'Multivariate Regression',
                     'Partial Correlation', 'Standardized Regression',
                     'Parameter Importance']
    left_subtitles = [
        'Feature Importance in Predictive Model',
        'Multivariate Regression Coefficients',
        'Partial Correlation Analysis',
        'Standardized Regression Coefficients',
        'Parameter Importance (Pearson Correlation)'
    ]

    fig, axes = plt.subplots(5, 2, figsize=(16, 22))

    for m_idx, method in enumerate(method_titles):
        ax_left = axes[m_idx, 0]
        ax_right = axes[m_idx, 1]

        x = np.arange(len(PARAM_SHORT))
        width = 0.2

        # LEFT: grouped by network type
        for n_idx, net_name in enumerate(net_names):
            vals = results[net_name][method]
            bars = ax_left.bar(x + n_idx * width - 1.5 * width, vals, width,
                              label=net_name, color=colors_list[n_idx])

        ax_left.set_xticks(x)
        ax_left.set_xticklabels(PARAM_SHORT, fontsize=9)
        ax_left.set_title(f'{labels_all[m_idx][0]}', fontweight='bold', fontsize=12, loc='left')
        ax_left.text(0.5, 1.05, left_subtitles[m_idx], transform=ax_left.transAxes,
                    ha='center', va='bottom', fontsize=10, fontweight='bold')
        ax_left.legend(fontsize=7, loc='best')
        ax_left.axhline(y=0, color='gray', linewidth=0.5)
        if method != 'Feature Importance':
            ax_left.set_ylabel('Coefficient')
        else:
            ax_left.set_ylabel('Importance')

        # RIGHT: aggregated "All"
        vals_all = results['All'][method]
        bars = ax_right.bar(x, vals_all, 0.6, color='steelblue')
        ax_right.set_xticks(x)
        ax_right.set_xticklabels(PARAM_SHORT, fontsize=9)
        ax_right.set_title(f'{labels_all[m_idx][1]}', fontweight='bold', fontsize=12, loc='left')
        ax_right.text(0.5, 1.05, method_titles[m_idx], transform=ax_right.transAxes,
                     ha='center', va='bottom', fontsize=10, fontweight='bold')
        ax_right.axhline(y=0, color='gray', linewidth=0.5)

        # Value labels on bars
        for bar, val in zip(bars, vals_all):
            va = 'bottom' if val >= 0 else 'top'
            y_pos = bar.get_height() if val >= 0 else bar.get_height()
            ax_right.text(bar.get_x() + bar.get_width() / 2., y_pos,
                         f'{val:.2f}', ha='center', va=va, fontsize=8, fontweight='bold')

    plt.tight_layout(h_pad=3.0)
    plt.savefig(f'{OUTPUT_DIR}/Fig9-combined.png', dpi=300, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    print("  Saved Fig9-combined.png")


if __name__ == '__main__':
    print("Loading sensitivity analysis data...")
    dfs = load_data()

    print("\nRunning 5 statistical analyses...")
    results = run_all_analyses(dfs)

    print_table2(results)
    verify_manuscript_values(results)

    print("\nGenerating figures...")
    plot_fig7(dfs)
    plot_fig8(dfs)
    plot_fig9(results)

    print("\nDone!")
