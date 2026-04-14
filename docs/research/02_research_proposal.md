# Research Proposal

## Title

**Lattice: 面向基础模型训练的数据价值建模与自动数据组合优化框架**

## 0. Executive Summary

本项目拟研究一个以数据为中心的 foundation model 基础设施与方法框架。核心问题不是“如何做一个更炫的 agent”，而是：**能否把异构原始信息自动转化为可训练的数据对象，并在给定任务与算力预算下，自动决定哪些数据最有价值、应如何组合、以及如何被喂给模型。**

项目的主假设是：相较于只做启发式清洗或静态人工配比，若我们为数据建立统一 schema、任务条件下的数据价值表示、以及基于代理实验的 mixture/curriculum 优化器，则可以在相同预算下显著提高模型训练效率和下游表现。

## 1. Problem Anchor

### Bottom-line problem

大模型训练的主要瓶颈正在从“有没有数据”转向“哪些数据值得训练、以什么方式训练”。当前数据构建和训练配比大多依赖经验规则，缺乏统一表示、统一价值度量和统一优化框架。

### Must-solve bottleneck

现有流程通常把以下几个环节割裂处理：

- 数据抽取与结构化
- 数据质量过滤
- 数据价值判断
- 数据 mixture 选择
- 训练顺序与 feeding strategy

这导致训练数据的使用高度 heuristic，难以复现，也难以在固定预算下达到最优。

### Non-goals

- 不把“做一个 agent”本身作为核心研究贡献
- 不试图提出适用于所有任务和所有模态的完美统一公式
- 不把整件事做成一个过度复杂的大而全系统

### Constraints

- 需要先在单一清晰场景下验证，例如 domain-adaptive pretraining 或 targeted post-training
- 需要允许异构数据进入系统，但论文主贡献必须集中
- 需要控制实验预算，避免全量大模型反复试错

### Success condition

如果在固定 token / compute 预算下，Lattice 自动选择的数据组合与训练顺序，能够稳定优于：

- 随机采样
- 统一混合
- 传统启发式过滤
- 单点数据选择或单点 mixture reweighting 方法

则可以说明项目抓住了真实瓶颈。

## 2. Motivation

导师的核心判断是正确的：在不重新设计底层模型架构的前提下，**数据质量直接决定 from-scratch training、continued pretraining 和 fine-tuning 的上限**。近两年的公开工作也支持这一点：

- DoReMi 说明仅通过优化 domain mixture，就能显著提高预训练效率。
- DataComp-LM、FineWeb、Dolma 说明高质量开源数据集与可复现实验管线本身就是竞争力。
- LESS、Data Advisor 说明针对性数据选择和动态数据策划可以远胜于“多多益善”。
- Data Shapley / DATE-LM 则说明“数据贡献度量”虽然重要，但仍然远未成熟。

换言之，领域里已经看到了“数据很重要”，但还没有把“数据如何被统一表示、统一量化、统一优化”变成一个完整范式。

## 3. Related Work and Gap

### 3.1 现有工作做到了什么

| 方向 | 代表工作 | 关键贡献 | 局限 |
|---|---|---|---|
| 开源数据管线 | Data-Juicer (2023), Data-Juicer 2.0 (2024), DataTrove, Dolma, FineWeb | 提供大规模处理、过滤、去重、构建数据集的工程框架 | 更偏系统与 recipe，缺乏统一“数据价值”理论 |
| 数据集构建 | Dolma (2024), FineWeb (2024), FineWeb2 (2025), DataComp-LM (2024) | 证明公开高质量数据可显著提升预训练效果 | 主要回答“怎么构”，较少回答“为什么这类数据更值钱、如何自动适配任务” |
| 数据选择 | LESS (ICML 2024), Data Advisor (EMNLP 2024) | 证明 targeted selection / dynamic curation 有效 | 通常局限于 instruction tuning、alignment 或特定场景 |
| mixture 优化 | DoReMi (2023), RegMix (2024) | 证明 data mixture 可以被自动优化 | 多针对已有 domain mixture，未统一到跨 schema、跨来源、跨阶段场景 |
| 数据价值度量 | Data Shapley in One Training Run (2024), DATE-LM (2025) | 推进可扩展 attribution，并指出评估仍不成熟 | 还不足以直接成为通用数据操作系统的核心决策器 |
| 小规模代理决策 | DataDecide (2025) | 说明小模型/小预算实验能较可靠预测大规模数据选择结果 | 更像评估套件，尚未形成端到端自动数据优化框架 |

### 3.2 核心缺口

当前仍缺三件事同时成立的方案：

1. **统一表示**  
   异构数据缺少 minimal schema family，导致后续价值评估和组合优化难以通用化。

2. **任务条件下的数据价值建模**  
   现有指标往往只看质量、相似度或 attribution 的某一面，缺少将质量、信息密度、任务相关性、覆盖性、可学习性联合起来的表示。

3. **从价值到策略的闭环优化**  
   现在多数方法要么做过滤，要么做重加权，要么做 curriculum，缺少一个统一框架把“选什么数据、配比多少、按何顺序、是否合成”一起优化。

## 4. Central Research Question

> 在给定任务目标和资源预算下，能否将异构数据映射到统一 schema，并学习一个任务条件下的数据价值表示，从而自动完成数据筛选、数据配比、数据合成和训练 feeding strategy 的联合优化？

## 5. Proposed Thesis

### One-sentence thesis

**Lattice 将训练数据建模为带有统一 schema 与价值向量的可操作对象，并通过代理实验驱动的组合优化器，自动生成最适合目标任务的数据 mixture 与 feeding schedule。**

### Dominant contribution

提出一个**任务条件下的数据价值建模 + 自动 mixture/curriculum 优化**框架，使训练数据选择从 heuristic 走向可计算决策。

### Supporting contribution

构建一个能够承载该研究的**minimal schema + reproducible data library**，使异构数据的抽取、清洗、重写、结构化和追踪具有统一接口。

## 6. Method

### 6.1 Lattice-Schema: 最小可覆盖数据模式族

我们不追求一个万能 schema，而是定义一组最小模式族：

- `Document`: 原始文本或段落级语料
- `InstructionTrace`: 指令-回答-工具/推理轨迹
- `KnowledgeRecord`: 实体-属性-关系-来源证据
- `StructuredRecord`: 表格、JSON、数据库记录
- `PairedMultimodalRecord`: 图文、音文、视频文等配对样本

每个样本除原始内容外，还带统一 metadata：

- source
- timestamp
- license / provenance
- domain
- schema type
- difficulty / length / structure stats
- dedup id
- quality/value annotations

这一步是整个系统的接口层，不主张在论文中把 schema 本身作为主要 novelty claim，但它是后续价值建模的必要前提。

### 6.2 Lattice-Value: 任务条件下的数据价值表示

对每个样本或数据簇，定义一个任务条件下的价值向量：

\[
v(x \mid \tau) = [q(x), n(x), c(x,\tau), d(x), \ell(x,\tau), s(x)]
\]

其中：

- `q(x)`: quality，文本/结构完整性、噪声度、可解析性
- `n(x)`: novelty / non-redundancy，相对已有数据的增量信息
- `c(x, τ)`: task affinity，和目标任务 `τ` 的相关性
- `d(x)`: diversity / coverage，对整体语料覆盖面的贡献
- `ℓ(x, τ)`: learnability / utility，对目标模型在当前阶段是否“学得动”
- `s(x)`: safety / license / trustworthiness

“知识密度”不直接作为单一神秘分数，而是作为上述多个量的组合结果来建模。这样更稳健，也更容易实验验证。

### 6.3 Lattice-Proxy: 用小规模代理实验校准价值

单靠静态打分很难可靠预测大模型收益，因此我们引入代理实验：

- 在小模型或小 token budget 上跑快速训练
- 估计数据簇 / mixture 的边际收益
- 学习从 `value vector -> expected downstream gain` 的映射

这一步借鉴了 DataDecide 的思想，但目标不是只做 benchmark，而是把代理实验嵌入自动优化闭环。

### 6.4 Lattice-Mix: 联合优化数据子集、配比与训练顺序

定义优化目标：

\[
\max_{\mathcal{S}, \alpha, \pi} \; U(M_{\tau}; \mathcal{S}, \alpha, \pi)
\quad \text{s.t.} \quad
\text{cost}(\mathcal{S}, \alpha, \pi) \le B
\]

其中：

- `S` 是被选中的数据子集或数据簇
- `α` 是各类数据 mixture proportion
- `π` 是 feeding / curriculum strategy
- `B` 是预算约束

候选优化技术：

- 多目标 Bayesian optimization
- bandit / successive halving
- offline RL / learning-to-rank over mixtures
- bilevel optimization with proxy feedback

论文的主方法应控制在一个清晰实现上，建议优先选：

**value-aware mixture search + stage-wise curriculum optimization**

这样贡献更聚焦，风险也更低。

### 6.5 Lattice-Agent: 自动化编排层

Agent 负责：

- 调度抓取、解析、过滤、抽取、重写
- 自动选择对应 schema pipeline
- 触发代理实验与优化搜索

但在论文叙事中，它只作为 orchestration layer，不作为核心 novelty。

## 7. Hypotheses

### H1

任务条件下的多维数据价值表示，比单一质量分数或启发式过滤更能预测真实训练收益。

### H2

基于代理实验校准的 mixture/curriculum 优化，在相同预算下优于静态 uniform mix、经验配比和单轮数据过滤。

### H3

最小 schema family 足以覆盖主要训练数据形态，并支持自动化 pipeline，而不会显著牺牲性能。

## 8. Experimental Plan

### 8.1 推荐的首个落地场景

为了降低复杂度，第一阶段建议聚焦到一个清楚、数据价值差异明显的场景：

**Option A: 面向材料/科学领域的 continued pretraining**  
数据来源包括论文、教材、百科、专利、领域网站和结构化数据库。

**Option B: 面向推理/技术问答能力的 targeted post-training**  
数据来源包括 instruction 数据、工具使用轨迹、技术文档、问答社区与高密度知识片段。

如果你要快速做出第一篇论文，我更建议 **Option A**，因为：

- 导师已经用材料领域举例，问题更贴近真实需求
- 垂域数据异构性更强，Lattice 的价值更容易体现
- 更适合同时沉淀“数据资产库”

### 8.2 Core experiment blocks

#### Block 1: Main anchor result

- 问题：自动数据组合是否真的优于人工/静态数据配比？
- 比较：
  - uniform mix
  - heuristic quality filtering
  - DoReMi/RegMix 风格 mixture baseline
  - Lattice
- 指标：
  - domain benchmark accuracy / F1
  - held-out perplexity
  - token efficiency / compute efficiency

#### Block 2: Value model necessity

- 问题：提升是否来自真正的数据价值建模，而不是更复杂的工程？
- 比较：
  - only quality filter
  - only task similarity
  - no proxy calibration
  - full Lattice-Value

#### Block 3: Curriculum / feeding strategy

- 问题：训练顺序是否重要？
- 比较：
  - static mix
  - two-stage curriculum
  - adaptive schedule

#### Block 4: Schema ablation

- 问题：统一 schema 是否真的帮助自动化和复用？
- 指标：
  - pipeline coverage
  - failure rate
  - engineering overhead
  - downstream performance impact

### 8.3 Evaluation principle

要避免“大模型全量重训很多次”。推荐策略：

- 用小模型做 mixture search
- 在 1-2 个最终 setting 上做中等规模验证
- 只把最关键的候选带到较大模型验证

## 9. Deliverables

### Research deliverables

- 一个任务条件下的数据价值 formalization
- 一个可复现的自动 mixture/curriculum optimizer
- 一组验证数据价值与训练收益关系的实验

### System deliverables

- 一个最小 schema family
- 一个数据处理 library / pipeline
- 一个可追踪的数据资产仓库

### Community deliverables

- 一个面向垂域数据的公开入口或 Hub
- 数据卡、处理 recipe、实验日志

## 10. Work Packages and Timeline

### WP1. Problem scoping and schema design (2-3 weeks)

- 选定首个应用场景
- 定义 minimal schema family
- 定义 metadata 与 provenance 标准

### WP2. Data pipeline and asset construction (3-5 weeks)

- 接入 3-5 类数据源
- 完成抓取、解析、去重、结构化、追踪
- 形成第一版垂域数据池

### WP3. Value modeling (4-6 weeks)

- 设计 value vector
- 建立 proxy tasks
- 训练价值预测/排序模型

### WP4. Mixture/curriculum optimization (4-6 weeks)

- 建立搜索空间
- 跑小规模代理实验
- 定义 stop/go 规则

### WP5. Final validation and paper writing (4 weeks)

- 固定最终方法
- 产出主结果与关键 ablation
- 撰写论文与系统文档

## 11. Risks and Mitigations

### Risk 1: “知识密度”太抽象，难以直接定义

Mitigation:

- 不把它当作单一标量硬定义
- 用多维 value vector 分解成可观测量

### Risk 2: 代理实验与大模型真实收益不一致

Mitigation:

- 用多种 proxy 指标校准
- 做少量高价值最终验证
- 将误差本身作为研究对象

### Risk 3: 系统做得太大，论文主线发散

Mitigation:

- 论文只 claim 一个主贡献：value-aware data optimization
- schema/library 作为 supporting system contribution

### Risk 4: 垂域 benchmark 不够成熟

Mitigation:

- 结合公开 benchmark 与自建 evaluation slices
- 同时报告 token efficiency、perplexity、task metrics

## 12. Why This Proposal Fits the Mentor's Intent

这版 proposal 刻意遵循了导师的三条底线：

1. **数据是核心，不是 agent。**
2. **要从 heuristic 走向 formalization。**
3. **要同时沉淀数据资产、数据工具和可发表的研究问题。**

## 13. Suggested Short Pitch

可以把项目对外描述为：

> **Lattice 是一个面向 foundation model 的 data-centric framework。它把异构原始信息转成统一数据对象，并通过任务条件下的数据价值建模，自动完成数据筛选、组合与训练喂养策略优化，从而在固定预算下最大化模型收益。**

## 14. Selected References

1. DoReMi: Optimizing Data Mixtures Speeds Up Language Model Pretraining, 2023.  
   https://arxiv.org/abs/2305.10429

2. Data-Juicer: A One-Stop Data Processing System for Large Language Models, 2023.  
   https://arxiv.org/abs/2309.02033

3. Dolma: an Open Corpus of Three Trillion Tokens for Language Model Pretraining Research, 2024.  
   https://arxiv.org/abs/2402.00159

4. LESS: Selecting Influential Data for Targeted Instruction Tuning, ICML 2024.  
   https://proceedings.mlr.press/v235/xia24c.html

5. DataComp-LM: In Search of the Next Generation of Training Sets for Language Models, 2024.  
   https://arxiv.org/abs/2406.11794

6. The FineWeb Datasets: Decanting the Web for the Finest Text Data at Scale, NeurIPS 2024 Datasets and Benchmarks.  
   https://arxiv.org/abs/2406.17557

7. Data Shapley in One Training Run, 2024.  
   https://arxiv.org/abs/2406.11011

8. Data Advisor: Dynamic Data Curation for Safety Alignment of Large Language Models, EMNLP 2024.  
   https://aclanthology.org/2024.emnlp-main.461/

9. RegMix: Data Mixture as Regression for Language Model Pre-training, 2024.  
   https://arxiv.org/abs/2407.01492

10. Data-Juicer 2.0: Cloud-Scale Adaptive Data Processing for Foundation Models, 2024.  
    https://arxiv.org/abs/2501.14755

11. FineWeb2: One Pipeline to Scale Them All -- Adapting Pre-Training Data Processing to Every Language, 2025.  
    https://arxiv.org/abs/2506.20920

12. DataDecide: How to Predict Best Pretraining Data with Small Experiments, 2025.  
    https://arxiv.org/abs/2504.11393

13. DATE-LM: Benchmarking Data Attribution Evaluation for Large Language Models, 2025.  
    https://arxiv.org/abs/2507.09424
