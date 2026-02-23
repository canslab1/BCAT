# BCAT 模擬程式完整時間複雜度與空間複雜度分析

## 符號定義 (Formal Notation)

| 符號 | 定義 | 預設值 |
|------|------|--------|
| **N** | 節點數 (number of nodes) | 400 |
| **T** | 最大模擬步數 (max_time) | 100-300 |
| **E** | 邊數 (number of edges) | SWN: ~1600, SFN: ~2000 |
| **K** | 每節點平均鄰居數 (average degree) | SWN: ~8, SFN: ~10 |
| **P** | 先驅者數量 (no_of_pioneers) | 5 |
| **X** | 實驗次數 (no_of_experiments) | 20 |
| **D_max** | 最大節點度 (maximum degree) | SFN 可達 ~60 |
| **W** | 網格寬度 (grid width) | 20 (W^2 = N = 400) |
| **U** | 不同整數態度值數量 | U <= 100 |
| **d(i)** | 節點 i 的度數 (degree) | varies |

---

## 1. 網絡建構 (Network Construction)

### 1.1 無尺度網絡 `setup_scale_free_network()` (line 522-585)

**演算法定義:**
> **Barabasi-Albert 優先附著 (Preferential Attachment)** 的變體。
> 逐步加入 N 個節點，每個新節點透過輪盤賭選擇 (roulette wheel selection) 連接一個已有節點。
> 之後對每個節點再透過 `_add_link` 追加 3 條邊。

**時間複雜度:**

| 階段 | 操作 | 複雜度 |
|------|------|--------|
| 初始兩節點 | `add_node`, `add_edge` | O(1) |
| 398 次 `_find_partner` + `add_edge` | 每次 `_find_partner` 掃描 i 個節點 (i=2..399) | sum(i=2..399) O(i) = **O(N^2)** |
| 1 次 `_add_link(0)` | 最壞情況 `_find_partner` x 重試 | O(N) 攤銷 |
| 400x3 = 1200 次 `_add_link` | 每次含 `_find_partner` O(N) x 期望 O(1) 重試 | **O(N^2)** |
| `_set_pos_xy_of_nodes` | 遍歷 N 節點 + `nx.set_node_attributes` | O(N) |

**`_find_partner()`** (line 587-636):
- 輪盤賭選擇: 掃描所有已有節點的度數序列直到累積超過隨機閾值
- 時間: **O(N)** 最壞情況，期望 O(N/2)

**`_add_link()`** (line 638-688):
- 外層 while 迴圈最多 N 次嘗試
- 每次呼叫 `_find_partner()` O(N)
- `G.has_edge()` O(1) (networkx adjacency dict)
- 期望嘗試次數: O(1) (因為網絡稀疏，大多數節點對之間沒有邊)
- **最壞 O(N^2)**，**期望 O(N)**

**SFN 建構總時間: O(N^2)**

**空間複雜度:**
- `_degree_list`: O(N)
- networkx Graph: O(N + E)，其中 E ~ 4N (每節點平均 ~8-10 度)
- **空間: O(N + E) = O(N)** (因 E = O(N))

---

### 1.2 小世界網絡 `setup_small_world_network()` (line 726-827)

**演算法定義:**
> **Watts-Strogatz 小世界模型。** 在 WxW 二維環形格子 (torus lattice) 上建立 Moore 鄰域 (8-connected) 邊，然後以機率 p 對每條邊進行重連 (rewiring)。

**時間複雜度:**

| 階段 | 操作 | 複雜度 |
|------|------|--------|
| 建立 N 節點 | N 次 `add_node` | O(N) |
| 建立 Moore 鄰域邊 | 每節點檢查 8 方向 x `has_edge` O(1) | O(8N) = **O(N)** |
| 重連 (rewiring) | 遍歷 E 條邊 | O(E) |
| 每條邊的重連 | 建構 `non_neighbors` 列表: O(N) | O(pEN) = **O(pN^2)** |
| 節點位置設定 | O(N) | O(N) |

**重連步驟的嚴格分析 (line 796-819):**
```python
non_neighbors = [n for n in G.nodes() if n != node1 and not G.has_edge(node1, n)]
```
- 對每條被選中重連的邊 (期望 p*E 條)，掃描所有 N 節點
- **O(p * E * N)**
- 因 E = O(N) (Moore 鄰域產生 ~4N 條無向邊)，故為 **O(p * N^2)**
- 最壞情況 (p = 1): **O(N^2)**

**SWN 建構總時間: O(N^2)** (最壞)；**O(pN^2)** (期望)

**空間複雜度:**
- `edges_to_process` 快照: O(E)
- `non_neighbors` 臨時列表: O(N) (每次重連建立一次)
- networkx Graph: O(N + E)
- **空間: O(N + E) = O(N)**

---

## 2. 智能體初始化 `setup_agent_population()` (line 832-894)

**演算法定義:**
> 為每個節點從常態分佈 N(mu, sigma) 抽樣態度值 att 和門檻值 theta，並 clamp 至 [1, 100]。選出 P 個先驅者設為已採用狀態。

**時間複雜度:**

| 操作 | 複雜度 |
|------|--------|
| NumPy `np.random.normal` + `np.clip` (向量化) | O(N) |
| 建立 `_states` 陣列 (Nx4) | O(N) |
| `_chosen_leaders()` | O(N log N) (clustered=True 時排序) 或 O(N) (隨機選取) |
| 設定先驅者屬性 | O(P) |

**`_chosen_leaders()`** (line 896-929):
- `clustered_pioneers=True`: `sorted(nodes, key=...)` -> **O(N log N)**
- `clustered_pioneers=False`: `random.sample(list(G.nodes()), n)` -> **O(N)**

**初始化總時間: O(N log N)** (受排序主導)

**空間複雜度:**
- `_states` NumPy 陣列 (Nx4): O(N)
- `att_arr`, `theta_arr` 臨時陣列: O(N)
- **空間: O(N)**

---

## 3. 鄰居快取建構 `_build_neighbors_cache()` (line 429-441)

**演算法定義:**
> 對網絡中每個節點，預先計算其鄰居列表並存入字典。

**時間複雜度:**
- 遍歷 N 節點，每個節點取鄰居列表
- `list(G.neighbors(n))` 的時間 = O(degree(n))
- 總計: sum_i degree(i) = 2E
- **O(N + E)** = O(N) (因 E = O(N))

**空間複雜度:**
- 字典含 N 個條目，每條目為鄰居列表
- 總空間 = sum_i degree(i) = 2E
- **O(N + E)** = O(N)

---

## 4. 模擬主迴圈

### 4.1 單步執行 `_step_all_agents()` (line 1092-1228)

**演算法定義:**
> **BCAT 核心模擬步驟。** 將所有 N 節點隨機排列 (Fisher-Yates shuffle)，依序對每個節點執行:
> 1. **意見交流 (Bounded Confidence):** 隨機選一鄰居，若態度差 < bounded_confidence，則依雙方採用狀態套用 opinion update rule (雙向/單向趨同)
> 2. **採納決策 (Threshold Model):** 若未採用、態度 > 50、且鄰居採用比例 >= 個人門檻比例，則採納

**時間複雜度 (每步):**

| 操作 | 每節點 | 全部 N 節點 |
|------|--------|-------------|
| `np.arange(N)` + `np.random.shuffle` | - | O(N) |
| `np.random.random(N)` (預生成隨機數) | - | O(N) |
| 存取快取鄰居 `neighbors_cache[node]` | O(1) | O(N) |
| 選擇隨機鄰居 | O(1) | O(N) |
| 讀取/寫入 `states[node, col]` | O(1) | O(N) |
| 意見更新 (opinion rule) | O(1) | O(N) |
| **採納決策 -- 計算鄰居採用比例** | **O(d(i))** | **O(sum d(i)) = O(E)** |

**採納決策的嚴格分析 (line 1214-1228):**
```python
for nb in neighbors:
    if states[nb, ACT] != 0.0:
        adopter_count += 1
```
- 遍歷每個鄰居檢查採用狀態: O(degree(node))
- 所有節點的總計: sum_i degree(i) = 2E

**單步時間: O(N + E)**

> 在預設參數下 E = O(N) (K ~ 8-10 為常數)，故實際為 **O(N)**。
> 嚴格表達: **O(N + E)** 其中 E 為邊數。

**空間複雜度 (每步):**
- `nodes` 陣列: O(N)
- `rand_vals` 陣列: O(N)
- 本地變數: O(1)
- **空間: O(N)**

---

### 4.2 完整模擬 `go()` (line 934-1034)

**演算法定義:**
> 執行 `setup()` 初始化，然後重複 T 步 `_step_all_agents()`，每步記錄統計數據。

**時間複雜度:**

| 階段 | 複雜度 |
|------|--------|
| `setup()` = 網絡建構 + 快取 + 初始化 | O(N^2) + O(N+E) + O(N log N) = **O(N^2)** |
| T 步 `_step_all_agents()` | **O(T * (N + E))** |
| 每步的統計 (`np.sum`, `np.mean`, `np.std`) | O(N) per step -> O(TN) |
| 每步的 `critical_point` | O(N) per step -> O(TN) |
| 每步的態度快照記錄 | O(N) per step -> O(TN) |

**`critical_point` property** (line 1456-1490):
- `np.sum(self._states[:, self._ACT])`: O(N)
- 一旦設定後短路: O(1)
- 攤銷: O(N) (前 T_c 步各 O(N)，之後各 O(1))

**go() 總時間: O(N^2 + T(N + E))**

> 當 T*E/N > N 時 (通常成立: 300*8 = 2400 > 400)，
> **主導項為 O(T(N + E))**

---

### 4.3 互動模式 `step()` (line 1036-1090)

**時間複雜度 (每次呼叫):**

| 操作 | 複雜度 |
|------|--------|
| `_step_all_agents()` | O(N + E) |
| `np.sum` 計算採用者 | O(N) |
| 態度快照建構 | O(N) |
| 新採用者統計 | O(N) |
| `critical_point` | O(N) |

**step() 單次呼叫: O(N + E)**

---

## 5. 批量實驗 `run_experiments()` (line 1495-1580)

**演算法定義:**
> 重複執行 X 次完整模擬 `go()`，每次模擬包含 setup + T 步迴圈。
> 將每次實驗的結果寫入檔案，最後輸出彙總統計。

**時間複雜度:**

| 操作 | 複雜度 |
|------|--------|
| X 次 `go()` | X * O(N^2 + T(N+E)) = **O(X * (N^2 + T(N+E)))** |
| 每次 `save_model_state()` - pickle 序列化 | O(N + E) per exp = O(X(N+E)) |
| 每次寫入實驗文件 | O(T) per exp = O(XT) |
| `adopter_list` 四捨五入 | O(T) |
| 寫入總結文件 | O(T + X) |

**run_experiments() 總時間: O(X * (N^2 + T(N + E)))**

> 簡化: 因 T(N+E) >> N^2 在典型參數下，
> **O(XT(N + E))**

**空間複雜度:**
- 每次實驗的 `results` 列表: O(T)
- `adopter_list`: O(T)
- `critical_time_list`: O(X)
- 模型本身: O(N + E)
- 每次實驗的態度快照: O(T * U)，U 為不同整數態度值數量 (U <= 100)
- **空間: O(N + E + TU + X)**

---

## 6. 資料持久化

### 6.1 `save_model_state()` (line 1585-1627)

**時間複雜度:**
- 建構 `node_states_dict`: O(N)
- pickle 序列化 Graph: O(N + E)
- pickle 序列化 `attitude_snapshots`: O(TU)
- **O(N + E + TU)**

**空間複雜度:**
- `node_states_dict`: O(N)
- `data` 字典: O(N + E + TU)
- **O(N + E + TU)**

### 6.2 `load_model_state()` (line 1629-1696)

**時間複雜度:**
- pickle 反序列化: O(N + E + TU)
- `node_states` setter (dict -> NumPy): O(N)
- `_build_neighbors_cache()`: O(N + E)
- `_reconstruct_adoption_history()`: O(TN)

**`_reconstruct_adoption_history()`** (line 1698-1724):
```python
for t in range(current_time):          # T iterations
    np.sum(time_col == t)              # O(N) each
    np.sum((time_col >= 0) & (...))    # O(N) each
```
- **O(TN)**

**load_model_state() 總時間: O(TN + E)**

---

## 7. 視覺化 (ModelVisualizer)

### 7.1 `plot_network()` (line 1836-1900)

| 操作 | 複雜度 |
|------|--------|
| `nx.get_node_attributes` | O(N) |
| 建構 `node_colors` 列表 | O(N) |
| `nx.draw_networkx_edges` | O(E) |
| `nx.draw_networkx_nodes` | O(N) |
| **總計** | **O(N + E)** |

**空間:** O(N + E) (顏色列表 + matplotlib 內部物件)

### 7.2 `plot_attitude_trajectory()` (line 1921-1976)

**增量繪圖:**
- 只繪製新增時間步: O(U) per new tick，U = 不同態度值數 (<= 100)
- 整個模擬累計: O(TU)
- **每次呼叫: O(dt * U)**，dt = 自上次繪圖以來新增的步數

### 7.3 `plot_adoption_dynamics()` (line 1978-2027)

- `Line2D.set_data()`: O(T) (傳遞整個時間序列)
- **O(T)**

### 7.4 `plot_new_adopter_dynamics()` (line 2029-2072)

- 同上: **O(T)**

### 7.5 `plot_attitude_distribution()` (line 2074-2101)

- 直接使用 NumPy 切片 -> matplotlib `hist()`
- **O(N + B)**，B = bins 數 ~ 100

### 7.6 `plot_threshold_distribution()` (line 2103-2129)

- 同上: **O(N + B)**

### 7.7 `plot_degree_distribution()` (line 2131-2194)

**SFN 模式:**
```python
degrees = [G.degree(n) for n in G.nodes()]  # O(N)
for d in range(1, max_degree + 1):          # O(D_max)
    count = degrees.count(d)                # O(N) each
```
- **O(N * D_max)**
- D_max 在 SFN 中可達 ~60，故 ~ O(60N)

**SWN 模式:**
- `hist()`: **O(N)**

### 7.8 `update_plots()` (line 2196-2221)

- 呼叫上述所有繪圖: **O(N + E + TU + N*D_max)**
- 簡化: **O(N * D_max + TU)** ~ **O(N * D_max + T)**

---

## 8. 整體模擬程式的複雜度總結

### 定義: 單次完整模擬 (Single Simulation Run)

**演算法偽碼:**
```
SINGLE_RUN(N, T, K):
  1. BUILD_NETWORK(N)           // SFN or SWN
  2. BUILD_NEIGHBOR_CACHE(N)
  3. INIT_AGENTS(N)
  4. FOR t = 0 TO T-1:
       STEP(N, K)               // opinion update + adoption decision
  5. RETURN results
```

#### 時間複雜度

| 成分 | 複雜度 | 說明 |
|------|--------|------|
| 網絡建構 | O(N^2) | 優先附著或重連 |
| 快取建構 | O(N + E) | 一次性 |
| 智能體初始化 | O(N log N) | 排序選先驅者 |
| T 步模擬主迴圈 | O(T(N + E)) | 每步每節點掃描鄰居 |
| 統計與記錄 | O(TN) | 被主迴圈包含 |

**單次模擬總時間:**

```
T_single(N, T, E) = O(N^2 + T(N + E))
```

> 因 E = O(N) 在 BCAT 預設網絡中 (K 為常數)，簡化為 **O(N^2 + TN)**。
> 在典型參數下 TK = 300*8 = 2400 > N = 400，故 T(N+E) > N^2，
> 主導項為 **O(T(N + E))**。

#### 空間複雜度

| 成分 | 複雜度 | 說明 |
|------|--------|------|
| networkx Graph | O(N + E) | 鄰接表示法 |
| `_states` 陣列 | O(N) | Nx4 float64 |
| `_neighbors_cache` | O(N + E) | 預計算鄰居列表 |
| 態度快照歷史 | O(TU) | U <= 100 |
| 採用者歷史列表 | O(T) | 每步一筆 |
| 臨時陣列 (per step) | O(N) | shuffle, rand_vals |

**單次模擬總空間:**

```
S_single(N, E, T) = O(N + E + T)
```

> 因 E = O(N) 且 TU = O(T) (U <= 100 為常數)，
> 簡化為 **O(N + T)**。

---

### 定義: 批量實驗 (Batch Experiments)

**演算法偽碼:**
```
BATCH_RUN(N, T, E, X):
  FOR exp = 1 TO X:
    SINGLE_RUN(N, T, E)
    SAVE_STATE()
  WRITE_SUMMARY()
```

#### 時間複雜度

```
T_batch(N, T, E, X) = O(X * (N^2 + T(N + E)))
```

> 簡化: **O(X * T * (N + E))** (主導項)

#### 空間複雜度

```
S_batch = O(N + E + T + X)
```

> 每次實驗重用相同記憶體 (`setup()` 會清除)，只累積 `critical_time_list` O(X) 和 `adopter_list` O(T)。

---

### 定義: 帶 GUI 的單次模擬

**演算法偽碼:**
```
GUI_RUN(N, T, E):
  SINGLE_RUN(N, T, E)
  FOR each GUI update (every dt steps):
    UPDATE_PLOTS()                // O(N*D_max + T)
```

假設 GUI 每 dt 步更新一次，共更新 T/dt 次:

```
T_gui = O(N^2 + T(N+E) + (T/dt) * (N*D_max + T))
```

> 在實務中，繪圖的 overhead 遠大於模擬邏輯的數值計算，
> 但 dt 通常會隨模擬加速而增大，使繪圖總次數可控。

---

## 9. 以預設參數代入的具體數值分析

取 N=400, T=300, E~1600(SWN)/~2000(SFN), X=20, D_max~60, U<=100:

| 操作 | 表達式 | 數量級 |
|------|--------|--------|
| SFN 建構 | N^2 = 160,000 | ~10^5 |
| 單步模擬 | N + E ~ 2,400 | ~10^3 |
| 完整模擬 | T(N+E) ~ 720,000 | ~10^6 |
| 批量實驗 | XT(N+E) ~ 14,400,000 | ~10^7 |
| 空間 (單次) | N + E + T ~ 2,700 | ~10^3 |

---

## 10. 各函式複雜度速查表

| 函式 | 行號 | 時間複雜度 | 空間複雜度 |
|------|------|------------|------------|
| `_nl_round(x)` | 145 | O(1) | O(1) |
| `_NodeStateView.__getitem__` | 207 | O(1) | O(1) |
| `_NodeStatesProxy.__getitem__` | 244 | O(1) | O(1) |
| `_NodeStatesProxy.items()` | 256 | O(N) | O(1) [1] |
| `setup()` | 446 | O(N^2) | O(N+E) |
| `_clear()` | 469 | O(1) [2] | - |
| `setup_scale_free_network()` | 522 | O(N^2) | O(N+E) |
| `_find_partner()` | 587 | O(N) | O(1) |
| `_add_link()` | 638 | O(N) amortized | O(1) |
| `_set_pos_xy_of_nodes()` | 690 | O(N) | O(N) |
| `setup_small_world_network()` | 726 | O(N^2) worst; O(pN^2) expected | O(N+E) |
| `setup_agent_population()` | 832 | O(N log N) | O(N) |
| `_chosen_leaders()` | 896 | O(N log N) | O(N) |
| `_build_neighbors_cache()` | 429 | O(N+E) | O(N+E) |
| `go()` | 934 | O(N^2 + T(N+E)) | O(N+E+T) |
| `step()` | 1036 | O(N+E) | O(N) |
| `_step_all_agents()` | 1092 | O(N+E) | O(N) |
| `_communicate()` | 1267 | O(1) | O(1) |
| `_change_opinion_{1,2,3}()` | 1345-1382 | O(1) | O(1) |
| `_make_decision()` | 1387 | O(d(i)) | O(1) |
| `_become_action()` | 1427 | O(1) | O(1) |
| `critical_point` (property) | 1455 | O(N) [3] | O(1) |
| `run_experiments()` | 1495 | O(X(N^2+T(N+E))) | O(N+E+T+X) |
| `save_model_state()` | 1585 | O(N+E+TU) | O(N+E+TU) |
| `load_model_state()` | 1629 | O(TN+E) | O(N+E+TU) |
| `_reconstruct_adoption_history()` | 1698 | O(TN) | O(T) |
| `plot_network()` | 1836 | O(N+E) | O(N+E) |
| `plot_attitude_trajectory()` | 1921 | O(dt*U) incremental | O(1) |
| `plot_adoption_dynamics()` | 1978 | O(T) | O(T) |
| `plot_new_adopter_dynamics()` | 2029 | O(T) | O(T) |
| `plot_attitude_distribution()` | 2074 | O(N) | O(N) |
| `plot_threshold_distribution()` | 2103 | O(N) | O(N) |
| `plot_degree_distribution()` | 2131 | O(N*D_max) SFN; O(N) SWN | O(N) |
| `update_plots()` | 2196 | O(N*D_max + TU) | O(N+E+T) |

**Notes:**
- [1] generator，不建構完整列表
- [2] 只是賦值，NumPy/dict 的舊物件由 GC 回收
- [3] 一旦 critical_time > 0 後短路為 O(1)

---

## 11. 演算法的嚴謹數學定義

### 定義 1: BCAT 模型形式化

**BCAT 模型**是一個五元組 **M = (G, S, Pi, Phi, Psi)**，其中:

- **G = (V, E)** 是無向圖，|V| = N, |E| = E
- **S: V -> [1,100] x [1,100] x {0,1} x (Z union {-1})** 是狀態函數，S(v) = (att_v, theta_v, act_v, time_v)
- **Pi** 是參數集合 {mu (convergence_rate), beta (bounded_confidence), P (pioneers count), T (max_time)}
- **Phi: S x S x Pi -> S x S** 是意見更新函數 (Bounded Confidence Opinion Dynamics)
- **Psi: S x 2^V -> S** 是採納決策函數 (Threshold Adoption)

### 定義 2: 意見更新函數 Phi

給定節點 i 和隨機選取的鄰居 j in N(i)，若 |att_i - att_j| < beta:

```
Phi(S(i), S(j)) = 根據 (act_i, act_j, att_i, att_j) 選取:
  opinion-1 (雙向): att_i' = floor(att_i + mu*(att_j - att_i) + 0.5)
                     att_j' = floor(att_j + mu*(att_i - att_j) + 0.5)
  opinion-2 (僅自身): att_i' = floor(att_i + mu*(att_j - att_i) + 0.5)
  opinion-3 (僅對象): att_j' = floor(att_j + mu*(att_i - att_j) + 0.5)
```

**選擇規則:**
| act_i | act_j | att_j > att_i | Rule |
|-------|-------|---------------|------|
| F | T | T | opinion-2 |
| F | T | F | opinion-1 |
| T | F | T | opinion-1 |
| T | F | F | opinion-3 |
| T | T | T | opinion-2 |
| T | T | F | opinion-3 |
| F | F | * | opinion-1 |

### 定義 3: 採納決策函數 Psi

```
Psi(i, t) = {
  act_i <- 1, time_i <- t   if act_i = 0
                              AND att_i > 50
                              AND |N(i)| > 0
                              AND |{j in N(i) : act_j = 1}| / |N(i)| >= theta_i / 100
  unchanged                  otherwise
}
```

### 定義 4: 模擬迴圈

```
SIMULATE(M, T):
  for t = 0 to T-1:
    pi <- random_permutation(V)
    for each v in pi:
      j <- uniform_random(N(v))
      (S(v), S(j)) <- Phi(S(v), S(j))
      S(v) <- Psi(v, t)
```

**每步時間複雜度:** O(sum_{v in V} (1 + d(v))) = O(N + 2E) = **O(N + E)**

### 定義 5: 臨界點

```
t_critical = min{t : |{v : act_v = 1}| > |{v : act_v = 0}|}, if exists
           = 0, if not exists
```
