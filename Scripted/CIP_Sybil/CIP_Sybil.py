import json
import os

import ctk
import numpy as np
import qt
import slicer
import vtk
from slicer.ScriptedLoadableModule import (
    ScriptedLoadableModule,
    ScriptedLoadableModuleLogic,
    ScriptedLoadableModuleTest,
    ScriptedLoadableModuleWidget,
)

# Sybil models selectable in the UI. Ensemble averages all five and is most accurate
# but ~5x slower than a single model.
SYBIL_MODELS = ["sybil_ensemble", "sybil_1", "sybil_2", "sybil_3", "sybil_4", "sybil_5"]

# Default voxel spacing Sybil resamples to (row, col, slice), see sybil.datasets.utils.VOXEL_SPACING.
# Used only to give the generated attention/input nodes a sensible physical size.
SYBIL_VOXEL_SPACING = (0.703125, 0.703125, 2.5)


class CIP_Sybil(ScriptedLoadableModule):
    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "Sybil Lung Cancer Risk"
        self.parent.categories = ["Chest Imaging Platform"]
        self.parent.dependencies = []
        self.parent.contributors = ["Applied Chest Imaging Laboratory, Brigham and Women's Hospital"]
        self.parent.helpText = """
Run the <a href="https://github.com/reginabarzilaygroup/Sybil">Sybil</a> deep-learning model on a
chest LDCT (DICOM series) to estimate 1-6 year lung cancer risk. Optionally overlays Sybil's
attention as a heatmap and exports the model's deep features (hidden embeddings + attention tensors).
<br><br>
The model expects an axial LDCT where the first frame is the abdomen and the last frame is along the
clavicles. DICOM frames are sorted automatically.
"""
        self.parent.acknowledgementText = """
Sybil was developed by the Regina Barzilay group (MIT). This module wraps it for 3D Slicer.
"""


class CIP_SybilWidget(ScriptedLoadableModuleWidget):
    def setup(self):
        ScriptedLoadableModuleWidget.setup(self)

        self.logic = CIP_SybilLogic()

        # --- Input parameters ---
        paramsCollapsible = ctk.ctkCollapsibleButton()
        paramsCollapsible.text = "Inputs"
        self.layout.addWidget(paramsCollapsible)
        paramsLayout = qt.QFormLayout(paramsCollapsible)

        self.inputDirSelector = ctk.ctkPathLineEdit()
        self.inputDirSelector.filters = ctk.ctkPathLineEdit.Dirs
        self.inputDirSelector.setToolTip("Directory containing the DICOM slices of a single CT exam.")
        paramsLayout.addRow("DICOM directory: ", self.inputDirSelector)

        self.modelSelector = qt.QComboBox()
        self.modelSelector.addItems(SYBIL_MODELS)
        self.modelSelector.setToolTip("'sybil_ensemble' is most accurate but ~5x slower than a single model.")
        paramsLayout.addRow("Model: ", self.modelSelector)

        self.attentionCheckBox = qt.QCheckBox()
        self.attentionCheckBox.checked = True
        self.attentionCheckBox.setToolTip("Build and overlay an attention heatmap (in Sybil's processed space).")
        paramsLayout.addRow("Show attention heatmap: ", self.attentionCheckBox)

        self.exportCheckBox = qt.QCheckBox()
        self.exportCheckBox.checked = False
        self.exportCheckBox.setToolTip("Write risk scores, hidden embeddings and the full prediction to disk.")
        paramsLayout.addRow("Export deep features: ", self.exportCheckBox)

        self.outputDirSelector = ctk.ctkPathLineEdit()
        self.outputDirSelector.filters = ctk.ctkPathLineEdit.Dirs
        self.outputDirSelector.currentPath = os.path.join(slicer.app.temporaryPath, "sybil_output")
        self.outputDirSelector.setToolTip("Where exported features are written.")
        paramsLayout.addRow("Output directory: ", self.outputDirSelector)

        # --- Run ---
        self.runButton = qt.QPushButton("Run Sybil")
        self.runButton.toolTip = "Run Sybil inference on the selected DICOM directory."
        self.layout.addWidget(self.runButton)
        self.runButton.connect("clicked(bool)", self.onRun)

        # --- Results ---
        resultsCollapsible = ctk.ctkCollapsibleButton()
        resultsCollapsible.text = "Risk scores"
        self.layout.addWidget(resultsCollapsible)
        resultsLayout = qt.QVBoxLayout(resultsCollapsible)

        self.statusLabel = qt.QLabel("")
        resultsLayout.addWidget(self.statusLabel)

        self.resultsTable = qt.QTableWidget()
        self.resultsTable.setColumnCount(2)
        self.resultsTable.setHorizontalHeaderLabels(["Year", "Risk"])
        self.resultsTable.horizontalHeader().setStretchLastSection(True)
        self.resultsTable.verticalHeader().setVisible(False)
        resultsLayout.addWidget(self.resultsTable)

        self.layout.addStretch(1)

    def onRun(self):
        dicomDir = self.inputDirSelector.currentPath
        if not dicomDir or not os.path.isdir(dicomDir):
            slicer.util.errorDisplay("Please select a valid DICOM directory.")
            return

        modelName = self.modelSelector.currentText
        showAttention = self.attentionCheckBox.checked
        exportFeatures = self.exportCheckBox.checked
        # Attention is required to obtain deep features (hidden embeddings).
        returnAttentions = showAttention or exportFeatures

        progress = slicer.util.createProgressDialog(
            parent=slicer.util.mainWindow(), maximum=0, labelText="Running Sybil..."
        )
        qt.QApplication.setOverrideCursor(qt.Qt.WaitCursor)
        try:
            self.statusLabel.text = "Ensuring Sybil is installed..."
            slicer.app.processEvents()
            self.logic.ensureSybilInstalled()

            self.statusLabel.text = "Running inference (this may take several minutes)..."
            slicer.app.processEvents()
            prediction, serie = self.logic.runPrediction(dicomDir, modelName, returnAttentions)

            self.populateResults(prediction.scores[0])

            if showAttention:
                self.statusLabel.text = "Building attention overlay..."
                slicer.app.processEvents()
                self.logic.buildAttentionNodes(serie, prediction)

            if exportFeatures:
                self.statusLabel.text = "Exporting deep features..."
                slicer.app.processEvents()
                outDir = self.outputDirSelector.currentPath or os.path.join(slicer.app.temporaryPath, "sybil_output")
                self.logic.exportFeatures(prediction, outDir)
                self.statusLabel.text = "Done. Features written to %s" % outDir
            else:
                self.statusLabel.text = "Done."
        except Exception as e:
            slicer.util.errorDisplay("Sybil run failed:\n%s" % str(e))
            self.statusLabel.text = "Failed: %s" % str(e)
            import traceback
            traceback.print_exc()
        finally:
            qt.QApplication.restoreOverrideCursor()
            progress.close()

    def populateResults(self, scores):
        self.resultsTable.setRowCount(len(scores))
        for i, score in enumerate(scores):
            self.resultsTable.setItem(i, 0, qt.QTableWidgetItem("Year %d" % (i + 1)))
            self.resultsTable.setItem(i, 1, qt.QTableWidgetItem("%.4f" % score))


class CIP_SybilLogic(ScriptedLoadableModuleLogic):
    def ensureSybilInstalled(self):
        """Ensure the real (lung cancer) Sybil package is installed and importable.

        PyPI's 'sybil' is an unrelated documentation-testing tool that occupies the same
        'sybil' import name, so we install the lung cancer model from our local repo. We must
        NOT probe with 'import sybil' before installing: a failed 'from sybil import Serie'
        still caches the wrong module in sys.modules, which then masks the real one for the
        rest of the session. Detect via distribution metadata instead, and require a Slicer
        restart after any install (torch/numpy cannot swap in a running interpreter).
        """
        import sys
        import importlib.metadata as importlib_metadata

        def realSybilInstalled():
            # The lung cancer model ships sybil/serie.py; the doc-testing tool does not.
            try:
                dist = importlib_metadata.distribution("sybil")
            except importlib_metadata.PackageNotFoundError:
                return False
            return any(f.name == "serie.py" for f in (dist.files or []))

        if not realSybilInstalled():
            # Remove the impostor 'sybil' (the doc-testing tool) if present, then install ours.
            try:
                importlib_metadata.distribution("sybil")
                slicer.util.pip_uninstall("sybil")
            except importlib_metadata.PackageNotFoundError:
                pass
            slicer.util.pip_install(self._sybilSource())
            raise RuntimeError(
                "Sybil and its dependencies were installed. Please restart Slicer, "
                "then run the module again."
            )

        # The real Sybil is on disk. If a conflicting 'sybil' was already imported this
        # session (e.g. by an earlier failed run), it shadows the real one until restart.
        if "sybil" in sys.modules and not hasattr(sys.modules["sybil"], "Serie"):
            raise RuntimeError(
                "A conflicting 'sybil' module was loaded earlier this session. "
                "Please restart Slicer, then run the module again."
            )

    def _sybilSource(self):
        """Local Sybil checkout if one sits near this module, else a pip-installable URL."""
        d = os.path.dirname(os.path.abspath(__file__))
        for _ in range(4):  # CIP_Sybil/ -> PW-ACIL/ -> PW-2026/ (where Sybil/ lives)
            candidate = os.path.join(d, "Sybil")
            if any(os.path.isfile(os.path.join(candidate, m))
                   for m in ("setup.py", "setup.cfg", "pyproject.toml")):
                return candidate
            d = os.path.dirname(d)
        return "git+https://github.com/reginabarzilaygroup/Sybil.git"

    def runPrediction(self, dicomDir, modelName, returnAttentions):
        """Run Sybil on a directory of DICOM files. Returns (Prediction, Serie)."""
        from sybil import Serie, Sybil

        input_files = [os.path.join(dicomDir, f) for f in os.listdir(dicomDir) if not f.startswith(".")]
        input_files = [f for f in input_files if os.path.isfile(f)]
        if not input_files:
            raise ValueError("No files found in %s" % dicomDir)

        serie = Serie(input_files)
        model = Sybil(modelName)
        prediction = model.predict([serie], return_attentions=returnAttentions)
        return prediction, serie

    def buildAttentionNodes(self, serie, prediction):
        """Create grayscale input + attention heatmap volume nodes and overlay them.

        Both volumes live in Sybil's processed 512x512xN space, not the original CT geometry.
        """
        from sybil.utils.visualization import collate_attentions

        raw_images = serie.get_raw_images()
        background = np.stack([np.asarray(img).squeeze() for img in raw_images]).astype(np.float32)
        n_slices = background.shape[0]
        attention = collate_attentions(prediction.attentions[0], n_slices).astype(np.float32)

        bgNode = self._addVolume(background, "Sybil Input")
        attnNode = self._addVolume(attention, "Sybil Attention")

        # Color the attention overlay with a hot colormap.
        attnDisplay = attnNode.GetDisplayNode()
        colorNode = slicer.util.getNode("vtkMRMLColorTableNodeFileColdToHotRainbow.txt")
        if colorNode is not None:
            attnDisplay.SetAndObserveColorNodeID(colorNode.GetID())

        slicer.util.setSliceViewerLayers(background=bgNode, foreground=attnNode, foregroundOpacity=0.5)
        return bgNode, attnNode

    def _addVolume(self, narray, name):
        node = slicer.util.addVolumeFromArray(narray, name=name)
        node.SetSpacing(*SYBIL_VOXEL_SPACING)
        node.CreateDefaultDisplayNodes()
        return node

    def exportFeatures(self, prediction, outputDir):
        """Write risk scores, hidden embeddings and the full prediction to disk."""
        import pickle

        os.makedirs(outputDir, exist_ok=True)

        with open(os.path.join(outputDir, "prediction_scores.json"), "w") as f:
            json.dump({"predictions": prediction.scores}, f, indent=2)

        with open(os.path.join(outputDir, "risk_scores.csv"), "w") as f:
            f.write("year,risk\n")
            for i, score in enumerate(prediction.scores[0]):
                f.write("%d,%f\n" % (i + 1, score))

        if prediction.attentions is not None:
            hidden = np.asarray(prediction.attentions[0]["hidden"])
            np.save(os.path.join(outputDir, "hidden.npy"), hidden)
            with open(os.path.join(outputDir, "prediction.pkl"), "wb") as f:
                pickle.dump(prediction, f)


class CIP_SybilTest(ScriptedLoadableModuleTest):
    # Expected calibrated ensemble scores for the demo series (see Sybil tests/regression_test.py).
    EXPECTED_SCORES = [
        0.021628819563619374,
        0.03857256315036462,
        0.07191945816622261,
        0.07926975188037134,
        0.09584583525781108,
        0.13568094038444453,
    ]

    # Demo CT (single exam) published by the Sybil authors.
    DEMO_DATA_URL = (
        "https://www.dropbox.com/scl/fi/covbvo6f547kak4em3cjd/sybil_example.zip"
        "?rlkey=7a13nhlc9uwga9x7pmtk1cf1c&st=dqi0cf9k&dl=1"
    )

    @staticmethod
    def _getDemoData():
        """Download and extract the Sybil demo exam, returning its DICOM file paths.

        Ported from Sybil/examples/utils.py:get_demo_data so the test does not depend on
        the Sybil source tree (the examples/ folder is not part of the installed package).
        """
        import zipfile
        from urllib.request import urlopen

        cache_dir = os.path.expanduser("~/.sybil")
        os.makedirs(cache_dir, exist_ok=True)
        zip_file_path = os.path.join(cache_dir, "sybil_example.zip")
        if not os.path.exists(zip_file_path):
            with open(zip_file_path, "wb") as f:
                f.write(urlopen(CIP_SybilTest.DEMO_DATA_URL).read())

        demo_data_dir = os.path.join(cache_dir, "sybil_example")
        image_data_dir = os.path.join(demo_data_dir, "sybil_demo_data")
        if not os.path.exists(demo_data_dir):
            with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
                zip_ref.extractall(demo_data_dir)

        return [os.path.join(image_data_dir, f) for f in os.listdir(image_data_dir)]

    def setUp(self):
        slicer.mrmlScene.Clear(0)

    def runTest(self):
        self.setUp()
        self.test_CIP_Sybil1()

    def test_CIP_Sybil1(self):
        self.delayDisplay("Starting Sybil test")
        logic = CIP_SybilLogic()
        logic.ensureSybilInstalled()

        dicom_files = self._getDemoData()
        dicomDir = os.path.dirname(dicom_files[0])

        prediction, serie = logic.runPrediction(dicomDir, "sybil_ensemble", returnAttentions=True)
        scores = prediction.scores[0]

        self.assertEqual(len(scores), 6)
        for s in scores:
            self.assertTrue(0.0 <= s <= 1.0)
        for actual, expected in zip(scores, self.EXPECTED_SCORES):
            self.assertAlmostEqual(actual, expected, places=2)

        self.delayDisplay("Sybil test passed")
