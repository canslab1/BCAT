#!/usr/bin/env python3
"""
Finite-Size Scaling Experiments for BCAT Model
===============================================
Tests whether the "best game no one played" phenomenon (high FRI, low GSI)
is robust at larger system sizes: N=900 (30x30), N=1600 (40x40), N=2500 (50x50).

This script imports the OpinionAdoptionModel from BCAT.py and patches the
network construction to support arbitrary grid sizes.
"""

import sys
import os
import csv
import time as time_module
import math
import numpy as np
import networkx as nx
import random


def _nl_round(x):
    """NetLogo 4.0.5 compatible round-half-up."""
    return int(math.floor(x + 0.5))


class OpinionAdoptionModel:
    """
    Minimal standalone BCAT model core extracted from BCAT.py.
    Supports arbitrary grid sizes for finite-size scaling experiments.
    """
    _ATT = 0
    _THETA = 1
    _ACT = 2
    _TIME = 3
    _N_FIELDS = 4

    def __init__(self, grid_width=20, grid_height=20):
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.G = None
        self.critical_time = 0
        self.critical_time_list = []
        self.adopter_list = []
        self.no_of_pioneers = 5
        self.clustered_pioneers = True
        self.bounded_confidence = 50
        self.convergence_rate = 0.1
        self.avg_of_attitudes = 50
        self.std_of_attitudes = 10
        self.avg_of_thresholds = 40
        self.std_of_thresholds = 10
        self.network_type = "SWN/RN/CA"
        self.rewiring_probability = 0.1
        self.max_time = 100
        self.no_of_experiments = 20
        self.current_time = 0
        self._states = np.empty((0, self._N_FIELDS), dtype=np.float64)
        self._neighbors_cache = {}
        self._degree_list = []
        self._total_degree = 0
        self._step_callback = None
        self._attitude_snapshots = {}

    def setup(self):
        self._clear()
        self.critical_time = 0
        self.setup_social_network()
        self._build_neighbors_cache()
        self.setup_agent_population()

    def _clear(self):
        self.current_time = 0
        self.G = None
        self._states = np.empty((0, self._N_FIELDS), dtype=np.float64)
        self._neighbors_cache = {}
        self._degree_list = []
        self._total_degree = 0
        self._attitude_snapshots = {}

    def _build_neighbors_cache(self):
        self._neighbors_cache = {
            n: list(self.G.neighbors(n)) for n in self.G.nodes()
        }

    def setup_social_network(self):
        if self.network_type == "SFN":
            self.setup_scale_free_network()
        else:
            self.setup_small_world_network()

    def setup_scale_free_network(self):
        total_nodes = self.grid_width * self.grid_height
        self.G = nx.Graph()
        self._degree_list = [0] * total_nodes
        self._total_degree = 0

        self.G.add_node(0)
        self.G.add_node(1)
        self.G.add_edge(1, 0)
        self._degree_list[0] = 1
        self._degree_list[1] = 1
        self._total_degree = 2

        for i in range(2, total_nodes):
            partner = self._find_partner()
            self.G.add_node(i)
            self.G.add_edge(i, partner)
            self._degree_list[i] += 1
            self._degree_list[partner] += 1
            self._total_degree += 2

        self._add_link(0)

        node_order = list(range(total_nodes))
        random.shuffle(node_order)
        for node_id in node_order:
            for _ in range(3):
                self._add_link(node_id)

        self._set_pos_xy_of_nodes()

    def _find_partner(self):
        degrees = self._degree_list
        total_degree = self._total_degree
        n_nodes = self.G.number_of_nodes()
        if total_degree == 0:
            return random.randrange(n_nodes)
        threshold = random.randint(0, total_degree - 1)
        for node in range(n_nodes):
            nc = degrees[node]
            if nc > threshold:
                return node
            threshold -= nc
        return n_nodes - 1

    def _add_link(self, source_node):
        max_attempts = self.G.number_of_nodes()
        passed = False
        attempts = 0
        while not passed and attempts < max_attempts:
            attempts += 1
            partner = self._find_partner()
            while partner == source_node:
                partner = self._find_partner()
            if not self.G.has_edge(source_node, partner):
                self.G.add_edge(source_node, partner)
                if self._degree_list:
                    self._degree_list[source_node] += 1
                    self._degree_list[partner] += 1
                    self._total_degree += 2
                passed = True

    def _set_pos_xy_of_nodes(self):
        world_width = self.grid_width
        pos = {}
        nowx = 0
        nowy = 0
        for node in sorted(self.G.nodes()):
            pos[node] = (nowx, nowy)
            nowx += 1
            nowy += nowx // world_width
            nowx = nowx % world_width
        nx.set_node_attributes(self.G, pos, 'pos')

    def setup_small_world_network(self):
        width, height = self.grid_width, self.grid_height
        total_nodes = width * height
        self.G = nx.Graph()

        for i in range(total_nodes):
            self.G.add_node(i)

        for y in range(height):
            for x in range(width):
                node_id = y * width + x
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        if dx == 0 and dy == 0:
                            continue
                        nx_ = (x + dx) % width
                        ny_ = (y + dy) % height
                        neighbor_id = ny_ * width + nx_
                        if not self.G.has_edge(node_id, neighbor_id):
                            self.G.add_edge(node_id, neighbor_id)

        edges_to_process = list(self.G.edges())
        for u, v in edges_to_process:
            if random.random() < self.rewiring_probability:
                node1 = u
                if self.G.degree(node1) < (total_nodes - 1):
                    non_neighbors = [
                        n for n in self.G.nodes()
                        if n != node1 and not self.G.has_edge(node1, n)
                    ]
                    if non_neighbors:
                        new_target = random.choice(non_neighbors)
                        self.G.add_edge(node1, new_target)
                        if self.G.has_edge(u, v):
                            self.G.remove_edge(u, v)

        pos = {}
        for y in range(height):
            for x in range(width):
                node_id = y * width + x
                pos[node_id] = (x, y)
        nx.set_node_attributes(self.G, pos, 'pos')

    def setup_agent_population(self):
        n_nodes = self.G.number_of_nodes()
        att_arr = np.clip(
            np.random.normal(self.avg_of_attitudes, self.std_of_attitudes, n_nodes),
            1.0, 100.0
        )
        theta_arr = np.clip(
            np.random.normal(self.avg_of_thresholds, self.std_of_thresholds, n_nodes),
            1.0, 100.0
        )
        self._states = np.empty((n_nodes, self._N_FIELDS), dtype=np.float64)
        self._states[:, self._ATT] = att_arr
        self._states[:, self._THETA] = theta_arr
        self._states[:, self._ACT] = 0.0
        self._states[:, self._TIME] = -1.0

        pioneers = self._chosen_leaders()
        for node in pioneers:
            self._states[node, self._ATT] = 100.0
            self._states[node, self._THETA] = 0.0
            self._states[node, self._ACT] = 1.0
            self._states[node, self._TIME] = 0.0

    def _chosen_leaders(self):
        n = min(self.no_of_pioneers, len(self.G.nodes()))
        if n == 0:
            return []
        if self.clustered_pioneers:
            pos = nx.get_node_attributes(self.G, 'pos')
            nodes_sorted = sorted(
                self.G.nodes(),
                key=lambda nd: pos[nd][0] + pos[nd][1],
                reverse=True
            )
            return nodes_sorted[:n]
        else:
            return random.sample(list(self.G.nodes()), n)

    def go(self, exp_id=0):
        self.setup()
        results = []
        states = self._states
        ATT = self._ATT
        ACT = self._ACT
        max_time = self.max_time
        n_total = states.shape[0]

        while self.current_time < max_time:
            self._step_all_agents()
            act_col = states[:, ACT]
            adopters = int(np.sum(act_col))
            non_adopters = n_total - adopters
            att_col = states[:, ATT]
            mean_att = float(np.mean(att_col))
            std_att = float(np.std(att_col, ddof=1)) if n_total > 1 else 0.0
            results.append((adopters, non_adopters, mean_att, std_att))

            if exp_id > 0 and self.current_time < len(self.adopter_list):
                self.adopter_list[self.current_time] += (
                    adopters * (1.0 / self.no_of_experiments)
                )
            self.current_time += 1
            _ = self.critical_point

        if exp_id > 0:
            self.critical_time_list.append(self.critical_time)
        return results

    def _step_all_agents(self):
        n_nodes = self._states.shape[0]
        nodes = np.arange(n_nodes)
        np.random.shuffle(nodes)

        states = self._states
        neighbors_cache = self._neighbors_cache
        ATT = self._ATT
        ACT = self._ACT
        THETA = self._THETA
        TIME = self._TIME
        bc = self.bounded_confidence
        cr = self.convergence_rate
        current_time = self.current_time

        rand_vals = np.random.random(n_nodes)
        _int = int
        neg_bc = -bc

        for node_idx in range(n_nodes):
            node = nodes[node_idx]
            neighbors = neighbors_cache[node]
            n_nb = len(neighbors)
            if n_nb == 0:
                continue

            obj = neighbors[_int(rand_vals[node_idx] * n_nb)]

            A1 = states[obj, ACT]
            A2 = states[node, ACT]
            B = states[obj, ATT]
            C = states[node, ATT]

            diff = C - B
            if neg_bc < diff < bc:
                obj_adopted = (A1 != 0.0)
                self_adopted = (A2 != 0.0)

                if obj_adopted and not self_adopted:
                    if B > C:
                        states[node, ATT] = _int(C + cr * (B - C) + 0.5)
                    else:
                        states[node, ATT] = _int(C + cr * (B - C) + 0.5)
                        states[obj, ATT] = _int(B + cr * (C - B) + 0.5)
                elif not obj_adopted and self_adopted:
                    if B > C:
                        states[node, ATT] = _int(C + cr * (B - C) + 0.5)
                        states[obj, ATT] = _int(B + cr * (C - B) + 0.5)
                    else:
                        states[obj, ATT] = _int(B + cr * (C - B) + 0.5)
                elif obj_adopted and self_adopted:
                    if B > C:
                        states[node, ATT] = _int(C + cr * (B - C) + 0.5)
                    else:
                        states[obj, ATT] = _int(B + cr * (C - B) + 0.5)
                elif not obj_adopted and not self_adopted:
                    states[node, ATT] = _int(C + cr * (B - C) + 0.5)
                    states[obj, ATT] = _int(B + cr * (C - B) + 0.5)

            if states[node, ACT] == 0.0:
                if states[node, ATT] > 50:
                    if n_nb > 0:
                        adopter_count = 0
                        for nb in neighbors:
                            if states[nb, ACT] != 0.0:
                                adopter_count += 1
                        adopter_ratio = adopter_count / n_nb
                        if adopter_ratio >= states[node, THETA] / 100.0:
                            states[node, ACT] = 1.0
                            states[node, TIME] = current_time

    @property
    def critical_point(self):
        if self.critical_time > 0:
            return self.critical_time
        n_total = self._states.shape[0]
        if n_total == 0:
            return 0
        adopters = int(np.sum(self._states[:, self._ACT]))
        non_adopters = n_total - adopters
        if adopters > non_adopters:
            self.critical_time = self.current_time
        else:
            self.critical_time = 0
        return self.critical_time


def create_model_with_grid_size(grid_size):
    """
    Create a model instance for a specific grid size.
    grid_size: int, e.g. 30 for 30x30 = 900 agents
    """
    return OpinionAdoptionModel(grid_width=grid_size, grid_height=grid_size)


def compute_fri_gsi(model):
    """
    Compute FRI and GSI from model state.
    FRI = count(att > 50) / N  (Favorable Review Index)
    GSI = count(act = true) / N  (Good Sales Index)
    """
    states = model._states
    n_total = states.shape[0]
    if n_total == 0:
        return 0.0, 0.0
    fri = float(np.sum(states[:, model._ATT] > 50)) / n_total
    gsi = float(np.sum(states[:, model._ACT] != 0.0)) / n_total
    return fri, gsi


def run_single_experiment(grid_size, params, max_time=300):
    """
    Run a single experiment with the given grid size and parameters.
    Returns (FRI, GSI, critical_time).
    """
    model = create_model_with_grid_size(grid_size)

    # Set parameters
    model.avg_of_attitudes = params['avg_att']
    model.std_of_attitudes = params['std_att']
    model.avg_of_thresholds = params['avg_thr']
    model.std_of_thresholds = params['std_thr']
    model.bounded_confidence = params['bc']
    model.convergence_rate = params['cr']
    model.no_of_pioneers = params['pioneers']
    model.clustered_pioneers = params['clustered']
    model.network_type = params['network_type']
    model.rewiring_probability = params['rewiring']
    model.max_time = max_time

    # Run
    model.go(exp_id=0)

    fri, gsi = compute_fri_gsi(model)
    return fri, gsi, model.critical_time


def main():
    output_dir = '/Users/gscott/Dropbox/文件/我的程式/Github/PLOS-BCAT/data/finite_size_scaling'
    os.makedirs(output_dir, exist_ok=True)

    grid_sizes = [20, 30, 40, 50]  # Include 20x20 as baseline
    n_runs = 30
    max_time = 300

    # Define scenarios
    # 1. Three specific scenarios
    scenarios = {
        'good_sales': {
            'avg_att': 50, 'std_att': 10,
            'avg_thr': 20, 'std_thr': 5,
            'bc': 50, 'cr': 0.1,
            'pioneers': 5, 'clustered': True,
            'network_type': 'SWN/RN/CA', 'rewiring': 0.0
        },
        'best_game_no_one_played': {
            'avg_att': 50, 'std_att': 10,
            'avg_thr': 40, 'std_thr': 10,
            'bc': 50, 'cr': 0.1,
            'pioneers': 5, 'clustered': True,
            'network_type': 'SWN/RN/CA', 'rewiring': 0.0
        },
        'high_threshold': {
            'avg_att': 50, 'std_att': 10,
            'avg_thr': 60, 'std_thr': 10,
            'bc': 50, 'cr': 0.1,
            'pioneers': 5, 'clustered': True,
            'network_type': 'SWN/RN/CA', 'rewiring': 0.0
        },
    }

    # 2. Threshold sweep
    threshold_sweep_values = list(range(10, 71, 10))  # 10, 20, 30, 40, 50, 60, 70

    # Collect all results
    all_results = []

    total_configs = len(scenarios) * len(grid_sizes) + len(threshold_sweep_values) * len(grid_sizes)
    config_count = 0
    start_time = time_module.time()

    # --- Run named scenarios ---
    for scenario_name, params in scenarios.items():
        for gs in grid_sizes:
            config_count += 1
            N = gs * gs
            print(f"\n[{config_count}/{total_configs}] Scenario: {scenario_name}, "
                  f"Grid: {gs}x{gs} (N={N}), {n_runs} runs")

            for run in range(1, n_runs + 1):
                fri, gsi, ct = run_single_experiment(gs, params, max_time)
                all_results.append({
                    'scenario': scenario_name,
                    'grid_size': gs,
                    'N': N,
                    'avg_thr': params['avg_thr'],
                    'run': run,
                    'FRI': fri,
                    'GSI': gsi,
                    'critical_time': ct,
                })
                if run % 10 == 0:
                    elapsed = time_module.time() - start_time
                    print(f"  Run {run}/{n_runs} done. "
                          f"FRI={fri:.4f}, GSI={gsi:.4f}  "
                          f"[{elapsed:.0f}s elapsed]")

    # --- Run threshold sweep ---
    for avg_thr in threshold_sweep_values:
        for gs in grid_sizes:
            config_count += 1
            N = gs * gs
            sweep_params = {
                'avg_att': 50, 'std_att': 10,
                'avg_thr': avg_thr, 'std_thr': 10,
                'bc': 50, 'cr': 0.1,
                'pioneers': 5, 'clustered': True,
                'network_type': 'SWN/RN/CA', 'rewiring': 0.0
            }

            # Skip if already covered by named scenarios
            already_done = False
            for sname, sparams in scenarios.items():
                if sparams['avg_thr'] == avg_thr and sparams['std_thr'] == 10:
                    already_done = True
                    break
            if already_done:
                print(f"\n[{config_count}/{total_configs}] Sweep avg_thr={avg_thr}, "
                      f"Grid: {gs}x{gs} (N={N}) -- already covered by named scenario, skipping")
                continue

            print(f"\n[{config_count}/{total_configs}] Sweep avg_thr={avg_thr}, "
                  f"Grid: {gs}x{gs} (N={N}), {n_runs} runs")

            for run in range(1, n_runs + 1):
                fri, gsi, ct = run_single_experiment(gs, sweep_params, max_time)
                all_results.append({
                    'scenario': f'sweep_thr{avg_thr}',
                    'grid_size': gs,
                    'N': N,
                    'avg_thr': avg_thr,
                    'run': run,
                    'FRI': fri,
                    'GSI': gsi,
                    'critical_time': ct,
                })
                if run % 10 == 0:
                    elapsed = time_module.time() - start_time
                    print(f"  Run {run}/{n_runs} done. "
                          f"FRI={fri:.4f}, GSI={gsi:.4f}  "
                          f"[{elapsed:.0f}s elapsed]")

    # --- Save raw results ---
    csv_path = os.path.join(output_dir, 'finite_size_scaling_results.csv')
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'scenario', 'grid_size', 'N', 'avg_thr', 'run',
            'FRI', 'GSI', 'critical_time'
        ])
        writer.writeheader()
        writer.writerows(all_results)
    print(f"\nRaw results saved to: {csv_path}")

    # --- Analysis ---
    print("\n" + "=" * 80)
    print("FINITE-SIZE SCALING ANALYSIS")
    print("=" * 80)

    # Group results by (scenario, grid_size)
    from collections import defaultdict
    grouped = defaultdict(list)
    for r in all_results:
        key = (r['scenario'], r['grid_size'], r['avg_thr'])
        grouped[key].append(r)

    # Also group by (avg_thr, grid_size) for the sweep analysis
    sweep_grouped = defaultdict(list)
    for r in all_results:
        key = (r['avg_thr'], r['grid_size'])
        sweep_grouped[key].append(r)

    # Print scenario comparison
    print("\n--- Named Scenario Results (Mean +/- Std over 30 runs) ---")
    print(f"{'Scenario':<30s} {'Grid':>6s} {'N':>6s} "
          f"{'FRI mean':>9s} {'FRI std':>8s} {'GSI mean':>9s} {'GSI std':>8s} "
          f"{'FRI-GSI':>8s}")
    print("-" * 95)

    for scenario_name in scenarios:
        for gs in grid_sizes:
            key = (scenario_name, gs, scenarios[scenario_name]['avg_thr'])
            runs = grouped[key]
            if not runs:
                continue
            fris = [r['FRI'] for r in runs]
            gsis = [r['GSI'] for r in runs]
            fri_mean = np.mean(fris)
            fri_std = np.std(fris)
            gsi_mean = np.mean(gsis)
            gsi_std = np.std(gsis)
            gap = fri_mean - gsi_mean
            print(f"{scenario_name:<30s} {gs:>4d}x{gs:<1d} {gs*gs:>6d} "
                  f"{fri_mean:>9.4f} {fri_std:>8.4f} {gsi_mean:>9.4f} {gsi_std:>8.4f} "
                  f"{gap:>8.4f}")
        print()

    # Print threshold sweep summary
    print("\n--- Threshold Sweep: Mean FRI and GSI by (avg_thr, N) ---")
    print(f"{'avg_thr':>8s}", end="")
    for gs in grid_sizes:
        print(f"  {'FRI_'+str(gs*gs):>9s} {'GSI_'+str(gs*gs):>9s} {'Gap_'+str(gs*gs):>9s}", end="")
    print()
    print("-" * (8 + len(grid_sizes) * 30))

    for avg_thr in sorted(set(r['avg_thr'] for r in all_results)):
        print(f"{avg_thr:>8.0f}", end="")
        for gs in grid_sizes:
            key = (avg_thr, gs)
            runs = sweep_grouped[key]
            if runs:
                fri_mean = np.mean([r['FRI'] for r in runs])
                gsi_mean = np.mean([r['GSI'] for r in runs])
                gap = fri_mean - gsi_mean
                print(f"  {fri_mean:>9.4f} {gsi_mean:>9.4f} {gap:>9.4f}", end="")
            else:
                print(f"  {'N/A':>9s} {'N/A':>9s} {'N/A':>9s}", end="")
        print()

    # Check if phenomenon persists
    print("\n--- Does the 'Best Game No One Played' phenomenon persist? ---")
    for gs in grid_sizes:
        key = (40, gs)  # avg_thr=40 is the canonical BGNOPL scenario
        runs = sweep_grouped[key]
        if runs:
            fri_mean = np.mean([r['FRI'] for r in runs])
            gsi_mean = np.mean([r['GSI'] for r in runs])
            gap = fri_mean - gsi_mean
            persists = "YES" if (fri_mean > 0.5 and gsi_mean < 0.5 and gap > 0.1) else "NO"
            print(f"  N={gs*gs:>5d} ({gs}x{gs}): FRI={fri_mean:.4f}, GSI={gsi_mean:.4f}, "
                  f"Gap={gap:.4f} -> Phenomenon persists: {persists}")

    # Check if avg-of-thresholds is dominant parameter
    print("\n--- Is avg-of-thresholds the dominant parameter? ---")
    for gs in grid_sizes:
        gsis_by_thr = []
        for avg_thr in sorted(set(r['avg_thr'] for r in all_results)):
            key = (avg_thr, gs)
            runs = sweep_grouped[key]
            if runs:
                gsi_mean = np.mean([r['GSI'] for r in runs])
                gsis_by_thr.append((avg_thr, gsi_mean))
        if len(gsis_by_thr) >= 3:
            thrs = [x[0] for x in gsis_by_thr]
            gsis = [x[1] for x in gsis_by_thr]
            # Check monotonic decrease of GSI with increasing threshold
            diffs = [gsis[i+1] - gsis[i] for i in range(len(gsis)-1)]
            mostly_decreasing = sum(1 for d in diffs if d < 0) >= len(diffs) * 0.6
            gsi_range = max(gsis) - min(gsis)
            print(f"  N={gs*gs:>5d}: GSI range across thresholds = {gsi_range:.4f}, "
                  f"Mostly decreasing: {mostly_decreasing}")

    total_time = time_module.time() - start_time
    print(f"\nTotal experiment time: {total_time:.1f} seconds ({total_time/60:.1f} minutes)")

    # Save summary CSV
    summary_path = os.path.join(output_dir, 'summary_by_threshold_and_N.csv')
    with open(summary_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['avg_thr', 'grid_size', 'N', 'FRI_mean', 'FRI_std',
                          'GSI_mean', 'GSI_std', 'FRI_GSI_gap', 'n_runs'])
        for avg_thr in sorted(set(r['avg_thr'] for r in all_results)):
            for gs in grid_sizes:
                key = (avg_thr, gs)
                runs = sweep_grouped[key]
                if runs:
                    fris = [r['FRI'] for r in runs]
                    gsis = [r['GSI'] for r in runs]
                    writer.writerow([
                        avg_thr, gs, gs*gs,
                        f"{np.mean(fris):.6f}", f"{np.std(fris):.6f}",
                        f"{np.mean(gsis):.6f}", f"{np.std(gsis):.6f}",
                        f"{np.mean(fris) - np.mean(gsis):.6f}",
                        len(runs)
                    ])
    print(f"Summary saved to: {summary_path}")


if __name__ == '__main__':
    main()
