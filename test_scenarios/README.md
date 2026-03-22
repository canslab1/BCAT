# Test Scenarios

This directory contains parameter configuration files for reproducing the simulation scenarios presented in the paper.

## Files

| File | Paper Reference | Description |
|------|----------------|-------------|
| `fig4_favorable_review_good_sales.json` | Figure 4 | Favorable review + good sales (CA network) |
| `fig5_favorable_review_poor_sales.json` | Figure 5 | Favorable review + poor sales (CA network) |
| `fig11_opinion_dynamics_only.json` | Figure 11 | Downward compatibility: opinion dynamics only |
| `fig12_adoption_threshold_only.json` | Figure 12 | Downward compatibility: adoption threshold only |
| `sensitivity_analysis_1000_runs.json` | Table 3, Figs. 7-9 | Sensitivity analysis parameter ranges |

## Usage

1. Open `BCAT.py`
2. Set parameters according to the JSON configuration file
3. Click **Setup** to initialize, then **Run** to execute

## Note on Stochastic Reproducibility

Due to the stochastic nature of agent initialization and interaction ordering, individual simulation runs will produce different results each time. The results reported in the paper are based on aggregate statistics from 1,000 independent runs per parameter configuration. To reproduce the statistical findings, use the **Experiments** button with `no-of-experiments` set to 1000.
