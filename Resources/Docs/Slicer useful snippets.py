- ScriptedLoadableModuleTemplate ==> class that contains the default template for a new Python module
- slicer.modules.volumes.logic() ==> handle volumes (events, etc.)
- slicer.app.applicationLogic() ==> important applications  general to Slicer
- slicer.app.layoutManager()  ==> general layout operations  (ex: select a different module?)
- node.GetAttribute("LabelMap") == '1'  ==> a volume is a LabelMap

########################################

Create a new scripted module from the template:
cd <Slicer source dir>
./Utilities/Scripts/ModuleWizard.py --template ./Extensions/Testing/ScriptedLoadableExtensionTemplate/ScriptedLoadableModuleTemplate --target ../ModuleFolder ModuleName



- slicer.mrmlScene.AddObserver(slicer.vtkMRMLScene.NodeAddedEvent, self.onNodeAdded)	==> listen to events in the scene. This does NOT return the added node (see "Observe the scene to capture a volume when it is added ")
Note: the "regular" node (volumes and labelmaps) are vtkMRMLScalarVolumeNode

- enter ==> event when entering the module (in the widget)
- exit ==> event when exiting the module (in the widget)

- All the scripted modules inherit from Base/QTGUI/qSlicerScriptedLoadableModule  

####################################################################################
# Create a new volume from scratch
node = slicer.mrmlScene.CreateNodeByClass("vtkMRMLDisplayNode")

# Get node by name
n = slicer.util.getNode("12257B_INSP_STD_UIA_COPD")


slicer.app.layoutManager()

####################################################################################

# NODE SELECTOR (FILTERED BY LABEL MAPS)
self.labelSelector = slicer.qMRMLNodeComboBox()
self.labelSelector.nodeTypes = ( "vtkMRMLScalarVolumeNode", "" )
self.labelSelector.addAttribute( "vtkMRMLScalarVolumeNode", "LabelMap", "1" )
# todo addAttribute
self.labelSelector.selectNodeUponCreation = False
self.labelSelector.addEnabled = False
self.labelSelector.noneEnabled = False
self.labelSelector.removeEnabled = False
self.labelSelector.showHidden = False
self.labelSelector.showChildNodeTypes = False
self.labelSelector.setMRMLScene( slicer.mrmlScene )
self.labelSelector.setToolTip( "Pick the label map to edit" )
self.labelSelectorFrame.layout().addWidget( self.labelSelector )
# Node changed event
self.labelSelectorFrame.connect('currentNodeChanged(vtkMRMLNode*)', self.onVolumeSelected)
def onVolumeSelected(self, node):.....


####################################################################################
# Create new instance of EditorWidget
editorWidgetParent = slicer.qMRMLWidget()
editorWidgetParent.setLayout(qt.QVBoxLayout())
editorWidgetParent.setMRMLScene(slicer.mrmlScene)
editorWidgetParent.hide()
self.editorWidget = EditorWidget(editorWidgetParent, False)
self.editorWidget.setup()



####################################################################################
# Select a volumnenode and a label map as the active nodes in Slicer. Required for example for the Editor
selectionNode = self.applicationLogic.GetSelectionNode()
selectionNode.SetReferenceActiveVolumeID( self.master.GetID() )
selectionNode.SetReferenceActiveLabelVolumeID( merge.GetID() )
self.applicationLogic.PropagateVolumeSelection(0)



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

# IMPORTANT: all these operations must be executed in the __init__ of the Widget
......
slicer.mrmlScene.AddObserver(slicer.vtkMRMLScene.NodeAddedEvent, self.onNodeAdded)




########################################################################
# Capture mouse clicks
self._greenSliceInteractor =
slicer.ApplicationGUI.GetMainSliceGUI("Green").GetSliceViewer().GetRenderWidget().GetRenderWindowInteractor()
self._greenSliceLeftButtonReleaseTag =
self._greenSliceInteractor.AddObserver("LeftButtonReleaseEvent",self._helper.HandleClickInGreenSliceWindow)

########################################################################
# Get numpy array from Scalar node
slicer.util.array(node.GetName())
# Note: If we manipulate the array, the changes will reflect in the vtkNode calling node.GetImageData().Modified()
        



