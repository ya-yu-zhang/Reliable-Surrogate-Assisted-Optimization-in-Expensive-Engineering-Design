# Engineering Optimization formatting and author review

This is a compiled author-review package, not an approved submission. It retains the measured results, failed promotion gate and scope limits from the evidence-integrated revision. No new finite-element experiment was run for this formatting step.

## Official sources and verification boundary

- Publisher template: https://files.taylorandfrancis.com/InteractCADLaTeX.zip
- Download checked on 11 October 2026. Archive SHA256: `5aeb0952b0021ad98653fe8ca6a1ea8edf35fbd639af5ee5443e6662dff90e25`.
- The unmodified bundle supplies `interact.cls` and `tfcad.bst`. The sample is v1.04 (May 2023); the included class is v1.03 (17 October 2016). The sample version must not be mistaken for the class version.
- Official journal scope: https://www.tandfonline.com/journals/geno20
- Journal instructions endpoint: https://www.tandfonline.com/action/authorSubmission?journalCode=geno20&show=instructions
- Publisher formatting guidance: https://authorservices.taylorandfrancis.com/publishing-your-research/writing-your-paper/formatting-and-templates/
- Official Chicago author-date guide: https://files.taylorandfrancis.com/tf_ChicagoAD.pdf

The official scope and publisher template were retrieved. The journal-specific instructions page returned HTTP 403. Therefore the Interact-CAD bundle's authenticity is verified, but the journal's current designation of that exact bundle, article-length rules and every portal requirement are **not fully verified**. Do not describe this release as certified to satisfy all current Engineering Optimization submission requirements. Confirm these items in the submission portal or with the publisher before uploading the final paper. No unsupported 7,000-word rule is treated as a verified requirement.

## Scope and evidence mapping

The official scope requires optimization innovation and engineering applicability. The manuscript presents an implemented method for inspecting surrogate management and allocating diagnostic evaluations, with finite-element design evidence. It does not rely on a calibration statistic alone as the engineering contribution.

| Editorial question | Existing manuscript evidence | Claim boundary retained |
|---|---|---|
| What can an engineer do with the method? | Algorithm 1; Section 3.5 response-equivalence rule; prediction-before-label records | An audit of a declared mechanism and cost boundary, without a convergence or universal coverage claim |
| What is added relative to established management and selection? | Section 2.3 and Table 1a compare the operational evidence objects with regional Kriging, management, diagnostic benchmarking and selection | The elementary additive-ranking lemma, logging and cost counting are not individually claimed as new |
| Does the method apply to decisions that can change ranking? | Section 6.3; Table 5; Supplement S9: 120 frozen GP states and 138 newly paid diagnostic evaluations | Immediate effects depend on history; successful optimizer endpoints do not by themselves establish a complete mechanism audit |
| Can a zero-gain first action still accompany later improvement? | Section 6.4 and S10.2: separately recorded 20-step trajectories | Whole-policy histories diverge; these are not isolated causal effects of a first action |
| What does cheaper selection cost in final performance? | Table 6, Figure 6 and S10: 280 vs 626 paid calls, 9.014%/27.217% paired median compliance gaps; fixed policies cost 200 | No performance-preserving savings claim; no retrospective promotion threshold |
| How broad is the engineering validation? | A volume-preserving beam design family, original load plus two added force positions | Within-family transfer; not cross-domain engineering validation or unrestricted 5,000-variable topology optimization |

The shortened abstract summarizes these existing findings. References retain stable numbered IDs in Markdown for evidence tracking; generated LaTeX uses author-date citations and a shared BibTeX database. `bibliography_verification.json` records DOI metadata checks and the corrected references 7, 8 and 26 and expanded EngiBench authors. This is not a new comprehensive literature review. Table S25a identifies the previously uncaptioned additional controls without shifting S26–S32. All historical numerical table cells are retained.

## AI disclosure and author responsibility

Official policy checked on 11 October 2026:
https://authorservices.taylorandfrancis.com/editorial-policies/using-ai-in-your-research-and-manuscript-preparations/

Taylor & Francis permits copyediting assistance and author-validated coding assistance, but disallows generative AI creating a manuscript/section first draft or creating/concluding an argument. The prior work in this conversation included assistance preparing drafts of added scientific sections and arguments. It must not be relabelled as grammar-only assistance or automatically certified compliant. The working acknowledgement states the actual unresolved status. Authors must substantively assess and rewrite the affected argument and ask the publisher about any remaining policy uncertainty; a detector score cannot establish that this history complies with the policy.

For this step, OpenAI Codex based on GPT-6 was used for formatting, source-building code, reference checks and copyediting. Earlier session versions and the full extent of assistance require author confirmation. Authors must independently validate the software, evidence, citations and final interpretations, verify applicable tool terms, complete an accurate disclosure, and approve the submitted version. Do not claim these actions have already occurred.

No AI-detector service was used, and no score is asserted. A result below 10% cannot be guaranteed across unspecified detectors, versions and settings. This revision makes no detector-evasion modifications and does not conceal assistance.

## Rebuild

From the repository root, with Pandoc and a working TeX Live installation:

```sh
python src/fetch_engineering_optimization_template.py
python src/build_engineering_optimization_sources.py
python src/compile_engineering_optimization.py
```

The fetcher checks the archive checksum before installing the official class/style unchanged. If a future publisher archive changes, inspect it and update provenance deliberately. Publisher assets are installed for local author use; this repository does not assert redistribution rights over the template. The downloadable author-review ZIP includes the class/style needed for its intended author workflow, without an added license claim.

For a container with TeX files but missing local formats/search databases, the compiler supports `--repair-runtime /absolute/task/path/tex-runtime`, which creates only task-local format and font-map files. A normal TeX installation does not need this option. Source generation copies the existing vector figures into the package; no figure data are regenerated or altered by formatting. The new transfer charts remain the existing data-derived PNG files. The evidence integrator now refreshes numerical table blocks by default, preserving author-edited prose; `--refresh-prose` explicitly restores its earlier working prose templates and requires a new author review.

## Remaining author actions

1. Supply the actual affiliations for Zhenyu Meng and Jia Zhao; placeholders remain visible in both PDFs.
2. Substantively review the AI-assisted added argument and prose, complete the disclosure and all author approvals, and resolve publisher-policy uncertainty.
3. Confirm the current journal-specific template, word limit, article type, reference variant and portal declarations through the instructions/portal.
4. Check the final data-availability statement and any large-file archive release, and cite the final frozen source release.

These items require author information or editorial judgment. They are not a request for manual GitHub pushing. Technical compilation, page review, numeric-integrity checks and the publication of this repository revision are handled in this stage. Journal fit is better supported by the revised framing, but novelty sufficiency and acceptance remain editorial decisions.
