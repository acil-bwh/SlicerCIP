'''Body Composition is a Slicer module that allows to segment different parts of the lungs in a manual or semi-automatic basis
with the help of a customized Slicer Editor.
It also performs a set of operations to analyze the different structures of
the volume based on its label map, like Area, Mean, Std.Dev., etc.
First version: Jorge Onieva (ACIL, jonieva@bwh.harvard.edu). 11/2014'''

import qt, vtk, ctk, slicer
import numpy as np

from slicer.ScriptedLoadableModule import *

from CIP.logic.SlicerUtil import SlicerUtil
import CIP.ui as CIPUI
from slicer.util import VTKObservationMixin


class CIP_Calibration(ScriptedLoadableModule):
    """Module that allows to segment different parts of the lungs in a manual or semi-automatic basis"""

    def __init__(self, parent):
        """Constructor for main class"""
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "Calibration"
        self.parent.categories = SlicerUtil.CIP_ModulesCategory
        self.parent.dependencies = [SlicerUtil.CIP_ModuleName]
        self.parent.contributors = ["Jorge Onieva (jonieva@bwh.harvard.edu)", "Applied Chest Imaging Laboratory", "Brigham and Women's Hospital"]
        self.parent.helpText = "Calibrate a scan with air and blood"
        self.parent.acknowledgementText = SlicerUtil.ACIL_AcknowledgementText

######################################
# CIP_StructuresDetectionWidget
#######################################
class CIP_CalibrationWidget(ScriptedLoadableModuleWidget,VTKObservationMixin):
    """GUI object"""
    def __init__(self, parent):
        ScriptedLoadableModuleWidget.__init__(self, parent)
        # needed for event observation:
        VTKObservationMixin.__init__(self)  
        self.activeEditorTools = None
        self.inputVolume = None
        self.outputSegmentation = None
        self.labelmapVolumeNode = None
        self.segmentEditorNode = None
        self.segmentEditorWidget = None
        self.logic = None
        self._parameterNode = None
        self._updatingGUIFromParameterNode = False

    @property
    def labelmapNodeNameExtension(self):
        return "calibrationLabelMap"


    ################
    # Main methods
    ################
    def setup(self):
        """Init the widget """
        ScriptedLoadableModuleWidget.setup(self) 

        # creale logic 
        self.logic = CIP_CalibrationLogic()

        ##########
        # Main area
        self.mainAreaCollapsibleButton = ctk.ctkCollapsibleButton()
        self.mainAreaCollapsibleButton.text = "Main area"
        #self.layout.addWidget(self.mainAreaCollapsibleButton, SlicerUtil.ALIGNMENT_VERTICAL_TOP)
        self.layout.addWidget(self.mainAreaCollapsibleButton)
        self.mainLayout = qt.QFormLayout(self.mainAreaCollapsibleButton)

        row = 0

        # Node selector
        volumeLabel = qt.QLabel("Active volume: ")
        volumeLabel.setStyleSheet("margin-left:5px")

        self.volumeSelector = slicer.qMRMLNodeComboBox()
        self.volumeSelector.nodeTypes = ("vtkMRMLScalarVolumeNode", "")
        self.volumeSelector.selectNodeUponCreation = True
        self.volumeSelector.autoFillBackground = True
        self.volumeSelector.addEnabled = False
        self.volumeSelector.noneEnabled = False
        self.volumeSelector.removeEnabled = False
        self.volumeSelector.showHidden = False
        self.volumeSelector.showChildNodeTypes = False
        self.volumeSelector.setMRMLScene(slicer.mrmlScene)
        self.volumeSelector.setMinimumWidth(150)
        self.mainLayout.addRow(volumeLabel, self.volumeSelector)
        self.volumeSelector.connect('currentNodeChanged(vtkMRMLNode*)', self._onMainVolumeChanged_)
        self.inputVolume = self.volumeSelector.currentNode()

        row += 1
        lb = qt.QLabel("Click to select the calibration type and, if needed, modify the HU value expected for that area")
        lb.setStyleSheet("margin:10px 0 10px 5px")
        self.mainLayout.addRow(lb)

        self.typeRadioButtonGroup = qt.QButtonGroup()
        self.typeRadioButtonGroup.connect("buttonClicked (QAbstractButton*)", self.__onTypeRadioButtonClicked__)
        row += 1
        self.rbAir = qt.QRadioButton("Air")
        self.rbAir.setStyleSheet("margin-left:10px; margin-top: 5px")
        self.typeRadioButtonGroup.addButton(self.rbAir, 1)

        self.txtAir = qt.QLineEdit()
        self.txtAir.setText("-1000")
        self.txtAir.setFixedWidth(80)
        self.txtAir.setValidator(qt.QIntValidator())
        self.mainLayout.addRow(self.rbAir, self.txtAir)
        self.rbAir.setChecked(True)

        row += 1
        self.rbBlood = qt.QRadioButton("Blood")
        self.rbBlood.setStyleSheet("margin-left:10px; margin-top: 5px")
        self.typeRadioButtonGroup.addButton(self.rbBlood, 2)

        self.txtBlood = qt.QLineEdit()
        self.txtBlood.setText("50")
        self.txtBlood.setFixedWidth(80)
        self.txtBlood.setValidator(qt.QIntValidator())
        self.mainLayout.addRow(self.rbBlood, self.txtBlood)
        row += 1

        # Create the standard segment editor widget
        self._createSegmentEditorWidget_()

        # Calibrate button
        self.calibrateButton = ctk.ctkPushButton()
        self.calibrateButton.setText("Calibrate")
        self.calibrateButton.toolTip = "Run the calibration"
        self.calibrateButton.setIcon(qt.QIcon("{0}/scale.png".format(SlicerUtil.CIP_ICON_DIR)))
        self.calibrateButton.setIconSize(qt.QSize(20, 20))
        #self.calibrateButton.setFixedWidth(135)
        self.layout.addWidget(self.calibrateButton)
        self.calibrateButton.connect('clicked()', self._onCalibrateButtonClicked_)

        # Reset button
        self.resetButton = ctk.ctkPushButton()
        self.resetButton.setText("Reset")
        self.resetButton.toolTip = "Reset module: Create new empty region segments and reset all parameters."
        self.calibrateButton.setIcon(qt.QIcon("{0}/scale.png".format(SlicerUtil.CIP_ICON_DIR)))
        self.calibrateButton.setIconSize(qt.QSize(20, 20))
        self.layout.addWidget(self.resetButton)
        self.resetButton.connect('clicked()', self._onResetButtonClicked_)

        # Add stretch to align the calibrate button and the layout to the top 
        self.layout.addStretch()

        # Make sure parameter node exists and observed
        self.initializeParameterNode()

        # Connect observers to scene events
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.StartCloseEvent, self.onSceneStartClose)
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndCloseEvent, self.onSceneEndClose)
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndImportEvent, self.onSceneEndImport)

    @property
    def currentVolumeLoaded(self):
        return self.volumeSelector.currentNode()

    @property
    def colorNode(self):
        nodeName =  "{}_colorNode".format(self.moduleName)
        colorTableNode = SlicerUtil.getNode(nodeName)
        if colorTableNode is None:
            colorTableNode = self.logic.createColormapNode(nodeName)
        return colorTableNode

    def checkMasterAndSegmentationNodes(self):
        """Set an appropiate MasterNode Segment to the Segment Editor,"""

        # Select default input nodes if nothing is selected yet to save a few clicks for the user
        if not self.inputVolume:
            firstVolumeNode = slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLScalarVolumeNode")
            if firstVolumeNode:
                self.inputVolume = firstVolumeNode

        if not self.outputSegmentation:
            self.outputSegmentation = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentationNode", self.inputVolume.GetName() + " Lung Calibration")
            self.outputSegmentation.CreateDefaultDisplayNodes()
            segmentationDisplayNode = self.outputSegmentation.GetDisplayNode()
            #segmentationDisplayNode.SetOpacity3D(0.2)
            segmentationDisplayNode.SetOpacity2DFill(0.5)
            segmentationDisplayNode.SetOpacity2DOutline(0.2)


            newSegId = self.outputSegmentation.GetSegmentation().AddEmptySegment("Air")
            newSeg = self.outputSegmentation.GetSegmentation().GetSegment(newSegId)
            newSeg.SetName("Air")
            color=(0, 1.0, 0)
            newSeg.SetColor(color)

            newSegId = self.outputSegmentation.GetSegmentation().AddEmptySegment("Blood")
            newSeg = self.outputSegmentation.GetSegmentation().GetSegment(newSegId)
            newSeg.SetName("Blood")
            color=(1.0, 0, 0)
            newSeg.SetColor(color)
        
        if self.segmentEditorWidget:
            # Set the right volumes
            self.segmentEditorWidget.setSegmentationNode(self.outputSegmentation)
            self.segmentEditorWidget.setMasterVolumeNode(self.inputVolume)
            # Set paint effect
            self.segmentEditorWidget.setActiveEffectByName("Paint")
            effect = self.segmentEditorWidget.activeEffect()
            effect.setParameter("BrushRelativeDiameter","1")
        slicer.app.applicationLogic().FitSliceToAll()

    def setParameterNode(self, inputParameterNode):
        """
        Set and observe parameter node.
        Observation is needed because when the parameter node is changed then the GUI must be updated immediately.
        """
        if inputParameterNode:
          self.logic.setDefaultParameters(inputParameterNode)

        # Unobserve previously selected parameter node and add an observer to the newly selected.
        # Changes of parameter node are observed so that whenever parameters are changed by a script or any other module
        # those are reflected immediately in the GUI.
        if self._parameterNode is not None:
            self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)
        self._parameterNode = inputParameterNode
        if self._parameterNode is not None:
            self.addObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)

        # Initial GUI update
        self.updateGUIFromParameterNode()

    def updateGUIFromParameterNode(self, caller=None, event=None):
        """
        This method is called whenever parameter node is changed.
        The module GUI is updated to show the current state of the parameter node.
        """

        if self._parameterNode is None or self._updatingGUIFromParameterNode:
            return

        # Make sure GUI changes do not call updateParameterNodeFromGUI (it could cause infinite loop)
        self._updatingGUIFromParameterNode = True

        # All the GUI updates are done
        self._updatingGUIFromParameterNode = False


    def initializeParameterNode(self):
        """
        Ensure parameter node exists and observed.
        """
        # Parameter node stores all user choices in parameter values, node selections, etc.
        # so that when the scene is saved and reloaded, these settings are restored.


        self.setParameterNode(self.logic.getParameterNode())


        # Load master nodes
        self.checkMasterAndSegmentationNodes()


    def getCurrentGrayscaleNode(self):
        """Get the grayscale node that is currently active in the widget"""
        return self.volumeSelector.currentNode()

    def setCurrentGrayscaleNode(self, node):
        """Set the grayscale node that is currently active in the widget"""
        self.inputVolume = node
        self.segmentEditorWidget.setMasterVolumeNode(node)

    def setCurrentSegmentation(self, node):
        """Get the segmentation node that is currently active in the widget"""

    def removeOutputSegmentation(self):
        """remove the output segmentation node """
        if self.outputSegmentation:
            slicer.mrmlScene.RemoveNode(self.outputSegmentation)
            self.outputSegmentation = None


    ##############
    # Aux methods
    ##############
    def _onMainVolumeChanged_(self, newVolumeNode):
        """ A volume was changed in the main volume selector
        :param newVolumeNode:
        :return:
        """
        self.inputVolume = newVolumeNode
        self.removeOutputSegmentation()
        self.checkMasterAndSegmentationNodes()

    def _onPreNavigatorLabelmapLoaded_(self, volumeNodeName):
        self.labelmapToBeRemoved = SlicerUtil.getNode(volumeNodeName)

    def _onNavigatorLabelmapLoaded_(self, volumeNode, region, type):
        """When a labelmap is loaded in the CaseNavigator, remove possible preexisting nodes"""
        if self.labelmapToBeRemoved:
            slicer.mrmlScene.RemoveNode(self.labelmapToBeRemoved)
            self.labelmapToBeRemoved = None
        self.checkMasterAndSegmentationNodes()

    def _createSegmentEditorWidget_(self):
        """Create and initialize a customize Slicer Editor which contains just some the tools that we need for the segmentation"""
        import qSlicerSegmentationsModuleWidgetsPythonQt
        # Segment editor area
        self.segmentEditorAreaCollapsibleButton = ctk.ctkCollapsibleButton()
        self.segmentEditorAreaCollapsibleButton.text = "Segment editor"
        self.layout.addWidget(self.segmentEditorAreaCollapsibleButton, SlicerUtil.ALIGNMENT_VERTICAL_TOP)
        self.segmentEditorLayout = qt.QFormLayout(self.segmentEditorAreaCollapsibleButton)

        if not self.segmentEditorWidget:
            self.segmentEditorWidget = qSlicerSegmentationsModuleWidgetsPythonQt.qMRMLSegmentEditorWidget()
        self.segmentEditorWidget.setMaximumNumberOfUndoStates(10)
        self.segmentEditorWidget.setMRMLScene(slicer.mrmlScene)
        self.segmentEditorWidget.unorderedEffectsVisible = False
        self.segmentEditorWidget.setEffectNameOrder(['Paint', 'Draw', 'Erase', 'Scissors'])
        if not self.segmentEditorNode:
            self.segmentEditorNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentEditorNode")
        self.segmentEditorNode.SetSingletonTag("CIP_Calibration")
        self.segmentEditorWidget.setMRMLSegmentEditorNode(self.segmentEditorNode)
        self.segmentEditorWidget.setMasterVolumeNodeSelectorVisible(False)
        self.segmentEditorWidget.setSegmentationNodeSelectorVisible(False)
        self.segmentEditorWidget.setSwitchToSegmentationsButtonVisible(False)
        self.segmentEditorWidget.findChild( 'ctkMenuButton', 'Show3DButton' ).hide()
        self.segmentEditorWidget.findChild( 'QPushButton', 'AddSegmentButton' ).hide()
        self.segmentEditorWidget.findChild( 'QPushButton', 'RemoveSegmentButton' ).hide()
        self.segmentEditorWidget.show()
        self.segmentEditorLayout.addWidget(self.segmentEditorWidget)       

    def _onCalibrateButtonClicked_(self):
        """ The calibrate button has been pressed"""

        self.labelmapVolumeNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLLabelMapVolumeNode")
        slicer.modules.segmentations.logic().ExportAllSegmentsToLabelmapNode(self.outputSegmentation, self.labelmapVolumeNode, slicer.vtkSegmentation.EXTENT_REFERENCE_GEOMETRY)
        error = self.logic.calibrate(self.inputVolume, self.labelmapVolumeNode, int(self.txtAir.text), int(self.txtBlood.text))
        slicer.mrmlScene.RemoveNode(self.labelmapVolumeNode)
        self.labelmapVolumeNode = None
        if error:
            slicer.util.warningDisplay(error)
        else:
            slicer.util.infoDisplay("Calibration completed")

    def _onResetButtonClicked_(self):
        """ The reset button has been pressed"""
        if self.outputSegmentation:
            slicer.mrmlScene.RemoveNode(self.outputSegmentation)
            self.outputSegmentation = None
        # Load master nodes
        self.checkMasterAndSegmentationNodes()
        self.txtAir.setText("-1000")
        self.txtBlood.setText("50")

        slicer.util.infoDisplay("Module reset complete.")

    #########
    # Events
    #########

 
    def enter(self):
        """Method that is invoked when we switch to the module in slicer user interface"""

        # Make sure parameter node exists and observed
        self.initializeParameterNode()

    def __onTypeRadioButtonClicked__(self, button):
        """ One of the radio buttons has been pressed
        :param button:
        :return:
        """
        self.segmentEditorNode.SetSelectedSegmentID(button.text)
    
    def onSceneStartClose(self, caller, event):
        """
        Called just before the scene is closed.
        """
        self.inputVolume = None
        if self.outputSegmentation:
            slicer.mrmlScene.RemoveNode(self.outputSegmentation)
            self.outputSegmentation = None
 
    def onSceneEndClose(self, caller, event):
        """
        Called just before the scene is closed.
        """
        if self.parent.isEntered:
            self.initializeParameterNode()

    def onSceneEndImport(self, caller, event):
        """
        Called when a scene has been imported.
        """
        #self.checkMasterAndSegmentationNodes()

    def exit(self):
        """
        Called each time the user opens a different module.
        """
        # Do not react to parameter node changes (GUI wlil be updated when the user enters into the module)
        self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)

    def cleanup(self):
        """
        Called when the application closes and the module widget is destroyed.
        """
        self.removeObservers()

        self.inputVolume = None
        if self.segmentEditorNode: 
            slicer.mrmlScene.RemoveNode(self.segmentEditorNode)
            self.segmentEditorNode = None
        if self.outputSegmentation:
            slicer.mrmlScene.RemoveNode(self.outputSegmentation)
            self.outputSegmentation = None
        if self.labelmapVolumeNode:
            slicer.mrmlScene.RemoveNode(self.labelmapVolumeNode)
            self.labelmapVolumeNode = None
        pass

# CIP_StructuresDetectionLogic
# This class makes all the operations not related with the user interface (download and handle volumes, etc.)
#
class CIP_CalibrationLogic(ScriptedLoadableModuleLogic):
    def __init__(self):
        """Constructor. """
        ScriptedLoadableModuleLogic.__init__(self)

    def setDefaultParameters(self, parameterNode):
        """
        Initialize parameter node with default settings.
        """

    def createColormapNode(self, nodeName):
        """
        Create a new colormap node for the editor
        @param nodeName:
        """
        colorNode = SlicerUtil.createNewColormapNode(nodeName, numberOfColors=3)
        colorNode.SetColor(0, "Background", 0, 0, 0, 0)
        colorNode.SetColor(1, "Air", 0, 1.0, 0)
        colorNode.SetColor(2, "Blood", 1.0, 0, 0)
        return colorNode

    def calibrate(self, scalarNode, labelmapNode, air_output, blood_output):
        """
        Calibrate the volume. Take the mean value of each region marked and rescale the volume to the values
        specified by air_output and blood_output
        @param scalarNode: MRML Scalar node to be calibrated
        @param labelmapNode: MRML labelmap node
        @param air_output: value expecte  for air
        @param blood_output: value expected for blood
        @return: error message if something goes wrong, or None if everything works fine
        """
        s = slicer.util.array(scalarNode.GetName())
        lm = slicer.util.array(labelmapNode.GetName())

        mask = lm == 1
        if not np.any(mask):
            return "Please mark some area corresponding to air in the volume"
        air_input = np.mean(s[mask])

        mask = lm == 2
        if not np.any(mask):
            return "Please mark some area corresponding to blood in the volume"
        blood_input = np.mean(s[mask])

        # Find the line that passes through these points
        d = float(blood_input - air_input)
        if d == 0:
            # Prevent overflow
            d = 0.0000001
        m = (blood_output - air_output) / d
        b = air_output - (m * air_input)

        # Adjust the CT
        a2 = s * m + b
        a2 = a2.astype(np.int16)
        slicer.util.updateVolumeFromArray(scalarNode, a2)



    @staticmethod
    def normalize_CT_image_intensity(image_array, min_value=-300, max_value=700, min_output=0.0, max_output=1.0,
                                     inplace=True):
        """
        Threshold and adjust contrast range in a CT image.
        :param image_array: int numpy array (CT or partial CT image)
        :param min_value: int. Min threshold (everything below that value will be thresholded). If None, ignore
        :param max_value: int. Max threshold (everything below that value will be thresholded). If None, ignore
        :param min_output: float. Min output value
        :param max_output: float. Max output value
        :return: None if in_place==True. Otherwise, float numpy array with adapted intensity
        """
        clip = min_value is not None or max_value is not None
        if min_value is None:
            min_value = np.min(image_array)
        if max_value is None:
            max_value = np.max(image_array)
        if clip:
            np.clip(image_array, min_value, max_value, image_array)

        if inplace and image_array.dtype != np.float32:
            raise Exception(
                "The image array must contain float32 elements, because the transformation will be performed in place")
        if not inplace:
            # Copy the array!
            image_array = image_array.astype(np.float32)

        # Change of range
        image_array -= min_value
        image_array /= (max_value - min_value)
        image_array *= (max_output - min_output)
        image_array += min_output
        if not inplace:
            return image_array
