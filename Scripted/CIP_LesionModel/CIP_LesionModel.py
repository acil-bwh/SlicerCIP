import os, sys
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import collections
import itertools
import numpy as np
import time
import SimpleITK as sitk

from FeatureWidgetHelperLib import FeatureExtractionLogic
# Add the CIP common library to the path if it has not been loaded yet
# try:
from CIP.logic.SlicerUtil import SlicerUtil
# except Exception as ex:
#     currentpath = os.path.dirname(os.path.realpath(__file__))
#     # We assume that CIP_Common is in the development structure
#     path = os.path.normpath(currentpath + '/../CIP_Common')
#     if not os.path.exists(path):
#         # We assume that CIP is a subfolder (Slicer behaviour)
#         path = os.path.normpath(currentpath + '/CIP')
#     sys.path.append(path)
#     print("The following path was manually added to the PythonPath in CIP_LesionModel: " + path)
#     from CIP.logic.SlicerUtil import SlicerUtil

from CIP.logic import Util
from CIP.logic import GeometryTopologyData, Point
from CIP.ui import CaseReportsWidget, MIPViewerWidget


import FeatureWidgetHelperLib
import FeatureExtractionLib

#
# CIP_LesionModel
#
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
            in concentric spheres of different radius centered in the centroid of the nodule"""
        self.parent.acknowledgementText = SlicerUtil.ACIL_AcknowledgementText


#
# CIP_LesionModelWidget
#

class CIP_LesionModelWidget(ScriptedLoadableModuleWidget):
    """Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent=None):
        """Widget constructor (existing module)"""
        ScriptedLoadableModuleWidget.__init__(self, parent)
        self.moduleName = "CIP_LesionModel"
        from functools import partial
        def onNodeAdded(self, caller, eventId, callData):
            """Node added to the Slicer scene"""
            if callData.GetClassName() == 'vtkMRMLScalarVolumeNode':
                self.__onVolumeAddedToScene__(callData)

        self.onNodeAdded = partial(onNodeAdded, self)
        self.onNodeAdded.CallDataType = vtk.VTK_OBJECT
        slicer.mrmlScene.AddObserver(slicer.vtkMRMLScene.NodeAddedEvent, self.onNodeAdded)

        # Default working mode: humans
        self.workingMode = CIP_LesionModelLogic.WORKING_MODE_HUMAN
        self.__initVars__()

    def __initVars__(self):
        self.logic = CIP_LesionModelLogic(self.workingMode)
        self.__featureClasses__ = None
        self.__storedColumnNames__ = None
        self.__analyzedSpheres__ = set()
        # Timer for dynamic zooming
        self.timer = qt.QTimer()
        self.timer.setInterval(150)
        self.timer.timeout.connect(self.__updateFOV__)

    @property
    def storedColumnNames(self):
        """ Column names that will be stored in the CaseReportsWidget
        :return:
        """
        if self.__storedColumnNames__ is None:
            self.__storedColumnNames__ = ["CaseId", "Date", "Threshold", "LesionType", "Seeds_LPS"]
            # Create a single features list with all the "child" features
            self.__storedColumnNames__.extend(itertools.chain.from_iterable(self.featureClasses.itervalues()))
        return self.__storedColumnNames__

    @property
    def featureClasses(self):
        """ Dictionary that contains all MainFeature-ChildFeatures values
        :return:
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
        :return: boolean
        """
        return self.evaluateSegmentationCheckbox.isChecked()

    @property
    def __printTimeCost__(self):
        """ Save the time cost for the analysis operations
        :return: boolean
        """
        return self.saveTimeCostCheckbox.isChecked()

    @property
    def lesionType(self):
        """ Unknown, Nodule or Tumor. This information will be saved in the GeometryTopologyData that
        stores the position of the seeds
        :return: text of the type
        """
        return self.lesionTypeRadioButtonGroup.checkedButton().text

    def setup(self):
        """This is called one time when the module GUI is initialized
        """
        ScriptedLoadableModuleWidget.setup(self)

        self.semaphoreOpen = False      # To prevent duplicate events
        # self.timer = qt.QTimer()
        # self.timer.timeout.connect(self.checkAndRefreshModels)
        self.lastRefreshValue = -5000  # Just a value out of range

        #######################
        # Case selector area
        collapsibleButton = ctk.ctkCollapsibleButton()
        collapsibleButton.text = "Case selector"
        self.layout.addWidget(collapsibleButton)
        # Layout within the dummy collapsible button. See http://doc.qt.io/qt-4.8/layout.html for more info about layouts
        self.caseSelectorLayout = qt.QGridLayout(collapsibleButton)

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
        self.inputVolumeSelector.sortFilterProxyModel().setFilterRegExp(self.logic.INPUTVOLUME_FILTER_REGEXPR)
        # self.volumeSelector.setStyleSheet("margin:0px 0 0px 0; padding:2px 0 2px 5px")
        self.caseSelectorLayout.addWidget(self.inputVolumeSelector, row, 1, 1, 3)

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
        collapsibleButton = ctk.ctkCollapsibleButton()
        collapsibleButton.text = "Nodule segmentation"
        self.layout.addWidget(collapsibleButton)
        # Layout within the dummy collapsible button. See http://doc.qt.io/qt-4.8/layout.html for more info about layouts
        self.noduleSegmentationLayout = qt.QGridLayout(collapsibleButton)

        # Add seeds
        row += 1
        self.labelAddedSeeds = qt.QLabel("Added seeds:")
        self.labelAddedSeeds.setStyleSheet("margin: 10px 0 0 5px")
        self.noduleSegmentationLayout.addWidget(self.labelAddedSeeds, row, 0)
        self.addFiducialButton = ctk.ctkPushButton()
        self.addFiducialButton.text = "Add new seed"
        self.addFiducialButton.toolTip = "Click in the button and add a new seed in the volume. " \
                                         "You can use MIP proyection by clicking in \"Enhance visualization\" checkbox"
        self.addFiducialButton.setIcon(SlicerUtil.getIcon("WelcomeFiducialWithArrow-Original.png"))
        self.addFiducialButton.setIconSize(qt.QSize(16, 16))
        self.addFiducialButton.checkable = True
        # self.addFiducialButton.enabled = False
        self.addFiducialButton.setFixedSize(qt.QSize(115, 30))
        self.noduleSegmentationLayout.addWidget(self.addFiducialButton, row, 1, 1, 3)

        # Container for the fiducials
        row += 1
        self.fiducialsContainerFrame = qt.QFrame()
        self.fiducialsContainerFrame.setLayout(qt.QVBoxLayout())
        self.noduleSegmentationLayout.addWidget(self.fiducialsContainerFrame, row, 0, 1, 4)

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
        self.noduleSegmentationLayout.addWidget(self.loadSeedsButton, row, 0, 1, 2)

        self.saveSeedsButton = qt.QPushButton()
        self.saveSeedsButton.text = "Save to XML"
        self.saveSeedsButton.toolTip = "Save the current seeds and lesion type for batch analysis in a XML file"
        self.saveSeedsButton.setIcon(qt.QIcon("{0}/Save.png".format(SlicerUtil.CIP_ICON_DIR)))
        self.saveSeedsButton.setIconSize(qt.QSize(16, 16))
        self.saveSeedsButton.setStyleSheet("margin: 10px 0; height: 30px")
        # self.saveSeedsButton.setMaximumWidth(150)
        self.noduleSegmentationLayout.addWidget(self.saveSeedsButton, row, 2, 1, 2)

        # Operation mode (human, small animal)
        # row += 1
        # label = qt.QLabel("Operation mode:")
        # label.setStyleSheet("margin-left:5px")

        # Type of nodule
        row += 1
        self.lesionTypeLabel = qt.QLabel("Lesion type:")
        self.lesionTypeLabel.setStyleSheet("margin:5px 0 0 5px")
        self.noduleSegmentationLayout.addWidget(self.lesionTypeLabel, row, 0)
        self.lesionTypeRadioButtonGroup = qt.QButtonGroup()
        button = qt.QRadioButton("Unknown")
        button.setChecked(True)
        self.lesionTypeRadioButtonGroup.addButton(button, 0)
        self.noduleSegmentationLayout.addWidget(button, row, 1)
        button = qt.QRadioButton("Nodule")
        self.lesionTypeRadioButtonGroup.addButton(button, 1)
        self.noduleSegmentationLayout.addWidget(button, row, 2)
        button = qt.QRadioButton("Tumor")
        self.lesionTypeRadioButtonGroup.addButton(button, 2)
        self.noduleSegmentationLayout.addWidget(button, row, 3)

        # Maximum radius
        row += 1
        self.labelMaxRad = qt.QLabel("Maximum lesion radius (mm)")
        self.labelMaxRad.setStyleSheet("margin: 20px 0 0 5px")
        self.noduleSegmentationLayout.addWidget(self.labelMaxRad, row, 0)

        self.maximumRadiusSpinbox = qt.QSpinBox()
        self.maximumRadiusSpinbox.minimum = 0
        self.maximumRadiusSpinbox.setStyleSheet("margin-top: 15px")
        # self.maximumRadiusSpinbox.setFixedWidth(40)
        # Default value: 30
        radius = SlicerUtil.settingGetOrSetDefault(self.moduleName, "maximumRadius", 30)
        self.maximumRadiusSpinbox.value = int(radius)
        self.maximumRadiusSpinbox.toolTip = "Maximum radius for the tumor. Recommended: 30 mm for humans and 3 mm for small animals"
        self.noduleSegmentationLayout.addWidget(self.maximumRadiusSpinbox, row, 1)

        row += 1
        self.segmentButton = qt.QPushButton()
        self.segmentButton.text = "Segment nodule"
        self.segmentButton.toolTip = "Run the segmentation algorithm"
        self.segmentButton.setIcon(qt.QIcon("{0}/Reload.png".format(SlicerUtil.CIP_ICON_DIR)))
        self.segmentButton.setIconSize(qt.QSize(20, 20))
        self.segmentButton.setStyleSheet(
            "font-weight:bold; font-size:12px; color: white; background-color:#274EE2; margin-top:10px;")
        self.segmentButton.setFixedHeight(40)
        self.noduleSegmentationLayout.addWidget(self.segmentButton, row, 1, 1, 2)

        # CLI progress bar
        row += 1
        self.progressBar = slicer.qSlicerCLIProgressBar()
        self.progressBar.visible = False
        self.noduleSegmentationLayout.addWidget(self.progressBar, row, 1, 1, 2)

        # Threshold
        row += 1
        self.selectThresholdLabel = qt.QLabel("Select a threshold:")
        self.selectThresholdLabel.setStyleSheet("margin: 10px 0 0 5px")
        self.selectThresholdLabel.setToolTip("Move the slider for a fine tuning segmentation")
        self.noduleSegmentationLayout.addWidget(self.selectThresholdLabel, row, 0)
        self.distanceLevelSlider = qt.QSlider()
        self.distanceLevelSlider.orientation = 1  # Horizontal
        self.distanceLevelSlider.minimum = -50  # Ad-hoc value
        self.distanceLevelSlider.maximum = 50
        self.distanceLevelSlider.setStyleSheet("margin-top:10px;padding-top:20px")
        self.distanceLevelSlider.setToolTip("Move the slider for a fine tuning segmentation")
        self.noduleSegmentationLayout.addWidget(self.distanceLevelSlider, row, 1, 1, 3)

        #####
        ## RADIOMICS SECTION
        # used to map feature class to a list of auto-generated feature checkbox widgets
        self.featureWidgets = collections.OrderedDict()
        for key in self.featureClasses.keys():
            self.featureWidgets[key] = list()

        self.radiomicsCollapsibleButton = ctk.ctkCollapsibleButton()
        self.radiomicsCollapsibleButton.text = "Radiomics"
        self.layout.addWidget(self.radiomicsCollapsibleButton)
        self.radiomicsLayout = qt.QFormLayout(self.radiomicsCollapsibleButton)

        self.noduleLabelmapLabel = qt.QLabel("Nodule labelmap")
        self.noduleLabelmapLabel.setStyleSheet("margin: 10px 0")
        self.noduleLabelmapSelector = slicer.qMRMLNodeComboBox()
        self.noduleLabelmapSelector.setStyleSheet("margin: 10px 0")
        self.noduleLabelmapSelector.nodeTypes = ("vtkMRMLLabelMapVolumeNode", "")
        self.noduleLabelmapSelector.selectNodeUponCreation = False
        self.noduleLabelmapSelector.addEnabled = False
        self.noduleLabelmapSelector.noneEnabled = True
        self.noduleLabelmapSelector.removeEnabled = False
        self.noduleLabelmapSelector.showHidden = False
        self.noduleLabelmapSelector.showChildNodeTypes = False
        self.noduleLabelmapSelector.setMRMLScene(slicer.mrmlScene)
        self.noduleLabelmapSelector.toolTip = "Labelmap with the segmented nodule"
        self.noduleLabelmapSelector.sortFilterProxyModel().setFilterRegExp(self.logic.LESION_LABELMAP_FILTER_REGEXPR)
        self.radiomicsLayout.addRow(self.noduleLabelmapLabel, self.noduleLabelmapSelector)

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
        self.featureWidgetList = list(itertools.chain.from_iterable(self.featureWidgets.values()))
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
        for rad in itertools.chain.from_iterable(self.logic.spheresDict.values()):
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

        r +=1
        # HeterogeneityCAD Apply Button
        self.runAnalysisButton = qt.QPushButton("Analyze!")
        self.runAnalysisButton.toolTip = "Run all the checked analysis"
        self.runAnalysisButton.setIcon(qt.QIcon("{0}/analyze.png".format(SlicerUtil.CIP_ICON_DIR)))
        self.runAnalysisButton.setIconSize(qt.QSize(24, 24))
        self.runAnalysisButton.setFixedWidth(150)
        self.runAnalysisButton.setStyleSheet("font-weight:bold; font-size:12px; color: white; background-color:#274EE2")
        # self.reportsFrame.layout().addWidget(self.runAnalysisButton)
        self.sphereRadiusFrameLayout.addWidget(self.runAnalysisButton, r, 0)

        self.radiomicsLayout.addWidget(self.sphereRadiusFrame)

        # Reports widget
        collapsibleButton = ctk.ctkCollapsibleButton()
        collapsibleButton.text = "Results of the analysis"
        self.layout.addWidget(collapsibleButton)
        self.reportsLayout = qt.QHBoxLayout(collapsibleButton)
        self.reportsWidget = CaseReportsWidget(self.moduleName, columnNames=self.storedColumnNames,
                                               parentWidget=self.reportsLayout)
        self.reportsWidget.setup()
        self.reportsWidget.showWarnigMessages(False)

        ######################
        # Case navigator widget
        if SlicerUtil.isSlicerACILLoaded():
            # Add a case list navigator
            caseNavigatorCollapsibleButton = ctk.ctkCollapsibleButton()
            caseNavigatorCollapsibleButton.text = "Case navigator (advanced)"
            self.layout.addWidget(caseNavigatorCollapsibleButton)
            caseNavigatorAreaLayout = qt.QHBoxLayout(caseNavigatorCollapsibleButton)

            from ACIL.ui import CaseNavigatorWidget
            self.caseNavigatorWidget = CaseNavigatorWidget("CIP_LesionModel", caseNavigatorCollapsibleButton)
            self.caseNavigatorWidget.setup()
            self.caseNavigatorWidget.addObservable(self.caseNavigatorWidget.EVENT_PRE_VOLUME_LOAD, self.__onPreVolumeLoad__)

        #######################
        # Advanced parameters area
        collapsibleButton = ctk.ctkCollapsibleButton()
        collapsibleButton.text = "Advanced parameters"
        collapsibleButton.collapsed = True
        self.layout.addWidget(collapsibleButton)
        # Layout within the dummy collapsible button. See http://doc.qt.io/qt-4.8/layout.html for more info about layouts
        self.advancedParametersLayout = qt.QFormLayout(collapsibleButton)
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
        self.noduleLabelmapSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.__onNoduleLabelmapChanged__)
        self.addFiducialButton.connect('clicked(bool)', self.__onAddFiducialButtonClicked__)
        self.enhanceVisualizationCheckbox.connect("stateChanged(int)", self.__onEnhanceVisualizationCheckChanged__)
        self.segmentButton.connect('clicked()', self.__onSegmentButtonClicked__)
        self.distanceLevelSlider.connect('sliderReleased()', self.checkAndRefreshModels)

        self.showSpheresButtonGroup.connect("buttonClicked(int)", self.__onShowSphereCheckboxClicked__)
        # runAnalysisButton.connect("clicked()", self.__onRunAnalysisButtonClicked__)
        self.runAnalysisButton.connect('clicked()', self.__onAnalyzeButtonClicked__)

        self.reportsWidget.addObservable(self.reportsWidget.EVENT_SAVE_BUTTON_CLICKED, self.forceSaveReport)
        self.evaluateSegmentationCheckbox.connect("clicked()", self.refreshUI)
        self.saveSeedsButton.connect("clicked()", self.saveCurrentSeedsToXML)
        self.loadSeedsButton.connect("clicked()", self.loadSeedsFromXML)
        self.saveTimeCostCheckbox.connect("stateChanged(int)", self.__onSaveTimeCostCheckboxClicked__)

        slicer.mrmlScene.AddObserver(slicer.vtkMRMLScene.EndCloseEvent, self.__onSceneClosed__)


        self.refreshUI()


    def refreshUI(self):
        """ Confiugre the GUI elements based on the current configuration
        """
        if self.inputVolumeSelector.currentNodeID != "":
            self.addFiducialButton.enabled = True
            self.addFiducialButton.toolTip = "Click and add a new seed in the volume"
        else:
            self.addFiducialButton.enabled = False
            self.addFiducialButton.toolTip = "Select a volume before adding any seed"
            self.__removeFiducialsFrames__()


        # Apply segmentation button allowed only if there is at least one seed
        if self.inputVolumeSelector.currentNodeID != "" and \
                        self.logic.getNumberOfFiducials(self.inputVolumeSelector.currentNodeID) > 0:
            self.segmentButton.setVisible(True)
        else:
            self.segmentButton.setVisible(False)

        # Level slider and Features Selection section active after running the segmentation algorithm
        self.selectThresholdLabel.visible = self.distanceLevelSlider.visible = self.logic.cliOutputScalarNode is not None

        # Show spheres buttons just visible for the analyzed spheres
        for mode in self.logic.spheresDict.iterkeys():
            for rad in self.logic.spheresDict[mode]:
                visible = self.workingMode == mode
                self.spheresButtonGroup.button(rad*10).setVisible(visible)
                # "Show sphere" radio buttons just visible if the analysis was already performed
                visible = (visible and self.__analyzedSpheres__.__contains__(rad))
                self.showSpheresButtonGroup.button(rad*10).setVisible(visible)
        # Other radius show button will be displayed every time any sphere has been analyzed
        self.otherRadiusShowSphereRadioButton.setVisible(len(self.__analyzedSpheres__) > 0)

        #self.progressBar.visible = self.distanceLevelSlider.enabled
        self.saveSeedsButton.visible = self.loadSeedsButton.visible = self.__evaluateSegmentationModeOn__
        self.reportsWidget.showSaveButton(self.__evaluateSegmentationModeOn__)




    def setAddSeedsMode(self, enabled):
        """ When enabled, the cursor will be enabled to add new fiducials that will be used for the segmentation
        :param enabled: boolean
        """
        applicationLogic = slicer.app.applicationLogic()
        if enabled:
            # print("DEBUG: entering __setAddSeedsMode__ - after enabled")
            if self.__validateInputVolumeSelection__():
                # Get the fiducials node
                fiducialsNodeList = self.logic.getFiducialsListNode(self.inputVolumeSelector.currentNodeID)
                # Set the cursor to draw fiducials
                markupsLogic = slicer.modules.markups.logic()
                markupsLogic.SetActiveListID(fiducialsNodeList)
                selectionNode = applicationLogic.GetSelectionNode()
                selectionNode.SetReferenceActivePlaceNodeClassName("vtkMRMLMarkupsFiducialNode")

                # Enable fiducials mode
                SlicerUtil.setFiducialsCursorMode(True, False)
        else:
            # Regular cursor mode (not fiducials)
            SlicerUtil.setFiducialsCursorMode(False)

    def addFiducialRow(self, fiducialsNode):
        """ Add a new row in the fiducials checkboxes section
        :param fiducialsNode:
        """
        if self.semaphoreOpen:  # To avoid the problem of duplicated events
            frame = qt.QFrame()
            frameLayout = qt.QHBoxLayout()
            frame.setLayout(frameLayout)

            n = fiducialsNode.GetNumberOfFiducials() - 1

            # Checkbox to select/unselect
            selectFiducialsCheckbox = qt.QCheckBox()
            selectFiducialsCheckbox.checked = True
            selectFiducialsCheckbox.text = "Seed " + str(n + 1)
            selectFiducialsCheckbox.toolTip = "Check/uncheck to include/exclude this seed"
            selectFiducialsCheckbox.objectName = n
            frameLayout.addWidget(selectFiducialsCheckbox)
            selectFiducialsCheckbox.clicked.connect(lambda: self.__onFiducialCheckClicked__(selectFiducialsCheckbox))

            # frame.layout().addWidget(fidButton)
            self.fiducialsContainerFrame.layout().addWidget(frame)
            self.addFiducialButton.checked = False

            # Avoid duplicated events for this fiducial node
            self.semaphoreOpen = False
            self.refreshUI()



    def checkAndRefreshModels(self, forceRefresh=False):
        """ Refresh the GUI if the slider value has changed since the last time"""
        if forceRefresh or self.lastRefreshValue != self.distanceLevelSlider.value:
            # Refresh slides
            # print("DEBUG: updating labelmaps with value:", float(self.distanceLevelSlider.value)/100)
            self.logic.updateModels(float(self.distanceLevelSlider.value) / 100)
            self.lastRefreshValue = self.distanceLevelSlider.value

            # Refresh visible windows
            SlicerUtil.refreshActiveWindows()

    def runNoduleSegmentation(self):
        """ Run the nodule segmentation through a CLI
        """
        maximumRadius = self.maximumRadiusSpinbox.value
        if self.__validateInputVolumeSelection__():
            result = self.logic.callNoduleSegmentationCLI(self.inputVolumeSelector.currentNodeID, maximumRadius,
                                                          self.__onCLISegmentationFinished__)
            self.progressBar.setCommandLineModuleNode(result)
            self.progressBar.visible = True
            SlicerUtil.setSetting(self.moduleName, "maximumRadius", maximumRadius)

            # Calculate meshgrid in parallel
            # self.logic.buildMeshgrid(self.inputVolumeSelector.currentNode())

    def runAnalysis(self):
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
        if self.inputVolumeSelector.currentNode() is None:
            # TODO: disable the button until segmentation is done
            qt.QMessageBox.warning(slicer.util.mainWindow(), "Select a volume",
                                   "Please select and segment an input volume")
            return
        if self.logic.currentLabelmap is None:
            qt.QMessageBox.warning(slicer.util.mainWindow(), "Segment a labelmap",
                                   "Please select and segment a labelmap volume")
            return
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
            keyName = self.inputVolumeSelector.currentNode().GetName()
            start = time.time()
            if self.noduleCheckbox.checked:
                logic = FeatureExtractionLogic(self.logic.currentVolume, self.logic.currentVolumeArray,
                                               self.logic.currentLabelmapArray,
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
                print(self.analysisResults[keyName])

                if self.logic.printTiming:
                    print("Elapsed time for the nodule analysis (TOTAL={0} seconds:".format(t2 - t1))
                    print(self.analysisResultsTiming[keyName])

            # Check in any sphere has been selected for the analysis, because otherwise it's not necessary to calculate the distance map
            anySphereChecked = False
            for r in self.logic.spheresDict[self.workingMode]:
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
                self.logic.getCurrentDistanceMap()
                if self.logic.printTiming:
                    print("Time to get the current distance map: {0} seconds".format(time.time() - t1))
                for r in self.logic.spheresDict[self.workingMode]:
                    if self.spheresButtonGroup.button(r*10).isChecked():
                        self.runAnalysisSphere(r, labelmapWholeVolumeArray)
                        self.__analyzedSpheres__.add(r)
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
                    self.runAnalysisSphere(r, labelmapWholeVolumeArray)
                    self.__analyzedSpheres__.add(r)

            t = time.time() - start
            if self.logic.printTiming:
                print("********* TOTAL ANALYSIS TIME: {0} SECONDS".format(t))

            # Save the results in the report widget
            qt.QMessageBox.information(slicer.util.mainWindow(), "Process finished",
                                       "Analysis finished. Total time: {0} seconds. Click the \"Open\" button to see the results".format(t))

            self.refreshUI()
        except StopIteration:
            qt.QMessageBox.warning(slicer.util.mainWindow(), "Process cancelled",
                                   "The process has been cancelled by the user")
        finally:
            self.saveReport(showConfirmation=False)

    def runAnalysisSphere(self, radius, labelmapWholeVolumeArray):
        """ Run the selected features for an sphere of radius r (excluding the nodule itself)
        :param radius:
        :return:
        """
        keyName = "{0}__r{1}".format(self.inputVolumeSelector.currentNode().GetName(), radius)
        t1 = time.time()
        labelmapArray = self.logic.getSphereLabelMapArray(radius)
        getSphereTime = time.time() - t1
        if self.logic.printTiming:
            print("Time elapsed to get a sphere labelmap of radius {0}: {1} seconds".format(radius, getSphereTime))
        slicer.app.processEvents()
        if labelmapArray.max() == 0:
            # Nothing to analyze
            results = {}
            for key in self.selectedFeatureKeys:
                results[key] = 0
            self.analysisResults[keyName] = results
        else:
            logic = FeatureExtractionLogic(self.logic.currentVolume, self.logic.currentVolumeArray,
                                           labelmapArray, self.selectedMainFeaturesKeys, self.selectedFeatureKeys,
                                           "__r{0}".format(radius), labelmapWholeVolumeArray)
            t1 = time.time()
            self.analysisResults[keyName] = collections.OrderedDict()
            self.analysisResultsTiming[keyName] = collections.OrderedDict()
            logic.run(self.analysisResults[keyName], self.logic.printTiming, self.analysisResultsTiming[keyName])
            t2 = time.time()

            print("********* Results for the sphere of radius {0}:".format(radius))
            print(self.analysisResults[keyName])
            if self.logic.printTiming:
                print("*** Elapsed time for the sphere radius {0} analysis (TOTAL={1} seconds:".format(radius, t2 - t1))
                print (self.analysisResultsTiming[keyName])

    def forceSaveReport(self):
        """ If basic report does not exist, it is created "on the fly"
        """
        keyName = self.inputVolumeSelector.currentNode().GetName()
        self.analysisResults = dict()
        self.analysisResults[keyName] = collections.OrderedDict()
        self.__saveBasicData__(keyName)
        self.saveReport()

    def saveReport(self, showConfirmation=True):
        """ Save the current values in a persistent csv file
        """
        keyName = self.inputVolumeSelector.currentNode().GetName()
        self.__saveSubReport__(keyName)
        for r in self.__analyzedSpheres__:
            keyName = "{0}__r{1}".format(self.inputVolumeSelector.currentNode().GetName(), r)
            self.__saveSubReport__(keyName)
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
        filePath = os.path.join(dirPath, self.logic.currentVolume.GetName() + "_seedEvaluation.xml")
        geom = GeometryTopologyData()
        geom.coordinate_system = GeometryTopologyData.LPS
        fidNode = self.logic.getCurrentFiducialsNode()
        for i in range(fidNode.GetNumberOfMarkups()):
            if fidNode.GetNthFiducialVisibility(i):
                coords = [0,0,0]
                fidNode.GetNthFiducialPosition(i, coords)
                coords = Util.ras_to_lps(coords)
                descr = None
                if self.lesionTypeRadioButtonGroup.checkedId() == 1:
                    descr = "Nodule"
                elif self.lesionTypeRadioButtonGroup.checkedId() == 2:
                    descr = "Tumor"
                geom.add_point(Point(0, 86, 0, coords, descr))

        geom.to_xml_file(filePath)
        qt.QMessageBox.information(slicer.util.mainWindow(), 'Data saved', 'The data were saved successfully in ' + filePath)

    def loadSeedsFromXML(self):
        """ Load all the seeds from a GeometryTopologyData object that is expected to be
        in Results folder of the module
        """
        if self.logic.currentVolume is None:
            self.logic.setActiveVolume(SlicerUtil.getFirstScalarNode().GetID())
        dirPath = os.path.join(SlicerUtil.getModuleFolder(self.moduleName), "Results")
        filePath = os.path.join(dirPath, self.logic.currentVolume.GetName() + "_seedEvaluation.xml")
        geom = GeometryTopologyData.from_xml_file(filePath)
        fidNode = self.logic.getCurrentFiducialsNode()
        for point in geom.points:
            position = Util.lps_to_ras(point.coordinate)
            index = fidNode.AddFiducial(*position)

        coords = Util.lps_to_ras(geom.points[0].coordinate)
        SlicerUtil.jumpToSeed(coords)

        self.timer.start()

    def reset(self):
        """ Reset the GUI
        """
        # Clean fiducials area
        self.__removeFiducialsFrames__()
        if self.logic.currentVolume is not None:
            fidNode = self.logic.getFiducialsListNode(self.logic.currentVolume.GetID())
            if fidNode is not None:
                slicer.mrmlScene.RemoveNode(fidNode)
        if self.logic.currentLabelmap is not None:
            slicer.mrmlScene.RemoveNode(self.logic.currentLabelmap)
        if self.logic.currentModelNode is not None:
            slicer.mrmlScene.RemoveNode(self.logic.currentModelNode)
        if self.logic.cliOutputScalarNode is not None:
            slicer.mrmlScene.RemoveNode(self.logic.cliOutputScalarNode)

        # Uncheck MIP
        self.enhanceVisualizationCheckbox.setChecked(False)
        # Free resources
        del self.logic
        # Recreate logic
        self.logic = CIP_LesionModelLogic()
        self.logic.printTiming = self.__printTimeCost__
        self.__analyzedSpheres__.clear()
        self.refreshUI()

    ############
    # Private methods
    ############
    def __activateCurrentLabelmap__(self):
        """ Display the right labelmap for the current background node if it exists"""
        # Set the current labelmap active
        selectionNode = slicer.app.applicationLogic().GetSelectionNode()
        selectionNode.SetReferenceActiveVolumeID(self.inputVolumeSelector.currentNodeID)

        selectionNode.SetReferenceActiveLabelVolumeID(self.logic.currentLabelmap.GetID())
        slicer.app.applicationLogic().PropagateVolumeSelection(0)


    def __validateInputVolumeSelection__(self):
        """ Check there is a valid input and/or output volume selected. Otherwise show a warning message
        :return: True if the validations are passed or False otherwise
        """
        inputVolumeId = self.inputVolumeSelector.currentNodeID
        if inputVolumeId == '':
            qt.QMessageBox.warning(slicer.util.mainWindow(), 'Warning', 'Please select an input volume')
            return False
        return True

    def __showSphere__(self, buttonId):
        if buttonId == 0:
            # Just nodule. No Spheres
            SlicerUtil.displayForegroundVolume(None)
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

        lm = self.logic.getSphereLabelMap(buttonId)
        # if lm is not None:
        SlicerUtil.displayForegroundVolume(lm.GetID(), 0.5)



    def __removeFiducialsFrames__(self):
        """ Remove all the possible fiducial frames that can remain obsolete (for example after closing a scene)
        """
        while len(self.fiducialsContainerFrame.children()) > 1:
            self.fiducialsContainerFrame.children()[1].hide()
            self.fiducialsContainerFrame.children()[1].delete()

    def __saveSubReport__(self, keyName):
        """ Save a report in Case Reports Widget for this case and a concrete radius
        :param keyName: CaseId[__rXX] where XX = sphere radius
        :param date: timestamp global to all records
        """
        if keyName in self.analysisResults and self.analysisResults[keyName] is not None \
                and len(self.analysisResults[keyName]) > 0:
            self.__saveBasicData__(keyName)
            self.reportsWidget.saveCurrentValues(**self.analysisResults[keyName])

            if self.logic.printTiming:
                # Save also timing report
                # self.analysisResultsTiming[keyName]["CaseId"] = keyName + "_timing"
                # self.analysisResultsTiming[keyName]["Date"] = date
                self.__saveBasicData__(keyName, isTiming=True)
                self.reportsWidget.saveCurrentValues(**self.analysisResultsTiming[keyName])

    def __saveBasicData__(self, keyName, isTiming=False):
        date = time.strftime("%Y/%m/%d %H:%M:%S")
        threshold = self.distanceLevelSlider.value
        # Read seeds
        fidNode = self.logic.getCurrentFiducialsNode()
        coordsList = []
        for i in range(fidNode.GetNumberOfMarkups()):
            if fidNode.GetNthFiducialVisibility(i):
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
        d[keyName]["Threshold"] = threshold
        d[keyName]["LesionType"] = self.lesionType
        d[keyName]["Seeds_LPS"] = coordsList.__str__()

    def __updateFOV__(self):
        """ Dynamic zoom to the center of the current view in all the 2D windows
        :return:
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
            self.timer.stop()

    ############
    # Events
    ############
    def enter(self):
        """This is invoked every time that we select this module as the active module in Slicer (not only the first time)"""
        if self.inputVolumeSelector.currentNodeID != '':
            self.logic.getFiducialsListNode(self.inputVolumeSelector.currentNodeID, self.__onFiducialsNodeModified__)
            self.logic.setActiveVolume(self.inputVolumeSelector.currentNodeID)

        if self.addFiducialButton.checked:
            self.setAddSeedsMode(True)
            # if not self.timer.isActive() \
            #         and self.logic.currentLabelmap is not None:  # Segmentation was already performed
            #     self.timer.start(500)

        self.refreshUI()


    def __onVolumeAddedToScene__(self, scalarNode):
        if self.inputVolumeSelector.currentNode() is None:
            self.inputVolumeSelector.setCurrentNode(scalarNode)

    def __onInputVolumeChanged__(self, node):
        """ Input volume selector changed
        :param node: selected node
        """
        if node is not None:
            # Create the fiducials node in case it doesn't exist yet
            self.logic.getFiducialsListNode(node.GetID(), self.__onFiducialsNodeModified__)
            # Switch to the current node
            self.logic.setActiveVolume(node.GetID())

        # elif self.timer.isActive():
        #     # Stop checking if there is no selected node
        #     self.timer.stop()

        self.refreshUI()

    def __onNoduleLabelmapChanged__(self, node):
        self.logic.currentLabelmap = node
        self.refreshUI()

    def __onPreVolumeLoad__(self, volume):
        self.reset()

    def __onEnhanceVisualizationCheckChanged__(self, state):
        active = self.enhanceVisualizationCheckbox.isChecked()
        self.mipFrame.visible = active
        self.mipViewer.activateEnhacedVisualization(active)
        if not active:
            # Reset layout. Force the cursor state because it changes to seeds mode for some unexplained reason!
            SlicerUtil.setFiducialsCursorMode(False)


    def __onAddFiducialButtonClicked__(self, checked):
        """ Click the add fiducial button so that we set the cursor in fiducial mode
        :param checked:
        :return:
        """
        self.semaphoreOpen = True
        if not (self.__validateInputVolumeSelection__()):
            self.addFiducialButton.checked = False
            return

        self.setAddSeedsMode(checked)

    def __onSegmentButtonClicked__(self):
        self.segmentButton.setEnabled(False)
        self.runNoduleSegmentation()


    def __onFiducialsNodeModified__(self, nodeID, event):
        """ The active fiducials node has been modified because we added or removed a fiducial
        :param nodeID: Current node id
        :param event:
        """
        # print("DEBUG: Fiducials node modified.", nodeID)
        self.addFiducialRow(nodeID)
        self.refreshUI()

    def __onFiducialCheckClicked__(self, checkBox):
        """ Click in one of the checkboxes that is associated with every fiducial
        :param checkBox: checkbox that has been clicked
        :return:
        """
        n = int(checkBox.objectName)
        logic = slicer.modules.markups.logic()
        fiducialsNode = slicer.util.getNode(logic.GetActiveListID())
        fiducialsNode.SetNthFiducialSelected(n, checkBox.checked)
        fiducialsNode.SetNthFiducialVisibility(n, checkBox.checked)
        # If selected, go to this markup
        if checkBox.checked:
            logic.JumpSlicesToNthPointInMarkup(fiducialsNode.GetID(), n, True)

    def __onCLISegmentationFinished__(self):
        """ Triggered when the CLI segmentation has finished the work.
        This is achieved because this is the function that we specify as a callback
        when calling the function "callCLI" in the logic class
        :return:
        """
        self.distanceLevelSlider.value = self.logic.defaultThreshold  # default
        self.__activateCurrentLabelmap__()

        r = self.logic.cliOutputScalarNode.GetImageData().GetScalarRange()

        self.distanceLevelSlider.minimum = r[0] * 100
        self.distanceLevelSlider.maximum = r[1] * 100
        self.distanceLevelSlider.value = self.logic.defaultThreshold

        self.checkAndRefreshModels(forceRefresh=True)
        self.progressBar.hide()

        # Center the volume in the first visible seed
        fidNode = self.logic.getCurrentFiducialsNode()
        for i in range(fidNode.GetNumberOfMarkups()):
            if fidNode.GetNthFiducialVisibility(i):
                coords = [0,0,0]
                fidNode.GetNthFiducialPosition(i, coords)
                break
        SlicerUtil.jumpToSeed(coords)
        self.segmentButton.setEnabled(True)
        # self.refreshUI()
        self.noduleLabelmapSelector.setCurrentNode(self.logic.currentLabelmap)

        # Start the timer that will refresh all the visualization nodes
        # self.timer.start(500)

    def __onShowSphereCheckboxClicked__(self, buttonId):
        self.__showSphere__(buttonId)

    def __onSaveSegmentationResultsClicked__(self):
        self.saveCurrentSeedsToXML()

    def __onSaveTimeCostCheckboxClicked__(self, checked):
        self.logic.printTiming = (checked == 2)

    def __onAnalyzeButtonClicked__(self):
        self.runAnalysis()

    def __onSceneClosed__(self, arg1, arg2):
        # self.timer.stop()
        self.reset()


    def exit(self):
        """This is invoked every time that we switch to another module (not only when Slicer is closed)."""
        # Disable chekbox of fiducials so that the cursor is not in "fiducials mode" forever if the
        # user leaves the module
        # self.timer.stop()
        self.setAddSeedsMode(False)

    def cleanup(self):
        """This is invoked as a destructor of the GUI when the module is no longer going to be used"""
        # self.timer.stop()
        self.setAddSeedsMode(False)

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

    def __init__(self, workingMode=WORKING_MODE_HUMAN):
        self.currentVolume = None  # Current active volume
        self.__currentVolumeArray__ = None  # Numpy array that represents the current volume
        self.currentLabelmap = None  # Current label map that contains the nodule segmentation for the current threshold (same size as the volume)
        self.__currentLabelmapArray__ = None  # Numpy array that represents the current label map
        self.cliOutputScalarNode = None  # Scalar volume that the CLI returns. This will be a cropped volume

        self.currentModelNodeId = None  # 3D model volume id
        self.defaultThreshold = 0  # Default threshold for the map distance used in the nodule segmentation
        self.onCLISegmentationFinishedCallback = None
        self.invokedCLI = False  # Semaphore to avoid duplicated events

        # self.origin = None                  # Current origin (centroid of the nodule)
        self.currentDistanceMap = None  # Current distance map from the specified origin
        self.currentCentroid = None  # Centroid of the nodule
        self.spheresLabelmaps = dict()  # Labelmap of spheres for a particular radius

        # Different sphere sizes depending on the case
        self.workingMode = workingMode
        self.spheresDict = dict()
        self.spheresDict[self.WORKING_MODE_HUMAN] = (15, 20, 25)  # Humans
        self.spheresDict[self.WORKING_MODE_SMALL_ANIMAL] = (1.5, 2, 2.5)  # Mouse

        self.thresholdFilter = None
        self.marchingCubesFilter = None

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
    def currentModelNode(self):
        if self.currentModelNodeId is None:
            return None
        return slicer.util.getNode(self.currentModelNodeId)

    @property
    def currentVolumeArray(self):
        if self.__currentVolumeArray__ is None and self.currentVolume is not None:
            self.__currentVolumeArray__ = slicer.util.array(self.currentVolume.GetName())
        return self.__currentVolumeArray__

    @currentVolumeArray.setter
    def currentVolumeArray(self, value):
        self.__currentVolumeArray__ = value

    @property
    def currentLabelmapArray(self):
        if self.__currentLabelmapArray__ is None and self.currentLabelmap is not None:
            self.__currentLabelmapArray__ = slicer.util.array(self.currentLabelmap.GetName())
        return self.__currentLabelmapArray__

    @currentLabelmapArray.setter
    def currentLabelmapArray(self, value):
        self.__currentLabelmapArray__ = value

    ##############################
    # General volume / fiducials methods
    ##############################
    def setActiveVolume(self, volumeID):
        """ Set the current volume as active and try to load the preexisting associated structures
        (labelmaps, CLI segmented nodes, numpy arrays...)
        :param volumeID:
        :return:
        """
        self.currentVolume = slicer.util.getNode(volumeID)

        # Switch the fiducials node
        fiducialsNode = self.getFiducialsListNode(volumeID)
        markupsLogic = slicer.modules.markups.logic()
        markupsLogic.SetActiveListID(fiducialsNode)

        # Search for preexisting labelmap
        #labelmapName = self.currentVolume.GetName() + '_nodulelm'
        labelmapName = self.currentVolume.GetName() + self.__SUFFIX__SEGMENTED_LABELMAP
        self.currentLabelmap = slicer.util.getNode(labelmapName)
        #segmentedNodeName = self.currentVolume.GetID() + '_segmentedlm'
        segmentedNodeName = self.__PREFIX_INPUTVOLUME__ + self.currentVolume.GetID()
        self.cliOutputScalarNode = slicer.util.getNode(segmentedNodeName)

    def __createFiducialsListNode__(self, fiducialsNodeName, onModifiedCallback=None):
        """ Create a new fiducials list node for the current volume
        :param fiducialsNodeName: fiducials node name that will be created
        :param onModifiedCallback: function that will be connected to node's "ModifiedEvent"
        :return: True if the node was created or False if it already existed
        """
        markupsLogic = slicer.modules.markups.logic()
        fiducialsNode = slicer.util.getNode(fiducialsNodeName)
        if fiducialsNode is not None:
            return False  # Node already created

        # Create new fiducials node
        fiducialListNodeID = markupsLogic.AddNewFiducialNode(fiducialsNodeName, slicer.mrmlScene)
        fiducialsNode = slicer.util.getNode(fiducialListNodeID)
        # Make the new fiducials node the active one
        markupsLogic.SetActiveListID(fiducialsNode)
        # Hide any text from all the fiducials
        fiducialsNode.SetMarkupLabelFormat('')
        displayNode = fiducialsNode.GetDisplayNode()
        # displayNode.SetColor([1,0,0])
        displayNode.SetSelectedColor([1, 0, 0])
        displayNode.SetGlyphScale(2)
        displayNode.SetGlyphType(8)  # Diamond shape (I'm so cool...)

        # Add observer when specified
        if onModifiedCallback is not None:
            # The callback function will be invoked when the fiducials node is modified
            fiducialsNode.AddObserver("ModifiedEvent", onModifiedCallback)

        # Node created succesfully
        return True

    def getFiducialsListNode(self, volumeId, onModifiedCallback=None):
        """ Get the current fiducialsListNode for the specified volume, and creates it in case
        it doesn't exist yet.
        :param volumeId: fiducials list will be connected to this volume
        :param onModifiedCallback: function to call when the fiducial is modified (optional)
        :return: the fiducials node or None if something fails
        """
        if volumeId == "":
            return None

        # Check if the node already exists
        fiducialsNodeName = volumeId + '_fiducialsNode'

        fiducialsNode = slicer.util.getNode(fiducialsNodeName)
        if fiducialsNode is not None:
            if onModifiedCallback is not None:
                fiducialsNode.AddObserver("ModifiedEvent", onModifiedCallback)
            return fiducialsNode

        # Create new fiducials node
        if self.__createFiducialsListNode__(fiducialsNodeName, onModifiedCallback):
            return slicer.util.getNode(fiducialsNodeName)  # return the created node

        return None  # The process failed

    def getCurrentFiducialsNode(self):
        return self.getFiducialsListNode(self.currentVolume.GetID())

    def getNumberOfFiducials(self, volumeId):
        """ Get the number of fiducials currently set for this volume
        :param volumeId:
        :return:
        """
        fid = self.getFiducialsListNode(volumeId)
        if fid:
            return fid.GetNumberOfMarkups()
        return None  # Error

    ##############################
    # CLI Nodule segmentation
    ##############################
    def callNoduleSegmentationCLI(self, inputVolumeID, maximumRadius, onCLISegmentationFinishedCallback=None):
        """ Invoke the Lesion Segmentation CLI for the specified volume and fiducials.
        Note: the fiducials will be retrieved directly from the scene
        :param inputVolumeID:
        :return:
        """
        # Try to load preexisting structures
        self.setActiveVolume(inputVolumeID)

        if self.cliOutputScalarNode is None:
            # Create the scalar node that will work as the CLI output
            self.cliOutputScalarNode = slicer.mrmlScene.CreateNodeByClass("vtkMRMLScalarVolumeNode")
            #segmentedNodeName = self.currentVolume.GetID() + '_segmentedlm'
            segmentedNodeName = self.__PREFIX_INPUTVOLUME__ + self.currentVolume.GetID()
            self.cliOutputScalarNode.SetName(segmentedNodeName)
            slicer.mrmlScene.AddNode(self.cliOutputScalarNode)

        parameters = {}
        print("Calling CLI...")
        parameters["inputImage"] = inputVolumeID
        parameters["outputLevelSet"] = self.cliOutputScalarNode
        parameters["seedsFiducials"] = self.getFiducialsListNode(inputVolumeID)
        parameters["maximumRadius"] = maximumRadius
        parameters["fullSizeOutput"] = True
        self.invokedCLI = False  # Semaphore to avoid duplicated events

        module = slicer.modules.generatelesionsegmentation
        result = slicer.cli.run(module, None, parameters)

        # Observer when the state of the process is modified
        result.AddObserver('ModifiedEvent', self.__onNoduleSegmentationCLIStateUpdated__)
        # Function that will be invoked when the CLI finishes
        self.onCLISegmentationFinishedCallback = onCLISegmentationFinishedCallback

        return result

    def updateModels(self, newThreshold):
        """ Modify the threshold for the current volume (update the models)
        :param newThreshold: new threshold (all the voxels below this threshold will be considered nodule)
        """
        print("DEBUG: updating models with threshold={0}....".format(newThreshold))
        self.thresholdFilter.ThresholdByUpper(newThreshold)
        self.thresholdFilter.Update()
        self.marchingCubesFilter.SetValue(0, newThreshold)
        self.marchingCubesFilter.Update()
        self.currentLabelmapArray = slicer.util.array(self.currentLabelmap.GetName())
        # Invalidate distances (the nodule is going to change)
        self.__invalidateDistances__()
        # Refresh 3D view
        viewNode = slicer.util.getNode('vtkMRMLViewNode*')
        viewNode.Modified()

    def getCurrentDistanceMap(self):
        """ Calculate the distance map to the centroid for the current labelmap volume.
        To that end, we have to calculate first the centroid.
        Please note the results could be cached
        :return:
        """
        if self.currentDistanceMap is None:
            centroid = Util.centroid(self.currentLabelmapArray)
            # Calculate the distance map for the specified origin
            # Get the dimensions of the volume in ZYX coords
            dims = Util.vtk_numpy_coordinate(self.currentVolume.GetImageData().GetDimensions())
            # Speed map (all ones because the growth will be constant).
            # The dimensions are reversed because we want the format in ZYX coordinates
            input = np.ones(dims, np.int32)
            sitkImage = sitk.GetImageFromArray(input)
            sitkImage.SetSpacing(self.currentVolume.GetSpacing())
            fastMarchingFilter = sitk.FastMarchingImageFilter()
            fastMarchingFilter.SetStoppingValue(self.MAX_TUMOR_RADIUS)
            # Reverse the coordinate of the centroid
            seeds = [Util.numpy_itk_coordinate(centroid)]
            fastMarchingFilter.SetTrialPoints(seeds)
            output = fastMarchingFilter.Execute(sitkImage)
            self.currentDistanceMap = sitk.GetArrayFromImage(output)

    def getSphereLabelMapArray(self, radius):
        """ Get a labelmap numpy array that contains a sphere centered in the nodule centroid, with radius "radius" and that
        EXCLUDES the nodule itself.
        If the results are not cached, this method creates the volume and calculates the labelmap
        :param radius: radius of the sphere
        :return: labelmap array for a sphere of this radius
        """
        # If the shere was already calculated, return the results
        if self.spheresLabelmaps.has_key(radius):
            return self.spheresLabelmaps[radius]
        # Init with the current segmented nodule labelmap
        # Mask with the voxels that are inside the radius of the sphere
        array = self.currentDistanceMap <= radius
        # Exclude the nodule
        array[self.currentLabelmapArray == 1] = 0
        # Cache the result
        self.spheresLabelmaps[radius] = array
        # Create a mrml labelmap node for sphere visualization purposes (this step could be skipped)
        self.__createLabelmapSphereVolume__(array, radius)
        return array

    def getSphereLabelMap(self, radius):
        if SlicerUtil.IsDevelopment:
            print("DEBUG: get sphere lm ", radius)
        return slicer.util.getNode("{0}_r{1}".format(self.currentVolume.GetName(), radius))


    ################
    # PRIVATE METHODS
    ################
    def __onNoduleSegmentationCLIStateUpdated__(self, caller, event):
        """ Event triggered when the CLI status changes
        :param caller:
        :param event:
        :return:
        """
        self.caller = caller
        if caller.IsA('vtkMRMLCommandLineModuleNode') \
                and not self.invokedCLI:  # Semaphore to avoid duplicated events
            if caller.GetStatus() == caller.Completed:
                self.invokedCLI = True
                self.__processNoduleSegmentationCLIResults__()
            elif caller.GetStatus() == caller.CompletedWithErrors:
                # TODO: print current parameters with caller.GetParameterDefault()
                raise Exception("The Nodule Segmentation CLI failed")

    def __processNoduleSegmentationCLIResults__(self):
        """ Method called once that the cli has finished the process.
        Create a new labelmap (currentLabelmap) and a model node with the result of the process.
        It also creates a numpy array associated with the labelmap (currentLabelmapArray)
        """
        print("DEBUG: processing results from process Nodule CLI...")
        if self.thresholdFilter is None:
            # Create vtk filters
            self.thresholdFilter = vtk.vtkImageThreshold()
        # The cliOutputScalarNode is new, so we have to set all the values again
        self.thresholdFilter.SetInputData(self.cliOutputScalarNode.GetImageData())
        self.thresholdFilter.SetReplaceOut(True)
        self.thresholdFilter.SetOutValue(0)  # Value of the background
        self.thresholdFilter.SetInValue(1)  # Value of the segmented nodule

        labelmapName = self.currentVolume.GetName() + self.__SUFFIX__SEGMENTED_LABELMAP
        self.currentLabelmap = slicer.util.getNode(labelmapName)
        if self.currentLabelmap is None:
            # Create a labelmap with the same dimensions that the ct volume
            self.currentLabelmap = SlicerUtil.getLabelmapFromScalar(self.cliOutputScalarNode, labelmapName)
            self.currentLabelmap.SetImageDataConnection(self.thresholdFilter.GetOutputPort())

        if self.marchingCubesFilter is None:
            self.marchingCubesFilter = vtk.vtkMarchingCubes()
        # The cliOutputScalarNode is new, so we have to set all the values again
        self.marchingCubesFilter.SetInputData(self.cliOutputScalarNode.GetImageData())
        self.marchingCubesFilter.SetValue(0, self.defaultThreshold)

        newNode = self.currentModelNode is None
        if newNode:
            # Create the result model node and connect it to the pipeline
            modelsLogic = slicer.modules.models.logic()
            currentModelNode = modelsLogic.AddModel(self.marchingCubesFilter.GetOutputPort())
            self.currentModelNodeId = currentModelNode.GetID()
            # Create a DisplayNode and associate it to the model, in order that transformations can work properly
            displayNode = slicer.vtkMRMLModelDisplayNode()
            displayNode.SetColor((0.255, 0.737, 0.851))
            slicer.mrmlScene.AddNode(displayNode)
            currentModelNode.AddAndObserveDisplayNodeID(displayNode.GetID())

        if self.onCLISegmentationFinishedCallback is not None:
            # Delegate the responsibility of updating the models with a chosen threshold (regular case)
            self.onCLISegmentationFinishedCallback()
        else:
            self.updateModels(self.defaultThreshold)  # Use default threshold value

        if newNode:
            # Align the model with the segmented labelmap applying a transformation
            transformMatrix = vtk.vtkMatrix4x4()
            self.currentLabelmap.GetIJKToRASMatrix(transformMatrix)
            currentModelNode.ApplyTransformMatrix(transformMatrix)
            # Center the 3D view in the seed/s
            layoutManager = slicer.app.layoutManager()
            threeDWidget = layoutManager.threeDWidget(0)
            threeDView = threeDWidget.threeDView()
            threeDView.resetFocalPoint()

    def __invalidateDistances__(self):
        """ Invalidate the current nodule centroid, distance maps, etc.
        """
        self.currentDistanceMap = None
        self.currentCentroid = None
        self.spheresLabelmaps = dict()

    def __createLabelmapSphereVolume__(self, array, radius):
        """ Create a Labelmap volume cloning the current global labelmap with the ROI sphere for visualization purposes
        :param array: labelmap array
        :param radius: radius of the sphere (used for naming the volume)
        :return: volume created
        """
        node = SlicerUtil.cloneVolume(self.currentLabelmap, "{0}_r{1}".format(self.currentVolume.GetName(), radius))
        arr = slicer.util.array(node.GetName())
        arr[:] = array
        node.GetImageData().Modified()
        # Set a different colormap for visualization purposes
        colorNode = slicer.util.getFirstNodeByClassByName("vtkMRMLColorTableNode", "HotToColdRainbow")
        displayNode = node.GetDisplayNode()
        displayNode.SetAndObserveColorNodeID(colorNode.GetID())
        return node


class CIP_LesionModelTest(ScriptedLoadableModuleTest):
    """
    This is the test case for your scripted module.
    Uses ScriptedLoadableModuleTest base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def setUp(self):
        """ Do whatever is needed to reset the state - typically a scene clear will be enough.
        """
        slicer.mrmlScene.Clear(0)

    def runTest(self):
        """Run as few or as many tests as needed here.
        """
        self.setUp()
        self.test_CIP_LesionModel_PrintMessage()

    def test_CIP_LesionModel_PrintMessage(self):
        self.delayDisplay("Starting the test")
        # logic = CIP_LesionModelLogic()
        # myMessage = "Print this test message in console"
        # logging.info("Starting the test with this message: " + myMessage)
        # expectedMessage = "I have printed this message: " + myMessage
        # logging.info("The expected message would be: " + expectedMessage)
        # responseMessage = logic.printMessage(myMessage)
        # logging.info("The response message was: " + responseMessage)
        # self.assertTrue(responseMessage == expectedMessage)
        # self.delayDisplay('Test passed!')
        # t = unittest.TestCase()
        self.fail("Test not implemented yet")
