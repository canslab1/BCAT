#!/usr/bin/env python3
"""
Reproduce Table 2 (statistical analysis) and Figs 7, 8, 9 from
the sensitivity analysis Excel data in BCAT/data/sensitivity_analysis/.

Uses sheet "表三" which contains the full 5-parameter sweep including
bounded-confidence (max-opinion-distance).
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

# --- Configuration ---
DATA_DIR = "../data/sensitivity_analysis" if False else \
    "/Users/gscott/Dropbox/文件/我的程式/Github/BCAT/data/sensitivity_analysis"
OUTPUT_DIR = "/Users/gscott/Dropbox/文件/我的程式/Github/PLOS-BCAT/figures"

FILES = {
    'Regular lattice': 'sensitivity_analysis_regular_lattice.xlsx',
    'Small-world': 'sensitivity_analysis_small_world.xlsx',
    'Random': 'sensitivity_analysis_random.xlsx',
    'Scale-free': 'sensitivity_analysis_scale_free.xlsx',
}

PARAMS = ['max-opinion-distance', 'avg-of-attitudes', 'std-of-attitudes',
          'avg-of-thresholds', 'std-of-thresholds']
PARAM_SHORT = ['bounded-\nconfidence', 'avg-of-\nattitudes', 'std-of-\nattitudes',
               'avg-of-\nthresholds', 'std-of-\nthresholds']
TARGET = '採用人數比例的平均值'  # Average adoption ratio (GSI proxy)


def load_data():
    """Load all network type data from sheet 表三."""
    dfs = {}
    for name, fname in FILES.items():
        path = f"{DATA_DIR}/{fname}"
        df = pd.read_excel(path, sheet_name='表三')
        # Rename columns for consistency
        df = df.rename(columns={
            'max-opinion-distance': 'max-opinion-distance',
        })
        dfs[name] = df
        print(f"  Loaded {name}: {len(df)} rows, columns: {list(df.columns[:16])}")
    return dfs


def compute_feature_importance(X, y):
    """Random Forest feature importance."""
    rf = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    rf.fit(X, y)
    return rf.feature_importances_


def compute_multivariate_regression(X, y):
    """OLS multivariate regression coefficients."""
    from numpy.linalg import lstsq
    X_with_const = np.column_stack([np.ones(len(X)), X])
    coef, _, _, _ = lstsq(X_with_const, y, rcond=None)
    return coef[1:]  # skip intercept


def compute_partial_correlation(X, y):
    """Partial correlation of each parameter with y, controlling for others."""
    n_params = X.shape[1]
    partial_corrs = []
    for i in range(n_params):
        # Regress x_i on all other x's
        others = np.delete(X, i, axis=1)
        others_with_const = np.column_stack([np.ones(len(others)), others])
        coef_x, _, _, _ = np.linalg.lstsq(others_with_const, X[:, i], rcond=None)
        resid_x = X[:, i] - others_with_const @ coef_x

        # Regress y on all other x's
        coef_y, _, _, _ = np.linalg.lstsq(others_with_const, y, rcond=None)
        resid_y = y - others_with_const @ coef_y

        # Correlation of residuals
        r, _ = stats.pearsonr(resid_x, resid_y)
        partial_corrs.append(r)
    return np.array(partial_corrs)


def compute_standardized_regression(X, y):
    """Standardized regression coefficients (beta weights)."""
    scaler = StandardScaler()
    X_std = scaler.fit_transform(X)
    y_std = (y - y.mean()) / y.std()
    from numpy.linalg import lstsq
    X_with_const = np.column_stack([np.ones(len(X_std)), X_std])
    coef, _, _, _ = lstsq(X_with_const, y_std, rcond=None)
    return coef[1:]


def compute_parameter_importance(X, y):
    """Parameter importance based on Pearson correlation."""
    importances = []
    for i in range(X.shape[1]):
        r, _ = stats.pearsonr(X[:, i], y)
        importances.append(r)
    return np.array(importances)


def run_all_analyses(dfs):
    """Run all 5 analyses for each network type and aggregated."""
    results = {}
    methods = [
        ('Feature Importance', compute_feature_importance),
        ('Multivariate Regression', compute_multivariate_regression),
        ('Partial Correlation', compute_partial_correlation),
        ('Standardized Regression', compute_standardized_regression),
        ('Parameter Importance', compute_parameter_importance),
    ]

    # Per network type
    for net_name, df in dfs.items():
        # Drop rows with NaN in target or parameters
        df_clean = df[PARAMS + [TARGET]].dropna()
        X = df_clean[PARAMS].values.astype(float)
        y = df_clean[TARGET].values.astype(float)
        print(f"  {net_name}: {len(df_clean)} clean rows (from {len(df)})")
        results[net_name] = {}
        for method_name, method_func in methods:
            results[net_name][method_name] = method_func(X, y)

    # Aggregated "All"
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
    """Print Table 2 in a readable format."""
    method_names = ['Feature Importance', 'Multivariate Regression',
                    'Partial Correlation', 'Standardized Regression',
                    'Parameter Importance']
    net_order = ['All', 'Regular lattice', 'Small-world', 'Random', 'Scale-free']

    print("\n" + "=" * 90)
    print("TABLE 2: Results from statistical analysis of primary model-related parameters")
    print("=" * 90)

    for method in method_names:
        print(f"\n--- {method} ---")
        print(f"{'Network':<18s} {'BC':>8s} {'avg-att':>8s} {'std-att':>8s} {'avg-thr':>8s} {'std-thr':>8s}")
        print("-" * 58)
        for net in net_order:
            vals = results[net][method]
            print(f"{net:<18s} {vals[0]:>8.2f} {vals[1]:>8.2f} {vals[2]:>8.2f} {vals[3]:>8.2f} {vals[4]:>8.2f}")


def plot_fig7_heatmaps(dfs):
    """Fig 7: Correlation coefficient heatmaps."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))
    net_names = ['Regular lattice', 'Small-world', 'Random', 'Scale-free']
    labels = ['(a)', '(b)', '(c)', '(d)']

    for idx, (net_name, label) in enumerate(zip(net_names, labels)):
        ax = axes[idx // 2, idx % 2]
        df = dfs[net_name]
        cols = PARAMS + [TARGET]
        corr = df[cols].corr()

        display_names = ['BC', 'avg-att', 'std-att', 'avg-thr', 'std-thr', 'GSI']
        im = ax.imshow(corr.values, cmap='RdBu_r', vmin=-1, vmax=1, aspect='auto')

        ax.set_xticks(range(len(display_names)))
        ax.set_yticks(range(len(display_names)))
        ax.set_xticklabels(display_names, rotation=45, ha='right', fontsize=9)
        ax.set_yticklabels(display_names, fontsize=9)

        # Add correlation values
        for i in range(len(display_names)):
            for j in range(len(display_names)):
                val = corr.values[i, j]
                color = 'white' if abs(val) > 0.5 else 'black'
                ax.text(j, i, f'{val:.2f}', ha='center', va='center',
                        fontsize=8, color=color)

        ax.set_title(f'{label} {net_name}', fontweight='bold')

    fig.colorbar(im, ax=axes, shrink=0.6, label='Correlation Coefficient')
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/Fig7-reproduced.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("  Saved Fig7-reproduced.png")


def plot_fig9_barcharts(results):
    """Fig 9: Bar charts for all 5 analysis methods."""
    method_names = ['Feature Importance', 'Multivariate Regression',
                    'Partial Correlation', 'Standardized Regression',
                    'Parameter Importance']
    net_names = ['Regular lattice', 'Small-world', 'Random', 'Scale-free']
    colors = ['#d62728', '#ff7f0e', '#2ca02c', '#1f77b4']  # red, yellow, green, blue
    param_labels = ['BC', 'avg-att', 'std-att', 'avg-thr', 'std-thr']

    fig, axes = plt.subplots(5, 2, figsize=(16, 20))
    labels_lr = [
        ['(a)', '(b)'], ['(c)', '(d)'], ['(e)', '(f)'],
        ['(g)', '(h)'], ['(i)', '(j)']
    ]

    for m_idx, method in enumerate(method_names):
        # Left: by network type
        ax_left = axes[m_idx, 0]
        x = np.arange(len(param_labels))
        width = 0.2
        for n_idx, net_name in enumerate(net_names):
            vals = results[net_name][method]
            ax_left.bar(x + n_idx * width - 1.5 * width, vals, width,
                       label=net_name, color=colors[n_idx])
        ax_left.set_xticks(x)
        ax_left.set_xticklabels(param_labels)
        ax_left.set_title(f'{labels_lr[m_idx][0]} {method} (by network)', fontweight='bold')
        ax_left.legend(fontsize=7)
        ax_left.axhline(y=0, color='gray', linewidth=0.5)

        # Right: aggregated (All)
        ax_right = axes[m_idx, 1]
        vals_all = results['All'][method]
        bars = ax_right.bar(x, vals_all, 0.6, color='steelblue')
        ax_right.set_xticks(x)
        ax_right.set_xticklabels(param_labels)
        ax_right.set_title(f'{labels_lr[m_idx][1]} {method} (aggregated)', fontweight='bold')
        ax_right.axhline(y=0, color='gray', linewidth=0.5)

        # Add value labels
        for bar, val in zip(bars, vals_all):
            ax_right.text(bar.get_x() + bar.get_width() / 2., bar.get_height(),
                         f'{val:.2f}', ha='center', va='bottom', fontsize=8)

    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/Fig9-reproduced.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("  Saved Fig9-reproduced.png")


if __name__ == '__main__':
    print("Loading sensitivity analysis data...")
    dfs = load_data()

    print("\nRunning 5 statistical analyses...")
    results = run_all_analyses(dfs)

    print_table2(results)

    print("\nGenerating figures...")
    plot_fig7_heatmaps(dfs)
    plot_fig9_barcharts(results)

    print("\nDone!")
