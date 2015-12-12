import os
import unittest
from __main__ import vtk, qt, ctk, slicer

#
# InteractiveLobeSegmentation
#

class InteractiveLobeSegmentation:
  def __init__(self, parent):
    parent.title = "Interactive Lobe Segmentation" # TODO make this more human readable by adding spaces
    parent.categories = ["Chest Imaging Platform"]
    parent.dependencies = []
    parent.contributors = ["Pietro Nardelli (UCC/SPL) and Applied Chest Imaging Laboratory, Brigham and Women's Hopsital"] 
    parent.helpText = """
    Scripted loadable module for Interactive Lobe segmentation.
    """
    parent.acknowledgementText = """
      This work is funded by the National Heart, Lung, And Blood Institute of the National 
      Institutes of Health under Award Number R01HL116931. The content is solely the responsibility of the authors
      and does not necessarily represent the official views of the National Institutes of Health.
"""
    self.parent = parent

    # Add this test to the SelfTest module's list for discovery when the module
    # is created.  Since this module may be discovered before SelfTests itself,
    # create the list if it doesn't already exist.
    try:
      slicer.selfTests
    except AttributeError:
      slicer.selfTests = {}
    slicer.selfTests['InteractiveLobeSegmentation'] = self.runTest

  def runTest(self):
    tester = InteractiveLobeSegmentationTest()
    tester.runTest()

#
# qInteractiveLobeSegmentationWidget
#

class InteractiveLobeSegmentationWidget:
  def __init__(self, parent = None):
   
    self.logic = InteractiveLobeSegmentationLogic()
    self.observerTags = []
    if not parent:
      self.parent = slicer.qMRMLWidget()
      self.parent.setLayout(qt.QVBoxLayout())
      self.parent.setMRMLScene(slicer.mrmlScene)
    else:
      self.parent = parent
    self.layout = self.parent.layout()
    if not parent:
      self.setup()
      self.parent.show()
    
  def setup(self):
    # Instantiate and connect widgets ...

    #
    # Reload and Test area
    #
    reloadCollapsibleButton = ctk.ctkCollapsibleButton()
    reloadCollapsibleButton.text = "Reload && Test"
    self.layout.addWidget(reloadCollapsibleButton)
    self.layout.setSpacing(6)
    reloadFormLayout = qt.QFormLayout(reloadCollapsibleButton)

    # reload button
    # (use this during development, but remove it when delivering
    #  your module to users)
    self.reloadButton = qt.QPushButton("Reload")
    self.reloadButton.toolTip = "Reload this module."
    self.reloadButton.name = "InteractiveLobeSegmentation Reload"
    reloadFormLayout.addWidget(self.reloadButton)
    self.reloadButton.connect('clicked()', self.onReload)

    # reload and test button
    # (use this during development, but remove it when delivering
    #  your module to users)
    self.reloadAndTestButton = qt.QPushButton("Reload and Test")
    self.reloadAndTestButton.toolTip = "Reload this module and then run the self tests."
    reloadFormLayout.addWidget(self.reloadAndTestButton)
    self.reloadAndTestButton.connect('clicked()', self.onReloadAndTest)

    #
    # Parameters Area
    #
    parametersCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersCollapsibleButton.text = "Parameters"
    self.layout.addWidget(parametersCollapsibleButton)

    # Layout within the dummy collapsible button
    parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)
    parametersFormLayout.setVerticalSpacing(5)

    #
    # first input volume selector
    #

    self.inputSelector1 = slicer.qMRMLNodeComboBox()
    #self.inputSelector1.nodeTypes = ( ("vtkMRMLScalarVolumeNode"), "" )
    #self.inputSelector1.addAttribute( "vtkMRMLScalarVolumeNode", "LabelMap", 1 )
    self.inputSelector1.nodeTypes = ( ("vtkMRMLLabelMapVolumeNode"), "" )
    self.inputSelector1.selectNodeUponCreation = True
    self.inputSelector1.addEnabled = False
    self.inputSelector1.removeEnabled = False
    self.inputSelector1.noneEnabled = False
    self.inputSelector1.showHidden = False
    self.inputSelector1.showChildNodeTypes = False
    self.inputSelector1.setMRMLScene( slicer.mrmlScene )
    self.inputSelector1.setToolTip( "Pick the label map to the algorithm." )
    parametersFormLayout.addRow("Label Map Volume: ", self.inputSelector1)
    #
    # output volume selector
    #

    self.outputSelector = slicer.qMRMLNodeComboBox()
    # self.outputSelector.nodeTypes = ( ("vtkMRMLScalarVolumeNode"), "" )
    # self.outputSelector.addAttribute( "vtkMRMLScalarVolumeNode", "LabelMap", 1 )
    self.outputSelector.nodeTypes = ( ("vtkMRMLLabelMapVolumeNode"), "" )
    self.outputSelector.selectNodeUponCreation = True
    self.outputSelector.addEnabled = True
    self.outputSelector.removeEnabled = True
    self.outputSelector.noneEnabled = True
    self.outputSelector.showHidden = False
    self.outputSelector.showChildNodeTypes = True
    self.outputSelector.setMRMLScene( slicer.mrmlScene )
    self.outputSelector.setToolTip( "Pick the output to the algorithm." )
    parametersFormLayout.addRow("Output Volume: ", self.outputSelector)


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
    # Fiducials Area
    #

    self.groupBox = qt.QFrame()
    self.groupBox.setLayout(qt.QHBoxLayout())
   
    fiducialsCollapsibleButton = ctk.ctkCollapsibleButton()
    fiducialsCollapsibleButton.text = "Fiducials Selection"
    self.layout.addWidget(fiducialsCollapsibleButton)
    self.fiducialsFormLayout = qt.QFormLayout(fiducialsCollapsibleButton)
    self.fiducialsFormLayout.setVerticalSpacing(5)
    self.fiducialsFormLayout.addRow(self.groupBox)


    # Add fiducial lists button
    self.AddLeftListButton = qt.QPushButton("Left oblique fissure")
    self.AddLeftListButton.toolTip = "Create a new fiducial list for the left lung oblique fissure."
    self.AddLeftListButton.setFixedHeight(40)
    self.groupBox.layout().addWidget(self.AddLeftListButton)

    # Add fiducial lists button
    self.AddRight1ListButton = qt.QPushButton("Right oblique fissure")
    self.AddRight1ListButton.toolTip = "Create a new fiducial list for the right lung oblique fissure."
    self.AddRight1ListButton.setFixedHeight(40)
    self.groupBox.layout().addWidget(self.AddRight1ListButton)

    # Add fiducial lists button
    self.AddRight2ListButton = qt.QPushButton("Right horizontal fissure")
    self.AddRight2ListButton.toolTip = "Create a new fiducial list for the right lung horizontal fissure."
    self.AddRight2ListButton.setFixedHeight(40)
    self.groupBox.layout().addWidget(self.AddRight2ListButton)
        
    #
    # Apply Button
    #
    self.applyButton = qt.QPushButton("Apply")
    self.applyButton.toolTip = "Run the algorithm."
    self.applyButton.enabled = False
    self.applyButton.setFixedSize(150,45)
    self.layout.addWidget(self.applyButton, 0, 4)
    #self.layout.setAlignment(2)
         
    #
    # Show Fiducials
    #
    fiducialButtonsList = []
    fiducialButtonsList.append(self.AddLeftListButton)
    fiducialButtonsList.append(self.AddRight1ListButton)
    fiducialButtonsList.append(self.AddRight2ListButton)

    self.visualizationWidget = ILSVisualizationWidget(self.logic, self.applyButton, fiducialButtonsList)
    self.fiducialsFormLayout.addRow(self.visualizationWidget.widget)

    # connections
    self.applyButton.connect('clicked(bool)', self.onApplyButton)
    self.inputSelector1.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.outputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.AddLeftListButton.connect('clicked()', self.onAddLeftListButton)
    self.AddRight1ListButton.connect('clicked()', self.onAddRight1ListButton)
    self.AddRight2ListButton.connect('clicked()', self.onAddRight2ListButton)
   
    self.updateList()
  
    # Add vertical spacer
    self.layout.addStretch(1)

  def cleanup(self):
    pass

  def onSelect(self):
    #self.applyButton.enabled = self.inputSelector.currentNode() and self.inputSelector1.currentNode() and self.outputSelector.currentNode() 
    self.layoutCollapsibleButton.setChecked(True)
    if  self.inputSelector1.currentNode() and (self.outputSelector.currentNode()!= None):
      self.visualizationWidget.enableApplyButton = True

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

    
  def onAddLeftListButton(self):
    #self.applyButton.enabled = self.inputSelector.currentNode() and self.inputSelector1.currentNode() and self.outputSelector.currentNode() 
    self.AddLeftListButton.setStyleSheet("background-color: rgb(255,99,71)")
    self.AddRight1ListButton.setStyleSheet("background-color: rgb(255,255,255)")
    self.AddRight2ListButton.setStyleSheet("background-color: rgb(255,255,255)")
    logic = InteractiveLobeSegmentationLogic() 
    self.logic.name = 'leftObliqueFiducial'
    logic.createList('leftObliqueFiducial') 
   
  def onAddRight1ListButton(self):
    #self.applyButton.enabled = self.inputSelector.currentNode() and self.inputSelector1.currentNode() and self.outputSelector.currentNode() 
    self.AddRight1ListButton.setStyleSheet("background-color: rgb(255,99,71)")
    self.AddLeftListButton.setStyleSheet("background-color: rgb(255,255,255)")
    self.AddRight2ListButton.setStyleSheet("background-color: rgb(255,255,255)")
    logic = InteractiveLobeSegmentationLogic()
    self.logic.name = 'rightObliqueFiducial'
    logic.createList('rightObliqueFiducial')

  def onAddRight2ListButton(self):
    #self.applyButton.enabled = self.inputSelector.currentNode() and self.inputSelector1.currentNode() and self.outputSelector.currentNode() 
    self.AddRight2ListButton.setStyleSheet("background-color: rgb(255,99,71)")
    self.AddLeftListButton.setStyleSheet("background-color: rgb(255,255,255)")
    self.AddRight1ListButton.setStyleSheet("background-color: rgb(255,255,255)")
    logic = InteractiveLobeSegmentationLogic()
    self.logic.name = 'rightHorizontalFiducial'
    logic.createList('rightHorizontalFiducial')    

  def onApplyButton(self):
    self.visualizationWidget.updateScene()
    self.applyButton.enabled = True    
    logic = InteractiveLobeSegmentationLogic()
    print("Run the algorithm")
    try:
       logic.run( self.inputSelector1.currentNode(), self.outputSelector.currentNode() )
    except Exception, e:
      import traceback
      traceback.print_exc()
      qt.QMessageBox.warning(slicer.util.mainWindow(), 
          "Running", 'Exception!\n\n' + str(e) + "\n\nSee Python Console for Stack Trace")
    self.onFourUpButton()
 
  def updateList(self):
    """Observe the mrml scene for changes that we wish to respond to."""    
     
    tag = slicer.mrmlScene.AddObserver(slicer.mrmlScene.EndCloseEvent, self.clearTable)
    tag = slicer.mrmlScene.AddObserver(slicer.mrmlScene.NodeAddedEvent, self.visualizationWidget.requestNodeAddedUpdate)
    self.observerTags.append( (slicer.mrmlScene, tag) )
   
  def clearTable(self,caller,event):
    self.onFourUpButton()
    self.visualizationWidget.tableWidget.clearContents()
    self.visualizationWidget.tableWidget.setRowCount(0)
    self.visualizationWidget.leftRow = 0
    self.visualizationWidget.rightObliqueRow = 0
    self.visualizationWidget.rightHorizontalRow = 0
    self.visualizationWidget.updateScene()
    self.visualizationWidget.fiducialsCollapsibleButton.hide()
    self.visualizationWidget.removeFiducialObservers()   

  def onReload(self,moduleName="InteractiveLobeSegmentation"):
    """Generic reload method for any scripted module.
    ModuleWizard will subsitute correct default moduleName.
    """
    import imp, sys, os, slicer

    widgetName = moduleName + "Widget"

    # reload the source code
    # - set source file path
    # - load the module to the global space
    filePath = eval('slicer.modules.%s.path' % moduleName.lower())
    p = os.path.dirname(filePath)
    if not sys.path.__contains__(p):
      sys.path.insert(0,p)
    fp = open(filePath, "r")
    globals()[moduleName] = imp.load_module(
        moduleName, fp, filePath, ('.py', 'r', imp.PY_SOURCE))
    fp.close()

    # rebuild the widget
    # - find and hide the existing widget
    # - create a new widget in the existing parent
    parent = slicer.util.findChildren(name='%s Reload' % moduleName)[0].parent().parent()
    for child in parent.children():
      try:
        child.hide()
      except AttributeError:
        pass
    # Remove spacer items
    item = parent.layout().itemAt(0)
    while item:
      parent.layout().removeItem(item)
      item = parent.layout().itemAt(0)

    # delete the old widget instance
    if hasattr(globals()['slicer'].modules, widgetName):
      getattr(globals()['slicer'].modules, widgetName).cleanup()

    # create new widget inside existing parent
    globals()[widgetName.lower()] = eval(
        'globals()["%s"].%s(parent)' % (moduleName, widgetName))
    globals()[widgetName.lower()].setup()
    setattr(globals()['slicer'].modules, widgetName, globals()[widgetName.lower()])

  def onReloadAndTest(self,moduleName="InteractiveLobeSegmentation"):
    try:
      self.onReload()
      evalString = 'globals()["%s"].%sTest()' % (moduleName, moduleName)
      tester = eval(evalString)
      tester.runTest()
    except Exception, e:
      import traceback
      traceback.print_exc()
      qt.QMessageBox.warning(slicer.util.mainWindow(), 
          "Reload and Test", 'Exception!\n\n' + str(e) + "\n\nSee Python Console for Stack Trace")


class ILSpqWidget(object):
  """
  A "QWidget"-like widget class that manages provides some
  helper functionality (signals, slots...)
  """
  def __init__(self):
    self.connections = {} # list of slots per signal

  def connect(self,signal,slot):
    """pseudo-connect - signal is arbitrary string and slot if callable"""
    if not self.connections.has_key(signal):
      self.connections[signal] = []
    self.connections[signal].append(slot)

  def disconnect(self,signal,slot):
    """pseudo-disconnect - remove the connection if it exists"""
    if self.connections.has_key(signal):
      if slot in self.connections[signal]:
        self.connections[signal].remove(slot)

  def emit(self,signal,args):
    """pseudo-emit - calls any slots connected to signal"""
    if self.connections.has_key(signal):
      for slot in self.connections[signal]:
        slot(*args)

class ILSVisualizationWidget(ILSpqWidget):
  """
  A "QWidget"-like class that manages some of the viewer options
  used during lobe segmentation
  """
  def __init__(self,logic,applyButton, buttonsList):
    super(ILSVisualizationWidget,self).__init__()
    self.logic = logic
    self.applyButton = applyButton
    self.fiducialButtonsList = buttonsList
    self.enableApplyButton = False
        
    self.widget = qt.QWidget()
    self.layout = qt.QFormLayout(self.widget)
    self.boxHolder = qt.QWidget()
    self.boxHolder.setLayout(qt.QVBoxLayout())
    self.layout.addRow(self.boxHolder)

    self.groupBox = qt.QFrame()
    self.groupBox.setLayout(qt.QHBoxLayout())

    self.fiducialsCollapsibleButton = ctk.ctkCollapsibleButton()
    self.fiducialsCollapsibleButton.text = "Show Fiducials"
    self.fiducialsCollapsibleButton.hide()
    self.fiducialsFormLayout = qt.QFormLayout(self.fiducialsCollapsibleButton)   
     
    # Table Widget Definition
    self.tableWidget = qt.QTableWidget()
    self.tableWidget.sortingEnabled = False 
    self.tableWidget.hide() 
    self.tableWidget.setColumnCount(3)
    self.tableWidget.setColumnWidth(0,190)
    self.tableWidget.setColumnWidth(1,190)
    self.tableWidget.setColumnWidth(2,190)
    self.tableWidget.setMaximumWidth(590)
    horizontalBar = self.tableWidget.horizontalScrollBar()
    horizontalBar.setDisabled(True)
    horizontalBar.hide()
    self.tableWidget.setHorizontalHeaderLabels(["Left Oblique Fiducials","Right Oblique Fiducials","Right Horizontal Fiducials"])
    behavior = qt.QAbstractItemView()
    self.tableWidget.setSelectionBehavior(behavior.SelectItems)
    self.tableWidget.setSelectionMode(behavior.SingleSelection)
    self.tableWidget.setContextMenuPolicy(3)  
    self.tableWidget.customContextMenuRequested.connect(self.onRightClick)
      
    self.groupBox.layout().addWidget(self.tableWidget)

    self.fiducialsFormLayout.addWidget(self.groupBox)
    self.boxHolder.layout().addWidget(self.fiducialsCollapsibleButton)
  
    self.pendingUpdate = False
    self.updatingFiducials = False
    self.observerTags = []

    self.leftRow = 0
    self.rightObliqueRow = 0
    self.rightHorizontalRow = 0
    
    self.tableItems = []
   
    self.deletionGroupBox = qt.QFrame()
    self.deletionGroupBox.setLayout(qt.QHBoxLayout())
    self.fiducialsFormLayout.addWidget(self.deletionGroupBox)  

    #
    # Delete Selected Fiducials Button
    #
    self.deleteButton = qt.QPushButton("Delete Selected Fiducial")
    self.deleteButton.toolTip = "Select a fiducial from the table and push this button to delete the selected fiducial from the scene."
    self.deleteButton.enabled = True  
    selectedIcon = qt.QIcon(":/Icons/MarkupsDelete.png") 
    self.deleteButton.setIcon(selectedIcon)
    self.deleteButton.setFixedSize(220,30)
    self.deletionGroupBox.layout().addWidget(self.deleteButton)
    self.deleteButton.connect('clicked(bool)', self.onDeleteOneFiducialButton)

    #
    # Delete All Fiducials Button
    #
    self.deleteAllButton = qt.QPushButton("Delete All Fiducials")
    self.deleteAllButton.toolTip = "Delete all fiducials in the scene."
    self.deleteAllButton.enabled = True
    allIcon = qt.QIcon(":/Icons/MarkupsDeleteAllRows.png")
    self.deleteAllButton.setIcon(allIcon)
    self.deleteAllButton.setFixedSize(220,30)
    self.deletionGroupBox.layout().addWidget(self.deleteAllButton)
    #self.fiducialsFormLayout.addRow(self.deleteAllButton)  
    self.deleteAllButton.connect('clicked(bool)', self.dialogBoxFunction)  
         
  def onDeleteOneFiducialButton(self):
    selectedItem = self.tableWidget.selectedItems()    
   
    if not selectedItem:
      return
   
    item = selectedItem[0]
    column = item.column()
    row = item.row()

    listsInScene = slicer.util.getNodes('vtkMRMLMarkupsFiducialNode*')
    if not listsInScene:
      return
       
    name = None  
    if column == 0:
      name = 'leftObliqueFiducial'
    elif column == 1:
      name = 'rightObliqueFiducial'
    else:
      name = 'rightHorizontalFiducial'   

    selectedList = None
    for selectedList in listsInScene.values():
      if selectedList.GetName() == name:
        selectedList.RemoveMarkup(row)
        break
            
    if row == self.tableWidget.rowCount -1:
      self.tableWidget.takeItem(row,column)
    else:
      count = self.tableWidget.rowCount - row
      for i in range(1,count):
        currentRow = row + i
        moved = self.tableWidget.takeItem(currentRow,column)
        self.tableWidget.setItem(currentRow-1,column,moved)
    if column == 0:
      self.leftRow -= 1      
    elif column == 1:
      self.rightObliqueRow -= 1
    else:
      self.rightHorizontalRow -= 1    
     
    if self.leftRow >= self.rightObliqueRow and self.leftRow >= self.rightHorizontalRow: 
      self.tableWidget.setRowCount(self.leftRow)
    elif self.rightObliqueRow >= self.leftRow and self.rightObliqueRow >= self.rightHorizontalRow:
      self.tableWidget.setRowCount(self.rightObliqueRow)
    elif self.rightHorizontalRow >= self.leftRow and self.rightHorizontalRow >= self.rightObliqueRow:
      self.tableWidget.setRowCount(self.rightHorizontalRow)
    self.updateScene()

  def onRightClick(self):
    menu = qt.QMenu()
    position = qt.QCursor.pos()     
    action = qt.QAction("Delete highlighted fiducial(s)",menu)  
    menu.addAction(action)
    connectObject = qt.QObject()
    connectObject.connect(action,'triggered()',self.onDeleteOneFiducialButton)
    action2 = qt.QAction("Cancel",menu)
    menu.addAction(action2)
    connectObject.connect(action2,'triggered()',menu.hide)
    menu.exec_(position)
    
  def dialogBoxFunction(self):
    self.deleteAllMsgBox = qt.QDialog(slicer.util.mainWindow())
    #self.deleteAllMsgBox.setWindowTitle("Delete All Fiducials?")
    self.deleteAllMsgBox.setFixedSize(200,100)
    self.deleteAllMsgBox.show()
    self.deleteAllMsgBox.setLayout( qt.QVBoxLayout() )

    messageLabel = qt.QLabel("Delete All Fiducials?")
    font = qt.QFont()
    font.setPointSize(10)
    messageLabel.setFont(font)
    self.deleteAllMsgBox.layout().addWidget(messageLabel,0,4)

    yesNoBox = qt.QFrame()
    yesNoBox.setLayout(qt.QHBoxLayout())
    self.deleteAllMsgBox.layout().addWidget(yesNoBox,0,4)

    #
    # OK button
    # 
    okButton = qt.QPushButton()
    okButton.setText("YES")
    okButton.enabled = True
    okIcon = qt.QIcon(":/Icons/AnnotationOkDone.png")
    okButton.setIcon(okIcon)
    yesNoBox.layout().addWidget(okButton)

    #
    # NO button
    #
    noButton = qt.QPushButton()
    noButton.setText("NO")
    noButton.enabled = True
    noIcon = qt.QIcon(":/Icons/AnnotationCancel.png")
    noButton.setIcon(noIcon)
    yesNoBox.layout().addWidget(noButton)
    
    # Connections
    okButton.connect("clicked()", self.onDeleteAllButton)
    noButton.connect("clicked()", self.deleteAllMsgBox.hide)

  def onDeleteAllButton(self):    
    mrmlScene = slicer.mrmlScene    
    listsInScene = slicer.util.getNodes('vtkMRMLMarkupsFiducialNode*')
    if(listsInScene):
      for oldList in listsInScene.values():
        oldList.RemoveAllMarkups()
        mrmlScene.RemoveNode(oldList)            

    rowCount = self.tableWidget.rowCount
    for i in range(rowCount,-1,-1):
      self.tableWidget.removeRow(i)
    self.leftRow = 0
    self.rightObliqueRow = 0
    self.rightHorizontalRow = 0
    self.updateScene()        
    self.deleteAllMsgBox.hide()
     
  def updateScene(self):
    applicationLogic = slicer.app.applicationLogic()
    interactionNode = applicationLogic.GetInteractionNode()
    interactionNode.Reset()
    self.applyButton.enabled = False
    for i in self.fiducialButtonsList:
      i.setStyleSheet("background-color: rgb(255,255,255)") 
    listsInScene = slicer.util.getNodes('vtkMRMLMarkupsFiducialNode*')
    if(listsInScene):
      mrmlScene = slicer.mrmlScene    
      for oldList in listsInScene.values():
        if oldList.GetName() == 'leftObliqueFiducial':
          if self.leftRow == 0:
            mrmlScene.RemoveNode(oldList)
        if oldList.GetName() == 'rightObliqueFiducial':
          if self.rightObliqueRow == 0:
            mrmlScene.RemoveNode(oldList)   
        if oldList.GetName() == 'rightHorizontalFiducial':
          if self.rightHorizontalRow == 0:
            mrmlScene.RemoveNode(oldList)
    if self.tableWidget.rowCount == 0:
      self.deleteButton.enabled = False
      self.deleteAllButton.enabled = False      
     

  def updateFiducialArray(self):
    """Rebuild the list of buttons based on current landmarks"""
    fiducialsLogic = slicer.modules.markups.logic()
    originalActiveListID = fiducialsLogic.GetActiveListID()
    originalActiveList = slicer.util.getNode(originalActiveListID)

    if originalActiveList:
      if originalActiveList.GetNumberOfFiducials() > 0 :
        self.updateTable()
        if self.enableApplyButton == True:
          self.applyButton.enabled = True
    self.addFiducialObservers()

  def addFiducialObservers(self):
    """Add observers to all fiducialLists in scene
    so we will know when new markups are added
    """
    self.removeFiducialObservers()
    for fiducialList in slicer.util.getNodes('vtkMRMLMarkupsFiducialNode*').values():
      tag = fiducialList.AddObserver(fiducialList.MarkupAddedEvent, self.requestNodeAddedUpdate)
      self.observerTags.append( (fiducialList,tag) )
        
  def removeFiducialObservers(self):
    """Remove any existing observers"""
    for obj,tag in self.observerTags:
      obj.RemoveObserver(tag)
    self.observerTags = []

  def updateTable(self):
    self.fiducialsCollapsibleButton.show()           
    fiducialsLogic = slicer.modules.markups.logic()
    originalActiveListID = fiducialsLogic.GetActiveListID()
    originalActiveList = slicer.util.getNode(originalActiveListID)
    self.tableWidget.show()
    self.deleteButton.enabled = True
    self.deleteAllButton.enabled = True
    
    if originalActiveList.GetName() == 'leftObliqueFiducial': 

      if self.tableWidget.rowCount == 0:
        self.tableWidget.setRowCount(1)
      elif self.leftRow >= self.rightObliqueRow and self.leftRow >= self.rightHorizontalRow: 
        self.tableWidget.setRowCount(self.leftRow + 1)
      elif self.rightObliqueRow > self.leftRow and self.rightObliqueRow > self.rightHorizontalRow:
        self.tableWidget.setRowCount(self.rightObliqueRow)
      elif self.rightHorizontalRow > self.leftRow and self.rightHorizontalRow > self.rightObliqueRow:
        self.tableWidget.setRowCount(self.rightHorizontalRow)
   
      lastElement = originalActiveList.GetNumberOfFiducials() - 1
      item = qt.QTableWidgetItem(originalActiveList.GetNthFiducialLabel(lastElement))
      item.setToolTip(originalActiveList.GetName())
      self.tableItems.append(item)
      self.tableWidget.setItem(self.leftRow,0,item)
      self.leftRow += 1     
      
    elif originalActiveList.GetName() == 'rightObliqueFiducial':

      if self.tableWidget.rowCount == 0:
        self.tableWidget.setRowCount(1)
      elif self.leftRow > self.rightObliqueRow and self.leftRow > self.rightHorizontalRow: 
        self.tableWidget.setRowCount(self.leftRow)
      elif self.rightObliqueRow >= self.leftRow and self.rightObliqueRow >= self.rightHorizontalRow:
        self.tableWidget.setRowCount(self.rightObliqueRow + 1)
      elif self.rightHorizontalRow > self.leftRow and self.rightHorizontalRow > self.rightObliqueRow:
        self.tableWidget.setRowCount(self.rightHorizontalRow)
    
      lastElement = originalActiveList.GetNumberOfFiducials() - 1
      item = qt.QTableWidgetItem(originalActiveList.GetNthFiducialLabel(lastElement))
      item.setToolTip(originalActiveList.GetName())
      self.tableItems.append(item)
      self.tableWidget.setItem(self.rightObliqueRow,1,item)
      self.rightObliqueRow += 1      

    elif originalActiveList.GetName() == 'rightHorizontalFiducial':

      if self.tableWidget.rowCount == 0:
        self.tableWidget.setRowCount(1)
      elif self.leftRow > self.rightObliqueRow and self.leftRow > self.rightHorizontalRow: 
        self.tableWidget.setRowCount(self.leftRow)
      elif self.rightObliqueRow > self.leftRow and self.rightObliqueRow > self.rightHorizontalRow:
        self.tableWidget.setRowCount(self.rightObliqueRow)
      elif self.rightHorizontalRow >= self.leftRow and self.rightHorizontalRow >= self.rightObliqueRow:
        self.tableWidget.setRowCount(self.rightHorizontalRow + 1)
      
      lastElement = originalActiveList.GetNumberOfFiducials() - 1
      item = qt.QTableWidgetItem(originalActiveList.GetNthFiducialLabel(lastElement))
      item.setToolTip(originalActiveList.GetName())
      self.tableItems.append(item)
      self.tableWidget.setItem(self.rightHorizontalRow,2,item)
      self.rightHorizontalRow += 1  
    
  def requestNodeAddedUpdate(self,caller,event):
    """Start a SingleShot timer that will check the fiducials
    in the scene and add them to the list"""
    if not self.pendingUpdate:
      qt.QTimer.singleShot(0, self.wrappedNodeAddedUpdate)
      self.pendingUpdate = True

  def wrappedNodeAddedUpdate(self):
    try:
      self.nodeAddedUpdate()
    except Exception, e:
      import traceback
      traceback.print_exc()
      qt.QMessageBox.warning(slicer.util.mainWindow(),
          "Node Added", 'Exception!\n\n' + str(e) + "\n\nSee Python Console for Stack Trace")

  def nodeAddedUpdate(self):
    """Perform the update of any new fiducials.
    First collect from any fiducial lists not associated with one of our
    lists (like when the process first gets started) and then check for
    new fiducials added to one of our lists.
    End result should be one fiducial per list with identical names and
    correctly assigned associated node ids.
    Most recently created new fiducial is picked as active landmark.
    """
    if self.updatingFiducials:
      return
  
    self.updatingFiducials = True    
    self.logic.ModifyList()    
    self.updateFiducialArray()
    self.pendingUpdate = False
    self.updatingFiducials = False


#
# InteractiveLobeSegmentationLogic
#

class InteractiveLobeSegmentationLogic:
  """This class should implement all the actual 
  computation done by your module.  The interface 
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget
  """
  def __init__(self):
    self.name = "Fiducial"

  def hasImageData(self,volumeNode):
    """This is a dummy logic method that 
    returns true if the passed in volume
    node has valid image data
    """
    if not volumeNode:
      print('no volume node')
      return False
    if volumeNode.GetImageData() == None:
      print('no image data')
      return False
    return True

  def delayDisplay(self,message,msec=1000):
    #
    # logic version of delay display
    #
    print(message)
    self.info = qt.QDialog()
    self.infoLayout = qt.QVBoxLayout()
    self.info.setLayout(self.infoLayout)
    self.label = qt.QLabel(message,self.info)
    self.infoLayout.addWidget(self.label)
    qt.QTimer.singleShot(msec, self.info.close)
    self.info.exec_()


  def createList(self,name):
    """Add an instance of a fiducial to the scene for a given
    volume node.  Creates a new list if needed.
    If list already has a fiducial with the given name, then
    set the position to the passed value.
    """    
    applicationLogic = slicer.app.applicationLogic()
    selectionNode = applicationLogic.GetSelectionNode()
    selectionNode.SetReferenceActivePlaceNodeClassName("vtkMRMLMarkupsFiducialNode")
    interactionNode = applicationLogic.GetInteractionNode()
    interactionNode.SwitchToPersistentPlaceMode()  
    
    fiducialsLogic = slicer.modules.markups.logic()

    listsInScene = slicer.util.getNodes('vtkMRMLMarkupsFiducialNode*')
    createNewList = True
    if(listsInScene):
      for oldList in listsInScene.values():
        if oldList.GetName() == name:
          fiducialsLogic.SetActiveListID(oldList)
          createNewList = False
          break
      if(createNewList):
        fiducialListNodeID = fiducialsLogic.AddNewFiducialNode("Fiducial",slicer.mrmlScene)
        fiducialList = slicer.util.getNode(fiducialListNodeID)
        fiducialsLogic.SetActiveListID(fiducialList)
    else:
      fiducialListNodeID = fiducialsLogic.AddNewFiducialNode("Fiducial",slicer.mrmlScene)
      fiducialList = slicer.util.getNode(fiducialListNodeID)
      fiducialsLogic.SetActiveListID(fiducialList)   

  
  def ModifyList(self):
    """Look at each fiducial list in scene and find any fiducials associated
    with one of our volumes but not in in one of our lists.
    Add the fiducial as a landmark and delete it from the other list.
    Return the name of the last added landmark if it exists.
    """
    fiducialsLogic = slicer.modules.markups.logic()
    originalActiveListID = fiducialsLogic.GetActiveListID() # TODO: naming convention?
    if(slicer.util.getNode(originalActiveListID)):
      fiducialList = slicer.util.getNode(originalActiveListID)
      fiducialList.SetName(self.name)  
      name = self.name    
      fiducialList.SetNthFiducialLabel(0,name+"-1")
    else:
      return

  def run(self,labelVolume,outputVolume):
    """
    Run the actual algorithm
    """           
    listsInScene = slicer.util.getNodes('vtkMRMLMarkupsFiducialNode*')
    leftObliqueFiducials = None
    rightObliqueFiducials = None
    rightHorizontalFiducials = None 

    name = ['leftObliqueFiducial','rightObliqueFiducial','rightHorizontalFiducial']

    if(listsInScene):
      for fiducialList in listsInScene.values():
        if fiducialList.GetName() == name[0]:
          leftObliqueFiducials = fiducialList
        elif fiducialList.GetName() == name[1]:
          rightObliqueFiducials = fiducialList
        elif fiducialList.GetName() == name[2]:
          rightHorizontalFiducials = fiducialList

    lobeSegmentation = slicer.modules.interactivelobesegmentation
    parameters = {
      #"GrayScaleInput": inputVolume.GetID(),
          "inLabelMapFileName": labelVolume.GetID(),
          "outLabelMapFileName": outputVolume.GetID(),	  
          }

    if leftObliqueFiducials:
      parameters["leftObliqueFiducials"] = leftObliqueFiducials
    if rightObliqueFiducials:
      if rightHorizontalFiducials:
        parameters["rightObliqueFiducials"] = rightObliqueFiducials
        parameters["rightHorizontalFiducials"] = rightHorizontalFiducials
      else:
        msgBox = qt.QMessageBox()
        msgBox.setText("Please place fiducials on the right horizontal fissure.")
        msgBox.exec_()
        #print('Please place fiducials on the right horizontal fissure')
        return False
    elif rightHorizontalFiducials:  
      msgBox = qt.QMessageBox()
      msgBox.setText("Please place fiducials on the right oblique fissure.")
      msgBox.setFixedSize(100,50)
      msgBox.exec_()       
      return False

    self.delayDisplay('Running the algorithm')
    slicer.cli.run( slicer.modules.segmentlunglobes,None,parameters,wait_for_completion=True )
    selectionNode = slicer.app.applicationLogic().GetSelectionNode()
    selectionNode.SetReferenceActiveLabelVolumeID(outputVolume.GetID())
    outputVolume.SetName(labelVolume.GetName().replace("_partialLungLabelMap","_iteractiveLobeSegmenation"))
    slicer.app.applicationLogic().PropagateLabelVolumeSelection(0)
    return True

class InteractiveLobeSegmentationTest(unittest.TestCase):
  """
  This is the test case for your scripted module.
  """

  def delayDisplay(self,message,msec=1000):
    """This utility method displays a small dialog and waits.
    This does two things: 1) it lets the event loop catch up
    to the state of the test so that rendering and widget updates
    have all taken place before the test continues and 2) it
    shows the user/developer/tester the state of the test
    so that we'll know when it breaks.
    """
    print(message)
    self.info = qt.QDialog()
    self.infoLayout = qt.QVBoxLayout()
    self.info.setLayout(self.infoLayout)
    self.label = qt.QLabel(message,self.info)
    self.infoLayout.addWidget(self.label)
    qt.QTimer.singleShot(msec, self.info.close)
    self.info.exec_()

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear(0)

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_InteractiveLobeSegmentation1()

  def test_InteractiveLobeSegmentation1(self):
    """ Ideally you should have several levels of tests.  At the lowest level
    tests should exercise the functionality of the logic with different inputs
    (both valid and invalid).  At higher levels your tests should emulate the
    way the user would interact with your code and confirm that it still works
    the way you intended.
    One of the most important features of the tests is that it should alert other
    developers when their changes will have an impact on the behavior of your
    module.  For example, if a developer removes a feature that you depend on,
    your test should break so they know that the feature is needed.
    """

    self.delayDisplay("Starting the test")
    #
    # first, get some data
    #
    import urllib
    downloads = (
        ('http://slicer.kitware.com/midas3/download?items=5767', 'FA.nrrd', slicer.util.loadVolume),
        )

    for url,name,loader in downloads:
      filePath = slicer.app.temporaryPath + '/' + name
      if not os.path.exists(filePath) or os.stat(filePath).st_size == 0:
        print('Requesting download %s from %s...\n' % (name, url))
        urllib.urlretrieve(url, filePath)
      if loader:
        print('Loading %s...\n' % (name,))
        loader(filePath)
    self.delayDisplay('Finished with download and loading\n')

    volumeNode = slicer.util.getNode(pattern="FA")
    logic = InteractiveLobeSegmentationLogic()
    self.assertTrue( logic.hasImageData(volumeNode) )
    self.delayDisplay('Test passed!')
