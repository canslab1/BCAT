# Changelog

## v1.1.0 (2025-03-10)

### Improved
- **Attitude Trajectory rendering performance**: compressed ~9,000 PathCollection objects into 15 fixed ones (one per color), using `set_offsets()` for incremental updates. Reduces `draw_idle()` artist traversal from O(T×K) to O(1), eliminating progressive slowdown at later time steps.
- **Hi-res export performance**: `save_attitude_trajectory_hires()` now batches scatter calls by color (max 15 calls instead of ~9,000).

### Removed
- 9 dead code methods (236 lines): `_become_susceptible`, `save_plots`, and 7 inlined methods (`_communicate_and_make_decision`, `_communicate`, `_change_opinion_1/2/3`, `_make_decision`, `_become_action`) that were fully inlined into `_step_all_agents()`.

## v1.0.0 (2025)

Initial public release.

### Added
- Python 3 implementation with Tkinter GUI
- NetLogo 4.0.5 reference implementation
- Four network topologies: regular lattice, small-world, random, scale-free
- Bounded confidence opinion dynamics mechanism
- Adoption threshold innovation diffusion mechanism
- Batch experiment mode with 1,000+ repetitions support
- Pre-configured test scenarios for reproducing paper figures
- Rigorous time/space complexity analysis documentation
- CITATION.cff for academic referencing
