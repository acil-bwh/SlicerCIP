# CIP_Lesion

A self-contained 3D Slicer scripted module (Chest Imaging Platform) for **radiomics feature
extraction** on a lung lesion and the concentric tissue spheres around it.

CIP_Lesion is a fresh, framework-decoupled rewrite of the older `CIP_LesionModel`. It keeps
that module's radiomics engine and multi-sphere analysis, but removes every dependency on
the CIP/ACIL Python packages and on the external `generatelesionsegmentation` CLI — so it
**loads and runs on Slicer 5.12 / Python 3.12** on its own.

## Functionality

- Computes a large set of features on a user-provided lesion and on concentric spheres
  (15 / 20 / 25 mm) that surround it (each sphere **excludes** the lesion voxels). Feature
  families (in `FeatureExtractionLib/`):
  - First-order statistics, Morphology & shape, Texture GLCM, Texture GLRL,
    Geometrical measures, Rényi fractal dimensions, Parenchymal volume.
- Interactive feature selection via checkable tabs (`FeatureWidgetHelperLib/`).
- Results shown in a native `vtkMRMLTableNode` table (one row per feature, one column per
  region) and exportable to **CSV**.
- Spheres are generated from a SimpleITK FastMarching distance map seeded at the lesion
  centroid.

## Workflow

1. Load a CT volume.
2. Create the lesion as a **Segmentation** — draw it in Segment Editor, or import a
   segmentation (e.g. a TotalSegmentator result). A labelmap can be converted to a
   segmentation via *Data* → drag into a segmentation, or the Segmentations module.
3. In CIP_Lesion: select the CT volume, the segmentation, and the lesion segment.
4. Choose the regions (lesion and/or spheres) and the feature families.
5. Click **Analyze**, then **Export CSV** if desired.

## Dependencies & limitations

- **Python / Slicer:** targets Python 3.12 / Slicer 5.12.
- **External libraries:** `numpy`, `SimpleITK` (both bundled with Slicer). The feature math
  is this module's own pure-Python implementation — it does **not** use the external
  `pyradiomics` package.
- **Self-contained:** no dependency on the CIP/ACIL framework or on SlicerCIP being
  installed. A few coordinate/centroid helpers are vendored in `LesionAnalysisLib/`.
- **No automatic segmentation:** unlike the original `CIP_LesionModel`, this module does not
  segment the lesion for you (the seed-based `generatelesionsegmentation` CLI is not used).
  You must supply the lesion as a segment.
- **Parenchymal Volume** feature class additionally requires a whole-volume labelmap,
  selected in its tab; if none is provided, that class is skipped.
- The bundled `FeatureExtractionLib` / `FeatureWidgetHelperLib` packages share their names
  with the copies in `CIP_LesionModel`. `CIP_LesionModel` does not load on Slicer 5.12, so
  there is no conflict in practice; avoid enabling both modules simultaneously.
