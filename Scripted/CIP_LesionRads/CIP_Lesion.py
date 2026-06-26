"""
CIP_Lesion
==========

A self-contained 3D Slicer scripted module (Slicer 5.12 / Python 3.12) for radiomics
feature extraction on a lung lesion and the concentric tissue spheres around it.

This is a fresh, framework-decoupled rewrite of the older ``CIP_LesionModel`` module. It
keeps that module's radiomics engine (FeatureExtractionLib / FeatureWidgetHelperLib) and
its multi-sphere analysis, but removes every dependency on the CIP/ACIL Python packages and
on the external ``generatelesionsegmentation`` CLI. The lesion is provided by the user as a
Segmentation node (drawn in Segment Editor or imported from e.g. TotalSegmentator).
"""

import os
import collections

import numpy as np
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *

# Self-contained, vendored libraries that live next to this module.
import FeatureExtractionLib
import FeatureWidgetHelperLib
from FeatureWidgetHelperLib import FeatureExtractionLogic
from LesionAnalysisLib import geometry


#############################
# CIP_Lesion
#############################
class CIP_Lesion(ScriptedLoadableModule):
    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "CIP Lesion Analysis"
        self.parent.categories = ["Chest Imaging Platform"]
        self.parent.dependencies = []
        self.parent.contributors = ["Applied Chest Imaging Laboratory", "Brigham and Women's Hospital"]
        self.parent.helpText = """Radiomics feature extraction for a lung lesion and the
concentric spheres around it. Provide a CT volume and a lesion segmentation (drawn in
Segment Editor or imported, e.g. from TotalSegmentator), choose the feature families and
sphere radii, and run the analysis. Results are shown in a table and can be exported to CSV.
This module is self-contained and does not require the CIP/ACIL framework."""
        self.parent.acknowledgementText = """For research use only. Developed at the Applied
Chest Imaging Laboratory (ACIL), Brigham and Women's Hospital."""
        self.parent.icon = qt.QIcon(os.path.join(os.path.dirname(__file__),
                                                  "Resources", "Icons", "CIP_Lesion.png"))


#############################
# CIP_LesionWidget
#############################
class CIP_LesionWidget(ScriptedLoadableModuleWidget):
    RADII = (15, 20, 25)  # predefined sphere radii (mm), "human" working mode

    def setup(self):
        ScriptedLoadableModuleWidget.setup(self)
        self.logic = CIP_LesionLogic()

        # ---------------- Inputs ----------------
        inputsButton = ctk.ctkCollapsibleButton()
        inputsButton.text = "Inputs"
        self.layout.addWidget(inputsButton)
        inputsLayout = qt.QFormLayout(inputsButton)

        self.inputVolumeSelector = slicer.qMRMLNodeComboBox()
        self.inputVolumeSelector.nodeTypes = ("vtkMRMLScalarVolumeNode", "")
        self.inputVolumeSelector.addEnabled = False
        self.inputVolumeSelector.removeEnabled = False
        self.inputVolumeSelector.noneEnabled = False
        self.inputVolumeSelector.showHidden = False
        self.inputVolumeSelector.setMRMLScene(slicer.mrmlScene)
        self.inputVolumeSelector.toolTip = "CT volume to analyze"
        inputsLayout.addRow("CT volume: ", self.inputVolumeSelector)

        self.segmentationSelector = slicer.qMRMLNodeComboBox()
        self.segmentationSelector.nodeTypes = ("vtkMRMLSegmentationNode", "")
        self.segmentationSelector.addEnabled = False
        self.segmentationSelector.removeEnabled = False
        self.segmentationSelector.noneEnabled = True
        self.segmentationSelector.showHidden = False
        self.segmentationSelector.setMRMLScene(slicer.mrmlScene)
        self.segmentationSelector.toolTip = "Segmentation containing the lesion segment"
        inputsLayout.addRow("Lesion segmentation: ", self.segmentationSelector)

        self.segmentCombo = qt.QComboBox()
        self.segmentCombo.toolTip = "Segment that represents the lesion"
        inputsLayout.addRow("Lesion segment: ", self.segmentCombo)

        # ---------------- Regions ----------------
        regionsButton = ctk.ctkCollapsibleButton()
        regionsButton.text = "Regions to analyze"
        self.layout.addWidget(regionsButton)
        regionsLayout = qt.QVBoxLayout(regionsButton)

        self.lesionCheckbox = qt.QCheckBox("Lesion")
        self.lesionCheckbox.checked = True
        regionsLayout.addWidget(self.lesionCheckbox)

        self.radiusChecks = {}
        for r in self.RADII:
            cb = qt.QCheckBox("Sphere r = {0} mm (excludes lesion)".format(r))
            regionsLayout.addWidget(cb)
            self.radiusChecks[r] = cb

        # ---------------- Features ----------------
        featuresButton = ctk.ctkCollapsibleButton()
        featuresButton.text = "Features"
        self.layout.addWidget(featuresButton)
        featuresLayout = qt.QFormLayout(featuresButton)

        self.featureClasses = self.__buildFeatureClasses__()
        self.featureWidgets = collections.OrderedDict()
        for key in self.featureClasses:
            self.featureWidgets[key] = []

        self.tabsFeatureClasses = FeatureWidgetHelperLib.CheckableTabsWidget()
        featuresLayout.addRow(self.tabsFeatureClasses)

        # Optional labelmap selector, only used by the Parenchymal Volume feature class.
        self.parenchymaLabelmapSelector = slicer.qMRMLNodeComboBox()
        self.parenchymaLabelmapSelector.nodeTypes = ("vtkMRMLLabelMapVolumeNode", "")
        self.parenchymaLabelmapSelector.addEnabled = False
        self.parenchymaLabelmapSelector.removeEnabled = False
        self.parenchymaLabelmapSelector.noneEnabled = True
        self.parenchymaLabelmapSelector.showHidden = False
        self.parenchymaLabelmapSelector.setMRMLScene(slicer.mrmlScene)
        self.parenchymaLabelmapSelector.toolTip = "Whole-volume labelmap required for Parenchymal Volume"

        gridWidth, gridHeight = 3, 9
        for featureClass in self.featureClasses:
            check = featureClass in ("First-Order Statistics", "Morphology and Shape")
            tabFeatureClass = qt.QWidget()
            tabFeatureClass.setLayout(qt.QGridLayout())
            if featureClass == "Parenchymal Volume":
                tabFeatureClass.layout().addWidget(qt.QLabel("Select a labelmap"), 0, 0)
                tabFeatureClass.layout().addWidget(self.parenchymaLabelmapSelector, 0, 1, 1, 2)
                gridLayoutCoordinates = ((row, col) for col in range(gridWidth) for row in range(1, gridHeight + 1))
            else:
                gridLayoutCoordinates = ((row, col) for col in range(gridWidth) for row in range(gridHeight))
            for featureName in self.featureClasses[featureClass]:
                rc = next(gridLayoutCoordinates, None)
                if featureName is None or rc is None:
                    break
                row, col = rc
                featureCheckboxWidget = FeatureWidgetHelperLib.FeatureWidget()
                featureCheckboxWidget.Setup(featureName=featureName, checkStatus=check)
                tabFeatureClass.layout().addWidget(featureCheckboxWidget, row, col)
                self.featureWidgets[featureClass].append(featureCheckboxWidget)
            self.tabsFeatureClasses.addTab(tabFeatureClass, featureClass,
                                           self.featureWidgets[featureClass], checkStatus=check)
        self.tabsFeatureClasses.setCurrentIndex(0)

        # ---------------- Analyze ----------------
        self.analyzeButton = qt.QPushButton("Analyze")
        self.analyzeButton.toolTip = "Run feature extraction on the selected regions"
        self.layout.addWidget(self.analyzeButton)

        # ---------------- Results ----------------
        resultsButton = ctk.ctkCollapsibleButton()
        resultsButton.text = "Results"
        self.layout.addWidget(resultsButton)
        resultsLayout = qt.QVBoxLayout(resultsButton)

        self.tableNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTableNode", "CIP_Lesion results")
        self.tableView = slicer.qMRMLTableView()
        self.tableView.setMRMLTableNode(self.tableNode)
        self.tableView.setMinimumHeight(250)
        resultsLayout.addWidget(self.tableView)

        self.exportButton = qt.QPushButton("Export CSV")
        resultsLayout.addWidget(self.exportButton)

        self.layout.addStretch(1)

        # ---------------- Connections ----------------
        self.segmentationSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSegmentationChanged)
        self.analyzeButton.connect("clicked(bool)", self.onAnalyze)
        self.exportButton.connect("clicked(bool)", self.onExportCSV)

        self.onSegmentationChanged(self.segmentationSelector.currentNode())

    # ---------- feature definitions (ported verbatim from CIP_LesionModel) ----------
    def __buildFeatureClasses__(self):
        fc = collections.OrderedDict()
        fc["First-Order Statistics"] = ["Voxel Count", "Gray Levels", "Energy", "Entropy",
                                        "Minimum Intensity", "Maximum Intensity", "Mean Intensity",
                                        "Median Intensity", "Range", "Mean Deviation",
                                        "Root Mean Square", "Standard Deviation",
                                        "Ventilation Heterogeneity",
                                        "Skewness", "Kurtosis", "Variance", "Uniformity"]
        fc["Morphology and Shape"] = ["Volume mm^3", "Volume cc", "Surface Area mm^2",
                                      "Surface:Volume Ratio", "Compactness 1", "Compactness 2",
                                      "Maximum 3D Diameter", "Spherical Disproportion", "Sphericity"]
        fc["Texture: GLCM"] = ["Autocorrelation", "Cluster Prominence", "Cluster Shade",
                               "Cluster Tendency", "Contrast", "Correlation", "Difference Entropy",
                               "Dissimilarity", "Energy (GLCM)", "Entropy(GLCM)", "Homogeneity 1",
                               "Homogeneity 2", "IMC1", "IDMN", "IDN", "Inverse Variance",
                               "Maximum Probability", "Sum Average", "Sum Entropy", "Sum Variance",
                               "Variance (GLCM)"]
        fc["Texture: GLRL"] = ["SRE", "LRE", "GLN", "RLN", "RP", "LGLRE", "HGLRE", "SRLGLE",
                               "SRHGLE", "LRLGLE", "LRHGLE"]
        fc["Geometrical Measures"] = ["Extruded Surface Area", "Extruded Volume",
                                      "Extruded Surface:Volume Ratio"]
        fc["Renyi Dimensions"] = ["Box-Counting Dimension", "Information Dimension",
                                  "Correlation Dimension"]
        fc["Parenchymal Volume"] = FeatureExtractionLib.ParenchymalVolume.getAllEmphysemaDescriptions()
        return fc

    # ---------- segment combo ----------
    def onSegmentationChanged(self, node):
        self.segmentCombo.clear()
        if node is None or node.GetSegmentation() is None:
            return
        segmentation = node.GetSegmentation()
        for i in range(segmentation.GetNumberOfSegments()):
            segmentId = segmentation.GetNthSegmentID(i)
            segment = segmentation.GetSegment(segmentId)
            self.segmentCombo.addItem(segment.GetName(), segmentId)

    def currentSegmentId(self):
        idx = self.segmentCombo.currentIndex
        if idx < 0:
            return None
        return self.segmentCombo.itemData(idx)

    # ---------- selected features ----------
    def selectedFeatures(self):
        categories = set()
        keys = set()
        orderedKeys = []
        for featureClass in self.featureWidgets:
            for widget in self.featureWidgets[featureClass]:
                if widget.checked:
                    categories.add(featureClass)
                    name = str(widget.text)
                    if name not in keys:
                        keys.add(name)
                        orderedKeys.append(name)
        return categories, keys, orderedKeys

    # ---------- run ----------
    def onAnalyze(self, _=None):
        volume = self.inputVolumeSelector.currentNode()
        segNode = self.segmentationSelector.currentNode()
        segmentId = self.currentSegmentId()

        if volume is None:
            self.__warn__("Select a volume", "Please select an input CT volume.")
            return
        if segNode is None or segmentId is None:
            self.__warn__("Select a lesion", "Please select a segmentation and a lesion segment.")
            return

        categories, keys, orderedKeys = self.selectedFeatures()
        if not keys:
            qt.QMessageBox.information(slicer.util.mainWindow(), "Select a feature",
                                       "Please select at least one feature to calculate.")
            return

        parenchymaArray = None
        if "Parenchymal Volume" in categories:
            pNode = self.parenchymaLabelmapSelector.currentNode()
            if pNode is None:
                self.__warn__("Select a labelmap",
                              "Please select a whole-volume labelmap in the Parenchymal Volume tab, "
                              "or unselect that feature class.")
                return
            parenchymaArray = slicer.util.array(pNode.GetID())

        # Lesion ROI as a binary numpy array aligned with the CT volume.
        lesionArray = self.logic.segmentToArray(volume, segNode, segmentId)
        if lesionArray is None or lesionArray.sum() == 0:
            self.__warn__("Empty lesion", "The selected segment is empty or could not be resampled "
                                          "to the CT geometry.")
            return

        # Build the list of (label, ROI array) to analyze.
        regions = []
        if self.lesionCheckbox.checked:
            regions.append(("lesion", lesionArray))
        checkedRadii = [r for r in self.RADII if self.radiusChecks[r].checked]
        if checkedRadii:
            distanceMap = self.logic.computeDistanceMap(volume, lesionArray)
            for r in checkedRadii:
                regions.append(("r{0}".format(r), self.logic.sphereArray(lesionArray, distanceMap, r)))
        if not regions:
            self.__warn__("Select a region", "Please select the lesion and/or at least one sphere.")
            return

        qt.QApplication.setOverrideCursor(qt.Qt.WaitCursor)
        try:
            resultsByRegion = self.logic.analyze(volume, regions, categories, keys, parenchymaArray)
        finally:
            qt.QApplication.restoreOverrideCursor()

        self.logic.resultsToTable(resultsByRegion, orderedKeys, self.tableNode)

    def onExportCSV(self, _=None):
        if self.tableNode.GetNumberOfColumns() == 0:
            self.__warn__("No results", "Run an analysis before exporting.")
            return
        path = qt.QFileDialog.getSaveFileName(slicer.util.mainWindow(), "Export results",
                                              "CIP_Lesion_results.csv", "CSV (*.csv)")
        if not path:
            return
        slicer.util.saveNode(self.tableNode, path)
        slicer.util.showStatusMessage("CIP_Lesion results saved to {0}".format(path), 3000)

    def __warn__(self, title, message):
        qt.QMessageBox.warning(slicer.util.mainWindow(), title, message)

    def cleanup(self):
        pass


#############################
# CIP_LesionLogic
#############################
class CIP_LesionLogic(ScriptedLoadableModuleLogic):
    MAX_RADIUS = 30  # mm, FastMarching stopping value (matches CIP_LesionModel)

    def __init__(self):
        ScriptedLoadableModuleLogic.__init__(self)
        self._parenchymaDescriptions = set(FeatureExtractionLib.ParenchymalVolume.getAllEmphysemaDescriptions())

    def segmentToArray(self, volumeNode, segmentationNode, segmentId):
        """ Return the lesion segment as a binary numpy array aligned with ``volumeNode``. """
        arr = slicer.util.arrayFromSegmentBinaryLabelmap(segmentationNode, segmentId, volumeNode)
        if arr is None:
            # Fallback: export the segment to a temporary labelmap in the CT geometry.
            labelmapNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLLabelMapVolumeNode")
            ids = vtk.vtkStringArray()
            ids.InsertNextValue(segmentId)
            slicer.modules.segmentations.logic().ExportSegmentsToLabelmapNode(
                segmentationNode, ids, labelmapNode, volumeNode)
            arr = slicer.util.arrayFromVolume(labelmapNode).copy()
            slicer.mrmlScene.RemoveNode(labelmapNode)
        return (arr != 0).astype(np.int16)

    def computeDistanceMap(self, volumeNode, lesionArray):
        """ Geodesic distance (mm) from the lesion centroid, via SimpleITK FastMarching. """
        import SimpleITK as sitk
        c = geometry.centroid(lesionArray)
        dims = geometry.vtk_numpy_coordinate(volumeNode.GetImageData().GetDimensions())  # (z, y, x)
        speed = np.ones(dims, np.int32)
        sitkImage = sitk.GetImageFromArray(speed)
        sitkImage.SetSpacing(volumeNode.GetSpacing())
        fastMarchingFilter = sitk.FastMarchingImageFilter()
        fastMarchingFilter.SetStoppingValue(self.MAX_RADIUS)
        fastMarchingFilter.SetTrialPoints([geometry.numpy_itk_coordinate(c)])
        output = fastMarchingFilter.Execute(sitkImage)
        return sitk.GetArrayFromImage(output)

    def sphereArray(self, lesionArray, distanceMap, radius):
        """ Binary ROI of a sphere of given radius around the lesion, EXCLUDING the lesion. """
        array = np.zeros_like(lesionArray)
        array[distanceMap <= radius] = 1
        array[lesionArray != 0] = 0
        return array

    def analyze(self, volumeNode, regions, categories, featureKeys, parenchymaArray=None):
        """ Run feature extraction on each (label, ROI array) region.
        :return: OrderedDict label -> OrderedDict(featureKey -> value)
        """
        cats = set(categories)
        keys = set(featureKeys)
        if "Parenchymal Volume" in cats and parenchymaArray is None:
            cats.discard("Parenchymal Volume")
            keys = keys.difference(self._parenchymaDescriptions)

        resultsByRegion = collections.OrderedDict()
        for label, roiArray in regions:
            results = collections.OrderedDict()
            fe = FeatureExtractionLogic(volumeNode, roiArray, cats, keys,
                                        additionalProgressbarDesc=" ({0})".format(label),
                                        labelmapWholeVolumeArray=parenchymaArray)
            fe.run(results)
            resultsByRegion[label] = results
        return resultsByRegion

    def resultsToTable(self, resultsByRegion, orderedKeys, tableNode):
        """ Fill ``tableNode`` with one row per feature and one column per region. """
        tableNode.RemoveAllColumns()

        featureCol = vtk.vtkStringArray()
        featureCol.SetName("Feature")
        for key in orderedKeys:
            featureCol.InsertNextValue(key)
        tableNode.AddColumn(featureCol)

        for label, results in resultsByRegion.items():
            col = vtk.vtkStringArray()
            col.SetName(label)
            for key in orderedKeys:
                col.InsertNextValue(self.__format__(results.get(key)))
            tableNode.AddColumn(col)
        tableNode.Modified()

    @staticmethod
    def __format__(value):
        if value is None:
            return ""
        if isinstance(value, float):
            return "{0:.6g}".format(value)
        return str(value)


#############################
# CIP_LesionTest
#############################
class CIP_LesionTest(ScriptedLoadableModuleTest):
    def setUp(self):
        slicer.mrmlScene.Clear(0)

    def runTest(self):
        self.setUp()
        self.test_geometry_helpers()

    def test_geometry_helpers(self):
        """ Lightweight, data-free test of the vendored geometry helpers and sphere masking. """
        self.delayDisplay("Starting CIP_Lesion geometry test")

        roi = np.zeros((10, 10, 10), dtype=np.int16)
        roi[4:6, 4:6, 4:6] = 1
        c = geometry.centroid(roi)
        assert all(coord in (4, 5) for coord in c), "Unexpected centroid {0}".format(c)
        assert geometry.vtk_numpy_coordinate((1, 2, 3)) == [3, 2, 1]
        assert geometry.numpy_itk_coordinate([3, 2, 1]) == [1, 2, 3]

        logic = CIP_LesionLogic()
        fakeDistanceMap = np.full((10, 10, 10), 100.0)
        fakeDistanceMap[3:7, 3:7, 3:7] = 5.0
        sphere = logic.sphereArray(roi, fakeDistanceMap, 10)
        assert sphere[roi != 0].sum() == 0, "Sphere must exclude the lesion voxels"
        assert sphere.sum() > 0, "Sphere should contain voxels"

        self.delayDisplay("CIP_Lesion geometry test passed")
