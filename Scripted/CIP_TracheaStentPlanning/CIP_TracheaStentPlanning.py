import os, sys
import unittest
from __main__ import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging

# Add the CIP common library to the path if it has not been loaded yet
try:
        from CIP.logic.SlicerUtil import SlicerUtil
except Exception as ex:
        import inspect
        path = os.path.dirname(inspect.getfile(inspect.currentframe()))
        if os.path.exists(os.path.normpath(path + '/../CIP_Common')):
                path = os.path.normpath(path + '/../CIP_Common')        # We assume that CIP_Common is a sibling folder of the one that contains this module
        elif os.path.exists(os.path.normpath(path + '/CIP')):
                path = os.path.normpath(path + '/CIP')        # We assume that CIP is a subfolder (Slicer behaviour)
        sys.path.append(path)
        from CIP.logic.SlicerUtil import SlicerUtil
        print("CIP was added to the python path manually in CIP_TracheaStentPlanning")

from CIP.logic import Util



#
# CIP_TracheaStentPlanning
#
class CIP_TracheaStentPlanning(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "Trachea Stent Planning"
        self.parent.categories = SlicerUtil.CIP_ModulesCategory
        self.parent.dependencies = [SlicerUtil.CIP_ModuleName]
        self.parent.contributors = ["Applied Chest Imaging Laboratory", "Brigham and Women's Hospital"]
        self.parent.helpText = """Write here the description of your module"""
        self.parent.acknowledgementText = SlicerUtil.ACIL_AcknowledgementText

#
# CIP_TracheaStentPlanningWidget
#

class CIP_TracheaStentPlanningWidget(ScriptedLoadableModuleWidget):
    """Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def setup(self):
        """This is called one time when the module GUI is initialized
        """
        ScriptedLoadableModuleWidget.setup(self)
        
        # Create objects that can be used anywhere in the module. Example: in most cases there should be just one
        # object of the logic class
        self.logic = CIP_TracheaStentPlanningLogic()
        
#        #
#        # Reload and Test area
#        #
#        reloadCollapsibleButton = ctk.ctkCollapsibleButton()
#        reloadCollapsibleButton.text = "Reload && Test"
#        self.layout.addWidget(reloadCollapsibleButton)
#        self.layout.setSpacing(6)
#        reloadFormLayout = qt.QFormLayout(reloadCollapsibleButton)
#        
#        # reload button
#        # (use this during development, but remove it when delivering
#        #  your module to users)
#        self.reloadButton = qt.QPushButton("Reload")
#        self.reloadButton.toolTip = "Reload this module."
#        self.reloadButton.name = "InteractiveLobeSegmentation Reload"
#        reloadFormLayout.addWidget(self.reloadButton)
#        self.reloadButton.connect('clicked()', self.onReload)
#            
#        # reload and test button
#        # (use this during development, but remove it when delivering
#        #  your module to users)
#        self.reloadAndTestButton = qt.QPushButton("Reload and Test")
#        self.reloadAndTestButton.toolTip = "Reload this module and then run the self tests."
#        reloadFormLayout.addWidget(self.reloadAndTestButton)
#        self.reloadAndTestButton.connect('clicked()', self.onReloadAndTest)


        # Layout selection
        self.layoutCollapsibleButton = ctk.ctkCollapsibleButton()
        self.layoutCollapsibleButton.text = "Layout Selection"
        self.layoutCollapsibleButton.setChecked(False)
        self.layoutCollapsibleButton.setFixedSize(600,40)
        self.layout.addWidget(self.layoutCollapsibleButton, 0, 4)
        self.layoutFormLayout = qt.QFormLayout(self.layoutCollapsibleButton)
        """spacer = ""
          for s in range( 20 ):
          spacer += " """
        #self.fiducialsFormLayout.setFormAlignment(4)
        
        
        self.layoutGroupBox = qt.QFrame()
        self.layoutGroupBox.setLayout(qt.QVBoxLayout())
        self.layoutGroupBox.setFixedHeight(86)
        self.layoutFormLayout.addRow(self.layoutGroupBox)
        
        
        self.buttonGroupBox = qt.QFrame()
        self.buttonGroupBox.setLayout(qt.QHBoxLayout())
        self.layoutGroupBox.layout().addWidget(self.buttonGroupBox)
        #self.layoutFormLayout.addRow(self.buttonGroupBox)
        
        #
        # Four-Up Button
        #
        self.fourUpButton = qt.QPushButton()
        self.fourUpButton.toolTip = "Four-up view."
        self.fourUpButton.enabled = True
        self.fourUpButton.setFixedSize(40,40)
        fourUpIcon = qt.QIcon(":/Icons/LayoutFourUpView.png")
        self.fourUpButton.setIcon(fourUpIcon)
        self.buttonGroupBox.layout().addWidget(self.fourUpButton)
        #
        # Red Slice Button
        #
        self.redViewButton = qt.QPushButton()
        self.redViewButton.toolTip = "Red slice only."
        self.redViewButton.enabled = True
        self.redViewButton.setFixedSize(40,40)
        redIcon = qt.QIcon(":/Icons/LayoutOneUpRedSliceView.png")
        self.redViewButton.setIcon(redIcon)
        self.buttonGroupBox.layout().addWidget(self.redViewButton)
        
        #
        # Yellow Slice Button
        #
        self.yellowViewButton = qt.QPushButton()
        self.yellowViewButton.toolTip = "Yellow slice only."
        self.yellowViewButton.enabled = True
        self.yellowViewButton.setFixedSize(40,40)
        yellowIcon = qt.QIcon(":/Icons/LayoutOneUpYellowSliceView.png")
        self.yellowViewButton.setIcon(yellowIcon)
        self.buttonGroupBox.layout().addWidget(self.yellowViewButton)
        
        #
        # Green Slice Button
        #
        self.greenViewButton = qt.QPushButton()
        self.greenViewButton.toolTip = "Yellow slice only."
        self.greenViewButton.enabled = True
        self.greenViewButton.setFixedSize(40,40)
        greenIcon = qt.QIcon(":/Icons/LayoutOneUpGreenSliceView.png")
        self.greenViewButton.setIcon(greenIcon)
        self.buttonGroupBox.layout().addWidget(self.greenViewButton)
        
        #
        # Buttons labels
        #
        self.labelsGroupBox = qt.QFrame()
        hBox = qt.QHBoxLayout()
        hBox.setSpacing(10)
        self.labelsGroupBox.setLayout(hBox)
        self.labelsGroupBox.setFixedSize(450,26)
        self.layoutGroupBox.layout().addWidget(self.labelsGroupBox,0,4)
        
        fourUpLabel = qt.QLabel("   Four-up")
        #fourUpLabel.setFixedHeight(10)
        self.labelsGroupBox.layout().addWidget(fourUpLabel)
        
        redLabel = qt.QLabel("       Axial")
        self.labelsGroupBox.layout().addWidget(redLabel)
        
        yellowLabel = qt.QLabel("       Saggital")
        self.labelsGroupBox.layout().addWidget(yellowLabel)
        
        greenLabel = qt.QLabel("          Coronal")
        self.labelsGroupBox.layout().addWidget(greenLabel)
        
        
        # Layout connections
        self.fourUpButton.connect('clicked()', self.onFourUpButton)
        self.redViewButton.connect('clicked()', self.onRedViewButton)
        self.yellowViewButton.connect('clicked()', self.onYellowViewButton)
        self.greenViewButton.connect('clicked()', self.onGreenViewButton)
      
        #
        # Create all the widgets. Example Area
        mainAreaCollapsibleButton = ctk.ctkCollapsibleButton()
        mainAreaCollapsibleButton.text = "Main parameters"
        self.layout.addWidget(mainAreaCollapsibleButton)
        # Layout within the dummy collapsible button. See http://doc.qt.io/qt-4.8/layout.html for more info about layouts
        self.mainAreaLayout = qt.QFormLayout(mainAreaCollapsibleButton)

        # Radio Buttons types
        stentTypesLabel = qt.QLabel("Stent type")
        stentTypesLabel.setStyleSheet("font-weight: bold; margin-left:5px")
        self.mainAreaLayout.addWidget(stentTypesLabel)
        self.stentTypesFrame = qt.QFrame()
        self.stentTypesLayout = qt.QHBoxLayout(self.stentTypesFrame)
        self.mainAreaLayout.addWidget(self.stentTypesFrame)
        
        self.stentTypesRadioButtonGroup = qt.QButtonGroup()
        for id,key in enumerate(self.logic.stentTypes):
            print key
            rbitem = qt.QRadioButton(key)
            self.stentTypesRadioButtonGroup.addButton(rbitem, id)
            self.stentTypesLayout.addWidget(rbitem)
        self.stentTypesRadioButtonGroup.buttons()[0].setChecked(True)

        #
        # Fiducials Area
        #

        # Radio Buttons types
        typesLabel = qt.QLabel("Select fiducial type")
        typesLabel.setStyleSheet("font-weight: bold; margin-left:5px")
        self.mainAreaLayout.addWidget(typesLabel)
        self.typesFrame = qt.QFrame()
        self.typesLayout = qt.QHBoxLayout(self.typesFrame)
        self.mainAreaLayout.addWidget(self.typesFrame)

        self.typesRadioButtonGroup = qt.QButtonGroup()
        st = self.logic.stentTypes[self.stentTypesRadioButtonGroup.checkedId()]
        for id,key in enumerate(self.logic.fiducialList[st]):
            rbitem = qt.QRadioButton(key)
            self.typesRadioButtonGroup.addButton(rbitem, id)
            self.typesLayout.addWidget(rbitem)
        self.typesRadioButtonGroup.buttons()[0].setChecked(True)

        self.addFiducialButton = ctk.ctkPushButton()
        self.addFiducialButton.text = "Add new seed"
        self.addFiducialButton.setFixedWidth(100)
        self.addFiducialButton.checkable = True
        self.addFiducialButton.enabled = True
        self.mainAreaLayout.addRow("Stent: ", self.addFiducialButton)

        # Container for the fiducials
        self.fiducialsContainerFrame = qt.QFrame()
        self.fiducialsContainerFrame.setLayout(qt.QVBoxLayout())
        self.mainAreaLayout.addWidget(self.fiducialsContainerFrame)

        # persistent option
        self.persistentCheckBox = qt.QCheckBox()
        self.persistentCheckBox.checkable = True
        self.persistentCheckBox.enabled = True
        self.mainAreaLayout.addRow("Stent model active on exit ",self.persistentCheckBox)
        
        #
        # Apply Button
        #
        self.applyButton = qt.QPushButton("Apply")
        self.applyButton.toolTip = "Run the algorithm."
        self.applyButton.enabled = False
        self.applyButton.setFixedSize(150,45)
        self.layout.addWidget(self.applyButton, 0, 4)
        #self.layout.setAlignment(2)
    
        # connections
        self.applyButton.connect('clicked(bool)', self.onApplyButton)
        self.stentTypesRadioButtonGroup.connect("buttonClicked (QAbstractButton*)", self.onStentTypesRadioButtonClicked)

        self.typesRadioButtonGroup.connect("buttonClicked (QAbstractButton*)", self.onTypesRadioButtonClicked)
        self.addFiducialButton.connect('clicked(bool)',self.onAddFiducialClicked)


    def enter(self):
        """This is invoked every time that we select this module as the active module in Slicer (not only the first time)"""
        #Add stent model to the scene (assuming that there are fiducials)
        pass

    def exit(self):
        """This is invoked every time that we switch to another module (not only when Slicer is closed)."""
        #Remove stent model if persistent-mode is not check (
        pass

    def cleanup(self):
        """This is invoked as a destructor of the GUI when the module is no longer going to be used"""
        pass
    
    
    # Callbacks
    
    def onFourUpButton(self):
        applicationLogic = slicer.app.applicationLogic()
        interactionNode = applicationLogic.GetInteractionNode()
        interactionNode.Reset()
        interactionNode.SwitchToPersistentPlaceMode()
        layoutManager = slicer.app.layoutManager()
        layoutManager.setLayout(3)

    def onRedViewButton(self):
        applicationLogic = slicer.app.applicationLogic()
        interactionNode = applicationLogic.GetInteractionNode()
        interactionNode.Reset()
        interactionNode.SwitchToPersistentPlaceMode()
        layoutManager = slicer.app.layoutManager()
        layoutManager.setLayout(6)

    def onYellowViewButton(self):
        applicationLogic = slicer.app.applicationLogic()
        interactionNode = applicationLogic.GetInteractionNode()
        interactionNode.Reset()
        interactionNode.SwitchToPersistentPlaceMode()
        layoutManager = slicer.app.layoutManager()
        layoutManager.setLayout(7)
      
    def onGreenViewButton(self):
        applicationLogic = slicer.app.applicationLogic()
        interactionNode = applicationLogic.GetInteractionNode()
        interactionNode.Reset()
        interactionNode.SwitchToPersistentPlaceMode()
        layoutManager = slicer.app.layoutManager()
        layoutManager.setLayout(8)
    
    def onStentTypesRadioButtonClicked(self, button):
        # Remove all the existing buttons in TypesGroup
        for b in self.typesRadioButtonGroup.buttons():
            b.hide()
            b.delete()
        # Add all the subtypes with the full description
        st = self.logic.stentTypes[self.stentTypesRadioButtonGroup.checkedId()]
        for id,key in enumerate(self.logic.fiducialList[st]):
            rbitem = qt.QRadioButton(key)
            self.typesRadioButtonGroup.addButton(rbitem, id)
            self.typesLayout.addWidget(rbitem)
            # Check first element by default
        self.typesRadioButtonGroup.buttons()[0].setChecked(True)
    
    def onTypesRadioButtonClicked(self, button):
        """ One of the radio buttons has been pressed
        :param button:
        :return:
        """
          #Do something to update list
        pass

    def onAddFiducialClicked(self, checked):
 
        self.semaphoreOpen = True
        self.__setAddSeedsMode__(checked)

    def __setAddSeedsMode__(self, enabled):
        """ When enabled, the cursor will be enabled to add new fiducials that will be used for the segmentation
          :param enabled:
      :return:
        """
        applicationLogic = slicer.app.applicationLogic()
        interactionNode = applicationLogic.GetInteractionNode()
        if enabled:
            #print("DEBUG: entering __setAddSeedsMode__ - after enabled")
            # Get the fiducials node
            fiducialsNodeList = self.logic.getFiducialsListNode(self.stentTypesRadioButtonGroup.checkedId(),self.typesRadioButtonGroup.checkedId())
            
            print fiducialsNodeList
            # Set the cursor to draw fiducials
            markupsLogic = slicer.modules.markups.logic()
            markupsLogic.SetActiveListID(fiducialsNodeList)
            selectionNode = applicationLogic.GetSelectionNode()
            selectionNode.SetReferenceActivePlaceNodeClassName("vtkMRMLMarkupsFiducialNode")
                
            #print("DEBUG: enabling fiducials again...")
                
            # interactionNode.SwitchToSinglePlaceMode()
            #interactionNode.SetCurrentInteractionMode(1)    # Enable fiducials mode. TODO: NOT WORKING!! (I think because of a event handling problem)


    def onApplyButton(self):
        message = self.logic.printMessage("This is the message that I want to print")
        qt.QMessageBox.information(slicer.util.mainWindow(), 'OK!', 'The test was ok. Review the console for details')

#    def onReload(self,moduleName="VolumeProbe"):
#        """Generic reload method for any scripted module.
#        ModuleWizard will subsitute correct default moduleName.
#        """
#        import imp, sys, os, slicer
#
#        widgetName = moduleName + "Widget"
#
#        # reload the source code
#        # - set source file path
#        # - load the module to the global space
#        filePath = eval('slicer.modules.%s.path' % moduleName.lower())
#        p = os.path.dirname(filePath)
#        if not sys.path.__contains__(p):
#            sys.path.insert(0,p)
#        fp = open(filePath, "r")
#        globals()[moduleName] = imp.load_module(
#            moduleName, fp, filePath, ('.py', 'r', imp.PY_SOURCE))
#        fp.close()
#
#        # rebuild the widget
#        # - find and hide the existing widget
#        # - create a new widget in the existing parent
#        parent = slicer.util.findChildren(name='%s Reload' % moduleName)[0].parent().parent()
#        for child in parent.children():
#            try:
#                child.hide()
#            except AttributeError:
#                pass
#        # Remove spacer items
#        item = parent.layout().itemAt(0)
#        while item:
#            parent.layout().removeItem(item)
#            item = parent.layout().itemAt(0)
#        # create new widget inside existing parent
#        globals()[widgetName.lower()] = eval(
#            'globals()["%s"].%s(parent)' % (moduleName, widgetName))
#        globals()[widgetName.lower()].setup()
#
#    def onReloadAndTest(self,moduleName="VolumeProbe",scenario=None):
#        try:
#            self.onReload()
#            evalString = 'globals()["%s"].%sTest()' % (moduleName, moduleName)
#            tester = eval(evalString)
#            tester.runTest(scenario=scenario)
#        except Exception, e:
#            import traceback
#            traceback.print_exc()
#            qt.QMessageBox.warning(slicer.util.mainWindow(),
#                                   "Reload and Test", 'Exception!\n\n' + str(e) + "\n\nSee Python Console for Stack Trace")

#
# CIP_TracheaStentPlanningLogic
#
class CIP_TracheaStentPlanningLogic(ScriptedLoadableModuleLogic):
    """This class should implement all the actual
    computation done by your module.    The interface
    should be such that other python code can import
    this class and make use of the functionality without
    requiring an instance of the Widget.
    Uses ScriptedLoadableModuleLogic base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    
    """
    
    
    def __init__(self):

        self.line=dict()
        self.tube=dict()
        for tag in ['cl1','cl2','cl3']:
            self.line[tag] = vtk.vtkLineSource()
            self.tube[tag] = vtk.vtkTubeFilter()
            self.tube[tag].SetNumberOfSides(15)
            self.tube[tag].CappingOff()
            self.tube[tag].SidesShareVerticesOff()
            self.tube[tag].SetInputData(self.line[tag].GetOutput())
      
        self.stentTypes = ['TStent','YStent']
        self.fiducialList = dict()
        self.fiducialList['YStent'] = ["Upper","Lower","Middle","Outside"]
        self.fiducialList['TStent'] = ["Upper","Middle","LowerRight","LowerLeft"]
      
        for st in self.stentTypes:
            for fl in self.fiducialList[st]:
                self.__createFiducialsListNode__(st+fl)
    
    def printMessage(self, message):
        print("This is your message: ", message)
        return "I have printed this message: " + message

    def createStentFromFiducials(self):
      #Get fiducial lists and built model
      pass
    def addStentToScene(self):
      #Add current model to scene.
      pass
                                           
    
    def __createFiducialsListNode__(self, fiducialsNodeName, onModifiedCallback=None):
      """ Create a new fiducials list node for the current volume
      :param volumeId: fiducials list will be connected to this volume
      :return: True if the node was created or False if it already existed
      """
      markupsLogic = slicer.modules.markups.logic()
        
      # Check if the node already exists
      #fiducialsNodeName = volumeId + '_fiducialsNode'
      
      fiducialsNode = slicer.util.getNode(fiducialsNodeName)
      if fiducialsNode is not None:
        return False    # Node already created
    
      # Create new fiducials node
      fiducialListNodeID = markupsLogic.AddNewFiducialNode(fiducialsNodeName,slicer.mrmlScene)
      fiducialsNode = slicer.util.getNode(fiducialListNodeID)
      # Make the new fiducials node the active one
      markupsLogic.SetActiveListID(fiducialsNode)
      # Hide any text from all the fiducials
      fiducialsNode.SetMarkupLabelFormat('')
      displayNode = fiducialsNode.GetDisplayNode()
      # displayNode.SetColor([1,0,0])
      displayNode.SetSelectedColor([1,0,0])
      displayNode.SetGlyphScale(4)
      displayNode.SetGlyphType(8)     # Diamond shape (I'm so cool...)
      
      # Add observer when specified
      if onModifiedCallback is not None:
        # The callback function will be invoked when the fiducials node is modified
        fiducialsNode.AddObserver("ModifiedEvent", onModifiedCallback)
      
      # Node created succesfully
      return True


    def getFiducialsListNode(self, st_id,fid_id, onModifiedCallback=None):
      """ Get the current fiducialsListNode for the specified volume, and creates it in case
        it doesn't exist yet.
        :param volumeId: fiducials list will be connected to this volume
        :return: the fiducials node or None if something fails
      """
      markupsLogic = slicer.modules.markups.logic()
        
      # Check if the node already exists
      st = self.stentTypes[st_id]
      ft = self.fiducialList[st][fid_id]
      fiducialsNodeName = st+ft
      
      fiducialsNode = slicer.util.getNode(fiducialsNodeName)
      if fiducialsNode is not None:
        if onModifiedCallback is not None:
          fiducialsNode.AddObserver("ModifiedEvent", onModifiedCallback)
        return fiducialsNode


class CIP_TracheaStentPlanningTest(ScriptedLoadableModuleTest):
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
        self.test_CIP_TracheaStentPlanning_PrintMessage()

    def test_CIP_TracheaStentPlanning_PrintMessage(self):
        self.delayDisplay("Starting the test")
        logic = CIP_TracheaStentPlanningLogic()

        myMessage = "Print this test message in console"
        logging.info("Starting the test with this message: " + myMessage)
        expectedMessage = "I have printed this message: " + myMessage
        logging.info("The expected message would be: " + expectedMessage)
        responseMessage = logic.printMessage(myMessage)
        logging.info("The response message was: " + responseMessage)
        self.assertTrue(responseMessage == expectedMessage)
        self.delayDisplay('Test passed!')
