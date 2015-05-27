'''
Created on Sep 29, 2014

@author: Jorge Onieva (Brigham and Women's Hospital)
'''
from __main__ import qt, slicer, vtk
from Editor import EditorWidget
from . import CIP_EditBox
 
class CIP_EditorWidget(EditorWidget):
  """Customized Slicer Editor which contains just some the tools that we need for the lung segmentation"""

  def __init__(self, parent=None, showVolumesFrame=True, activeTools=("DefaultTool", "PaintEffect", "DrawEffect", "LevelTracingEffect", "RectangleEffect", "EraseLabel", "PreviousCheckPoint", "NextCheckPoint")):
    """Constructor. Just invokes the parent's constructor"""     
    self.activeTools = activeTools
#       if str(type(parent)).find("qSlicerScriptedLoadableModuleWidget") != -1:      
    EditorWidget.__init__(self, parent, showVolumesFrame)
#       elif slicer.app.settings().value('Developer/DeveloperMode').lower() == 'true':
#           print("ACIL_EdiotrWidget not initialized")

  def createEditBox(self):
    """Override the parent's method. Builds the editor with a limited set of tools"""
    self.editBoxFrame = qt.QFrame(self.effectsToolsFrame)
    self.editBoxFrame.objectName = 'EditBoxFrame'
    self.editBoxFrame.setLayout(qt.QVBoxLayout())
    self.effectsToolsFrame.layout().addWidget(self.editBoxFrame)
    self.toolsBox = CIP_EditBox.CIP_EditBox(self.activeTools, self.editBoxFrame, optionsFrame=self.effectOptionsFrame)
    
  def setThresholds(self, min, max):
    """Set the threshold for all the allowed effects"""
    self.toolsBox.setThresholds(min, max)