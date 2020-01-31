import os, sys
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import collections
import itertools
import numpy as np
import time
import SimpleITK as sitk
import logging
from collections import OrderedDict

from CIP.logic.SlicerUtil import SlicerUtil
from CIP.logic import Util
from CIP.logic import GeometryTopologyData, Point
from CIP.ui import CaseReportsWidget, MIPViewerWidget

from FeatureWidgetHelperLib import FeatureExtractionLogic
import FeatureWidgetHelperLib
import FeatureExtractionLib

#############################
# CIP_LesionModel
#############################
class CIP_LesionModel(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "Lung lesion analyzer"
        self.parent.categories = SlicerUtil.CIP_ModulesCategory
        self.parent.dependencies = [SlicerUtil.CIP_ModuleName]
        self.parent.contributors = ["Jorge Onieva (jonieva@bwh.harvard.edu)", "Applied Chest Imaging Laboratory",
                                    "Brigham and Women's Hospital"]
        self.parent.helpText = """This module allows to segment benign nodules and tumors in the lung.
            Besides, it analyzes a lot of different features inside the nodule and in its surroundings,
            in concentric spheres of different radius centered in the centroid of the nodule<br>
            A quick tutorial of the module can be found <a href='https://chestimagingplatform.org/files/chestimagingplatform/files/lung_lesion_analyzer.pdf'>here</a>"""
        self.parent.acknowledgementText = SlicerUtil.ACIL_AcknowledgementText


#############################
# CIP_LesionModelWidget
#############################
class CIP_LesionModelWidget(ScriptedLoadableModuleWidget):
    """Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent=None):
        """Widget constructor (existing module)"""
        ScriptedLoadableModuleWidget.__init__(self, parent)
        self.moduleName = "CIP_LesionModel"
        # from functools import partial
        # def onNodeAdded(self, caller, eventId, callData):
        #     """Node added to the Slicer scene"""
        #     if callData.GetClassName() == 'vtkMRMLScalarVolumeNode':
        #         self.__onVolumeAddedToScene__(callData)
        #
        # self.onNodeAdded = partial(onNodeAdded, self)
        # self.onNodeAdded.CallDataType = vtk.VTK_OBJECT
        # slicer.mrmlScene.AddObserver(slicer.vtkMRMLScene.NodeAddedEvent, self.onNodeAdded)

        self.__initVars__()

    def __initVars__(self):
        self.logic = CIP_LesionModelLogic()
        self.__featureClasses__ = None
        self.__storedColumnNames__ = None
        self.__analyzedSpheres__ = set()
        self.__showRadiomics__ = False

        # Timer for dynamic zooming
        self.zoomToSeedTimer = qt.QTimer()
        self.zoomToSeedTimer.setInterval(100)
        self.zoomToSeedTimer.timeout.connect(self.zoomToSeed)


    @property
    def storedColumnNames(self):
        """ Column names that will be stored in the CaseReportsWidget
        @return:
        """
        if self.__storedColumnNames__ is None:
            self.__storedColumnNames__ = ["CaseId", "Date", "NoduleId", "SphereRadius", "Threshold", "LesionType", "Seeds_LPS", "Axis"]
            # Create a single features list with all the "child" features
            self.__storedColumnNames__.extend(itertools.chain.from_iterable(iter(self.featureClasses.values())))
        return self.__storedColumnNames__

    @property
    def featureClasses(self):
        """ Dictionary that contains all MainFeature-ChildFeatures values
        @return:
        """
        if self.__featureClasses__ is None:
            self.__featureClasses__ = collections.OrderedDict()
            self.__featureClasses__["First-Order Statistics"] = ["Voxel Count", "Gray Levels", "Energy", "Entropy",
                                                                 "Minimum Intensity", "Maximum Intensity",
                                                                 "Mean Intensity",
                                                                 "Median Intensity", "Range", "Mean Deviation",
                                                                 "Root Mean Square", "Standard Deviation",
                                                                 "Ventilation Heterogeneity",
                                                                 "Skewness", "Kurtosis", "Variance", "Uniformity"]
            self.__featureClasses__["Morphology and Shape"] = ["Volume mm^3", "Volume cc", "Surface Area mm^2",
                                                               "Surface:Volume Ratio", "Compactness 1", "Compactness 2",
                                                               "Maximum 3D Diameter", "Spherical Disproportion",
                                                               "Sphericity"]
            self.__featureClasses__["Texture: GLCM"] = ["Autocorrelation", "Cluster Prominence", "Cluster Shade",
                                                        "Cluster Tendency", "Contrast", "Correlation",
                                                        "Difference Entropy",
                                                        "Dissimilarity", "Energy (GLCM)", "Entropy(GLCM)",
                                                        "Homogeneity 1",
                                                        "Homogeneity 2", "IMC1", "IDMN", "IDN", "Inverse Variance",
                                                        "Maximum Probability", "Sum Average", "Sum Entropy",
                                                        "Sum Variance",
                                                        "Variance (GLCM)"]  # IMC2 missing
            self.__featureClasses__["Texture: GLRL"] = ["SRE", "LRE", "GLN", "RLN", "RP", "LGLRE", "HGLRE", "SRLGLE",
                                                        "SRHGLE", "LRLGLE", "LRHGLE"]
            self.__featureClasses__["Geometrical Measures"] = ["Extruded Surface Area", "Extruded Volume",
                                                               "Extruded Surface:Volume Ratio"]
            self.__featureClasses__["Renyi Dimensions"] = ["Box-Counting Dimension", "Information Dimension",
                                                           "Correlation Dimension"]

            self.__featureClasses__[
                "Parenchymal Volume"] = FeatureExtractionLib.ParenchymalVolume.getAllEmphysemaDescriptions()

        return self.__featureClasses__

    @property
    def __evaluateSegmentationModeOn__(self):
        """ True when the user is reviewing the results of a previous segmentation
        @return: boolean
        """
        return self.evaluateSegmentationCheckbox.isChecked()

    @property
    def __printTimeCost__(self):
        """ Save the time cost for the analysis operations
        @return: boolean
        """
        return self.saveTimeCostCheckbox.isChecked()

    @property
    def lesionType(self):
        """ Unknown, Nodule or Tumor. This information will be saved in the GeometryTopologyData that
        stores the position of the seeds
        @return: text of the type
        """
        return self.lesionTypeRadioButtonGroup.checkedButton().text

    def setup(self):
        """This is called one time when the module GUI is initialized
        """
        ScriptedLoadableModuleWidget.setup(self)
        # self.timer = qt.QTimer()
        # self.timer.timeout.connect(self.checkAndRefreshModels)
        self.lastRefreshValue = -5000  # Just a value out of range

        #######################
        # Case selector area
        self.caseSeletorCollapsibleButton = ctk.ctkCollapsibleButton()
        self.caseSeletorCollapsibleButton.text = "Case selector"
        self.layout.addWidget(self.caseSeletorCollapsibleButton)
        # Layout within the dummy collapsible button. See http://doc.qt.io/qt-4.8/layout.html for more info about layouts
        self.caseSelectorLayout = qt.QGridLayout(self.caseSeletorCollapsibleButton)

        row = 0
        # Main volume selector
        self.inputVolumeLabel = qt.QLabel("Input volume")
        self.inputVolumeLabel.setStyleSheet("margin-left:5px")
        self.caseSelectorLayout.addWidget(self.inputVolumeLabel, row, 0)

        self.inputVolumeSelector = slicer.qMRMLNodeComboBox()
        self.inputVolumeSelector.nodeTypes = ("vtkMRMLScalarVolumeNode", "")
        self.inputVolumeSelector.selectNodeUponCreation = True
        self.inputVolumeSelector.autoFillBackground = True
        self.inputVolumeSelector.addEnabled = False
        self.inputVolumeSelector.noneEnabled = True
        self.inputVolumeSelector.removeEnabled = False
        self.inputVolumeSelector.showHidden = False
        self.inputVolumeSelector.showChildNodeTypes = False
        self.inputVolumeSelector.setMRMLScene(slicer.mrmlScene)
        # self.inputVolumeSelector.sortFilterProxyModel().setFilterRegExp(self.logic.INPUTVOLUME_FILTER_REGEXPR)
        # self.volumeSelector.setStyleSheet("margin:0px 0 0px 0; padding:2px 0 2px 5px")
        self.caseSelectorLayout.addWidget(self.inputVolumeSelector, row, 1, 1, 3)

        # Load / save seeds button
        row += 1
        self.loadSeedsButton = qt.QPushButton()
        self.loadSeedsButton.text = "Load seeds from XML"
        self.loadSeedsButton.toolTip = "Load the current seeds and lesion type for batch analysis in a XML file"
        self.loadSeedsButton.setIcon(qt.QIcon("{0}/Load.png".format(SlicerUtil.CIP_ICON_DIR)))
        self.loadSeedsButton.setIconSize(qt.QSize(16, 16))
        # self.loadSeedsButton.setMaximumWidth(150)
        self.loadSeedsButton.setStyleSheet("margin: 10px 0 10px 5px; height: 30px")
        # self.loadSeedsButton.setVisible(False)
        self.caseSelectorLayout.addWidget(self.loadSeedsButton, row, 0)

        self.saveSeedsButton = qt.QPushButton()
        self.saveSeedsButton.text = "Save to XML"
        self.saveSeedsButton.toolTip = "Save the current seeds and lesion type for batch analysis in a XML file"
        self.saveSeedsButton.setIcon(qt.QIcon("{0}/Save.png".format(SlicerUtil.CIP_ICON_DIR)))
        self.saveSeedsButton.setIconSize(qt.QSize(16, 16))
        self.saveSeedsButton.setStyleSheet("margin: 10px 0; height: 30px")
        # self.saveSeedsButton.setMaximumWidth(150)
        self.caseSelectorLayout.addWidget(self.saveSeedsButton, row, 1)

        # MIP frame
        row += 1
        self.enhanceVisualizationCheckbox = qt.QCheckBox("Enhance visualization (MIP)")
        self.enhanceVisualizationCheckbox.setStyleSheet("margin: 10px 0 10px 8px; font-weight: bold;")
        self.caseSelectorLayout.addWidget(self.enhanceVisualizationCheckbox, row, 0, 1, 4)

        row += 1
        self.mipFrame = qt.QFrame()
        self.mipFrame.setFrameStyle(0x0002 | 0x0010)
        self.mipFrame.lineWidth = 2
        self.mipFrame.visible = False
        self.mipFrame.setStyleSheet("background-color: #EEEEEE")
        self.caseSelectorLayout.addWidget(self.mipFrame, row, 0, 1, 4)

        self.mipLayout = qt.QVBoxLayout(self.mipFrame)
        self.mipViewer = MIPViewerWidget(self.mipFrame, MIPViewerWidget.CONTEXT_VASCULATURE)
        self.mipViewer.setup()

        #######################
        # Nodule segmentation area
        self.noduleSegmentationCollapsibleButton = ctk.ctkCollapsibleButton()
        self.noduleSegmentationCollapsibleButton.text = "Nodule segmentation"
        self.layout.addWidget(self.noduleSegmentationCollapsibleButton)
        # Layout within the dummy collapsible button. See http://doc.qt.io/qt-4.8/layout.html for more info about layouts
        self.noduleSegmentationLayout = qt.QGridLayout(self.noduleSegmentationCollapsibleButton)
        row = 0
        self.noduleSegmentationLayout.addWidget(qt.QLabel("Select nodule: "), row, 0)

        self.nodulesComboBox = qt.QComboBox()
        self.noduleSegmentationLayout.addWidget(self.nodulesComboBox, row, 1)

        self.addNewNoduleButton = ctk.ctkPushButton()
        self.addNewNoduleButton.text = "New nodule"
        self.addNewNoduleButton.toolTip = "Add a new nodule"
        self.addNewNoduleButton.setIcon(SlicerUtil.getIcon("Plus.png"))
        self.addNewNoduleButton.setIconSize(qt.QSize(16, 16))
        self.addNewNoduleButton.setStyleSheet("font-weight:bold; font-size:12px; color: white; background-color:#274EE2;")
        self.noduleSegmentationLayout.addWidget(self.addNewNoduleButton, row, 2)

        self.jumpToNoduleButton = ctk.ctkPushButton()
        self.jumpToNoduleButton.toolTip = "Jump to nodule slice"
        self.jumpToNoduleButton.setIcon(qt.QIcon(":/Icons/ViewFeaturesVisible.png"))
        self.jumpToNoduleButton.setIconSize(qt.QSize(20, 20))
        self.jumpToNoduleButton.setFixedSize(qt.QSize(32, 32))
        self.noduleSegmentationLayout.addWidget(self.jumpToNoduleButton, row, 3)

        # NODULE FRAME
        row += 1
        self.noduleFrame = qt.QFrame()
        self.noduleFrameLayout = qt.QGridLayout(self.noduleFrame)
        self.noduleSegmentationLayout.addWidget(self.noduleFrame, row, 0, 1, 4)

        # Type of nodule
        noduleRow = 0
        self.lesionTypeLabel = qt.QLabel("Lesion type:")
        self.lesionTypeLabel.setFixedWidth(100)
        self.lesionTypeLabel.setStyleSheet("margin:5px 0 0 5px")
        self.noduleFrameLayout.addWidget(self.lesionTypeLabel, noduleRow, 0)
        self.lesionTypeRadioButtonGroup = qt.QButtonGroup()
        button = qt.QRadioButton("Unknown")
        button.setChecked(True)
        button.setStyleSheet("margin: 10px 0")
        self.lesionTypeRadioButtonGroup.addButton(button, 0)
        self.noduleFrameLayout.addWidget(button, noduleRow, 1)
        button = qt.QRadioButton("Nodule")
        button.setStyleSheet("margin: 10px 0")
        self.lesionTypeRadioButtonGroup.addButton(button, 1)
        self.noduleFrameLayout.addWidget(button, noduleRow, 2)
        button = qt.QRadioButton("Tumor")
        button.setStyleSheet("margin: 10px 0")
        self.lesionTypeRadioButtonGroup.addButton(button, 2)
        self.noduleFrameLayout.addWidget(button, noduleRow, 3)

        # Add/Remove seeds buttons
        noduleRow += 1
        self.labelAddedSeeds = qt.QLabel("Seeds / Axis:")
        self.labelAddedSeeds.setFixedWidth(100)
        self.labelAddedSeeds.setStyleSheet("margin: 10px 0 0 5px")
        self.noduleFrameLayout.addWidget(self.labelAddedSeeds, noduleRow, 0)
        self.addSeedButton = ctk.ctkPushButton()
        # self.addSeedButton.text = "Add new seed"
        self.addSeedButton.objectName = "AddSeed"
        self.addSeedButton.toolTip = "Click in the button and add a new seed in the volume. " \
                                         "You can use MIP proyection by clicking in \"Enhance visualization\" checkbox"
        self.addSeedButton.setIcon(SlicerUtil.getIcon("WelcomeFiducialWithArrow-Original.png"))
        self.addSeedButton.setIconSize(qt.QSize(16, 16))
        # self.addSeedButton.setStyleSheet("margin: 10px")
        self.addSeedButton.checkable = True
        # self.addSeedButton.enabled = False
        # self.addSeedButton.setMinimumSize(qt.QSize(45, 30))
        self.addSeedButton.setFixedWidth(25)
        self.noduleFrameLayout.addWidget(self.addSeedButton, noduleRow, 1)
        # self.addSeedButton.connect('clicked(bool)', self.__onAddFiducialButtonClicked__)

        self.removeSeedsButton = ctk.ctkPushButton()
        # self.removeSeedsButton.text = "Remove seeds"
        self.removeSeedsButton.setIcon(qt.QIcon(":/Icons/SnapshotDelete.png"))
        self.removeSeedsButton.setIconSize(qt.QSize(16, 16))
        # self.removeSeedsButton.setStyleSheet("margin: 10px")
        self.removeSeedsButton.objectName = "RemoveSeed"
        self.removeSeedsButton.toolTip = "Remove the selected seed/s"
        self.removeSeedsButton.setFixedWidth(25)
        # self.removeSeedsButton.setIcon(SlicerUtil.getIcon("WelcomeFiducialWithArrow-Original.png"))
        # self.removeSeedsButton.setIconSize(qt.QSize(16, 16))
        # self.removeSeedsButton.checkable = True
        # self.removeSeedsButton.enabled = False
        # self.removeSeedsButton.setFixedSize(qt.QSize(115, 30))
        self.noduleFrameLayout.addWidget(self.removeSeedsButton, noduleRow, 2)

        # Show/Hide calipers
        self.showAxisButton = ctk.ctkPushButton()
        self.showAxisButton.checkable = True
        self.showAxisButton.setIcon(SlicerUtil.getIcon("rulers.png"))
        self.showAxisButton.setIconSize(qt.QSize(16, 16))
        self.showAxisButton.toolTip = "Set nodule axis manually"
        self.showAxisButton.setFixedWidth(25)
        self.noduleFrameLayout.addWidget(self.showAxisButton, noduleRow, 3)

        # Container for the fiducials
        noduleRow += 1
        self.seedsContainerFrame = qt.QFrame()
        self.seedsContainerFrame.setLayout(qt.QVBoxLayout())
        self.seedsContainerFrame.setFrameStyle(0x0032)
        self.seedsContainerFrame.setStyleSheet("margin: 5px 0 0 5px")
        self.noduleFrameLayout.addWidget(self.seedsContainerFrame, noduleRow, 0, 1, 4)
        #self.seedsRadioButtonGroup = qt.QButtonGroup()


        # Maximum radius / Solid checkbox
        noduleRow += 1
        self.labelMaxRad = qt.QLabel("Max. lesion radius (mm)")
        self.labelMaxRad.setStyleSheet("margin: 20px 0 0 5px")
        self.labelMaxRad.toolTip = "Maximum radius for the tumor. Recommended: 30 mm for humans and 3 mm for small animals"
        self.noduleFrameLayout.addWidget(self.labelMaxRad, noduleRow, 0)

        self.maximumRadiusSpinbox = qt.QSpinBox()
        self.maximumRadiusSpinbox.minimum = 0
        self.maximumRadiusSpinbox.setStyleSheet("margin-top: 15px")
        self.maximumRadiusSpinbox.setFixedWidth(50)
        self.maximumRadiusSpinbox.toolTip = "Maximum radius for the tumor. Recommended: 30 mm for humans and 3 mm for small animals"
        self.noduleFrameLayout.addWidget(self.maximumRadiusSpinbox, noduleRow, 1)

        self.solidLesionCb = qt.QCheckBox()
        self.solidLesionCb.setText("Part solid lesion")
        self.solidLesionCb.setChecked(False)
        self.solidLesionCb.setStyleSheet("margin-top: 15px")
        self.noduleFrameLayout.addWidget(self.solidLesionCb, noduleRow, 2)

        # Run segmentation button
        noduleRow += 1
        self.segmentButton = qt.QPushButton()
        self.segmentButton.text = "Segment nodule"
        self.segmentButton.toolTip = "Run the segmentation algorithm"
        # self.segmentButton.setIcon(qt.QIcon("{0}/Reload.png".format(SlicerUtil.CIP_ICON_DIR)))
        # self.segmentButton.setIconSize(qt.QSize(20, 20))
        self.segmentButton.setStyleSheet(
            "font-weight:bold; font-size:12px; color: white; background-color:#274EE2; margin-top:10px;")
        self.segmentButton.setFixedHeight(35)
        self.noduleFrameLayout.addWidget(self.segmentButton, noduleRow, 0)

        label = qt.QLabel("Nodule labelmap")
        label.setContentsMargins(30, 10, 20, 0)
        self.noduleFrameLayout.addWidget(label, noduleRow, 1)

        self.noduleLabelmapVolumeSelector = slicer.qMRMLNodeComboBox()
        self.noduleLabelmapVolumeSelector.setContentsMargins(0, 10, 0, 0)
        self.noduleLabelmapVolumeSelector.nodeTypes = ("vtkMRMLLabelMapVolumeNode", "")
        self.noduleLabelmapVolumeSelector.selectNodeUponCreation = False
        self.noduleLabelmapVolumeSelector.autoFillBackground = True
        self.noduleLabelmapVolumeSelector.addEnabled = False
        self.noduleLabelmapVolumeSelector.noneEnabled = False
        self.noduleLabelmapVolumeSelector.removeEnabled = False
        self.noduleLabelmapVolumeSelector.showHidden = False
        self.noduleLabelmapVolumeSelector.showChildNodeTypes = False
        self.noduleLabelmapVolumeSelector.setMRMLScene(slicer.mrmlScene)
        # self.inputVolumeSelector.sortFilterProxyModel().setFilterRegExp(self.logic.INPUTVOLUME_FILTER_REGEXPR)
        # self.volumeSelector.setStyleSheet("margin:0px 0 0px 0; padding:2px 0 2px 5px")
        self.noduleFrameLayout.addWidget(self.noduleLabelmapVolumeSelector, noduleRow, 2, 1, 2)


        noduleRow += 1
        self.removeNoduleButton = qt.QPushButton()
        self.removeNoduleButton.text = "Remove nodule"
        self.removeNoduleButton.toolTip = "Remove the active nodule"
        self.removeNoduleButton.setIcon(qt.QIcon("{0}/delete.png".format(SlicerUtil.CIP_ICON_DIR)))
        self.removeNoduleButton.setStyleSheet("margin-top:10px;")
        self.removeNoduleButton.setIconSize(qt.QSize(20, 20))
        self.removeNoduleButton.setMinimumSize(130, 40)
        self.noduleFrameLayout.addWidget(self.removeNoduleButton, noduleRow, 0)

        # CLI progress bar
        noduleRow += 1
        self.progressBar = slicer.qSlicerCLIProgressBar()
        self.progressBar.visible = False
        self.noduleFrameLayout.addWidget(self.progressBar, noduleRow, 0, 1, 3)

        # Threshold
        noduleRow += 1
        self.selectThresholdLabel = qt.QLabel("Select a threshold:")
        self.selectThresholdLabel.setStyleSheet("margin: 10px 0 0 5px")
        self.selectThresholdLabel.setToolTip("Move the slider for a fine tuning segmentation")
        self.noduleFrameLayout.addWidget(self.selectThresholdLabel, noduleRow, 0)
        self.distanceLevelSlider = qt.QSlider()
        self.distanceLevelSlider.orientation = 1  # Horizontal
        self.distanceLevelSlider.minimum = -50  # Ad-hoc value
        self.distanceLevelSlider.maximum = 50
        self.distanceLevelSlider.setStyleSheet("margin-top:10px;padding-top:20px")
        self.distanceLevelSlider.setToolTip("Move the slider for a fine tuning segmentation")
        self.noduleFrameLayout.addWidget(self.distanceLevelSlider, noduleRow, 1, 1, 3)

        #####
        ## RADIOMICS SECTION
        # used to map feature class to a list of auto-generated feature checkbox widgets
        self.featureWidgets = collections.OrderedDict()
        for key in list(self.featureClasses.keys()):
            self.featureWidgets[key] = list()

        self.radiomicsCollapsibleButton = ctk.ctkCollapsibleButton()
        self.radiomicsCollapsibleButton.text = "Radiomics"
        self.layout.addWidget(self.radiomicsCollapsibleButton)
        self.radiomicsLayout = qt.QFormLayout(self.radiomicsCollapsibleButton)

        self.noduleLabelmapLabel = qt.QLabel("Nodule labelmap")
        self.noduleLabelmapLabel.setStyleSheet("margin: 10px 0")
        # self.noduleLabelmapSelector = slicer.qMRMLNodeComboBox()
        # self.noduleLabelmapSelector.setStyleSheet("margin: 10px 0")
        # self.noduleLabelmapSelector.nodeTypes = ("vtkMRMLLabelMapVolumeNode", "")
        # self.noduleLabelmapSelector.selectNodeUponCreation = False
        # self.noduleLabelmapSelector.addEnabled = False
        # self.noduleLabelmapSelector.noneEnabled = True
        # self.noduleLabelmapSelector.removeEnabled = False
        # self.noduleLabelmapSelector.showHidden = False
        # self.noduleLabelmapSelector.showChildNodeTypes = False
        # self.noduleLabelmapSelector.setMRMLScene(slicer.mrmlScene)
        # self.noduleLabelmapSelector.toolTip = "Labelmap with the segmented nodule"
        # self.noduleLabelmapSelector.sortFilterProxyModel().setFilterRegExp(self.logic.LESION_LABELMAP_FILTER_REGEXPR)
        # self.radiomicsLayout.addRow(self.noduleLabelmapLabel, self.noduleLabelmapSelector)

        # auto-generate QTabWidget Tabs and QCheckBoxes (subclassed in FeatureWidgetHelperLib)
        self.tabsFeatureClasses = FeatureWidgetHelperLib.CheckableTabsWidget()
        self.radiomicsLayout.addRow(self.tabsFeatureClasses)

        # Labelmap selector (just for parenchymal volume analysis)
        self.parenchymaLabelmapSelector = slicer.qMRMLNodeComboBox()
        self.parenchymaLabelmapSelector.nodeTypes = ("vtkMRMLLabelMapVolumeNode", "")
        self.parenchymaLabelmapSelector.selectNodeUponCreation = False
        self.parenchymaLabelmapSelector.addEnabled = False
        self.parenchymaLabelmapSelector.noneEnabled = True
        self.parenchymaLabelmapSelector.removeEnabled = False
        self.parenchymaLabelmapSelector.showHidden = False
        self.parenchymaLabelmapSelector.showChildNodeTypes = False
        self.parenchymaLabelmapSelector.setMRMLScene(slicer.mrmlScene)
        self.parenchymaLabelmapSelector.toolTip = "Select a labelmap if you want to run Parenchymal Volume analysis"
        # self.mainAreaLayout.addRow("Select a labelmap", self.labelMapSelector)

        # Features
        gridWidth, gridHeight = 3, 9
        for featureClass in self.featureClasses:
            # by default, features from the following features classes are checked:
            if featureClass in ["First-Order Statistics", "Morphology and Shape"]:
                check = True
            else:
                check = False
            tabFeatureClass = qt.QWidget()
            tabFeatureClass.setLayout(qt.QGridLayout())
            if featureClass == "Parenchymal Volume":
                label = qt.QLabel("Select a labelmap")
                tabFeatureClass.layout().addWidget(label, 0, 0)
                tabFeatureClass.layout().addWidget(self.parenchymaLabelmapSelector, 0, 1, 1, 2)
                gridLayoutCoordinates = ((row, col) for col in range(gridWidth) for row in range(1, gridHeight + 1))
            else:
                gridLayoutCoordinates = ((row, col) for col in range(gridWidth) for row in range(gridHeight))
            for featureName in self.featureClasses[featureClass]:
                row, col = next(gridLayoutCoordinates, None)
                if featureName is None or row is None or col is None:
                    break
                featureCheckboxWidget = FeatureWidgetHelperLib.FeatureWidget()
                featureCheckboxWidget.Setup(featureName=featureName, checkStatus=check)

                tabFeatureClass.layout().addWidget(featureCheckboxWidget, row, col)
                self.featureWidgets[featureClass].append(featureCheckboxWidget)

            self.tabsFeatureClasses.addTab(tabFeatureClass, featureClass, self.featureWidgets[featureClass],
                                           checkStatus=check)

        self.tabsFeatureClasses.setCurrentIndex(0)

        # Convert the ordered dictionary to a flat list that contains all the features
        self.featureWidgetList = list(itertools.chain.from_iterable(list(self.featureWidgets.values())))
        self.featureMainCategoriesStringList = list(self.featureWidgets.keys())


        # Different radius selection
        self.structuresLabel = qt.QLabel("Structures to analyze:")
        self.structuresLabel.setStyleSheet("margin-top: 10px")
        self.radiomicsLayout.addRow(self.structuresLabel, None)


        self.spheresButtonGroup = qt.QButtonGroup()
        self.spheresButtonGroup.setExclusive(False)
        self.showSpheresButtonGroup = qt.QButtonGroup()

        fixedSizePolicy = qt.QSizePolicy()
        fixedSizePolicy.setHorizontalPolicy(0)

        # SPHERES
        self.sphereRadiusFrame = qt.QFrame()
        sp_id = 0
        self.sphereRadiusFrameLayout = qt.QGridLayout(self.sphereRadiusFrame)
        self.noduleCheckbox = qt.QCheckBox()
        self.noduleCheckbox.setText("Nodule")
        self.noduleCheckbox.setSizePolicy(fixedSizePolicy)
        self.noduleCheckbox.setChecked(True)
        self.spheresButtonGroup.addButton(self.noduleCheckbox, sp_id)
        self.sphereRadiusFrameLayout.addWidget(self.noduleCheckbox, 0, 0)
        showSphereRadioButton = qt.QRadioButton("(Show just nodule)")
        showSphereRadioButton.setChecked(True)
        self.sphereRadiusFrameLayout.addWidget(showSphereRadioButton, 0, 1)
        self.showSpheresButtonGroup.addButton(showSphereRadioButton, sp_id)

        # Go over all the possible radius
        r = 1
        for rad in itertools.chain.from_iterable(list(self.logic.__spheresDict__.values())):
            sp_id = int(rad*10)    # Multiply by 10 to avoid decimals
            sphereCheckBox = qt.QCheckBox()
            sphereCheckBox.setText("{0} mm radius".format(rad))
            sphereCheckBox.setSizePolicy(fixedSizePolicy)
            self.spheresButtonGroup.addButton(sphereCheckBox, sp_id)
            self.sphereRadiusFrameLayout.addWidget(sphereCheckBox, r, 0)
            showSphereRadioButton = qt.QRadioButton("Show")
            # showSphereCheckbox.setVisible(False)
            self.sphereRadiusFrameLayout.addWidget(showSphereRadioButton, r, 1)
            self.showSpheresButtonGroup.addButton(showSphereRadioButton, sp_id)
            r += 1

        self.otherRadiusCheckbox = qt.QCheckBox()
        sp_id = -2
        self.otherRadiusCheckbox.setText("Other (mm sphere radius)")
        self.otherRadiusCheckbox.setSizePolicy(fixedSizePolicy)
        self.spheresButtonGroup.addButton(self.otherRadiusCheckbox, sp_id)
        self.sphereRadiusFrameLayout.addWidget(self.otherRadiusCheckbox, r, 0)
        self.otherRadiusTextbox = qt.QLineEdit()
        self.otherRadiusTextbox.setMaximumWidth(50)
        self.sphereRadiusFrameLayout.addWidget(self.otherRadiusTextbox, r, 1)
        self.otherRadiusShowSphereRadioButton = qt.QRadioButton("Show")
        # showSphereCheckbox.setVisible(False)
        self.sphereRadiusFrameLayout.addWidget(self.otherRadiusShowSphereRadioButton, r, 2)
        self.showSpheresButtonGroup.addButton(self.otherRadiusShowSphereRadioButton, sp_id)

        self.radiomicsLayout.addWidget(self.sphereRadiusFrame)

        # Run Analysis
        self.runAnalysisButton = qt.QPushButton("Analyze!")
        self.runAnalysisButton.toolTip = "Run all the checked analysis"
        self.runAnalysisButton.setIcon(qt.QIcon("{0}/analyze.png".format(SlicerUtil.CIP_ICON_DIR)))
        self.runAnalysisButton.setIconSize(qt.QSize(24, 24))
        self.runAnalysisButton.setFixedWidth(150)
        self.runAnalysisButton.setStyleSheet("font-weight:bold; font-size:12px; color: white; background-color:#274EE2")

        self.analyzeAllNodulesCheckbox = qt.QCheckBox()
        self.analyzeAllNodulesCheckbox.text = "Analyze all nodules"
        self.analyzeAllNodulesCheckbox.setStyleSheet("margin:10px 0 0 8px; font-weight: bold")

        self.radiomicsLayout.addRow(self.runAnalysisButton, self.analyzeAllNodulesCheckbox)

        # Reports widget
        self.analysisResultsCollapsibleButton = ctk.ctkCollapsibleButton()
        self.analysisResultsCollapsibleButton.text = "Results of the analysis"
        self.layout.addWidget(self.analysisResultsCollapsibleButton)
        self.reportsLayout = qt.QHBoxLayout(self.analysisResultsCollapsibleButton)

        columns = CaseReportsWidget.getColumnKeysNormalizedDictionary(self.storedColumnNames)
        self.reportsWidget = CaseReportsWidget(self.moduleName, columns,
                                               parentWidget=self.analysisResultsCollapsibleButton)
        self.reportsWidget.setup()
        self.reportsWidget.showWarnigMessages(False)

        ######################
        # Case navigator widget
        if SlicerUtil.isSlicerACILLoaded():
            # Add a case list navigator
            caseNavigatorCollapsibleButton = ctk.ctkCollapsibleButton()
            caseNavigatorCollapsibleButton.text = "Case navigator (advanced)"
            self.layout.addWidget(caseNavigatorCollapsibleButton)
            # caseNavigatorAreaLayout = qt.QHBoxLayout(caseNavigatorCollapsibleButton)

            from ACIL.ui import CaseNavigatorWidget
            self.caseNavigatorWidget = CaseNavigatorWidget("CIP_LesionModel", caseNavigatorCollapsibleButton)
            self.caseNavigatorWidget.setup()
            # self.caseNavigatorWidget.addObservable(self.caseNavigatorWidget.EVENT_PRE_VOLUME_LOAD, self.__onPreVolumeLoad__)

        #######################
        # Advanced parameters area
        self.advancedParametersCollapsibleButton = ctk.ctkCollapsibleButton()
        self.advancedParametersCollapsibleButton.text = "Advanced parameters"
        self.advancedParametersCollapsibleButton.collapsed = True
        self.layout.addWidget(self.advancedParametersCollapsibleButton)
        # Layout within the dummy collapsible button. See http://doc.qt.io/qt-4.8/layout.html for more info about layouts
        self.advancedParametersLayout = qt.QFormLayout(self.advancedParametersCollapsibleButton)
        self.evaluateSegmentationCheckbox = qt.QCheckBox()
        self.evaluateSegmentationCheckbox.setText("Enable saving seeds mode for batch processing")
        self.advancedParametersLayout.addWidget(self.evaluateSegmentationCheckbox)
        self.saveTimeCostCheckbox = qt.QCheckBox()
        self.saveTimeCostCheckbox.setText("Save time cost of every operation")
        self.advancedParametersLayout.addWidget(self.saveTimeCostCheckbox)

        # Add vertical spacer
        self.layout.addStretch(1)

        ######################
        # Connections
        self.inputVolumeSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.__onInputVolumeChanged__)
        self.addNewNoduleButton.connect('clicked(bool)', self.__onAddNoduleButtonClicked__)
        self.jumpToNoduleButton.connect('clicked(bool)', self.__onJumpToNoduleButtonClicked__)
        self.nodulesComboBox.connect("currentIndexChanged (int)", self.__onNodulesComboboxCurrentIndexChanged__)
        self.noduleLabelmapVolumeSelector.connect("currentNodeChanged (vtkMRMLNode*)", self.__onLabelmapVolumeSelectorCurrentIndexChanged__)
        self.enhanceVisualizationCheckbox.connect("stateChanged(int)", self.__onEnhanceVisualizationCheckChanged__)
        self.addSeedButton.connect('clicked()', self.__onAddSeedButtonClicked__)
        self.removeSeedsButton.connect('clicked()', self.__onRemoveSeedsButtonClicked__)
        self.showAxisButton.connect('clicked()', self.__onShowAxisButtonClicked__)
        self.segmentButton.connect('clicked()', self.__onSegmentButtonClicked__)
        self.distanceLevelSlider.connect('sliderReleased()', self.__onThresholdSegmentationChanged__)
        self.removeNoduleButton.connect('clicked()', self.__onRemoveNoduleButtonClicked__)
        self.lesionTypeRadioButtonGroup.connect("buttonClicked (QAbstractButton*)", self.__onLesionTypeChanged__)
        self.showSpheresButtonGroup.connect("buttonClicked(int)", self.__onShowSphereCheckboxClicked__)
        self.runAnalysisButton.connect('clicked()', self.__onRunAnalysisButtonClicked__)

        # self.reportsWidget.addObservable(self.reportsWidget.EVENT_SAVE_BUTTON_CLICKED, self.forceSaveReport)
        self.evaluateSegmentationCheckbox.connect("clicked()", self.refreshGUI)
        self.saveSeedsButton.connect("clicked()", self.saveCurrentSeedsToXML)
        self.loadSeedsButton.connect("clicked()", self.loadSeedsFromXML)
        self.saveTimeCostCheckbox.connect("stateChanged(int)", self.__onSaveTimeCostCheckboxClicked__)

        slicer.mrmlScene.AddObserver(slicer.vtkMRMLScene.EndCloseEvent, self.__onSceneClosed__)

        self.refreshGUI()

    @property
    def currentVolume(self):
        """
        Current active volume node
        @return:
        """
        return self.inputVolumeSelector.currentNode()

    @property
    def currentNoduleIndex(self):
        """
        Current index of the selected nodule
        @return:
        """
        return self.nodulesComboBox.itemData(self.nodulesComboBox.currentIndex)


    def refreshGUI(self):
        """ Configure the GUI elements based on the current configuration
        """
        # Show fiducials panel just if there is a main volume loaded
        if self.currentVolume is None:
            self.noduleSegmentationCollapsibleButton.visible = self.radiomicsCollapsibleButton.visible = False
            self.__removeFiducialsFrames__()
        else:
            self.noduleSegmentationCollapsibleButton.visible = True

        self.noduleFrame.visible = self.currentNoduleIndex is not None

        # Level slider, Features Selection and radiomics section active after running the segmentation algorithm
        self.selectThresholdLabel.visible = self.distanceLevelSlider.visible = \
            self.currentVolume is not None and \
            self.logic.getNthAlgorithmSegmentationNode(self.currentVolume, self.currentNoduleIndex) is not None

        # Show only sphere buttons for this working mode
        for button in self.spheresButtonGroup.buttons():
            button.setVisible(False)
        for button in self.showSpheresButtonGroup.buttons():
            button.setVisible(False)
        # Show spheres buttons just visible for the analyzed spheres
        if self.currentVolume:
            for rad in self.logic.getPredefinedSpheresDict(self.currentVolume):
                self.spheresButtonGroup.button(rad*10).setVisible(True)
                if self.logic.getNthSphereLabelmapNode(self.currentVolume, self.currentNoduleIndex, rad):
                    self.showSpheresButtonGroup.button(rad*10).setVisible(True)

            # Always show the "other" buttons
            self.otherRadiusCheckbox.setVisible(True)
            self.otherRadiusShowSphereRadioButton.setVisible(True)

        #self.progressBar.visible = self.distanceLevelSlider.enabled
        self.saveSeedsButton.visible = self.loadSeedsButton.visible = self.__evaluateSegmentationModeOn__
        self.reportsWidget.enableSaveButton(self.__evaluateSegmentationModeOn__)
        self.radiomicsCollapsibleButton.visible = self.__showRadiomics__


    def addNewNodule(self):
        """
        Add a new nodule to the scene
        @return: hiearchy node corresponding to the nodule
        """
        # Add the new hierarchy node to the scene
        hierNode = self.logic.addNewNodule(self.currentVolume)
        # Get the index of the added nodule node
        index = int(self.logic.shSceneNode.GetItemName(hierNode))
        # Add it to the combobox saving the index (we can't just use the combobox index because the user can clear elems)
        # Disable signals because we don't want the nodule to be active until we build all the required objects
        self.nodulesComboBox.blockSignals(True)
        self.nodulesComboBox.addItem("Nodule {}".format(index))
        self.nodulesComboBox.setItemData(self.nodulesComboBox.count - 1, index)
        self.nodulesComboBox.currentIndex = self.nodulesComboBox.count - 1

        # Add a listener to the fiducials node to know when the user added a new seed and register it
        fiducialsNode = self.logic.getNthFiducialsListNode(self.currentVolume, index)
        fiducialsNode.AddObserver(fiducialsNode.MarkupAddedEvent, self.__onAddedSeed__)

        # Lesion type
        self.lesionTypeRadioButtonGroup.buttons()[0].setChecked(True)
        self.logic.lesionTypes[(self.currentVolume, index)] = self.lesionTypeRadioButtonGroup.buttons()[0].text

        # Enable signals again
        self.nodulesComboBox.blockSignals(False)
        # Activate nodule
        self.setActiveNodule(index)
        # Set the cursor in Crosshair+fiducials mode
        SlicerUtil.setCrosshairCursor(True)
        SlicerUtil.setFiducialsCursorMode(True)

        # Uncheck fiducials button
        self.showAxisButton.setChecked(False)

        return hierNode

    def setActiveNodule(self, noduleIndex):
        """
        Set the specified nodule as active, setting the right Fiducials Node, Rulers Node, Model, etc.
        @param noduleIndex: nodule index (different from the combobox index!)
        @return:
        """
        # Set active Fiducials node
        markupsLogic = slicer.modules.markups.logic()
        # Hide first all the current markups
        for node in self.logic.getAllFiducialNodes(self.currentVolume):
            markupsLogic.SetAllMarkupsVisibility(node, False)
        markupNode = self.logic.getNthFiducialsListNode(self.currentVolume, noduleIndex)
        markupsLogic.SetActiveListID(markupNode)
        # Show markups
        markupsLogic.SetAllMarkupsVisibility(markupNode, True)

        # Update the seeds checkboxes
        # for i in range(1, len(self.seedsContainerFrame.children())):
        #     self.seedsContainerFrame.children()[i].delete()
        while len(self.seedsContainerFrame.children()) > 1:
            self.seedsContainerFrame.children()[1].delete()
        for i in range(markupNode.GetNumberOfMarkups()):
            self.addFiducialRow(markupNode, i)

        # Set active Rulers node
        annotationsLogic = slicer.modules.annotations.logic()
        # Hide first all the rulers
        for node in SlicerUtil.getNodesByClass("vtkMRMLAnnotationRulerNode"):
            node.SetDisplayVisibility(False)
        annotationsLogic.SetActiveHierarchyNodeID(
            self.logic.getNthRulersListNode(self.currentVolume, noduleIndex).GetID())

        # Show Nodule Labelmap (if it exists)
        self._showCurrentLabelmap_()

        # Nodule Model (if it exists).
        # Hide all the models first
        for node in SlicerUtil.getNodesByClass("vtkMRMLModelNode"):
            node.SetDisplayVisibility(False)
        model = self.logic.getNthNoduleModelNode(self.currentVolume, noduleIndex)
        if model:
            modelsLogic = slicer.modules.models.logic()
            modelsLogic.SetActiveModelNode(model)
            model.SetDisplayVisibility(True)

        self.noduleLabelmapVolumeSelector.setCurrentNode(self.logic.getNthNoduleLabelmapNode(self.currentVolume, noduleIndex))

        # Jump to the central seed (if it exist)
        if markupNode.GetNumberOfMarkups() > 0:
            pos = [0,0,0]
            markupNode.GetNthFiducialPosition(0, pos)
            SlicerUtil.jumpToSeed(pos)


    def setAddSeedsMode(self, enabled):
        """ When enabled, the cursor will be enabled to add new fiducials that will be used for the segmentation
        @param enabled: boolean
        """
        applicationLogic = slicer.app.applicationLogic()
        if enabled:
            if self.__validateInputVolumeSelection__():
                # Get the fiducials node
                fiducialsNodeList = self.logic.getNthFiducialsListNode(self.currentVolume, self.currentNoduleIndex)
                # Set the cursor to draw fiducials
                markupsLogic = slicer.modules.markups.logic()
                markupsLogic.SetActiveListID(fiducialsNodeList)
                selectionNode = applicationLogic.GetSelectionNode()
                #selectionNode.SetReferenceActivePlaceNodeClassName("vtkMRMLMarkupsFiducialNode")

                # Enable fiducials mode
                SlicerUtil.setFiducialsCursorMode(True, False)
        else:
            # Regular cursor mode (not fiducials)
            SlicerUtil.setFiducialsCursorMode(False)


    def addFiducialRow(self, fiducialsNode, fiducialPosition):
        """ Add a new row in the fiducials checkboxes section
        @param fiducialsNode:
        """
        # n = fiducialsNode.GetNumberOfFiducials()
        pos = [0,0,0]
        fiducialsNode.GetNthFiducialPosition(fiducialPosition, pos)
        seedCheckbox = qt.QCheckBox()
        seedCheckbox.text = "{:.3f}, {:.3f}, {:.3f}".format(pos[0], pos[1], pos[2])
        if fiducialPosition == 0:
            # First seed
            seedCheckbox.text += " (Center)"
            seedCheckbox.checked = False
            # Disable
            seedCheckbox.enabled = False
        self.seedsContainerFrame.layout().addWidget(seedCheckbox)
        self.addSeedButton.setChecked(False)
        SlicerUtil.setFiducialsCursorMode(False)
        self.refreshGUI()

    def resetNodulesCheckboxes(self):
        """
        Remove all the seeds checkboxes for a nodule
        @return:
        """
        layout = self.seedsContainerFrame.layout()
        # Remove current nodules
        for child in self.seedsContainerFrame.children():
            if isinstance(child, qt.QCheckBox):
                layout.removeWidget(child)


    def showAxis(self, volume, noduleIndex, show):
        """
        Show/Hide the axis for the nodule. If the rulers have not been created, create default ones around the central seed
        with the maximum radius for this volume.
        @param volume:
        @param noduleIndex:
        @param show: show or hide the axis
        """
        rulerNodeParent = self.logic.getNthRulersListNode(volume, noduleIndex)
        col = vtk.vtkCollection()
        rulerNodeParent.GetAllChildren(col)

        if col.GetNumberOfItems() == 0 and show:
            # No axis created. Create them if seed exists and we should show them
            markupsNode = self.logic.getNthFiducialsListNode(volume, noduleIndex)
            if markupsNode.GetNumberOfMarkups() == 0:
                qt.QMessageBox.warning(slicer.util.mainWindow(), 'Seed not found',
                                           'Please add at least one seed for the current nodule')
                return
            # Get the coordinates of the central seed
            pos = [0, 0, 0]
            markupsNode.GetNthFiducialPosition(0, pos)
            # Create rulers around the seed with maximum radius
            self.logic.createDefaultAxis(volume, noduleIndex, pos, self.maximumRadiusSpinbox.value)

        # Show/Hide axis
        rulerNodeParent.GetAllChildren(col)
        for i in range(col.GetNumberOfItems()):
            node = col.GetItemAsObject(i)
            node.SetDisplayVisibility(show)

    def runNoduleSegmentation(self):
        """ Run the nodule segmentation through a CLI
        """
        maximumRadius = self.maximumRadiusSpinbox.value
        partsSolid = self.solidLesionCb.isChecked()
        if self.__validateInputVolumeSelection__():
            result = self.logic.callNoduleSegmentationCLI(self.inputVolumeSelector.currentNodeID, self.currentNoduleIndex,
                                                          maximumRadius, partsSolid,
                                                          self.__onCLISegmentationFinished__)
            self.progressBar.setCommandLineModuleNode(result)
            self.progressBar.visible = True
            SlicerUtil.setSetting(self.moduleName, "maximumRadius", maximumRadius)

            # Calculate meshgrid in parallel
            # self.logic.buildMeshgrid(self.inputVolumeSelector.currentNode())

    def runAnalysis(self, volume, noduleIndex):
        """ Compute all the features that are currently selected, for the nodule and/or for
        the surrounding spheres
        """
        # build list of features and feature classes based on what is checked by the user
        self.selectedMainFeaturesKeys = set()
        self.selectedFeatureKeys = set()
        self.analysisResults = dict()
        self.analysisResultsTiming = dict()
        self.__analyzedSpheres__ = set()

        for featureClass in self.featureWidgets:
            for widget in self.featureWidgets[featureClass]:
                if widget.checked:
                    self.selectedMainFeaturesKeys.add(featureClass)
                    self.selectedFeatureKeys.add(str(widget.text))

        # Preconditions
        if volume is None:
            # TODO: disable the button until segmentation is done
            qt.QMessageBox.warning(slicer.util.mainWindow(), "Select a volume",
                                   "Please select and segment an input volume")
            return
        # currentLabelmap = self.logic.getNthNoduleLabelmapNode(volume, noduleIndex)
        # if currentLabelmap is None:
        #     qt.QMessageBox.warning(slicer.util.mainWindow(), "Nodule not segmented",
        #                            "The current nodule has not being segmented yet")
        #     return
        if len(self.selectedFeatureKeys) == 0:
            qt.QMessageBox.information(slicer.util.mainWindow(), "Select a feature",
                                       "Please select at least one feature from the menu to calculate")
            return
        if "Parenchymal Volume" in self.selectedMainFeaturesKeys and self.parenchymaLabelmapSelector.currentNode() is None:
            qt.QMessageBox.warning(slicer.util.mainWindow(), "Select a labelmap",
                                   "Please select a segmented emphysema labelmap in the Parenchymal Volume tab")
            return

        if self.otherRadiusCheckbox.checked and int(self.otherRadiusTextbox.text) > self.logic.MAX_TUMOR_RADIUS:
            qt.QMessageBox.warning(slicer.util.mainWindow(), "Invalid value",
                                   "The radius of the sphere must have a maximum value of {0}".format(
                                       self.logic.MAX_TUMOR_RADIUS))
            return

        try:
            # Analysis for the volume and the nodule:
            keyName = "{}_{}".format(volume.GetName(), noduleIndex)
            start = time.time()
            if self.noduleCheckbox.checked:
                currentLabelmapArray = slicer.util.array(self.logic.getNthNoduleLabelmapNode(volume, noduleIndex).GetID())
                logic = FeatureExtractionLogic(volume, currentLabelmapArray,
                                               self.selectedMainFeaturesKeys.difference(["Parenchymal Volume"]),
                                               self.selectedFeatureKeys.difference(
                                                   self.featureClasses["Parenchymal Volume"]))

                print("******** Nodule analysis results...")
                t1 = start

                t2 = time.time()

                self.analysisResults[keyName] = collections.OrderedDict()
                self.analysisResultsTiming[keyName] = collections.OrderedDict()
                logic.run(self.analysisResults[keyName], self.logic.printTiming, self.analysisResultsTiming[keyName])

                # Print analysis results
                print((self.analysisResults[keyName]))

                if self.logic.printTiming:
                    print(("Elapsed time for the nodule analysis (TOTAL={0} seconds:".format(t2 - t1)))
                    print((self.analysisResultsTiming[keyName]))

            # Check in any sphere has been selected for the analysis, because otherwise it's not necessary to calculate the distance map
            anySphereChecked = False
            for r in self.logic.getPredefinedSpheresDict(self.currentVolume):
                if self.spheresButtonGroup.button(r*10).isChecked():
                    anySphereChecked = True
                    break
            if self.otherRadiusCheckbox.checked and self.otherRadiusTextbox.text != "":
                anySphereChecked = True

            # if self.r15Checkbox.checked or self.r20Checkbox.checked or self.r25Checkbox.checked \
            #         or (self.rOtherCheckbox.checked and self.otherRadiusTextbox.text != ""):
            if anySphereChecked:
                if "Parenchymal Volume" in self.selectedMainFeaturesKeys:
                    # If the parenchymal volume analysis is required, we need the numpy array represeting the whole
                    # emphysema segmentation labelmap
                    labelmapWholeVolumeArray = slicer.util.array(self.parenchymaLabelmapSelector.currentNode().GetName())
                else:
                    labelmapWholeVolumeArray = None

                # print("DEBUG: analyzing spheres...")
                t1 = time.time()
                self.logic.getCurrentDistanceMap(volume, noduleIndex)
                if self.logic.printTiming:
                    print(("Time to get the current distance map: {0} seconds".format(time.time() - t1)))

                for r in self.logic.getPredefinedSpheresDict(self.currentVolume):
                    if self.spheresButtonGroup.button(r*10).isChecked():
                        self.runAnalysisSphere(volume, noduleIndex, r, labelmapWholeVolumeArray)
                        self.__analyzedSpheres__.add((noduleIndex,r))
                # if self.r15Checkbox.checked:
                #     self.runAnalysisSphere(15, labelmapWholeVolumeArray)
                #     self.__analyzedSpheres__.add(15)
                # if self.r20Checkbox.checked:
                #     self.runAnalysisSphere(20, labelmapWholeVolumeArray)
                #     self.__analyzedSpheres__.add(20)
                # if self.r25Checkbox.checked:
                #     self.runAnalysisSphere(25, labelmapWholeVolumeArray)
                #     self.__analyzedSpheres__.add(25)
                if self.otherRadiusCheckbox.checked:
                    r = int(self.otherRadiusTextbox.text)
                    self.runAnalysisSphere(volume, noduleIndex, r, labelmapWholeVolumeArray)
                    self.__analyzedSpheres__.add((noduleIndex,r))

            t = time.time() - start
            if self.logic.printTiming:
                print(("********* TOTAL ANALYSIS TIME: {0} SECONDS".format(t)))

            # Save the results in the report widget
            qt.QMessageBox.information(slicer.util.mainWindow(), "Process finished",
                                       "Analysis finished. Total time: {0} seconds. Click the \"Open\" button to see the results".format(t))

            self.refreshGUI()
        except StopIteration:
            qt.QMessageBox.warning(slicer.util.mainWindow(), "Process cancelled",
                                   "The process has been cancelled by the user")
        finally:
            self.saveReport(volume, noduleIndex, showConfirmation=False)

    def runAnalysisSphere(self, volume, noduleIndex, radius, parenchymaWholeVolumeArray=None):
        """ Run the selected features for an sphere of radius r (excluding the nodule itself)
        @param radius:
        @param parenchymaWholeVolumeArray: parenchyma volume (only used in parenchyma analysis). Numpy array
        """
        keyName = "{0}_r{1}_{2}".format(volume.GetName(), radius, noduleIndex)
        t1 = time.time()
        labelmapArray = self.logic.getSphereLabelMapArray(volume, noduleIndex, radius)
        getSphereTime = time.time() - t1
        if self.logic.printTiming:
            print(("Time elapsed to get a sphere labelmap of radius {0}: {1} seconds".format(radius, getSphereTime)))
        slicer.app.processEvents()
        if labelmapArray.max() == 0:
            # Nothing to analyze
            results = {}
            for key in self.selectedFeatureKeys:
                results[key] = 0
            self.analysisResults[keyName] = results
        else:
            logic = FeatureExtractionLogic(volume, labelmapArray, self.selectedMainFeaturesKeys,
                                           self.selectedFeatureKeys, "_r{}_{}".format(radius, noduleIndex), parenchymaWholeVolumeArray)
            t1 = time.time()
            self.analysisResults[keyName] = collections.OrderedDict()
            self.analysisResultsTiming[keyName] = collections.OrderedDict()
            logic.run(self.analysisResults[keyName], self.logic.printTiming, self.analysisResultsTiming[keyName])
            t2 = time.time()

            print(("********* Results for the sphere of radius {0}:".format(radius)))
            print((self.analysisResults[keyName]))
            if self.logic.printTiming:
                print(("*** Elapsed time for the sphere radius {0} analysis (TOTAL={1} seconds:".format(radius, t2 - t1)))
                print((self.analysisResultsTiming[keyName]))

    # def forceSaveReport(self):
    #     """ If basic report does not exist, it is created "on the fly"
    #     """
    #     keyName = self.inputVolumeSelector.currentNode().GetName()
    #     self.analysisResults = dict()
    #     self.analysisResults[keyName] = collections.OrderedDict()
    #     self.__saveBasicData__(keyName)
    #     self.saveReport(self.currentVolume, self.currentNoduleIndex)

    def saveReport(self, volume, noduleIndex, showConfirmation=True):
        """ Save the current values in a persistent csv file
        """
        #keyName = self.inputVolumeSelector.currentNode().GetName()
        keyName = "{}_{}".format(volume.GetName(), noduleIndex)
        self.__saveSubReport__(keyName, volume, noduleIndex)
        # Get all the spheres for this nodule
        for r in (s[1] for s in self.__analyzedSpheres__ if s[0]==noduleIndex):
            keyName = "{}_r{}_{}".format(volume.GetName(), r, noduleIndex)
            self.__saveSubReport__(keyName, volume, noduleIndex, r)
        # keyName = self.inputVolumeSelector.currentNode().GetName() + "__r15"
        # self.__saveSubReport__(keyName)
        # keyName = self.inputVolumeSelector.currentNode().GetName() + "__r20"
        # self.__saveSubReport__(keyName)
        # keyName = self.inputVolumeSelector.currentNode().GetName() + "__r25"
        # self.__saveSubReport__(keyName)
        # keyName = "{0}__r{1}".format(self.inputVolumeSelector.currentNode().GetName(), self.otherRadiusTextbox.text)
        # self.__saveSubReport__(keyName)
        if showConfirmation:
            qt.QMessageBox.information(slicer.util.mainWindow(), 'Data saved', 'The data were saved successfully')

    def saveCurrentSeedsToXML(self):
        """ Save the current selected seed to a GeometryTopologyData object that will be
        stored in the Results folder of the module, with the preffix _seedEvaluation.xml
        """
        dirPath = os.path.join(SlicerUtil.getModuleFolder(self.moduleName), "Results")
        Util.create_directory(dirPath)
        filePath = os.path.join(dirPath, self.currentVolume.GetName() + "_seedEvaluation.xml")
        geom = GeometryTopologyData()
        geom.coordinate_system = GeometryTopologyData.LPS

        # Spacing, Origin, Dimensions
        geom.spacing = self.currentVolume.GetSpacing()
        geom.origin = self.currentVolume.GetOrigin()
        geom.dimensions = self.currentVolume.GetImageData().GetDimensions()

        for nodule in self.logic.getAllNoduleKeys(self.currentVolume):
            fidNode = self.logic.getNthFiducialsListNode(self.currentVolume, nodule)
            for i in range(fidNode.GetNumberOfMarkups()):
                coords = [0,0,0]
                fidNode.GetNthFiducialPosition(i, coords)
                coords = Util.ras_to_lps(coords)
                descr = "{}-Unknown".format(nodule)
                if (self.currentVolume, nodule) in self.logic.lesionTypes:
                    if self.logic.lesionTypes[self.currentVolume, nodule] == 1:
                        descr = "{}-Nodule".format(nodule)
                    elif self.logic.lesionTypes[self.currentVolume, nodule] == 2:
                        descr = "{}-Tumor".format(nodule)
                geom.add_point(Point(0, 86, 0, coords, descr))

        geom.to_xml_file(filePath)
        qt.QMessageBox.information(slicer.util.mainWindow(), 'Data saved', 'The data were saved successfully in ' + filePath)

    def loadSeedsFromXML(self):
        """ Load all the seeds from a GeometryTopologyData object that is expected to be
        in Results folder of the module
        """
        if self.currentVolume is None:
            return

        #     self.logic.setActiveVolume(SlicerUtil.getFirstScalarNode().GetID())
        dirPath = os.path.join(SlicerUtil.getModuleFolder(self.moduleName), "Results")
        filePath = os.path.join(dirPath, self.currentVolume.GetName() + "_seedEvaluation.xml")
        geom = GeometryTopologyData.from_xml_file(filePath)
        noduleKeys = {}

        for point in geom.points:
            noduleKey = int(point.description.split("-")[0])
            if noduleKey not in noduleKeys:
                # New nodule
                hn = self.addNewNodule()
                index = int(hn.GetName())
                noduleKeys[noduleKey] = index
            else:
                index = noduleKeys[noduleKey]
            fidNode = self.logic.getNthFiducialsListNode(self.currentVolume, index)
            if geom.coordinate_system == geom.IJK:
                position = Util.ijk_to_ras(point.coordinate)
            elif geom.coordinate_system == geom.LPS:
                position = Util.lps_to_ras(point.coordinate)
            else:
                position = point.coordinate
            fidNode.AddFiducial(*position)
        SlicerUtil.setCrosshairCursor(False)
        SlicerUtil.setFiducialsCursorMode(False)
        # coords = Util.lps_to_ras(geom.points[0].coordinate)
        # SlicerUtil.jumpToSeed(coords)

        # self.timer.start()


    def zoomToSeed(self):
        """ Dynamic zoom to the center of the current view in all the 2D windows
        @return:
        """
        sliceNode = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeRed')
        fov = sliceNode.GetFieldOfView()
        if fov[0] > 45:
            sliceNode.SetFieldOfView(fov[0] * 0.90,
                                     fov[1] * 0.90, fov[2])
            sliceNode = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeYellow')
            sliceNode.SetFieldOfView(fov[0] * 0.90,
                                     fov[1] * 0.90, fov[2])
            sliceNode = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeGreen')
            sliceNode.SetFieldOfView(fov[0] * 0.90,
                                     fov[1] * 0.90, fov[2])
        else:
            self.zoomToSeedTimer.stop()


    def resetGUI(self):
        """ Reset the GUI
        """
        # Clean fiducials area
        self.__removeFiducialsFrames__()
        self.nodulesComboBox.clear()

        # Uncheck MIP
        self.enhanceVisualizationCheckbox.setChecked(False)

        # Uncheck checkable buttons
        self.addSeedButton.setChecked(False)
        self.showAxisButton.setChecked(False)

        # Free resources
        # del self.logic
        # # Recreate logic
        # self.logic = CIP_LesionModelLogic()
        # self.logic.printTiming = self.__printTimeCost__
        # self.__analyzedSpheres__.clear()

        self.__showRadiomics__ = False
        self.refreshGUI()

    ############
    # Private methods
    ############

    def _showCurrentLabelmap_(self):
        """ Display the right labelmap for the current background node if it exists"""
        # Set the current labelmap active
        selectionNode = slicer.app.applicationLogic().GetSelectionNode()
        selectionNode.SetReferenceActiveVolumeID(self.currentVolume.GetID())
        labelmap = self.logic.getNthNoduleLabelmapNode(self.currentVolume, self.currentNoduleIndex)
        selectionNode.SetReferenceActiveLabelVolumeID(labelmap.GetID() if labelmap is not None else "")
        slicer.app.applicationLogic().PropagateVolumeSelection(0)

    def __validateInputVolumeSelection__(self):
        """ Check there is a valid input and/or output volume selected. Otherwise show a warning message
        @return: True if the validations are passed or False otherwise
        """
        inputVolumeId = self.inputVolumeSelector.currentNodeID
        if inputVolumeId == '':
            qt.QMessageBox.warning(slicer.util.mainWindow(), 'Warning', 'Please select an input volume')
            return False
        return True

    def __showSphere__(self, buttonId):
        SlicerUtil.displayForegroundVolume(None)
        if buttonId == 0:
            # Just nodule. No Spheres
            return

        if buttonId == -2:
            buttonId = self.otherRadiusTextbox.text
        else:
            # To adapt the button id to the name of the labelmap (radius of the sphere)
            if buttonId % 10 == 0:
                # Integer radius
                buttonId /= 10
            else:
                # Decimal number
                buttonId /= 10.0

        lm = self.logic.getNthSphereLabelmapNode(self.currentVolume, self.currentNoduleIndex, buttonId)
        if lm is not None:
            SlicerUtil.displayForegroundVolume(lm.GetID(), 0.5)

    def __removeFiducialsFrames__(self):
        """ Remove all the possible fiducial frames that can remain obsolete (for example after closing a scene)
        """
        while len(self.seedsContainerFrame.children()) > 1:
            self.seedsContainerFrame.children()[1].hide()
            self.seedsContainerFrame.children()[1].delete()

    def __saveSubReport__(self, keyName, volume, noduleIndex, sphereRadius=None):
        """ Save a report in Case Reports Widget for this case and a concrete radius
        @param keyName: CaseId[__rXX] where XX = sphere radius
        @param noduleIndex: nodule id
        @param date: timestamp global to all records
        """
        if keyName in self.analysisResults and self.analysisResults[keyName] is not None \
                and len(self.analysisResults[keyName]) > 0:
            self.__saveBasicData__(keyName, volume, noduleIndex, sphereRadius=sphereRadius)
            self.reportsWidget.insertRow(**self.analysisResults[keyName])

            if self.logic.printTiming:
                # Save also timing report
                # self.analysisResultsTiming[keyName]["CaseId"] = keyName + "_timing"
                # self.analysisResultsTiming[keyName]["Date"] = date
                self.__saveBasicData__(keyName, volume, noduleIndex, isTiming=True, sphereRadius=sphereRadius)
                self.reportsWidget.insertRow(**self.analysisResultsTiming[keyName])

    def __saveBasicData__(self, keyName, volume, noduleIndex, isTiming=False, sphereRadius=None):
        date = time.strftime("%Y/%m/%d %H:%M:%S")
        # noduleKeys = self.logic.getAllNoduleKeys(self.currentVolume)
        # for noduleIndex in noduleKeys:
        # Read seeds
        fidNode = self.logic.getNthFiducialsListNode(volume, noduleIndex)
        coordsList = []
        for i in range(fidNode.GetNumberOfMarkups()):
            coords = [0,0,0]
            fidNode.GetNthFiducialPosition(i, coords)
            coords = Util.ras_to_lps(coords)
            coordsList.append(coords)
        if isTiming:
            d = self.analysisResultsTiming
            d[keyName]["CaseId"] = keyName + "_timing"
        else:
            d = self.analysisResults
            d[keyName]["CaseId"] = keyName

        d[keyName]["Date"] = date
        d[keyName]["NoduleId"] = noduleIndex
        d[keyName]["SphereRadius"] = sphereRadius
        d[keyName]["Threshold"] = self.logic.marchingCubesFilters[(volume.GetID(), noduleIndex)].GetValue(0) \
            if (volume.GetID(), noduleIndex) in self.logic.marchingCubesFilters else str(self.logic.defaultThreshold)
        d[keyName]["LesionType"] = self.logic.lesionTypes[(volume.GetID(), noduleIndex)] \
            if (volume.GetID(), noduleIndex) in self.logic.lesionTypes else 'Unknown'
        d[keyName]["Seeds_LPS"] = coordsList.__str__()
        d[keyName]["Axis"] = self.logic.getAxisStringRepr(volume, noduleIndex)

    ############
    # Events
    ############
    def enter(self):
        """This is invoked every time that we select this module as the active module in Slicer (not only the first time)"""
        # TODO: REVIEW
        # if self.inputVolumeSelector.currentNodeID != '':
        #     self.logic.getNthFiducialsListNode(self.inputVolumeSelector.currentNodeID, self.__onFiducialsNodeModified__)
        #     self.logic.setActiveVolume(self.inputVolumeSelector.currentNodeID)

        # if self.addSeedButton.checked:
        #     self.setAddSeedsMode(True)
            # if not self.timer.isActive() \
            #         and self.logic.currentLabelmap is not None:  # Segmentation was already performed
            #     self.timer.start(500)

        self.refreshGUI()

    # def __onVolumeAddedToScene__(self, scalarNode):
    #     if self.inputVolumeSelector.currentNode() is None:
    #         self.inputVolumeSelector.setCurrentNode(scalarNode)

    def __onInputVolumeChanged__(self, node):
        """ Input volume selector changed. Create a new fiducials node if it doesn't exist yet
        @param node: selected node
        """
        if node is not None:
            # Get the associated hierarchy item associated to this volume.
            shNode = self.logic.shSceneNode
            subjectHierarchyItem = shNode.GetItemByDataNode(node)
            # It should always be present
            if not subjectHierarchyItem:
                raise EnvironmentError("SubjectHierarchyItem not found for node " + node.GetName())

            # Create the initial structure if it does not exist yet
            self.logic.getRootNodulesFolderSubjectHierarchyItem(node, createIfNotExist=True)

            # Load the nodules combobox (if any nodule present)
            nodules = self.logic.getAllNoduleKeys(self.currentVolume)
            self.nodulesComboBox.blockSignals(True)
            self.nodulesComboBox.clear()
            self.resetNodulesCheckboxes()
            for i in range(len(nodules)):
                self.nodulesComboBox.addItem("Nodule {}".format(nodules[i]))
                self.nodulesComboBox.setItemData(i, nodules[i])
            self.nodulesComboBox.blockSignals(False)
            if len(nodules) > 0:
                self.setActiveNodule(self.nodulesComboBox.itemData(0))

            self.maximumRadiusSpinbox.value = self.logic.getMaxRadius(node)
            # Display this volume in all the windows
            SlicerUtil.setActiveVolumeIds(node.GetID())

        self.refreshGUI()

    def __onAddNoduleButtonClicked__(self):
        self.addNewNodule()

    def __onJumpToNoduleButtonClicked__(self):
        """
        Jump to the slice where the first seed of the current nodule is
        """
        if self.currentNoduleIndex:
            fids = self.logic.getNthFiducialsListNode(self.currentVolume, self.currentNoduleIndex)
            if fids and fids.GetNumberOfFiducials() > 0:
                coords = [0,0,0]
                fids.GetNthFiducialPosition(0, coords)
                SlicerUtil.jumpToSeed(coords)
                self.zoomToSeedTimer.start()


    def __onNodulesComboboxCurrentIndexChanged__(self, index):
        self.resetNodulesCheckboxes()
        if index is not None and index >= 0:
            self.setActiveNodule(self.nodulesComboBox.itemData(index))

    def __onLabelmapVolumeSelectorCurrentIndexChanged__(self, node):
        if self.currentVolume and node:
            self.logic.setNthNoduleLabelmapNode(self.currentVolume, self.currentNoduleIndex, node)
            # Make this labelmap the visible one
            SlicerUtil.setActiveVolumeIds(self.currentVolume.GetID(), node.GetID())
            # Show the radiomics the moment there is a labelmap for any of the nodules
            self.__showRadiomics__ = True
            self.refreshGUI()

    def __onEnhanceVisualizationCheckChanged__(self, state):
        active = self.enhanceVisualizationCheckbox.isChecked()
        self.mipFrame.visible = active
        self.mipViewer.activateEnhacedVisualization(active)
        if not active:
            # Reset layout. Force the cursor state because it changes to seeds mode for some unexplained reason!
            SlicerUtil.setFiducialsCursorMode(False)

    def __onAddSeedButtonClicked__(self):
        """ Click the add fiducial button so that we set the cursor in fiducial mode
        @param button:
        """
        # if not (self.__validateInputVolumeSelection__()):
        #     button.checked = False
        #     return
        # self.setAddSeedsMode(button.checked)
        if self.addSeedButton.checked:
            SlicerUtil.setFiducialsCursorMode(True, False)
        else:
            SlicerUtil.setFiducialsCursorMode(False)

    def __onAddedSeed__(self, vtkMRMLMarkupsFiducialNode, event):
        """ The active fiducials node has been modified because we added or removed a fiducial
        @param vtkMRMLMarkupsFiducialNode: Current fiducials node
        @param event:
        """
        fiducialPosition = vtkMRMLMarkupsFiducialNode.GetNumberOfFiducials() - 1
        self.addFiducialRow(vtkMRMLMarkupsFiducialNode, fiducialPosition)
        SlicerUtil.setFiducialsCursorMode(False)
        self.refreshGUI()
        if SlicerUtil.isOtherVolumeVisible(self.currentVolume.GetID()):
            slicer.util.warningDisplay("Please note that the input volume selected ({}) is different from the one "
            "that you are actually watching".format(self.currentVolume.GetName()))

    def __onRemoveSeedsButtonClicked__(self):
        numSeeds = len(self.seedsContainerFrame.children())
        fiducialsNode = self.logic.getNthFiducialsListNode(self.currentVolume, self.currentNoduleIndex)

        # Navigate the list in reverse order so that when a Markup is removed, the previous indexes are
        # not changed and there's no need to recalculate the index with each deletion
        for i in range(numSeeds-1, 1, -1):
            if self.seedsContainerFrame.children()[i].checked:
                # Remove Markup
                fiducialsNode.RemoveMarkup(i-1)
                # Remove checkbox
                self.seedsContainerFrame.children()[i].delete()

    def __onShowAxisButtonClicked__(self):
        """
        A Show calipers button was clicked. Get the object that provoked the event to find the corresponding nodes
        """
        self.showAxis(self.currentVolume, self.currentNoduleIndex, self.showAxisButton.isChecked())

    def __onSegmentButtonClicked__(self):
        self.segmentButton.setEnabled(False)
        self.runNoduleSegmentation()

    def __onFiducialCheckClicked__(self, checkBox):
        """ Click in one of the checkboxes that is associated with every fiducial
        @param checkBox: checkbox that has been clicked
        @return:
        """
        n = int(checkBox.objectName)
        logic = slicer.modules.markups.logic()
        fiducialsNode = SlicerUtil.getNode(logic.GetActiveListID())
        fiducialsNode.SetNthFiducialSelected(n, checkBox.checked)
        fiducialsNode.SetNthFiducialVisibility(n, checkBox.checked)
        # If selected, go to this markup
        if checkBox.checked:
            logic.JumpSlicesToNthPointInMarkup(fiducialsNode.GetID(), n, True)

    def __onLesionTypeChanged__(self, button):
        self.logic.lesionTypes[(self.currentVolume, self.currentNoduleIndex)] = self.lesionTypeRadioButtonGroup.checkedId()

    def __onCLISegmentationFinished__(self, currentVolume, noduleIndex):
        """ Triggered when the CLI segmentation has finished the work.
        This is achieved because this is the function that we specify as a callback
        when calling the function "callCLI" in the logic class
        @param noduleIndex: index of the nodule that was segmented
        """
        self.distanceLevelSlider.value = self.logic.defaultThreshold  # default
        self._showCurrentLabelmap_()
        cliOutputScalarNode = self.logic.getNthAlgorithmSegmentationNode(currentVolume, noduleIndex)
        r = cliOutputScalarNode.GetImageData().GetScalarRange()

        self.distanceLevelSlider.minimum = r[0] * 100
        self.distanceLevelSlider.maximum = r[1] * 100
        self.distanceLevelSlider.value = self.logic.defaultThreshold

        self.__onThresholdSegmentationChanged__(forceRefresh=True)
        self.progressBar.hide()

        # Center the volume in the first visible seed
        fidNode = self.logic.getNthFiducialsListNode(self.currentVolume, noduleIndex)
        for i in range(fidNode.GetNumberOfMarkups()):
            if fidNode.GetNthFiducialVisibility(i):
                coords = [0,0,0]
                fidNode.GetNthFiducialPosition(i, coords)
                break
        SlicerUtil.jumpToSeed(coords)
        self.segmentButton.setEnabled(True)

        # Show the radiomics section as soon as ANY nodule has been segmented, as
        # the user has the option to analyze all nodules in batch mode
        # self.__showRadiomics__ = True
        #
        # self.refreshGUI()

        # Change the layout to a regular 3D view (without MIP)
        self.enhanceVisualizationCheckbox.setChecked(False)
        SlicerUtil.changeLayout(1)

        # Select the labelmap in the volume selector
        self.noduleLabelmapVolumeSelector.setCurrentNode(self.logic.getNthNoduleLabelmapNode(currentVolume, noduleIndex))

        # TODO: Zoom to seed with the right zoom value
        #self.zoomToSeed()

        # Start the timer that will refresh all the visualization nodes
        # self.timer.start(500)

    def __onThresholdSegmentationChanged__(self, forceRefresh=False):
        """ Refresh the GUI if the slider value has changed since the last time"""
        #if forceRefresh or self.lastRefreshValue != self.distanceLevelSlider.value:
            # Refresh slides
            # print("DEBUG: updating labelmaps with value:", float(self.distanceLevelSlider.value)/100)
        self.logic.updateModels(self.currentVolume, self.currentNoduleIndex,
                                float(self.distanceLevelSlider.value) / 100)
        # self.lastRefreshValue = self.distanceLevelSlider.value

        # Refresh visible windows
        SlicerUtil.refreshActiveWindows()

    def __onShowSphereCheckboxClicked__(self, buttonId):
        self.__showSphere__(buttonId)

    def __onSaveSegmentationResultsClicked__(self):
        self.saveCurrentSeedsToXML()

    def __onSaveTimeCostCheckboxClicked__(self, checked):
        self.logic.printTiming = (checked == 2)

    def __onRunAnalysisButtonClicked__(self):
        if self.analyzeAllNodulesCheckbox.isChecked():
            if qt.QMessageBox.question(slicer.util.mainWindow(), "Analyze all nodules",
                                "Are you sure you want to analyze ALL the available nodules?",
                                qt.QMessageBox.Yes | qt.QMessageBox.No) == qt.QMessageBox.Yes:
                for nodule in self.logic.getAllNoduleKeys(self.currentVolume):
                    if self.logic.getNthNoduleLabelmapNode(self.currentVolume, nodule) is not None:
                        self.runAnalysis(self.currentVolume, nodule)
        else:
            self.runAnalysis(self.currentVolume, self.currentNoduleIndex)

    def __onLoadNoduleSegmentationButtonClicked__(self):
        pass

    def __onRemoveNoduleButtonClicked__(self):
        if  qt.QMessageBox.question(slicer.util.mainWindow(), "Remove nodule?",
                    "Are you sure you want to clear this nodule?",
                    qt.QMessageBox.Yes|qt.QMessageBox.No) == qt.QMessageBox.Yes:
            if self.logic.removeNthNodule(self.currentVolume, self.currentNoduleIndex):
                # Remove the item from the combobox
                self.nodulesComboBox.removeItem(self.nodulesComboBox.currentIndex)

    def __onSceneClosed__(self, arg1, arg2):
        # self.timer.stop()
        self.resetGUI()

    def exit(self):
        """This is invoked every time that we switch to another module (not only when Slicer is closed)."""
        # Disable chekbox of fiducials so that the cursor is not in "fiducials mode" forever if the
        # user leaves the module
        # self.timer.stop()
        # self.setAddSeedsMode(False)
        pass

    def cleanup(self):
        """This is invoked as a destructor of the GUI when the module is no longer going to be used"""
        # self.timer.stop()
        #self.setAddSeedsMode(False)
        self.reportsWidget.cleanup()
        self.reportsWidget = None
    # def updateFeatureParameterDict(self, intValue, featureWidget):
    #     featureName = featureWidget.getName()
    #     self.featureParametersDict[featureName].update(featureWidget.getParameterDict())
    #
    # def updateFeatureClassParameterDict(self, intValue, featureClassWidget):
    #     featureClassName = featureClassWidget.getName()
    #     self.featureClassParametersDict[featureClassName].update(featureClassWidget.getParameterDict())


#############################
# CIP_LesionModelLogic
#############################
class CIP_LesionModelLogic(ScriptedLoadableModuleLogic):
    MAX_TUMOR_RADIUS = 30
    WORKING_MODE_HUMAN = 0
    WORKING_MODE_SMALL_ANIMAL = 1

    def __init__(self):
        """
        Constructor
        """
        ScriptedLoadableModuleLogic.__init__(self)
        # self.currentVolume = None # Current active volume.
        # self.__currentVolumeArray__ = None  # Numpy array that represents the current volume
        # self.currentLabelmap = None  # Current label map that contains the nodule segmentation for the current threshold (same size as the volume)
        # self.__currentLabelmapArray__ = None  # Numpy array that represents the current label map
        # self.cliOutputScalarNode = None  # Scalar volume that the CLI returns. This will be a cropped volume

        #self.currentModelNodeId = None  # 3D model volume id
        self.defaultThreshold = 0  # Default threshold for the map distance used in the nodule segmentation
        # self.onCLISegmentationFinishedCallback = None
        self.invokedCLI = False  # Semaphore to avoid duplicated events

        # self.origin = None                  # Current origin (centroid of the nodule)
        self.currentDistanceMaps = {}   # Dictionary of distance maps from the specified origin for each nodule in a particular volume
        self.currentCentroids = {}      # Dictionary of centroid of the nodule in a particular volume
        self.spheresLabelmaps = {}  # Labelmap of spheres for a particular radius
        self.lesionTypes = {}       # Dict of (Volume, nodule) with the type of lesion (nodule, tumor)

        # Different sphere sizes depending on the case
        self.__spheresDict__ = dict()
        self.__spheresDict__[self.WORKING_MODE_HUMAN] = (15, 20, 25)  # Humans
        self.__spheresDict__[self.WORKING_MODE_SMALL_ANIMAL] = (1.5, 2, 2.5)  # Mouse

        self.thresholdFilters = {}    # Dictionary of thresholds for each nodule in a particular volume
        self.marchingCubesFilters = {}     # Dictionary of thresholds for each nodule in a particular volume

        self.printTiming = SlicerUtil.IsDevelopment

    @property
    def __PREFIX_INPUTVOLUME__(self):
        """ Prefix that will be used to name the "ghost" volumes that shouldn't be displayed
        in the input volume selector
        """
        return "__segmentResults__"

    @property
    def INPUTVOLUME_FILTER_REGEXPR(self):
        """ Regular expresion that will be used to filter the nodes that shouldn't show up in the
        input volume selector
        """
        return "^(?!{0})(.)+$".format(self.__PREFIX_INPUTVOLUME__)


    @property
    def __SUFFIX__SEGMENTED_LABELMAP(self):
        """ Suffix that will be used to rename the nodule segmented labelmaps that will show up in
        the nodule labelmap volume selector
        """
        return "_lesion"

    @property
    def LESION_LABELMAP_FILTER_REGEXPR(self):
        """ Regular expresion that will be used to filter the lesion labelmap nodes that should
        show up in the labelmap volume selector
        """
        return "^(.)+{0}$".format(self.__SUFFIX__SEGMENTED_LABELMAP)

    @property
    def shSceneNode(self):
        """
        Get the root SubjectHierarchy node associated to the main mrmlscene
        @return:
        """
        return slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
    # @property
    # def currentModelNode(self):
    #     if self.currentModelNodeId is None:
    #         return None
    #     return SlicerUtil.getNode(self.currentModelNodeId)

    # @property
    # def currentVolumeArray(self):
    #     if self.__currentVolumeArray__ is None and self.currentVolume is not None:
    #         self.__currentVolumeArray__ = slicer.util.array(self.currentVolume.GetName())
    #     return self.__currentVolumeArray__

    # @currentVolumeArray.setter
    # def currentVolumeArray(self, value):
    #     self.__currentVolumeArray__ = value

    # @property
    # def currentLabelmapArray(self):
    #     if self.__currentLabelmapArray__ is None and self.currentLabelmap is not None:
    #         self.__currentLabelmapArray__ = slicer.util.array(self.currentLabelmap.GetName())
    #     return self.__currentLabelmapArray__
    #
    # @currentLabelmapArray.setter
    # def currentLabelmapArray(self, value):
    #     self.__currentLabelmapArray__ = value

    ##############################
    # General volume / fiducials methods
    ##############################
    # def setActiveVolume(self, volumeID):
    #     """ Set the current volume as active
    #     @param volumeID:
    #     @return:
    #     """
    #     self.currentVolume = SlicerUtil.getNode(volumeID)

        # Switch the fiducials node
        # fiducialsNode = self.getNthCurrentFiducialsListNode(volumeID)
        # markupsLogic = slicer.modules.markups.logic()
        # markupsLogic.SetActiveListID(fiducialsNode)
        #
        # # Search for preexisting labelmap
        # #labelmapName = self.currentVolume.GetName() + '_nodulelm'
        # labelmapName = self.currentVolume.GetName() + self.__SUFFIX__SEGMENTED_LABELMAP
        # self.currentLabelmap = SlicerUtil.getNode(labelmapName)
        # #segmentedNodeName = self.currentVolume.GetID() + '_segmentedlm'
        # segmentedNodeName = self.__PREFIX_INPUTVOLUME__ + self.currentVolume.GetID()
        # self.cliOutputScalarNode = SlicerUtil.getNode(segmentedNodeName)

    def getWorkingMode(self, vtkMRMLScalarVolumeNode):
        """
        Get the right working mode for this volume based on the size
        @param vtkMRMLScalarVolumeNode:
        @return: self.WORKING_MODE_HUMAN or self.WORKING_MODE_SMALL_ANIMAL
        """
        size = vtkMRMLScalarVolumeNode.GetSpacing()[0] * vtkMRMLScalarVolumeNode.GetImageData().GetDimensions()[0]
        return self.WORKING_MODE_HUMAN if size >= 100 else self.WORKING_MODE_SMALL_ANIMAL

    def getPredefinedSpheresDict(self, vtkMRMLScalarVolumeNode):
        """Get predefined spheres """
        return self.__spheresDict__[self.getWorkingMode(vtkMRMLScalarVolumeNode)]

    def getMaxRadius(self, vtkMRMLScalarVolumeNode):
        """
        Get the max radius for a nodule based on the current working mode for this volume
        @param vtkMRMLScalarVolumeNode:
        @return:
        """
        return 30.0 if self.getWorkingMode(vtkMRMLScalarVolumeNode) == self.WORKING_MODE_HUMAN else 2.0


    def createRootNodulesHierarchy(self, vtkMRMLScalarVolumeNode):
        """
        Create a "Nodules" subject hierarchy folder
        @param vtkMRMLScalarVolumeNode:
        @return: int id with the folder node identifier
        """
        shNode = self.shSceneNode
        root = shNode.GetItemByDataNode(vtkMRMLScalarVolumeNode)
        return shNode.CreateFolderItem(root, "{}_Nodules".format(vtkMRMLScalarVolumeNode.GetName()))

    def getLastNoduleIndex(self, vtkMRMLScalarVolumeNode):
        """
        Get the biggest nodule index currently present for this volume
        @return: Max index or 0 if there are no nodules
        """
        # nodulesFolder = self.getRootNodulesFolderSubjectHierarchyItem(vtkMRMLScalarVolumeNode, createIfNotExist=False)
        # if nodulesFolder is None:
        #     return 0
        # index = 0
        # for i in range(nodulesFolder.GetNumberOfChildrenNodes()):
        #     node = nodulesFolder.GetNthChildNode(i)
        #     if node.GetLevel() == "Folder":     # In theory all the children should be folders
        #         # The name of the node is the index
        #         nodeIndex = int(node.GetName())
        #         index = max(index, nodeIndex)
        # return index
        keys = self.getAllNoduleKeys(vtkMRMLScalarVolumeNode)

        return 0 if len(keys) == 0 else max(keys)

    def addNewNodule(self, vtkMRMLScalarVolumeNode):
        """
        Create all the hierarchy nodes needed to store the information for a new nodule (markups, rulers, etc)
        @param vtkMRMLScalarVolumeNode: vtkMRMLScalarVolumeNode
        @return: SubjectHierarchyItem folder id associated to the node, once that all the subhierarchy has been created
        """
        if vtkMRMLScalarVolumeNode is None:
            return slicer.vtkMRMLSubjectHierarchyNode.GetInvalidItemID()
        # Get the root folder for the current volume
        shNode = self.shSceneNode
        # volumeRootFolder = shNode.GetItemByDataNode(vtkMRMLScalarVolumeNode)
        # Get subject hierarchy node
        # If there is not Nodules root folder yet, create it
        nodulesFolder = self.getRootNodulesFolderSubjectHierarchyItem(vtkMRMLScalarVolumeNode)
        # if nodulesFolder == slicer.vtkMRMLSubjectHierarchyNode.GetInvalidItemID():
        #     # Create the folder for the different nodules
        #     nodeName =  "{}_Nodules".format(vtkMRMLScalarVolumeNode.GetName())
        #     nodulesFolder = shNode.CreateItem(volumeRootFolder, nodeName)
        if nodulesFolder == slicer.vtkMRMLSubjectHierarchyNode.GetInvalidItemID():
            raise Exception("Parent nodules folder could not be created")
        # Add a new Nodule folder with the corresponding index number (starting at 1!, more intuitive for the user)
        noduleIndex = self.getLastNoduleIndex(vtkMRMLScalarVolumeNode) + 1
        hierNoduleFolder = shNode.CreateFolderItem(nodulesFolder, str(noduleIndex))

        # Create the fiducials node
        fidNode = self._createFiducialsListNode_(vtkMRMLScalarVolumeNode, noduleIndex)
        # Move it to the right place in the hierarchy
        self.setNthFiducialsListNode(vtkMRMLScalarVolumeNode, noduleIndex, fidNode)

        # Create the Annotations Ruler hierarchy for the three rulers
        annotRulersNode = self._createRulersNode_(vtkMRMLScalarVolumeNode, noduleIndex)
        # Create a folder that will be associated with the rulers hierarchy
        #rulersItem = shNode.CreateItem(hierNoduleFolder, annotRulersNode)
        # Move it to the right place
        self.setNthRulersListNode(vtkMRMLScalarVolumeNode, noduleIndex, annotRulersNode)

        # Return the root nodule node
        return hierNoduleFolder

    def getRootNodulesFolderSubjectHierarchyItem(self, vtkMRMLScalarVolumeNode, createIfNotExist=True):
        """
        Get the current SubjectHierarchyItem that corresponds to the root folder for a given volume ('Nodules' folder)
        @param vtkMRMLScalarVolumeNode: volume node
        @param createIfNotExist: create the node if it doesn't exist yet
        @return: "Nodules" vtkMRMLSubjectHierarchyItem id
        """
        if vtkMRMLScalarVolumeNode is None:
            return slicer.vtkMRMLSubjectHierarchyNode.GetInvalidItemID()
        shNode = self.shSceneNode
        root = shNode.GetItemByDataNode(vtkMRMLScalarVolumeNode)
        children = vtk.vtkIdList()
        shNode.GetItemChildren(root, children)
        for i in range(children.GetNumberOfIds()):
            child = children.GetId(i)
            if shNode.GetItemLevel(child) == "Folder":
                return child
        if createIfNotExist:
            # Create the node because it wasn't found
            return self.createRootNodulesHierarchy(vtkMRMLScalarVolumeNode)
        return slicer.vtkMRMLSubjectHierarchyNode.GetInvalidItemID()


    def getAllNoduleKeys(self, vtkMRMLScalarVolumeNode):
        shNode = self.shSceneNode
        root = self.getRootNodulesFolderSubjectHierarchyItem(vtkMRMLScalarVolumeNode, createIfNotExist=False)
        keys = []
        children = vtk.vtkIdList()
        shNode.GetItemChildren(root, children)
        for i in range(children.GetNumberOfIds()):
            keys.append(int(shNode.GetItemName(children.GetId(i))))
        return keys

    def getNthNoduleFolder(self, vtkMRMLScalarVolumeNode, noduleIndex):
        """
        Get the Nth SubjectHierarchyItem "Nodule" folder
        @param vtkMRMLScalarVolumeNode: volume node
        @param noduleIndex: number of nodule
        @return: Nth "Nodule" subject hierarchy item ID
        """
        nodulesFolder = self.getRootNodulesFolderSubjectHierarchyItem(vtkMRMLScalarVolumeNode)
        if not nodulesFolder:
            return slicer.vtkMRMLSubjectHierarchyNode.GetInvalidItemID()

        shNode = self.shSceneNode
        children = vtk.vtkIdList()
        shNode.GetItemChildren(nodulesFolder, children)
        if children.GetNumberOfIds() < noduleIndex:
            print(("WARNING: attempting to access to nodule {} when the total number of children for node {} is {}".format(
                noduleIndex, shNode.GetItemName(nodulesFolder), children.GetNumberOfIds())))
            return slicer.vtkMRMLSubjectHierarchyNode.GetInvalidItemID()
        return children.GetId(noduleIndex-1)

    def _getNthSubjectHierarchyNode_(self, vtkMRMLScalarVolumeNode, noduleIndex, nodeName):
        """
        Get an item that is a direct child of the nodules folder based on the name of the item
        @param vtkMRMLScalarVolumeNode:
        @param noduleIndex:
        @param nodeName:
        @return: Node id or slicer.vtkMRMLSubjectHierarchyNode.GetInvalidItemID()
        """
        if noduleIndex is None:
            return slicer.vtkMRMLSubjectHierarchyNode.GetInvalidItemID()
        if noduleIndex <= 0:
            return slicer.vtkMRMLSubjectHierarchyNode.GetInvalidItemID()
        noduleFolder = self.getNthNoduleFolder(vtkMRMLScalarVolumeNode, noduleIndex)
        if not noduleFolder:
            return slicer.vtkMRMLSubjectHierarchyNode.GetInvalidItemID()
        shNode = self.shSceneNode
        children = vtk.vtkIdList()
        shNode.GetItemChildren(noduleFolder, children)
        for i in range(children.GetNumberOfIds()):
            child = children.GetId(i)
            if shNode.GetItemName(child) == nodeName:
                #return shNode.GetItemDataNode(child)
                return child
        return slicer.vtkMRMLSubjectHierarchyNode.GetInvalidItemID()

    def _setNthSubjectHierarchyNode_(self, vtkMRMLScalarVolumeNode, noduleIndex, node, nodeName):
        """
        Set and associate a node to a particular SubjectHierarchyNode that is a direct child of the nodule folder
        @param vtkMRMLScalarVolumeNode:
        @param noduleIndex:
        @param node: Node
        @param nodeName: Ex: "Fiducials"
        @return: True (everything ok) or False
        """
        if not vtkMRMLScalarVolumeNode:
            return False
        parent = self.getNthNoduleFolder(vtkMRMLScalarVolumeNode, noduleIndex)
        if not parent:
            return False

        # First, clear the possibly existing one
        self._extractNthSubjectHierarchyNode_(vtkMRMLScalarVolumeNode, noduleIndex, nodeName)

        # Get the subject hierachy item associated to the node
        shNode = self.shSceneNode
        itemID = shNode.GetItemByDataNode(node)
        if not itemID:
            return False
        # Set the parent
        shNode.SetItemParent(itemID, parent)
        return True

    def _extractNthSubjectHierarchyNode_(self, vtkMRMLScalarVolumeNode, noduleIndex, nodeName):
        if noduleIndex < 0:
            return
        noduleFolder = self.getNthNoduleFolder(vtkMRMLScalarVolumeNode, noduleIndex)
        if not noduleFolder:
            return
        shNode = self.shSceneNode
        children = vtk.vtkIdList()
        shNode.GetItemChildren(noduleFolder, children)
        for i in range(children.GetNumberOfIds()):
            child = children.GetId(i)
            if shNode.GetItemName(child) == nodeName:
                # Disassociate the Subject Hierarchy Node from the nodule folder
                shNode.SetItemParent(child, shNode.GetSceneItemID())
                return

    # def _moveNodeToNodulesFolder_(self, vtkMRMLScalarVolumeRootNode, noduleIndex, node):
    #     """
    #     Get the subject hierarchy node for a node and move it to the corresponding nodule folder
    #     @param vtkMRMLScalarVolumeRootNode: vtkMRMLScalarVolumeNode root of the hierarchy
    #     @param noduleIndex: nodule index where the node must be moved
    #     @param node: node that must be moved
    #     @return: True iv everything went fine or False otherwise
    #     """
    #     # Get the nodules folder
    #     if not vtkMRMLScalarVolumeRootNode:
    #         return False
    #     parent = self.getNthNoduleFolder(vtkMRMLScalarVolumeRootNode, noduleIndex)
    #     if not parent:
    #         return False
    #     # Get the subject hierachy item associated to the node
    #     shNode = self.shSceneNode
    #     shn = shNode.GetItemByDataNode(node)
    #     if not shn:
    #         return False
    #     # Set the parent
    #     shn.SetParentNodeID(parent.GetID())
    #     return True


    def getNthFiducialsListNode(self, vtkMRMLScalarVolumeNode, noduleIndex):
        """
        Get the current fiducialsListNode for the specified volume and index of nodule
        @param vtkMRMLScalarVolumeNode: volume node
        @param noduleIndex: int number of nodule (starting at 1)
        @return: vtkMRMLMarkupsFiducialNode (or None if not found)
        """
        nodeId = self._getNthSubjectHierarchyNode_(vtkMRMLScalarVolumeNode, noduleIndex,
                                                 "{}_Fiducials_{}".format(vtkMRMLScalarVolumeNode.GetName(), noduleIndex))
        return self.shSceneNode.GetItemDataNode(nodeId)

    def setNthFiducialsListNode(self, vtkMRMLScalarVolumeNode, noduleIndex, vtkMRMLMarkupsFiducialNode):
        """
        Set the current fiducialsListNode for the specified volume and index of nodule
        @param vtkMRMLScalarVolumeNode: volume node
        @param noduleIndex: int number of nodule (starting at 1)
        @param vtkMRMLMarkupsFiducialNode: markups node to set
        @return: True if everything went fine
        """
        nodeName = "{}_Fiducials_{}".format(vtkMRMLScalarVolumeNode.GetName(), noduleIndex)
        return self._setNthSubjectHierarchyNode_(vtkMRMLScalarVolumeNode, noduleIndex, vtkMRMLMarkupsFiducialNode, nodeName)

    def getNthRulersListNode(self, vtkMRMLScalarVolumeNode, noduleIndex):
        """
        Get the current annotation rulers hierarchy node for the specified volume and index of nodule
        @param vtkMRMLScalarVolumeNode: volume node
        @param noduleIndex:  number of nodule (starting at 1)
        @return: vtkMRMLAnnotationHierarchyNode or None
        """
        nodeId = self._getNthSubjectHierarchyNode_(vtkMRMLScalarVolumeNode, noduleIndex,
                                                 "{}_Rulers_{}".format(vtkMRMLScalarVolumeNode.GetName(), noduleIndex))
        return self.shSceneNode.GetItemDataNode(nodeId)

    def setNthRulersListNode(self, vtkMRMLScalarVolumeNode, noduleIndex, vtkMRMLAnnotationHierarchyNode):
        """
        Set the current annotation rulers hierarchy node for the specified volume and index of nodule
        @param vtkMRMLScalarVolumeNode: volume node
        @param noduleIndex:  number of nodule (starting at 1)
        @param vtkMRMLAnnotationHierarchyNode: rulers node to set
        @return: True (everything ok) or False
        """
        nodeName = "{}_Rulers_{}".format(vtkMRMLScalarVolumeNode.GetName(), noduleIndex)
        return self._setNthSubjectHierarchyNode_(vtkMRMLScalarVolumeNode, noduleIndex, vtkMRMLAnnotationHierarchyNode, nodeName)

    def getNthNoduleLabelmapNode(self, vtkMRMLScalarVolumeNode, noduleIndex):
        """
        Get the current annotation rulers hierarchy node for the specified volume and index of nodule
        @param vtkMRMLScalarVolumeNode: volume node
        @param noduleIndex:  number of nodule (starting at 1)
        @return: labelmap node or None
        """
        nodeId = self._getNthSubjectHierarchyNode_(vtkMRMLScalarVolumeNode, noduleIndex,
                                        "{}_noduleLabelmap_{}".format(vtkMRMLScalarVolumeNode.GetName(), noduleIndex))
        return self.shSceneNode.GetItemDataNode(nodeId)


    def setNthNoduleLabelmapNode(self, vtkMRMLScalarVolumeNode, noduleIndex, labelmapNode):
        """
        Set the current labelmap for the specified volume and index of nodule
        @param vtkMRMLScalarVolumeNode: volume node
        @param noduleIndex: int number of nodule (starting at 1)
        @param vtkMRMLMarkupsFiducialNode: markups node to set
        @return: True if everything went fine
        """
        if vtkMRMLScalarVolumeNode is None or labelmapNode is None:
            return False
        nodeName = "{}_noduleLabelmap_{}".format(vtkMRMLScalarVolumeNode.GetName(), noduleIndex)
        return self._setNthSubjectHierarchyNode_(vtkMRMLScalarVolumeNode, noduleIndex, labelmapNode, nodeName)


    def getNthAlgorithmSegmentationNode(self, vtkMRMLScalarVolumeNode, noduleIndex):
        """
        Get the scalar node output from the CLI
        @param vtkMRMLScalarVolumeNode: volume node
        @param noduleIndex:  number of nodule (starting at 1)
        @return: scalar node or None
        """
        nodeId = self._getNthSubjectHierarchyNode_(vtkMRMLScalarVolumeNode, noduleIndex,
                             "{}_NoduleAlgorithmSegmentation_{}".format(vtkMRMLScalarVolumeNode.GetName(), noduleIndex))
        return self.shSceneNode.GetItemDataNode(nodeId)

    def setNthAlgorithmSegmentationNode(self, vtkMRMLScalarVolumeNode, noduleIndex, node):
        """
        @param vtkMRMLScalarVolumeNode: volume node
        @param noduleIndex: int number of nodule (starting at 1)
        @param node: labelmap node to set
        @return: True if everything went fine
        """
        nodeName = "{}_NoduleAlgorithmSegmentation_{}".format(vtkMRMLScalarVolumeNode.GetName(), noduleIndex)
        return self._setNthSubjectHierarchyNode_(vtkMRMLScalarVolumeNode, noduleIndex, node, nodeName)

    def getNthNoduleModelNode(self, vtkMRMLScalarVolumeNode, noduleIndex):
        """
        Get the 3D model for the nodule
        @param vtkMRMLScalarVolumeNode: volume node
        @param noduleIndex:  number of nodule (starting at 1)
        @return: model node or None
        """
        nodeId = self._getNthSubjectHierarchyNode_(vtkMRMLScalarVolumeNode, noduleIndex,
                                            "{}_NoduleModel_{}".format(vtkMRMLScalarVolumeNode.GetName(),noduleIndex))
        return self.shSceneNode.GetItemDataNode(nodeId)

    def setNthNoduleModelNode(self, vtkMRMLScalarVolumeNode, noduleIndex, modelNode):
        """
        @param vtkMRMLScalarVolumeNode: volume node
        @param noduleIndex: int number of nodule (starting at 1)
        @param modelNode: model node to set
        @return: True if everything went fine
        """
        nodeName = "{}_NoduleModel_{}".format(vtkMRMLScalarVolumeNode.GetName(), noduleIndex)
        return self._setNthSubjectHierarchyNode_(vtkMRMLScalarVolumeNode, noduleIndex, modelNode, nodeName)

    def getAllSphereLabelmapNodes(self, vtkMRMLScalarVolumeNode, noduleIndex):
        """
        Get all the sphere labelmaps for this nodule
        @param vtkMRMLScalarVolumeNode: volume node
        @param noduleIndex:  number of nodule (starting at 1)
        @return: vtkMRMLAnnotationHierarchyNode
        """
        # Get all the nodes that can be a sphere labelmap
        folder = self.getNthNoduleFolder(vtkMRMLScalarVolumeNode, noduleIndex)
        nodes = []
        children = vtk.vtkIdList()
        self.shSceneNode.GetItemChildren(folder, children)
        for i in range(children.GetNumberOfIds()):
            node = self.shSceneNode.GetItemDataNode(children.GetId(i))
            if node:
                if "SphereLabelmap" in node.GetName():
                    nodes.append(node)
        return nodes

    def getNthSphereLabelmapNode(self, vtkMRMLScalarVolumeNode, noduleIndex, sphereRadius):
        """
        Get the sphere labelmap of radius "sphereRadius" for this nodule
        @param vtkMRMLScalarVolumeNode: volume node
        @param noduleIndex:  number of nodule (starting at 1)
        @param sphereRadius: radius of the sphere
        @return: vtkMRMLAnnotationHierarchyNode or None
        """
        nodeId = self._getNthSubjectHierarchyNode_(vtkMRMLScalarVolumeNode, noduleIndex,
                                                 "{}_SphereLabelmap_r{}_{}".format(vtkMRMLScalarVolumeNode.GetName(),
                                                                                     sphereRadius, noduleIndex))
        return self.shSceneNode.GetItemDataNode(nodeId)

    def setNthSphereLabelmapNode(self, vtkMRMLScalarVolumeNode, noduleIndex, modelNode, sphereRadius):
        """
        @param vtkMRMLScalarVolumeNode: volume node
        @param noduleIndex: int number of nodule (starting at 1)
        @param modelNode: model node to set
        @param sphereRadius: radius of the sphere
        @return: True if everything went fine
        """
        nodeName = "{}_SphereLabelmap_r{}_{}".format(vtkMRMLScalarVolumeNode.GetName(), sphereRadius, noduleIndex)
        return self._setNthSubjectHierarchyNode_(vtkMRMLScalarVolumeNode, noduleIndex, modelNode, nodeName)


    def getAllFiducialNodes(self, vtkMRMLScalarVolumeNode):
        """
        Get a list of Markup nodes for all the current nodules
        @return: list of markup nodes
        """
        rootNodulesParentId = self.getRootNodulesFolderSubjectHierarchyItem(vtkMRMLScalarVolumeNode, createIfNotExist=False)
        nodules = vtk.vtkIdList()
        self.shSceneNode.GetItemChildren(rootNodulesParentId, nodules)
        numberOfNodules = nodules.GetNumberOfIds()
        fidNodes = []
        for i in range(numberOfNodules):
            # Get all the children for the nodule
            noduleChildren = vtk.vtkIdList()
            self.shSceneNode.GetItemChildren(nodules.GetId(i), noduleChildren)
            # Loop over the children to find the Markups nodes
            for j in range(noduleChildren.GetNumberOfIds()):
                node = self.shSceneNode.GetItemDataNode(noduleChildren.GetId(j))
                if node is not None and isinstance(node, slicer.vtkMRMLMarkupsFiducialNode):
                    fidNodes.append(node)
        return fidNodes

    def getAllRulerChildNodes(self, vtkMRMLScalarVolumeNode):
        """
        Get a list of Ruler nodes for all the current nodules.
        Please note that this method will return the parents (vtkMRMLAnnotationHierarchyNode), not the children
        ruler nodes (vtkMRMLAnnotationRulerNodes)
        @return: list of vtkMRMLAnnotationHierarchyNode nodes
        """
        nodulesParent = self.getRootNodulesFolderSubjectHierarchyItem(vtkMRMLScalarVolumeNode, createIfNotExist=False)
        numberOfNodules = nodulesParent.GetNumberOfChildrenNodes()
        rulerNodes = []
        for i in range(numberOfNodules):
            # Get the node folder
            node = nodulesParent.GetNthChildNode(i)
            # Loop over the nodule folder children
            for j in range(node.GetNumberOfChildrenNodes()):
                if isinstance(node.GetNthChildNode(j).GetAssociatedNode(), slicer.vtkMRMLAnnotationHierarchyNode):
                    rulerNodes.append(node.GetNthChildNode(j).GetAssociatedNode())
        return rulerNodes

    def getNumberOfFiducials(self, volumeId, noduleIndex):
        """ Get the number of fiducials currently set for this volume
        @param volumeId:
        @return:
        """
        fid = self.getNthFiducialsListNode(volumeId, noduleIndex)
        if fid:
            return fid.GetNumberOfMarkups()
        return 0  # Error

    ##############################
    # CLI Nodule segmentation
    ##############################
    def callNoduleSegmentationCLI(self, inputVolumeID, noduleIndex, maximumRadius, partSolid, onCLISegmentationFinishedCallback=None):
        """ Invoke the Lesion Segmentation CLI for the specified volume and fiducials.
        Note: the fiducials will be retrieved directly from the scene
        @param inputVolumeID: input scalar node id
        @param noduleIndex: index of the nodule to segment from the ones available in the scene
        @param maximumRadius: maximum lesion radius in mm (CLI parameter)
        @param partSolid: boolean. CLI flag for solid lesions
        @param onCLISegmentationFinishedCallback: function that will be invoked when the CLI finishes

        @return: result of the CLI run call (boolean)
        """
        # Try to load preexisting structures
        # self.setActiveVolume(inputVolumeID)
        inputVolume = SlicerUtil.getNode(inputVolumeID)
        cliOutputScalarNode = self.getNthAlgorithmSegmentationNode(inputVolume, noduleIndex)

        if cliOutputScalarNode is None:
            # Create the scalar node that will work as the CLI output
            cliOutputScalarNode = slicer.mrmlScene.CreateNodeByClass("vtkMRMLScalarVolumeNode")
            slicer.mrmlScene.AddNode(cliOutputScalarNode)

            cliOutputScalarNode.SetName("{}_NoduleAlgorithmSegmentation_{}".format(inputVolume.GetName(), noduleIndex))
            # Place it correctly in the hierarchy
            self.setNthAlgorithmSegmentationNode(inputVolume, noduleIndex, cliOutputScalarNode)

        parameters = {}
        parameters["inputImage"] = inputVolumeID
        parameters["outputLevelSet"] = cliOutputScalarNode
        parameters["seedsFiducials"] = self.getNthFiducialsListNode(inputVolume, noduleIndex)
        parameters["maximumRadius"] = maximumRadius
        parameters["fullSizeOutput"] = True
        parameters["partSolid"] = partSolid

        self.invokedCLI = False  # Semaphore to avoid duplicated events

        module = slicer.modules.generatelesionsegmentation
        result = slicer.cli.run(module, None, parameters)

        # Observer when the state of the process is modified. Replace the "event" parameter (unused) with the nodule index
        result.AddObserver("ModifiedEvent", lambda caller, event: self.__onNoduleSegmentationCLIStateUpdated__(
                                                                            caller, inputVolume, noduleIndex,
                                                                            onCLISegmentationFinishedCallback))
        return result

    def updateModels(self, vtkMRMLScalarVolumeNode, noduleIndex, newThreshold):
        """ Modify the threshold for the current volume (update the model)
        @param newThreshold: new threshold (all the voxels below this threshold will be considered nodule)
        """
        thresholdFilter = self.thresholdFilters[(vtkMRMLScalarVolumeNode.GetID(), noduleIndex)]
        thresholdFilter.ThresholdByUpper(newThreshold)
        thresholdFilter.Update()
        marchingCubesFilter = self.marchingCubesFilters[(vtkMRMLScalarVolumeNode.GetID(), noduleIndex)]
        marchingCubesFilter.SetValue(0, newThreshold)
        marchingCubesFilter.Update()
        # self.currentLabelmapArray = slicer.util.array(self.currentLabelmap.GetName())
        # Invalidate distances (the nodule is going to change)
        self.__invalidateDistances__(vtkMRMLScalarVolumeNode, noduleIndex)
        # Refresh 3D view
        viewNode = SlicerUtil.getNode('vtkMRMLViewNode*')
        viewNode.Modified()

    def getCurrentDistanceMap(self, vtkMRMLScalarVolumeNode, noduleIndex):
        """ Calculate the distance map to the centroid for the current labelmap volume.
        To that end, we have to calculate first the centroid.
        Please note the results could be cached
        @return:
        """
        if (vtkMRMLScalarVolumeNode.GetID(), noduleIndex) not in self.currentDistanceMaps:
            labelmapArray = slicer.util.array(self.getNthNoduleLabelmapNode(vtkMRMLScalarVolumeNode, noduleIndex).GetID())
            centroid = Util.centroid(labelmapArray)
            # Calculate the distance map for the specified origin
            # Get the dimensions of the volume in ZYX coords
            dims = Util.vtk_numpy_coordinate(vtkMRMLScalarVolumeNode.GetImageData().GetDimensions())
            # Speed map (all ones because the growth will be constant).
            # The dimensions are reversed because we want the format in ZYX coordinates
            input = np.ones(dims, np.int32)
            sitkImage = sitk.GetImageFromArray(input)
            sitkImage.SetSpacing(vtkMRMLScalarVolumeNode.GetSpacing())
            fastMarchingFilter = sitk.FastMarchingImageFilter()
            fastMarchingFilter.SetStoppingValue(self.MAX_TUMOR_RADIUS)
            # Reverse the coordinate of the centroid
            seeds = [Util.numpy_itk_coordinate(centroid)]
            fastMarchingFilter.SetTrialPoints(seeds)
            output = fastMarchingFilter.Execute(sitkImage)
            self.currentDistanceMaps[(vtkMRMLScalarVolumeNode.GetID(), noduleIndex)] = sitk.GetArrayFromImage(output)

        return self.currentDistanceMaps[(vtkMRMLScalarVolumeNode.GetID(), noduleIndex)]

    def getSphereLabelMapArray(self, vtkMRMLScalarVolumeNode, noduleIndex, radius):
        """ Get a labelmap numpy array that contains a sphere centered in the nodule centroid, with radius "radius" and that
        EXCLUDES the nodule itself.
        If the results are not cached, this method creates the volume and calculates the labelmap
        @param radius: radius of the sphere
        @return: labelmap array for a sphere of this radius
        """
        # If the shere was already calculated, return the results
        #name = "SphereLabelmap_r{0}".format(radius)
        # Try to get first the node from the subject hierarchy tree
        sphereLabelmap = self.getNthSphereLabelmapNode(vtkMRMLScalarVolumeNode, noduleIndex, radius)
        if sphereLabelmap is not None:
            return slicer.util.array(sphereLabelmap.GetID())

        # Otherwise, Init with the current segmented nodule labelmap
        # Create and save the labelmap in the Subject hierarchy
        labelmapNodule = self.getNthNoduleLabelmapNode(vtkMRMLScalarVolumeNode, noduleIndex)
        newSphereLabelmap = SlicerUtil.cloneVolume(labelmapNodule,
                        "{}_SphereLabelmap_r{}_{}".format(vtkMRMLScalarVolumeNode.GetName(), radius, noduleIndex))
        array = slicer.util.array(newSphereLabelmap.GetID())
        # Mask with the voxels that are inside the radius of the sphere
        dm = self.currentDistanceMaps[(vtkMRMLScalarVolumeNode.GetID(), noduleIndex)]
        array[dm <= radius] = 1
        # Exclude the nodule
        labelmapArray = slicer.util.array(labelmapNodule.GetID())
        array[labelmapArray == 1] = 0
        # Save the result
        self.setNthSphereLabelmapNode(vtkMRMLScalarVolumeNode, noduleIndex, newSphereLabelmap, radius)
        # self.spheresLabelmaps[radius] = array
        # Create a mrml labelmap node for sphere visualization purposes (this step could be skipped)
        # self.__createLabelmapSphereVolume__(array, radius)
        return array

    # def getSphereLabelMap(self, radius):
    #     if SlicerUtil.IsDevelopment:
    #         print("DEBUG: get sphere lm ", radius)
    #     return SlicerUtil.getNode("{0}_r{1}".format(self.vtkMRMLScalarVolumeNode.GetName(), radius))

    def removeNthNodule(self, vtkMRMLScalarVolumeNode, noduleIndex):
        """
        Remove the Nth nodule and all the associated nodes
        @param vtkMRMLScalarVolumeNode:
        @param noduleIndex:
        @return: True if the node was removed or False otherwise
        """
        if vtkMRMLScalarVolumeNode is None:
            return False
        node = self.getNthNoduleFolder(vtkMRMLScalarVolumeNode, noduleIndex)
        if not node:
            return False

        shNode = self.shSceneNode
        shNode.RemoveItem(node)
        return True

    def createDefaultAxis(self, vtkMRMLScalarVolumeNode, noduleIndex, seedPosition, maxRadius=None):
        """
        Create three rulers around a seed. The rulers will be children of this nodule ruler node
        @param vtkMRMLScalarVolumeNode: volume
        @param noduleIndex: nodule index
        @param seedPosition: 3 coordinates list
        @param maxRadius: optional length of the axis
        """
        if not vtkMRMLScalarVolumeNode:
            return

        rulersParentNode = self.getNthRulersListNode(vtkMRMLScalarVolumeNode, noduleIndex)
        if not rulersParentNode:
            print ("No rulers parent node found")
            return

        if maxRadius is None:
            maxRadius = self.getMaxRadius(vtkMRMLScalarVolumeNode)

        annotationsLogic = slicer.modules.annotations.logic()
        annotationsLogic.SetActiveHierarchyNodeID(rulersParentNode.GetID())

        # Axis 1 (width)
        position1 = [seedPosition[0] - maxRadius, seedPosition[1], seedPosition[2], 0]
        position2 = [seedPosition[0] + maxRadius, seedPosition[1], seedPosition[2], 0]
        node = slicer.mrmlScene.CreateNodeByClass('vtkMRMLAnnotationRulerNode')
        node.SetPositionWorldCoordinates1(position1)
        node.SetPositionWorldCoordinates2(position2)
        node.SetName("W")
        slicer.mrmlScene.AddNode(node)

        # Axis 2 (height)
        position1 = [seedPosition[0], seedPosition[1] - maxRadius, seedPosition[2], 0]
        position2 = [seedPosition[0], seedPosition[1] + maxRadius, seedPosition[2], 0]
        node = slicer.mrmlScene.CreateNodeByClass('vtkMRMLAnnotationRulerNode')
        node.SetPositionWorldCoordinates1(position1)
        node.SetPositionWorldCoordinates2(position2)
        node.SetName("H")
        slicer.mrmlScene.AddNode(node)

        # Axis 3 (depth)
        position1 = [seedPosition[0], seedPosition[1], seedPosition[2] - maxRadius, 0]
        position2 = [seedPosition[0], seedPosition[1], seedPosition[2] + maxRadius, 0]
        node = slicer.mrmlScene.CreateNodeByClass('vtkMRMLAnnotationRulerNode')
        node.SetPositionWorldCoordinates1(position1)
        node.SetPositionWorldCoordinates2(position2)
        node.SetName("D")
        slicer.mrmlScene.AddNode(node)

    def getAxisStringRepr(self, vtkMRMLScalarVolumeNode, noduleIndex):
        """
        Get a string representation of the 3 axis.
        If there are no axis or the three axis have exactly the same dimensions, we will
        assume that no axis were used.
        The string will have the shape:
        [[W11:x,y,z],[W12:x,y,x],[W21:x,y,z],[W22:x,y,x],[W31:x,y,z],[W32:x,y,x]]
        @param vtkMRMLScalarVolumeNode:
        @param noduleIndex:
        @return: string
        """
        parent = self.getNthRulersListNode(vtkMRMLScalarVolumeNode, noduleIndex)
        if not parent:
            return ""
        s = "["
        pos1 = [0, 0, 0, 0]
        pos2 = [0, 0, 0, 0]
        col = vtk.vtkCollection()
        parent.GetAllChildren(col)
        if col.GetNumberOfItems() < 3:
            # Wrong case
            return ""
        for i in range(3):
            axis = col.GetItemAsObject(i)
            axis.GetPositionWorldCoordinates1(pos1)
            s += "[W{}1:{},{},{}],".format(i, pos1[0], pos1[1], pos1[2])
            axis.GetPositionWorldCoordinates2(pos2)
            s += "[W{}2:{},{},{}]]".format(i, pos2[0], pos2[1], pos2[2])
        return s

    ################
    # PROTECTED/PRIVATE METHODS
    ################
    def _createFiducialsListNode_(self, vtkMRMLScalarVolumeNode, noduleIndex):
        """ Create a new fiducials list node for the current volume
        @param fiducialsNodeName: fiducials node name that will be created
        @param onModifiedCallback: function that will be connected to node's "ModifiedEvent"
        @return: Fiducials node
        """
        markupsLogic = slicer.modules.markups.logic()
        fiducialsNodeName="{}_Fiducials_{}".format(vtkMRMLScalarVolumeNode.GetName(), noduleIndex)
        fiducialsNodeID = markupsLogic.AddNewFiducialNode(fiducialsNodeName, slicer.mrmlScene)
        fiducialsNode = SlicerUtil.getNode(fiducialsNodeID)
        # Make the new fiducials node the active one
        # markupsLogic.SetActiveListID(fiducialsNode)
        # Hide any text from all the fiducials
        fiducialsNode.SetMarkupLabelFormat('')
        displayNode = fiducialsNode.GetDisplayNode()
        # displayNode.SetColor([1,0,0])
        displayNode.SetSelectedColor([1, 0, 0])
        displayNode.SetGlyphScale(2)
        displayNode.SetGlyphType(8)  # Diamond shape (I'm so cool...)
        # Add observer when specified
        # if onModifiedCallback is not None:
        #     # The callback function will be invoked when the fiducials node is modified
        #     fiducialsNode.AddObserver("ModifiedEvent", onModifiedCallback)

        # Node created succesfully
        return fiducialsNode

    def _createRulersNode_(self, vtkMRMLScalarVolumeNode, noduleIndex):
        """
        Create a rulers hierarchy node to store the three rulers belonging to a nodule
        @return: created vtkMRMLAnnotationHierarchyNode
        """
        annotationsLogic = slicer.modules.annotations.logic()
        rootHierarchyNode = SlicerUtil.getRootAnnotationsNode()
        annotationsLogic.SetActiveHierarchyNodeID(rootHierarchyNode.GetID())
        annotationsLogic.AddHierarchy()
        hierarchyNode = SlicerUtil.getNode(annotationsLogic.GetActiveHierarchyNodeID())
        hierarchyNode.SetName("{}_Rulers_{}".format(vtkMRMLScalarVolumeNode.GetName(), noduleIndex))
        return hierarchyNode

    def __onNoduleSegmentationCLIStateUpdated__(self, caller, vtkMRMLScalarVolumeNode, noduleIndex, callbackFunctionWhenFinished=None):
        """ Event triggered when the CLI status changes
        @param caller: CommandLineModule
        @param noduleIndex: index of the nodule that was segmented
        """
        self.caller = caller
        if caller.IsA('vtkMRMLCommandLineModuleNode') \
                and not self.invokedCLI:  # Semaphore to avoid duplicated events
            if caller.GetStatus() == caller.Completed:
                self.invokedCLI = True
                self.__processNoduleSegmentationCLIResults__(vtkMRMLScalarVolumeNode, noduleIndex, callbackFunction=callbackFunctionWhenFinished)
            elif caller.GetStatus() == caller.CompletedWithErrors:
                # TODO: print current parameters with caller.GetParameterDefault()
                raise Exception("The Nodule Segmentation CLI failed")

    def __processNoduleSegmentationCLIResults__(self, vtkMRMLScalarVolumeNode, noduleIndex, callbackFunction=None):
        """ Method called once that the CLI has finished the process.
        Create a new labelmap (currentLabelmap) and a model node with the result of the process.
        It also creates a numpy array associated with the labelmap (currentLabelmapArray)
        @param noduleIndex: index of the nodule that is being processed
        """
        if not (vtkMRMLScalarVolumeNode.GetID(), noduleIndex) in self.thresholdFilters:
            self.thresholdFilters[(vtkMRMLScalarVolumeNode.GetID(), noduleIndex)] = vtk.vtkImageThreshold()
        thresholdFilter = self.thresholdFilters[(vtkMRMLScalarVolumeNode.GetID(), noduleIndex)]

        # The cliOutputScalarNode is new, so we have to set all the values again
        cliOutputScalarNode = self.getNthAlgorithmSegmentationNode(vtkMRMLScalarVolumeNode, noduleIndex)
        thresholdFilter.SetInputData(cliOutputScalarNode.GetImageData())
        thresholdFilter.SetReplaceOut(True)
        thresholdFilter.SetOutValue(0)  # Value of the background
        thresholdFilter.SetInValue(1)  # Value of the segmented nodule
        thresholdFilter.SetOutputScalarTypeToUnsignedShort()    # Follow CIP labelmap convention

        labelmap = self.getNthNoduleLabelmapNode(vtkMRMLScalarVolumeNode, noduleIndex)
        if labelmap is None:
            # Create a labelmap with the same dimensions that the ct volume
            labelmap = SlicerUtil.getLabelmapFromScalar(cliOutputScalarNode,
                                            "{}_noduleLabelmap_{}".format(vtkMRMLScalarVolumeNode.GetName(), noduleIndex))
            labelmap.SetImageDataConnection(thresholdFilter.GetOutputPort())
            # Associate it to the right place in the Subject Hierarchy Tree
            self.setNthNoduleLabelmapNode(vtkMRMLScalarVolumeNode, noduleIndex, labelmap)
            # self._moveNodeToNodulesFolder_(vtkMRMLScalarVolumeNode, noduleIndex, labelmap.GetID())

        if not (vtkMRMLScalarVolumeNode.GetID(), noduleIndex) in self.marchingCubesFilters:
            self.marchingCubesFilters[(vtkMRMLScalarVolumeNode.GetID(), noduleIndex)] = vtk.vtkMarchingCubes()
        marchingCubesFilter = self.marchingCubesFilters[(vtkMRMLScalarVolumeNode.GetID(), noduleIndex)]

        # The cliOutputScalarNode is new, so we have to set all the values again
        marchingCubesFilter.SetInputData(cliOutputScalarNode.GetImageData())
        marchingCubesFilter.SetValue(0, self.defaultThreshold)

        currentModelNode = self.getNthNoduleModelNode(vtkMRMLScalarVolumeNode, noduleIndex)
        newNode = currentModelNode is None
        if newNode:
            # Create the result model node and connect it to the pipeline
            modelsLogic = slicer.modules.models.logic()
            currentModelNode = modelsLogic.AddModel(marchingCubesFilter.GetOutputPort())
            currentModelNode.SetName("{}_NoduleModel_{}".format(vtkMRMLScalarVolumeNode.GetName(), noduleIndex))
            # Set the model to the right subject hierarchy node
            self.setNthNoduleModelNode(vtkMRMLScalarVolumeNode, noduleIndex, currentModelNode)
            # Create a DisplayNode and associate it to the model, in order that transformations can work properly
            displayNode = slicer.vtkMRMLModelDisplayNode()
            displayNode.SetColor((0.255, 0.737, 0.851))
            slicer.mrmlScene.AddNode(displayNode)
            currentModelNode.AddAndObserveDisplayNodeID(displayNode.GetID())

        if callbackFunction is not None:
            # Delegate the responsibility of updating the models with a chosen threshold (regular case)
            callbackFunction(vtkMRMLScalarVolumeNode, noduleIndex)
        else:
            self.updateModels(vtkMRMLScalarVolumeNode, noduleIndex, self.defaultThreshold)  # Use default threshold value

        if newNode:
            # Align the model with the segmented labelmap applying a transformation
            transformMatrix = vtk.vtkMatrix4x4()
            labelmap.GetIJKToRASMatrix(transformMatrix)
            currentModelNode.ApplyTransformMatrix(transformMatrix)
            # Center the 3D view in the seed/s
            layoutManager = slicer.app.layoutManager()
            threeDWidget = layoutManager.threeDWidget(0)
            threeDView = threeDWidget.threeDView()
            threeDView.resetFocalPoint()

    def __invalidateDistances__(self, vtkMRMLScalarVolumeNode, noduleIndex):
        """ Invalidate the current nodule centroid, distance maps, etc.
        """
        if (vtkMRMLScalarVolumeNode.GetID(), noduleIndex) in self.currentDistanceMaps:
            # Extract item
            self.currentDistanceMaps.pop((vtkMRMLScalarVolumeNode.GetID(), noduleIndex))
        if (vtkMRMLScalarVolumeNode.GetID(), noduleIndex) in self.currentCentroids:
            # Extract item
            self.currentCentroids.pop((vtkMRMLScalarVolumeNode.GetID(), noduleIndex))
        # self.currentCentroids = {}
        #self.spheresLabelmaps = dict()
        for node in self.getAllSphereLabelmapNodes(vtkMRMLScalarVolumeNode, noduleIndex):
            slicer.mrmlScene.RemoveNode(node)


    def __createLabelmapSphereVolume__(self, vtkMRMLScalarVolumeNode, noduleIndex, radius):
        """ Create a Labelmap volume cloning the current global labelmap with the ROI sphere for visualization purposes
        @param labelmap: working labelmap
        @param noduleIndex: current nodule index
        @param radius: radius of the sphere (used for naming the volume)
        @return: volume created
        """
        labelmap = self.getNthNoduleLabelmapNode(vtkMRMLScalarVolumeNode, noduleIndex)
        node = SlicerUtil.cloneVolume(labelmap, "{}_SphereLabelmap_r{0}".format(vtkMRMLScalarVolumeNode.GetName(), radius))
        arr = slicer.util.array(node.GetID())
        arr[:] = slicer.util.array(labelmap.GetID())
        node.GetImageData().Modified()
        # Set a different colormap for visualization purposes
        colorNode = slicer.util.getFirstNodeByClassByName("vtkMRMLColorTableNode", "HotToColdRainbow")
        displayNode = node.GetDisplayNode()
        displayNode.SetAndObserveColorNodeID(colorNode.GetID())
        return node

    def __onAnnotationsHierarchyNodeModified__(self, vtkMRMLAnnotationHierarchyNode, event):
        """ Observe when a new ruler has been added to the hierarchy and place it in the right
        position in the SubjectHiearchyTree
        @param caller:
        @param event:
        @return:
        """
        # children = vtk.vtkCollection()
        # vtkMRMLAnnotationHierarchyNode.GetAllChildren(children)
        # for i in range(children.GetNumberOfItems()):
        #     rulerNode = children.GetItemAsObject(i)
        #     # Get the SHN corresponding to the ruler node
        #     shNode = self.shSceneNode
        #     rulerSHNode = shNode.GetItemByDataNode(rulerNode)
        #     # Get the SHN for the Hierarchy
        #     parentSHNode = shNode.GetItemByDataNode(vtkMRMLAnnotationHierarchyNode)
        #     # Set the parent
        #     rulerSHNode.SetParentNodeID(parentSHNode.GetID())
        pass

#############################
# CIP_LesionModel
class CIP_LesionModelTest(ScriptedLoadableModuleTest):
    def setUp(self):
        """ Do whatever is needed to reset the state - typically a scene clear will be enough.
        """
        slicer.mrmlScene.Clear(0)
        slicer.util.selectModule('CIP_LesionModel')

    def runTest(self):
        """Run as few or as many tests as needed here.
        """
        self.setUp()
        self.test_CIP_LesionModel()

    def test_CIP_LesionModel(self):
        # Download a case with a known nodule
        #
        import urllib.request, urllib.parse, urllib.error
        downloads = (
            ('http://midas.chestimagingplatform.org/download/item/667/1001_UVM_CANCER.nrrd', '1001_UVM_CANCER.nrrd', slicer.util.loadVolume),
            )

        for url,name,loader in downloads:
          filePath = slicer.app.temporaryPath + '/' + name
          if not os.path.exists(filePath) or os.stat(filePath).st_size == 0:
            logging.info('Requesting download %s from %s...\n' % (name, url))
            urllib.request.urlretrieve(url, filePath)
          if loader:
            logging.info('Loading %s...' % (name,))
            (isLoaded, volume) = loader(filePath)

        self.assertIsNotNone(volume, "Volume loading failed")

        # Make sure we have the required cli to do the segmentation


        self.delayDisplay('Test passed!')
        # self.assertTrue(True)


