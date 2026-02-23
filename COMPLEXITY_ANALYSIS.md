# Computational Complexity Analysis of the BCAT Simulation Framework

## Abstract

This document presents a rigorous time and space complexity analysis of the Bounded Confidence with Adoption Threshold (BCAT) agent-based simulation framework. The BCAT model integrates bounded confidence opinion dynamics with threshold-based adoption decisions on complex network topologies, including scale-free networks (SFN) and small-world networks (SWN). We formally define the model as a five-tuple and derive tight asymptotic bounds for all major algorithmic components. Our analysis demonstrates that a single simulation run executes in O(N² + T(N + E)) time and O(N + E + T) space, where N denotes the number of agents, T the number of time steps, and E the number of edges. For sparse networks with bounded average degree, the dominant term reduces to O(TN). A batch of X experiments requires O(X · T · (N + E)) time overall.

---

## 1. Introduction

Agent-based models (ABMs) of innovation diffusion on complex networks are widely employed in computational social science to study how technologies, behaviors, and opinions propagate through populations (Rogers, 2003; Watts & Strogatz, 1998; Barabási & Albert, 1999). The computational cost of such simulations is a critical concern when scaling to large populations or conducting extensive parameter sweeps.

The BCAT framework couples two well-established mechanisms: (i) *bounded confidence opinion dynamics* (Deffuant et al., 2000; Hegselmann & Krause, 2002), wherein agents update their attitudes only when the opinion distance to a neighbor falls below a confidence threshold; and (ii) *threshold-based adoption* (Granovetter, 1978; Valente, 1996), wherein agents adopt an innovation when the fraction of adopting neighbors exceeds a personal threshold.

This document provides a comprehensive complexity analysis of the BCAT simulation codebase, covering network construction, agent initialization, the core simulation loop, batch experimentation, data persistence, and visualization. All bounds are stated in standard asymptotic notation and verified against the implementation.

---

## 2. Notation and Definitions

### 2.1 Symbol Table

| Symbol | Definition | Default Value |
|--------|-----------|---------------|
| *N* | Number of nodes (agents) | 400 |
| *T* | Maximum number of simulation time steps | 100–300 |
| *E* | Number of edges in the network | SWN: ~1,600; SFN: ~2,000 |
| *K* | Average node degree | SWN: ~8; SFN: ~10 |
| *P* | Number of pioneer (seed) agents | 5 |
| *X* | Number of experimental replications | 20 |
| *D*_max | Maximum node degree | SFN: up to ~60 |
| *W* | Grid width (for SWN lattice) | 20 (W² = N = 400) |
| *U* | Number of distinct integer attitude values | U ≤ 100 |
| *d(v)* | Degree of node *v* | varies |
| *p* | Rewiring probability (Watts–Strogatz) | [0, 1] |
| *μ* | Convergence rate for opinion update | (0, 1) |
| *β* | Bounded confidence threshold | > 0 |

### 2.2 Formal Model Definition

**Definition 1** (BCAT Model). The BCAT model is defined as a five-tuple **M** = (*G*, *S*, Π, Φ, Ψ), where:

- *G* = (*V*, *E*) is an undirected graph with |*V*| = *N* and |*E*| = *E*.
- *S*: *V* → [1, 100] × [1, 100] × {0, 1} × (ℤ ∪ {−1}) is a state function mapping each node *v* to a tuple (*att*_v, *θ*_v, *act*_v, *time*_v), representing its attitude, adoption threshold, adoption status, and adoption time, respectively.
- Π = {*μ*, *β*, *P*, *T*} is the parameter set comprising the convergence rate, bounded confidence threshold, number of pioneers, and maximum simulation time.
- Φ: *S* × *S* × Π → *S* × *S* is the opinion update function (bounded confidence dynamics).
- Ψ: *S* × 2^*V* → *S* is the adoption decision function (threshold model).

**Definition 2** (Opinion Update Function Φ). Given node *i* and a uniformly randomly selected neighbor *j* ∈ *N*(*i*), if |*att*_i − *att*_j| < *β*, then:

- **Rule 1** (Bilateral convergence):
  *att*'_i = ⌊*att*_i + *μ*(*att*_j − *att*_i) + 0.5⌋,
  *att*'_j = ⌊*att*_j + *μ*(*att*_i − *att*_j) + 0.5⌋

- **Rule 2** (Unilateral — subject only):
  *att*'_i = ⌊*att*_i + *μ*(*att*_j − *att*_i) + 0.5⌋

- **Rule 3** (Unilateral — partner only):
  *att*'_j = ⌊*att*_j + *μ*(*att*_i − *att*_j) + 0.5⌋

The rule selection depends on the adoption states and relative attitudes of both agents:

| *act*_i | *act*_j | *att*_j > *att*_i | Applied Rule |
|---------|---------|-------------------|-------------|
| 0 | 1 | True | Rule 2 |
| 0 | 1 | False | Rule 1 |
| 1 | 0 | True | Rule 1 |
| 1 | 0 | False | Rule 3 |
| 1 | 1 | True | Rule 2 |
| 1 | 1 | False | Rule 3 |
| 0 | 0 | * | Rule 1 |

**Definition 3** (Adoption Decision Function Ψ). For node *i* at time step *t*:

```
Ψ(i, t) =
  act_i ← 1, time_i ← t   if  act_i = 0
                             ∧   att_i > 50
                             ∧   |N(i)| > 0
                             ∧   |{j ∈ N(i) : act_j = 1}| / |N(i)| ≥ θ_i / 100
  unchanged                  otherwise
```

**Definition 4** (Simulation Loop). The main simulation procedure is defined as:

```
SIMULATE(M, T):
  for t = 0 to T − 1:
    π ← random_permutation(V)
    for each v in π:
      j ← uniform_random(N(v))
      (S(v), S(j)) ← Φ(S(v), S(j))
      S(v) ← Ψ(v, t)
```

**Definition 5** (Critical Point). The critical time *t*_c is defined as:

> *t*_c = min{*t* : |{*v* ∈ *V* : *act*_v = 1}| > |{*v* ∈ *V* : *act*_v = 0}|}, if such *t* exists; *t*_c = 0 otherwise.

---

## 3. Network Construction

### 3.1 Scale-Free Network via Preferential Attachment

**Algorithm.** The scale-free network is constructed using a variant of the Barabási–Albert preferential attachment model (Barabási & Albert, 1999). Starting from two connected seed nodes, each subsequent node is attached to an existing node selected via roulette wheel selection proportional to degree. After all *N* nodes are placed, each node receives three additional edges via the same preferential attachment mechanism.

**Implementation reference:** `setup_scale_free_network()` (line 522–585).

#### 3.1.1 Time Complexity

| Phase | Operation | Complexity |
|-------|-----------|------------|
| Seed initialization | `add_node`, `add_edge` (2 nodes) | O(1) |
| Incremental attachment | *N* − 2 calls to `_find_partner` + `add_edge` | O(∑_{i=2}^{N-1} i) = **O(N²)** |
| Additional edge augmentation | 3*N* calls to `_add_link`, each with `_find_partner` | **O(N²)** |
| Position assignment | `_set_pos_xy_of_nodes`: iterate over *N* nodes | O(N) |

**Subroutine: `_find_partner()`** (line 587–636). Performs roulette wheel selection by scanning the cumulative degree sequence until exceeding a uniformly random threshold. Worst-case: **O(N)**; expected: O(N/2).

**Subroutine: `_add_link()`** (line 638–688). Repeatedly invokes `_find_partner()` until a valid (non-duplicate, non-self-loop) edge is found. Edge existence is checked in O(1) via the NetworkX adjacency dictionary. Because the network is sparse, the expected number of retries is O(1), yielding an amortized cost of **O(N)** per call. Worst-case: O(N²) per call.

**Total SFN construction time: O(N²).**

#### 3.1.2 Space Complexity

- Degree list for roulette selection: O(N)
- NetworkX `Graph` object (adjacency list representation): O(N + E), where E ~ 4N
- **Total: O(N + E) = O(N)**, since E = O(N) for bounded average degree

### 3.2 Small-World Network via Watts–Strogatz Model

**Algorithm.** The small-world network follows the Watts–Strogatz construction (Watts & Strogatz, 1998). A *W* × *W* two-dimensional torus lattice is created with Moore neighborhood (8-connected) edges. Each edge is then rewired with probability *p*: one endpoint is reconnected to a uniformly random non-neighbor.

**Implementation reference:** `setup_small_world_network()` (line 726–827).

#### 3.2.1 Time Complexity

| Phase | Operation | Complexity |
|-------|-----------|------------|
| Node creation | *N* calls to `add_node` | O(N) |
| Moore neighborhood edges | 8 directions per node, `has_edge` in O(1) | O(8N) = **O(N)** |
| Edge rewiring | Iterate over *E* edges, rewire with probability *p* | See below |
| Position assignment | O(N) | O(N) |

**Rewiring analysis** (line 796–819). For each edge selected for rewiring (expected: *p* · *E*), the algorithm constructs a candidate list of non-neighbors:

```python
non_neighbors = [n for n in G.nodes() if n != node1 and not G.has_edge(node1, n)]
```

This scan costs O(N) per rewired edge. The total rewiring cost is therefore O(*p* · *E* · *N*). Since *E* = O(N) for the Moore lattice (~4*N* undirected edges), this simplifies to **O(*p* · N²)**. In the worst case (*p* = 1): **O(N²)**.

**Total SWN construction time: O(N²)** (worst case); **O(pN²)** (expected).

#### 3.2.2 Space Complexity

- Snapshot of edges for processing: O(E)
- Temporary `non_neighbors` list: O(N) per rewiring operation
- NetworkX `Graph` object: O(N + E)
- **Total: O(N + E) = O(N)**

---

## 4. Agent Initialization

**Algorithm.** Each node *v* is assigned an attitude value *att*_v and a threshold *θ*_v sampled from a normal distribution 𝒩(μ, σ) and clamped to [1, 100]. A set of *P* pioneer agents is selected and initialized to the adopted state.

**Implementation reference:** `setup_agent_population()` (line 832–894).

### 4.1 Time Complexity

| Operation | Complexity |
|-----------|------------|
| Vectorized sampling via `np.random.normal` + `np.clip` | O(N) |
| State array construction (*N* × 4 matrix) | O(N) |
| Pioneer selection via `_chosen_leaders()` | O(N log N) or O(N) |
| Pioneer attribute assignment | O(P) |

**Subroutine: `_chosen_leaders()`** (line 896–929). When `clustered_pioneers=True`, nodes are sorted by a spatial clustering criterion, requiring O(N log N). When `clustered_pioneers=False`, `random.sample` is used in O(N).

**Total initialization time: O(N log N)**, dominated by the sorting step.

### 4.2 Space Complexity

- State array `_states` (N × 4, float64): O(N)
- Temporary sampling arrays: O(N)
- **Total: O(N)**

---

## 5. Neighbor Cache Construction

**Algorithm.** For each node *v* ∈ *V*, the neighbor list is precomputed and stored in a dictionary for O(1) lookup during simulation.

**Implementation reference:** `_build_neighbors_cache()` (line 429–441).

### 5.1 Time Complexity

Iterating over all *N* nodes and collecting each node's adjacency list requires O(*d*(*v*)) per node. The total cost is:

> ∑_{v ∈ V} d(v) = 2E

**Total: O(N + E) = O(N)** for bounded average degree.

### 5.2 Space Complexity

The dictionary stores *N* entries with a combined size of ∑_v d(v) = 2*E*.

**Total: O(N + E) = O(N).**

---

## 6. Core Simulation Loop

### 6.1 Single Time Step

**Algorithm.** The core simulation step (`_step_all_agents`, line 1092–1228) applies a random-order asynchronous update. All *N* nodes are randomly permuted (Fisher–Yates shuffle). For each node in the permuted order: (i) a neighbor is selected uniformly at random; (ii) the bounded confidence opinion update rule Φ is applied; (iii) the threshold adoption decision Ψ is evaluated.

#### 6.1.1 Time Complexity per Step

| Operation | Per Node | Over All *N* Nodes |
|-----------|----------|-------------------|
| Array creation + Fisher–Yates shuffle | — | O(N) |
| Random number pre-generation | — | O(N) |
| Neighbor cache lookup | O(1) | O(N) |
| Random neighbor selection | O(1) | O(N) |
| State array read/write | O(1) | O(N) |
| Opinion update (Φ) | O(1) | O(N) |
| **Adoption decision (Ψ) — neighbor scan** | **O(d(v))** | **O(∑_v d(v)) = O(2E)** |

The adoption decision (line 1214–1228) iterates over all neighbors to compute the fraction of adopters:

```python
for nb in neighbors:
    if states[nb, ACT] != 0.0:
        adopter_count += 1
```

This requires O(d(v)) per node, summing to O(2E) over all nodes.

**Single step time complexity: O(N + E).**

> **Remark.** Under the default parameters where *K* is a constant (K ~ 8–10), we have *E* = O(*N*), and thus each step runs in **O(N)**.

#### 6.1.2 Space Complexity per Step

- Permutation array: O(N)
- Pre-generated random values: O(N)
- Local variables: O(1)
- **Total: O(N)**

### 6.2 Complete Simulation Run

**Algorithm.** The `go()` method (line 934–1034) invokes `setup()` for initialization, then executes *T* iterations of `_step_all_agents()`, recording per-step statistics (adopter count, mean attitude, standard deviation, critical point).

#### 6.2.1 Time Complexity

| Component | Complexity |
|-----------|------------|
| `setup()` = network construction + cache + agent init | O(N²) + O(N + E) + O(N log N) = **O(N²)** |
| *T* iterations of `_step_all_agents()` | **O(T · (N + E))** |
| Per-step statistics (`np.sum`, `np.mean`, `np.std`) | O(N) per step → O(TN) total |
| Critical point evaluation | O(N) per step (amortized: O(1) after reaching *t*_c) |
| Attitude snapshot recording | O(N) per step → O(TN) total |

**`critical_point` property** (line 1456–1490): Computes `np.sum(states[:, ACT])` in O(N). Once the critical point is identified, subsequent calls short-circuit in O(1).

**Total time for `go()`: O(N² + T(N + E)).**

> **Remark.** Under typical parameters (T · K = 300 × 8 = 2,400 > N = 400), the simulation loop dominates: **O(T(N + E))**.

#### 6.2.2 Space Complexity

| Component | Complexity | Description |
|-----------|------------|-------------|
| NetworkX `Graph` | O(N + E) | Adjacency list representation |
| State array `_states` | O(N) | N × 4 float64 matrix |
| Neighbor cache | O(N + E) | Precomputed adjacency lists |
| Attitude snapshot history | O(TU) | U ≤ 100 distinct values |
| Adopter history list | O(T) | One entry per step |
| Temporary arrays per step | O(N) | Shuffle, random values |

**Total space for a single run: O(N + E + T).**

> Since *E* = O(*N*) and *TU* = O(*T*) (with *U* ≤ 100 as a constant), this simplifies to **O(N + T)**.

### 6.3 Interactive Mode

The `step()` method (line 1036–1090) executes a single time step with statistics collection.

**Time per invocation: O(N + E).** Space: O(N).

---

## 7. Batch Experimentation

**Algorithm.** The `run_experiments()` method (line 1495–1580) executes *X* independent replications of the complete simulation. Each replication reinitializes the network and agent population via `setup()`, runs *T* time steps, serializes the model state, and writes per-experiment results to disk. A summary file with aggregated statistics is produced upon completion.

### 7.1 Time Complexity

| Operation | Complexity |
|-----------|------------|
| *X* invocations of `go()` | X · O(N² + T(N + E)) |
| State serialization per experiment (`save_model_state`) | O(N + E) per experiment |
| File I/O per experiment | O(T) per experiment |
| Adopter list rounding | O(T) |
| Summary file output | O(T + X) |

**Total: O(X · (N² + T(N + E))).**

> Under typical parameters where T(N + E) ≫ N², this simplifies to **O(X · T · (N + E))**.

### 7.2 Space Complexity

- Per-experiment results list: O(T)
- Aggregated adopter list: O(T)
- Critical time list: O(X)
- Model state: O(N + E)
- Per-experiment attitude snapshots: O(T · U), where U ≤ 100

**Total: O(N + E + TU + X).** Each experiment reuses the same memory (cleared by `setup()`), accumulating only O(X) for `critical_time_list` and O(T) for `adopter_list`.

---

## 8. Data Persistence

### 8.1 State Serialization

**Implementation reference:** `save_model_state()` (line 1585–1627).

| Operation | Complexity |
|-----------|------------|
| Construct `node_states_dict` | O(N) |
| Pickle-serialize graph | O(N + E) |
| Pickle-serialize attitude snapshots | O(TU) |
| **Total** | **O(N + E + TU)** |

**Space: O(N + E + TU).**

### 8.2 State Deserialization

**Implementation reference:** `load_model_state()` (line 1629–1696).

| Operation | Complexity |
|-----------|------------|
| Pickle-deserialize | O(N + E + TU) |
| Reconstruct state array (dict → NumPy) | O(N) |
| Rebuild neighbor cache | O(N + E) |
| Reconstruct adoption history | O(TN) |

**Subroutine: `_reconstruct_adoption_history()`** (line 1698–1724). For each of *T* time steps, performs O(N) element-wise comparisons on the adoption time column:

```python
for t in range(current_time):
    np.sum(time_col == t)               # O(N)
    np.sum((time_col >= 0) & (...))     # O(N)
```

**Total deserialization time: O(TN + E).** Space: O(N + E + TU).

---

## 9. Visualization

The `ModelVisualizer` class provides real-time rendering of simulation dynamics via matplotlib. Each visualization routine is analyzed below.

### 9.1 Network Visualization

**`plot_network()`** (line 1836–1900).

| Operation | Complexity |
|-----------|------------|
| Retrieve node attributes | O(N) |
| Construct color map | O(N) |
| Draw edges (`nx.draw_networkx_edges`) | O(E) |
| Draw nodes (`nx.draw_networkx_nodes`) | O(N) |
| **Total** | **O(N + E)** |

### 9.2 Attitude Trajectory Plot

**`plot_attitude_trajectory()`** (line 1921–1976). Uses incremental rendering: only newly added time steps are plotted, at a cost of O(U) per new tick. Over the entire simulation: O(TU). **Per invocation: O(Δt · U)**, where Δt is the number of new steps since the last update.

### 9.3 Adoption Dynamics Plot

**`plot_adoption_dynamics()`** (line 1978–2027). Updates the full time series via `Line2D.set_data()`. **Time: O(T).**

### 9.4 New Adopter Dynamics Plot

**`plot_new_adopter_dynamics()`** (line 2029–2072). Analogous to adoption dynamics. **Time: O(T).**

### 9.5 Attitude Distribution Histogram

**`plot_attitude_distribution()`** (line 2074–2101). Computes a histogram from the NumPy state array. **Time: O(N + B)**, where B ~ 100 is the number of bins.

### 9.6 Threshold Distribution Histogram

**`plot_threshold_distribution()`** (line 2103–2129). Analogous to attitude distribution. **Time: O(N + B).**

### 9.7 Degree Distribution Plot

**`plot_degree_distribution()`** (line 2131–2194).

- **SFN mode:** Iterates over degrees 1 to *D*_max, calling `list.count(d)` (O(N) each):

  ```python
  for d in range(1, max_degree + 1):
      count = degrees.count(d)           # O(N) each
  ```

  **Time: O(N · D_max).** With *D*_max ~ 60 in SFN, this is approximately O(60N).

- **SWN mode:** Uses `matplotlib.hist()`. **Time: O(N).**

### 9.8 Composite Update

**`update_plots()`** (line 2196–2221). Invokes all visualization routines. **Total: O(N · D_max + TU)**, which simplifies to **O(N · D_max + T)** since U is bounded.

---

## 10. Aggregate Complexity Summary

### 10.1 Single Simulation Run

**Pseudocode:**

```
SINGLE_RUN(N, T, K):
  1. BUILD_NETWORK(N)              // SFN or SWN
  2. BUILD_NEIGHBOR_CACHE(N)
  3. INITIALIZE_AGENTS(N)
  4. for t = 0 to T − 1:
       STEP_ALL_AGENTS(N, K)       // opinion update + adoption decision
  5. return results
```

#### Time Complexity

| Component | Complexity | Description |
|-----------|------------|-------------|
| Network construction | O(N²) | Preferential attachment or lattice rewiring |
| Neighbor cache | O(N + E) | One-time precomputation |
| Agent initialization | O(N log N) | Pioneer selection with sorting |
| *T*-step simulation loop | O(T(N + E)) | Per-step neighbor scan for adoption |
| Per-step statistics | O(TN) | Subsumed by simulation loop |

**Total:**

> **T**_single(*N*, *T*, *E*) = **O(N² + T(N + E))**

For sparse networks with bounded average degree *K*, E = O(N):

> **T**_single = **O(N² + TN)**

Under typical parameters (*TK* = 300 × 8 = 2,400 > *N* = 400), the simulation loop dominates:

> **T**_single = **O(T(N + E))** = **O(TN)** (for constant *K*)

#### Space Complexity

> **S**_single(*N*, *E*, *T*) = **O(N + E + T)** = **O(N + T)** (for constant *K*)

### 10.2 Batch Experiments

**Pseudocode:**

```
BATCH_RUN(N, T, E, X):
  for exp = 1 to X:
    SINGLE_RUN(N, T, E)
    SAVE_STATE()
  WRITE_SUMMARY()
```

#### Time Complexity

> **T**_batch(*N*, *T*, *E*, *X*) = **O(X · (N² + T(N + E)))**

Simplified (dominant term):

> **T**_batch = **O(X · T · (N + E))**

#### Space Complexity

> **S**_batch = **O(N + E + T + X)**

Each experiment reuses the same memory allocation (cleared by `setup()`).

### 10.3 GUI-Enabled Simulation

**Pseudocode:**

```
GUI_RUN(N, T, E, Δt):
  SINGLE_RUN(N, T, E)
  for each GUI refresh (every Δt steps):
    UPDATE_PLOTS()                      // O(N · D_max + T)
```

Assuming *T*/Δ*t* visualization refreshes:

> **T**_gui = O(N² + T(N + E) + (T/Δt) · (N · D_max + T))

In practice, the rendering overhead substantially exceeds the numerical computation cost; however, Δ*t* typically increases with simulation speed, keeping the total number of refreshes manageable.

---

## 11. Empirical Parameterization

Substituting the default parameter values (N = 400, T = 300, E ~ 1,600–2,000, X = 20, D_max ~ 60, U ≤ 100):

| Operation | Expression | Order of Magnitude |
|-----------|-----------|-------------------|
| SFN construction | N² = 160,000 | ~10⁵ |
| Single simulation step | N + E ~ 2,400 | ~10³ |
| Complete simulation | T(N + E) ~ 720,000 | ~10⁶ |
| Batch experiments | XT(N + E) ~ 14,400,000 | ~10⁷ |
| Space (single run) | N + E + T ~ 2,700 | ~10³ |

These figures confirm that even batch experimentation with 20 replications remains computationally tractable (order 10⁷ elementary operations), well within the capacity of commodity hardware.

---

## 12. Per-Function Complexity Reference

| Function | Line | Time Complexity | Space Complexity |
|----------|------|----------------|-----------------|
| `_nl_round(x)` | 145 | O(1) | O(1) |
| `_NodeStateView.__getitem__` | 207 | O(1) | O(1) |
| `_NodeStatesProxy.__getitem__` | 244 | O(1) | O(1) |
| `_NodeStatesProxy.items()` | 256 | O(N) | O(1) [a] |
| `setup()` | 446 | O(N²) | O(N + E) |
| `_clear()` | 469 | O(1) [b] | — |
| `setup_scale_free_network()` | 522 | O(N²) | O(N + E) |
| `_find_partner()` | 587 | O(N) | O(1) |
| `_add_link()` | 638 | O(N) amortized | O(1) |
| `_set_pos_xy_of_nodes()` | 690 | O(N) | O(N) |
| `setup_small_world_network()` | 726 | O(N²) worst; O(pN²) expected | O(N + E) |
| `setup_agent_population()` | 832 | O(N log N) | O(N) |
| `_chosen_leaders()` | 896 | O(N log N) | O(N) |
| `_build_neighbors_cache()` | 429 | O(N + E) | O(N + E) |
| `go()` | 934 | O(N² + T(N + E)) | O(N + E + T) |
| `step()` | 1036 | O(N + E) | O(N) |
| `_step_all_agents()` | 1092 | O(N + E) | O(N) |
| `_communicate()` | 1267 | O(1) | O(1) |
| `_change_opinion_{1,2,3}()` | 1345–1382 | O(1) | O(1) |
| `_make_decision()` | 1387 | O(d(v)) | O(1) |
| `_become_action()` | 1427 | O(1) | O(1) |
| `critical_point` (property) | 1455 | O(N) [c] | O(1) |
| `run_experiments()` | 1495 | O(X(N² + T(N + E))) | O(N + E + T + X) |
| `save_model_state()` | 1585 | O(N + E + TU) | O(N + E + TU) |
| `load_model_state()` | 1629 | O(TN + E) | O(N + E + TU) |
| `_reconstruct_adoption_history()` | 1698 | O(TN) | O(T) |
| `plot_network()` | 1836 | O(N + E) | O(N + E) |
| `plot_attitude_trajectory()` | 1921 | O(Δt · U) incremental | O(1) |
| `plot_adoption_dynamics()` | 1978 | O(T) | O(T) |
| `plot_new_adopter_dynamics()` | 2029 | O(T) | O(T) |
| `plot_attitude_distribution()` | 2074 | O(N) | O(N) |
| `plot_threshold_distribution()` | 2103 | O(N) | O(N) |
| `plot_degree_distribution()` | 2131 | O(N · D_max) SFN; O(N) SWN | O(N) |
| `update_plots()` | 2196 | O(N · D_max + TU) | O(N + E + T) |

**Notes:**
- [a] Returns a generator; does not construct a full list in memory.
- [b] Performs only reference reassignment; deallocation of the previous NumPy array and dictionary is handled by the garbage collector.
- [c] Short-circuits to O(1) once the critical time *t*_c has been identified.

---

## 13. Conclusion

This analysis establishes tight asymptotic bounds for all computational components of the BCAT simulation framework. The key findings are as follows:

1. **Network construction** constitutes a one-time O(N²) cost for both scale-free and small-world topologies, dominated by preferential attachment partner search (SFN) or edge rewiring with non-neighbor enumeration (SWN).

2. **The simulation loop** is the dominant computational cost, running in O(T(N + E)) time. For sparse networks with bounded average degree, this reduces to O(TN), yielding linear scaling in both population size and simulation duration.

3. **Batch experimentation** scales linearly with the number of replications: O(X · T · (N + E)).

4. **Space requirements** are modest at O(N + E + T) per simulation run, with no super-linear memory demands.

5. **Visualization overhead**, while significant in wall-clock time due to rendering latency, is bounded by O(N · D_max + T) per update and does not affect the asymptotic complexity of the simulation logic itself.

These results confirm that the BCAT framework is computationally efficient for the parameter ranges typical of innovation diffusion studies (N ≤ 10⁴, T ≤ 10³), and identify network construction as the primary bottleneck for scaling to larger populations.

---

## References

- Barabási, A.-L., & Albert, R. (1999). Emergence of scaling in random networks. *Science*, 286(5439), 509–512.
- Deffuant, G., Neau, D., Amblard, F., & Weisbuch, G. (2000). Mixing beliefs among interacting agents. *Advances in Complex Systems*, 3(01n04), 87–98.
- Granovetter, M. (1978). Threshold models of collective behavior. *American Journal of Sociology*, 83(6), 1420–1443.
- Hegselmann, R., & Krause, U. (2002). Opinion dynamics and bounded confidence models, analysis, and simulation. *Journal of Artificial Societies and Social Simulation*, 5(3).
- Rogers, E. M. (2003). *Diffusion of Innovations* (5th ed.). Free Press.
- Valente, T. W. (1996). Social network thresholds in the diffusion of innovations. *Social Networks*, 18(1), 69–89.
- Watts, D. J., & Strogatz, S. H. (1998). Collective dynamics of 'small-world' networks. *Nature*, 393(6684), 440–442.
