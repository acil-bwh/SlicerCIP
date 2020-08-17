# -*- coding: utf-8 -*-
import logging
from collections import OrderedDict

import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *

from CIP.logic.SlicerUtil import SlicerUtil
from CIP.logic import Util
from CIP.ui import CaseReportsWidget

#
# CIP_RVLVRatio
#
class CIP_RVLVRatio(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "RV/LV Ratio"
        self.parent.categories = SlicerUtil.CIP_ModulesCategory
        self.parent.dependencies = [SlicerUtil.CIP_ModuleName]
        self.parent.contributors = ["Jorge Onieva (jonieva@bwh.harvard.edu)", "Applied Chest Imaging Laboratory", "Brigham and Women's Hospital"]
        self.parent.helpText = """Calculate the ratio between the right and left heart ventricles (RV / LV)"""
        self.parent.acknowledgementText = SlicerUtil.ACIL_AcknowledgementText

#
# CIP_RVLVRatioWidget
#

class CIP_RVLVRatioWidget(ScriptedLoadableModuleWidget):
    """Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    @property
    def currentVolumeId(self):
        return self.volumeSelector.currentNodeID

    def __init__(self, parent):
        ScriptedLoadableModuleWidget.__init__(self, parent)
        self.moduleName = "CIP_RVLVRatio"
        from functools import partial
        def __onNodeAddedObserver__(self, caller, eventId, callData):
            """Node added to the Slicer scene"""
            if callData.GetClassName() == 'vtkMRMLScalarVolumeNode' \
                    and slicer.util.mainWindow().moduleSelector().selectedModule == self.moduleName:    # Current module visible
                self.volumeSelector.setCurrentNode(callData)
                SlicerUtil.changeContrastWindow(350, 40)

        self.__onNodeAddedObserver__ = partial(__onNodeAddedObserver__, self)
        self.__onNodeAddedObserver__.CallDataType = vtk.VTK_OBJECT

    def setup(self):
        """This is called one time when the module GUI is initialized
        """
        ScriptedLoadableModuleWidget.setup(self)

        # Create objects that can be used anywhere in the module. Example: in most cases there should be just one
        # object of the logic class
        self.logic = CIP_RVLVRatioLogic()

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
        self.volumeSelector.name = "rvlv_volumeSelector"
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

        self.jumptToTemptativeSliceButton = ctk.ctkPushButton()
        self.jumptToTemptativeSliceButton.name = "jumptToTemptativeSliceButton"
        self.jumptToTemptativeSliceButton.text = "Jump to temptative slice"
        self.jumptToTemptativeSliceButton.toolTip = "Jump to the best estimated slice to place the rulers"
        self.jumptToTemptativeSliceButton.setIcon(qt.QIcon("{0}/ruler.png".format(SlicerUtil.CIP_ICON_DIR)))
        self.jumptToTemptativeSliceButton.setIconSize(qt.QSize(20, 20))
        self.jumptToTemptativeSliceButton.setStyleSheet("font-weight: bold;")
        # self.jumptToTemptativeSliceButton.setFixedWidth(140)
        self.mainAreaLayout.addWidget(self.jumptToTemptativeSliceButton, 1, 1)

        ### Structure Selector
        self.structuresGroupbox = qt.QGroupBox("Select the structure")
        self.groupboxLayout = qt.QVBoxLayout()
        self.structuresGroupbox.setLayout(self.groupboxLayout)
        self.mainAreaLayout.addWidget(self.structuresGroupbox, 2, 0)


        self.structuresButtonGroup=qt.QButtonGroup()
        # btn = qt.QRadioButton("None")
        # btn.visible = False
        # self.structuresButtonGroup.addButton(btn)
        # self.groupboxLayout.addWidget(btn)

        btn = qt.QRadioButton("Both")
        btn.name = "rvlvButton"
        btn.checked = True

        self.structuresButtonGroup.addButton(btn, 0)
        self.groupboxLayout.addWidget(btn)

        btn = qt.QRadioButton("Right Ventricle (RV)")
        btn.name = "rvRadioButton"
        self.structuresButtonGroup.addButton(btn, 1)
        self.groupboxLayout.addWidget(btn)

        btn = qt.QRadioButton("Left Ventricle (LV)")
        btn.name = "lvRadioButton"
        self.structuresButtonGroup.addButton(btn, 2)
        self.groupboxLayout.addWidget(btn)

        ### Buttons toolbox
        self.buttonsToolboxFrame = qt.QFrame()
        self.buttonsToolboxLayout = qt.QGridLayout()
        self.buttonsToolboxFrame.setLayout(self.buttonsToolboxLayout)
        self.mainAreaLayout.addWidget(self.buttonsToolboxFrame, 2, 1)


        self.placeRulersButton = ctk.ctkPushButton()
        self.placeRulersButton.text = "Place ruler/s"
        self.placeRulersButton.name = "placeRulersButton"
        self.placeRulersButton.toolTip = "Place the ruler/s for the selected structure/s in the current slice"
        self.placeRulersButton.setIcon(qt.QIcon("{0}/ruler.png".format(SlicerUtil.CIP_ICON_DIR)))
        self.placeRulersButton.setIconSize(qt.QSize(20,20))
        self.placeRulersButton.setFixedWidth(105)
        self.placeRulersButton.setStyleSheet("font-weight:bold")
        self.buttonsToolboxLayout.addWidget(self.placeRulersButton, 0, 0)

        self.moveUpButton = ctk.ctkPushButton()
        self.moveUpButton.text = "Move up"
        self.moveUpButton.toolTip = "Move the selected ruler/s one slice up"
        self.moveUpButton.setIcon(qt.QIcon("{0}/move_up.png".format(SlicerUtil.CIP_ICON_DIR)))
        self.moveUpButton.setIconSize(qt.QSize(20,20))
        self.moveUpButton.setFixedWidth(95)
        self.buttonsToolboxLayout.addWidget(self.moveUpButton, 0, 1)

        self.moveDownButton = ctk.ctkPushButton()
        self.moveDownButton.text = "Move down"
        self.moveDownButton.toolTip = "Move the selected ruler/s one slice down"
        self.moveDownButton.setIcon(qt.QIcon("{0}/move_down.png".format(SlicerUtil.CIP_ICON_DIR)))
        self.moveDownButton.setIconSize(qt.QSize(20,20))
        self.moveDownButton.setFixedWidth(95)
        self.buttonsToolboxLayout.addWidget(self.moveDownButton, 0, 2)

        self.removeButton = ctk.ctkPushButton()
        self.removeButton.text = "Remove ALL rulers"
        self.removeButton.toolTip = "Remove all the rulers for this volume"
        self.removeButton.setIcon(qt.QIcon("{0}/delete.png".format(SlicerUtil.CIP_ICON_DIR)))
        self.removeButton.setIconSize(qt.QSize(20,20))
        self.buttonsToolboxLayout.addWidget(self.removeButton, 1, 1, 1, 2, 2)

        ### Textboxes
        self.textboxesFrame = qt.QFrame()
        self.textboxesLayout = qt.QFormLayout()
        self.textboxesFrame.setLayout(self.textboxesLayout)
        self.textboxesFrame.setFixedWidth(190)
        self.mainAreaLayout.addWidget(self.textboxesFrame, 3, 0)

        self.rvTextBox = qt.QLineEdit()
        self.rvTextBox.setReadOnly(True)
        self.textboxesLayout.addRow("RV (mm):  ", self.rvTextBox)

        self.lvTextBox = qt.QLineEdit()
        self.lvTextBox.setReadOnly(True)
        self.textboxesLayout.addRow("LV (mm):  ", self.lvTextBox)

        self.ratioTextBox = qt.QLineEdit()
        self.ratioTextBox.name = "ratioTextBox"
        self.ratioTextBox.setReadOnly(True)
        self.textboxesLayout.addRow("Ratio RV/LV: ", self.ratioTextBox)

        # Save case data
        self.reportsCollapsibleButton = ctk.ctkCollapsibleButton()
        self.reportsCollapsibleButton.text = "Reporting"
        self.layout.addWidget(self.reportsCollapsibleButton)
        self.reportsLayout = qt.QHBoxLayout(self.reportsCollapsibleButton)

        self.storedColumnNames = ["caseId", "rvDiameterMm", "lvDiameterMm",
                                  "rv1r", "rv1a", "rv1s", "rv2r", "rv2a", "rv2s",
                                  "lv1r", "lv1a", "lv1s", "lv2r", "lv2a", "lv2s"]
        columns = CaseReportsWidget.getColumnKeysNormalizedDictionary(self.storedColumnNames)
        self.reportsWidget = CaseReportsWidget(self.moduleName, columns, parentWidget=self.reportsCollapsibleButton)
        self.reportsWidget.setup()

        # Init state
        self.resetModuleState()

        self.preventSavingState = False
        self.saveStateBeforeEnteringModule()
        self.preventSavingState = True

        self.switchToRedView()

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

        self.volumeSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.onVolumeSelectorChanged)
        self.jumptToTemptativeSliceButton.connect('clicked()', self.onJumpToTemptativeSliceButtonClicked)
        self.placeRulersButton.connect('clicked()', self.onPlaceRulersClicked)
        self.moveUpButton.connect('clicked()', self.onMoveUpRulerClicked)
        self.moveDownButton.connect('clicked()', self.onMoveDownRulerClicked)
        self.removeButton.connect('clicked()', self.onRemoveRulerClicked)

        self.reportsWidget.addObservable(self.reportsWidget.EVENT_SAVE_BUTTON_CLICKED, self.onSaveReport)

        # Init state
        self.resetModuleState()

        self.preventSavingState = False
        self.saveStateBeforeEnteringModule()
        self.preventSavingState = True

    def enter(self):
        """This is invoked every time that we select this module as the active module in Slicer (not only the first time)"""
        # activeVolumeId = SlicerUtil.getActiveVolumeIdInRedSlice()
        # if activeVolumeId is not None:
        #     self.volumeSelector.setCurrentNodeID(activeVolumeId)
        #     if activeVolumeId not in self.logic.currentVolumesLoaded:
        #         self.placeDefaultRulers(activeVolumeId)
        # Save state
        self.saveStateBeforeEnteringModule()

        # Start listening again to scene events
        self.__addSceneObservables__()

        volumeId = self.volumeSelector.currentNodeID
        if volumeId:
            SlicerUtil.displayBackgroundVolume(volumeId)
            # Show the current rulers (if existing)
            self.logic.rulersVisible(volumeId, visible=True)

        # This module always works in Axial
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
        if self.preventSavingState:
            # Avoid that the first time that the module loads, the state is saved twice
            self.preventSavingState = False
            return

        # Save existing layout
        self.savedLayout = None
        if slicer.app.layoutManager() is not None:
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
                self.savedContrastLevel = (displayNode.GetWindow(), displayNode.GetLevel())
                # activeLabelmapId = SlicerUtil.getFirstActiveLabelmapId()
                # self.savedLabelmapID = activeLabelmapId
                # if activeLabelmapId is None:
                #     self.savedLabelmapOpacity = None
                # else:
                #     self.savedLabelmapOpacity = SlicerUtil.getLabelmapOpacity()
                #     # Hide any labelmap
                #     SlicerUtil.displayLabelmapVolume(None)
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
                # if self.savedLabelmapID:
                #     print "Restoring active labelmap: " + self.savedLabelmapID
                #     # There was a valid labelmap. Restore it
                #     SlicerUtil.displayLabelmapVolume(self.savedLabelmapID)
                #     # Restore previous opacity
                #     SlicerUtil.changeLabelmapOpacity(self.savedLabelmapOpacity)
                # else:
                #     # Hide labelmap
                #     print "No labelmap saved. Hide all"
                #     SlicerUtil.displayLabelmapVolume(None)
            # else:
            #     # Hide labelmap
            #     print "No volume saved. Hide labelmap"
            #     SlicerUtil.displayLabelmapVolume(None)

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
        SlicerUtil.changeContrastWindow(350, 40)

    def changeToDefaultContrastLevel(self):
        # Preferred contrast
        SlicerUtil.changeContrastWindow(1000, 200)

    def jumpToTemptativeSlice(self, volumeId):
        """ Jump the red window to a predefined slice based on the size of the volume
        :param volumeId:
        """
        # Get the default coordinates of the ruler
        rv1, rv2, pa1, pa2 = self.logic.getDefaultCoords(volumeId)
        # Set the display in the right slice
        self.moveRedWindowToSlice(rv1[2])

        redSliceNode = slicer.util.getFirstNodeByClassByName("vtkMRMLSliceNode", "Red")

        factor = 0.5
        newFOVx = redSliceNode.GetFieldOfView()[0] * factor
        newFOVy = redSliceNode.GetFieldOfView()[1] * factor
        newFOVz = redSliceNode.GetFieldOfView()[2]
        # Move the camera up to fix the view
        redSliceNode.SetXYZOrigin(0, 50, 0)
        # Update the FOV (zoom in)
        redSliceNode.SetFieldOfView(newFOVx, newFOVy, newFOVz)
        # Refresh the data in the viewer
        redSliceNode.UpdateMatrices()

    def placeDefaultRulers(self, volumeId):
        """ Set the Aorta and PA rulers to a default estimated position and jump to that slice
        :param volumeId:
        """
        if not volumeId:
            return
        # Hide all the actual ruler nodes
        self.logic.hideAllRulers()
        # Remove the current rulers for this volume
        self.logic.removeRulers(volumeId)
        # Create the default rulers
        self.logic.createDefaultRulers(volumeId, self.onRulerUpdated)
        # Activate both structures
        self.structuresButtonGroup.buttons()[0].setChecked(True)
        # Jump to the slice where the rulers are
        self.jumpToTemptativeSlice(volumeId)
        # Place the rulers in the current slice
        self.placeRuler()
        # Add the current volume to the list of loaded volumes
        #self.logic.currentVolumesLoaded.add(volumeId)

        # Modify the zoom of the Red slice
        redSliceNode = slicer.util.getFirstNodeByClassByName("vtkMRMLSliceNode", "Red")
        factor = 0.5
        newFOVx = redSliceNode.GetFieldOfView()[0] * factor
        newFOVy = redSliceNode.GetFieldOfView()[1] * factor
        newFOVz = redSliceNode.GetFieldOfView()[2]
        redSliceNode.SetFieldOfView( newFOVx, newFOVy, newFOVz )
        # Move the camera up to fix the view
        redSliceNode.SetXYZOrigin(0, 50, 0)
        # Refresh the data in the viewer
        redSliceNode.UpdateMatrices()


    def placeRuler(self):
        """ Place one or the two rulers in the current visible slice in Red node
        """
        volumeId = self.volumeSelector.currentNodeID
        if volumeId == '':
            self.showUnselectedVolumeWarningMessage()
            return

        selectedStructure = self.getCurrentSelectedStructure()
        if selectedStructure == self.logic.NONE:
            qt.QMessageBox.warning(slicer.util.mainWindow(), 'Review structure',
                'Please select RV, LV or both to place the right ruler/s')
            return

        # Get the current slice
        currentSlice = self.getCurrentRedWindowSlice()

        print(("Selected: ", selectedStructure))
        if selectedStructure == self.logic.BOTH:
            structures = [self.logic.LV, self.logic.RV]
        else:
            structures = [selectedStructure]

        for structure in structures:
            self.logic.placeRulerInSlice(volumeId, structure, currentSlice, self.onRulerUpdated)

        self.refreshTextboxes()


    def getCurrentSelectedStructure(self):
        """ Get the current selected structure id
        :return: self.logic.AORTA or self.logic.PA
        """
        selectedStructureText = self.structuresButtonGroup.checkedButton().text
        if selectedStructureText == "Right Ventricle (RV)": return self.logic.RV
        elif selectedStructureText == "Left Ventricle (LV)": return  self.logic.LV
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
            self.logic.stepSlice(volumeId, self.logic.RV, offset)
            newSlice = self.logic.stepSlice(volumeId, self.logic.LV, offset)
        else:
            newSlice = self.logic.stepSlice(volumeId, selectedStructure, offset)

        self.moveRedWindowToSlice(newSlice)

    def removeRulers(self):
        """ Remove all the rulers related to the current volume node
        :return:
        """
        self.logic.removeRulers(self.volumeSelector.currentNodeID)
        self.refreshTextboxes(reset=True)


    def getCurrentRedWindowSlice(self):
        """ Get the current slice (in RAS) of the Red window
        :return:
        """
        redNodeSliceNode = slicer.app.layoutManager().sliceWidget('Red').sliceLogic().GetSliceNode()
        return redNodeSliceNode.GetSliceOffset()

    def moveRedWindowToSlice(self, newSlice):
        """ Moves the red display to the specified RAS slice
        :param newSlice: slice to jump (RAS format)
        :return:
        """
        redNodeSliceNode = slicer.app.layoutManager().sliceWidget('Red').sliceLogic().GetSliceNode()
        redNodeSliceNode.JumpSlice(0,0,newSlice)

    def refreshTextboxes(self, reset=False):
        """ Update the information of the textboxes that give information about the measurements
        """
        self.rvTextBox.setText("0")
        self.lvTextBox.setText("0")
        self.ratioTextBox.setText("0")
        self.ratioTextBox.setStyleSheet(" QLineEdit { background-color: white; color: black}");

        volumeId = self.volumeSelector.currentNodeID
        # if volumeId not in self.logic.currentVolumesLoaded:
        #     return

        rv = None
        lv = None
        if not reset:
            rulerRV, newRV = self.logic.getRulerNodeForVolumeAndStructure(self.volumeSelector.currentNodeID,
                                                                                self.logic.RV, createIfNotExist=False)
            rulerLV, newLV = self.logic.getRulerNodeForVolumeAndStructure(self.volumeSelector.currentNodeID,
                                                                          self.logic.LV, createIfNotExist=False)
            if rulerRV:
                rv = rulerRV.GetDistanceMeasurement()
                self.rvTextBox.setText(str(rv))
            if rulerLV:
                lv = rulerLV.GetDistanceMeasurement()
                self.lvTextBox.setText(str(lv))
            if lv is not None and rv is not None and rv != 0:
                try:
                    ratio = lv / rv
                    self.ratioTextBox.setText(str(ratio))
                    if ratio > 1.0:
                        # Switch colors ("alarm")
                        st = " QLineEdit {{ background-color: rgb({0}, {1}, {2}); color: white }}". \
                                                        format(int(self.logic.defaultWarningColor[0]*255),
                                                                int(self.logic.defaultWarningColor[1]*255),
                                                                int(self.logic.defaultWarningColor[2]*255))
                        self.ratioTextBox.setStyleSheet(st)
                except Exception:
                    Util.print_last_exception()

    def showUnselectedVolumeWarningMessage(self):
        qt.QMessageBox.warning(slicer.util.mainWindow(), 'Select a volume',
                'Please select a volume')

    def showUnselectedStructureWarningMessage(self):
        qt.QMessageBox.warning(slicer.util.mainWindow(), 'Review structure',
                'Please select RV, LV or Both to place the right ruler/s')

    def switchToRedView(self):
        """ Switch the layout to Red slice only
        :return:
        """
        layoutManager = slicer.app.layoutManager()
        # Test the layout manager is not none in case the module is initialized without a main window
        # This happens for example in automatic tests
        if layoutManager is not None:
            layoutManager.setLayout(6)

    def __addSceneObservables__(self):
        self.observers.append(slicer.mrmlScene.AddObserver(slicer.vtkMRMLScene.NodeAddedEvent, self.__onNodeAddedObserver__))
        self.observers.append(slicer.mrmlScene.AddObserver(slicer.vtkMRMLScene.EndCloseEvent, self.__onSceneClosed__))

    def __removeSceneObservables(self):
        for observer in self.observers:
            slicer.mrmlScene.RemoveObserver(observer)
            self.observers.remove(observer)

    #########
    # EVENTS
    def onVolumeSelectorChanged(self, node):
        #if node is not None and node.GetID() not in self.currentVolumesLoaded:
        # if node is not None:
        #     # New node. Load default rulers
        #     if node.GetID() not in self.logic.currentVolumesLoaded:
        #         self.placeDefaultRulers(node.GetID())
        logging.info("Volume selector node changed: {0}".format(
            '(None)' if node is None else node.GetName()
        ))
        # Preferred contrast (TODO: set right level)
        SlicerUtil.changeContrastWindow(1144, 447)
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

    def onJumpToTemptativeSliceButtonClicked(self):
        volumeId = self.volumeSelector.currentNodeID
        if volumeId == '':
            self.showUnselectedVolumeWarningMessage()
            return
        #self.placeDefaultRulers(volumeId)
        self.jumpToTemptativeSlice(volumeId)

    def onRulerUpdated(self, node, event):
        self.refreshTextboxes()

    def onPlaceRulersClicked(self):
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
            pa1 = pa2 = a1 = a2 = None
            # RV
            rulerNode, newNode = self.logic.getRulerNodeForVolumeAndStructure(volumeId, self.logic.RV, createIfNotExist=False)
            if rulerNode:
                # Get current RAS coords
                rulerNode.GetPositionWorldCoordinates1(coords)
                rv1 = list(coords)
                rulerNode.GetPositionWorldCoordinates2(coords)
                rv2 = list(coords)
            # LV
            rulerNode, newNode = self.logic.getRulerNodeForVolumeAndStructure(volumeId, self.logic.LV, createIfNotExist=False)
            if rulerNode:
                rulerNode.GetPositionWorldCoordinates1(coords)
                lv1 = list(coords)
                rulerNode.GetPositionWorldCoordinates2(coords)
                lv2 = list(coords)
            self.reportsWidget.insertRow(
                caseId=caseName,
                rvDiameterMm=self.rvTextBox.text,
                lvDiameterMm=self.lvTextBox.text,
                rv1r = rv1[0] if rv1 is not None else '',
                rv1a = rv1[1] if rv1 is not None else '',
                rv1s = rv1[2] if rv1 is not None else '',
                rv2r = rv2[0] if rv2 is not None else '',
                rv2a = rv2[1] if rv2 is not None else '',
                rv2s = rv2[2] if rv2 is not None else '',
                lv1r = lv1[0] if lv1 is not None else '',
                lv1a = lv1[1] if lv1 is not None else '',
                lv1s = lv1[2] if lv1 is not None else '',
                lv2r = lv2[0] if lv2 is not None else '',
                lv2a = lv2[1] if lv2 is not None else '',
                lv2s = lv2[2] if lv2 is not None else ''
            )
            qt.QMessageBox.information(slicer.util.mainWindow(), 'Data saved', 'The data were saved successfully')

    def __onSceneClosed__(self, arg1, arg2):
        """ Scene closed. Reset currently loaded volumes
        :param arg1:
        :param arg2:
        :return:
        """
        #self.logic.currentVolumesLoaded.clear()
        self.logic.currentActiveVolumeId = None


# CIP_RVLVRatioLogic
#
class CIP_RVLVRatioLogic(ScriptedLoadableModuleLogic):
    """This class should implement all the actual
    computation done by your module.    The interface
    should be such that other python code can import
    this class and make use of the functionality without
    requiring an instance of the Widget.
    Uses ScriptedLoadableModuleLogic base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    NONE = 0
    RV = 1
    LV = 2
    BOTH = 3
    SLICEFACTOR = 0.33

    # TODO: MODIFY THIS
    # Default XY coordinates for RV and LV (the Z will be estimated depending on the number of slices)
    defaultRV1 = [250, 170, 0]
    defaultRV2 = [300, 200, 0]
    defaultLV1 = [330, 200, 0]
    defaultLV2 = [355, 230, 0]

    defaultColor = [0.5, 0.5, 1.0]
    defaultWarningColor = [1.0, 0.0, 0.0]

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
        :return: "volumeId_paaRulersNode" vtkMRMLAnnotationHierarchyNode
        """
        # Search for the current volume hierarchy node (each volume has its own hierarchy)
        nodeName = volumeId + '_rvlvRulersNode'
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

    def getRulerNodeForVolumeAndStructure(self, volumeId, structureId, createIfNotExist=True, callbackWhenRulerModified=None):
        """ Search for the right ruler node to be created based on the volume and the selected
        structure (RV or LV).
        It also creates the necessary node hierarchy if it doesn't exist.
        :param volumeId:
        :param structureId: RV (1), LV (2)
        :param createIfNotExist: create the ruler node if it doesn't exist yet
        :param callbackWhenRulerModified: function to call when the ruler node is modified
        :return: node and a boolean indicating if the node has been created now
        """
        isNewNode = False
        if structureId == 0: # none
            return None, isNewNode
        if structureId == self.RV:
             #nodeName = volumeId + '_paaRulers_rv'
            nodeName = "RV"
        elif structureId == self.LV:   # 'Pulmonary Arterial':
        #     nodeName = volumeId + '_paaRulers_pa'
            nodeName = "LV"
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

    def createDefaultRulers(self, volumeId, callbackWhenRulerModified):
        """ Set the RV and LV rulers to their default position.
        The X and Y will be configured in "defaultRV1, defaultRV2, defaultLV1, defaultLV2" properties
        The Z will be estimated based on the number of slices of the volume
        :param volumeId: volume id
        :param callbackWhenRulerModified: function to invoke when the ruler is modified
        :return: a tuple of 4 vales. For each node, return the node and a boolean indicating if the node was
        created now
        """
        rv1, rv2, lv1, lv2 = self.getDefaultCoords(volumeId)

        rulerNodeRV, newNodeRV = self.getRulerNodeForVolumeAndStructure(volumeId, self.RV,
                                                                              createIfNotExist=True, callbackWhenRulerModified=callbackWhenRulerModified)
        rulerNodeRV.SetPositionWorldCoordinates1(rv1)
        rulerNodeRV.SetPositionWorldCoordinates2(rv2)

        rulerNodeLV, newNodeLV = self.getRulerNodeForVolumeAndStructure(volumeId, self.LV,
                                                                        createIfNotExist=True, callbackWhenRulerModified=callbackWhenRulerModified)
        rulerNodeLV.SetPositionWorldCoordinates1(lv1)
        rulerNodeLV.SetPositionWorldCoordinates2(lv2)

        return rulerNodeRV, newNodeRV, rulerNodeLV, newNodeLV

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

        coords = [0, 0, 0, 0]
        # Get current RAS coords
        rulerNode.GetPositionWorldCoordinates1(coords)

        # Get the transformation matrixes
        rastoijk=vtk.vtkMatrix4x4()
        ijktoras=vtk.vtkMatrix4x4()
        scalarVolumeNode = slicer.mrmlScene.GetNodeByID(volumeId)
        scalarVolumeNode.GetRASToIJKMatrix(rastoijk)
        scalarVolumeNode.GetIJKToRASMatrix(ijktoras)

        # Get the current slice (Z). It will be the same in both positions
        ijkCoords = list(rastoijk.MultiplyPoint(coords))

        # Add/substract the offset to Z
        ijkCoords[2] += sliceStep
        # Convert back to RAS, just replacing the Z
        newSlice = ijktoras.MultiplyPoint(ijkCoords)[2]

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
                                    createIfNotExist=True, callbackWhenRulerModified=callbackWhenUpdated)

        # Add the volume to the list of volumes that have some ruler
        # self.currentVolumesLoaded.add(volumeId)

        # Move the ruler
        self._placeRulerInSlice_(rulerNode, structureId, volumeId, newSlice)

        #return rulerNode, newNode

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
        coords1[2] = coords2[2] = newSlice

        if coords1[0] == 0 and coords1[1] == 0:
            # New node, get default coordinates depending on the structure
            defaultCoords = self.getDefaultCoords(volumeId)
            if structureId == self.RV:
                coords1[0] = defaultCoords[0][0]
                coords1[1] = defaultCoords[0][1]
                coords2[0] = defaultCoords[1][0]
                coords2[1] = defaultCoords[1][1]
            elif structureId == self.LV:
                coords1[0] = defaultCoords[2][0]
                coords1[1] = defaultCoords[2][1]
                coords2[0] = defaultCoords[3][0]
                coords2[1] = defaultCoords[3][1]

        rulerNode.SetPositionWorldCoordinates1(coords1)
        rulerNode.SetPositionWorldCoordinates2(coords2)

    def getDefaultCoords(self, volumeId):
        """ Get the default coords for rv and PA in this volume (RAS format)
        :param volumeId:
        :return: (rv1, rv2, pa1, pa2). All of them lists of 3 positions in RAS format
        """
        volume = slicer.mrmlScene.GetNodeByID(volumeId)
        rasBounds = [0,0,0,0,0,0]
        volume.GetRASBounds(rasBounds)
        # Get the slice (Z)
        ijk = self.RAStoIJK(volume, [0, 0, rasBounds[5]])
        slice = int(ijk[2] * self.SLICEFACTOR)       # Empiric estimation

        # Get the default coords, converting from IJK to RAS
        rv1 = list(self.defaultRV1)
        rv1[2] = slice
        rv1 = self.IJKtoRAS(volume, rv1)
        rv2 = list(self.defaultRV2)
        rv2[2] = slice
        rv2 = self.IJKtoRAS(volume, rv2)

        lv1 = list(self.defaultLV1)
        lv1[2] = slice
        lv1 = self.IJKtoRAS(volume, lv1)
        lv2 = list(self.defaultLV2)
        lv2[2] = slice
        lv2 = self.IJKtoRAS(volume, lv2)

        return rv1, rv2, lv1, lv2


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


class CIP_RVLVRatioTest(ScriptedLoadableModuleTest):
    @classmethod
    def setUpClass(cls):
        """ Executed once for all the tests """
        slicer.util.selectModule('CIP_RVLVRatio')

    def setUp(self):
        """ Do whatever is needed to reset the state - typically a scene clear will be enough.
        """
        slicer.mrmlScene.Clear(0)

    def runTest(self):
        """Run as few or as many tests as needed here.
        """
        self.setUp()
        self.test_CIP_RVLVRatio()

    def test_CIP_RVLVRatio(self):
        self.assertIsNotNone(slicer.modules.CIP_RVLVratio)

        # Get the widget
        widget = slicer.modules.CIP_RVLVratio.widgetRepresentation()
        volume = SlicerUtil.downloadVolumeForTests(widget=widget)

        self.assertFalse(volume is None)

        # Get the logic
        logging.info("Getting logic...")
        logic = widget.self().logic

        # Actions
        # Make sure that the right volume is selected
        volumeSelector = SlicerUtil.findChildren(widget=widget, name='rvlv_volumeSelector')[0]
        volumeSelector.setCurrentNode(volume)
        button = SlicerUtil.findChildren(widget=widget, name='jumptToTemptativeSliceButton')[0]
        # Place default rulers
        button.click()
        logging.info("Default rulers placed...OK")
        # Get rulers
        rv = logic.getRulerNodeForVolumeAndStructure(volume.GetID(), logic.RV, createIfNotExist=False)[0]
        pa = logic.getRulerNodeForVolumeAndStructure(volume.GetID(), logic.LV, createIfNotExist=False)[0]
        # Make sure that rulers are in default color
        color = rv.GetNthDisplayNode(0).GetColor()
        for i in range(3):
            self.assertEqual(color[i], logic.defaultColor[i])
        logging.info("Default color...OK")
        # Check that the rulers are properly positioned
        coordsRV1 = [0,0,0]
        coordsLV1 = [0,0,0]
        rv.GetPosition1(coordsRV1)
        pa.GetPosition1(coordsLV1)
        # Aorta ruler should be on the left
        self.assertTrue(coordsRV1[0] > coordsLV1[0])
        # Aorta and PA should be in the same slice
        self.assertTrue(coordsRV1[2] == coordsLV1[2])
        logging.info("Default position...OK")

        # Change Slice of the RV ruler
        layoutManager = slicer.app.layoutManager()
        redWidget = layoutManager.sliceWidget('Red')
        style = redWidget.interactorStyle()
        style.MoveSlice(1)
        # Click in the radio button
        button = SlicerUtil.findChildren(widget=widget, name='rvRadioButton')[0]
        button.click()
        # click in the place ruler button
        button = SlicerUtil.findChildren(widget=widget, name='placeRulersButton')[0]
        button.click()
        # Make sure that the slice of the ruler has changed
        rv.GetPosition1(coordsRV1)
        self.assertTrue(coordsRV1[2] != coordsLV1[2])
        logging.info("Position changed...OK")

        coordsRV2 = [0,0,0]
        coordsLV2 = [0,0,0]
        rv.GetPosition2(coordsRV2)
        pa.GetPosition2(coordsLV2)
        currentRatio = pa.GetDistanceMeasurement() / rv.GetDistanceMeasurement()
        # Calculate how much do we have to increase the position of the pa marker
        delta = 1 - currentRatio + 0.2
        pa.SetPosition2(coordsLV2[0] + coordsLV2[0]*delta, coordsLV2[1], coordsLV2[2])

        # Make sure that rulers are red now
        color = rv.GetNthDisplayNode(0).GetColor()
        for i in range(3):
            self.assertEqual(color[i], logic.defaultWarningColor[i])
        logging.info("Red color...OK")
        self.delayDisplay('Test passed!')
