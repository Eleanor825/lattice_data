<div align="right">
  <a href="./README.md">
    <img alt="English" src="https://img.shields.io/badge/English-2563eb?style=for-the-badge">
  </a>
  <a href="./README.zh-CN.md">
    <img alt="中文" src="https://img.shields.io/badge/中文-111827?style=for-the-badge">
  </a>
  <a href="./docs/README.md">
    <img alt="Docs" src="https://img.shields.io/badge/Docs-0f766e?style=for-the-badge">
  </a>
  <a href="./docs/demo.md">
    <img alt="Demo" src="https://img.shields.io/badge/Demo-7c3aed?style=for-the-badge">
  </a>
</div>

# Lattice

Lattice 是一个面向科学与材料领域的大模型数据与训练平台。它首先解决最具体、也最关键的问题：把分散的数据源整理成可追踪、可复用、可直接进入训练流程的数据资产。

它覆盖的数据与训练链路包括 pretraining、continued pretraining、fine-tuning 和 post-training，但仓库当前的重点仍然是把这条基础链路真正跑通并做扎实。

<p>
  <img src="./figures/phase1-phase2-roadmap.svg" alt="Lattice system architecture" width="100%">
</p>

## Lattice 在做什么

Lattice 试图把下面这条链路统一起来：

1. 接入异构科学数据源
2. 规范化成稳定的 schema
3. 跟踪 provenance、license 和 dedup
4. 编译成可复用训练视图
5. 支持本地或分布式执行
6. 连接到训练与优化工作流

## 当前范围

| 模块 | 状态 | 说明 |
|---|---|---|
| Phase 1 数据接入与编译 | ✅ 已实现 | source registry、adapter、normalization、filter、dedup、manifest |
| 开源科学/材料数据源覆盖 | ✅ 已实现 | OpenAlex、Crossref、arXiv、PubChem、OQMD、NOMAD、JARVIS、Wikidata、Europe PMC、Materials Cloud 等 |
| 本地执行 | ✅ 已实现 | local Python 和 pandas 路径 |
| 分布式执行 | ✅ 已实现 | Spark 和 Flink 本地 runtime 已验证 |
| Phase 2 训练工作流 | ✅ 已实现 | `pretrain`、`continue`、`finetune`、`posttrain` |
| Registry 与任务 API | ✅ 已实现 | run registry、异步提交、rerun、manifest sync |
| Workflow spec 执行 | ✅ 已实现 | 保存下来的 spec 可以直接复现或迁移到其他执行引擎 |
| 对话式 / 拖拽式界面 | ◐ 进行中 | 是产品方向，不是当前仓库的重点实现面 |

## 核心能力

| 能力 | 在当前仓库中的含义 |
|---|---|
| 多源数据接入 | 从 API、归档、网页资源和结构化数据库拉取数据 |
| 稳定 schema 边界 | 将原始输入转换成 `Document`、`StructuredRecord`、`KnowledgeRecord` 等类型 |
| 训练视图编译 | 输出 `pretrain`、`qa`、`instruction`、`knowledge` 视图 |
| 来源追踪与可审计性 | 输出 manifest、registry 记录和 workflow spec |
| 执行引擎可迁移 | 同一条数据准备逻辑可在 pandas、Spark、Flink 上运行 |
| 训练编排 | 支持本地参考训练和 provider-backed 的 Phase 2 工作流 |
| 可复现性 | 支持从 workflow spec 或 registry 中的旧任务直接复现 |

## 仓库结构

| 路径 | 用途 |
|---|---|
| `src/lattice/` | 平台源码 |
| `configs/` | source registry 和配置文件 |
| `examples/` | demo 数据和可运行样例 |
| `docs/` | 结构化文档、对比、demo 和研究材料 |
| `tests/` | 端到端和模块级测试 |
| `figures/` | README 与文档配图 |

## 快速开始

检查本地 runtime：

```bash
PYTHONPATH=src python3 -m lattice engine-check
```

运行一个小型 Phase 1 release：

```bash
PYTHONPATH=src python3 -m lattice phase1-run \
  --data-root outputs/phase1-demo \
  --registry configs/source_registry.json \
  --release-name materials-demo \
  --source openalex \
  --source pubchem \
  --compound "lithium iron phosphate" \
  --limit 1
```

运行一个 Phase 2 workflow：

```bash
PYTHONPATH=src python3 -m lattice phase2-run \
  --workflow finetune \
  --engine pandas \
  --input examples/training/demo_dataset \
  --output outputs/phase2-demo \
  --run-name finetune-demo \
  --model-backend local_tiny \
  --model-name tiny-local \
  --compiled-input
```

直接复现保存下来的 workflow spec：

```bash
PYTHONPATH=src python3 -m lattice run-spec \
  --spec outputs/phase2-demo/workflow_spec.json \
  --engine spark \
  --output outputs/phase2-demo-spark
```

从 registry 里重新提交旧任务：

```bash
PYTHONPATH=src python3 -m lattice run-rerun \
  --db outputs/platform/registry.db \
  --run-id <existing-run-id>
```

## 文档

详细内容已经从首页移到 `docs/`，首页只保留最关键的说明。

- [文档索引](./docs/README.md)
- [总览](./docs/overview.md)
- [Phase 1 流程](./docs/phase1.md)
- [训练工作流](./docs/training.md)
- [执行引擎说明](./docs/engines.md)
- [数据源目录](./docs/source-catalog.md)
- [平台对比](./docs/platform-comparison.md)
- [存储架构](./docs/storage_architecture.md)
- [Demo](./docs/demo.md)
- [研究材料](./docs/research/README.md)
- [更新记录](./CHANGELOG.md)

## 路线

- 继续扩充 Phase 1 的开源数据源覆盖和质量控制。
- 继续强化 Phase 2 的编排、registry 驱动执行和 provider adapter。
- 后续再把对话式和拖拽式工作流做成更清晰的产品层。

## 当前状态

仓库当前已经可以本地运行。现有测试覆盖了数据接入、执行引擎、训练工作流、registry sync、workflow replay 和 API rerun。
