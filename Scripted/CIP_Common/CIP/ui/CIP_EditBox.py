'''
Created on Sep 29, 2014

@author: Jorge Onieva
'''
from __main__ import qt, slicer
from EditorLib.EditUtil import EditUtil
from EditorLib import EditBox


class CIP_EditBox(EditBox):
    '''
    classdocs
    '''

    def __init__(self, activeTools, parent=None, optionsFrame=None):
        """Constructor. Just invokes the parent's constructor"""
        self.activeTools = activeTools
        EditBox.__init__(self, parent, optionsFrame)

    def create(self):
        self.findEffects()

        self.mainFrame = qt.QFrame(self.parent)
        self.mainFrame.objectName = 'MainFrame'
        vbox = qt.QVBoxLayout()
        self.mainFrame.setLayout(vbox)
        self.parent.layout().addWidget(self.mainFrame)

        #
        # the buttons
        #
        self.rowFrames = []
        self.actions = {}
        self.buttons = {}
        self.icons = {}
        self.callbacks = {}

        # create all of the buttons (restricted version from the original)
        self.createButtonRow(self.activeTools)
        # # createButtonRow() ensures that only effects in self.effects are exposed,
        # self.createButtonRow( ("DefaultTool", "EraseLabel", "PaintEffect", "DrawEffect", "WandEffect", "LevelTracingEffect", "RectangleEffect", "IdentifyIslandsEffect", "ChangeIslandEffect", "RemoveIslandsEffect", "SaveIslandEffect") )
        # self.createButtonRow( ("ErodeEffect", "DilateEffect", "GrowCutEffect", "WatershedFromMarkerEffect", "ThresholdEffect", "ChangeLabelEffect", "MakeModelEffect", "FastMarchingEffect") )

        extensions = []
        for k in slicer.modules.editorExtensions:
            extensions.append(k)
        self.createButtonRow(extensions)

        # self.createButtonRow( ("PreviousCheckPoint", "NextCheckPoint"), rowLabel="Undo/Redo: " )

        #
        # the labels
        #
        self.toolsActiveToolFrame = qt.QFrame(self.parent)
        self.toolsActiveToolFrame.setLayout(qt.QHBoxLayout())
        self.parent.layout().addWidget(self.toolsActiveToolFrame)
        self.toolsActiveTool = qt.QLabel(self.toolsActiveToolFrame)
        self.toolsActiveTool.setText('Active Tool:')
        self.toolsActiveTool.setStyleSheet("background-color: rgb(232,230,235)")
        self.toolsActiveToolFrame.layout().addWidget(self.toolsActiveTool)
        self.toolsActiveToolName = qt.QLabel(self.toolsActiveToolFrame)
        self.toolsActiveToolName.setText('')
        self.toolsActiveToolName.setStyleSheet("background-color: rgb(232,230,235)")
        self.toolsActiveToolFrame.layout().addWidget(self.toolsActiveToolName)

        vbox.addStretch(1)

        self.setDefaultParams()

        self.updateUndoRedoButtons()
        self._onParameterNodeModified(EditUtil.getParameterNode())

    def setDefaultParams(self):
        """Configure here all the required params for any LabelEffect (Paint, Draw, ect.)"""
        # self.editUtil = EditUtil()
        self.parameterNode = EditUtil.getParameterNode()

        self.parameterNode.SetParameter("LabelEffect,paintOver", "1")  # Enable paintOver
        self.parameterNode.SetParameter("LabelEffect,paintThreshold", "1")  # Enable Threshold checkbox
        self.parameterNode.SetParameter("PaintEffect,radius", "5")

    def setThresholds(self, min, max):
        """Set the threshold for all the allowed effects"""
        self.parameterNode.SetParameter("LabelEffect,paintThreshold", "1")
        self.parameterNode.SetParameter("LabelEffect,paintThresholdMin", str(min))
        self.parameterNode.SetParameter("LabelEffect,paintThresholdMax", str(max))
