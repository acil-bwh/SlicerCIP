# -*- coding: utf-8 -*-
import os
import unittest
from __main__ import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging

# Add the CIP common library to the path if it has not been loaded yet
try:
    from CIP.logic import SlicerUtil
except Exception as ex:
    import inspect
    path = os.path.dirname(inspect.getfile(inspect.currentframe()))
    if os.path.exists(os.path.normpath(path + '/../CIP_Common')):
            path = os.path.normpath(path + '/../CIP_Common')        # We assume that CIP_Common is a sibling folder of the one that contains this module
    elif os.path.exists(os.path.normpath(path + '/CIP')):
            path = os.path.normpath(path + '/CIP')        # We assume that CIP is a subfolder (Slicer behaviour)
    sys.path.append(path)
    from CIP.logic import SlicerUtil
print("CIP was added to the python path manually in CIP_PAARatio")

from CIP.logic import Util

#
# CIP_PAARatio
#
class CIP_PAARatio(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "PAA Ratio"
        self.parent.categories = SlicerUtil.CIP_ModulesCategory
        self.parent.dependencies = [SlicerUtil.CIP_ModuleName]
        self.parent.contributors = ["Jorge Onieva (jonieva@bwh.harvard.edu)", "Applied Chest Imaging Laboratory", "Brigham and Women's Hospital"]
        self.parent.helpText = """Calculate the ratio between pulmonary arterial and aorta. This biomarker has been proved
                                to predict acute exacerbations of COPD (Wells, J. M., Washko, G. R., Han, M. K., Abbas,
                                N., Nath, H., Mamary, a. J., Dransfield, M. T. (2012). Pulmonary Arterial Enlargement and Acute Exacerbations
                                of COPD. New England Journal of Medicine, 367(10), 913-921).
                                For more information refer to:
                                http://www.nejm.org/doi/full/10.1056/NEJMoa1203830"""
        self.parent.acknowledgementText = SlicerUtil.ACIL_AcknowledgementText

#
# CIP_PAARatioWidget
#

class CIP_PAARatioWidget(ScriptedLoadableModuleWidget):
    """Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def setup(self):
        """This is called one time when the module GUI is initialized
        """
        ScriptedLoadableModuleWidget.setup(self)

        # Create objects that can be used anywhere in the module. Example: in most cases there should be just one
        # object of the logic class
        self.logic = CIP_PAARatioLogic()

        #
        # Create all the widgets. Example Area
        mainAreaCollapsibleButton = ctk.ctkCollapsibleButton()
        mainAreaCollapsibleButton.text = "Parameters"
        self.layout.addWidget(mainAreaCollapsibleButton)
        # Layout within the dummy collapsible button. See http://doc.qt.io/qt-4.8/layout.html for more info about layouts
        mainAreaLayout = qt.QFormLayout(mainAreaCollapsibleButton)

        self.volumeSelector = slicer.qMRMLNodeComboBox()
        self.volumeSelector.nodeTypes = ( "vtkMRMLScalarVolumeNode", "" )
        self.volumeSelector.addAttribute( "vtkMRMLScalarVolumeNode", "LabelMap", "0" )

        self.volumeSelector.selectNodeUponCreation = False
        self.volumeSelector.addEnabled = True
        self.volumeSelector.noneEnabled = False
        self.volumeSelector.removeEnabled = False
        self.volumeSelector.showHidden = False
        self.volumeSelector.showChildNodeTypes = False
        self.volumeSelector.setMRMLScene( slicer.mrmlScene )
        self.volumeSelector.setToolTip( "Pick the label map to edit" )
        mainAreaLayout.addWidget( self.volumeSelector )

        # Selector
        label = qt.QLabel("Select the structure")
        mainAreaLayout.addWidget(label)

        self.structuresCheckboxGroup=qt.QButtonGroup()
        btn = qt.QRadioButton("None")
        btn.checked = True
        self.structuresCheckboxGroup.addButton(btn)
        mainAreaLayout.addWidget(btn)

        btn = qt.QRadioButton("Aorta")
        self.structuresCheckboxGroup.addButton(btn)
        mainAreaLayout.addWidget(btn)

        btn = qt.QRadioButton("Pulmonary Arterial")
        self.structuresCheckboxGroup.addButton(btn)
        mainAreaLayout.addWidget(btn)


        self.placeRulerButton = ctk.ctkPushButton()
        self.placeRulerButton.text = "Place ruler"
        self.placeRulerButton.toolTip = "This is the button tooltip"
        self.placeRulerButton.setIcon(qt.QIcon("{0}/Reload.png".format(Util.ICON_DIR)))
        self.placeRulerButton.setIconSize(qt.QSize(20,20))
        #self.placeRulerButton.setStyleSheet("font-weight:bold; font-size:12px" )
        self.placeRulerButton.setFixedWidth(200)
        mainAreaLayout.addWidget(self.placeRulerButton)

        self.moveUpButton = ctk.ctkPushButton()
        self.moveUpButton.text = "Up"
        mainAreaLayout.addWidget(self.moveUpButton)

        # Connections
        #self.structuresCheckboxGroup.connect("buttonClicked (QAbstractButton*)", self.onStructureClicked)

        self.placeRulerButton.connect('clicked()', self.onPlaceRuler)
        self.moveUpButton.connect('clicked()', self.onMoveUpRuler)

    def enter(self):
        """This is invoked every time that we select this module as the active module in Slicer (not only the first time)"""
        pass

    def exit(self):
        """This is invoked every time that we switch to another module (not only when Slicer is closed)."""
        pass

    def cleanup(self):
        """This is invoked as a destructor of the GUI when the module is no longer going to be used"""
        pass

    def __getLandmarkNode__(self, volumeId):
        """ Get a landmarks node for the specified volume id. If the node doesn't exist, it creates it.
        :param volumeId:
        :return:
        """



    # def getFiducialsNode(self, volumeId):
    #     """ Get the fiducials node for this volume id or create it if it doesn't exist
    #     :param option:
    #     :return:
    #     """
    #     # Check the active volume
    #     if volumeId != '':
    #          # Get the fiducials node for this volume (create it if it doesn't exist)
    #         name = volumeId + '_landmarks'
    #         fiducialsNode = slicer.mrmlScene.GetNodeByID(name)
    #         if fiducialsNode is None:
    #             # Create new fiducials node
    #             markupsLogic = slicer.modules.markups.logic()
    #             fiducialsNode = slicer.mrmlScene.GetNodeByID(markupsLogic.AddNewFiducialNode(name, slicer.mrmlScene))
    #         return fiducialsNode
    #     return None

    def getRootAnnotationsNode(self):
        """ Get the root annotations node, creating it if necessary
        :return:
        """
        rootHierarchyNode = slicer.util.getNode('All Annotations')
        if rootHierarchyNode is None:
            # Create root annotations node
            rootHierarchyNode = slicer.modules.annotations.logic().GetActiveHierarchyNode()
            logging.debug("Root annotations node created")
        return rootHierarchyNode

    def getRulersListNode(self, volumeId):
        """ Get the rulers node for this volume, creating it if it doesn't exist yet
        :param volumeId:
        :return:
        """
        rootHierarchyNode = self.getRootAnnotationsNode()
        # Search for the current volume hierarchy node (each volume has its own hierarchy)
        nodeName = volumeId + '_paaRulersNode'
        rulersNode = slicer.util.getNode(nodeName)

        if rulersNode is None:
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

    def getRulerNodeForVolumeAndStructure(self, volumeId, structureId):
        """ Search for the right ruler node to be created based on the volume and the selected
        structure (aorta or PA).
        It also creates the necessary node hierarchy if it doesn't exist.
        :param volumeId:
        :param structureId:
        :return:
        """
        if structureId == 0: # none
            return None
        if structureId == 1:     # Aorta
            nodeName = volumeId + '_paaRulers_aorta'
        elif structureId == 2:   # 'Pulmonary Arterial':
            nodeName = volumeId + '_paaRulers_pa'

        # Get the node that contains all the rulers
        rulersListNode = self.getRulersListNode(volumeId)

        # Search for the node
        node = slicer.util.getNode(nodeName)
        if node is None:
            # Set the active node, so that the new ruler is a child node
            annotationsLogic = slicer.modules.annotations.logic()
            annotationsLogic.SetActiveHierarchyNodeID(rulersListNode.GetID())
            node = slicer.mrmlScene.CreateNodeByClass('vtkMRMLAnnotationRulerNode')
            node.SetName(nodeName)
            slicer.mrmlScene.AddNode(node)
            logging.debug("Created node " + nodeName)

        return node



    def placeRuler(self, volumeId, structureId):
        """ Place a ruler in the current slice in the Red window. It replaces the existing
        one or creates a new one
        :param volumeId:
        :param option: Aorta or PA
        """
        rulerNode = self.getRulerNodeForVolumeAndStructure(volumeId, structureId)
        # Get the current slice
        layoutManager = slicer.app.layoutManager()
        redWidget = layoutManager.sliceWidget('Red')
        redNodeSliceNode = redWidget.sliceLogic().GetSliceNode()
        rasSliceOffset = redNodeSliceNode.GetSliceOffset()

         # Create the node in the current slice
        # TODO: conversion RAS -> IJK?
        defaultXY1 = [0, 50, rasSliceOffset]
        defaultXY2 = [0, 100, rasSliceOffset]

        coords1 = [defaultXY1[0], defaultXY1[1], rasSliceOffset]
        coords2 = [defaultXY2[0], defaultXY2[1], rasSliceOffset]
        rulerNode.SetPosition1(coords1)
        rulerNode.SetPosition2(coords2)

    def moveSlice(self, volumeId, structureId, offset):
        rulerNode = self.getRulerNodeForVolumeAndStructure(volumeId, structureId)
        coords1 = [0, 0, 0, 0]
        coords2 = [0, 0, 0, 0]
        # Get RAS coords
        rulerNode.GetPositionWorldCoordinates1(coords1)
        rulerNode.GetPositionWorldCoordinates2(coords2)

        # Get the transformation matrixes
        rastoijk=vtk.vtkMatrix4x4()
        ijktoras=vtk.vtkMatrix4x4()
        scalarVolumeNode = slicer.mrmlScene.GetNodeByID(volumeId)
        scalarVolumeNode.GetRASToIJKMatrix(rastoijk)
        scalarVolumeNode.GetIJKToRASMatrix(ijktoras)

        # Get the current slice (Z). It will be the same in both positions
        ijkCoords = list(rastoijk.MultiplyPoint(coords1))
        # Add/substract the offset to Z
        ijkCoords[2] += offset
        # Convert back to RAS, just replacing the Z
        newSlice = ijktoras.MultiplyPoint(ijkCoords)[2]
        # Set the ruler positions
        coords1[2] = coords2[2] = newSlice
        rulerNode.SetPositionWorldCoordinates1(coords1)
        rulerNode.SetPositionWorldCoordinates2(coords2)

        # Jump to the current slice
        layoutManager = slicer.app.layoutManager()
        redWidget = layoutManager.sliceWidget('Red')
        redNodeSliceNode = redWidget.sliceLogic().GetSliceNode()
        redNodeSliceNode.JumpSlice(0,0,newSlice)


    # Events
    def onStructureClicked(self, button):
        fiducialsNode = self.getFiducialsNode(self.volumeSelector.currentNodeId)
        if fiducialsNode is not None:
            self.__addRuler__(button.text, self.volumeSelector.currentNodeId)

            markupsLogic = slicer.modules.markups.logic()
            markupsLogic.SetActiveListID(fiducialsNode)

            applicationLogic = slicer.app.applicationLogic()
            selectionNode = applicationLogic.GetSelectionNode()

            selectionNode.SetReferenceActivePlaceNodeClassName("vtkMRMLAnnotationRulerNode")
            interactionNode = applicationLogic.GetInteractionNode()
            interactionNode.SwitchToSinglePlaceMode()


    def getCurrentSelectedStructure(self):
        selectedStructureText = self.structuresCheckboxGroup.checkedButton().text
        if selectedStructureText == "Aorta": return 1
        elif selectedStructureText == "Pulmonary Arterial": return  2
        return 0

    def onPlaceRuler(self):
        if self.volumeSelector.currentNodeId == '':
            qt.QMessageBox.warning(slicer.util.mainWindow(), 'Select a volume',
                'Please select a volume')
            return
        selectedStructure = self.getCurrentSelectedStructure()
        if selectedStructure == 0:
            qt.QMessageBox.warning(slicer.util.mainWindow(), 'Review structure',
                'Please select Aorta or Pulmonary Arterial to place the right ruler')
        else:
            self.placeRuler(self.volumeSelector.currentNodeId, selectedStructure)

    def onMoveUpRuler(self):
        selectedStructure = self.getCurrentSelectedStructure()
        if selectedStructure == 0:
            qt.QMessageBox.warning(slicer.util.mainWindow(), 'Review structure',
                'Please select Aorta or Pulmonary Arterial to move the right ruler')
        else:
            self.moveSlice(self.volumeSelector.currentNodeId, selectedStructure, 1)
#
# CIP_PAARatioLogic
#
class CIP_PAARatioLogic(ScriptedLoadableModuleLogic):
    """This class should implement all the actual
    computation done by your module.    The interface
    should be such that other python code can import
    this class and make use of the functionality without
    requiring an instance of the Widget.
    Uses ScriptedLoadableModuleLogic base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """
    def printMessage(self, message):
        print("This is your message: ", message)
        return "I have printed this message: " + message



class CIP_PAARatioTest(ScriptedLoadableModuleTest):
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
        self.test_CIP_PAARatio_PrintMessage()

    def test_CIP_PAARatio_PrintMessage(self):
        self.delayDisplay("Starting the test")
        logic = CIP_PAARatioLogic()

        myMessage = "Print this test message in console"
        logging.info("Starting the test with this message: " + myMessage)
        expectedMessage = "I have printed this message: " + myMessage
        logging.info("The expected message would be: " + expectedMessage)
        responseMessage = logic.printMessage(myMessage)
        logging.info("The response message was: " + responseMessage)
        self.assertTrue(responseMessage == expectedMessage)
        self.delayDisplay('Test passed!')
