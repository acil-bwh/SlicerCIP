# -*- coding: utf-8 -*-
import logging
from collections import OrderedDict

import os
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
        self.parent.contributors = ["Jorge Onieva (jonieva@bwh.harvard.edu)", "Applied Chest Imaging Laboratory", "Brigham and Women's Hospital"]
        self.parent.helpText = """Calculate the ratio between pulmonary arterial and aorta.<br>
            A quick tutorial of the module can be found <a href='https://s3.amazonaws.com/acil-public/SlicerCIP+Tutorials/PAA_Ratio.pptx'>here</a>.<br><br>
            The AV Ratio biomarker has been proved to predict acute exacerbations of COPD (Wells, J. M., Washko, G. R.,
            Han, M. K., Abbas, N., Nath, H., Mamary, a. J., Dransfield, M. T. (2012).
            Pulmonary Arterial Enlargement and Acute Exacerbations of COPD. New England Journal of Medicine, 367(10), 913-921).
            For more information refer to: <a href='http://www.nejm.org/doi/full/10.1056/NEJMoa1203830'>http://www.nejm.org/doi/full/10.1056/NEJMoa1203830</a>"""
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
    def moduleName(self):
        return os.path.basename(__file__).replace(".py", "")

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

        self.__onNodeAddedObserver__ = partial(__onNodeAddedObserver__, self)
        self.__onNodeAddedObserver__.CallDataType = vtk.VTK_OBJECT

        # Timer for dynamic zooming
        self.zoomToSeedTimer = qt.QTimer()
        self.zoomToSeedTimer.setInterval(100)
        self.zoomToSeedTimer.timeout.connect(self.zoomToSeed)

        self.interactor = None
        self.initialFOV = [0.0, 0.0, 0.0]
        self.initialRAS = [0.0, 0.0, 0.0]

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
        self.mainAreaLayout.addWidget(self.structuresGroupbox, 2, 0)

        self.structuresButtonGroup=qt.QButtonGroup()

        btn = qt.QRadioButton("Both")
        btn.name = "avButton"
        btn.checked = True

        self.structuresButtonGroup.addButton(btn, 0)
        self.groupboxLayout.addWidget(btn)

        btn = qt.QRadioButton("Airway")
        btn.name = "airwayRadioButton"
        self.structuresButtonGroup.addButton(btn, 1)
        self.groupboxLayout.addWidget(btn)

        btn = qt.QRadioButton("Vessel")
        btn.name = "vesselRadioButton"
        self.structuresButtonGroup.addButton(btn, 2)
        self.groupboxLayout.addWidget(btn)

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

        self.placeRulersButton = ctk.ctkPushButton()
        self.placeRulersButton.text = "Place ruler/s"
        self.placeRulersButton.name = "placeRulersButton"
        self.placeRulersButton.toolTip = "Place the ruler/s for the selected structure/s in the current slice"
        self.placeRulersButton.setIcon(qt.QIcon("{0}/ruler.png".format(SlicerUtil.CIP_ICON_DIR)))
        self.placeRulersButton.setIconSize(qt.QSize(20, 20))
        self.placeRulersButton.setFixedWidth(105)
        self.placeRulersButton.setStyleSheet("font-weight:bold")
        self.buttonsToolboxLayout.addWidget(self.placeRulersButton, 1, 0)

        self.removeButton = ctk.ctkPushButton()
        self.removeButton.text = "Remove ALL rulers"
        self.removeButton.toolTip = "Remove all the rulers for this volume"
        self.removeButton.setIcon(qt.QIcon("{0}/delete.png".format(SlicerUtil.CIP_ICON_DIR)))
        self.removeButton.setIconSize(qt.QSize(20, 20))
        self.buttonsToolboxLayout.addWidget(self.removeButton, 1, 1, 1, 2, 2)


        ### Textboxes
        self.textboxesFrame = qt.QFrame()
        self.textboxesLayout = qt.QFormLayout()
        self.textboxesFrame.setLayout(self.textboxesLayout)
        self.textboxesFrame.setFixedWidth(190)
        self.mainAreaLayout.addWidget(self.textboxesFrame, 3, 0)

        self.airwayTextBox = qt.QLineEdit()
        self.airwayTextBox.setReadOnly(True)
        self.textboxesLayout.addRow("Airway (mm):  ", self.airwayTextBox)

        self.vesselTextBox = qt.QLineEdit()
        self.vesselTextBox.setReadOnly(True)
        self.textboxesLayout.addRow("Vessel (mm):  ", self.vesselTextBox)

        self.ratioTextBox = qt.QLineEdit()
        self.ratioTextBox.name = "ratioTextBox"
        self.ratioTextBox.setReadOnly(True)
        self.textboxesLayout.addRow("A/V Ratio: ", self.ratioTextBox)

        # Save case data
        self.reportsCollapsibleButton = ctk.ctkCollapsibleButton()
        self.reportsCollapsibleButton.text = "Reporting"
        self.layout.addWidget(self.reportsCollapsibleButton)
        self.reportsLayout = qt.QHBoxLayout(self.reportsCollapsibleButton)

        self.storedColumnNames = ["caseId", "airwayDiameterMm", "vesselDiameterMm", "AVRationMm",
                                  "a1r", "a1a", "a1s", "a2r", "a2a", "a2s",
                                  "v1r", "v1a", "v1s", "v2r", "v2a", "v2s"]
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
        # self.defaultButton.connect('clicked()', self.onDefaultLayoutButton)
        self.redViewButton.connect('clicked()', self.onRedViewButton)
        self.yellowViewButton.connect('clicked()', self.onYellowViewButton)
        self.greenViewButton.connect('clicked()', self.onGreenViewButton)
        self.placeRulersButton.connect('clicked()', self.onPlaceRulersClicked)
        # self.moveUpButton.connect('clicked()', self.onMoveUpRulerClicked)
        # self.moveDownButton.connect('clicked()', self.onMoveDownRulerClicked)
        self.removeButton.connect('clicked()', self.onRemoveRulerClicked)
        self.zoomToPlaceButton.connect('clicked()', self.onJumpToPlaceButtonClicked)
        self.zoomBackButton.connect('clicked()', self.onJumpBackButtonClicked)

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

    def saveStateBeforeEnteringModule(self):
        """Save the state of the module regarding labelmap, etc. This state will be saved/loaded when
        exiting/entering the module
        """
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
                displayNode = slicer.util.getNode(activeVolumeId).GetDisplayNode()
                self.savedContrastLevel = (displayNode.GetWindow(), displayNode.GetLevel())
            except:
                Util.print_last_exception()
                # Not action really needed
                pass

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
        SlicerUtil.changeContrastWindow(1400, -500)

    def changeToDefaultContrastLevel(self):
        # Preferred contrast
        SlicerUtil.changeContrastWindow(1400, -500)

    def onDefaultLayoutButton(self):
        SlicerUtil.changeLayoutToFourUp()

    def onRedViewButton(self):
        SlicerUtil.changeLayoutToAxial()

    def onYellowViewButton(self):
        SlicerUtil.changeLayoutToSagittal()

    def onGreenViewButton(self):
        SlicerUtil.changeLayoutToCoronal()

    def placeRuler(self):
        """ Place one or the two rulers in the current visible slice in active view node
        """
        volumeId = self.volumeSelector.currentNodeID
        if volumeId == '':
            self.showUnselectedVolumeWarningMessage()
            return

        selectedStructure = self.getCurrentSelectedStructure()
        if selectedStructure == self.logic.NONE:
            qt.QMessageBox.warning(slicer.util.mainWindow(), 'Review structure',
                                   'Please select Airway, Vessel or Both to place the ruler/s')
            return

        # Get the current slice
        currentSlice = self.getCurrentActiveWindowSlice()

        if selectedStructure == self.logic.BOTH:
            structures = [self.logic.AIRWAY, self.logic.VESSEL]
        else:
            structures = [selectedStructure]

        for structure in structures:
            self.logic.placeRulerInSlice(volumeId, structure, currentSlice, self.onRulerUpdated)

        self.refreshTextboxes()

    def getCurrentSelectedStructure(self):
        """ Get the current selected structure id
        :return: self.logic.AIRWAY or self.logic.VESSEL
        """
        selectedStructureText = self.structuresButtonGroup.checkedButton().text
        if selectedStructureText == "Airway": return self.logic.AIRWAY
        elif selectedStructureText == "Vessel": return self.logic.VESSEL
        elif selectedStructureText == "Both": return self.logic.BOTH
        return self.logic.NONE

    def stepSlice(self, offset):
        """ Move the selected structure one slice up or down
        :param offset: +1 or -1
        :return:
        """
        volumeId = self.volumeSelector.currentNodeID

        if volumeId == '':
            self.showUnselectedVolumeWarningMessage()
            return

        selectedStructure = self.getCurrentSelectedStructure()
        if selectedStructure == self.logic.NONE:
            self.showUnselectedStructureWarningMessage()
            return

        if selectedStructure == self.logic.BOTH:
            # Move both rulers
            self.logic.stepSlice(volumeId, self.logic.AIRWAY, offset)
            newSlice = self.logic.stepSlice(volumeId, self.logic.VESSEL, offset)
        else:
            newSlice = self.logic.stepSlice(volumeId, selectedStructure, offset)

        self.moveActiveWindowToSlice(newSlice)

    def removeRulers(self):
        """ Remove all the rulers related to the current volume node
        :return:
        """
        self.logic.removeRulers(self.volumeSelector.currentNodeID)
        self.refreshTextboxes(reset=True)

    def getCurrentActiveWindowSlice(self):
        """ Get the current slice (in RAS) of the Red window
        :return:
        """
        layoutManager = slicer.app.layoutManager()
        activeWindow = layoutManager.layout
        if activeWindow == self.AXIAL:
            nodeSliceNode = layoutManager.sliceWidget('Red').sliceLogic().GetSliceNode()
        elif activeWindow == self.SAGITTAL:
            nodeSliceNode = layoutManager.sliceWidget('Yellow').sliceLogic().GetSliceNode()
        else:
            nodeSliceNode = layoutManager.sliceWidget('Green').sliceLogic().GetSliceNode()

        return nodeSliceNode.GetSliceOffset()

    def moveActiveWindowToSlice(self, newSlice):
        """ Moves the red display to the specified RAS slice
        :param newSlice: slice to jump (RAS format)
        :return:
        """
        layoutManager = slicer.app.layoutManager()
        activeWindow = layoutManager.layout
        if activeWindow == self.AXIAL:
            nodeSliceNode = layoutManager.sliceWidget('Red').sliceLogic().GetSliceNode()
            nodeSliceNode.JumpSlice(0,0,newSlice)
        elif activeWindow == self.SAGITTAL:
            nodeSliceNode = layoutManager.sliceWidget('Yellow').sliceLogic().GetSliceNode()
            nodeSliceNode.JumpSlice(newSlice, 0, 0)
        else:
            nodeSliceNode = layoutManager.sliceWidget('Green').sliceLogic().GetSliceNode()
            nodeSliceNode.JumpSlice(0, newSlice, 0)

    def refreshTextboxes(self, reset=False):
        """ Update the information of the textboxes that give information about the measurements
        """
        self.airwayTextBox.setText("0")
        self.vesselTextBox.setText("0")
        self.ratioTextBox.setText("0")
        self.ratioTextBox.setStyleSheet(" QLineEdit { background-color: white; color: black}");

        volumeId = self.volumeSelector.currentNodeID

        if volumeId:
            self.logic.changeActiveRulersColor(volumeId)

        airway = None
        vessel = None
        if not reset:
            rulerAirway, newAirway = self.logic.getRulerNodeForVolumeAndStructure(self.volumeSelector.currentNodeID,
                                                                                  self.logic.AIRWAY,
                                                                                  createIfNotExist=False)
            rulerVessel, newVessel = self.logic.getRulerNodeForVolumeAndStructure(self.volumeSelector.currentNodeID,
                                                                                  self.logic.VESSEL,
                                                                                  createIfNotExist=False)
            if rulerAirway:
                airway = rulerAirway.GetDistanceMeasurement()

                self.airwayTextBox.setText(str(airway))
            if rulerVessel:
                vessel = rulerVessel.GetDistanceMeasurement()
                self.vesselTextBox.setText(str(vessel))
            if airway is not None and vessel is not None and vessel != 0:
                try:
                    ratio = airway / vessel
                    self.ratioTextBox.setText(str(ratio))
                    # if ratio > 1.0:
                    # ratio > 1.0 means bronchiectasis
                    #     # Switch colors ("alarm")
                    #     st = " QLineEdit {{ background-color: rgb({0}, {1}, {2}); color: white }}". \
                    #                                     format(int(self.logic.defaultWarningColor[0]*255),
                    #                                            int(self.logic.defaultWarningColor[1]*255),
                    #                                            int(self.logic.defaultWarningColor[2]*255))
                    #     self.ratioTextBox.setStyleSheet(st)
                    #     self.logic.changeActiveRulersColor(volumeId, self.logic.defaultWarningColor)
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
        for sliceNode in sliceNodes.values():
            sliceNode.SetFieldOfView(self.initialFOV[0], self.initialFOV[1], self.initialFOV[2])


    def __addSceneObservables__(self):
        self.observers.append(slicer.mrmlScene.AddObserver(slicer.vtkMRMLScene.NodeAddedEvent,
                                                           self.__onNodeAddedObserver__))
        self.observers.append(slicer.mrmlScene.AddObserver(slicer.vtkMRMLScene.EndCloseEvent, self.__onSceneClosed__))

    def __removeSceneObservables(self):
        for observer in self.observers:
            slicer.mrmlScene.RemoveObserver(observer)

    #########
    # EVENTS
    def onVolumeSelectorChanged(self, node):
        logging.info("Volume selector node changed: {0}".format(
            '(None)' if node is None else node.GetName()
        ))
        # Preferred contrast
        SlicerUtil.centerAllVolumes()
        SlicerUtil.changeContrastWindow(1400, -500)
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

    def onPlaceRulersClicked(self):
        self.removeZoomObserver()
        self.placeRuler()

    def onMoveUpRulerClicked(self):
        self.stepSlice(1)

    def onMoveDownRulerClicked(self):
        self.stepSlice(-1)

    def onRemoveRulerClicked(self):
        if (qt.QMessageBox.question(slicer.util.mainWindow(), 'Remove rulers',
            'Are you sure you want to remove all the rulers from this volume?',
                                    qt.QMessageBox.Yes|qt.QMessageBox.No)) == qt.QMessageBox.Yes:
            self.logic.removeRulers(self.volumeSelector.currentNodeID)
            self.refreshTextboxes()

    def onSaveReport(self):
        """ Save the current values in a persistent csv file
        :return:
        """
        volumeId = self.volumeSelector.currentNodeID
        if volumeId:
            caseName = slicer.mrmlScene.GetNodeByID(volumeId).GetName()
            coords = [0, 0, 0, 0]
            a1 = a2 = v1 = v2 = None

            # AIRWAY
            rulerNode, newNode = self.logic.getRulerNodeForVolumeAndStructure(volumeId, self.logic.AIRWAY,
                                                                              createIfNotExist=False)
            if rulerNode:
                # Get current RAS coords
                rulerNode.GetPositionWorldCoordinates1(coords)
                a1 = list(coords)
                rulerNode.GetPositionWorldCoordinates2(coords)
                a2 = list(coords)

            # VESSEL
            rulerNode, newNode = self.logic.getRulerNodeForVolumeAndStructure(volumeId, self.logic.VESSEL,
                                                                              createIfNotExist=False)
            if rulerNode:
                rulerNode.GetPositionWorldCoordinates1(coords)
                v1 = list(coords)
                rulerNode.GetPositionWorldCoordinates2(coords)
                v2 = list(coords)

            self.reportsWidget.insertRow(
                caseId=caseName,
                airwayDiameterMm=self.airwayTextBox.text,
                vesselDiameterMm=self.vesselTextBox.text,
                AVRationMm=self.ratioTextBox.text,
                a1r=a1[0] if a1 is not None else '',
                a1a=a1[1] if a1 is not None else '',
                a1s=a1[2] if a1 is not None else '',
                a2r=a2[0] if a2 is not None else '',
                a2a=a2[1] if a2 is not None else '',
                a2s=a2[2] if a2 is not None else '',
                v1r=v1[0] if v1 is not None else '',
                v1a=v1[1] if v1 is not None else '',
                v1s=v1[2] if v1 is not None else '',
                v2r=v2[0] if v2 is not None else '',
                v2a=v2[1] if v2 is not None else '',
                v2s=v2[2] if v2 is not None else ''
            )
            qt.QMessageBox.information(slicer.util.mainWindow(), 'Data saved', 'The data were saved successfully')
        else:
            self.showUnselectedVolumeWarningMessage()
            return

    def onPrintReportToPDF(self):
        """
        Print a pdf report
        """
        import time
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
                    date = tableNode.GetCellText(rr, 15).split(' ')[0]
                    rasLocation = [float(tableNode.GetCellText(rr, 3)), float(tableNode.GetCellText(rr, 4)),
                                   float(tableNode.GetCellText(rr, 5))]

                    ijkCoords = self.RAStoIJK(scalarVolumeNode, rasLocation)
                    ijkLocation = str([int(ijkCoords[0]), int(ijkCoords[1]), int(ijkCoords[2])])

                    airwayDiameter = float(tableNode.GetCellText(rr, 1))
                    vesselDiameter = float(tableNode.GetCellText(rr, 2))
                    ratio = airwayDiameter / vesselDiameter

                    pdfRows += """<tr>
                      <td align="center">{} </td>
                      <td align="center">{} </td>
                      <td align="center">{:.2f} </td>
                      <td align="center">{:.2f} </td>
                      <td align="center">{:.2f} </td>
                    </tr>""".format(date, ijkLocation, airwayDiameter, vesselDiameter, ratio)

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
        if event == 'LeftButtonPressEvent':
            sliceNode = self.getSliceNode()

            xy = self.interactor.GetLastEventPosition()
            xyzw = [xy[0], xy[1], 0, 1]
            rasw = [0.0, 0.0, 0.0, 1.0]

            sliceNode.GetXYToRAS().MultiplyPoint(xyzw, rasw)
            SlicerUtil.jumpToSeed(rasw)

            self.zoomToSeedTimer.start()
            self.removeZoomObserver()

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

    def onJumpToPlaceButtonClicked(self):
        """
        Zoom to the area around the clicked point
        """
        sliceNode = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeRed')
        self.initialFOV = sliceNode.GetFieldOfView()
        self.initialRAS = self.getInitialRAS()
        sliceWidget = self.getSliceWidget()

        self.interactor = sliceWidget.sliceView().interactor()

        style = sliceWidget.sliceView().interactorStyle().GetInteractor()
        tag = style.AddObserver('LeftButtonPressEvent', self.zoomToPosition, 2)
        self.zoomObserver.append([style, tag])

    def onJumpBackButtonClicked(self):
        """
        Zoom to the area around the clicked point
        """
        # self.zoomBackTimer.start()
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

    # Default XY coordinates for Aorta and PA (the Z will be estimated depending on the number of slices)
    # defaultAorta1 = [220, 170, 0]
    # defaultAorta2 = [275, 175, 0]
    # defaultPA1 = [280, 175, 0]
    # defaultPA2 = [320, 190, 0]

    defaultColor = [0.3, 1.0, 0.0]
    defaultAirwayColor = [0.0, 0.0, 1.0]
    defaultVesselColor = [1.0, 0.0, 0.0]
    defaultWarningColor = [1.0, 1.0, 0.0]

    def __init__(self):
        self.currentActiveVolumeId = None
        # self.currentVolumesLoaded = set()

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
        rulersNode = slicer.util.getNode(nodeName)

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

    def getRulerNodeForVolumeAndStructure(self, volumeId, structureId, createIfNotExist=True,
                                          callbackWhenRulerModified=None):
        """ Search for the right ruler node to be created based on the volume and the selected
        structure (Airway or Vessel).
        It also creates the necessary node hierarchy if it doesn't exist.
        :param volumeId:
        :param structureId: Airway (1), Vessel (2)
        :param createIfNotExist: create the ruler node if it doesn't exist yet
        :param callbackWhenRulerModified: function to call when the ruler node is modified
        :return: node and a boolean indicating if the node has been created now
        """
        isNewNode = False
        if structureId == self.AIRWAY:  # Airway
            nodeName = "A"
        elif structureId == self.VESSEL:  # Vessel:
            nodeName = "V"
        else:
            return None, isNewNode

        # Get the node that contains all the rulers for this volume
        rulersListNode = self.getRulersListNode(volumeId, createIfNotExist=createIfNotExist)
        node = None
        if rulersListNode:
            # Search for the node
            for i in range(rulersListNode.GetNumberOfChildrenNodes()):
                nodeWrapper = rulersListNode.GetNthChildNode(i)
                # nodeWrapper is also a HierarchyNode. We need to look for its only child that will be the rulerNode
                col = vtk.vtkCollection()
                nodeWrapper.GetChildrenDisplayableNodes(col)
                rulerNode = col.GetItemAsObject(0)

                if rulerNode.GetName() == nodeName:
                    node = rulerNode
                    break

            if node is None and createIfNotExist:
                # Create the node
                # Set the active node, so that the new ruler is a child node
                annotationsLogic = slicer.modules.annotations.logic()
                annotationsLogic.SetActiveHierarchyNodeID(rulersListNode.GetID())
                node = slicer.mrmlScene.CreateNodeByClass('vtkMRMLAnnotationRulerNode')
                node.SetName(nodeName)
                if structureId == self.AIRWAY:
                    self.__changeColor__(node, self.defaultAirwayColor)
                elif structureId == self.VESSEL:
                    self.__changeColor__(node, self.defaultVesselColor)

                slicer.mrmlScene.AddNode(node)
                isNewNode = True
                node.AddObserver(vtk.vtkCommand.ModifiedEvent, callbackWhenRulerModified)
                logging.debug("Created node " + nodeName + " for volume " + volumeId)

        return node, isNewNode

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

    def stepSlice(self, volumeId, structureId, sliceStep):
        """ Move the selected ruler up or down one slice.
        :param volumeId:
        :param structureId:
        :param sliceStep: +1 or -1
        :return: new slice in RAS format
        """
        # Calculate the RAS coords of the slice where we should jump to
        rulerNode, newNode = self.getRulerNodeForVolumeAndStructure(volumeId, structureId, createIfNotExist=False)
        if not rulerNode:
            # The ruler has not been created. This op doesn't make sense
            return False

        coords = [0, 0, 0, 1.0]
        # Get current RAS coords
        rulerNode.GetPositionWorldCoordinates1(coords)

        # Get the transformation matrixes
        rastoijk = vtk.vtkMatrix4x4()
        ijktoras = vtk.vtkMatrix4x4()
        scalarVolumeNode = slicer.mrmlScene.GetNodeByID(volumeId)
        scalarVolumeNode.GetRASToIJKMatrix(rastoijk)
        scalarVolumeNode.GetIJKToRASMatrix(ijktoras)

        # Get the current slice. It will be the same in both positions
        ijkCoords = list(rastoijk.MultiplyPoint(coords))

        # Add/substract the offset
        lm = slicer.app.layoutManager()
        activeWindow = lm.layout
        if activeWindow == self.AXIAL:
            ijkCoords[2] += sliceStep
            # Convert back to RAS, just replacing the Z
            newSlice = ijktoras.MultiplyPoint(ijkCoords)[2]
        elif activeWindow == self.SAGITTAL:
            ijkCoords[0] += sliceStep
            # Convert back to RAS, just replacing the X
            newSlice = ijktoras.MultiplyPoint(ijkCoords)[0]
        else:
            ijkCoords[1] += sliceStep
            # Convert back to RAS, just replacing the Z
            newSlice = ijktoras.MultiplyPoint(ijkCoords)[1]

        self._placeRulerInSlice_(rulerNode, structureId, volumeId, newSlice)

        return newSlice

    def placeRulerInSlice(self, volumeId, structureId, newSlice, callbackWhenUpdated=None):
        """ Move the ruler to the specified slice (in RAS format)
        :param volumeId:
        :param structureId:
        :param newSlice: slice in RAS format
        :return: tuple with ruler node and a boolean indicating if the node was just created
        """
        # Get the correct ruler
        rulerNode, newNode = self.getRulerNodeForVolumeAndStructure(volumeId, structureId,
                                                                    createIfNotExist=True,
                                                                    callbackWhenRulerModified=callbackWhenUpdated)

        # Add the volume to the list of volumes that have some ruler
        # self.currentVolumesLoaded.add(volumeId)

        # Move the ruler
        self._placeRulerInSlice_(rulerNode, structureId, volumeId, newSlice)

    def _placeRulerInSlice_(self, rulerNode, structureId, volumeId, newSlice):
        """ Move the ruler to the specified slice (in RAS format)
        :param rulerNode: node of type vtkMRMLAnnotationRulerNode
        :param newSlice: slice in RAS format
        :return: True if the operation was succesful
        """
        coords1 = [0, 0, 0, 0]
        coords2 = [0, 0, 0, 0]
        # Get RAS coords of the ruler node
        rulerNode.GetPositionWorldCoordinates1(coords1)
        rulerNode.GetPositionWorldCoordinates2(coords2)

        # Set the slice of the coordinate
        layoutManager = slicer.app.layoutManager()
        if layoutManager is not None:
            activeWindow = layoutManager.layout
            if activeWindow == self.AXIAL:
                coords1[2] = coords2[2] = newSlice
                viewBounds = self.getViewBounds('Red')

                meanR = (viewBounds[0] + viewBounds[1]) / 2.0
                meanA = (viewBounds[2] + viewBounds[3]) / 2.0
                sepR = (viewBounds[1] - viewBounds[0]) * 0.1 - (viewBounds[1] - viewBounds[0]) * 0.05
                sepA = (viewBounds[3] - viewBounds[2]) * 0.1 - (viewBounds[3] - viewBounds[2]) * 0.05

                if structureId == self.AIRWAY:
                    coords1[0] = meanR - sepR
                    coords1[1] = meanA - sepA
                    coords2[0] = meanR + sepR
                    coords2[1] = meanA + sepA
                elif structureId == self.VESSEL:
                    coords1[0] = meanR - sepR
                    coords1[1] = meanA - 4.0 * sepA
                    coords2[0] = meanR + sepR
                    coords2[1] = meanA - 2.0 * sepA

            elif activeWindow == self.SAGITTAL:
                coords1[0] = coords2[0] = newSlice
                viewBounds = self.getViewBounds('Yellow')

                meanA = (viewBounds[2] + viewBounds[3]) / 2.0
                meanS = (viewBounds[4] + viewBounds[5]) / 2.0
                sepA = (viewBounds[3] - viewBounds[2]) * 0.1 - (viewBounds[3] - viewBounds[2]) * 0.05
                sepS = (viewBounds[5] - viewBounds[4]) * 0.1 - (viewBounds[5] - viewBounds[4]) * 0.05

                if structureId == self.AIRWAY:
                    coords1[1] = meanA - sepA
                    coords1[2] = meanS - sepS
                    coords2[1] = meanA + sepA
                    coords2[2] = meanS + sepS
                elif structureId == self.VESSEL:
                    coords1[1] = meanA - sepA
                    coords1[2] = meanS - 4.0 * sepS
                    coords2[1] = meanA + sepA
                    coords2[2] = meanS - 2.0 * sepS
            else:
                coords1[1] = coords2[1] = newSlice
                viewBounds = self.getViewBounds('Green')

                meanR = (viewBounds[0] + viewBounds[1]) / 2.0
                meanS = (viewBounds[4] + viewBounds[5]) / 2.0
                sepR = (viewBounds[1] - viewBounds[0]) * 0.1 - (viewBounds[1] - viewBounds[0]) * 0.05
                sepS = (viewBounds[5] - viewBounds[4]) * 0.1 - (viewBounds[5] - viewBounds[4]) * 0.05

                if structureId == self.AIRWAY:
                    coords1[0] = meanR - sepR
                    coords1[2] = meanS - sepS
                    coords2[0] = meanR + sepR
                    coords2[2] = meanS + sepS
                elif structureId == self.VESSEL:
                    coords1[0] = meanR - sepR
                    coords1[2] = meanS - 4.0 * sepS
                    coords2[0] = meanR + sepR
                    coords2[2] = meanS - 2.0 * sepS

        rulerNode.SetPositionWorldCoordinates1(coords1)
        rulerNode.SetPositionWorldCoordinates2(coords2)

        textDisplayNode = rulerNode.GetAnnotationTextDisplayNode()
        textDisplayNode.SetOpacity(0.3)

    def getViewBounds(self, view):
        """ Get the current view bounds (RAS format)
        :param view: view name (Red, Yellow, Green)
        :return: RAS bounds
        """
        rasBounds = [0, 0, 0, 0, 0, 0]
        layoutManager = slicer.app.layoutManager()
        if layoutManager is not None:
            layoutManager.sliceWidget(view).sliceLogic().GetSliceModelNode().GetRASBounds(rasBounds)

        return rasBounds

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


# TODO: modify this part!!
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
        self.assertIsNotNone(slicer.modules.cip_AVRatio)

        # Get the widget
        widget = slicer.modules.cip_AVRatio.widgetRepresentation()
        volume = SlicerUtil.downloadVolumeForTests(widget=widget)

        self.assertFalse(volume is None)

        # Get the logic
        logging.info("Getting logic...")
        logic = widget.self().logic

        # Actions
        # Make sure that the right volume is selected
        volumeSelector = SlicerUtil.findChildren(widget=widget, name='av_volumeSelector')[0]
        volumeSelector.setCurrentNode(volume)
        button = SlicerUtil.findChildren(widget=widget, name='jumptToTemptativeSliceButton')[0]
        # Place default rulers
        button.click()
        logging.info("Default rulers placed...OK")
        # Get rulers
        aorta = logic.getRulerNodeForVolumeAndStructure(volume.GetID(), logic.AORTA, createIfNotExist=False)[0]
        pa = logic.getRulerNodeForVolumeAndStructure(volume.GetID(), logic.PA, createIfNotExist=False)[0]
        # Make sure that rulers are in default color
        color = aorta.GetNthDisplayNode(0).GetColor()
        for i in range(3):
            self.assertEqual(color[i], logic.defaultColor[i])
        logging.info("Default color...OK")
        # Check that the rulers are properly positioned
        coordsAorta1 = [0,0,0]
        coordsPa1 = [0,0,0]
        aorta.GetPosition1(coordsAorta1)
        pa.GetPosition1(coordsPa1)
        # Aorta ruler should be on the left
        self.assertTrue(coordsAorta1[0] > coordsPa1[0])
        # Aorta and PA should be in the same slice
        self.assertTrue(coordsAorta1[2] == coordsPa1[2])
        logging.info("Default position...OK")

        # Change Slice of the Aorta ruler
        layoutManager = slicer.app.layoutManager()
        redWidget = layoutManager.sliceWidget('Red')
        style = redWidget.interactorStyle()
        style.MoveSlice(1)
        # Click in the radio button
        button = SlicerUtil.findChildren(widget=widget, name='aortaRadioButton')[0]
        button.click()
        # click in the place ruler button
        button = SlicerUtil.findChildren(widget=widget, name='placeRulersButton')[0]
        button.click()
        # Make sure that the slice of the ruler has changed
        aorta.GetPosition1(coordsAorta1)
        self.assertTrue(coordsAorta1[2] != coordsPa1[2])
        logging.info("Position changed...OK")

        # Force PAA ratio > 1
        coordsAorta2 = [0,0,0]
        coordsPa2 = [0,0,0]
        aorta.GetPosition2(coordsAorta2)
        pa.GetPosition2(coordsPa2)
        currentRatio = pa.GetDistanceMeasurement() / aorta.GetDistanceMeasurement()
        # Calculate how much do we have to increase the position of the pa marker
        delta = 1 - currentRatio + 0.2
        pa.SetPosition2(coordsPa2[0] + coordsPa2[0]*delta, coordsPa2[1], coordsPa2[2])

        # Make sure that rulers are red now
        color = aorta.GetNthDisplayNode(0).GetColor()
        for i in range(3):
            self.assertEqual(color[i], logic.defaultWarningColor[i])
        logging.info("Red color...OK")
        self.delayDisplay('Test passed!')
