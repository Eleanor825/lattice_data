# Source Catalog

## Source Registry Snapshot

This table summarizes the current open-source source coverage and how each source maps into Lattice.

| Source | Category | Access | Priority | Status | Main Use | Schema Targets |
|---|---|---|---|---|---|---|
| OpenAlex | Scholarly metadata | REST API | P0 | Implemented | work discovery, paper metadata, provenance | `Document` |
| Crossref | Scholarly metadata | REST API | P0 | Implemented | DOI metadata, metadata enrichment, provenance | `Document` |
| arXiv | Preprints / papers | API + bulk | P0 | Implemented | abstracts and paper text | `Document` |
| Materials Project | Structured materials DB | API | P0 | Implemented, API-key gated | material properties and summaries | `StructuredRecord`, `KnowledgeRecord` |
| MPContribs | Materials contributed data | platform / API | P0 | Registry only | contributed experiments and project data | `StructuredRecord` |
| OQMD | Structured materials DB | API / download | P0 | Implemented | crystal and DFT properties | `StructuredRecord` |
| NOMAD | Materials repository | API | P0 | Implemented | materials entries and repository metadata | `StructuredRecord`, `Document` |
| AFLOW | Structured materials DB | REST / AFLUX | P1 | Connector-ready | large-scale materials properties | `StructuredRecord` |
| JARVIS | Materials repository | OPTIMADE / tools | P0 | Implemented | materials structure and property records | `StructuredRecord`, `Document` |
| COD | Crystal structure database | search / dumps | P1 | Connector-ready | crystal structure coverage | `StructuredRecord` |
| Materials Cloud Archive | Materials repository | archive / metadata | P1 | Implemented | archive records and bundles | `StructuredRecord`, `Document` |
| MDF | Materials repository | discover / publish | P1 | Connector-ready | curated materials datasets | `StructuredRecord` |
| NIST Materials Data Repository | Materials repository | repository portal | P1 | Connector-ready | open materials datasets | `StructuredRecord` |
| NIST Chemistry WebBook | Chemistry database | web resource | P0 | Connector-ready | physical and chemical properties | `StructuredRecord`, `KnowledgeRecord` |
| PubChem | Chemistry database | PUG REST | P0 | Implemented | compound properties and identifiers | `StructuredRecord`, `KnowledgeRecord` |
| Open Reaction Database | Reaction data | docs / repository | P1 | Connector-ready | machine-readable reaction data | `StructuredRecord`, `InstructionTrace` |
| Open Catalyst Project | Catalysis data | dataset downloads + code | P1 | Connector-ready | catalyst structure / relaxation data | `StructuredRecord` |
| Catalysis-Hub | Catalysis data | web platform | P1 | Connector-ready | surface reaction data | `StructuredRecord`, `KnowledgeRecord` |
| Battery Archive | Battery data | website / csv access | P1 | Connector-ready | cycling and safety data | `StructuredRecord` |
| Wikidata | Open knowledge graph | MediaWiki API | P0 | Implemented | entity descriptions and linked knowledge | `KnowledgeRecord` |
| Wikipedia dumps | Open knowledge text | official dumps | P1 | Connector-ready | encyclopedia-style explanatory text | `Document` |
| ChemLibreTexts | Open education | web pages / PDFs | P1 | Connector-ready | chemistry learning content | `Document` |
| MIT OCW | Open education | course site | P1 | Connector-ready | course notes and assignments | `Document` |
| NPTEL | Open education | course site | P1 | Connector-ready | engineering course content | `Document` |
| CORE | OA aggregator | API | P1 | Connector-ready | aggregated open-access papers | `Document` |
| Europe PMC | OA aggregator | REST API | P1 | Implemented | publications and open-access metadata | `Document`, `KnowledgeRecord` |
| PatentsView | Patents | ODP migration | P0 optional | Optional / migration blocked | patent metadata and technical prior art | `Document`, `StructuredRecord` |
| PATENTSCOPE | Patents | search / api-related access | P1 | Connector-ready | global patent documents | `Document` |
| EPO OPS | Patents | OPS automation path | P1 | Connector-ready | patent search and metadata | `Document` |

## Data Type Classification

Lattice separates source type from data type.

### Source-side categories

| Category | Meaning | Example Sources |
|---|---|---|
| Scholarly metadata | Paper-level metadata and discovery signals | OpenAlex, Crossref |
| Preprints / papers | Paper text and abstracts | arXiv |
| Structured materials DB | Structured scientific property tables | Materials Project, OQMD |
| Materials repository | Broader materials datasets and archives | NOMAD, JARVIS |
| Chemistry database | Compound-level chemistry information | PubChem |
| Open knowledge graph | Entity-level symbolic knowledge | Wikidata |
| Patents | Technical and industrial documents | PatentsView |
| Crystal structure DB | Structure-centric crystallographic records | COD |

### Lattice schema types

| Schema Type | Meaning | Typical Fields | Example Sources |
|---|---|---|---|
| `Document` | Long-form text for reading or training | title, text, sections | arXiv, OpenAlex, Crossref |
| `StructuredRecord` | Entity-centered structured properties | entity, fields, description | OQMD, NOMAD, JARVIS, PubChem |
| `KnowledgeRecord` | Subject-predicate-object knowledge units | subject, predicate, object, evidence | Wikidata, Materials Project, PubChem |
| `InstructionTrace` | Instruction-following or workflow examples | instruction, input, output, tool trace | future task recipes, generated workflows |

### Training-facing compiled views

| View | Purpose |
|---|---|
| `pretrain_view` | language-model pretraining text |
| `qa_view` | supervised QA or retrieval-style supervision |
| `instruction_view` | instruction tuning or task adaptation |
| `knowledge_view` | structured knowledge or symbolic supervision |
