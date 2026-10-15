# Post-hoc reporting additions

These files were added after the frozen experiment detected exact source overlap
between development F03 and one program each in F22/F23. They are deliberately
separate from the unchanged, hashed inference implementation and original scripts.
They read saved predictions and labels; they never call models or change analysis.

`evaluate_integrity.py` removes whole overlapping families using source hashes only,
reports 28 base programs / 112 variants and the eligible repeat subset, and leaves
the original scheduled-cohort evidence intact. This sensitivity was not preregistered.
`package_study.py` wraps the frozen packaging script to include this disclosed addition.

One-command saved evidence rebuild: `bash scripts/rebuild_study.sh`.
These additions, unlike frozen inference code, may incorporate approved label reviews
through evaluator annotation files. Such reviews must preserve original labels.

`finalize_report.py` applies the author's final approval to reporting metadata,
rebuilds the real binary-labelled-subset table from saved predictions, and generates
figures with final label terminology. It does not change controlled truth values,
model inputs, predictions or the frozen implementation. The earlier five-positive
annotation subset is preserved in `data/annotations/review-history/`. The original
frozen rebuild script's historical status strings are overridden by this explicit
post-freeze reporting step; the script itself remains unchanged.
