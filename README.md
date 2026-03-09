# BCAT: Bounded Confidence and Adoption Threshold Model

A mixed opinion dynamics and innovation diffusion simulation model for exploring the "best game no one played" phenomenon.

## Overview

The BCAT (Bounded Confidence + Adoption Threshold) model integrates a bounded confidence-based opinion dynamics model with an adoption threshold innovation diffusion model. It simulates opinion exchanges and product acceptance behaviors across four types of theoretical social networks:

- **Regular Lattice (CA)**: Toroidal 2D cellular automata with Moore neighborhood (rewiring probability = 0)
- **Small-World Network (SWN)**: Watts-Strogatz model (0 < rewiring probability < 1)
- **Random Network (RN)**: Fully rewired network (rewiring probability = 1)
- **Scale-Free Network (SFN)**: Barabasi-Albert preferential attachment model

Each simulation consists of 400 agents connected by approximately 1,600 edges, with an average of 8 neighbors per agent.

## Features

- **Mixed model** — Integrates bounded confidence opinion dynamics with adoption threshold innovation diffusion in a single simulation.
- **Four network topologies** — Regular Lattice (CA), Small-World (SWN), Random (RN), and Scale-Free (SFN) networks.
- **Interactive GUI** — Tkinter-based interface with real-time visualization of attitude trajectories, social networks, adoption dynamics, and distributions.
- **Batch experiments** — Run multiple repetitions with automatic result aggregation.
- **Reproducible scenarios** — Pre-configured parameter files for reproducing all key paper figures.
- **Dual implementation** — Both Python 3 (with GUI) and NetLogo 4.0.5 versions producing statistically equivalent results.

## Installation

### Python Version

- Python 3.10 or later (tested on Python 3.12 and 3.13)

### Dependencies

Install all required packages:

```bash
pip install -r requirements.txt
```

Or install individually:

```bash
pip install numpy>=1.24.0 networkx>=3.0 matplotlib>=3.7.0
```

### Standard Library Modules (no installation needed)

`tkinter`, `random`, `os`, `time`, `math`, `threading`, `pickle`, `warnings`

### NetLogo Version (for `.nlogo` file)

- NetLogo 4.0.5 or later (available at https://ccl.northwestern.edu/netlogo/)

## Usage

### Python Version

```bash
python3 BCAT.py
```

This launches the GUI application with:
- **Left panel**: Parameter sliders and control buttons
- **Center/Right panels**: Real-time visualization plots
  - Attitude Trajectory (opinion evolution over time)
  - Social Network (node colors reflect attitudes and adoption status)
  - New Adopter Dynamics, Attitude Distribution, Threshold Distribution, Degree Distribution
  - Adoption Dynamics (adopter vs. non-adopter counts)
- **Monitors**: PA, NA, Avg PA, Std PA, Avg NA, Std NA, Links, Critical Point, Adopter count

### Controls

| Button | Function |
|--------|----------|
| **Setup** | Initialize the network and agent population |
| **Run** | Execute a complete simulation run (max-time steps) |
| **Run Once** | Execute a single time step |
| **Experiments** | Run batch experiments (no-of-experiments repetitions) |
| **Save** | Save current model state |
| **Load** | Load a previously saved model state |

### NetLogo Version

1. Open `English - best game no one played.nlogo` in NetLogo 4.0.5+
2. Adjust parameters using the interface sliders
3. Click "Setup" to initialize, then "Run once" to execute

## Model Parameters

| Parameter | Range | Default | Description |
|-----------|-------|---------|-------------|
| `no-of-pioneers` | 0 -- 100 | 5 | Number of initial adopter agents |
| `clustered-pioneers?` | ON/OFF | ON | Whether pioneers are spatially clustered |
| `bounded-confidence` | 0 -- 90 | 50 | Attitude distance threshold for opinion exchange |
| `convergence-rate` | 0.1 -- 1.0 | 0.1 | Rate of attitude adjustment per exchange |
| `avg-of-attitudes` | 10 -- 100 | 50 | Mean of initial attitude distribution |
| `std-of-attitudes` | 0 -- 30 | 10 | Std. dev. of initial attitude distribution |
| `avg-of-thresholds` | 10 -- 100 | 40 | Mean of adoption threshold distribution |
| `std-of-thresholds` | 0 -- 30 | 10 | Std. dev. of adoption threshold distribution |
| `network-type` | SFN / SWN | SWN/RN/CA | Social network topology |
| `rewiring-probability` | 0.00 -- 1.00 | 0.00 | Network rewiring probability (SWN only) |
| `max-time` | 50 -- 1000 | 300 | Maximum simulation time steps |
| `no-of-experiments` | 10 -- 1000 | 20 | Number of batch experiment repetitions |

## Reproducing Paper Results

Parameter configuration files for reproducing the simulation scenarios presented in the paper are provided in the `test_scenarios/` directory.

### Scenario 1: Favorable Review + Good Sales (Fig. 4)

```
python3 BCAT.py
```
Then set parameters: no-of-pioneers=5, clustered-pioneers=ON, bounded-confidence=50, convergence-rate=0.1, avg-of-attitudes=50, std-of-attitudes=10, avg-of-thresholds=20, std-of-thresholds=5, network-type=SWN/RN/CA, rewiring-probability=0.00, max-time=300. Click Setup, then Run.

### Scenario 2: Downward Compatibility -- Opinion Dynamics Only (Fig. 10)

Set: avg-of-thresholds=100, std-of-thresholds=0, no-of-pioneers=0, bounded-confidence=10, convergence-rate=0.4, avg-of-attitudes=50, std-of-attitudes=20, network-type=SWN/RN/CA, rewiring-probability=0.00, max-time=300.

### Scenario 3: Downward Compatibility -- Adoption Threshold Only (Fig. 11)

Set: avg-of-attitudes=100, std-of-attitudes=0, bounded-confidence=0, avg-of-thresholds=20, std-of-thresholds=10, no-of-pioneers=3, network-type=SWN/RN/CA, rewiring-probability=0.00, max-time=50.

## Model Algorithm

The BCAT model operates in the following phases per time step:

1. **Agent Selection**: All agents are processed in random order each tick.
2. **Neighbor Selection**: Each agent randomly selects one neighboring agent.
3. **Opinion Exchange**: If the attitude difference is below the bounded confidence threshold, attitudes are adjusted according to four scenarios based on adoption status (see Algorithm 3 in the paper).
4. **Adoption Decision**: A not-yet-adopted agent with a positive attitude (att > 50) adopts if the proportion of adopted neighbors exceeds its adoption threshold.

## Implementation Notes

- The Python version faithfully replicates the NetLogo 4.0.5 implementation, including the sequential execution semantics of NetLogo's `ask-concurrent` (which processes agents in random order with immediate effect).
- `int(v + 0.5)` is used as an equivalent to NetLogo's `round()` for positive values.
- NumPy arrays replace NetLogo's `turtles-own` for performance optimization.
- NetworkX graphs replace NetLogo's native turtle/link network structure.
- Both versions produce statistically equivalent results under identical random seeds and parameter settings.

## Project Structure

```
BCAT/
├── BCAT.py                                # Python 3 implementation with GUI (Tkinter + matplotlib)
├── English - best game no one played.nlogo # NetLogo 4.0.5 implementation
├── requirements.txt                       # Python dependencies
├── CITATION.cff                           # Citation metadata
├── test_scenarios/                        # Parameter configs for paper reproduction
│   ├── fig4_favorable_review_good_sales.json
│   ├── fig5_favorable_review_poor_sales.json
│   ├── fig10_opinion_dynamics_only.json
│   ├── fig11_adoption_threshold_only.json
│   └── sensitivity_analysis_1000_runs.json
└── LICENSE                                # MIT License
```

## Authors

- **Chung-Yuan Huang** (黃崇源) — Department of Computer Science and Information Engineering, Chang Gung University, Taiwan (gscott@mail.cgu.edu.tw)
- **Sheng-Wen Wang** (Corresponding author) — Department of Finance and Information, National Kaohsiung University of Science and Technology, Taiwan (swwang@nkust.edu.tw)

## Citation

If you use this software in your research, please cite:

> Huang, C.-Y., & Wang, S.-W. (2025). Exploring the "Best Game No One Played" Phenomenon Using A Mixed Opinion Dynamics and Innovation Diffusion Model. *PLOS ONE*. (forthcoming)

See `CITATION.cff` for machine-readable citation metadata.

## References

1. Wang, S.-W., Huang, C.-Y., & Sun, C.-T. (2022). Multiagent Diffusion and Opinion Dynamics Model Interaction Effects on Controversial Products. *IEEE Access*, 10, 115252–115272. https://doi.org/10.1109/ACCESS.2022.3218719

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
