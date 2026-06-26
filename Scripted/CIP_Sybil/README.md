# CIP_Sybil — Sybil Lung Cancer Risk

A [3D Slicer](https://www.slicer.org/) scripted module that runs the
[Sybil](https://github.com/reginabarzilaygroup/Sybil) deep-learning model on a chest LDCT
(DICOM series) to estimate 1–6 year lung cancer risk. It can optionally overlay Sybil's
attention as a heatmap and export the model's deep features (hidden embeddings and
attention tensors).

The model expects an axial LDCT where the first frame is the abdomen and the last frame is
along the clavicles. DICOM frames are sorted automatically.

## ⚠️ Compatibility

**Only compatible with 3D Slicer 5.8 or lower.** Sybil currently pins **torch 1.13**, which
conflicts with the newer torch/Python shipped in Slicer 5.9+.

After the first dependency install, **restart Slicer once** before running — torch/numpy
cannot be swapped in a running interpreter.

## Usage

1. Open the module under **Chest Imaging Platform → Sybil Lung Cancer Risk**.
2. Select a **DICOM directory** containing the slices of a single CT exam.
3. Pick a model: `sybil_ensemble` (most accurate, ~5× slower) or `sybil_1`–`sybil_5`.
4. Optional: enable the **attention heatmap** overlay, and/or **export deep features**
   (risk scores JSON/CSV, hidden embeddings `.npy`, full prediction `.pkl`).
5. Choose an **output directory** (defaults to Slicer's temp directory) and run.
6. Results show the 1–6 year risk scores in a table.

## Notes

On first run the module installs the real Sybil package from a local checkout or from
GitHub. The unrelated PyPI `sybil` documentation-testing tool occupies the same import name
and is uninstalled automatically if present.

## License

For research use only. See the top-level [README](../README.md) and
[LICENSE](../LICENSE).
