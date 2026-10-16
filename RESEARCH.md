# Research and scope — 16 October 2026

## Brief

User: Localization engineers checking a text corpus against locally available OpenType/TrueType fonts before packaging a fallback set.

Pain: A font family name does not prove nominal coverage for a corpus, and coverage union can conceal missing code points or inconsistent cmap choice.

Smallest useful capability: Parse real standalone SFNT cmap format4/12 mappings, report per-font corpus gaps and choose a deterministic greedy fallback order with code-point evidence.

Acceptance: Synthetic Latin/accent fonts cover ABé🙂 in a stable two-step plan; missing characters are explicit. Format4 delta/array and format12 non-BMP mappings, offsets, malformed tables and preferred unsupported encodings are tested. Two installed real TTF/OTF files match FontTools4.61.1 on65617 queried code points each.

Demand is inferred from the workflow and adjacent public discussions, not a verified request for this project. Discovery: precise GitHub topics, this runnable example and the chronological profile index; no unsolicited outreach or activity manipulation.

## Comparables

Live GitHub repository search, sort **Most stars**, query `font editor in:description`. Highest-star relevant comparable found within this search scope: **fontforge/fontforge**. Search coverage is limited; this is not an exhaustive worldwide ranking. Broad queries returned unrelated products and were filtered by the actual user workflow.

| Repository | Stars observed | Last push observed (UTC) | Archived | API license classification |
| --- | ---: | --- | --- | --- |
| [fontforge/fontforge](https://github.com/fontforge/fontforge) | 8024 | 2026-10-13T20:50:40Z | False | NOASSERTION |
| [fonttools/fonttools](https://github.com/fonttools/fonttools) | 5292 | 2026-10-15T09:24:13Z | False | MIT |
| [fonttools/fontbakery](https://github.com/fonttools/fontbakery) | 705 | 2025-11-04T18:52:25Z | False | Apache-2.0 |

Exact observation times, README blob identities and up to five issue/PR references per comparable are in [research provenance](RESEARCH_PROVENANCE.json). NOASSERTION means the API did not classify the license; it is not permission to reuse. Stars are discovery evidence, not a measure of quality, performance or reliability.

FontForge is a full font editor and converter. FontTools already manipulates cmap mappings and exposes a preferred Unicode cmap. FontBakery offers broad font QA checks, with Fontspector as a related Rust port. Our bounded corpus-and-fallback report is an explicit standalone workflow; it does not prove these tools lack an equivalent script or check.

Workflow alternatives: FontForge for interactive font editing; FontTools for full font manipulation and scripting; FontBakery for extensive QA. These provide much broader format and validation support.

Our install is a small Python wheel and two or fewer input steps, with a synthetic example and explicit failure states. Competitors offer broader interfaces, integrations, formats, documentation and support communities; their current READMEs/code and issue discussions were inspected, but their installations, reliability, support response and time to first useful result were not measured here. Our successful example establishes only our stated behavior. Licensing was recorded, not used as a proxy for capability.

Portfolio distinction: colortool/colourdist deal with colors, and no existing owned project inspected handles SFNT character maps or font-set corpus coverage.

## Claims and reuse

No technical performance benchmark was conducted. There is no speed, memory, reliability or feature-absence superiority claim. Standard algorithms/formats are not inventions of this project. Source references were read for semantics and workflow comparison; implementation, prose and synthetic fixtures were written for this project. No third-party code, font assets or sample user data is bundled. No competitor logos/branding are reused.
