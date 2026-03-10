#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BCAT (Bounded Confidence Adoption Threshold) 模擬模型
=====================================================
從 NetLogo 4.0.5 轉換至 Python 3.13

原始 NetLogo 檔案: "English - best game no one played.nlogo"
                  "best game no one played.nlogo" (中文版)

本程式完整對應 NetLogo 4.0.5 的 BCAT 模型，包含：
  1. 核心模擬邏輯 (OpinionAdoptionModel)
  2. 圖形視覺化    (ModelVisualizer) — 6個圖表完全對應 NetLogo 介面
  3. GUI 使用者介面 (ModelGUI)       — Tkinter 互動介面對應 NetLogo 介面

使用的 Python packages:
  - matplotlib 3.10.8  (對應 NetLogo 的 plot 系統)
  - networkx 3.3       (對應 NetLogo 的 turtles/links 網絡系統)
  - numpy 1.26.4       (對應 NetLogo 的數學運算)

NetLogo → Python 轉換對照總覽:
  NetLogo 概念              Python 對應
  ─────────────────────────────────────────────────────────
  globals [...]             類別屬性 (self.xxx)
  turtles-own [...]         NumPy 2D 陣列: self._states[node_id, col]
  turtles                   networkx Graph 的 nodes
  links                     networkx Graph 的 edges
  patches (20x20 grid)      networkx Graph + 位置屬性
  ask-concurrent turtles    for node in nodes (隨機打亂順序)
  create-turtles            G.add_node()
  create-link-with          G.add_edge()
  link-neighbors            list(G.neighbors(node))
  one-of link-neighbors     random.choice(list(G.neighbors(node)))
  set-current-plot          matplotlib axes 切換
  plot / plotxy             ax.plot() / ax.scatter()
  histogram                 ax.hist() / ax.bar()
  slider                    tkinter Scale
  switch                    tkinter Checkbutton
  chooser                   tkinter Combobox
  monitor                   tkinter Label (動態更新)
  button                    tkinter Button

作者說明:
  此模型模擬社交網絡中意見傳播與產品/行為採納的動態過程。
  模型名稱 "叫好不叫座" 意指「好評如潮但無人買單」的現象，
  英文對應 "Best game no one played"。

BCAT 模型核心數學公式 (語言無關):
  ───────────────────────────────
  1. 態度初始化:
       att_i  = clamp(Normal(avg_of_attitudes,  std_of_attitudes),  1, 100)
       theta_i = clamp(Normal(avg_of_thresholds, std_of_thresholds), 1, 100)
     先驅者 (pioneers): att = 100, theta = 0, act = True

  2. 意見更新 (Bounded Confidence):
     每步每個節點 i 隨機選一個鄰居 j，若 |att_i - att_j| < bounded_confidence:
       雙向趨同 (opinion-1):
         att_i' = round(att_i + mu * (att_j - att_i))
         att_j' = round(att_j + mu * (att_i - att_j))
       單向(僅自身, opinion-2):
         att_i' = round(att_i + mu * (att_j - att_i))
       單向(僅對象, opinion-3):
         att_j' = round(att_j + mu * (att_i - att_j))
     其中 mu = convergence_rate, round = round-half-up (非銀行家捨入)
     選用哪種 opinion 規則取決於雙方的採納狀態 (act_i, act_j) 和態度高低 (att 大小)。

  3. 採納決策:
       adopt(i) iff act_i = False
                    AND att_i > 50
                    AND |N(i)| > 0
                    AND (|{j in N(i) : act_j = True}| / |N(i)|) >= theta_i / 100
     其中 N(i) 是節點 i 的鄰居集合。

  4. 臨界點 (Critical Point):
       t_critical = min{ t : |{i : act_i = True}| > |{i : act_i = False}| }
     一旦記錄就不再改變。

資料結構需求 (跨語言移植參考):
  ─────────────────────────────
  Graph G:     無向圖, 400 個節點, 邊數可變
  Per-node:    att   in [1, 100]  (float, 經 opinion update 後取整)
               theta in [1, 100]  (float, 初始化後不再改變)
               act   in {True, False}
               time  in {-1} U N_0  (採納的 tick, -1 表示尚未採納)
  Global:      current_time in N_0
               critical_time in N_0  (0 表示尚未達到臨界)

演算法偽代碼 (跨語言移植參考):
  ──────────────────────────────
  SETUP:
    build_network(400 nodes)   // SFN (preferential attachment) 或 SWN (lattice + rewiring)
    FOR each node i:
      att_i  <- clamp(Normal(mu_att, sigma_att), 1, 100)
      theta_i <- clamp(Normal(mu_theta, sigma_theta), 1, 100)
      act_i  <- False
    FOR each pioneer node p:
      att_p <- 100, theta_p <- 0, act_p <- True, time_p <- 0

  SIMULATION LOOP (for t = 0, 1, ..., max_time - 1):
    nodes_order <- random_permutation(all_nodes)
    FOR each node i in nodes_order:
      j <- random_neighbor(i)
      IF j exists AND |att_i - att_j| < bounded_confidence:
        APPLY opinion_update_rule(i, j)   // 依 act_i, act_j, att 大小選規則
      IF NOT act_i AND att_i > 50 AND |N(i)| > 0:
        IF (count_adopting_neighbors(i) / |N(i)|) >= theta_i / 100:
          act_i <- True, time_i <- t
    t <- t + 1
    UPDATE critical_point

隨機數生成規格 (跨語言移植參考):
  ─────────────────────────────
  - Normal distribution: random_normal(mean, std) — 標準高斯 RNG
  - Uniform integer:     random_int(0, N-1) — 含兩端的均勻整數
  - Uniform float:       random_float(0, 1) — [0, 1) 的均勻浮點數
  - Random permutation:  shuffle(list) — Fisher-Yates 或等價演算法
  - Random choice:       從列表中均勻隨機選取一個元素
  - round():             必須使用 round-half-up (傳統四捨五入),
                         而非 Python 3 預設的 round-half-to-even (銀行家捨入)
"""

import warnings                                                     # 用於抑制字體缺失警告
warnings.filterwarnings("ignore", category=UserWarning,
                        message=".*Glyph.*missing from.*font.*")    # 抑制 CJK 字體缺失警告

import numpy as np                                                  # 對應 NetLogo 內建的數學函數
import networkx as nx                                               # 對應 NetLogo 的 turtles/links 網絡系統
import matplotlib
matplotlib.use('TkAgg')                                             # 使用 TkAgg 後端以支持 Tkinter GUI
import matplotlib.pyplot as plt                                     # 對應 NetLogo 的 plot 繪圖系統
from matplotlib.figure import Figure                                # matplotlib 圖形物件
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg     # matplotlib 嵌入 Tkinter
from matplotlib.backends.backend_agg import FigureCanvasAgg         # 離線渲染 (線程安全)
import matplotlib.colors as mcolors                                 # 顏色處理
import random                                                       # 對應 NetLogo 的 random 系列函數
import os                                                           # 檔案與目錄操作
import time as time_module                                          # 時間控制 (避免與 turtles-own 的 time 衝突)
import tkinter as tk                                                # GUI 框架 (對應 NetLogo 的 Interface tab)
from tkinter import ttk, filedialog, messagebox                     # 進階 GUI 元件
import math                                                         # 數學函數
import threading                                                    # 多線程 (用於非阻塞 GUI 更新)
import pickle                                                       # 序列化 (對應 NetLogo 的 export-world/import-world)


def _nl_round(x):
    """
    NetLogo 4.0.5 相容的四捨五入函數

    NetLogo 的 round 使用傳統四捨五入 (round-half-up):
      round(0.5)  = 1    round(-0.5) = 0
      round(1.5)  = 2    round(-1.5) = -1
      round(2.5)  = 3    round(-2.5) = -2

    Python 3 的 round() 使用銀行家捨入 (round-half-to-even):
      round(0.5)  = 0    round(-0.5) = 0
      round(1.5)  = 2    round(-1.5) = -2
      round(2.5)  = 2    round(-2.5) = -2

    此差異在 change-opinion 函數中會產生不同結果。
    例如: convergence-rate=0.1, B=60, C=45
          C + 0.1*(B-C) = 46.5
          NetLogo: round(46.5) = 47
          Python:  round(46.5) = 46 ← 不同！

    使用 math.floor(x + 0.5) 精確複製 NetLogo 的行為。
    """
    return int(math.floor(x + 0.5))


# =============================================================================
# NetLogo globals [ critical-time critical-time-list adopter-list ]
# → Python: OpinionAdoptionModel 類別的實例屬性
#
# NetLogo turtles-own [ act att theta time object ]
# → Python: self._states NumPy 陣列 (shape: N×4)
#           columns: [att, theta, act, time]
#           其中 'object' 不需要持久儲存，僅在 communicate-and-make-decision 中臨時使用
#
# 效能最佳化: 使用 NumPy 陣列取代巢狀字典，搭配 _NodeStatesProxy 提供相容介面
# =============================================================================


class _NodeStateView:
    """
    單一節點狀態的代理物件，支援 view['att'] 等字典語法。
    直接讀寫底層 NumPy 陣列的對應列。

    設計動機:
      模型核心迴路 (_step_all_agents) 直接操作 NumPy 陣列以獲得最佳效能，
      但外部模組 (ModelVisualizer, save/load, 單步除錯) 仍需要用
      node_states[node_id]['att'] 的字典語法存取節點狀態。
      此代理物件彌合了兩者之間的介面差異，無需複製資料。

    跨語言移植說明:
      此類別是 Python 特有的效能最佳化包裝，其他語言可直接使用
      struct/record/dict 來儲存每個節點的 {att, theta, act, time}。
    """
    __slots__ = ('_arr', '_row')

    # 類別層級的欄位映射 (避免每次查找時重建)
    _KEY_MAP = {'att': 0, 'theta': 1, 'act': 2, 'time': 3}

    def __init__(self, arr, row):
        self._arr = arr
        self._row = row

    def __getitem__(self, key):
        col = self._KEY_MAP[key]
        val = self._arr[self._row, col]
        if col == 2:      # act → 回傳 bool
            return val != 0.0
        elif col == 3:    # time → 回傳 int
            return int(val)
        return val        # att, theta → 回傳 float

    def __setitem__(self, key, value):
        col = self._KEY_MAP[key]
        if col == 2:      # act → 存為 0.0/1.0
            self._arr[self._row, col] = 1.0 if value else 0.0
        else:
            self._arr[self._row, col] = value


class _NodeStatesProxy:
    """
    node_states 的代理物件，讓 node_states[node_id] 回傳 _NodeStateView。
    支援 iteration、len、in 等字典操作，用於 Visualizer 和序列化的向後相容性。

    設計動機:
      原始版本使用 dict[int, dict] 儲存節點狀態 (node_states[node_id]['att'])。
      效能最佳化後改為 NumPy 2D 陣列 (_states[node_id, col])，
      但許多外部程式碼仍依賴舊的 dict 介面。此 Proxy 提供相容的存取方式，
      讓舊介面的使用者不需要修改程式碼，同時底層享受 NumPy 的效能。

    跨語言移植說明:
      此類別是 Python 特有的相容層，其他語言不需要此設計。
      直接使用 array[node_id].att 或 nodes[node_id]["att"] 等原生語法即可。
    """
    __slots__ = ('_arr',)

    def __init__(self, arr):
        self._arr = arr

    def __getitem__(self, node_id):
        return _NodeStateView(self._arr, node_id)

    def __len__(self):
        return self._arr.shape[0]

    def __iter__(self):
        return iter(range(self._arr.shape[0]))

    def __contains__(self, node_id):
        return 0 <= node_id < self._arr.shape[0]

    def items(self):
        """回傳 (node_id, _NodeStateView) 的迭代器"""
        for i in range(self._arr.shape[0]):
            yield i, _NodeStateView(self._arr, i)

    def keys(self):
        return range(self._arr.shape[0])

    def values(self):
        for i in range(self._arr.shape[0]):
            yield _NodeStateView(self._arr, i)

class OpinionAdoptionModel:
    """
    BCAT 意見採納模型核心類別
    ========================
    完整對應 NetLogo 4.0.5 的所有 procedures (程序)。

    NetLogo 程序對照:
      startup                       → __init__() + setup()
      setup                         → setup()
      clear                         → _clear() (內嵌於 setup)
      setup-social-network          → setup_social_network()
      setup-scale-free-network      → setup_scale_free_network()
      setup-small-world-network     → setup_small_world_network()
      make-node                     → (內聯於 setup_scale_free_network)
      find-partner                  → _find_partner()
      add-link                      → _add_link()
      set-posXY-of-nodes            → _set_pos_xy_of_nodes()
      setup-agent-population        → setup_agent_population()
      chosen-leaders                → _chosen_leaders()
      go                            → go()
      communicate-and-make-decision ┐
      communicate                   │
      change-opinion-1/2/3          ├→ (全部內聯於 _step_all_agents)
      make-decision                 │
      become-action                 ┘
      critical-point                → critical_point (property)
      run-100-experiments           → run_experiments()
      import-simulation             → load_model_state()

    效能最佳化 (相對原始版本):
      - 使用 NumPy 陣列取代巢狀字典 (node_states)，減少雜湊查找開銷
      - 鄰居快取 (_neighbors_cache)：網絡建立後預計算所有節點的鄰居列表
      - 批量實驗模式 (run_experiments) 跳過所有 GUI 更新
    """

    # 節點屬性在 NumPy 陣列中的索引常數
    _ATT   = 0    # 態度值 (attitude)
    _THETA = 1    # 採納門檻 (threshold)
    _ACT   = 2    # 採納狀態 (0.0=未採納, 1.0=已採納)
    _TIME  = 3    # 採納時間 (-1=尚未採納)
    _N_FIELDS = 4 # 每個節點的屬性數量

    def __init__(self):
        """
        初始化模型參數和狀態

        NetLogo 對應:
          globals [ critical-time critical-time-list adopter-list ]
          → self.critical_time, self.critical_time_list, self.adopter_list

          turtles-own [ act att theta time object ]
          → self._states NumPy 陣列 (shape: N×4)
            以及相容的 self.node_states 屬性 (property)

          所有 slider/switch/chooser 的預設值
          → self.xxx 各參數屬性
        """
        # ─── NetLogo globals 對應 ───
        self.G                  = None      # 網絡結構 (networkx Graph)
        self.critical_time      = 0         # 臨界時間點
        self.critical_time_list = []        # 多次實驗的臨界時間列表
        self.adopter_list       = []        # 累計採用者數量列表

        # ─── NetLogo slider/switch/chooser 預設值對應 ───
        # 對應 NetLogo 介面上的各個控制元件及其預設值
        #
        # NetLogo SLIDER no-of-pioneers (0~100, 預設 5, 步進 1)
        self.no_of_pioneers       = 5
        #
        # NetLogo SWITCH clustered-pioneers? (預設 ON=true)
        # 注意: NetLogo switch 值 0 表示 ON (true), 1 表示 OFF (false)
        self.clustered_pioneers   = True
        #
        # NetLogo SLIDER bounded-confidence (0~90, 預設 50, 步進 10)
        # 中文版使用 max-opinion-distance (10~90, 預設 50)
        self.bounded_confidence   = 50
        #
        # NetLogo SLIDER convergence-rate (0.1~1.0, 預設 0.1, 步進 0.1)
        self.convergence_rate     = 0.1
        #
        # NetLogo SLIDER avg-of-attitudes (10~100, 預設 50, 步進 10)
        self.avg_of_attitudes     = 50
        #
        # NetLogo SLIDER std-of-attitudes (0~30, 預設 10, 步進 5)
        self.std_of_attitudes     = 10
        #
        # NetLogo SLIDER avg-of-thresholds (10~100, 預設 40, 步進 5)
        self.avg_of_thresholds    = 40
        #
        # NetLogo SLIDER std-of-thresholds (0~30, 預設 10, 步進 5)
        self.std_of_thresholds    = 10
        #
        # NetLogo CHOOSER network-type ("SFN" "SWN/RN/CA", 預設索引 1 = "SWN/RN/CA")
        # 中文版預設索引 0 = "SFN"
        self.network_type         = "SWN/RN/CA"
        #
        # NetLogo SLIDER rewiring-probability (0.00~1.00, 預設 0, 步進 0.05)
        # Python 版調整為 0.1 作為更具展示效果的預設值 (NetLogo 原版預設 0)
        self.rewiring_probability = 0.1
        #
        # NetLogo SLIDER max-time (50~1000, 預設 300, 步進 50)
        # Python 版調整為 100 以加快互動模式的執行速度 (NetLogo 原版預設 300)
        self.max_time             = 100
        #
        # NetLogo SLIDER no-of-experiments (10~1000, 預設 20, 步進 10)
        self.no_of_experiments    = 20

        # ─── 執行時狀態 (非 NetLogo 直接對應，Python 實作所需) ───
        self.current_time = 0               # 對應 NetLogo 的 ticks
        # 效能最佳化: 使用 NumPy 陣列取代巢狀字典
        # _states shape: (N, 4) — 列: [att, theta, act, time]
        self._states = np.empty((0, self._N_FIELDS), dtype=np.float64)
        # 效能最佳化: 鄰居快取 — 建立網絡後預計算
        self._neighbors_cache = {}          # {node_id: [neighbor_id, ...]}
        # 效能最佳化: SFN 建構用的增量度數快取
        self._degree_list = []              # [degree_of_node_0, degree_of_node_1, ...]
        self._total_degree = 0              # sum of all degrees

        # ─── GUI 繪圖用的每步歷史記錄 ───
        # 每步在 step() 中記錄，確保即使 GUI 跳步更新也不遺失任何 tick 的資料
        self._attitude_snapshots = {}       # {tick: {att_value: count, ...}}
        self._new_adopters_per_tick = []    # [tick0_count, tick1_count, ...]
        self._adopters_per_tick = []        # [tick0_count, tick1_count, ...]
        self._non_adopters_per_tick = []    # [tick0_count, tick1_count, ...]

        # 供外部回調使用 (GUI 進度更新等)
        self._step_callback = None

    # ─── 相容性屬性: node_states ───
    # 讓舊的 dict 存取方式仍可運作 (用於 visualizer / save / load)
    @property
    def node_states(self):
        """
        提供與原始 dict 介面相容的存取方式。
        回傳一個輕量代理物件，支援 node_states[node]['att'] 等語法。
        注意: 這只用於向後相容，核心模擬迴路直接操作 self._states。
        """
        return _NodeStatesProxy(self._states)

    @node_states.setter
    def node_states(self, value):
        """
        支援 self.node_states = dict 的賦值語法 (在 load_model_state 中用於
        將舊格式的 dict 資料轉換為 NumPy 陣列)
        """
        if isinstance(value, dict):
            if len(value) == 0:
                self._states = np.empty((0, self._N_FIELDS), dtype=np.float64)
            else:
                # 從 dict 轉換 (用於 load_model_state 的相容性)
                n = max(value.keys()) + 1
                self._states = np.empty((n, self._N_FIELDS), dtype=np.float64)
                for node_id, state in value.items():
                    self._states[node_id, self._ATT]   = state['att']
                    self._states[node_id, self._THETA] = state['theta']
                    self._states[node_id, self._ACT]   = 1.0 if state['act'] else 0.0
                    self._states[node_id, self._TIME]  = state['time']

    def _build_neighbors_cache(self):
        """
        建立鄰居快取 — 在網絡建立後呼叫一次

        效能最佳化:
          原始版本在每次交流與決策中都呼叫 list(self.G.neighbors(node))，
          共計 400×300×2=240,000 次列表建構。
          預計算並快取後，改為簡單的字典查找。

        """
        self._neighbors_cache = {
            n: list(self.G.neighbors(n)) for n in self.G.nodes()
        }

    # =========================================================================
    # NetLogo: to startup / setup
    # =========================================================================
    def setup(self):
        """
        初始化模型，設置網絡和智能體群體

        NetLogo 對應:
          to startup
             setup
          end

          to setup
             clear
             set critical-time 0
             setup-social-network
             setup-agent-population
          end
        """
        self._clear()
        self.critical_time = 0
        self.setup_social_network()
        # 效能最佳化: 網絡建立後立即快取鄰居列表
        self._build_neighbors_cache()
        self.setup_agent_population()

    def _clear(self):
        """
        清除所有狀態，為新一輪模擬做準備

        NetLogo 對應:
          to clear
             reset-ticks          → self.current_time = 0
             clear-turtles        → self.G = None; self._states = empty
             clear-patches        → (patches 在 Python 中不需要獨立清除)
             clear-drawing         → (繪圖由 matplotlib 管理)
             clear-all-plots      → (由 visualizer 處理)
             clear-output         → (由 GUI 處理)
             random-seed new-seed → random 模組自動使用系統熵
          end
        """
        self.current_time = 0
        self.G = None
        self._states = np.empty((0, self._N_FIELDS), dtype=np.float64)
        self._neighbors_cache = {}
        self._degree_list = []
        self._total_degree = 0
        self._attitude_snapshots = {}
        self._new_adopters_per_tick = []
        self._adopters_per_tick = []
        self._non_adopters_per_tick = []

    # =========================================================================
    # NetLogo: to setup-social-network
    # =========================================================================
    def setup_social_network(self):
        """
        建立社交網絡結構

        NetLogo 對應:
          to setup-social-network
             no-display                              → (Python 中不需要)
             set-default-shape turtles "circle"      → (視覺化由 matplotlib 處理)
             ifelse (network-type = "SFN")
                [ setup-scale-free-network ]
                [ setup-small-world-network ]
             ask-concurrent links [ set color gray - 3 ] → (邊的顏色在繪圖時設定)
             display                                     → (Python 中不需要)
             plot-network-degree-distribution            → (由 visualizer 處理)
          end
        """
        if self.network_type == "SFN":
            self.setup_scale_free_network()
        else:
            self.setup_small_world_network()

    # =========================================================================
    # NetLogo: to setup-scale-free-network
    # =========================================================================
    def setup_scale_free_network(self):
        """
        建立無尺度網絡 (Scale-Free Network, SFN)
        使用優先附著 (Preferential Attachment) 機制

        NetLogo 對應:
          to setup-scale-free-network
             make-node nobody          → 建立第一個孤立節點 (node 0)
             make-node turtle 0        → 建立第二個節點 (node 1)，連接到 node 0
             repeat 398 [ make-node find-partner ]
                                       → 建立 398 個節點 (nodes 2~399)，
                                         每個用 find-partner 選擇一個已有節點連接
             add-link 0                → 為 node 0 再加一條邊
             foreach shuffle n-values 400 [ ? ] [ repeat 3 [ add-link ? ] ]
                                       → 對所有 400 個節點隨機排列，
                                         每個節點再用 add-link 增加 3 條邊
             set-posXY-of-nodes        → 設定節點位置為 20x20 網格
          end

        Python 實作說明:
          - networkx Graph 替代 NetLogo 的 turtles + links
          - 節點以整數 0~399 標識，對應 NetLogo 的 turtle 0 ~ turtle 399
          - 總共 400 個節點 (NetLogo: create-turtles 1 執行 400 次)
        """
        self.G = nx.Graph()

        # 效能最佳化: 增量維護度數陣列，避免 _find_partner 每次重查 G.degree
        self._degree_list = [0] * 400
        self._total_degree = 0

        # ─── make-node nobody → 建立第一個孤立節點 ───
        self.G.add_node(0)

        # ─── make-node turtle 0 → 建立 node 1 並連接到 node 0 ───
        self.G.add_node(1)
        self.G.add_edge(1, 0)
        self._degree_list[0] = 1
        self._degree_list[1] = 1
        self._total_degree = 2

        # ─── repeat 398 [ make-node find-partner ] ───
        # 逐步新增 398 個節點 (node 2 ~ node 399)
        # 每個新節點用 find-partner (優先附著) 選擇一個已有節點建立連接
        for i in range(2, 400):
            partner = self._find_partner()
            self.G.add_node(i)
            self.G.add_edge(i, partner)
            self._degree_list[i] += 1
            self._degree_list[partner] += 1
            self._total_degree += 2

        # ─── add-link 0 → 為 node 0 追加一條邊 ───
        self._add_link(0)

        # ─── foreach shuffle n-values 400 [ ? ] [ repeat 3 [ add-link ? ] ] ───
        # 將 0~399 隨機打亂，對每個節點追加 3 條邊以增加網絡密度
        node_order = list(range(400))
        random.shuffle(node_order)
        for node_id in node_order:
            for _ in range(3):
                self._add_link(node_id)

        # ─── set-posXY-of-nodes → 設定網格位置 ───
        self._set_pos_xy_of_nodes()

    def _find_partner(self):
        """
        基於優先附著選擇合作夥伴節點

        NetLogo 對應:
          to-report find-partner
             let total random sum [ count link-neighbors ] of turtles
                          → total = random(0, sum_of_all_degrees - 1)
             let partner nobody
             ask turtles [
                 let nc count link-neighbors
                 if (partner = nobody) [
                     ifelse (nc > total)
                         [ set partner self ]
                         [ set total total - nc ]
                 ]
             ]
             report partner
          end

        Python 實作說明:
          NetLogo 的 ask turtles 按照 turtle 的 who 號碼順序遍歷。
          此函數實現累積度分佈的輪盤賭選擇 (roulette wheel selection):
          - 計算所有節點度的總和
          - 隨機產生 0 ~ (總和-1) 的隨機數作為閾值
          - 依序累加每個節點的度，當累加值超過閾值時選中該節點
          這使得高度數的節點更容易被選中 (優先附著原則)
        """
        # 效能最佳化: 使用增量維護的 _degree_list 和 _total_degree
        # 避免每次呼叫都重新建構 list(G.nodes()) 和 [G.degree(n) for n in nodes]
        degrees = self._degree_list
        total_degree = self._total_degree
        n_nodes = self.G.number_of_nodes()

        if total_degree == 0:
            return random.randrange(n_nodes)

        # NetLogo: let total random sum [count link-neighbors] of turtles
        # random N 在 NetLogo 中回傳 0 ~ N-1 的隨機整數
        threshold = random.randint(0, total_degree - 1)

        # NetLogo: ask turtles [ ... ifelse (nc > total) [...] [...] ]
        # 依序檢查每個節點，累減度數直到變成負數
        for node in range(n_nodes):
            nc = degrees[node]
            if nc > threshold:
                return node
            threshold -= nc

        return n_nodes - 1

    def _add_link(self, source_node):
        """
        為指定節點添加一條新邊 (避免自環和重複邊)

        NetLogo 對應:
          to add-link [ self-no ]
             let pass false
             while [ pass = false ] [
                   let partner find-partner
                   while [ partner = turtle self-no ] [ set partner find-partner ]
                   ask turtle self-no [
                       if (not link-neighbor? partner) [
                          create-link-with partner
                          set pass true
                       ]
                   ]
             ]
          end

        Python 實作說明:
          - 與 NetLogo 相同，持續嘗試直到找到有效的合作夥伴 (非自身且尚未連接)
          - NetLogo 的 while [pass = false] 是無限迴圈
          - Python 加入安全上限 (節點數) 防止極端情況下的無限迴圈
            (當節點已連接到所有其他節點時)
        """
        # 安全上限 = 節點總數 N
        # 理由: 每個節點最多只能連接 N-1 個其他節點，因此 find-partner 最多
        # 只有 N-1 種不同結果。嘗試 N 次足以覆蓋所有可能的配對。
        # 若超過 N 次仍找不到，表示該節點已連接到所有其他節點，無需再加邊。
        # 在 SFN 400 節點的正常情況下不會觸發 (每個節點最終約有 7~10 條邊)。
        max_attempts = self.G.number_of_nodes()
        passed = False
        attempts = 0
        while not passed and attempts < max_attempts:
            attempts += 1
            # let partner find-partner
            partner = self._find_partner()

            # while [ partner = turtle self-no ] [ set partner find-partner ]
            while partner == source_node:
                partner = self._find_partner()

            # if (not link-neighbor? partner) [ create-link-with partner; set pass true ]
            if not self.G.has_edge(source_node, partner):
                self.G.add_edge(source_node, partner)
                # 效能最佳化: 增量更新度數快取
                if self._degree_list:
                    self._degree_list[source_node] += 1
                    self._degree_list[partner] += 1
                    self._total_degree += 2
                passed = True

    def _set_pos_xy_of_nodes(self):
        """
        為節點設定 20x20 網格佈局位置

        NetLogo 對應:
          to set-posXY-of-nodes
             let nowx 0
             let nowy 0
             ask turtles [
                 setxy nowx nowy
                 set nowx nowx + 1
                 set nowy nowy + int(nowx / world-width)
                 set nowx nowx mod world-width
             ]
          end

        Python 實作說明:
          NetLogo 的 world-width 為 20 (從 GRAPHICS-WINDOW 設定: 0~19)
          - 節點按照 who 號碼順序排列在 20x20 的網格上
          - node 0 → (0,0), node 1 → (1,0), ..., node 19 → (19,0),
            node 20 → (0,1), ...
        """
        world_width = 20  # 對應 NetLogo GRAPHICS-WINDOW 的 max-pxcor - min-pxcor + 1 = 20
        pos = {}
        nowx = 0
        nowy = 0
        for node in sorted(self.G.nodes()):
            pos[node] = (nowx, nowy)
            nowx += 1
            nowy += nowx // world_width  # int(nowx / world-width)
            nowx = nowx % world_width    # nowx mod world-width
        nx.set_node_attributes(self.G, pos, 'pos')

    # =========================================================================
    # NetLogo: to setup-small-world-network
    # =========================================================================
    def setup_small_world_network(self):
        """
        建立小世界網絡 (Small-World Network, SWN)
        基於 20x20 的二維格子 (lattice) + Watts-Strogatz 重連機制

        NetLogo 對應:
          to setup-small-world-network
             ask-concurrent patches [ sprout 1 [ set size 0.3 ] ]
                → 在每個 patch 上產生一個 turtle (20x20=400 個)
             ask-concurrent turtles [ create-links-with turtles-on neighbors ]
                → 每個 turtle 與其 Moore 鄰居 (8方向) 上的 turtles 建立連接
             ask-concurrent links [
                 let rewired? false
                 if (random-float 1) < rewiring-probability [
                    let node1 end1
                    ask node1 [
                        if ([ count link-neighbors ] of node1 < (count turtles - 1)) [
                           create-link-with one-of turtles with
                               [ (self != node1) and (not link-neighbor? node1) ]
                               [ set rewired? true ]
                        ]
                    ]
                    if (rewired?) [ die ]    → 移除被重連的原始邊
                 ]
             ]
          end

        Python 實作說明:
          1. 建立 20x20=400 個節點
          2. 連接 Moore 鄰居 (8鄰域，使用環形邊界 wrapping)
          3. 以 rewiring-probability 機率重連每條邊:
             - 選擇邊的 end1 節點
             - 為其找一個新的、尚未連接的目標節點
             - 若成功重連，移除原邊、加新邊

        注意: NetLogo patches 使用環形邊界 (wrapping)，
              即 (0,0) 的左鄰居是 (19,0)，上鄰居是 (0,19)
        """
        width, height = 20, 20
        total_nodes = width * height

        self.G = nx.Graph()

        # ─── ask-concurrent patches [ sprout 1 [...] ] ───
        # 在每個 patch 上產生一個 turtle
        for i in range(total_nodes):
            self.G.add_node(i)

        # ─── ask-concurrent turtles [ create-links-with turtles-on neighbors ] ───
        # 連接 Moore 鄰居 (8方向，環形邊界)
        # NetLogo 的 neighbors 回傳 8 個方向的 patches
        for y in range(height):
            for x in range(width):
                node_id = y * width + x
                # 8 個 Moore 鄰居方向
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        if dx == 0 and dy == 0:
                            continue  # 排除自身
                        # 環形邊界 (wrapping)
                        nx_ = (x + dx) % width
                        ny_ = (y + dy) % height
                        neighbor_id = ny_ * width + nx_
                        if not self.G.has_edge(node_id, neighbor_id):
                            self.G.add_edge(node_id, neighbor_id)

        # ─── ask-concurrent links [ ... rewiring ... ] ───
        # Watts-Strogatz 重連機制
        # 注意: NetLogo 在 ask-concurrent links 中遍歷所有邊
        # 每條邊以 rewiring-probability 的機率被重連
        edges_to_process = list(self.G.edges())
        for u, v in edges_to_process:
            if random.random() < self.rewiring_probability:
                # let node1 end1 → 取邊的第一個端點
                node1 = u

                # if ([ count link-neighbors ] of node1 < (count turtles - 1))
                if self.G.degree(node1) < (total_nodes - 1):
                    # one-of turtles with [ (self != node1) and (not link-neighbor? node1) ]
                    non_neighbors = [
                        n for n in self.G.nodes()
                        if n != node1 and not self.G.has_edge(node1, n)
                    ]
                    if non_neighbors:
                        new_target = random.choice(non_neighbors)
                        # create-link-with ... [set rewired? true]
                        self.G.add_edge(node1, new_target)
                        # if (rewired?) [ die ] → 移除原始邊
                        # 必須先檢查 has_edge(u, v):
                        # 因為 edges_to_process 是在遍歷前快照的邊集合，
                        # 先前迭代的重連操作可能已將 (u, v) 作為「新邊」的
                        # 一端而間接刪除或覆蓋，所以需要確認邊仍存在才移除。
                        if self.G.has_edge(u, v):
                            self.G.remove_edge(u, v)

        # 設定節點位置為 20x20 網格
        pos = {}
        for y in range(height):
            for x in range(width):
                node_id = y * width + x
                pos[node_id] = (x, y)
        nx.set_node_attributes(self.G, pos, 'pos')

    # =========================================================================
    # NetLogo: to setup-agent-population
    # =========================================================================
    def setup_agent_population(self):
        """
        初始化智能體群體的態度和門檻值

        NetLogo 對應 (英文版):
          to setup-agent-population
             ask-concurrent turtles [
                 set att   max list 1 (min list 100 random-normal avg-of-attitudes  std-of-attitudes)
                 set theta max list 1 (min list 100 random-normal avg-of-thresholds std-of-thresholds)
                 become-susceptible
             ]
             ask-concurrent chosen-leaders [
                 set att   100
                 set theta   0
                 become-action
             ]
             plot-theta-distribution
             plot-att-distribution
          end

        中文版差異:
          set att   round(abs(random-normal avg-of-attitudes  std-of-attitudes))  mod 100 + 1
          set theta round(abs(random-normal avg-of-thresholds std-of-thresholds)) mod 100 + 1
          → 使用 abs + mod 而非 clamp，結果略有不同

        Python 實作說明:
          - 使用英文版的 clamp 方式: max(1, min(100, normal()))
          - numpy.random.normal 對應 NetLogo 的 random-normal
          - round() 對應 NetLogo 的隱式取整（NetLogo att 為數值型，此處為 int）

        效能最佳化:
          - 使用 NumPy 向量化生成 att/theta 陣列
          - self._states shape: (N, 4) — 列: [att, theta, act, time]
        """
        n_nodes = self.G.number_of_nodes()

        # ─── 使用 NumPy 向量化生成 att 和 theta ───
        # set att max list 1 (min list 100 random-normal ...)
        att_arr = np.clip(
            np.random.normal(self.avg_of_attitudes, self.std_of_attitudes, n_nodes),
            1.0, 100.0
        )

        # set theta max list 1 (min list 100 random-normal ...)
        theta_arr = np.clip(
            np.random.normal(self.avg_of_thresholds, self.std_of_thresholds, n_nodes),
            1.0, 100.0
        )

        # ─── 建立 _states 陣列: [att, theta, act, time] ───
        self._states = np.empty((n_nodes, self._N_FIELDS), dtype=np.float64)
        self._states[:, self._ATT]   = att_arr       # 態度值 (1~100)
        self._states[:, self._THETA] = theta_arr     # 採納門檻 (1~100)
        self._states[:, self._ACT]   = 0.0           # become-susceptible → False
        self._states[:, self._TIME]  = -1.0          # 尚未採納

        # ─── ask-concurrent chosen-leaders [ set att 100; set theta 0; become-action ] ───
        pioneers = self._chosen_leaders()
        for node in pioneers:
            self._states[node, self._ATT]   = 100.0
            self._states[node, self._THETA] = 0.0
            self._states[node, self._ACT]   = 1.0    # become-action
            self._states[node, self._TIME]  = 0.0    # 在 ticks=0 時採納

    def _chosen_leaders(self):
        """
        選擇先驅者 (pioneers)

        NetLogo 對應:
          to-report chosen-leaders
             report ifelse-value (clustered-pioneers? = true)
                 [ max-n-of no-of-pioneers turtles [ xcor + ycor ] ]
                 [ n-of no-of-pioneers turtles ]
          end

        Python 實作說明:
          - clustered-pioneers? = true:
              選擇 xcor + ycor 最大的 N 個節點 (即位於網格右上角的節點)
              → 這些節點在空間上是聚集的
          - clustered-pioneers? = false:
              隨機選擇 N 個節點
        """
        n = min(self.no_of_pioneers, len(self.G.nodes()))
        if n == 0:
            return []

        if self.clustered_pioneers:
            # max-n-of no-of-pioneers turtles [ xcor + ycor ]
            pos = nx.get_node_attributes(self.G, 'pos')
            nodes_sorted = sorted(
                self.G.nodes(),
                key=lambda nd: pos[nd][0] + pos[nd][1],
                reverse=True
            )
            return nodes_sorted[:n]
        else:
            # n-of no-of-pioneers turtles → 隨機選擇
            return random.sample(list(self.G.nodes()), n)

    # =========================================================================
    # NetLogo: to go [ exp-ID ]
    # =========================================================================
    def go(self, exp_id=0):
        """
        執行一次完整的模擬

        NetLogo 對應:
          to go [ exp-ID ]
             setup
             while [ ticks < max-time ] [
                   ask-concurrent turtles [ communicate-and-make-decision ]
                   update-plot
                   if (exp-ID > 0) [
                      file-print (word exp-ID ":" ticks ":act:" ...)
                   ]
                   if (exp-ID > 0) [
                      set adopter-list replace-item ticks adopter-list (...)
                   ]
                   tick
             ]
             if (exp-ID > 0) [
                file-print (word "critical-point:" critical-time)
                set critical-time-list lput critical-time critical-time-list
             ]
          end

        Python 實作說明:
          - exp_id=0 表示互動模式 (Run once 按鈕)，不寫入檔案
          - exp_id>0 表示批量實驗模式，記錄數據
          - 每個 tick 的步驟:
            1. 所有節點執行 communicate-and-make-decision
            2. 更新繪圖 (由 _step_callback 處理)
            3. 記錄數據 (若 exp_id > 0)
            4. tick 計數器 +1

        go() vs step() 的差異:
          go()  用於批量實驗 (run_experiments 呼叫)，不記錄 GUI 繪圖用的
                歷史資料 (_attitude_snapshots, _adopters_per_tick 等)，
                以最大化批量執行效能。統計數據透過 results 列表回傳。
          step() 用於 GUI 互動模式 (Run Once / Run 按鈕)，每步記錄完整的
                歷史資料供 ModelVisualizer 增量繪圖使用，即使 GUI 每 N 步
                才更新一次也不會遺失中間步的資料。

        效能最佳化:
          - 使用 NumPy 向量化統計 (np.sum / np.mean / np.std)
          - 快取 _states 和 column 的本地引用
        """
        self.setup()
        results = []

        # 效能最佳化: 本地引用，避免每次迭代的屬性查找
        states = self._states
        ATT = self._ATT
        ACT = self._ACT
        max_time = self.max_time
        n_total = states.shape[0]

        while self.current_time < max_time:
            # ─── ask-concurrent turtles [ communicate-and-make-decision ] ───
            self._step_all_agents()

            # 效能最佳化: 使用 NumPy 向量化統計
            act_col = states[:, ACT]
            adopters = int(np.sum(act_col))
            non_adopters = n_total - adopters
            att_col = states[:, ATT]
            mean_att = float(np.mean(att_col))
            std_att  = float(np.std(att_col, ddof=1)) if n_total > 1 else 0.0
            results.append((adopters, non_adopters, mean_att, std_att))

            # ─── 記錄態度快照 (供 Attitude Trajectory 圖和 save/load 重播) ───
            # 與 step() 中相同的邏輯，在 current_time += 1 之前記錄
            snapshot = {}
            for v in att_col:
                iv = int(v)
                if iv == v:
                    snapshot[iv] = snapshot.get(iv, 0) + 1
            self._attitude_snapshots[self.current_time] = snapshot

            # 記錄數據 (exp_id > 0 時)
            if exp_id > 0 and self.current_time < len(self.adopter_list):
                self.adopter_list[self.current_time] += (
                    adopters * (1.0 / self.no_of_experiments)
                )

            # ─── tick ───
            self.current_time += 1

            # ─── 計算 critical-point ───
            # 修正: 必須在 current_time += 1 之後呼叫。
            # NetLogo 的 critical-point 由 monitor widget 在 tick 命令之後觸發，
            # 此時 ticks 已遞增。set critical-time ticks 記錄的是後增值。
            _ = self.critical_point

            # 外部回調 (用於 GUI 更新)
            if self._step_callback:
                self._step_callback()

        # 記錄臨界時間 (exp_id > 0 時)
        if exp_id > 0:
            self.critical_time_list.append(self.critical_time)

        return results

    def step(self):
        """
        執行單一時間步 (供 GUI 的 "Run Once" 按鈕使用)

        對應 NetLogo "Run once" 按鈕執行的動作:
          ask-concurrent turtles [ communicate-and-make-decision ]
          update-plot
          tick
        """
        self._step_all_agents()

        # 效能最佳化: NumPy 向量化統計
        adopters = int(np.sum(self._states[:, self._ACT]))
        non_adopters = self._states.shape[0] - adopters

        # ─── 記錄每步歷史供 GUI 繪圖使用 ───
        # 在 current_time += 1 之前記錄，確保 TIME 欄位匹配
        #
        # 採用者/非採用者數量 (供 Adoption Dynamics 圖)
        self._adopters_per_tick.append(adopters)
        self._non_adopters_per_tick.append(non_adopters)

        # 態度快照 (供 Attitude Trajectory 圖)
        # NetLogo 的 update-plot 遍歷整數 attitude 1..100:
        #   while [ attitude <= 100 ] [
        #       let no count turtles with [ att = attitude ]
        # 因此快照以整數 att 值為 key，對應 NetLogo 的精確整數匹配。
        # 注意: 未被 round() 取整的浮點 att (如 47.3) 在 NetLogo 中
        # 不會匹配任何整數 attitude，所以不會被繪製。
        att_col = self._states[:, self._ATT]
        snapshot = {}
        for v in att_col:
            int_v = int(v)
            if int_v == v:  # 只計入精確整數值 (對應 NetLogo att = attitude)
                snapshot[int_v] = snapshot.get(int_v, 0) + 1
        self._attitude_snapshots[self.current_time] = snapshot

        # 新採用者數量 (供 New Adopter Dynamics 圖)
        # count turtles with [ act and time = ticks ]
        new_adopters = int(np.sum(
            (self._states[:, self._ACT] != 0.0) &
            (self._states[:, self._TIME] == self.current_time)
        ))
        self._new_adopters_per_tick.append(new_adopters)

        # ─── tick ───
        self.current_time += 1

        # ─── 計算 critical-point ───
        # 修正: 必須在 current_time += 1 之後呼叫。
        # NetLogo 的 critical-point 由 monitor widget 在 tick 命令之後觸發，
        # 此時 ticks 已遞增。set critical-time ticks 記錄的是後增值。
        _ = self.critical_point

        return adopters, non_adopters

    def _step_all_agents(self):
        """
        所有智能體執行一輪交流與決策

        NetLogo 對應:
          ask-concurrent turtles [ communicate-and-make-decision ]

        Python 實作說明:
          NetLogo 4.0.5 的 ask-concurrent 雖名為「同時」，實際上仍以
          隨機順序逐一執行，每個 turtle 的修改立即生效。
          Python 版本忠實重現此行為：隨機打亂節點順序，逐一執行交流與決策。

        效能最佳化:
          - 使用 NumPy arange + shuffle 取代 list + shuffle
          - 本地引用快取和狀態陣列
          - _nl_round 內聯為 int(v + 0.5) (att 值恆正，二者等價)
          - 預生成隨機浮點數取代逐次 random.choice
          - abs(C-B) 改用鏈式比較 -bc < diff < bc (避免函數呼叫)
          - len(neighbors) 快取為 n_nb (避免重複呼叫)
        """
        n_nodes = self._states.shape[0]
        nodes = np.arange(n_nodes)
        np.random.shuffle(nodes)

        # 效能最佳化: 本地引用避免重複屬性查找
        states = self._states
        neighbors_cache = self._neighbors_cache
        ATT = self._ATT
        ACT = self._ACT
        THETA = self._THETA
        TIME = self._TIME
        bc = self.bounded_confidence
        cr = self.convergence_rate
        current_time = self.current_time

        # 效能最佳化: 一次性預生成 400 個隨機浮點數 [0, 1)
        # 取代 400 次 random.choice() 呼叫 (每次經 _randbelow_with_getrandbits)
        rand_vals = np.random.random(n_nodes)
        _int = int  # 本地引用加速

        neg_bc = -bc  # 效能最佳化: 預計算負值供鏈式比較使用

        for node_idx in range(n_nodes):
            node = nodes[node_idx]
            # ─── 內聯 _communicate_and_make_decision ───
            # 效能最佳化: 避免函數呼叫開銷 (400 次/step × 300 steps = 120,000 次)
            neighbors = neighbors_cache[node]
            n_nb = len(neighbors)
            if n_nb == 0:
                # 無鄰居 → 跳過此節點 (幾乎不會到這裡，SFN/SWN 所有節點都有鄰居)
                # NetLogo 原版會呼叫 make-decision，但其條件包含
                # count link-neighbors != 0，無鄰居節點必然不通過，
                # 直接 continue 是等價的最佳化。
                continue

            # ─── set object one-of link-neighbors ───
            # 效能最佳化: int(random_float * len) 等價於 random.choice
            obj = neighbors[_int(rand_vals[node_idx] * n_nb)]

            # ─── communicate ───
            # 規則語義詳見檔案標頭的「BCAT 模型核心數學公式」及「演算法偽代碼」
            # 直接存取 NumPy 陣列而非透過 dict
            A1 = states[obj,  ACT]   # 對象的 act
            A2 = states[node, ACT]   # 自身的 act
            B  = states[obj,  ATT]   # 對象的 att
            C  = states[node, ATT]   # 自身的 att

            # 前提條件: abs(C - B) < bounded-confidence
            # 效能最佳化: 鏈式比較取代 abs() 函數呼叫
            diff = C - B
            if neg_bc < diff < bc:
                obj_adopted  = (A1 != 0.0)
                self_adopted = (A2 != 0.0)

                # 效能最佳化: _nl_round(v) 內聯為 int(v + 0.5)
                # 在 att 值恆正 (clamp [1, 100]) 的前提下，
                # int(x + 0.5) 與 int(math.floor(x + 0.5)) 完全等價。

                if obj_adopted and not self_adopted:
                    # 對象已採用，自身未採用
                    if B > C:
                        # change-opinion-2: 自身態度靠近對象
                        states[node, ATT] = _int(C + cr * (B - C) + 0.5)
                    else:
                        # change-opinion-1: 雙向靠近
                        states[node, ATT] = _int(C + cr * (B - C) + 0.5)
                        states[obj,  ATT] = _int(B + cr * (C - B) + 0.5)

                elif not obj_adopted and self_adopted:
                    # 自身已採用，對象未採用
                    if B > C:
                        # change-opinion-1: 雙向靠近
                        states[node, ATT] = _int(C + cr * (B - C) + 0.5)
                        states[obj,  ATT] = _int(B + cr * (C - B) + 0.5)
                    else:
                        # change-opinion-3: 對象態度靠近自身
                        states[obj, ATT] = _int(B + cr * (C - B) + 0.5)

                elif obj_adopted and self_adopted:
                    # 雙方都已採用
                    if B > C:
                        # change-opinion-2: 自身向對象靠近
                        states[node, ATT] = _int(C + cr * (B - C) + 0.5)
                    else:
                        # change-opinion-3: 對象向自身靠近
                        states[obj, ATT] = _int(B + cr * (C - B) + 0.5)

                elif not obj_adopted and not self_adopted:
                    # 雙方都未採用 → change-opinion-1: 雙向靠近
                    states[node, ATT] = _int(C + cr * (B - C) + 0.5)
                    states[obj,  ATT] = _int(B + cr * (C - B) + 0.5)

            # ─── make-decision ───
            # 內聯以避免函數呼叫開銷
            #
            # 採納決策語義 (跨語言移植參考):
            #   theta (門檻值, 1~100) 除以 100 轉為比例 (0.01~1.00)。
            #   意義: 當「鄰居中已採用者的比例」>= 「個人門檻比例」時，決定採納。
            #   例如: theta=40 代表 40% 以上鄰居已採用時，此節點才會採用。
            #   同時必須滿足 att > 50 (態度正面)。
            #   這體現了「叫好不叫座」的核心:
            #   即使態度正面 (att 高)，若社交壓力不足 (鄰居採用比例低)，仍不會採納。
            if states[node, ACT] == 0.0:     # act = false (尚未採用)
                if states[node, ATT] > 50:   # att > 50 (態度正面)
                    # count link-neighbors with [ act = true ] / count link-neighbors
                    # n_nb 已在迴圈開頭快取，且已確認 > 0
                    if n_nb > 0:
                        adopter_count = 0
                        for nb in neighbors:
                            if states[nb, ACT] != 0.0:
                                adopter_count += 1
                        adopter_ratio = adopter_count / n_nb
                        # 鄰居採用比例 >= 個人門檻比例 → 採納
                        if adopter_ratio >= states[node, THETA] / 100.0:
                            # become-action
                            states[node, ACT]  = 1.0
                            states[node, TIME] = current_time

    # =========================================================================
    # NetLogo: to-report critical-point
    # =========================================================================
    @property
    def critical_point(self):
        """
        計算並回報臨界點 (採用者首次超過非採用者的時間)

        NetLogo 對應:
          to-report critical-point
             ifelse (critical-time > 0)
                 [ report critical-time ]
                 [ ifelse (count turtles with [ act ] > count turtles with [ not act ])
                       [ set critical-time ticks ]
                       [ set critical-time 0 ]
                   report critical-time
                 ]
          end

        說明:
          - 一旦設定 critical-time > 0，就不再改變 (只記錄第一次超過的時間)
          - 若採用者 > 非採用者，設定 critical-time = 當前 ticks
        """
        if self.critical_time > 0:
            return self.critical_time

        # 效能最佳化: NumPy 向量化統計
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

    # =========================================================================
    # NetLogo: to run-100-experiments
    # =========================================================================
    def run_experiments(self, output_dir, progress_callback=None):
        """
        執行多次實驗並保存結果

        NetLogo 對應:
          to run-100-experiments
             let world-directory user-directory
             if (world-directory != false) [
                set-current-directory world-directory
                set critical-time-list []
                set adopter-list []
                repeat max-time [ set adopter-list lput 0 adopter-list ]
                let exp-no 1
                while [ exp-no <= no-of-experiments ] [
                      print (word "exp: " exp-no)
                      file-open (word "experiment-" exp-no ".txt")
                      go exp-no
                      file-close
                      export-interface (word "experiment-" exp-no "-interface.png")
                      export-world (word "experiment-" exp-no "-world")
                      set exp-no exp-no + 1
                ]
                ...
                file-open "experiment.txt"
                file-print (word "critical-points:" critical-time-list)
                file-print (word "adopters:"        adopter-list)
                file-close
             ]
          end

        Python 實作:
          - output_dir 對應 NetLogo 的 user-directory
          - progress_callback 用於 GUI 進度更新
          - 保存格式與 NetLogo 相同
        """
        os.makedirs(output_dir, exist_ok=True)

        # ─── set critical-time-list [] ───
        self.critical_time_list = []

        # ─── set adopter-list []; repeat max-time [ set adopter-list lput 0 adopter-list ] ───
        self.adopter_list = [0.0] * self.max_time

        for exp_no in range(1, self.no_of_experiments + 1):
            print(f"exp: {exp_no}")

            # ─── file-open (word "experiment-" exp-no ".txt") ───
            exp_filename = os.path.join(output_dir, f"experiment-{exp_no}.txt")

            # ─── go exp-no ───
            results = self.go(exp_id=exp_no)

            # ─── file-close ───
            # 寫入實驗數據
            # 對應 NetLogo: file-print (word exp-ID ":" ticks ":act:" ... ":att:" mean ... ":" standard-deviation ...)
            # NetLogo 的 word 會用預設精度輸出浮點數 (無尾端零)，Python 用 repr 對應
            with open(exp_filename, 'w') as f:
                for t, (adopters, non_adopters, mean_att, std_att) in enumerate(results):
                    # repr(float) 輸出最短且能唯一識別該浮點數的表示法，
                    # 行為與 NetLogo 的 word 對浮點數的轉換一致 (無尾端零、無固定小數位)
                    mean_str = repr(mean_att)
                    std_str  = repr(std_att)
                    f.write(f"{exp_no}:{t}:act:{adopters}:{non_adopters}"
                            f":att:{mean_str}:{std_str}\n")
                f.write(f"critical-point:{self.critical_time}\n")

            # ─── export-world (word "experiment-" exp-no "-world") ───
            self.save_model_state(
                os.path.join(output_dir, f"experiment-{exp_no}-world.pkl")
            )

            if progress_callback:
                progress_callback(exp_no)

        # ─── 四捨五入 adopter_list ───
        # 對應 NetLogo: set adopter-list replace-item index adopter-list round(item index adopter-list)
        self.adopter_list = [_nl_round(a) for a in self.adopter_list]

        # ─── 保存總結果 ───
        # 格式對應 NetLogo 的 file-print (word "critical-points:" critical-time-list)
        # NetLogo list 格式使用空格分隔: [0 45 23]，非 Python 的 [0, 45, 23]
        with open(os.path.join(output_dir, "experiment.txt"), 'w') as f:
            crit_str  = '[' + ' '.join(str(x) for x in self.critical_time_list) + ']'
            adopt_str = '[' + ' '.join(str(x) for x in self.adopter_list) + ']'
            f.write(f"critical-points:{crit_str}\n")
            f.write(f"adopters:{adopt_str}\n")

    # =========================================================================
    # NetLogo: import-simulation / export-world
    # =========================================================================
    def save_model_state(self, filename):
        """
        保存模型狀態 (對應 NetLogo 的 export-world)

        NetLogo 對應:
          export-world (word "experiment-" exp-no "-world")

        Python 實作: 使用 pickle 序列化完整模型狀態
        保存格式: 將 NumPy _states 轉換為 dict 格式以保持向後相容
        """
        # 轉換為 dict 格式以保持與舊版 .pkl 檔案的相容性
        node_states_dict = {}
        for node in range(self._states.shape[0]):
            node_states_dict[node] = {
                'att':   float(self._states[node, self._ATT]),
                'theta': float(self._states[node, self._THETA]),
                'act':   self._states[node, self._ACT] != 0.0,
                'time':  int(self._states[node, self._TIME]),
            }

        data = {
            'G': self.G,
            'node_states': node_states_dict,
            'critical_time': self.critical_time,
            'current_time': self.current_time,
            'attitude_snapshots': self._attitude_snapshots,
            'parameters': {
                'no_of_pioneers':       self.no_of_pioneers,
                'clustered_pioneers':   self.clustered_pioneers,
                'bounded_confidence':   self.bounded_confidence,
                'convergence_rate':     self.convergence_rate,
                'avg_of_attitudes':     self.avg_of_attitudes,
                'std_of_attitudes':     self.std_of_attitudes,
                'avg_of_thresholds':    self.avg_of_thresholds,
                'std_of_thresholds':    self.std_of_thresholds,
                'network_type':         self.network_type,
                'rewiring_probability': self.rewiring_probability,
                'max_time':             self.max_time,
                'no_of_experiments':    self.no_of_experiments,
            }
        }
        with open(filename, 'wb') as f:
            pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)

    def load_model_state(self, filename):
        """
        載入模型狀態 (對應 NetLogo 的 import-simulation / import-world)

        NetLogo 對應:
          to import-simulation
             clear-all
             let world-file user-file
             if (world-file != false) [ import-world world-file ]
          end

        視覺化歷史重建:
          .pkl 檔案保存了 attitude_snapshots (Attitude Trajectory 所需)。
          Adoption Dynamics 和 New Adopter Dynamics 則從節點的 time 欄位
          (採納時間) 精確反推重建，無需額外保存。
        """
        with open(filename, 'rb') as f:
            data = pickle.load(f)

        # ─── 清除舊的視覺化歷史資料 ───
        # 對應 NetLogo 的 clear-all (在 import-simulation 中)
        self._attitude_snapshots = {}
        self._new_adopters_per_tick = []
        self._adopters_per_tick = []
        self._non_adopters_per_tick = []

        self.G             = data['G']
        self.critical_time = data['critical_time']
        self.current_time  = data['current_time']

        # 從 dict 轉換為 NumPy 陣列 (向後相容舊格式)
        ns = data['node_states']
        if isinstance(ns, dict):
            self.node_states = ns  # 使用 setter 轉換
        else:
            self._states = ns  # 已經是 NumPy 陣列

        # 重建鄰居快取
        self._build_neighbors_cache()

        params = data['parameters']
        self.no_of_pioneers       = params['no_of_pioneers']
        self.clustered_pioneers   = params['clustered_pioneers']
        self.bounded_confidence   = params['bounded_confidence']
        self.convergence_rate     = params['convergence_rate']
        self.avg_of_attitudes     = params['avg_of_attitudes']
        self.std_of_attitudes     = params['std_of_attitudes']
        self.avg_of_thresholds    = params['avg_of_thresholds']
        self.std_of_thresholds    = params['std_of_thresholds']
        self.network_type         = params['network_type']
        self.rewiring_probability = params['rewiring_probability']
        self.max_time             = params['max_time']
        self.no_of_experiments    = params.get('no_of_experiments', 20)

        # ─── 重建視覺化歷史資料 ───
        # 1. 態度快照: 從 .pkl 載入 (向後相容: 舊版 .pkl 無此欄位時生成最終狀態)
        self._attitude_snapshots = data.get('attitude_snapshots', {})
        if not self._attitude_snapshots and self.current_time > 0:
            att_col = self._states[:, self._ATT]
            snapshot = {}
            for v in att_col:
                iv = int(v)
                if iv == v:
                    snapshot[iv] = snapshot.get(iv, 0) + 1
            self._attitude_snapshots[self.current_time - 1] = snapshot

        # 2. 採納動態: 從節點 time 欄位精確反推
        self._reconstruct_adoption_history()

    def _reconstruct_adoption_history(self):
        """
        從節點的 time 欄位反推每步的採納動態歷史資料。

        每個節點的 time 欄位記錄了該節點的採納時間:
          time = -1  → 尚未採納
          time = 0   → 先驅者 (初始即採納)
          time = t   → 在第 t 步採納

        從這些資訊可精確重建:
          _adopters_per_tick:     每步的累計採用者數
          _non_adopters_per_tick: 每步的未採用者數
          _new_adopters_per_tick: 每步新增的採用者數
        """
        if self.G is None or self._states.shape[0] == 0 or self.current_time == 0:
            return

        n_total = self._states.shape[0]
        time_col = self._states[:, self._TIME]

        for t in range(self.current_time):
            new_adopters = int(np.sum(time_col == t))
            self._new_adopters_per_tick.append(new_adopters)

            adopters = int(np.sum((time_col >= 0) & (time_col <= t)))
            self._adopters_per_tick.append(adopters)
            self._non_adopters_per_tick.append(n_total - adopters)


# =============================================================================
# ModelVisualizer: 對應 NetLogo Interface Tab 的所有圖表
#
# NetLogo 介面共有 6 個 PLOT 區域:
#   1. Attitude trajectory   (態度軌跡圖)    — 主圖，佔最大面積
#   2. Adoption dynamics     (採用動態圖)    — 採用/未採用人數曲線
#   3. New adopter dynamics  (新採用者動態)  — 每步新增採用者柱狀圖
#   4. Attitude distribution (態度分佈圖)    — 態度值直方圖
#   5. Threshold distribution(門檻分佈圖)    — 門檻值直方圖
#   6. Node degree distribution (節點度分佈) — 網絡度分佈圖
# =============================================================================

class ModelVisualizer:
    """
    模型視覺化類別
    ==============
    對應 NetLogo 4.0.5 Interface Tab 的所有 PLOT 區域和 MONITOR 顯示。

    NetLogo PLOT 對照:
      "Attitude trajectory"       → axes['attitude_trajectory']  (scatter plot)
      "Adoption dynamics"         → axes['adoption_dynamics']    (line plot)
      "New adopter dynamics"      → axes['new_adopter_dynamics'] (bar plot)
      "Attitude distribution"     → axes['attitude_dist']        (histogram)
      "Threshold distribution"    → axes['threshold_dist']       (histogram)
      "Node degree distribution"  → axes['degree_dist']          (histogram/scatter)

    加上一個額外的網絡結構圖:
      GRAPHICS-WINDOW             → axes['network']              (network graph)
    """

    def __init__(self, model):
        """初始化視覺化器"""
        self.model  = model
        self.fig    = None
        self.axes   = {}
        self.canvas = None
        self._network_canvas = None  # Social Network 獨立畫布

        # 儲存歷史數據 (對應 NetLogo plot 的自動累積功能)
        self.reset_plots()

    def reset_plots(self):
        """
        重置所有圖表的歷史數據

        對應 NetLogo:
          clear-all-plots (在 clear 程序中)
          plot-pen-reset  (在各 plot 程序中)

        效能最佳化:
          重置增量繪圖的內部追蹤狀態
        """
        # ─── 增量繪圖狀態 ───
        # 注意: 歷史資料現在由模型 (model._*_per_tick) 記錄和管理，
        # visualizer 只需追蹤繪圖狀態（Line2D 物件和已繪製的時間步）。
        # attitude_trajectory: 只繪製新增的時間步
        self._att_traj_last_drawn_time = -1
        self._att_traj_collections = [None] * 15  # 每種顏色一個 PathCollection
        self._att_traj_points = [[] for _ in range(15)]  # 每種顏色的 (t, att) 座標累積
        # adoption_dynamics: 只追加新數據點 (保留 Line2D 物件)
        self._adoption_line_adopters     = None
        self._adoption_line_non_adopters = None
        # new_adopter_dynamics: 只追加新數據點
        self._new_adopter_line = None
        # 標記是否需要完全重繪 (setup 後)
        self._needs_full_redraw = True

    def setup_figure(self, fig_size=(16, 10)):
        """
        設定圖形和子圖佈局

        對應 NetLogo Interface Tab 的 PLOT 佈局 (已調整):
          ┌───────────┬──────────┬──────────────┐
          │ Attitude  │Threshold │ Node degree  │
          │ dist.     │ dist.    │ dist.        │
          ├───────────┴──────────┴──────────────┤
          │ Attitude trajectory (全寬)           │
          ├─────────────────────────────────────┤
          │ Adoption dynamics (全寬)             │
          ├─────────────────────────────────────┤
          │ New adopter dynamics (全寬)          │
          └─────────────────────────────────────┘
          (Social Network 圖移至左側控制面板)

        Python 使用嵌套 GridSpec 實現佈局:
          Row 0: attitude_dist, threshold_dist, degree_dist ← 三等分
          Row 1: attitude_trajectory (全寬)
          Row 2: adoption_dynamics (全寬)
          Row 3: new_adopter_dynamics (全寬)
        """
        self.fig = Figure(figsize=fig_size, dpi=100)

        # 外層 GridSpec: 4 行，height_ratios 控制各列高度比例
        gs = self.fig.add_gridspec(4, 1, hspace=0.4,
                                   height_ratios=[2, 3, 1.5, 1.5])

        # Row 0: 三等分 (分佈圖)
        gs_row0 = gs[0, 0].subgridspec(1, 3, wspace=0.5)
        self.axes['attitude_dist']        = self.fig.add_subplot(gs_row0[0, 0])
        self.axes['threshold_dist']       = self.fig.add_subplot(gs_row0[0, 1])
        self.axes['degree_dist']          = self.fig.add_subplot(gs_row0[0, 2])

        # Row 1: 態度軌跡 (全寬)
        self.axes['attitude_trajectory']  = self.fig.add_subplot(gs[1, 0])

        # Row 2: 採用動態 (全寬)
        self.axes['adoption_dynamics']    = self.fig.add_subplot(gs[2, 0])

        # Row 3: 新採用者動態 (全寬)
        self.axes['new_adopter_dynamics'] = self.fig.add_subplot(gs[3, 0])

        return self.fig

    def setup_network_figure(self, fig_size=(5, 5)):
        """
        設定 Social Network 圖的獨立 Figure (嵌入左側控制面板)

        從主圖表 Figure 分離，使右側圖表區的三張時間序列圖
        (Attitude Trajectory, Adoption Dynamics, New Adopter Dynamics)
        共享相同的全寬 X 軸 (Time)。
        """
        self._network_fig = Figure(figsize=fig_size, dpi=100)
        self.axes['network'] = self._network_fig.add_subplot(111)
        return self._network_fig

    def plot_network(self):
        """
        繪製社交網絡結構圖

        NetLogo 對應:
          GRAPHICS-WINDOW (850, 10, 1290, 471)
          - 20x20 的世界 (0~19, 0~19)
          - 節點顏色:
              已採用 (act=true)  → red
              未採用 (act=false) → scale-color green att 100 1
                                   (綠色漸變，att越高越綠)
          - 邊的顏色: gray - 3 (深灰色)

        NetLogo set-agent-color 對應:
          to set-agent-color
             ifelse (act = true)
                 [ set color red ]
                 [ set color scale-color green att 100 1 ]
          end

        Python 實作:
          - scale-color green att 100 1 在 NetLogo 中意思是:
            以 green 為基色，proportion = (att - 1) / (100 - 1)
            att=1 → proportion=0 → 最暗 (深綠/黑)
            att=100 → proportion=1 → 最亮 (亮綠/白)
          - 在 Python 中使用 (0, att/100, 0) 的 RGB 近似
        """
        ax = self.axes['network']
        ax.clear()
        ax.set_title('Social Network', fontsize=9, color='blue', fontweight='bold')

        if self.model.G is None or self.model._states.shape[0] == 0:
            return

        pos = nx.get_node_attributes(self.model.G, 'pos')

        # ─── set-agent-color 對應 ───
        # 效能最佳化: 直接存取 NumPy 陣列
        states = self.model._states
        ATT = self.model._ATT
        ACT = self.model._ACT
        node_colors = []
        for node in self.model.G.nodes():
            if states[node, ACT] != 0.0:
                node_colors.append('red')
            else:
                intensity = max(0.05, states[node, ATT] / 100.0)
                node_colors.append((0, intensity, 0))

        # 繪製邊 (gray - 3 ≈ 深灰色)
        nx.draw_networkx_edges(
            self.model.G, pos, ax=ax,
            edge_color='#404040', alpha=0.3, width=0.3
        )

        # 繪製節點 (set size 0.3 → 小圓點)
        nx.draw_networkx_nodes(
            self.model.G, pos, ax=ax,
            node_color=node_colors, node_size=20, edgecolors='none'
        )

        ax.set_xlim(-1, 20)
        ax.set_ylim(-1, 20)
        ax.set_aspect('equal')
        ax.set_axis_off()

    # ─── NetLogo 色譜 (類別常數，避免每次重建) ───
    _COLOR_SPECTRUM = [
        '#FFFFFF',   # 9 (white in NetLogo = color 9)
        '#FF69B4',   # pink
        '#FF0000',   # red
        '#FF8C00',   # orange
        '#8B4513',   # brown
        '#FFFF00',   # yellow
        '#00FF00',   # green
        '#32CD32',   # lime
        '#40E0D0',   # turquoise
        '#00FFFF',   # cyan
        '#87CEEB',   # sky
        '#0000FF',   # blue
        '#EE82EE',   # violet
        '#FF00FF',   # magenta
        '#000000',   # black
    ]

    def plot_attitude_trajectory(self):
        """
        繪製態度軌跡圖 — 顯示態度值分佈隨時間的演變

        NetLogo 對應:
          PLOT "Attitude trajectory" (220, 10, 780, 457)
          X軸: Time (1~max-time), Y軸: Attitude (1~100)

        效能最佳化:
          將每個 (t, att) 的獨立 ax.scatter() 呼叫改為按顏色分組，
          每種顏色固定一個 PathCollection，以 set_offsets() 增量更新。
          axes 上的 artist 數量從 O(T×K) 降為固定 15 個，
          使 draw_idle() 的渲染成本與時間步數無關。
        """
        ax = self.axes['attitude_trajectory']

        if self.model.G is None or self.model._states.shape[0] == 0:
            return

        # 檢測模型重置 → 需要完全重繪
        if self.model.current_time == 0 or self._needs_full_redraw:
            ax.clear()
            ax.set_title('Attitude Trajectory', fontsize=9, color='blue', fontweight='bold')
            ax.set_xlabel('Time')
            ax.set_ylabel('Attitude')
            ax.set_ylim(1, 100)
            ax.grid(True, linestyle='--', alpha=0.3)
            self._att_traj_last_drawn_time = -1
            # ax.clear() 會移除所有 artist，必須重建 PathCollection 狀態
            self._att_traj_collections = [None] * 15
            self._att_traj_points = [[] for _ in range(15)]

        # ─── 增量繪圖: 從模型的態度快照中讀取所有未繪製的時間步 ───
        # 資料由 model.step() 每步記錄到 model._attitude_snapshots，
        # 因此即使 GUI 每 N 步才更新一次繪圖，也不會遺失中間步的資料。
        color_spectrum = self._COLOR_SPECTRUM
        n_colors = len(color_spectrum)
        total_turtles = self.model._states.shape[0]
        log_total = math.log2(total_turtles) if total_turtles > 1 else 1

        snapshots = self.model._attitude_snapshots
        last_drawn = self._att_traj_last_drawn_time
        # 遍歷所有已記錄但尚未繪製的快照
        # 注意: 快照在 step() 的 current_time += 1 之前記錄，
        # 所以 key 範圍是 0..current_time-1。用 snapshots 的實際 key 確保不遺漏。
        max_snap_t = max(snapshots.keys()) if snapshots else -1

        # 追蹤哪些顏色有新增資料（避免不必要的 set_offsets 呼叫）
        dirty = set()

        for t in range(last_drawn + 1, max_snap_t + 1):
            attitudes = snapshots.get(t)
            if attitudes is None:
                continue
            for att, count in attitudes.items():
                if count > 0:
                    log_count = math.log2(count) if count > 1 else 0
                    color_index = _nl_round(log_count * ((n_colors - 1) / log_total))
                    color_index = max(0, min(color_index, n_colors - 1))
                    self._att_traj_points[color_index].append((t, att))
                    dirty.add(color_index)

        # 更新有新增資料的 PathCollection
        for ci in dirty:
            pts = self._att_traj_points[ci]
            offsets = np.array(pts)
            if self._att_traj_collections[ci] is None:
                # 首次出現此顏色 → 建立 PathCollection
                self._att_traj_collections[ci] = ax.scatter(
                    offsets[:, 0], offsets[:, 1],
                    color=color_spectrum[ci],
                    s=1, marker=',', linewidths=0, alpha=0.9)
            else:
                # 追加座標到現有 PathCollection
                self._att_traj_collections[ci].set_offsets(offsets)

        self._att_traj_last_drawn_time = max_snap_t
        ax.set_xlim(0, max(self.model.max_time, self.model.current_time + 1))

    def plot_adoption_dynamics(self):
        """
        繪製採用動態圖

        NetLogo 對應:
          PLOT "Adoption dynamics" (220, 457, 842, 577)
          PENS: "Adopter" (紅色線), "Not-yet-adopter" (綠色線)

        效能最佳化:
          使用 Line2D.set_data() 更新已有的線條物件，
          不再每次 clear + 重繪。
        """
        ax = self.axes['adoption_dynamics']

        # 檢測模型重置或首次繪製 → 設定標題和軸標籤
        if self._needs_full_redraw or self._adoption_line_adopters is None:
            ax.clear()
            ax.set_title('Adoption Dynamics', fontsize=9, color='blue', fontweight='bold')
            ax.set_xlabel('Time')
            ax.set_ylabel('Agent')
            self._adoption_line_adopters = None
            self._adoption_line_non_adopters = None

        if self.model.G is None or self.model._states.shape[0] == 0:
            return

        # ─── 從模型的每步記錄中讀取採用者/非採用者數量 ───
        # 資料由 model.step() 每步記錄，確保即使 GUI 跳步更新也完整
        adopters_hist = self.model._adopters_per_tick
        non_adopters_hist = self.model._non_adopters_per_tick
        if not adopters_hist:
            return

        n_total = self.model._states.shape[0]
        times = list(range(len(adopters_hist)))

        if self._adoption_line_adopters is None:
            # 首次繪製 → 建立 Line2D 物件
            self._adoption_line_adopters, = ax.plot(
                times, adopters_hist, color='red', label='Adopter')
            self._adoption_line_non_adopters, = ax.plot(
                times, non_adopters_hist, color='green', label='Not-yet-adopter')
            ax.legend(fontsize=7)
        else:
            # 增量更新: 只更新數據，不重繪整個圖
            self._adoption_line_adopters.set_data(times, adopters_hist)
            self._adoption_line_non_adopters.set_data(times, non_adopters_hist)

        ax.set_ylim(0, n_total)
        ax.set_xlim(1, max(self.model.max_time, len(times)))

    def plot_new_adopter_dynamics(self):
        """
        繪製新採用者動態圖

        NetLogo 對應:
          PLOT "New adopter dynamics" (220, 577, 842, 697)
          PENS: "New adopter" (橘色線)

        效能最佳化:
          使用 Line2D.set_data() 增量更新，
          使用 NumPy 向量化統計新採用者數量。
        """
        ax = self.axes['new_adopter_dynamics']

        # 檢測模型重置或首次繪製 → 設定標題和軸標籤
        if self._needs_full_redraw or self._new_adopter_line is None:
            ax.clear()
            ax.set_title('New Adopter Dynamics', fontsize=9, color='blue', fontweight='bold')
            ax.set_xlabel('Time')
            ax.set_ylabel('Agent')
            self._new_adopter_line = None

        if self.model.G is None or self.model._states.shape[0] == 0:
            return

        # ─── 從模型的每步記錄中讀取新採用者數量 ───
        # 資料由 model.step() 每步記錄到 model._new_adopters_per_tick，
        # 因此即使 GUI 每 N 步才更新一次繪圖，也不會遺失中間步的資料。
        # 且因為是在 current_time += 1 之前記錄的，TIME 欄位匹配正確。
        history = self.model._new_adopters_per_tick
        if not history:
            return

        times = list(range(len(history)))

        if self._new_adopter_line is None:
            self._new_adopter_line, = ax.plot(
                times, history, color='orange', linewidth=1)
        else:
            self._new_adopter_line.set_data(times, history)

        max_val = max(history)
        ax.set_ylim(0, max(10, max_val * 1.1))
        ax.set_xlim(1, max(self.model.max_time, len(times)))

    def plot_attitude_distribution(self):
        """
        繪製態度分佈直方圖

        NetLogo 對應:
          PLOT "Attitude distribution" (40, 457, 212, 696)
          histogram [ att ] of turtles

        效能最佳化:
          直接使用 NumPy 陣列的 att 欄位，避免列表建構。
          (直方圖每次需要完全重繪，因為分佈會改變)
        """
        ax = self.axes['attitude_dist']
        ax.clear()
        ax.set_title('Attitude Distribution', fontsize=9, color='blue', fontweight='bold')
        ax.set_xlabel('Attitude', fontsize=8)
        ax.set_ylabel('Agent', fontsize=8)

        if self.model.G is None or self.model._states.shape[0] == 0:
            return

        # 效能最佳化: 直接使用 NumPy 陣列切片
        attitudes = self.model._states[:, self.model._ATT]

        x_max = 101 if self.model.avg_of_attitudes == 100 else 100
        ax.hist(attitudes, bins=range(1, x_max + 1), color='red', edgecolor='darkred',
                alpha=0.7, rwidth=0.8)
        ax.set_xlim(1, x_max)

    def plot_threshold_distribution(self):
        """
        繪製門檻分佈直方圖

        NetLogo 對應:
          PLOT "Threshold distribution" (850, 472, 1070, 698)
          histogram [ theta ] of turtles

        效能最佳化:
          直接使用 NumPy 陣列的 theta 欄位。
        """
        ax = self.axes['threshold_dist']
        ax.clear()
        ax.set_title('Threshold Distribution', fontsize=9, color='blue', fontweight='bold')
        ax.set_xlabel('Threshold', fontsize=8)
        ax.set_ylabel('Agent', fontsize=8)

        if self.model.G is None or self.model._states.shape[0] == 0:
            return

        # 效能最佳化: 直接使用 NumPy 陣列切片
        thresholds = self.model._states[:, self.model._THETA]

        x_max = 101 if self.model.avg_of_thresholds == 100 else 100
        ax.hist(thresholds, bins=range(1, x_max + 1), color='red', edgecolor='darkred',
                alpha=0.7, rwidth=0.8)
        ax.set_xlim(1, x_max)

    def plot_degree_distribution(self):
        """
        繪製節點度分佈圖

        NetLogo 對應:
          PLOT "Node degree distribution" (1070, 472, 1290, 698)
          X軸: Degree, Y軸: Node
          PENS: "default" 1.0 1 -2674135 false (紅色)

          兩種模式:
          1. SWN/RN/CA → plot-SWN-degree-distribution (直方圖, pen mode 1)
             to plot-SWN-degree-distribution
                set-plot-pen-mode 1
                let max-degree max [ count link-neighbors ] of turtles
                let min-degree min [ count link-neighbors ] of turtles
                set-plot-x-range min-degree max-degree + 1
                histogram [ count link-neighbors ] of turtles
             end

          2. SFN → plot-SFN-degree-distribution (散點圖, pen mode 2, log-log)
             to plot-SFN-degree-distribution
                set-plot-pen-mode 2
                let degree 1
                let max-degree max [ count link-neighbors ] of turtles
                while [ degree <= max-degree ] [
                      let matches turtles with [ count link-neighbors = degree ]
                      if (any? matches) [ plotxy log degree 10 log (count matches) 10 ]
                      set degree degree + 1
                ]
             end
        """
        ax = self.axes['degree_dist']
        ax.clear()
        ax.set_title('Degree Distribution', fontsize=9, color='blue', fontweight='bold')

        if self.model.G is None:
            return

        degrees = [self.model.G.degree(n) for n in self.model.G.nodes()]

        if self.model.network_type == "SFN":
            # ─── SFN: 雙對數散點圖 (log-log) ───
            ax.set_xlabel('log(Degree)', fontsize=8)
            ax.set_ylabel('log(Count)', fontsize=8)

            max_degree = max(degrees) if degrees else 1
            for d in range(1, max_degree + 1):
                count = degrees.count(d)
                if count > 0:
                    # plotxy log degree 10 log (count matches) 10
                    ax.scatter(
                        math.log10(d), math.log10(count),
                        color='red', s=15, alpha=0.7
                    )
        else:
            # ─── SWN/RN/CA: 直方圖 ───
            ax.set_xlabel('Degree', fontsize=8)
            ax.set_ylabel('Node', fontsize=8)

            min_deg = min(degrees) if degrees else 0
            max_deg = max(degrees) if degrees else 1
            ax.hist(degrees, bins=range(min_deg, max_deg + 2), color='red',
                    edgecolor='darkred', alpha=0.7, rwidth=0.8)
            ax.set_xlim(min_deg, max_deg + 1)

    def update_plots(self):
        """
        更新所有圖表

        NetLogo 對應:
          update-plot 程序中依序更新所有 PLOT
          + plot-att-distribution (在 update-plot 末尾呼叫)
          + plot-theta-distribution (在 setup-agent-population 中呼叫)
          + plot-network-degree-distribution (在 setup-social-network 中呼叫)
        """
        try:
            self.plot_network()
            self.plot_attitude_trajectory()
            self.plot_adoption_dynamics()
            self.plot_new_adopter_dynamics()
            self.plot_attitude_distribution()
            self.plot_threshold_distribution()
            self.plot_degree_distribution()

            # 增量繪圖: 重置完全重繪旗標
            self._needs_full_redraw = False

            if self.canvas:
                self.canvas.draw_idle()
            if self._network_canvas:
                self._network_canvas.draw_idle()
        except Exception as e:
            print(f"Plot update error: {e}")

    def set_canvas(self, canvas):
        """設定 Tkinter 畫布"""
        self.canvas = canvas

    def set_network_canvas(self, canvas):
        """設定 Social Network 的 Tkinter 畫布"""
        self._network_canvas = canvas

    def save_attitude_trajectory_hires(self, filename, dpi=300):
        """
        將 Attitude Trajectory 圖表單獨保存為高解析度 JPEG 圖片，供研究使用。

        此方法會建立一個獨立的 Figure，將模型中所有已記錄的態度快照
        (_attitude_snapshots) 重新繪製在上面，然後以指定的 dpi 輸出。
        不影響 GUI 上的即時圖表。

        參數:
          filename: 輸出檔案路徑 (應以 .jpeg 結尾)
          dpi:      輸出解析度 (預設 300，適合研究論文)

        設計說明:
          不直接擷取 GUI 上的子圖 (因為 GUI 子圖受限於螢幕 dpi 和佈局比例)，
          而是建立獨立 Figure 重新繪製，確保輸出品質和尺寸可控。
        """
        if self.model.G is None or self.model._states.shape[0] == 0:
            print("No simulation data to save.")
            return

        snapshots = self.model._attitude_snapshots
        if not snapshots:
            print("No attitude snapshots to save.")
            return

        # ─── 建立獨立的高解析度 Figure (不使用 plt，避免線程安全問題) ───
        hires_fig = Figure(figsize=(10, 6), dpi=dpi)
        FigureCanvasAgg(hires_fig)  # 附加 Agg 畫布以支援 savefig
        ax = hires_fig.add_subplot(111)
        ax.set_title('Attitude Trajectory', fontsize=14, color='blue', fontweight='bold')
        ax.set_xlabel('Time', fontsize=12)
        ax.set_ylabel('Attitude', fontsize=12)
        ax.set_ylim(1, 100)
        ax.grid(True, linestyle='--', alpha=0.3)

        # ─── 使用與 GUI 版完全相同的色譜和繪製邏輯 ───
        color_spectrum = self._COLOR_SPECTRUM
        n_colors = len(color_spectrum)
        total_turtles = self.model._states.shape[0]
        log_total = math.log2(total_turtles) if total_turtles > 1 else 1

        # ─── 按顏色分組收集所有座標 ───
        color_points = [[] for _ in range(n_colors)]
        for t in sorted(snapshots.keys()):
            attitudes = snapshots[t]
            for att, count in attitudes.items():
                if count > 0:
                    log_count = math.log2(count) if count > 1 else 0
                    color_index = _nl_round(log_count * ((n_colors - 1) / log_total))
                    color_index = max(0, min(color_index, n_colors - 1))
                    color_points[color_index].append((t, att))

        # 每種顏色一次 scatter 呼叫（最多 15 次，取代原本 ~9,000 次）
        for ci in range(n_colors):
            if color_points[ci]:
                pts = np.array(color_points[ci])
                ax.scatter(pts[:, 0], pts[:, 1],
                           color=color_spectrum[ci],
                           s=2, marker=',', linewidths=0, alpha=0.9)

        ax.set_xlim(0, max(self.model.max_time, self.model.current_time + 1))

        # ─── 保存為 JPEG ───
        hires_fig.savefig(filename, dpi=dpi, bbox_inches='tight',
                          format='jpeg', pil_kwargs={'quality': 95})
        del hires_fig
        print(f"Attitude Trajectory saved: {filename}")


# =============================================================================
# ModelGUI: 對應 NetLogo Interface Tab 的完整使用者介面
#
# NetLogo 介面元件對照:
#   BUTTON "Experiments"      → btn_experiments
#   BUTTON "Run once"         → btn_run_once
#   BUTTON "Load"             → btn_load
#   SLIDER no-of-pioneers     → pioneers_scale
#   SWITCH clustered-pioneers → clustered_check
#   SLIDER bounded-confidence → confidence_scale
#   SLIDER convergence-rate   → conv_rate_scale
#   SLIDER avg-of-attitudes   → avg_att_scale
#   SLIDER std-of-attitudes   → std_att_scale
#   SLIDER avg-of-thresholds  → avg_thres_scale
#   SLIDER std-of-thresholds  → std_thres_scale
#   CHOOSER network-type      → network_combo
#   SLIDER rewiring-probability → rewiring_scale
#   SLIDER max-time           → max_time_scale
#   SLIDER no-of-experiments  → experiments_scale
#   MONITOR PA                → pa_label
#   MONITOR Avg PA            → avg_pa_label
#   MONITOR Std PA            → std_pa_label
#   MONITOR NA                → na_label
#   MONITOR Avg NA            → avg_na_label
#   MONITOR Std NA            → std_na_label
#   MONITOR Links             → links_label
#   MONITOR Critical          → critical_label
#   MONITOR Adopter           → adopter_label
# =============================================================================

class ModelGUI(tk.Tk):
    """
    BCAT 模型的圖形使用者介面
    ==========================
    對應 NetLogo 4.0.5 的 Interface Tab，包含:
    - 控制按鈕 (Experiments, Run once, Setup, Run, Stop, Load)
    - 參數滑桿和選擇器
    - 監視器面板 (即時數據顯示)
    - 圖表區域 (7個子圖)
    """

    def __init__(self):
        """
        初始化 GUI

        NetLogo 對應:
          startup 程序在模型載入時自動執行
          → 這裡在建立 GUI 後自動呼叫 setup()
        """
        super().__init__()

        self.title("BCAT - Best Game No One Played / 叫好不叫座")
        self.geometry("1400x1150")

        # 建立模型和視覺化器
        self.model      = OpinionAdoptionModel()
        self.visualizer = ModelVisualizer(self.model)

        # 控制旗標
        self.running     = False
        self.stop_button = None

        # 建立 GUI 元件
        self._create_widgets()

        # ─── startup → setup ───
        self.model.setup()
        self.visualizer.reset_plots()
        self.visualizer.update_plots()
        self._update_monitors()

    def _create_widgets(self):
        """
        建立所有 GUI 元件

        佈局對應 NetLogo Interface Tab:
          左側: 控制面板 (按鈕 + 滑桿 + 監視器)
          右側: 圖表區域

        NetLogo 介面座標 (像素):
          控制區域:   x=40~212
          監視器:     x=780~842
          圖表區域:   x=220~1290
          GRAPHICS:   x=850~1290
        """
        # ════════════════════════════════════════
        # 左側控制面板
        # ════════════════════════════════════════
        control_frame = ttk.Frame(self, padding=10)
        control_frame.pack(side=tk.LEFT, fill=tk.Y)

        # ─── 按鈕列 (對應 NetLogo BUTTON 元件) ───
        btn_frame = ttk.Frame(control_frame)
        btn_frame.grid(row=0, column=0, columnspan=2, sticky=tk.EW, pady=(0, 5))

        # BUTTON "Experiments" (40, 11, 142, 44) → run-100-experiments
        ttk.Button(btn_frame, text="Experiments",
                   command=self._run_experiments).pack(side=tk.LEFT, padx=2)

        # BUTTON "Run once" (145, 11, 211, 44) → go 0
        ttk.Button(btn_frame, text="Run Once",
                   command=self._run_once).pack(side=tk.LEFT, padx=2)

        # 額外按鈕 (非 NetLogo 原有，但 Python 版本需要)
        ttk.Button(btn_frame, text="Setup",
                   command=self._setup).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Run",
                   command=self._run_simulation).pack(side=tk.LEFT, padx=2)

        # BUTTON "Load" (780, 424, 843, 458) → import-simulation
        ttk.Button(btn_frame, text="Load",
                   command=self._load_model).pack(side=tk.LEFT, padx=2)

        row = 1

        # ─── SLIDER no-of-pioneers (40, 50, 211, 83) ───
        # 範圍: 0~100, 預設: 5, 步進: 1
        row = self._add_slider(control_frame, row, "No. of Pioneers",
                               'pioneers_var', tk.IntVar, self.model.no_of_pioneers,
                               0, 100, 'no_of_pioneers')

        # ─── SWITCH clustered-pioneers? (40, 83, 211, 116) ───
        # NetLogo switch: 0=ON(true), 1=OFF(false)
        self.clustered_var = tk.BooleanVar(value=self.model.clustered_pioneers)
        ttk.Checkbutton(
            control_frame, text="Clustered Pioneers",
            variable=self.clustered_var,
            command=lambda: self._update_param('clustered_pioneers', self.clustered_var.get())
        ).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2)
        row += 1

        # ─── SLIDER bounded-confidence (40, 115, 211, 148) ───
        # 範圍: 0~90, 預設: 50, 步進: 10
        row = self._add_slider(control_frame, row, "Bounded Confidence",
                               'confidence_var', tk.IntVar, self.model.bounded_confidence,
                               0, 90, 'bounded_confidence')

        # ─── SLIDER convergence-rate (40, 149, 212, 182) ───
        # 範圍: 0.1~1.0, 預設: 0.1, 步進: 0.1
        row = self._add_slider(control_frame, row, "Convergence Rate",
                               'conv_rate_var', tk.DoubleVar, self.model.convergence_rate,
                               0.1, 1.0, 'convergence_rate', resolution=0.1)

        # ─── SLIDER avg-of-attitudes (40, 182, 212, 215) ───
        # 範圍: 10~100, 預設: 50, 步進: 10
        row = self._add_slider(control_frame, row, "Avg. of Attitudes",
                               'avg_att_var', tk.IntVar, self.model.avg_of_attitudes,
                               10, 100, 'avg_of_attitudes')

        # ─── SLIDER std-of-attitudes (40, 215, 212, 248) ───
        # 範圍: 0~30, 預設: 10, 步進: 5
        row = self._add_slider(control_frame, row, "Std. of Attitudes",
                               'std_att_var', tk.IntVar, self.model.std_of_attitudes,
                               0, 30, 'std_of_attitudes')

        # ─── SLIDER avg-of-thresholds (40, 248, 212, 281) ───
        # 範圍: 10~100, 預設: 40, 步進: 5
        row = self._add_slider(control_frame, row, "Avg. of Thresholds",
                               'avg_thres_var', tk.IntVar, self.model.avg_of_thresholds,
                               10, 100, 'avg_of_thresholds')

        # ─── SLIDER std-of-thresholds (40, 280, 212, 313) ───
        # 範圍: 0~30, 預設: 10, 步進: 5
        row = self._add_slider(control_frame, row, "Std. of Thresholds",
                               'std_thres_var', tk.IntVar, self.model.std_of_thresholds,
                               0, 30, 'std_of_thresholds')

        # ─── CHOOSER network-type (40, 314, 212, 359) ───
        # 選項: "SFN" "SWN/RN/CA", 預設索引: 1
        ttk.Label(control_frame, text="Network Type").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.network_var = tk.StringVar(value=self.model.network_type)
        network_combo = ttk.Combobox(
            control_frame, textvariable=self.network_var,
            values=["SFN", "SWN/RN/CA"], state="readonly", width=12
        )
        network_combo.grid(row=row, column=1, sticky=tk.EW)
        network_combo.bind("<<ComboboxSelected>>",
                           lambda e: self._update_param('network_type', self.network_var.get()))
        row += 1

        # ─── SLIDER rewiring-probability (40, 358, 212, 391) ───
        # 範圍: 0.00~1.00, 預設: 0, 步進: 0.05
        row = self._add_slider(control_frame, row, "Rewiring Prob.",
                               'rewiring_var', tk.DoubleVar, self.model.rewiring_probability,
                               0.0, 1.0, 'rewiring_probability', resolution=0.05)

        # ─── SLIDER max-time (40, 390, 212, 423) ───
        # 範圍: 50~1000, 預設: 300, 步進: 50
        row = self._add_slider(control_frame, row, "Max Time",
                               'max_time_var', tk.IntVar, self.model.max_time,
                               50, 1000, 'max_time')

        # ─── SLIDER no-of-experiments (40, 424, 211, 457) ───
        # 範圍: 10~1000, 預設: 20, 步進: 10
        row = self._add_slider(control_frame, row, "No. of Experiments",
                               'experiments_var', tk.IntVar, self.model.no_of_experiments,
                               10, 1000, 'no_of_experiments')

        # ════════════════════════════════════════
        # Social Network 圖 (獨立 Figure，嵌入左側面板)
        # ════════════════════════════════════════
        network_fig = self.visualizer.setup_network_figure()
        self._network_canvas = FigureCanvasTkAgg(network_fig, master=control_frame)
        self._network_canvas.get_tk_widget().grid(
            row=row, column=0, columnspan=2, sticky=tk.EW, pady=5)
        self.visualizer.set_network_canvas(self._network_canvas)
        row += 1

        # ════════════════════════════════════════
        # 監視器面板 (對應 NetLogo MONITOR 元件)
        # ════════════════════════════════════════
        monitor_frame = ttk.LabelFrame(control_frame, text="Monitors", padding=5)
        monitor_frame.grid(row=row, column=0, columnspan=2, sticky=tk.EW, pady=10)

        # ─── MONITOR Critical ───
        # critical-point
        self.critical_var = tk.StringVar(value="0")
        ttk.Label(monitor_frame, text="Critical").grid(row=0, column=0, sticky=tk.W)
        ttk.Label(monitor_frame, textvariable=self.critical_var, width=10, anchor=tk.E).grid(row=0, column=1)

        # ─── MONITOR FRI (Favorable Review Index) ───
        # FRI = count(att > 50) / N
        self.fri_var = tk.StringVar(value="0.0000")
        ttk.Label(monitor_frame, text="FRI").grid(row=1, column=0, sticky=tk.W)
        ttk.Label(monitor_frame, textvariable=self.fri_var, width=10, anchor=tk.E).grid(row=1, column=1)

        # ─── MONITOR GSI (Good Sales Index) ───
        # GSI = count(act = true) / N
        self.gsi_var = tk.StringVar(value="0.0000")
        ttk.Label(monitor_frame, text="GSI").grid(row=2, column=0, sticky=tk.W)
        ttk.Label(monitor_frame, textvariable=self.gsi_var, width=10, anchor=tk.E).grid(row=2, column=1)

        # ════════════════════════════════════════
        # 右側圖表區域
        # ════════════════════════════════════════
        plot_frame = ttk.Frame(self)
        plot_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        fig = self.visualizer.setup_figure()
        self.canvas = FigureCanvasTkAgg(fig, master=plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.visualizer.set_canvas(self.canvas)

    def _add_slider(self, parent, row, label, var_name, var_type, default,
                    from_, to, param_name, resolution=None):
        """
        建立一個滑桿控制元件 (對應 NetLogo SLIDER)

        NetLogo SLIDER 格式:
          SLIDER
          x1 y1 x2 y2        (位置座標)
          variable-name       (變數名)
          variable-name       (顯示名)
          min max default     (最小值 最大值 預設值)
          step                (步進)
          1                   (精度)
          NIL                 (單位)
          HORIZONTAL          (方向)
        """
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky=tk.W, pady=2)

        var = var_type(value=default)
        setattr(self, var_name, var)

        # 顯示當前值的標籤
        value_label = ttk.Label(parent, text=str(default), width=6, anchor=tk.E)
        value_label.grid(row=row, column=1, sticky=tk.E)

        row += 1

        # 使用 tk.Scale (非 ttk.Scale)：
        #   - 原生支援 resolution 參數，數值精確對齊步進值
        #   - 拖曳和點擊行為一致，不會跳到端點
        #   - ttk.Scale 在 macOS 上點擊 trough 時可能跳到 0 或 1
        scale_kw = dict(
            from_=from_, to=to, variable=var, orient=tk.HORIZONTAL,
            length=180, showvalue=False,        # 值已由 value_label 顯示
        )
        if resolution:
            scale_kw['resolution'] = resolution
        elif var_type == tk.IntVar:
            scale_kw['resolution'] = 1

        scale = tk.Scale(parent, **scale_kw)
        scale.grid(row=row, column=0, columnspan=2, sticky=tk.EW, padx=5)

        def on_change(val=None):
            v = var.get()
            value_label.config(text=f"{v}")
            self._update_param(param_name, v)

        scale.config(command=on_change)

        return row + 1

    def _update_param(self, param_name, value):
        """更新模型參數"""
        setattr(self.model, param_name, value)

    def _update_monitors(self):
        """
        更新所有監視器顯示

        對應 NetLogo 介面上的 MONITOR 元件，每個 MONITOR 顯示一個即時計算的值。

        效能最佳化:
          使用 NumPy 向量化操作取代逐節點遍歷。
        """
        if self.model.G is None or self.model._states.shape[0] == 0:
            return

        try:
            states = self.model._states
            ATT = self.model._ATT
            ACT = self.model._ACT
            n_total = states.shape[0]
            att_col = states[:, ATT]

            # ─── MONITOR Critical: critical-point ───
            self.critical_var.set(str(self.model.critical_point))

            # ─── MONITOR FRI: Favorable Review Index = count(att > 50) / N ───
            pa_count = int(np.sum((att_col > 50) & (att_col <= 100)))
            fri = pa_count / n_total if n_total > 0 else 0.0
            self.fri_var.set(f"{fri:.4f}")

            # ─── MONITOR GSI: Good Sales Index = count(act = true) / N ───
            adopter_count = int(np.sum(states[:, ACT]))
            gsi = adopter_count / n_total if n_total > 0 else 0.0
            self.gsi_var.set(f"{gsi:.4f}")

        except Exception as e:
            print(f"Monitor update error: {e}")

    def _setup(self):
        """
        重新初始化模型

        NetLogo 對應: 點擊 Setup 按鈕
          → 呼叫 setup 程序
        """
        self.running = False
        self.model.setup()
        self.visualizer.reset_plots()
        self.visualizer._needs_full_redraw = True
        self.visualizer.update_plots()
        self._update_monitors()

    def _run_once(self):
        """
        執行單步模擬

        NetLogo 對應:
          BUTTON "Run once" (145, 11, 211, 44)
          → go 0 (在 NetLogo 中會先 setup 再執行完整 max-time 模擬)

        行為差異:
          Python 版將 "Run Once" 改為執行單一時間步 (step)，
          而非 NetLogo 原版的完整模擬，以提供更好的互動體驗。
          使用者可逐步觀察每個 tick 的變化。
          若要執行完整的 setup + max-time 模擬，使用 "Run" 按鈕。
        """
        if self.model.G is None or len(self.model.node_states) == 0:
            self.model.setup()
            self.visualizer.reset_plots()

        self.model.step()
        self.visualizer.update_plots()
        self._update_monitors()

    # 效能最佳化: 繪圖更新頻率控制
    # 每 _PLOT_UPDATE_INTERVAL 步更新一次圖表，而非每步都更新
    _PLOT_UPDATE_INTERVAL = 5

    def _build_attitude_trajectory_filename(self):
        """
        依照目前 GUI 介面上的參數組合，組裝 Attitude Trajectory 圖片的檔案名稱。

        檔名格式:
          Attitude-Trajectory-{pioneers}-{clustered}-{bc}-{cr}-{avg_att}-{std_att}
          -{avg_thresh}-{std_thresh}-{network}-{rewiring}-{max_time}-{experiments}.jpeg

        範例:
          Attitude-Trajectory-5-T-50-0.1-50-10-30-10-SWN-0.1-100-20.jpeg

        參數對應:
          pioneers    = no_of_pioneers       (int)
          clustered   = clustered_pioneers   (T/F)
          bc          = bounded_confidence   (int)
          cr          = convergence_rate     (float, 移除尾部零)
          avg_att     = avg_of_attitudes     (int)
          std_att     = std_of_attitudes     (int)
          avg_thresh  = avg_of_thresholds    (int)
          std_thresh  = std_of_thresholds    (int)
          network     = network_type         ("SFN" 或 "SWN"; "SWN/RN/CA" 縮寫為 "SWN")
          rewiring    = rewiring_probability (float, 移除尾部零)
          max_time    = max_time             (int)
          experiments = no_of_experiments    (int)
        """
        m = self.model

        # clustered_pioneers: True → "T", False → "F"
        clustered_str = "T" if m.clustered_pioneers else "F"

        # network_type: "SWN/RN/CA" → "SWN" (取斜線前第一段), "SFN" → "SFN"
        network_str = m.network_type.split("/")[0]

        # 浮點數格式: 移除尾部的零 (0.10 → "0.1", 1.0 → "1.0", 0.05 → "0.05")
        cr_str       = f"{m.convergence_rate:g}"
        rewiring_str = f"{m.rewiring_probability:g}"

        filename = (
            f"Attitude-Trajectory"
            f"-{m.no_of_pioneers}"
            f"-{clustered_str}"
            f"-{m.bounded_confidence}"
            f"-{cr_str}"
            f"-{m.avg_of_attitudes}"
            f"-{m.std_of_attitudes}"
            f"-{m.avg_of_thresholds}"
            f"-{m.std_of_thresholds}"
            f"-{network_str}"
            f"-{rewiring_str}"
            f"-{m.max_time}"
            f"-{m.no_of_experiments}"
            f".jpeg"
        )
        return filename

    def _run_simulation(self):
        """
        持續執行模擬直到 max-time 或手動停止

        對應 NetLogo 的持續執行模式 (Run 按鈕)

        模擬完成後自動保存:
          當模擬執行到 max-time 完成時 (非手動停止)，自動將 Attitude Trajectory
          圖表保存為高解析度 (dpi=300) 的 JPEG 圖片，檔名包含所有參數組合。

        效能最佳化:
          - 每 N 步更新一次圖表 (而非每步都更新)
          - 移除固定 20ms sleep，改為動態更新
          - 結束時強制更新一次確保最終狀態正確
        """
        self.running = True

        def _run():
            try:
                step_count = 0
                interval = self._PLOT_UPDATE_INTERVAL
                while (self.running
                       and self.model.current_time < self.model.max_time):
                    self.model.step()
                    step_count += 1

                    # 效能最佳化: 每 N 步才更新 GUI
                    if step_count % interval == 0:
                        self.after(0, self.visualizer.update_plots)
                        self.after(0, self._update_monitors)
                        time_module.sleep(0.01)  # 給 GUI 主線程時間處理

                # 最終更新: 確保最終狀態正確顯示
                self.after(0, self.visualizer.update_plots)
                self.after(0, self._update_monitors)

                # ─── 自動保存 Attitude Trajectory 高解析度圖片 ───
                # 僅在模擬完整執行到 max-time 時保存 (手動停止不保存)
                if self.model.current_time >= self.model.max_time:
                    filename = self._build_attitude_trajectory_filename()
                    self.visualizer.save_attitude_trajectory_hires(filename, dpi=300)

                self.running = False
                if self.stop_button:
                    self.after(0, self.stop_button.destroy)
                    self.stop_button = None
            except Exception as e:
                print(f"Simulation error: {e}")

        # 移除之前的 Stop 按鈕
        if self.stop_button:
            self.stop_button.destroy()

        # 建立 Stop 按鈕
        self.stop_button = ttk.Button(
            self, text="Stop",
            command=lambda: setattr(self, 'running', False)
        )
        self.stop_button.pack(side=tk.BOTTOM, pady=5)

        # 在新線程中執行模擬
        sim_thread = threading.Thread(target=_run, daemon=True)
        sim_thread.start()

    def _run_experiments(self):
        """
        執行批量實驗

        NetLogo 對應:
          BUTTON "Experiments" (40, 11, 142, 44)
          → run-100-experiments

        Python 實作:
          - 彈出目錄選擇對話框 (對應 NetLogo 的 user-directory)
          - 在新線程中執行實驗
          - 顯示進度條
        """
        output_dir = filedialog.askdirectory(title="Select experiment output directory")
        if not output_dir:
            return

        # 建立進度顯示
        progress_window = tk.Toplevel(self)
        progress_window.title("Running Experiments...")
        progress_window.geometry("300x100")

        progress_var = tk.DoubleVar()
        progress_label = ttk.Label(progress_window, text="Starting experiments...")
        progress_label.pack(pady=10)
        progress_bar = ttk.Progressbar(
            progress_window, variable=progress_var,
            maximum=self.model.no_of_experiments
        )
        progress_bar.pack(fill=tk.X, padx=20, pady=5)

        def progress_callback(exp_no):
            self.after(0, lambda: progress_var.set(exp_no))
            self.after(0, lambda: progress_label.config(
                text=f"Experiment {exp_no} / {self.model.no_of_experiments}"
            ))

        def _run():
            try:
                # 效能最佳化: 批量實驗模式確保不設定 step_callback
                # 這樣 go() 迴圈中不會觸發任何 GUI 更新
                saved_callback = self.model._step_callback
                self.model._step_callback = None

                self.model.run_experiments(output_dir, progress_callback)

                self.model._step_callback = saved_callback

                self.after(0, lambda: messagebox.showinfo(
                    "Experiments Complete",
                    f"Completed {self.model.no_of_experiments} experiments.\n"
                    f"Results saved to: {output_dir}"
                ))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror(
                    "Experiment Error", str(e)
                ))
            finally:
                self.after(0, progress_window.destroy)
                # 更新顯示為最後一次實驗的結果
                self.after(0, self.visualizer.update_plots)
                self.after(0, self._update_monitors)

        exp_thread = threading.Thread(target=_run, daemon=True)
        exp_thread.start()

    def _load_model(self):
        """
        載入已保存的模型狀態

        NetLogo 對應:
          BUTTON "Load" (780, 424, 843, 458)
          → import-simulation
          → clear-all; import-world user-file
        """
        filename = filedialog.askopenfilename(
            title="Select model file",
            filetypes=[("Pickle Files", "*.pkl"), ("All Files", "*.*")]
        )
        if not filename:
            return

        try:
            self.model.load_model_state(filename)
            self.visualizer.reset_plots()
            self.visualizer.update_plots()
            self._update_monitors()

            # 同步 GUI 控制元件的值 (對應載入後更新介面)
            self.pioneers_var.set(self.model.no_of_pioneers)
            self.clustered_var.set(self.model.clustered_pioneers)
            self.confidence_var.set(self.model.bounded_confidence)
            self.conv_rate_var.set(self.model.convergence_rate)
            self.avg_att_var.set(self.model.avg_of_attitudes)
            self.std_att_var.set(self.model.std_of_attitudes)
            self.avg_thres_var.set(self.model.avg_of_thresholds)
            self.std_thres_var.set(self.model.std_of_thresholds)
            self.network_var.set(self.model.network_type)
            self.rewiring_var.set(self.model.rewiring_probability)
            self.max_time_var.set(self.model.max_time)
            self.experiments_var.set(self.model.no_of_experiments)

            messagebox.showinfo("Load Complete", f"Model loaded from:\n{filename}")
        except Exception as e:
            messagebox.showerror("Load Error", str(e))


# =============================================================================
# 主程式入口
# =============================================================================
def main():
    """
    主程式入口

    NetLogo 對應:
      模型載入 → startup → setup → 顯示 Interface Tab
    """
    app = ModelGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
