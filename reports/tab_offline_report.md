# RAGShield TAB Offline Privacy Evaluation

## Study Identity

- Protocol: `tab-offline-external-v1`
- Benchmark commit: `558e09e26d6b36f5f78440074e6a233946d98bd9`
- Split: `test` (127 quality-checked documents)
- NER model: `en_core_web_sm`
- LLM API calls: 0

## Results

| System | Character F1 | Exact Mention F1 | Full Coverage Recall | Overlap Recall | False-positive Character Rate | Text Retention |
|---|---:|---:|---:|---:|---:|---:|
| regex_rules | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| spacy_ner | 0.610 | 0.447 | 0.674 | 0.878 | 0.107 | 0.783 |
| combined | 0.610 | 0.447 | 0.674 | 0.878 | 0.107 | 0.783 |

## Combined Detector by Entity Type

| Entity Type | Full Coverage Recall |
|---|---:|
| CODE | 0.777 |
| DATETIME | 0.918 |
| DEM | 0.456 |
| LOC | 0.830 |
| MISC | 0.141 |
| ORG | 0.675 |
| PERSON | 0.375 |
| QUANTITY | 0.394 |

## Interpretation

The regex-only detector targets structured secrets and therefore does not cover ordinary court-document names, locations, or organizations. NER broadens coverage but also redacts non-gold spans. This external evaluation measures that privacy-utility trade-off instead of treating all redaction as correct.

## Claim Boundary

This is an offline evaluation against TAB's human span annotations. It is not an LLM generation study and does not establish re-identification resistance or production privacy.
