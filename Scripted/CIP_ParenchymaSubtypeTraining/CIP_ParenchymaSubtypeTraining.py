import os, sys
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
        path = os.path.normpath(path + '/../CIP_Common')    # We assume that CIP_Common is a sibling folder of the one that contains this module
    elif os.path.exists(os.path.normpath(path + '/CIP')):
        path = os.path.normpath(path + '/CIP')    # We assume that CIP is a subfolder (Slicer behaviour)
    sys.path.append(path)
    from CIP.logic import SlicerUtil
    print("CIP was added to the python path manually in CIP_ParenchyaSubtypeTraining")

from CIP.logic import SubtypingParameters


#
# CIP_ParenchymaSubtypeTraining
#
class CIP_ParenchymaSubtypeTraining(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "Parenchyma Subtype Training"
        self.parent.categories = SlicerUtil.CIP_ModulesCategory
        self.parent.dependencies = [SlicerUtil.CIP_ModuleName]
        self.parent.contributors = ["Jorge Onieva (jonieva@bwh.harvard.edu)", "Applied Chest Imaging Laboratory", "Brigham and Women's Hospital"]
        self.parent.helpText = """Training for a subtype of emphysema done quickly by an expert"""
        self.parent.acknowledgementText = SlicerUtil.ACIL_AcknowledgementText

#
# CIP_ParenchymaSubtypeTrainingWidget
#

class CIP_ParenchymaSubtypeTrainingWidget(ScriptedLoadableModuleWidget):
    """Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """
    def setup(self):
        """This is called one time when the module GUI is initialized
        """
        ScriptedLoadableModuleWidget.setup(self)

        # Create objects that can be used anywhere in the module. Example: in most cases there should be just one
        # object of the logic class
        self.logic = CIP_ParenchymaSubtypeTrainingLogic()

        ##########
        # Main area
        self.mainAreaCollapsibleButton = ctk.ctkCollapsibleButton()
        self.mainAreaCollapsibleButton.text = "Main area"
        self.layout.addWidget(self.mainAreaCollapsibleButton)
        self.mainLayout = qt.QGridLayout(self.mainAreaCollapsibleButton)

        # Node selector
        self.volumeSelector = slicer.qMRMLNodeComboBox()
        self.volumeSelector.nodeTypes = ( "vtkMRMLScalarVolumeNode", "")
        self.volumeSelector.selectNodeUponCreation = True
        self.volumeSelector.autoFillBackground = True
        self.volumeSelector.addEnabled = False
        self.volumeSelector.noneEnabled = False
        self.volumeSelector.removeEnabled = False
        self.volumeSelector.showHidden = False
        self.volumeSelector.showChildNodeTypes = False
        self.volumeSelector.setMRMLScene( slicer.mrmlScene )
        self.volumeSelector.setStyleSheet("margin: 15px 0")
        #self.volumeSelector.selectNodeUponCreation = False
        self.mainLayout.addWidget(self.volumeSelector, 0, 0, 1, 2)

        # Radio Buttons types
        self.mainLayout.addWidget(qt.QLabel("Select the type"), 1, 0)
        self.typesFrame = qt.QFrame()
        self.typesLayout = qt.QVBoxLayout(self.typesFrame)
        self.mainLayout.addWidget(self.typesFrame, 2, 0)

        self.typesRadioButtonGroup = qt.QButtonGroup()
        for key, description in self.logic.mainTypes.iteritems():
            rbitem = qt.QRadioButton(description)
            self.typesRadioButtonGroup.addButton(rbitem, key)
            self.typesLayout.addWidget(rbitem)
        self.typesRadioButtonGroup.buttons()[0].setChecked(True)

        # Radio buttons subtypes
        self.mainLayout.addWidget(qt.QLabel("Select the subtype"), 1, 1)
        self.subtypesRadioButtonGroup = qt.QButtonGroup()
        self.subtypesFrame = qt.QFrame()
        self.subtypesFrame.setFixedHeight(300)
        self.subtypesLayout = qt.QVBoxLayout(self.subtypesFrame)
        self.mainLayout.addWidget(self.subtypesFrame, 2, 1)
        self.updateState()






        # Example button with some common properties
        self.exampleButton = ctk.ctkPushButton()
        self.exampleButton.text = "Push me!"
        self.exampleButton.toolTip = "This is the button tooltip"
        self.exampleButton.setIcon(qt.QIcon("{0}/Reload.png".format(SlicerUtil.ICON_DIR)))
        self.exampleButton.setIconSize(qt.QSize(20,20))
        self.exampleButton.setStyleSheet("font-weight:bold; font-size:12px" )
        self.exampleButton.setFixedWidth(200)
        self.mainLayout.addWidget(self.exampleButton)

        # Connections
        self.typesRadioButtonGroup.connect("buttonClicked (QAbstractButton*)", self.ontypestRadioButtonClicked)
        self.volumeSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.onVolumeSelected)





        self.exampleButton.connect('clicked()', self.onApplyButton)


    def updateState(self):
        """ Refresh the markups state, activate the right fiducials list node (depending on the
        current selected type) and creates it when necessary
        :return:
        """
        selectedVolume = self.volumeSelector.currentNode()
        if selectedVolume is not None:
            self.logic.setActiveFiducialsListNode(selectedVolume, self.typesRadioButtonGroup.checkedId())

        for i in range(len(self.typesRadioButtonGroup.buttons())):
            if self.typesRadioButtonGroup.buttons()[i].checked:
                # Load the subtypes for this type
                subtypesDict = self.logic.getSubtypes(self.typesRadioButtonGroup.checkedId())
                # Remove all the existing buttons
                for b in self.subtypesRadioButtonGroup.buttons():
                    b.hide()
                    b.delete()
                # Add all the subtypes with the full description
                for subtype in subtypesDict.iterkeys():
                    rbitem = qt.QRadioButton(self.logic.getSubtypeFullDescription(subtype))
                    self.subtypesRadioButtonGroup.addButton(rbitem, subtype)
                    self.subtypesLayout.addWidget(rbitem)
                # Check first element
                self.subtypesRadioButtonGroup.buttons()[0].setChecked(True)



    def enter(self):
        """This is invoked every time that we select this module as the active module in Slicer (not only the first time)"""
        SlicerUtil.setFiducialsMode(True, True)


    def exit(self):
        """This is invoked every time that we switch to another module (not only when Slicer is closed)."""
        try:
            SlicerUtil.setFiducialsMode(False)
        except:
            pass

    def cleanup(self):
        """This is invoked as a destructor of the GUI when the module is no longer going to be used"""
        pass

    def onVolumeSelected(self, volumeNode):
        # Get the fiducials node for this volume. Create it if necessary
        #fid = self.logic.setActiveFiducialsListNode(volumeNode)
        self.updateState()

    def ontypestRadioButtonClicked(self, button):
        """ One of the radio buttons has been pressed. I can't do anything with the button because what I really
        need is the index. Although radio buttons in Qt have an id that should be used instead of indexes,
        for some reason this property is not exposed in Slicer!
        :param button:
        :return:
        """
        self.updateState()


    def onApplyButton(self):
        message = self.logic.printMessage("This is the message that I want to print")
        qt.QMessageBox.information(slicer.util.mainWindow(), 'OK!', 'The test was ok. Review the console for details')



#
# CIP_ParenchymaSubtypeTrainingLogic
#
class CIP_ParenchymaSubtypeTrainingLogic(ScriptedLoadableModuleLogic):
    def __init__(self):
        self.params = SubtypingParameters.SubtypingParameters()
        self.markupsLogic = slicer.modules.markups.logic()

    # Constants
    @property
    def mainTypes(self):
        """ Return an OrderedDic with key=Code and value=Description of the subtype """
        return self.params.types

    # @property
    # def subtypes(self):
    #     return self.params.subtypes

    def getSubtypes(self, typeId):
        """ Get all the subtypes for the specified type
        :param typeId: type id
        :return: List of tuples with (Key, Description) with the subtypes """
        return self.params.getSubtypes(typeId)

    def getSubtypeFullDescription(self, subtypeId):
        return self.params.getSubtypeFullDescr(subtypeId)

    def _createFiducialsNode_(self, nodeName, typeId):
        """ Create a fiducials list node for this volume and this type. Depending on the type, the color will be different
        :param nodeName: Full name of the fiducials list node
        :param typeId: type id that will modify the color of the fiducial
        :return: fiducials list node
        """
        fidListID = self.markupsLogic.AddNewFiducialNode(nodeName, slicer.mrmlScene)
        fidNode = slicer.util.getNode(fidListID)
        displayNode = fidNode.GetDisplayNode()
        displayNode.SetSelectedColor(self.params.getColor(typeId))

        return fidNode

    def setActiveFiducialsListNode(self, volumeNode, typeId, createIfNotExists=True):
        """ Get the vtkMRMLMarkupsFiducialNode node associated with this volume and this type"""
        if volumeNode is not None:
            nodeName = "{0}_fiducials_{1}".format(volumeNode.GetID(), typeId)
            fid = slicer.util.getNode(nodeName)
            if fid is None and createIfNotExists:
                fid = self._createFiducialsNode_(nodeName, typeId)

            return fid

    def setActiveFiducialsList(self, fiducialsNode):
        self.markupsLogic.SetActiveListID(fiducialsNode)


    def printMessage(self, message):
        print("This is your message: ", message)
        return "I have printed this message: " + message



class CIP_ParenchymaSubtypeTrainingTest(ScriptedLoadableModuleTest):
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
        self.test_CIP_ParenchymaSubtypeTraining_PrintMessage()

    def test_CIP_ParenchymaSubtypeTraining_PrintMessage(self):
        self.delayDisplay("Starting the test")
        logic = CIP_ParenchymaSubtypeTrainingLogic()

        myMessage = "Print this test message in console"
        logging.info("Starting the test with this message: " + myMessage)
        expectedMessage = "I have printed this message: " + myMessage
        logging.info("The expected message would be: " + expectedMessage)
        responseMessage = logic.printMessage(myMessage)
        logging.info("The response message was: " + responseMessage)
        self.assertTrue(responseMessage == expectedMessage)
        self.delayDisplay('Test passed!')
