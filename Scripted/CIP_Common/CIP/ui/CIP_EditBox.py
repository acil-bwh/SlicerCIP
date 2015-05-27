'''
Created on Sep 29, 2014

@author: Jorge Onieva
'''
from __main__ import qt, slicer
#import EditorLib
from EditorLib import EditUtil, EditBox

class CIP_EditBox(EditBox):
    '''
    classdocs
    '''
    def __init__(self, activeTools, parent=None, optionsFrame=None):
      """Constructor. Just invokes the parent's constructor"""
      self.activeTools = activeTools
      EditBox.__init__(self, parent, optionsFrame)
      
    def create(self):     
      """Overriden from the parent. Called in init method. Similar to parent's one but restricting the available options"""      
      # the buttons      
      self.rowFrames = []
      self.actions = {}
      self.buttons = {}
      self.icons = {}
      self.callbacks = {}
            
      self.findEffects()      

      self.mainFrame = qt.QFrame(self.parent)
      self.mainFrame.objectName = 'MainFrame'
      vbox = qt.QVBoxLayout()
      self.mainFrame.setLayout(vbox)
      self.parent.layout().addWidget(self.mainFrame)
  
      # create all of the buttons that are going to be used 
      #self.createButtonRow( ("DefaultTool", "PaintEffect", "DrawEffect", "LevelTracingEffect", "RectangleEffect", "EraseLabel", "PreviousCheckPoint", "NextCheckPoint") )
      self.createButtonRow(self.activeTools)
      
      #self.createButtonRow( ("PreviousCheckPoint", "NextCheckPoint"), rowLabel="Undo/Redo: " )
  
      #
      # the labels
      #
      self.toolsActiveToolFrame = qt.QFrame(self.parent)
      self.toolsActiveToolFrame.setLayout(qt.QHBoxLayout())
      self.parent.layout().addWidget(self.toolsActiveToolFrame)
      self.toolsActiveTool = qt.QLabel(self.toolsActiveToolFrame)
      self.toolsActiveTool.setText( 'Active Tool:' )
      self.toolsActiveTool.setStyleSheet("background-color: rgb(232,230,235)")
      self.toolsActiveToolFrame.layout().addWidget(self.toolsActiveTool)
      self.toolsActiveToolName = qt.QLabel(self.toolsActiveToolFrame)
      self.toolsActiveToolName.setText( '' )
      self.toolsActiveToolName.setStyleSheet("background-color: rgb(232,230,235)")
      self.toolsActiveToolFrame.layout().addWidget(self.toolsActiveToolName)
  
      #vbox.addStretch(1)
  
      self.updateUndoRedoButtons()
      
      self.setDefaultParams()
   
    def setDefaultParams(self):
      """Configure here all the required params for any LabelEffect (Paint, Draw, ect.)"""
      self.editUtil = EditUtil.EditUtil()
      self.parameterNode = self.editUtil.getParameterNode()
      
      self.parameterNode.SetParameter("LabelEffect,paintOver", "1") # Enable paintOver
      self.parameterNode.SetParameter("LabelEffect,paintThreshold", "1")   # Enable Threshold checkbox
   
      
    def setThresholds(self, min, max):
      """Set the threshold for all the allowed effects"""
      self.parameterNode.SetParameter("LabelEffect,paintThreshold", "1") 
      self.parameterNode.SetParameter("LabelEffect,paintThresholdMin", str(min))
      self.parameterNode.SetParameter("LabelEffect,paintThresholdMax", str(max))
      

      