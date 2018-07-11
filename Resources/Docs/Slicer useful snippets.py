MAIN CLASSES:

- Slicer/Base/Python/slicer/util.py ==> very useful class to load volumes and other common operations (import as slicer.util)
- vtk.util ==> convert vtk in numpy and viceversa  (see also CIP_/CIP/Util)

- ScriptedLoadableModuleTemplate ==> class that contains the default template for a new Python module
- slicer.modules.volumes.logic() ==> handle volumes (events, etc.)
- slicer.vtkSlicerVolumesLogic() ==> more volumes handeling 
- slicer.app.applicationLogic() ==> important applications general to Slicer
- slicer.app.layoutManager()  ==> general layout operations  (ex: select a different module?)
- slicer.modules.volumerendering.logic() ==> many utilites for 3D 3rendering

- SlicerCIP/CIP_/CIP/SlicerUtil ==> some common utils for Slicer (expected to be extended in the future)
- SlicerCIP/CIP_/CIP/Util ==> common utils specially fot volume handling: VTK<=>numpy, save nodes


Some useful snippets: http://wiki.slicer.org/slicerWiki/index.php/Documentation/Nightly/Developers/Python_scripting
####################################################################################
- All the scripted modules inherit from Base/QTGUI/qSlicerScriptedLoadableModule. 
- Every scripted module should have:
	- Class named like the module
	- Class_widget ==> gui components
	- Class_logic ==> class logic (optional). Shouldn't use any componentes from the gui
	- Class_tests ==> testing class (optional). Tests that could be run from Slicer in runtime.

- enter ==> event when entering the module (in the widget)
- exit ==> event when exiting the module (in the widget)
- cleanup ==> free resources, stop listening to events, etc.

####################################################################################
Node types:

- vtkMRMLScalarVolumeNode: "raw" data
- vtkImageData: "geometrical information" associated with the rendering.  To get it: scalarNode.GetImageData() 

- slicer.util.loadVolume(path) ==> load a regular volume
- slicer.util.loadLabelVolume(path) ==> load a labelmap volume

- slicer.util.saveNode(node, path) ==> save a node

# Is the volume a labelmap?
- node.GetAttribute("LabelMap") == '1'  
Note: the "regular" node (both volumes and labelmaps) are vtkMRMLScalarVolumeNode

- node = slicer.util.getNode(nodeName) ==> get a node loaded in the scene with its name
- node = slicer.mrmlScene.GetNodeByID(id) ==> get a node loaded in the scene with its internal id
- nodes = slicer.mrmlScene.GetNodesByClass('vtkMRMLScalarVolumeNode') ==> get all the nodes of type vtkMRMLScalarVolumeNode
	- to iterate over the nodes:
		nodes.InitTraversal()
		n = nodes.GetNextItemAsObject()  or n = nodes.GetItemAsObject(0)   (this would return an object of type vtkMRMLScalarVolumeNode)

####################################################################################
NUMPY / VTK
- slicer.util.array(node.GetName())  ==> create a numpy array that is bound to the node (the changes in the array will can be updated in the node )
	- to refresh the changes in the user interface: 
      - node.GetImageData().Modified()
      - SlicerUtil.refreshActiveWindows()   # custom method that repaints all the visible windows

####################################################################################



# General mechanism to listen to the events in a node or in the Slicer scene
- slicer.mrmlScene.AddObserver(slicer.vtkMRMLScene.NodeAddedEvent, self.onNodeAdded)	==> listen to events in the scene. This does NOT return the added node (see "Observe the scene to capture a volume when it is added ")


####################################################################################


# Create a new volume from scratch (adding it to the scene automatically)
node = slicer.mrmlScene.CreateNodeByClass("vtkMRMLDisplayNode")
slicer.mrmlScene.AddNode(node)
# or
#node =  slicer.vtkSlicerVolumesLogic().

# Get node by name (also valid with id)
n = slicer.util.getNode("12257B_INSP_STD_UIA_COPD")

####################################################################################
# Clone a volume
vl = slicer.modules.volumes.logic()
newvol = vl.CloneVolume(slicer.mrmlScene, node, "myNode")

####################################################################################

# NODE SELECTOR (FILTERED BY LABEL MAPS)
self.volumeSelector = slicer.qMRMLNodeComboBox()
self.volumeSelector.nodeTypes = ( "vtkMRMLScalarVolumeNode", "" )
#self.volumeSelector.addAttribute( "vtkMRMLScalarVolumeNode", "LabelMap", "1" )  deprecated. use new vtkMRMLLabelMapVolumeNode type

self.volumeSelector.selectNodeUponCreation = False
self.volumeSelector.addEnabled = False
self.volumeSelector.noneEnabled = False
self.volumeSelector.removeEnabled = False
self.volumeSelector.showHidden = False
self.volumeSelector.showChildNodeTypes = False
self.volumeSelector.setMRMLScene( slicer.mrmlScene )
self.volumeSelector.setToolTip( "Pick the label map to edit" )
self.volumeSelectorFrame.layout().addWidget( self.volumeSelector )
....
self.volumeSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.onVolumeSelected)
...
selectedNode = self.volumeSelector.currentNode()
self.volumeSelector.setCurrentNode(node) or setCurrentNodeID(volumeId)
####################################################################################
# Select a volumnenode and a label map as the active nodes in Slicer through a selectionNode. Required for example for the Editor
selectionNode = slicer.app.applicationLogic().GetSelectionNode()
selectionNode.SetReferenceActiveVolumeID( self.master.GetID() )
selectionNode.SetReferenceActiveLabelVolumeID( merge.GetID() )
slicer.app.applicationLogic().PropagateVolumeSelection(0)
# IMPORTANT: the layer is the type of node (background, foreground, labelmap). We can use a particular method like appLogic.PropagateForegroundVolumeSelection()

NOTE: selectionNode can be used not only for volumes, but also for fiducials, ROIs, etc.


####################################################################################
#  use the Red slice composite node to define the active volumes """
count = slicer.mrmlScene.GetNumberOfNodesByClass('vtkMRMLSliceCompositeNode')
for n in xrange(count):
	compNode = slicer.mrmlScene.GetNthNodeByClass(n, 'vtkMRMLSliceCompositeNode')
if compNode.GetLayoutName() == layoutName:
	return compNode

Note: vtkMRMLSliceCompositeNode has:
	- BackgroundVolumeID: vtkMRMLScalarVolumeNode2
  	- ForegroundVolumeID: (none)
  	- LabelVolumeID: vtkMRMLScalarVolumeNode4



 ########################################################################
 # Clone a volume.
 	- Direct (will keep the same name and added directly to the scene)
 		slicer.mrmlScene.CopyNode(labelMapNode)
 	- "Manual":
		logic = slicer.vtkSlicerVolumesLogic()
		labelMapNode = slicer.util.getNode("10270J_INSP_STD_JHU_COPD_bodyComposition")
		labelMapCopyNode = logic.CloneVolume(labelMapNode, "Copy_10270J_INSP_STD_JHU_COPD_bodyComposition") 



########################################################################
# Invoke a Python sentence from C++:
slicer.app.pythonManager().executeString("slicer.util.openAddDICOMDialog()")

########################################################################
# Observe the scene to capture a volume when it is added 
from functools import partial
def onNodeAdded(self, caller, eventId, callData):
  """Node added to the Slicer scene"""
  if callData.GetClassName() == 'vtkMRMLAnnotationSnapshotNode':    # (Generally vtkMRMLScalarVolumeNode)
    self.__onNodeAdded__(callData)

self.onNodeAdded = partial(onNodeAdded, self)
self.onNodeAdded.CallDataType = vtk.VTK_OBJECT

#####################################################
# Capture the scene closed event
slicer.mrmlScene.AddObserver(slicer.vtkMRMLScene.EndCloseEvent, self.__onSceneClosed__)
...
def __onSceneClosed__(self, arg1, arg2):
  ...


# IMPORTANT: all these operations must be executed in the __init__ of the Widget
......
slicer.mrmlScene.AddObserver(slicer.vtkMRMLScene.NodeAddedEvent, self.onNodeAdded)


#####################################################
# Open a file for reading
with open(self.csvFilePath, 'r+b') as csvfileReader:
  text = csvfileReader.read()

# Open a file for writing
with open(self.csvFilePath, 'a+b') as csvfile:
  csvfile.write("This is what I write")
  
########################################################################
# Handle user events (mouse, keyboard...)

layoutManager = slicer.app.layoutManager()
sliceNodeCount = slicer.mrmlScene.GetNumberOfNodesByClass('vtkMRMLSliceNode')
for nodeIndex in xrange(sliceNodeCount):
  # find the widget for each node in scene
  sliceNode = slicer.mrmlScene.GetNthNodeByClass(nodeIndex, 'vtkMRMLSliceNode')
  sliceWidget = layoutManager.sliceWidget(sliceNode.GetLayoutName())
  if sliceWidget:
    # add obserservers and keep track of tags
    interactor = sliceWidget.sliceView().interactor()
    self.sliceWidgetsPerStyle[style] = sliceWidget
    events = ("MouseMoveEvent", "EnterEvent", "LeaveEvent")
    # See http://www.vtk.org/doc/release/5.0/html/a01252.html for a complete list of VTK events
    for event in events:
      tag = interactor.AddObserver(event, self.processEvent, self.priority)
      self.observerTags.append([interactor,tag])
    tag = sliceNode.AddObserver("ModifiedEvent", self.processEvent, self.priority)
    self.observerTags.append([sliceNode,tag])
    sliceLogic = sliceWidget.sliceLogic()
    compositeNode = sliceLogic.GetSliceCompositeNode()
    tag = compositeNode.AddObserver("ModifiedEvent", self.processEvent, self.priority)
    self.observerTags.append([compositeNode,tag])

# To get the position of the mouse in a left click:
def f(obj, event):
    pos = (interactor.GetLastEventPosition())
    volumePos = sliceNode.GetXYToRAS().MultiplyPoint(pos + (0, 1))

interactor.AddObserver(vtk.vtkCommand.LeftButtonPressEvent, f)



########################################################################
# Make a batch of changes in the scene and trigger just one event
slicer.mrmlScene.StartState(slicer.mrmlScene.BatchProcessState)
...
...
slicer.mrmlScene.EndState(slicer.mrmlScene.BatchProcessState)  => triggers EndBatchProcessEvent 

########################################################################
# Work with fiducials
vtkMRMLMarkupsFiducialNode --> node type that stores fiducials
markupsLogic = slicer.modules.markups.logic()

# Add new fiducials node
fiducialListNodeID = markupsLogic.AddNewFiducialNode(nodeName,slicer.mrmlScene)
fiducialList = slicer.util.getNode(fiducialListNodeID)

# Add fiducial
position = (-6, 2.5, 100) --> RAS coordinates
index = fiducialList.AddFiducial(*position)
index = fiducialsNode.AddFiducial(-6, 103, -204.5, 'otro')		--> alternative


# Modify fiducial
fiducialsNode.SetNthMarkupVisibility(1, False)  --> hide fiducial

# Get/set active node that will contain the fiducials 
originalActiveListID = markupsLogic.GetActiveListID()
markupsLogic.SetActiveListID(fiducialList)

# Modify visual properties of the fiducials set (example)
displayNode = fiducialList.GetDisplayNode()
displayNode.SetTextScale(6.)
displayNode.SetGlyphScale(6.)
displayNode.SetGlyphTypeFromString('StarBurst2D')
displayNode.SetSelectedColor((1,1,0)) # Enabled fiducials (default)
displayNode.SetColor((1,1,0.4))   # Disabled fiducials
displayNode.SetVisibility(True)

fiducialList.SetAttribute("AssociatedNodeID", associatedNode.GetID()) ???

# Get the position of a fiducial
pos = [0,0,0]
activeNode = markupsLogic.GetActiveListID()
activeNode.GetNthFiducialPosition(0, pos) ==> it stores in pos the RAS coordinates

# Position the 2D windows in a fiducial:
logic.JumpSlicesToNthPointInMarkup(fiducialsNode.GetID(), 0, True)


####################################################################################
# Set the cursor to draw fiducials
# This functionaluty has been encapsulated in the SlicerUtil  "setFiducialMode" method
 def setFiducialsMode(isFiducialsMode, keepFiducialsModeOn=False):
        """ Activate fiducials mode.
        When activateFiducials==True, the mouse cursor will be ready to add fiducials. Also, if
        keepFiducialsModeOn==True, then the cursor will be still in Fiducials mode until we deactivate it by
        calling setFiducialsMode with activateFiducials=False
        :param isFiducialsMode: True for "fiducials mode". False for a regular use
        :param keepFiducialsModeOn: when True, we can add an unlimited number of fiducials. Otherwise after adding the
        first fiducial we will come back to the regular state
        """
        applicationLogic = slicer.app.applicationLogic()
        selectionNode = applicationLogic.GetSelectionNode()
        selectionNode.SetReferenceActivePlaceNodeClassName("vtkMRMLMarkupsFiducialNode")
        interactionNode = applicationLogic.GetInteractionNode()
        if isFiducialsMode:
            # Mouse cursor --> fiducials
            interactionNode.SetCurrentInteractionMode(1)
            # Persistence depending on if we to keep fiducials (or just one)
            interactionNode.SetPlaceModePersistence(keepFiducialsModeOn)
        else:
            # Regular cursor
            interactionNode.SetCurrentInteractionMode(2)
            interactionNode.SetPlaceModePersistence(False)

####################################################################################
# Capture fiducials events
fidListNode.AddObserver(fidNode.MarkupAddedEvent, self.onMarkupAdded)
...
def onMarkupAdded(self, markupListNode, event):
    # Get the last added markup (there is no index in the event!)
    n = markupListNode.GetNumberOfFiducials()
    # Change the label of the last added node
    markupListNode.SetNthMarkupLabel(n-1, label)

# NOTE: see some very useful event handling here: https://github.com/pieper/LandmarkRegistration/blob/master/RegistrationLib/Landmarks.py#L77-L115


####################################################################################
# XYZ --> RAS (in a ROI). Extracted from SlicerLongitudinalPETCTModuleViewHelper in LongitudinalPETCT Module. There are another useful functions there
def getROIPositionInRAS(roi):
    xyz = [0.,0.,0.]
    if roi:
      roi.GetXYZ(xyz)
      
      xyz = [xyz[0],xyz[1],xyz[2],1.0]
      
      roiTransform = roi.GetParentTransformNode()
      
      if roiTransform:
        matrix = vtk.vtkMatrix4x4()
        roiTransform.GetMatrixTransformToWorld(matrix)
        
        xyz = matrix.MultiplyDoublePoint(xyz)
      
      xyz = [xyz[0],xyz[1],xyz[2]]  
            
    return xyz  


####################################################################################
# RAS --> IJK (XYZ). Working with current slice in Axial 
layoutManager = slicer.app.layoutManager()
redWidget = layoutManager.sliceWidget('Red')
redNodeSliceNode = redWidget.sliceLogic().GetSliceNode()
scalarVolumeNode = ...
#redNodeSliceNode = redWidget.sliceLogic().GetLabelLayer().GetSliceNode()	# Working with the labelmap (optional)
# Get the current slice in RAS coordinates
rasSliceOffset = redNodeSliceNode.GetSliceOffset()
# Get the RAS to IJK transformation matrix to convert RAS-->IJK coordinates
transformationMatrix=vtk.vtkMatrix4x4()
scalarVolumeNode.GetRASToIJKMatrix(transformationMatrix)
# Get the K coordinate (slice number in IJK coordinate)
sliceK = transformationMatrix.MultiplyPoint([0,0,rasSliceOffset,1])[2]

# Alternative way: through sliceWidget.sliceView, but it doesn't seem to work well



####################################################################################
# Show a popup message in the main window
qt.QMessageBox.warning(slicer.util.mainWindow(), 'My Warning', 'This is a warning message')      
              #.information, etc.

####################################################################################
# Print debug messages in console (general, not Python one)
import logging
logging.info('This is an info message')


####################################################################################
# Create new instance of EditorWidget
editorWidgetParent = slicer.qMRMLWidget()
editorWidgetParent.setLayout(qt.QVBoxLayout())
editorWidgetParent.setMRMLScene(slicer.mrmlScene)
editorWidgetParent.hide()
self.editorWidget = EditorWidget(editorWidgetParent, False)
self.editorWidget.setup()

####################################################################################
# Go to a specific module
m = slicer.util.mainWindow() 
m.moduleSelector().selectModule('ModelMaker')


###
# Iterate over the different 2D windows  and change opacity
nodes = slicer.mrmlScene.GetNodesByClass("vtkMRMLSliceCompositeNode")  
# Call necessary to allow the iteration.
nodes.InitTraversal()
# Get the first CompositeNode (typically Red)
compositeNode = nodes.GetNextItemAsObject()    

# Link the nodes by default
while compositeNode:
    compositeNode.SetLinkedControl(True)
    compositeNode.SetLabelOpacity(0.5)        # In order the structures are visible
    compositeNode = nodes.GetNextItemAsObject()

####################################################################################
# WORKING WITH CLIs

# Call the CLI
parameters = {"command": command}
module = slicer.modules.executesystemcommand
self.commandLineModuleNode = slicer.cli.run(module, None, parameters, wait_for_completion=False)

# Get the result
self.commandLineModuleNode.AddObserver('ModifiedEvent', self.__onExecuteCommandCLIStateUpdated__)
...
def __onExecuteCommandCLIStateUpdated__(self, caller, event):
   if caller.IsA('vtkMRMLCommandLineModuleNode'):
    if caller.GetStatusString() == "Completed":
        # IMPORTANT: this is not necessarily executed just once!
        print("CLI Process complete")
        # If you want to get some output values:
        myOutputParam = self.commandLineModuleNode.GetParameterDefault(0,1)   # Get the parameter 1 in the group 0
    elif caller.GetStatusString() == "Completed with errors":
        # IMPORTANT: this is not necessarily executed just once!
        print("CLI Process FAILED")
       

# In order that parameter/s output works, we should do this in the CLI:
include <fstream>
....
std::ofstream writeFile (returnParameterFile.c_str());
writeFile << "output = " << valueThatIWantToReturn << std::endl;
writeFile.close();


####################################################################################
# Camera node selector
cameraNodeSelector = slicer.qMRMLNodeComboBox()
cameraNodeSelector.objectName = 'cameraNodeSelector'
cameraNodeSelector.toolTip = "Select a camera that will fly along this path."
cameraNodeSelector.nodeTypes = ['vtkMRMLCameraNode']
cameraNodeSelector.noneEnabled = False
cameraNodeSelector.addEnabled = False
cameraNodeSelector.removeEnabled = False
cameraNodeSelector.connect('currentNodeChanged(bool)', self.enableOrDisableCreateButton)
cameraNodeSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.setCameraNode)
pathFormLayout.addRow("Camera:", cameraNodeSelector)
self.parent.connect('mrmlSceneChanged(vtkMRMLScene*)',
                    cameraNodeSelector, 'setMRMLScene(vtkMRMLScene*)')


####################################################################
# Getting cursor position
widget = slicer.app.layoutManager().sliceWidget('Red')
interactor = widget.interactorStyle().GetInteractor()
crosshairNode=slicer.util.getNode('Crosshair')

from CIP.logic.SlicerUtil import SlicerUtil
from CIP.logic import Util
v = SlicerUtil.getFirstScalarNode()
def f(arg1, arg2):
    coords = [0,0, 0]
    crosshairNode.GetCursorPositionRAS(coords)
    print "RAS: ", coords
    print "Converted:", Util.ras_to_ijk(v, coords)

interactor.AddObserver("LeftButtonPressEvent", f)

