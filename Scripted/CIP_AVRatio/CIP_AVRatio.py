# -*- coding: utf-8 -*-
import logging
from collections import OrderedDict

import os
import numpy as np
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *

from CIP.logic.SlicerUtil import SlicerUtil
from CIP.logic import Util
from CIP.ui import CaseReportsWidget
from CIP.ui import PdfReporter

#
# CIP_AVRatio
#
class CIP_AVRatio(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "AV Ratio"
        self.parent.categories = SlicerUtil.CIP_ModulesCategory
        self.parent.dependencies = [SlicerUtil.CIP_ModuleName]
        self.parent.contributors = ["Pietro Nardelli (pnardelli@bwh.harvard.edu)", "Applied Chest Imaging Laboratory", "Brigham and Women's Hospital"]
        self.parent.helpText = """Calculate the ratio between pulmonary airway and vessel.<br>
            A quick tutorial of the module can be found <a href='https://s3.amazonaws.com/acil-public/SlicerCIP+Tutorials/AV_Ratio.pptx'>here</a>.<br><br>
            """
        self.parent.acknowledgementText = SlicerUtil.ACIL_AcknowledgementText

#
# CIP_AVRatioWidget
#
class CIP_AVRatioWidget(ScriptedLoadableModuleWidget):
    """Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """
    AXIAL = 6
    SAGITTAL = 7
    CORONAL = 8

    @property
    def currentVolumeId(self):
        return self.volumeSelector.currentNodeID

    def __init__(self, parent):
        ScriptedLoadableModuleWidget.__init__(self, parent)
        self.moduleName = "CIP_AVRatio"
        from functools import partial
        def __onNodeAddedObserver__(self, caller, eventId, callData):
            """Node added to the Slicer scene"""
            if callData.GetClassName() == 'vtkMRMLScalarVolumeNode' \
                    and slicer.util.mainWindow().moduleSelector().selectedModule == self.moduleName:    # Current module visible
                self.volumeSelector.setCurrentNode(callData)
                SlicerUtil.changeContrastWindow(350, 40)
                self.initialFOV = self.getInitialFOV()

            elif callData.GetClassName() == 'vtkMRMLAnnotationRulerNode':
                self.setRulersOptions(self.rulers_ID, self.rulerType, self.structureID)
                self.refreshTextboxes()

        self.__onNodeAddedObserver__ = partial(__onNodeAddedObserver__, self)
        self.__onNodeAddedObserver__.CallDataType = vtk.VTK_OBJECT

        # Timer for dynamic zooming
        self.zoomToSeedTimer = qt.QTimer()
        self.zoomToSeedTimer.setInterval(50)
        self.zoomToSeedTimer.timeout.connect(self.zoomToSeed)

        self.interactor = None
        self.rulerType = -1
        self.structureID = -1

        self.initialFOV = self.getInitialFOV()
        # self.initialRAS = self.getInitialRAS()
        self.initialRAS = [0.0, 0.0, 0.0]
        self.zoomed = False

        self.shortcuts = []
        self.activeRuler = None

        self.rulers_ID = 0

    def setup(self):
        """This is called one time when the module GUI is initialized
        """
        ScriptedLoadableModuleWidget.setup(self)

        # Create objects that can be used anywhere in the module. Example: in most cases there should be just one
        # object of the logic class
        self.logic = CIP_AVRatioLogic()

        #
        # Create all the widgets. Example Area
        mainAreaCollapsibleButton = ctk.ctkCollapsibleButton()
        mainAreaCollapsibleButton.text = "Main parameters"
        self.layout.addWidget(mainAreaCollapsibleButton)
        self.mainAreaLayout = qt.QGridLayout(mainAreaCollapsibleButton)

        self.label = qt.QLabel("Select the volume")
        self.label.setStyleSheet("margin:10px 0 20px 7px")
        self.mainAreaLayout.addWidget(self.label, 0, 0)

        self.volumeSelector = slicer.qMRMLNodeComboBox()
        self.volumeSelector.nodeTypes = ( "vtkMRMLScalarVolumeNode", "" )
        self.volumeSelector.name = "av_volumeSelector"
        self.volumeSelector.selectNodeUponCreation = True
        self.volumeSelector.autoFillBackground = True
        self.volumeSelector.addEnabled = True
        self.volumeSelector.noneEnabled = False
        self.volumeSelector.removeEnabled = False
        self.volumeSelector.showHidden = False
        self.volumeSelector.showChildNodeTypes = False
        self.volumeSelector.setMRMLScene( slicer.mrmlScene )
        self.volumeSelector.setStyleSheet("margin:0px 0 0px 0; padding:2px 0 2px 5px")
        self.mainAreaLayout.addWidget(self.volumeSelector, 0, 1)

        #
        # Buttons to enlarge views upon request
        #
        self.viewsGroupBox = qt.QGroupBox("Choose the view")
        self.viewsGroupBox.setLayout(qt.QHBoxLayout())
        self.mainAreaLayout.addWidget(self.viewsGroupBox, 1, 1)

        #
        # Red Slice Button
        #
        self.redViewButton = qt.QToolButton()
        self.redViewButton.toolTip = "Red slice only."
        self.redViewButton.setToolButtonStyle(3)
        self.redViewButton.enabled = True
        self.redViewButton.setFixedSize(60, 43)
        redIcon = qt.QIcon(":/Icons/LayoutOneUpRedSliceView.png")
        self.redViewButton.setIcon(redIcon)
        self.redViewButton.setText('Axial')
        # self.redViewButton.setStyleSheet("font-weight:bold")
        self.viewsGroupBox.layout().addWidget(self.redViewButton)


        #
        # Yellow Slice Button
        #
        self.yellowViewButton = qt.QToolButton()
        self.yellowViewButton.toolTip = "Yellow slice only."
        self.yellowViewButton.setToolButtonStyle(3)
        self.yellowViewButton.enabled = True
        self.yellowViewButton.setFixedSize(60, 43)
        yellowIcon = qt.QIcon(":/Icons/LayoutOneUpYellowSliceView.png")
        self.yellowViewButton.setIcon(yellowIcon)
        self.yellowViewButton.setText('Sagittal')
        # self.yellowViewButton.setStyleSheet("font-weight:bold")
        self.viewsGroupBox.layout().addWidget(self.yellowViewButton)

        #
        # Green Slice Button
        #
        self.greenViewButton = qt.QToolButton()
        self.greenViewButton.toolTip = "Yellow slice only."
        self.greenViewButton.setToolButtonStyle(3)
        self.greenViewButton.enabled = True
        self.greenViewButton.setFixedSize(60, 43)
        greenIcon = qt.QIcon(":/Icons/LayoutOneUpGreenSliceView.png")
        self.greenViewButton.setIcon(greenIcon)
        self.greenViewButton.setText('Coronal')
        # self.greenViewButton.setStyleSheet("font-weight:bold")
        self.viewsGroupBox.layout().addWidget(self.greenViewButton)

        # Structure Selector
        self.structuresGroupbox = qt.QGroupBox("Select the structure")
        self.groupboxLayout = qt.QVBoxLayout()
        self.structuresGroupbox.setLayout(self.groupboxLayout)
        self.structuresGroupbox.setFixedHeight(100)
        self.mainAreaLayout.addWidget(self.structuresGroupbox, 2, 0)

        self.structuresButtonGroup=qt.QButtonGroup()

        self.btnBoth = qt.QRadioButton("Both")
        self.btnBoth.name = "avButton"
        self.btnBoth.checked = True
        self.structuresButtonGroup.addButton(self.btnBoth, 0)
        self.groupboxLayout.addWidget(self.btnBoth)

        self.btnA = qt.QRadioButton("Airway")
        self.btnA.name = "airwayRadioButton"
        self.structuresButtonGroup.addButton(self.btnA, 1)
        self.groupboxLayout.addWidget(self.btnA)

        self.btnV = qt.QRadioButton("Vessel")
        self.btnV.name = "vesselRadioButton"
        self.structuresButtonGroup.addButton(self.btnV, 2)
        self.groupboxLayout.addWidget(self.btnV)

        ### Buttons toolbox
        self.buttonsToolboxFrame = qt.QFrame()
        self.buttonsToolboxLayout = qt.QGridLayout()
        self.buttonsToolboxFrame.setLayout(self.buttonsToolboxLayout)
        self.mainAreaLayout.addWidget(self.buttonsToolboxFrame, 2, 1)

        self.zoomToPlaceButton = ctk.ctkPushButton()
        self.zoomToPlaceButton.text = "Zoom in on region"
        self.zoomToPlaceButton.toolTip = "Zoom to clicked region"
        self.zoomToPlaceButton.setIcon(qt.QIcon("{0}/zoom_in.png".format(SlicerUtil.CIP_ICON_DIR)))
        self.zoomToPlaceButton.setIconSize(qt.QSize(20, 20))
        # self.zoomToPlaceButton.setFixedWidth(123)
        self.buttonsToolboxLayout.addWidget(self.zoomToPlaceButton, 0, 0)

        self.zoomBackButton = ctk.ctkPushButton()
        self.zoomBackButton.text = "Zoom out"
        self.zoomBackButton.toolTip = "Zoom out"
        self.zoomBackButton.setIcon(qt.QIcon("{0}/zoom_out.png".format(SlicerUtil.CIP_ICON_DIR)))
        self.zoomBackButton.setIconSize(qt.QSize(20, 20))
        self.zoomBackButton.setFixedWidth(116)
        self.buttonsToolboxLayout.addWidget(self.zoomBackButton, 0, 1)

        self.placeLongAirwayRulerButton = ctk.ctkPushButton()
        self.placeLongAirwayRulerButton.text = "Long airway ruler"
        self.placeLongAirwayRulerButton.name = "placeLongAirwayRulerButton"
        self.placeLongAirwayRulerButton.toolTip = "Activate the ruler for the long diameter airway"
        self.placeLongAirwayRulerButton.setIcon(qt.QIcon("{0}/ruler.png".format(SlicerUtil.CIP_ICON_DIR)))
        self.placeLongAirwayRulerButton.setIconSize(qt.QSize(20, 20))
        self.placeLongAirwayRulerButton.setFixedWidth(132)
        self.placeLongAirwayRulerButton.setStyleSheet("font-weight:bold")
        self.buttonsToolboxLayout.addWidget(self.placeLongAirwayRulerButton, 2, 0)

        self.placeShortAirwayRulerButton = ctk.ctkPushButton()
        self.placeShortAirwayRulerButton.text = "Short airway ruler"
        self.placeShortAirwayRulerButton.name = "placeShortAirwayRulerButton"
        self.placeShortAirwayRulerButton.toolTip = "Activate the ruler for the short diameter airway"
        self.placeShortAirwayRulerButton.setIcon(qt.QIcon("{0}/ruler.png".format(SlicerUtil.CIP_ICON_DIR)))
        self.placeShortAirwayRulerButton.setIconSize(qt.QSize(20, 20))
        self.placeShortAirwayRulerButton.setFixedWidth(132)
        self.placeShortAirwayRulerButton.setStyleSheet("font-weight:bold")
        self.buttonsToolboxLayout.addWidget(self.placeShortAirwayRulerButton, 2, 1)

        self.placeLongVesselRulerButton = ctk.ctkPushButton()
        self.placeLongVesselRulerButton.text = "Long vessel ruler"
        self.placeLongVesselRulerButton.name = "placeLongVesselRulerButton"
        self.placeLongVesselRulerButton.toolTip = "Activate the ruler for the long diameter vessel"
        self.placeLongVesselRulerButton.setIcon(qt.QIcon("{0}/ruler.png".format(SlicerUtil.CIP_ICON_DIR)))
        self.placeLongVesselRulerButton.setIconSize(qt.QSize(20, 20))
        self.placeLongVesselRulerButton.setFixedWidth(132)
        self.placeLongVesselRulerButton.setStyleSheet("font-weight:bold")
        self.buttonsToolboxLayout.addWidget(self.placeLongVesselRulerButton, 3, 0)

        self.placeShortVesselRulerButton = ctk.ctkPushButton()
        self.placeShortVesselRulerButton.text = "Short vessel ruler"
        self.placeShortVesselRulerButton.name = "placeShortVesselRulerButton"
        self.placeShortVesselRulerButton.toolTip = "Activate the ruler for the short diameter vessel"
        self.placeShortVesselRulerButton.setIcon(qt.QIcon("{0}/ruler.png".format(SlicerUtil.CIP_ICON_DIR)))
        self.placeShortVesselRulerButton.setIconSize(qt.QSize(20, 20))
        self.placeShortVesselRulerButton.setFixedWidth(132)
        self.placeShortVesselRulerButton.setStyleSheet("font-weight:bold")
        self.buttonsToolboxLayout.addWidget(self.placeShortVesselRulerButton, 3, 1)

        self.removeButton = ctk.ctkPushButton()
        self.removeButton.text = "Remove ALL rulers"
        self.removeButton.toolTip = "Remove all the rulers for this volume"
        self.removeButton.setIcon(qt.QIcon("{0}/delete.png".format(SlicerUtil.CIP_ICON_DIR)))
        self.removeButton.setIconSize(qt.QSize(20, 20))
        self.removeButton.setFixedWidth(132)
        # self.buttonsToolboxLayout.addWidget(self.removeButton, 1, 1, 1, 2, 2)
        self.buttonsToolboxLayout.addWidget(self.removeButton, 1, 2)

        # Textboxes
        # self.longtextboxesFrame = qt.QFrame()
        # self.longtextboxesLayout = qt.QFormLayout()
        # self.longtextboxesFrame.setLayout(self.longtextboxesLayout)
        # self.longtextboxesFrame.setFixedWidth(190)
        # self.mainAreaLayout.addWidget(self.longtextboxesFrame, 3, 0)
        #
        # self.airwayLongTextBox = qt.QLineEdit()
        # self.airwayLongTextBox.setReadOnly(True)
        # self.longtextboxesLayout.addRow("Airway Long (mm):  ", self.airwayLongTextBox)
        #
        # self.vesselLongTextBox = qt.QLineEdit()
        # self.vesselLongTextBox.setReadOnly(True)
        # self.longtextboxesLayout.addRow("Vessel Long (mm):  ", self.vesselLongTextBox)
        #
        # self.ratioLongTextBox = qt.QLineEdit()
        # self.ratioLongTextBox.name = "ratioTextBox"
        # self.ratioLongTextBox.setReadOnly(True)
        # self.longtextboxesLayout.addRow("A/V Ratio Long: ", self.ratioLongTextBox)
        #
        # self.shorttextboxesFrame = qt.QFrame()
        # self.shorttextboxesLayout = qt.QFormLayout()
        # self.shorttextboxesFrame.setLayout(self.shorttextboxesLayout)
        # self.shorttextboxesFrame.setFixedWidth(190)
        # self.mainAreaLayout.addWidget(self.shorttextboxesFrame, 3, 1)
        #
        # self.airwayShortTextBox = qt.QLineEdit()
        # self.airwayShortTextBox.setReadOnly(True)
        # self.shorttextboxesLayout.addRow("Airway Short (mm):  ", self.airwayShortTextBox)
        #
        # self.vesselShortTextBox = qt.QLineEdit()
        # self.vesselShortTextBox.setReadOnly(True)
        # self.shorttextboxesLayout.addRow("Vessel Short (mm):  ", self.vesselShortTextBox)
        #
        # self.ratioShortTextBox = qt.QLineEdit()
        # self.ratioShortTextBox.name = "ratioTextBox"
        # self.ratioShortTextBox.setReadOnly(True)
        # self.shorttextboxesLayout.addRow("A/V Ratio Short: ", self.ratioShortTextBox)

        self.activateShortcutButton = ctk.ctkPushButton()
        self.activateShortcutButton.text = "Ctrl-X Shortcut"
        self.activateShortcutButton.toolTip = "Activate automatic rulers selection using the Ctrl-X shortcut " \
                                              "in this order: airway long, airway short, vessel long, vessel short. " \
                                              "Once all rulers are placed, a new Ctrl-X will save results and remove " \
                                              "the rulers. To deactivate the shortcut, press the button again."
        self.activateShortcutButton.setIcon(qt.QIcon("{0}/shortcut.png".format(SlicerUtil.CIP_ICON_DIR)))
        self.activateShortcutButton.setIconSize(qt.QSize(20, 20))
        self.activateShortcutButton.setCheckable(True)
        self.activateShortcutButton.setFixedWidth(120)
        self.buttonsToolboxLayout.addWidget(self.activateShortcutButton, 4, 2)

        self.meantextboxesFrame = qt.QFrame()
        self.meantextboxesLayout = qt.QFormLayout()
        self.meantextboxesFrame.setLayout(self.meantextboxesLayout)
        self.meantextboxesFrame.setFixedWidth(190)
        self.mainAreaLayout.addWidget(self.meantextboxesFrame, 3, 0)

        self.airwayMeanTextBox = qt.QLineEdit()
        self.airwayMeanTextBox.setReadOnly(True)
        self.meantextboxesLayout.addRow("Airway Mean (mm):  ", self.airwayMeanTextBox)

        self.vesselMeanTextBox = qt.QLineEdit()
        self.vesselMeanTextBox.setReadOnly(True)
        self.meantextboxesLayout.addRow("Vessel Mean (mm):  ", self.vesselMeanTextBox)

        self.ratioMeanTextBox = qt.QLineEdit()
        self.ratioMeanTextBox.name = "ratioTextBox"
        self.ratioMeanTextBox.setReadOnly(True)
        self.meantextboxesLayout.addRow("A/V Ratio Mean: ", self.ratioMeanTextBox)

        # Save case data
        self.reportsCollapsibleButton = ctk.ctkCollapsibleButton()
        self.reportsCollapsibleButton.text = "Reporting"
        self.layout.addWidget(self.reportsCollapsibleButton)
        self.reportsLayout = qt.QHBoxLayout(self.reportsCollapsibleButton)

        self.storedColumnNames = ["caseId", "airwayLongDiameterMm", "vesselLongDiameterMm", "avRatioLongMm",
                                  "airwayShortDiameterMm", "vesselShortDiameterMm", "avRatioShortMm",
                                  "airwayMeanDiameterMm", "vesselMeanDiameterMm", "AVRationMeanMm",
                                  "a1_long_r", "a1_long_a", "a1_long_s", "a2_long_r", "a2_long_a", "a2_long_s",
                                  "a1_short_r", "a1_short_a", "a1_short_s", "a2_short_r", "a2_short_a", "a2_short_s",
                                  "v1_long_r", "v1_long_a", "v1_long_s", "v2_long_r", "v2_long_a", "v2_long_s",
                                  "v1_short_r", "v1_short_a", "v1_short_s", "v2_short_r", "v2_short_a", "v2_short_s"]
        columns = CaseReportsWidget.getColumnKeysNormalizedDictionary(self.storedColumnNames)

        dbPath = os.path.join(SlicerUtil.getSettingsDataFolder(), "CIP_AVRatio.db")
        self.reportsWidget = CaseReportsWidget(self.moduleName, columns, parentWidget=self.reportsCollapsibleButton,
                                               dbFilePath=dbPath)
        self.reportsWidget.setup()
        # By default, the Print button is hidden
        self.reportsWidget.showPrintButton(True)

        # Init state
        self.resetModuleState()

        self.preventSavingState = False
        self.saveStateBeforeEnteringModule()
        self.preventSavingState = True

        self.switchToRedView() # By default the Red view is used

        #####
        # Case navigator
        if SlicerUtil.isSlicerACILLoaded():
            caseNavigatorAreaCollapsibleButton = ctk.ctkCollapsibleButton()
            caseNavigatorAreaCollapsibleButton.text = "Case navigator"
            self.layout.addWidget(caseNavigatorAreaCollapsibleButton, 0x0020)
            # caseNavigatorLayout = qt.QVBoxLayout(caseNavigatorAreaCollapsibleButton)

            # Add a case list navigator
            from ACIL.ui import CaseNavigatorWidget
            self.caseNavigatorWidget = CaseNavigatorWidget(self.moduleName, caseNavigatorAreaCollapsibleButton)
            self.caseNavigatorWidget.setup()

        self.layout.addStretch()

        # Connections
        self.observers = []
        self.zoomObserver = []

        self.volumeSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.onVolumeSelectorChanged)
        self.redViewButton.connect('clicked()', self.onRedViewButton)
        self.yellowViewButton.connect('clicked()', self.onYellowViewButton)
        self.greenViewButton.connect('clicked()', self.onGreenViewButton)

        self.btnBoth.connect('clicked()', self.onRadioButtonBoth)
        self.btnA.connect('clicked()', self.onRadioButtonAirway)
        self.btnV.connect('clicked()', self.onRadioButtonVessel)

        # self.placeRulersButton.connect('clicked()', self.onPlaceRulersClicked)
        self.placeLongAirwayRulerButton.connect('clicked()', self.onPlaceLongAirwayRulerClicked)
        self.placeShortAirwayRulerButton.connect('clicked()', self.onPlaceShortAirwayRulerClicked)
        self.placeLongVesselRulerButton.connect('clicked()', self.onPlaceLongVesselRulerClicked)
        self.placeShortVesselRulerButton.connect('clicked()', self.onPlaceShortVesselRulerClicked)
        self.removeButton.connect('clicked()', self.onRemoveRulerClicked)
        self.zoomToPlaceButton.connect('clicked()', self.onJumpToPlaceButtonClicked)
        self.zoomBackButton.connect('clicked()', self.onJumpBackButtonClicked)
        self.activateShortcutButton.connect('clicked()', self.onKeyShortcutClicked)

        self.reportsWidget.addObservable(self.reportsWidget.EVENT_SAVE_BUTTON_CLICKED, self.onSaveReport)
        self.reportsWidget.addObservable(self.reportsWidget.EVENT_PRINT_BUTTON_CLICKED, self.onPrintReportToPDF)

        # Init state
        self.resetModuleState()

        self.preventSavingState = False
        self.saveStateBeforeEnteringModule()
        self.preventSavingState = True

    def enter(self):
        """This is invoked every time that we select this module as the active module in Slicer
        (not only the first time)"""
        # Save state
        self.saveStateBeforeEnteringModule()

        # Start listening again to scene events
        self.__addSceneObservables__()

        volumeId = self.volumeSelector.currentNodeID
        if volumeId:
            SlicerUtil.displayBackgroundVolume(volumeId)

            SlicerUtil.changeLayout(3)
            SlicerUtil.centerAllVolumes()

            # Show the current rulers (if existing)
            self.logic.rulersVisible(volumeId, visible=True)

        SlicerUtil.changeLayoutToAxial()
        self.changeToDefaultContrastLevel()

    def exit(self):
        """This is invoked every time that we switch to another module (not only when Slicer is closed)."""
        # Stop listening to Scene events
        self.__removeSceneObservables()

        # Hide rulers
        if self.currentVolumeId:
            self.logic.rulersVisible(self.currentVolumeId, False)

        # Load previous state
        self.restoreStateBeforeExitingModule()

    def cleanup(self):
        """This is invoked as a destructor of the GUI when the module is no longer going to be used"""
        self.__removeSceneObservables()
        self.reportsWidget.cleanup()
        self.reportsWidget = None

    def saveStateBeforeEnteringModule(self):
        """Save the state of the module regarding labelmap, etc. This state will be saved/loaded when
        exiting/entering the module
        """
        if slicer.app.commandOptions().noMainWindow:
           return

        if self.preventSavingState:
            # Avoid that the first time that the module loads, the state is saved twice
            self.preventSavingState = False
            return

        # Save existing layout
        self.savedLayout = slicer.app.layoutManager().layout

        # Get the active volume (it it exists)
        activeVolumeId = SlicerUtil.getFirstActiveVolumeId()
        if activeVolumeId is None:
            # Reset state
            self.resetModuleState()
        else:
            # There is a Volume loaded. Save state
            try:
                self.savedVolumeID = activeVolumeId
                displayNode = SlicerUtil.getNode(activeVolumeId).GetDisplayNode()
                # self.savedContrastLevel = (displayNode.GetWindow(), displayNode.GetLevel())
                self.savedContrastLevel = (1500, -450)
            except:
                Util.print_last_exception()
                # Not action really needed
                pass

    def getInitialFOV(self):
        sliceNode = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeRed')
        return sliceNode.GetFieldOfView()

    def getInitialRAS(self):
        sliceWidget = self.getSliceWidget()
        width = sliceWidget.width
        height = sliceWidget.height

        centralXY = [int(width / 2.0), int(height / 2.0)]
        xyzw = [centralXY[0], centralXY[1], 0, 1]
        rasw = [0.0, 0.0, 0.0, 1.0]

        sliceNode = self.getSliceNode()
        sliceNode.GetXYToRAS().MultiplyPoint(xyzw, rasw)

        return rasw

    def onRadioButtonBoth(self):
        self.placeLongAirwayRulerButton.enabled = True
        self.placeShortAirwayRulerButton.enabled = True
        self.placeLongVesselRulerButton.enabled = True
        self.placeShortVesselRulerButton.enabled = True

    def onRadioButtonAirway(self):
        self.placeLongAirwayRulerButton.enabled = True
        self.placeShortAirwayRulerButton.enabled = True
        self.placeLongVesselRulerButton.enabled = False
        self.placeShortVesselRulerButton.enabled = False

    def onRadioButtonVessel(self):
        self.placeLongAirwayRulerButton.enabled = False
        self.placeShortAirwayRulerButton.enabled = False
        self.placeLongVesselRulerButton.enabled = True
        self.placeShortVesselRulerButton.enabled = True

    def restoreStateBeforeExitingModule(self):
        """Load the last state of the module when the user exited (labelmap, opacity, contrast window, etc.)
        """
        try:
            if self.savedVolumeID:
                # There is a previously saved valid state.
                SlicerUtil.setActiveVolumeIds(self.savedVolumeID)
                SlicerUtil.changeContrastWindow(self.savedContrastLevel[0], self.savedContrastLevel[1])

            # Restore layout
            SlicerUtil.changeLayout(self.savedLayout)
        except:
            Util.print_last_exception()
            pass

    def resetModuleState(self):
        """ Reset all the module state variables
        """
        self.savedVolumeID = None  # Active grayscale volume ID
        self.savedLabelmapID = None  # Active labelmap node ID
        self.savedLabelmapOpacity = None  # Labelmap opacity
        self.savedContrastLevel = (None, None)  # Contrast window/level that the user had when entering the module
        SlicerUtil.changeContrastWindow(1500, -450)

    def changeToDefaultContrastLevel(self):
        # Preferred contrast
        SlicerUtil.changeContrastWindow(1500, -450)

    def onDefaultLayoutButton(self):
        SlicerUtil.changeLayoutToFourUp()

    def onRedViewButton(self):
        SlicerUtil.changeLayoutToAxial()

    def onYellowViewButton(self):
        SlicerUtil.changeLayoutToSagittal()

    def onGreenViewButton(self):
        SlicerUtil.changeLayoutToCoronal()

    def createRulersNode(self):
        volumeId = self.volumeSelector.currentNodeID
        if volumeId == '':
            self.resetAVButtonsColor()
            self.showUnselectedVolumeWarningMessage()
            return

        self.logic.activateRulersListNode(volumeId, createIfNotExist=True)
        self.switchToRulerMode()

    def switchToRulerMode(self):
        applicationLogic = slicer.app.applicationLogic()
        selectionNode = applicationLogic.GetSelectionNode()
        selectionNode.SetReferenceActivePlaceNodeClassName("vtkMRMLAnnotationRulerNode")
        interactionNode = applicationLogic.GetInteractionNode()
        interactionNode.SwitchToSinglePlaceMode()

    def setRulersOptions(self, rulers_id, rulerType=-1, structureID=-1):
        self.logic.setRulersNameAndColor(rulerType, structureID, rulers_id)
        self.resetAVButtonsColor()

    def getCurrentSelectedStructure(self):
        """ Get the current selected structure id
        :return: self.logic.AIRWAY or self.logic.VESSEL
        """
        selectedStructureText = self.structuresButtonGroup.checkedButton().text
        if selectedStructureText == "Airway": return self.logic.AIRWAY
        elif selectedStructureText == "Vessel": return self.logic.VESSEL
        elif selectedStructureText == "Both": return self.logic.BOTH
        return self.logic.NONE

    def removeRulers(self):
        """ Remove all the rulers related to the current volume node
        :return:
        """
        self.logic.removeRulers(self.volumeSelector.currentNodeID)
        self.resetAVButtonsColor()
        self.refreshTextboxes(reset=True)
        self.rulers_ID = 0

    def refreshTextboxes(self, reset=False):
        """
         Update the information of the textboxes that give information about the measurements
        """
        self.airwayMeanTextBox.setText("0")
        self.vesselMeanTextBox.setText("0")
        self.ratioMeanTextBox.setText("0")
        self.ratioMeanTextBox.setStyleSheet(" QLineEdit { background-color: white; color: black}");

        volumeId = self.volumeSelector.currentNodeID

        # if volumeId:
        #     self.logic.changeActiveRulersColor(volumeId)

        meanAirwayDiameter = None
        meanVesselDiameter = None
        if not reset:
            # Airway
            longAirwayRuler, shortAirwayRuler = self.logic.getRulerNodesForStructure(self.logic.AIRWAY, self.rulers_ID)

            # Vessel
            longVesselRuler, shortVesselRuler = self.logic.getRulerNodesForStructure(self.logic.VESSEL, self.rulers_ID)

            if longAirwayRuler and shortAirwayRuler:
                longAirway = longAirwayRuler.GetDistanceMeasurement()
                shortAirway = shortAirwayRuler.GetDistanceMeasurement()
                meanAirwayDiameter = (longAirway + shortAirway) / 2.0
                meanAirwayDiameter = round(meanAirwayDiameter, 2)

                self.airwayMeanTextBox.setText(str(meanAirwayDiameter))
            if longVesselRuler and shortVesselRuler:
                longVessel = longVesselRuler.GetDistanceMeasurement()
                shortVessel = shortVesselRuler.GetDistanceMeasurement()
                meanVesselDiameter = (longVessel + shortVessel) / 2.0
                meanVesselDiameter = round(meanVesselDiameter, 2)

                self.vesselMeanTextBox.setText(str(meanVesselDiameter))
            if meanAirwayDiameter is not None and meanVesselDiameter is not None and meanVesselDiameter != 0:
                try:
                    ratio = meanAirwayDiameter / meanVesselDiameter
                    ratio = round(ratio, 2)
                    self.ratioMeanTextBox.setText(str(ratio))
                except Exception:
                    Util.print_last_exception()

    def showUnselectedVolumeWarningMessage(self):
        qt.QMessageBox.warning(slicer.util.mainWindow(), 'Select a volume',
                               'Please select a volume')

    def showUnselectedStructureWarningMessage(self):
        qt.QMessageBox.warning(slicer.util.mainWindow(), 'Review structure',
                               'Please select Airway, Vessel, or Both to place the right ruler/s')

    def switchToRedView(self):
        """ Switch the layout to Red slice only
        :return:
        """
        layoutManager = slicer.app.layoutManager()
        # Test the layout manager is not none in case the module is initialized without a main window
        # This happens for example in automatic tests
        if layoutManager is not None:
            SlicerUtil.changeLayoutToAxial()

    def zoomToSeed(self):
        """
        Dynamic zoom to the center of the current view in all the 2D windows
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

    def zoomBack(self):
        """
        Dynamic zoom to the center of the current view in all the 2D windows
        @return:
        """
        sliceNodes = slicer.util.getNodes('vtkMRMLSliceNode*')
        for sliceNode in list(sliceNodes.values()):
            sliceNode.SetFieldOfView(self.initialFOV[0], self.initialFOV[1], self.initialFOV[2])

        self.zoomed = False

    def __addSceneObservables__(self):
        self.observers.append(slicer.mrmlScene.AddObserver(slicer.vtkMRMLScene.NodeAddedEvent,
                                                           self.__onNodeAddedObserver__))
        self.observers.append(slicer.mrmlScene.AddObserver(slicer.vtkMRMLScene.EndCloseEvent, self.__onSceneClosed__))

    def __removeSceneObservables(self):
        for observer in self.observers:
            slicer.mrmlScene.RemoveObserver(observer)

    def nextRuler(self):
        if self.activeRuler is None:
            self.onPlaceLongAirwayRulerClicked()
        elif self.activeRuler == 'AL':
            self.onPlaceShortAirwayRulerClicked()
        elif self.activeRuler == 'AS':
            self.onPlaceLongVesselRulerClicked()
        elif self.activeRuler == 'VL':
            self.onPlaceShortVesselRulerClicked()
        elif self.activeRuler == 'VS':
            # self.onSaveReport()
            self.activeRuler = None
            self.onPlaceLongAirwayRulerClicked()

    def removeShortcutKeys(self):
        for shortcut in self.shortcuts:
            shortcut.disconnect('activated()')
            shortcut.setParent(None)
        self.shortcuts = []

    ##########
    # EVENTS #
    ##########
    def onVolumeSelectorChanged(self, node):
        logging.info("Volume selector node changed: {0}".format(
            '(None)' if node is None else node.GetName()
        ))
        # Preferred contrast
        SlicerUtil.centerAllVolumes()
        SlicerUtil.changeContrastWindow(1500, -450)
        self.refreshTextboxes()

    def onStructureClicked(self, button):
        fiducialsNode = self.getFiducialsNode(self.volumeSelector.currentNodeID)
        if fiducialsNode is not None:
            self.__addRuler__(button.text, self.volumeSelector.currentNodeID)

            markupsLogic = slicer.modules.markups.logic()
            markupsLogic.SetActiveListID(fiducialsNode)

            applicationLogic = slicer.app.applicationLogic()
            selectionNode = applicationLogic.GetSelectionNode()

            selectionNode.SetReferenceActivePlaceNodeClassName("vtkMRMLAnnotationRulerNode")
            interactionNode = applicationLogic.GetInteractionNode()
            interactionNode.SwitchToSinglePlaceMode()

    def onRulerUpdated(self, node, event):
        self.refreshTextboxes()

    def checkNode(self, nodeName):
        node = slicer.mrmlScene.GetNodesByName(nodeName).GetItemAsObject(0)
        if node:
            qt.QMessageBox.warning(slicer.util.mainWindow(), 'Remove ruler/s',
                                   'Please remove ruler/s before adding more of the same type')
            return False
        return True

    def resetAVButtonsColor(self):
        self.placeLongAirwayRulerButton.setStyleSheet("background-color: white; font-weight:bold")
        self.placeShortAirwayRulerButton.setStyleSheet("background-color: white; font-weight:bold")
        self.placeLongVesselRulerButton.setStyleSheet("background-color: white; font-weight:bold")
        self.placeShortVesselRulerButton.setStyleSheet("background-color: white; font-weight:bold")

    def onPlaceLongAirwayRulerClicked(self):
        self.removeZoomObserver()
        # self.refreshTextboxes()

        # if self.checkNode('AL'):
        self.resetAVButtonsColor()
        self.placeLongAirwayRulerButton.setStyleSheet("background-color: rgb(255,255,200); font-weight:bold")
        self.createRulersNode()
        self.rulerType = 0
        self.structureID = self.logic.AIRWAY

        self.activeRuler = 'AL'
        ruler_name = 'AL_{}'.format(str(self.rulers_ID))
        if slicer.mrmlScene.GetNodesByName(ruler_name).GetItemAsObject(0) is not None:
            self.rulers_ID += 1

    def onPlaceShortAirwayRulerClicked(self):
        self.removeZoomObserver()
        # self.refreshTextboxes()

        # if self.checkNode('AS'):
        self.resetAVButtonsColor()
        self.placeShortAirwayRulerButton.setStyleSheet("background-color: rgb(255,255,200); font-weight:bold")
        self.createRulersNode()
        self.rulerType = 1
        self.structureID = self.logic.AIRWAY
        self.activeRuler = 'AS'
        ruler_name = 'AS_{}'.format(str(self.rulers_ID))
        if slicer.mrmlScene.GetNodesByName(ruler_name).GetItemAsObject(0) is not None:
            self.rulers_ID += 1

    def onPlaceLongVesselRulerClicked(self):
        self.removeZoomObserver()
        # self.refreshTextboxes()

        # if self.checkNode('VL'):
        self.resetAVButtonsColor()
        self.placeLongVesselRulerButton.setStyleSheet("background-color: rgb(255,255,200); font-weight:bold")
        self.createRulersNode()
        self.rulerType = 2
        self.structureID = self.logic.VESSEL
        self.activeRuler = 'VL'
        ruler_name = 'VL_{}'.format(str(self.rulers_ID))
        if slicer.mrmlScene.GetNodesByName(ruler_name).GetItemAsObject(0) is not None:
            self.rulers_ID += 1

    def onPlaceShortVesselRulerClicked(self):
        self.removeZoomObserver()
        # self.refreshTextboxes()

        # if self.checkNode('VS'):
        self.resetAVButtonsColor()
        self.placeShortVesselRulerButton.setStyleSheet("background-color: rgb(255,255,200); font-weight:bold")
        self.createRulersNode()
        self.rulerType = 3
        self.structureID = self.logic.VESSEL
        self.activeRuler = 'VS'
        ruler_name = 'VS_{}'.format(str(self.rulers_ID))
        if slicer.mrmlScene.GetNodesByName(ruler_name).GetItemAsObject(0) is not None:
            self.rulers_ID += 1

    # def onMoveUpRulerClicked(self):
    #     self.stepSlice(1)
    #
    # def onMoveDownRulerClicked(self):
    #     self.stepSlice(-1)

    def onRemoveRulerClicked(self):
        if (qt.QMessageBox.question(slicer.util.mainWindow(), 'Remove rulers',
            'Are you sure you want to remove all the rulers from this volume?',
                                    qt.QMessageBox.Yes|qt.QMessageBox.No)) == qt.QMessageBox.Yes:
            self.removeRulers()
            self.refreshTextboxes()
            self.activeRuler = None

    def onKeyShortcutClicked(self):
        if self.activateShortcutButton.checked:
            self.shortcuts = []
            volumeId = self.volumeSelector.currentNodeID
            if volumeId == '':
                self.showUnselectedVolumeWarningMessage()
                self.activateShortcutButton.checked = False
                return

            Key_Ctrl = [0x04000000, 0x10000000]  # From QKeySequence enum. Note: On Mac OS X, the ControlModifier value
                                                 # corresponds to the Command keys on the Macintosh keyboard, and the
                                                 # MetaModifier value corresponds to the Control key
            Key_X = 0x58

            for key in Key_Ctrl:
                shortcut = qt.QShortcut(qt.QKeySequence(key+Key_X), slicer.util.mainWindow())
                shortcut.connect('activated()', self.nextRuler)
                self.shortcuts.append(shortcut)
        else:
            self.removeShortcutKeys()

    def onSaveReport(self):
        """ Save the current values in a persistent csv file
        :return:
        """
        volumeId = self.volumeSelector.currentNodeID
        if volumeId:
            caseName = slicer.mrmlScene.GetNodeByID(volumeId).GetName()
            coords = [0, 0, 0, 0]
            a1_long = a2_long = v1_long = v2_long = None
            a1_short = a2_short = v1_short = v2_short = None
            a1_mean = a2_mean = v1_mean = v2_mean = None

            airwayLongMm = airwayShortMm = vesselLongMm = vesselShortMm = 0

            avRatioLong = avRatioShort = avRationMean = 0

            # AIRWAY
            for rr in range(self.rulers_ID+1):
                longAirwayRuler, shortAirwayRuler = self.logic.getRulerNodesForStructure(self.logic.AIRWAY, rr)

                if longAirwayRuler and shortAirwayRuler:
                    airwayLongMm = round(longAirwayRuler.GetDistanceMeasurement(), 2)
                    airwayShortMm = round(shortAirwayRuler.GetDistanceMeasurement(), 2)

                    longAirwayRuler.GetPositionWorldCoordinates1(coords)
                    a1_long = list(coords)
                    longAirwayRuler.GetPositionWorldCoordinates2(coords)
                    a2_long = list(coords)

                    shortAirwayRuler.GetPositionWorldCoordinates1(coords)
                    a1_short = list(coords)
                    shortAirwayRuler.GetPositionWorldCoordinates2(coords)
                    a2_short = list(coords)

                    meanAirwayDiameter = (longAirwayRuler.GetDistanceMeasurement() +
                                          shortAirwayRuler.GetDistanceMeasurement()) / 2.0

                    meanAirwayDiameter = round(meanAirwayDiameter, 2)

                else:
                    meanAirwayDiameter = 0.0

                # VESSEL
                longVesselRuler, shortVesselRuler = self.logic.getRulerNodesForStructure(self.logic.VESSEL, rr)

                if longVesselRuler and shortVesselRuler:
                    vesselLongMm = round(longVesselRuler.GetDistanceMeasurement(), 2)
                    vesselShortMm = round(shortVesselRuler.GetDistanceMeasurement(), 2)

                    longVesselRuler.GetPositionWorldCoordinates1(coords)
                    v1_long = list(coords)
                    longVesselRuler.GetPositionWorldCoordinates2(coords)
                    v2_long = list(coords)

                    shortVesselRuler.GetPositionWorldCoordinates1(coords)
                    v1_short = list(coords)
                    shortVesselRuler.GetPositionWorldCoordinates2(coords)
                    v2_short = list(coords)

                    meanVesselDiameter = (longVesselRuler.GetDistanceMeasurement() +
                                          shortVesselRuler.GetDistanceMeasurement()) / 2.0

                    meanVesselDiameter = round(meanVesselDiameter, 2)
                else:
                    meanVesselDiameter = 0.0

                if airwayLongMm != 0 and vesselLongMm != 0:
                    avRatioLong = round(airwayLongMm / vesselLongMm, 2)
                if airwayShortMm != 0 and vesselShortMm != 0:
                    avRatioShort = round(airwayShortMm / vesselShortMm, 2)

                self.reportsWidget.insertRow(
                    caseId=caseName,
                    airwayLongDiameterMm=str(airwayLongMm),
                    vesselLongDiameterMm=str(vesselLongMm),
                    avRatioLongMm=str(avRatioLong),
                    airwayShortDiameterMm=str(airwayShortMm),
                    vesselShortDiameterMm=str(vesselShortMm),
                    avRatioShortMm=str(avRatioShort),
                    airwayMeanDiameterMm=str(meanAirwayDiameter),
                    vesselMeanDiameterMm=str(meanVesselDiameter),
                    AVRationMeanMm=self.ratioMeanTextBox.text,
                    a1_long_r=round(a1_long[0], 2) if a1_long is not None else '',
                    a1_long_a=round(a1_long[1], 2) if a1_long is not None else '',
                    a1_long_s=round(a1_long[2], 2) if a1_long is not None else '',
                    a2_long_r=round(a2_long[0], 2) if a2_long is not None else '',
                    a2_long_a=round(a2_long[1], 2) if a2_long is not None else '',
                    a2_long_s=round(a2_long[2], 2) if a2_long is not None else '',
                    a1_short_r=round(a1_short[0], 2) if a1_short is not None else '',
                    a1_short_a=round(a1_short[1], 2) if a1_short is not None else '',
                    a1_short_s=round(a1_short[2], 2) if a1_short is not None else '',
                    a2_short_r=round(a2_short[0], 2) if a2_short is not None else '',
                    a2_short_a=round(a2_short[1], 2) if a2_short is not None else '',
                    a2_short_s=round(a2_short[2], 2) if a2_short is not None else '',
                    v1_long_r=round(v1_long[0], 2) if v1_long is not None else '',
                    v1_long_a=round(v1_long[1], 2) if v1_long is not None else '',
                    v1_long_s=round(v1_long[2], 2) if v1_long is not None else '',
                    v2_long_r=round(v2_long[0], 2) if v2_long is not None else '',
                    v2_long_a=round(v2_long[1], 2) if v2_long is not None else '',
                    v2_long_s=round(v2_long[2], 2) if v2_long is not None else '',
                    v1_short_r=round(v1_short[0], 2) if v1_short is not None else '',
                    v1_short_a=round(v1_short[1], 2) if v1_short is not None else '',
                    v1_short_s=round(v1_short[2], 2) if v1_short is not None else '',
                    v2_short_r=round(v2_short[0], 2) if v2_short is not None else '',
                    v2_short_a=round(v2_short[1], 2) if v2_short is not None else '',
                    v2_short_s=round(v2_short[2], 2) if v2_short is not None else ''
                )
            qt.QMessageBox.information(slicer.util.mainWindow(), 'Data saved', 'The data were saved successfully')
            # self.removeRulers()
            self.activeRuler = None
        else:
            self.resetAVButtonsColor()
            self.showUnselectedVolumeWarningMessage()
            return

    def onPrintReportToPDF(self):
        """
        Print a pdf report
        """
        volumeId = self.volumeSelector.currentNodeID
        if volumeId:
            pdfReporter = PdfReporter()

            scalarVolumeNode = slicer.mrmlScene.GetNodeByID(volumeId)
            caseName = scalarVolumeNode.GetName()

            # Get the values that are going to be inserted in the html template
            values = dict()
            values["@@PATH_TO_STATIC@@"] = os.path.join(os.path.dirname(os.path.realpath(__file__)), "Resources/")
            values["@@SUBJECT@@"] = "Subject: " + str(caseName)
            values["@@SUMMARY@@"] = "Level of Bronchiectasis: "

            reportsWidgetLogic = self.reportsWidget.logic
            tableNode = reportsWidgetLogic.tableNode

            pdfRows = """"""
            for rr in range(tableNode.GetNumberOfRows()):
                if tableNode.GetCellText(rr, 0) == caseName:
                    dateCol = tableNode.GetNumberOfColumns() - 2
                    date = tableNode.GetCellText(rr, dateCol).split(' ')[0]
                    rasLocationAL = [float(tableNode.GetCellText(rr, 10)), float(tableNode.GetCellText(rr, 11)),
                                     float(tableNode.GetCellText(rr, 12))]
                    rasLocationAS = [float(tableNode.GetCellText(rr, 13)), float(tableNode.GetCellText(rr, 14)),
                                     float(tableNode.GetCellText(rr, 15))]

                    rasLocation = (np.asarray(rasLocationAL) + np.asarray(rasLocationAS)) / 2.0
                    rasLocation = rasLocation.tolist()

                    ijkCoords = self.RAStoIJK(scalarVolumeNode, rasLocation)
                    ijkLocation = str([int(ijkCoords[0]), int(ijkCoords[1]), int(ijkCoords[2])])

                    meanAirwayDiameter = float(tableNode.GetCellText(rr, 7))
                    meanVesselDiameter = float(tableNode.GetCellText(rr, 8))
                    meanRatio = float(tableNode.GetCellText(rr, 9))
                    # ratio = airwayDiameter / vesselDiameter

                    pdfRows += """<tr>
                      <td align="center">{} </td>
                      <td align="center">{} </td>
                      <td align="center">{:.2f} </td>
                      <td align="center">{:.2f} </td>
                      <td align="center">{:.2f} </td>
                    </tr>""".format(date, ijkLocation, meanAirwayDiameter, meanVesselDiameter, meanRatio)

            values["@@TABLE_ROWS@@"] = pdfRows

            # Get the path to the html template
            htmlTemplatePath = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                            "Resources/CIP_AVRatioReport.html")
            # Get a list of image absolute paths that may be needed for the report. In this case, we get the ACIL logo
            imagesFileList = [SlicerUtil.ACIL_LOGO_PATH]

            # Print the report. Remember that we can optionally specify the absolute path where the report is going to
            # be stored
            pdfReporter.printPdf(htmlTemplatePath, values, self.reportPrinted, imagesFileList=imagesFileList)
        else:
            self.resetAVButtonsColor()
            self.showUnselectedVolumeWarningMessage()
            return

    def reportPrinted(self, reportPath):
        Util.openFile(reportPath)

    def RAStoIJK(self, volumeNode, rasCoords):
        """ Transform a list of RAS coords in IJK for a volume
        :return: list of IJK coordinates
        """
        rastoijk = vtk.vtkMatrix4x4()
        volumeNode.GetRASToIJKMatrix(rastoijk)
        rasCoords.append(1.0)
        return list(rastoijk.MultiplyPoint(rasCoords))

    def getSliceWidget(self):
        activeWindow = self.getActiveWindow()
        lm = slicer.app.layoutManager()
        if activeWindow == self.AXIAL:
            sliceWidget = lm.sliceWidget('Red')
        elif activeWindow == self.SAGITTAL:
            sliceWidget = lm.sliceWidget('Yellow')
        else:
            sliceWidget = lm.sliceWidget('Green')

        return sliceWidget

    def getActiveWindow(self):
        lm = slicer.app.layoutManager()
        return lm.layout

    def removeZoomObserver(self):
        sliceWidget = self.getSliceWidget()
        style = sliceWidget.sliceView().interactorStyle().GetInteractor()
        for ii in range(len(self.zoomObserver)):
            style.RemoveObserver(self.zoomObserver[ii][1])

    def zoomToPosition(self, observee, event):
        if event == 'LeftButtonPressEvent' and not self.zoomed:
            self.initialRAS = self.getInitialRAS()
            sliceNode = self.getSliceNode()

            xy = self.interactor.GetLastEventPosition()
            xyzw = [xy[0], xy[1], 0, 1]
            rasw = [0.0, 0.0, 0.0, 1.0]

            sliceNode.GetXYToRAS().MultiplyPoint(xyzw, rasw)
            SlicerUtil.jumpToSeed(rasw)

            self.zoomToSeedTimer.start()
            self.removeZoomObserver()
            self.zoomed = True

    def getSliceNode(self):
        sliceNodes = slicer.util.getNodes('vtkMRMLSliceNode*')

        activeWindow = self.getActiveWindow()
        if activeWindow == self.AXIAL:
            sliceNode = sliceNodes['Red']
        elif activeWindow == self.SAGITTAL:
            sliceNode = sliceNodes['Yellow']
        else:
            sliceNode = sliceNodes['Green']

        return sliceNode

    def resetRulerMode(self):
        applicationLogic = slicer.app.applicationLogic()
        interactionNode = applicationLogic.GetInteractionNode()
        interactionNode.Reset(None)
        self.resetAVButtonsColor()
        self.activeRuler = None
        # if self.activeRuler == 'AL':
        #     self.onPlaceLongAirwayRulerClicked()
        # elif self.activeRuler == 'AS':
        #     self.onPlaceShortAirwayRulerClicked()
        # elif self.activeRuler == 'VL':
        #     self.onPlaceLongVesselRulerClicked()
        # elif self.activeRuler == 'VS':
        #     self.onPlaceShortVesselRulerClicked()

    def onJumpToPlaceButtonClicked(self):
        """
        Zoom to the area around the clicked point
        """
        self.resetRulerMode()
        sliceWidget = self.getSliceWidget()
        self.interactor = sliceWidget.sliceView().interactor()

        style = sliceWidget.sliceView().interactorStyle().GetInteractor()
        tag = style.AddObserver('LeftButtonPressEvent', self.zoomToPosition, 2)
        self.zoomObserver.append([style, tag])

    def onJumpBackButtonClicked(self):
        """
        Zoom to the area around the clicked point
        """
        self.zoomBack()
        SlicerUtil.jumpToSeed(self.initialRAS)
        self.removeZoomObserver()

    def __onSceneClosed__(self, arg1, arg2):
        """ Scene closed. Reset currently loaded volumes
        :param arg1:
        :param arg2:
        :return:
        """
        #self.logic.currentVolumesLoaded.clear()
        self.logic.currentActiveVolumeId = None


# CIP_AVRatioLogic
#
class CIP_AVRatioLogic(ScriptedLoadableModuleLogic):
    """This class should implement all the actual
    computation done by your module.    The interface
    should be such that other python code can import
    this class and make use of the functionality without
    requiring an instance of the Widget.
    Uses ScriptedLoadableModuleLogic base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    NONE = 0
    AIRWAY = 1
    VESSEL = 2
    BOTH = 3

    SLICEFACTOR = 0.6
    AXIAL = 6
    SAGITTAL = 7
    CORONAL = 8

    defaultColor = [0.3, 1.0, 0.0]
    defaultAirwayColor = [0.0, 0.0, 1.0]
    defaultVesselColor = [1.0, 0.0, 0.0]
    defaultWarningColor = [1.0, 1.0, 0.0]

    def __init__(self):
        self.currentActiveVolumeId = None
        # self.currentVolumesLoaded = set()

    def setRulersNameAndColor(self, rulerType, structureID, id_rulers):
        rulersNode = slicer.mrmlScene.GetNodesByClass('vtkMRMLAnnotationRulerNode')
        node = rulersNode.GetItemAsObject(rulersNode.GetNumberOfItems() - 1)
        if rulerType == 0:
            name = 'AL_{}'.format(str(id_rulers))
            node.SetName(name)
        elif rulerType == 1:
            name = 'AS_{}'.format(str(id_rulers))
            node.SetName(name)
        elif rulerType == 2:
            name = 'VL_{}'.format(str(id_rulers))
            node.SetName(name)
        elif rulerType == 3:
            name = 'VS_{}'.format(str(id_rulers))
            node.SetName(name)

        if structureID == self.AIRWAY:
            self.__changeColor__(node, self.defaultAirwayColor)
        elif structureID == self.VESSEL:
            self.__changeColor__(node, self.defaultVesselColor)

        textDisplayNode = node.GetAnnotationTextDisplayNode()
        textDisplayNode.SetOpacity(0.3)

    def getRootAnnotationsNode(self):
        """ Get the root annotations node global to the scene, creating it if necessary
        :return: "All Annotations" vtkMRMLAnnotationHierarchyNode
        """
        return SlicerUtil.getRootAnnotationsNode()

    def getRulersListNode(self, volumeId, createIfNotExist=True):
        """ Get the rulers node for this volume, creating it if it doesn't exist yet
        :param volumeId:
        :return: "volumeId_avRulersNode" vtkMRMLAnnotationHierarchyNode
        """
        # Search for the current volume hierarchy node (each volume has its own hierarchy)
        nodeName = volumeId + '_avRulersNode'
        rulersNode = SlicerUtil.getNode(nodeName)

        if rulersNode is None and createIfNotExist:
            # Create the node
            annotationsLogic = slicer.modules.annotations.logic()
            rootHierarchyNode = self.getRootAnnotationsNode()
            annotationsLogic.SetActiveHierarchyNodeID(rootHierarchyNode.GetID())
            annotationsLogic.AddHierarchy()
            n = rootHierarchyNode.GetNumberOfChildrenNodes()
            rulersNode = rootHierarchyNode.GetNthChildNode(n-1)
            # Rename the node
            rulersNode.SetName(nodeName)
            logging.debug("Created node " + nodeName + " (general rulers node for this volume")

        # Return the node
        return rulersNode

    def activateRulersListNode(self, volumeId, createIfNotExist=True):
        nodeName = volumeId + '_avRulersNode'
        rulersNode = SlicerUtil.getNode(nodeName)

        annotationsLogic = slicer.modules.annotations.logic()

        if rulersNode is None and createIfNotExist:
            # Create the node
            rootHierarchyNode = self.getRootAnnotationsNode()
            annotationsLogic.SetActiveHierarchyNodeID(rootHierarchyNode.GetID())
            annotationsLogic.AddHierarchy()
            n = rootHierarchyNode.GetNumberOfChildrenNodes()
            rulersNode = rootHierarchyNode.GetNthChildNode(n - 1)
            # Rename the node
            rulersNode.SetName(nodeName)
            logging.debug("Created node " + nodeName + " (general rulers node for this volume")
        elif rulersNode is not None:
            annotationsLogic.SetActiveHierarchyNodeID(rulersNode.GetID())

    def getRulerNodesForStructure(self, structureId, ruler_id):
        """ Search for the right ruler node to be created based on the volume and the selected
        structure (Airway or Vessel).
        It also creates the necessary node hierarchy if it doesn't exist.
        :param structureId: Airway (1), Vessel (2)
        :return:
        """
        if structureId == self.AIRWAY:  # Airway
            longNodeName = 'AL_{}'.format(str(ruler_id))
            shortNodeName = 'AS_{}'.format(str(ruler_id))
        elif structureId == self.VESSEL:  # Vessel:
            longNodeName = 'VL_{}'.format(str(ruler_id))
            shortNodeName = 'VS_{}'.format(str(ruler_id))
        else:
            return None, None

        longNode = slicer.mrmlScene.GetNodesByName(longNodeName).GetItemAsObject(0)
        shortNode = slicer.mrmlScene.GetNodesByName(shortNodeName).GetItemAsObject(0)

        return longNode, shortNode

    def hideAllRulers(self):
        """
        Hide all the current rulers in the scene
        :return:
        """
        nodes = slicer.mrmlScene.GetNodesByClass("vtkMRMLAnnotationRulerNode")
        for i in range(nodes.GetNumberOfItems()):
            nodes.GetItemAsObject(i).SetDisplayVisibility(False)

    def rulersVisible(self, volumeId, visible):
        """ Show or hide all the ruler nodes
        """
        if volumeId is not None:
            rulersListNode = self.getRulersListNode(volumeId, False)
            if rulersListNode:
                for i in range(rulersListNode.GetNumberOfChildrenNodes()):
                    nodeWrapper = rulersListNode.GetNthChildNode(i)
                    # nodeWrapper is also a HierarchyNode. We need to look for its only child that will be the rulerNode
                    col = vtk.vtkCollection()
                    nodeWrapper.GetChildrenDisplayableNodes(col)
                    rulerNode = col.GetItemAsObject(0)
                    rulerNode.SetDisplayVisibility(visible)

    def __changeColor__(self, node, color):
        for i in range(3):
            n = node.GetNthDisplayNode(i)
            if n:
                n.SetColor(color)

        layoutManager = slicer.app.layoutManager()
        # Test the layout manager is not none in case the module is initialized without a main window
        # This happens for example in automatic tests
        if layoutManager is not None:
            # Refresh UI to repaint both rulers. Is this the best way? Who knows...
            activeWindow = layoutManager.layout
            if activeWindow == self.AXIAL:
                layoutManager.sliceWidget('Red').sliceView().mrmlSliceNode().Modified()
            elif activeWindow == self.SAGITTAL:
                layoutManager.sliceWidget('Yellow').sliceView().mrmlSliceNode().Modified()
            else:
                layoutManager.sliceWidget('Green').sliceView().mrmlSliceNode().Modified()

    def changeActiveRulersColor(self, volumeId):
        """ Change the color for all the rulers in this volume
        :param volumeId:
        :param color:
        :return:
        """
        for structureId, color in zip([self.AIRWAY, self.VESSEL], [self.defaultAirwayColor, self.defaultVesselColor]):
            node, new = self.getRulerNodeForVolumeAndStructure(volumeId, structureId, createIfNotExist=False)
            if node:
                self.__changeColor__(node, color)

    def removeRulers(self, volumeId):
        """ Remove all the rulers for the selected volume
        :param volumeId:
        :param structureId:
        """
        #rulerNode, newNode = self.getRulerNodeForVolumeAndStructure(volumeId, structureId)
        rulersListNode = self.getRulersListNode(volumeId, createIfNotExist=False)
        if rulersListNode:
            rulersListNode.RemoveAllChildrenNodes()
            slicer.mrmlScene.RemoveNode(rulersListNode)

    def RAStoIJK(self, volumeNode, rasCoords):
        """ Transform a list of RAS coords in IJK for a volume
        :return: list of IJK coordinates
        """
        rastoijk=vtk.vtkMatrix4x4()
        volumeNode.GetRASToIJKMatrix(rastoijk)
        rasCoords.append(1)
        return list(rastoijk.MultiplyPoint(rasCoords))

    def IJKtoRAS(self, volumeNode, ijkCoords):
        """ Transform a list of IJK coords in RAS for a volume
        :return: list of RAS coordinates
        """
        ijktoras=vtk.vtkMatrix4x4()
        volumeNode.GetIJKToRASMatrix(ijktoras)
        ijkCoords.append(1)
        return list(ijktoras.MultiplyPoint(ijkCoords))


class CIP_AVRatioTest(ScriptedLoadableModuleTest):
    @classmethod
    def setUpClass(cls):
        """ Executed once for all the tests """
        slicer.util.selectModule('CIP_AVRatio')

    def setUp(self):
        """ Do whatever is needed to reset the state - typically a scene clear will be enough.
        """
        slicer.mrmlScene.Clear(0)

    def runTest(self):
        """Run as few or as many tests as needed here.
        """
        self.setUp()
        self.test_CIP_AVRatio()

    def test_CIP_AVRatio(self):
        self.assertIsNotNone(slicer.modules.cip_avratio)

        # Get the widget
        widget = slicer.modules.cip_avratio.widgetRepresentation()
        volume = SlicerUtil.downloadVolumeForTests(widget=widget)

        self.assertFalse(volume is None)

        # Get the logic
        logging.info("Getting logic...")
        logic = widget.self().logic

        # Actions
        # Make sure that the right volume is selected
        volumeSelector = SlicerUtil.findChildren(widget=widget, name='av_volumeSelector')[0]
        volumeSelector.setCurrentNode(volume)

        # XXX To be implemented
        self.delayDisplay('Test passed!')
