# CIP_RibAnalysis — Rib Analysis

A [3D Slicer](https://www.slicer.org/) scripted module that analyzes rib segmentations to
compute per-rib, per-level, and regional metrics — volume, mean HU, mass, and density. It
expects the 24 rib segments produced by
[TotalSegmentator](https://github.com/wasserth/TotalSegmentator) (`rib_left_1..12`,
`rib_right_1..12`).

## Usage

1. Open the module under **Chest Imaging Platform → Rib Analysis**.
2. Select the input **CT volume** and the **rib segmentation**.
3. Click **Analyze**.
4. Outputs:
   - A sortable results table (TS Label, Rib, Volume cm³, Mean HU, Density g/cm³, Mass g).
   - A 3D rib view with the true ribs highlighted.
   - Stacked bar charts of density and mass by anatomical region (true / false / floating).

## Notes

Mass is computed with a piecewise HU→density conversion calibrated for bone. Rib level 1 is
excluded from the true-rib region because of field-of-view inconsistencies in the
segmentations.

## License

For research use only. See the top-level [README](../README.md) and
[LICENSE](../LICENSE).
