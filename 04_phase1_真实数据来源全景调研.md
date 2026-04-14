# Phase 1 真实数据来源全景调研

## 1. 结论先行

如果 `Lattice Phase 1` 的目标是做一个 **materials/scientific domain data compiler**，那么“集成全部数据来源”不能理解为“一次性把所有数据全量镜像到本地”。更合理的定义是：

> **把 Phase 1 需要覆盖的真实数据生态全部建成 source adapters 和 source registry，并按开放性、价值、结构化程度和法务风险分层接入。**

也就是说，Phase 1 要做的是：

1. 建立一份**非常全面的 source registry**
2. 对每类 source 明确：
   - 能不能抓
   - 通过什么方式抓
   - 法务和 license 风险是什么
   - 应映射到哪类 schema
   - 在 Phase 1 里的优先级是什么
3. 先把 **P0 + P1** 做成真正可运行的 adapters
4. 对 **P2（受限/商业）** 只做 connector 设计，不默认抓取

## 2. Phase 1 应覆盖的 source 类别

从数据生态看，材料/科学领域 Phase 1 至少要覆盖 7 大类：

1. **学术发现与元数据源**
   - 用来发现论文、作者、期刊、DOI、机构、主题、open-access 状态
2. **论文/预印本全文源**
   - 用来抽正文、摘要、表格、图注、实验条件、知识片段
3. **结构化材料数据库**
   - 用来拿 crystal structure、DFT 属性、材料性质、实验测量
4. **实验/模拟数据仓库**
   - 用来拿原始数据包、补充材料、dataset-level metadata
5. **开放知识与教育资源**
   - 用来补背景知识、定义、教材化解释、标准术语
6. **专利与技术情报源**
   - 用来补工业信息、工艺路线、配方、应用和 prior art
7. **受限/商业数据库**
   - 价值很高，但默认不能直接纳入开源抓取管线

## 3. 推荐的 Phase 1 分层策略

### P0：必须优先集成

这些是 Phase 1 的核心来源，必须优先做 adapter：

- OpenAlex
- Crossref
- arXiv
- Materials Project
- MPContribs
- OQMD
- NOMAD
- JARVIS
- COD
- PubChem
- NIST Chemistry WebBook
- USPTO PatentsView
- Lens
- Wikidata
- Wikipedia dumps

### P1：强烈建议在 Phase 1 后半段补齐

- AFLOW / AFLUX
- Materials Cloud Archive
- Materials Data Facility (MDF)
- Open Catalyst Project
- Catalysis-Hub
- Battery Archive
- NIST Materials Data Repository
- CORE
- Europe PMC / PubMed / PMC（用于跨到 chemistry / biomaterials / energy 时）
- ChemLibreTexts
- MIT OpenCourseWare
- NPTEL
- WIPO PATENTSCOPE
- EPO OPS / Espacenet
- Open Reaction Database

### P2：Phase 1 设计 connector，但不开源默认抓取

- ICSD
- CSD
- MPDS
- MatWeb
- SpringerMaterials
- Reaxys / SciFinder 一类商业库

原因不是它们不重要，而是：

- 许可证限制
- 访问方式受限
- 很多需要机构订阅
- 不适合直接纳入开源 repo 的默认 pipeline

## 4. Source 全景表

下面这张表是给 `Lattice Phase 1` 真正可执行用的，不是泛泛的“相关网站列表”。

| Source | 类别 | 主要内容 | 官方访问方式 | 开放性/限制 | 推荐优先级 | 适合映射到 |
|---|---|---|---|---|---|---|
| OpenAlex | 学术元数据 | works/authors/sources/institutions/topics | REST API + data downloads | 开放，API key 免费 | P0 | `Document` / metadata index |
| Crossref | 学术元数据 | DOI metadata、license、funding、abstract、relations | REST API | 公开；大多数 metadata 可自由使用，abstract 需谨慎 | P0 | `Document` / provenance |
| arXiv | 预印本 | 论文 metadata、全文、源文件、S3/full-text 管线 | public API + bulk/full-text pipelines | 开放；需遵守 API ToU 和品牌规则 | P0 | `Document` |
| CORE | OA 聚合 | 聚合 open access 论文和仓储内容 | CORE API | 开放但需遵守其 API 条款 | P1 | `Document` |
| Europe PMC | 学术/生物医学聚合 | publications、annotations、部分 full text、patent links | REST API | 开放，偏 biomedical | P1 | `Document` / `KnowledgeRecord` |
| PubMed / PMC | 生物医学论文 | abstracts / PMC OA full text | NCBI E-utilities | 开放 API，但覆盖偏 biomedical | P1 | `Document` |
| Materials Project | 结构化材料库 | inorganic materials properties、phase data、API、AWS Open Data | official API + docs + AWS | 公开，需按官方 API 使用 | P0 | `StructuredRecord` / `KnowledgeRecord` |
| MPContribs | MP contributed data | 实验和计算社区贡献数据、DOI-backed projects | platform + API + python client | 开放但项目级别可能有发布状态差异 | P0 | `StructuredRecord` / attachments |
| OQMD | 结构化材料库 | 140 万+ DFT thermodynamic/structural properties | site + REST/OPTIMADE API + download | CC-BY 4.0 | P0 | `StructuredRecord` |
| NOMAD | 材料数据基础设施 | heterogenous materials data、rich metadata、processed data | web + APIs | CC-BY 4.0；free/open source | P0 | `StructuredRecord` / `Document` / provenance |
| AFLOW / AFLUX | 材料结构化库 | large-scale materials properties, REST/AFLUX query | REST/AFLUX | 开放，但要按 API 设计访问 | P1 | `StructuredRecord` |
| JARVIS | NIST 材料基础设施 | DFT/FF/QETB/ChemNLP/battery/interface/leaderboard | site + datasets + OPTIMADE + tools | 免费注册；数据库与下载能力强 | P0 | `StructuredRecord` / `Document` |
| COD | 晶体结构库 | organic/inorganic/metal-organic/mineral crystal structures | web + mirrors + dumps | CC0 / public domain | P0 | `StructuredRecord` |
| Materials Cloud Archive | 研究数据归档 | computational materials archive records, metadata, bundles | archive pages + DOI records | 开放，但记录级差异大 | P1 | `StructuredRecord` / `Document` |
| Materials Data Facility (MDF) | 数据仓库 | curated materials datasets, ML-ready datasets, DOI-backed | discover/publish + Foundry ML | 开放，数据集级差异大 | P1 | `StructuredRecord` / dataset manifests |
| NIST Materials Data Repository | 数据仓库 | open materials research datasets and metadata | repository portal | 开放社区导向 | P1 | `StructuredRecord` / bundles |
| NIST Chemistry WebBook | 化学/物性 | chemical & physical property data for species and reactions | web resource | 官方数据资源；结构化程度中等 | P0 | `StructuredRecord` / `KnowledgeRecord` |
| PubChem | 化学结构/属性 | compounds, properties, synonyms, identifiers | PUG REST | 开放、程序化访问成熟 | P0 | `StructuredRecord` / `KnowledgeRecord` |
| Open Reaction Database | 反应数据 | machine-readable reaction data | docs + repository | 开放 | P1 | `StructuredRecord` / `InstructionTrace` |
| Open Catalyst Project | 催化数据 | OC20/OC22, relaxations, DFT calc outputs | dataset downloads + code | 开放；大规模 | P1 | `StructuredRecord` |
| Catalysis-Hub | 催化表面反应 | surface reaction database | web platform | 开放，但接口使用要额外核对 | P1 | `StructuredRecord` / `KnowledgeRecord` |
| Battery Archive | 电池实验数据 | cycling / disruptive tests / comparison views | website + full CSV by request | 开放展示，完整 CSV 需联系获取 | P1 | `StructuredRecord` |
| Wikidata | 开放知识图谱 | entity / property / relation / identifiers | dumps + query/API ecosystem | structured data CC0 | P0 | `KnowledgeRecord` |
| Wikipedia dumps | 开放百科文本 | encyclopedia-style explanatory text | official dumps | 文本通常 CC BY-SA；要处理 attribution 和 exceptions | P0 | `Document` |
| ChemLibreTexts | 开放教材/百科 | chemistry textbooks and learning objects | web pages / PDFs | 多数页面开源，但以页级 license 为准 | P1 | `Document` |
| MIT OpenCourseWare | 课程资料 | lecture notes, assignments, course texts | OCW site | openly-licensed collection；按课程核对条款 | P1 | `Document` |
| NPTEL | 课程资料 | engineering/materials courses, lecture material | NPTEL course pages | 公开访问，但 license 需逐课程核对 | P1 | `Document` |
| USPTO PatentsView | 美国专利研究数据 | disambiguated patents, pre-grants, long text | USPTO ODP downloads/API | 公开，研究友好 | P0 | `Document` / `StructuredRecord` |
| USPTO BSD / ODP | 美国专利官方检索/批量接口 | published apps and grants | API / bulk interfaces | 公开，但新 API key/portal rules需遵守 | P1 | `Document` |
| Lens | 专利+学术 | patent + scholarly search, APIs | Lens API | trial/custom access，token 管理 | P0 | `Document` / linkage graph |
| WIPO PATENTSCOPE | 国际专利 | global patent documents incl. PCT | search interface / related APIs | 覆盖广；程序化使用需遵循条款 | P1 | `Document` |
| Espacenet / EPO OPS | 欧洲及全球专利 | patent search, classification, citations, dossiers | Espacenet UI + OPS for automation | Espacenet 本身不支持 bulk robots；自动化应走 OPS | P1 | `Document` / metadata |
| ICSD | 商业/高价值 | high-quality inorganic crystal structures | licensed web/database access | 付费/机构订阅 | P2 | `StructuredRecord` |
| CSD | 商业/高价值 | curated organic/metal-organic crystal structures | CCDC services | 访问受条款约束 | P2 | `StructuredRecord` |
| MPDS | 商业/高价值 | materials ontology and databases | platform | 非完全开放 | P2 | `StructuredRecord` |
| MatWeb | 工程材料性质 | material datasheets across metals/polymers/ceramics | website | 非开放 bulk source | P2 | `StructuredRecord` |
| OpenStax Chemistry | 教材 | chemistry textbook | website | **不建议默认纳入**：页面明确写明不得在未经许可的情况下用于 LLM 训练/摄取 | Exclude by default | `Document` |

## 5. 各类 source 的接入意义

### A. 学术发现与元数据层

这一层不是拿来训模型正文的，而是做：

- 去重
- DOI / arXiv / PMID / patent 之间的对齐
- 找 open-access 全文
- 找 license
- 建 citation graph
- 建 source provenance

**核心来源：**

- OpenAlex
- Crossref
- arXiv
- CORE
- Europe PMC / PubMed（按需要）

### B. 论文与预印本文本层

这一层用于生成：

- `Document`
- `InstructionTrace`
- `KnowledgeRecord`

主要内容包括：

- 标题
- 摘要
- 正文段落
- 图表说明
- 材料名称 / 配方 / 性质 / 条件 / 结论

**核心来源：**

- arXiv
- CORE
- JARVIS-ChemNLP
- Materials Cloud Archive records
- 部分开放网页与课程资料

### C. 结构化材料数据层

这是 Phase 1 最重要的高价值层。

原因是：

- 结构化程度高
- 易映射到统一 schema
- 直接支撑 `KnowledgeRecord` 和 `StructuredRecord`
- 对后续训练收益最有可能产生稳定贡献

**核心来源：**

- Materials Project
- MPContribs
- OQMD
- NOMAD
- JARVIS
- COD
- PubChem
- NIST WebBook

### D. 实验/仓储/补充数据层

这一层用于：

- 接补充材料
- 接原始实验曲线
- 接 dataset-level files
- 建 provenance-rich archives

**核心来源：**

- MDF
- Materials Cloud Archive
- NIST Materials Data Repository
- Battery Archive
- Open Catalyst
- Catalysis-Hub
- ORD

### E. 专利与技术情报层

这层对 `materials + battery + synthesis + manufacturing` 尤其重要。

优点：

- 产业信息密度高
- 工艺和配方细节多
- 很多内容比论文更靠近应用

但难点也明显：

- OCR / layout 更复杂
- 专利语言冗长
- 国别和格式不统一

**建议的 Phase 1 做法：**

- 先接 metadata / abstract / claims / CPC / citations
- 暂时不要把专利全文解析作为第一优先级

**核心来源：**

- USPTO PatentsView
- Lens
- PATENTSCOPE
- EPO OPS

## 6. 每类 source 的法务和工程风险

### 6.1 可以优先开源接入的

- OpenAlex
- Crossref metadata
- arXiv
- Materials Project
- MPContribs
- OQMD
- NOMAD
- JARVIS
- COD
- PubChem
- Wikidata
- USPTO PatentsView

这些来源的共同特点是：

- 官方提供 API / dump / open portal
- 公开复用路径明确
- 有清晰 metadata/provenance

### 6.2 可以接，但要逐条核对条款的

- CORE
- Materials Cloud Archive
- MDF
- ChemLibreTexts
- MIT OCW
- NPTEL
- PATENTSCOPE
- EPO OPS
- Battery Archive

风险点通常是：

- 使用条款不完全统一
- 页面级或记录级 license 差异较大
- 允许浏览/下载，但不等于允许大规模训练摄取

### 6.3 不应默认纳入开源抓取管线的

- ICSD
- CSD
- MPDS
- MatWeb
- SpringerMaterials
- Reaxys / SciFinder

原因：

- 商业订阅
- 许可受限
- 不能在公开 repo 里默认抓取或再分发

### 6.4 明确应谨慎对待的

**OpenStax**

OpenStax 的官方页面对 `Chemistry 2e` 明确给出限制：虽然书本是 CC BY，但页面同时声明**未经许可不得用于 LLM 训练或被 generative AI 摄取**。因此：

- 不要把 OpenStax 默认放进 Phase 1 开源训练数据管线
- 如果后续确实需要，必须先单独法务确认

**Espacenet**

Espacenet 官方说明它**不支持 robots 的 bulk automated searches**。因此：

- 不要直接对 Espacenet 做爬虫
- 自动化接入应改用 **EPO OPS**

## 7. 对 Lattice 的 schema 映射建议

### `Document`

适合来源：

- arXiv
- CORE
- JARVIS-ChemNLP
- Wikipedia
- ChemLibreTexts
- MIT OCW
- NPTEL
- patent abstracts / descriptions

### `StructuredRecord`

适合来源：

- Materials Project
- MPContribs
- OQMD
- NOMAD
- AFLOW
- JARVIS
- COD
- PubChem
- NIST WebBook
- Battery Archive
- ORD
- Open Catalyst

### `KnowledgeRecord`

适合来源：

- Wikidata
- extracted triples from papers
- property tables from materials DBs
- claims / evidence from patents

### `InstructionTrace`

适合来源：

- protocols / procedures / tutorials
- chemistry/materials educational content
- reaction steps
- benchmark tasks transformed into instruction format

## 8. 我建议的 Phase 1 集成顺序

### Stage 0：先做 source registry

先不要直接开抓，先把一张统一清单定下来，字段至少包括：

- `source_name`
- `category`
- `official_url`
- `access_mode`
- `license_status`
- `priority`
- `schema_targets`
- `rate_limit_or_auth`
- `redistribution_risk`
- `notes`

### Stage 1：先接 P0 的 metadata + structured open sources

第一批建议：

- OpenAlex
- Crossref
- arXiv
- Materials Project
- MPContribs
- OQMD
- NOMAD
- JARVIS
- COD
- PubChem
- NIST WebBook
- PatentsView
- Lens
- Wikidata

这一步就足够做出：

- 论文/材料/专利的统一 ID 图谱
- 高质量 `StructuredRecord`
- 第一版 `KnowledgeRecord`
- 可复现 provenance

### Stage 2：补 P1 的 archive / education / patent-global sources

第二批建议：

- AFLOW
- Materials Cloud
- MDF
- Open Catalyst
- Catalysis-Hub
- Battery Archive
- NIST MDR
- ChemLibreTexts
- MIT OCW
- NPTEL
- PATENTSCOPE
- EPO OPS
- CORE
- Europe PMC
- ORD

### Stage 3：为 P2 做 connector 设计

这一步只做：

- source adapter interface
- auth placeholder
- license gate
- no-op / disabled-by-default config

不要在开源默认配置中实际抓取：

- ICSD
- CSD
- MPDS
- MatWeb
- 其他商业数据库

## 9. 你们现在最该做什么

如果目标是“Phase 1 做全”，我建议不是再继续讨论抽象 idea，而是立刻落三件事：

### 1. 建 `sources.yaml`

把上面这份清单变成机器可读 registry。

### 2. 先写 8-10 个 P0 adapters

优先顺序：

1. OpenAlex
2. Crossref
3. arXiv
4. Materials Project
5. OQMD
6. NOMAD
7. JARVIS
8. COD
9. PubChem
10. PatentsView

### 3. 先做统一 provenance + license gate

任何数据进系统时都要记录：

- 来源
- 官方 URL
- 获取方式
- 时间
- 许可证状态
- 是否允许再分发
- 是否允许训练

没有这一步，后面数据越多，风险越大。

## 10. 最终判断

如果你问我：

> Phase 1 的真实数据来源到底能不能做得“非常完整”？

答案是：

**可以，而且应该做得很完整，但要通过“source registry + adapters + license tiers”的方式来完整，而不是通过“盲目全量爬取”来完整。**

最重要的不是把所有网站都 scrape 一遍，而是：

- 先把数据生态看全
- 把开放层、灰色层、商业层分清
- 让每个 source 都有明确接入策略

这样 `Lattice` 才会像一个真正的数据操作系统，而不是一组临时脚本。

## 11. 官方来源链接

### 学术元数据与全文

- OpenAlex API: https://developers.openalex.org/api-reference/introduction
- Crossref REST API: https://www.crossref.org/documentation/retrieve-metadata/rest-api/
- arXiv API access: https://info.arxiv.org/help/api/index.html
- CORE API: https://core.ac.uk/services/api
- Europe PMC REST service: https://europepmc.org/RestfulWebService
- NCBI APIs / E-utilities: https://www.ncbi.nlm.nih.gov/home/develop/api/

### 材料数据库与仓库

- Materials Project docs: https://docs.materialsproject.org/
- MPContribs: https://docs.materialsproject.org/services/mpcontribs
- OQMD: https://oqmd.org/
- NOMAD: https://nomad-lab.eu/nomad-lab/
- AFLOW: https://aflowlib.org/
- JARVIS: https://jarvis.nist.gov/
- COD: https://crystallography.net/cod/
- Materials Cloud Archive: https://archive.materialscloud.org/information
- Materials Data Facility: https://www.materialsdatafacility.org/
- NIST Materials Data Repository: https://materialsdata.nist.gov/
- PubChem PUG REST: https://pubchem.ncbi.nlm.nih.gov/docs/pug-rest
- NIST Chemistry WebBook: https://webbook.nist.gov/
- Open Reaction Database: https://docs.open-reaction-database.org/en/latest/overview.html
- Open Catalyst Project: https://opencatalystproject.org/
- Catalysis-Hub: https://www.catalysis-hub.org/
- Battery Archive: https://batteryarchive.org/

### 知识与教育资源

- Wikidata dump docs: https://www.wikidata.org/wiki/Wikidata:Database_download
- Wikimedia dumps licensing: https://dumps.wikimedia.org/legal.html
- Chemistry LibreTexts: https://chem.libretexts.org/
- MIT OpenCourseWare: https://ocw.mit.edu/index.html
- NPTEL: https://nptel.ac.in/
- OpenStax Chemistry 2e: https://openstax.org/books/chemistry-2e/pages/1-introduction

### 专利

- USPTO PatentsView: https://www.uspto.gov/ip-policy/economic-research/patentsview
- USPTO BSD / bulk API overview: https://data.commerce.gov/bulk-search-and-download-bsd-api-version-100
- Lens Patent & Scholar API: https://support.lens.org/knowledge-base/lens-patent-and-scholar-api/
- WIPO PATENTSCOPE: https://www.wipo.int/en/web/patentscope/index
- Espacenet / EPO: https://www.epo.org/en/searching-for-patents/technical/espacenet

### 受限/商业（仅 connector）

- ICSD: https://icsd.products.fiz-karlsruhe.de/
- CCDC / CSD: https://support.ccdc.cam.ac.uk/support/solutions/articles/103000306360/
- MPDS: https://mpds.io/
- MatWeb: https://www.matweb.com/
