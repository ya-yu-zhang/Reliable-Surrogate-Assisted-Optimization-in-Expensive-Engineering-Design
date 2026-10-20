# Engineering Optimization author-review materials

Current status: post-review factual implementation/claim revision and zero-solver
class/capacity/order/grid-range analysis are complete. The simulated review at
cfc2b94 and review_revision/RESPONSE_TO_REVIEW.md identify the remaining gates. This is an author-review draft, not a submission-approved
manuscript. See work_status.json, CONTRIBUTION_EVIDENCE_MATRIX.md and
MANUSCRIPT_INTEGRATION_PLAN.md for the remaining scientific and author decisions.

The existing main/supplement draft now includes the preceding measured-record tables plus a code-to-method table, primary
truth/cost table and four supporting review tables for archived common continuation, independent budget
validation, small thermal verification, differing GP settings, selected mesh
checks and the cumulative 55,305 paid physics-attempt ledger. Historical inline
numeric table rows and the 38-entry bibliography are preserved. Existing
abstract, contribution summary, limitations, conclusion and disclosure statements
received narrowly scoped factual edits; no new scientific argument sections were
drafted in this integration. Earlier notes recording AI-assisted drafting of
working-draft sections were incorrect; the AI disclosure now records copyediting
and language refinement only.

## Publication boundary

The updated source and analysis results are published separately from their
compressed artifacts. The full local review package contains the complete
26-page main/31-page supplement and selected grid records. Publication of the
paired-grid raw archive is incomplete: segments-003.b85 and segments-004.b85
were rejected by automatic approval review despite complete decoding and
provenance checks. No broken partial archive is published. The first new PDF segment was also rejected by automatic approval review;
no new PDF segments are committed. Until this specific public disclosure is
approved and all parts verified, the public pdf_release manifest remains the
earlier 23/27-page release. See work_status.json.

## Review the compiled documents

```bash
python -m src.restore_engineering_optimization_pdfs --output ./review_pdfs
```

The public pdf_release/manifest.json still points to the earlier 23-page main
and 27-page supplement. The complete updated PDFs are in the local review
package; see the publication boundary above. The restoration script verifies exact PDF bytes before
writing and refuses to replace a different file. Older segment files are retained
as historical release bytes, not selected by the current manifest.

To compile from LaTeX, work in paper/engineering_optimization and run pdfLaTeX,
BibTeX and two more pdfLaTeX passes for each EO_manuscript/EO_supplementary source.
Use the supplied publisher interact.cls, tfcad.bst, EO_references.bib, figures/
and integrated_evidence/ inputs. Compilation with the installed TeX Live engine
produced no undefined references or overfull-box warnings; all 57 rendered pages
were checked. See integrated_evidence/release_validation.json and
integrated_evidence/pdf_render_review.json.

## Reproduce the new numerical record

Use requirements-budget-audit.txt and the instructions in paired_mesh/README.md.
Restoration/analysis needs no physical solves. Twenty-five exact selected input
and journal files restore successfully, and all three mesh-analysis outputs match
byte for byte. The 24 relevant local tests pass; this count does not imply that
every historical remote test module was run in the current extracted workspace.

Selected fixed-design classifications persist in the six mesh/mapping contexts,
including eight differing endpoint pairs and six identical-endpoint ties. The
original strict coarse-source gate remains failed, one point remains flagged,
and the stopped/recovery attempts are fully charged. Physical mesh convergence,
an adaptive-allocation advantage and net deployment savings are not established.

## Remaining author work

* Independently assess the closest prior art, the technical increment and the
  article's scientific argument using the contribution--evidence matrix. This is the
  blocking scientific item.
* Verify current journal-specific submission instructions and exact data/release
  citation wording, including the separately held large historical source archive.

Affiliations, contribution/funding/conflict statements and all-author approval are
settled for the Markdown/Word submission track (approval recorded 2026-10-19), and the
AI-use record is copyediting and language refinement only. The LaTeX files in this
directory are a frozen review artifact and are not the submission source.

submission_ready remains false. Neither a journal acceptance guarantee nor an
AI-detector score is supplied.

Latest post-review reproducibility instructions and author gates are in
review_revision/README.md, IMPLEMENTATION_CONTRACT.md and RESPONSE_TO_REVIEW.md.
The new sensitivity is retrospective and does not certify novelty or efficacy.
