import os
import unittest
from __main__ import vtk, qt, ctk, slicer
#import slicer.modules.ChestImagingPlatform
#
# LungRegistration
#

class LungRegistration:
  def __init__(self, parent):
    parent.title = "LungRegistration" # TODO make this more human readable by adding spaces
    parent.categories = ["Chest Imaging Platform"]
    parent.dependencies = []
    parent.contributors = ["Jean-Christophe Fillion-Robin (Kitware), Steve Pieper (Isomics)"] # replace with "Firstname Lastname (Org)"
    parent.helpText = """
    This is an example of scripted loadable module bundled in an extension.
    """
    parent.acknowledgementText = """
    This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc. and Steve Pieper, Isomics, Inc.  and was partially funded by NIH grant 3P41RR013218-12S1.
""" # replace with organization, grant and thanks.
    self.parent = parent

    # Add this test to the SelfTest module's list for discovery when the module
    # is created.  Since this module may be discovered before SelfTests itself,
    # create the list if it doesn't already exist.
    try:
      slicer.selfTests
    except AttributeError:
      slicer.selfTests = {}
    slicer.selfTests['LungRegistration'] = self.runTest

  def runTest(self):
    tester = LungRegistrationTest()
    tester.runTest()

#
# qLungRegistrationWidget
#

class LungRegistrationWidget:
  def __init__(self, parent = None):
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
    reloadFormLayout = qt.QFormLayout(reloadCollapsibleButton)

    # reload button
    # (use this during development, but remove it when delivering
    #  your module to users)
    self.reloadButton = qt.QPushButton("Reload")
    self.reloadButton.toolTip = "Reload this module."
    self.reloadButton.name = "LungRegistration Reload"
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

    #
    # input .vtk selector
    #
    self.inputVTKSelector = slicer.qMRMLNodeComboBox()
    self.inputVTKSelector.nodeTypes = ( ("vtkMRMLModelNode"), "" )
    self.inputVTKSelector.selectNodeUponCreation = True
    self.inputVTKSelector.addEnabled = False
    self.inputVTKSelector.removeEnabled = False
    self.inputVTKSelector.noneEnabled = False
    self.inputVTKSelector.showHidden = False
    self.inputVTKSelector.showChildNodeTypes = False
    self.inputVTKSelector.setMRMLScene( slicer.mrmlScene )
    self.inputVTKSelector.setToolTip( "Pick the input convex hull to the algorithm." )
    parametersFormLayout.addRow("Input .vtk atlas convex hull: ", self.inputVTKSelector)    
        
    #input CT image selector
    self.inputSelector = slicer.qMRMLNodeComboBox()
    self.inputSelector.nodeTypes = ( ("vtkMRMLScalarVolumeNode"), "" )
    #self.inputSelector.addAttribute( "vtkMRMLScalarVolumeNode", "LabelMap", 0 )
    self.inputSelector.selectNodeUponCreation = True
    self.inputSelector.addEnabled = False
    self.inputSelector.removeEnabled = False
    self.inputSelector.noneEnabled = False
    self.inputSelector.showHidden = False
    self.inputSelector.showChildNodeTypes = False
    self.inputSelector.setMRMLScene( slicer.mrmlScene )
    self.inputSelector.setToolTip( "Pick the input to the algorithm." )
    parametersFormLayout.addRow("Input volume: ", self.inputSelector)
    
    
    ##
    ## atlas volume selector
    ##
    self.atlasSelector = slicer.qMRMLNodeComboBox()
    self.atlasSelector.nodeTypes = ( ("vtkMRMLScalarVolumeNode"), "" )
    #self.leftAtlasSelector.addAttribute( "vtkMRMLScalarVolumeNode", "LabelMap", 1 )
    self.atlasSelector.selectNodeUponCreation = True
    self.atlasSelector.addEnabled = False
    self.atlasSelector.removeEnabled = False
    self.atlasSelector.noneEnabled = False
    self.atlasSelector.showHidden = False
    self.atlasSelector.showChildNodeTypes = False
    self.atlasSelector.setMRMLScene( slicer.mrmlScene )
    self.atlasSelector.setToolTip( "Pick the atlas volume." )
    parametersFormLayout.addRow("Atlas Volume: ", self.atlasSelector)
    #
    ##
    ## right atlas volume selector
    ##
    #self.rightAtlasSelector = slicer.qMRMLNodeComboBox()
    #self.rightAtlasSelector.nodeTypes = ( ("vtkMRMLScalarVolumeNode"), "" )
    ##self.rightAtlasSelector.addAttribute( "vtkMRMLScalarVolumeNode", "LabelMap", 2 )
    #self.rightAtlasSelector.selectNodeUponCreation = True
    #self.rightAtlasSelector.addEnabled = False
    #self.rightAtlasSelector.removeEnabled = False
    #self.rightAtlasSelector.noneEnabled = False
    #self.rightAtlasSelector.showHidden = False
    #self.rightAtlasSelector.showChildNodeTypes = False
    #self.rightAtlasSelector.setMRMLScene( slicer.mrmlScene )
    #self.rightAtlasSelector.setToolTip( "Pick the atlas volume." )
    #parametersFormLayout.addRow("right Atlas Volume: ", self.rightAtlasSelector)
    

            
                    
    #
    # output volume selector
    #
    self.outputSelector = slicer.qMRMLNodeComboBox()
    self.outputSelector.nodeTypes = ( ("vtkMRMLScalarVolumeNode"), "" )
    self.outputSelector.addAttribute( "vtkMRMLScalarVolumeNode", "LabelMap", 0 )
    self.outputSelector.selectNodeUponCreation = False
    self.outputSelector.addEnabled = True
    self.outputSelector.removeEnabled = True
    self.outputSelector.noneEnabled = False
    self.outputSelector.showHidden = False
    self.outputSelector.showChildNodeTypes = False
    self.outputSelector.setMRMLScene( slicer.mrmlScene )
    self.outputSelector.setToolTip( "Pick the output to the algorithm." )
    parametersFormLayout.addRow("Output Volume: ", self.outputSelector)
    
    
    #Add parameters:
    self.numberOfIterations = qt.QSpinBox()    
    self.numberOfIterations.setRange(1,1000000) 
    self.numberOfIterations.setValue(200)
    self.numberOfIterations.setToolTip( "Specify the number of iterations to find the transformation." )
    parametersFormLayout.addRow("Number of iterations (Registration part): ", self.numberOfIterations)
    
    self.boneThreshold = qt.QSpinBox()    
    self.boneThreshold.setRange(1,1000000) 
    self.boneThreshold.setValue(600)
    self.boneThreshold.setToolTip( "Threshold value for bone. Any voxel having HU intensity greater than or equal to this value will be considered bone and will be added to the fixed point set.." )
    parametersFormLayout.addRow("Threshold value for bone (Registration part): ", self.boneThreshold)    
    
    #
    # Apply Button
    #
    self.applyButton = qt.QPushButton("Register")
    self.applyButton.toolTip = "Run the registration algorithm."
    self.applyButton.enabled = False
    parametersFormLayout.addRow(self.applyButton)


    # connections
    self.applyButton.connect('clicked(bool)', self.onApplyButton)
    self.inputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.outputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.inputVTKSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.atlasSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.boneThreshold.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    #self.rightAtlasSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect) 
    #self.outModel.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect) 
    #self.numberOfIterations.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect) 
    
    # Add vertical spacer
    self.layout.addStretch(1)

  def cleanup(self):
    pass

  def onSelect(self):
    self.applyButton.enabled = self.outputSelector.currentNode() 

  def onApplyButton(self):
    logic = LungRegistrationLogic()
    print("Run the algorithm")
    #logic.run(self.inputSelector.currentNode(), self.leftAtlasSelector.currentNode(), self.rightAtlasSelector.currentNode(),"~/TestConvexHull.vtk", self.numberOfIterations, self.outModel)
    logic.run(self.inputSelector.currentNode(), self.atlasSelector.currentNode(),self.inputVTKSelector.currentNode(), self.numberOfIterations, self.boneThreshold,self.outputSelector.currentNode())

####need to specify output type for resample

  def onReload(self,moduleName="LungRegistration"):
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

  def onReloadAndTest(self,moduleName="LungRegistration"):
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


#
# LungRegistrationLogic
#

class LungRegistrationLogic:
  """This class should implement all the actual 
  computation done by your module.  The interface 
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget
  """
  def __init__(self):
    pass

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



  def run(self,inputVolume,atlasVolume, convexHullVolume, numIterations, boneThreshold, outVolume):
    """
    Run the actual algorithm
    """
    print('In Run method')
    
    """
    Generate Atlas convex Hull
    """
        
    #convexHullVolume = "~/TestConvexHull.vtk"
    #cliparameters = {
    #"leftAtlasFileName" : leftAtlasVolume.GetID(),
    #"rightAtlasFileName" : rightAtlasVolume.GetID(),
    #"downsampleFactor" : 4,  
    #"outputFileName" : outModel.GetID(), #"~/TestConvexHull.vtk",   *** should be a vtk file  
    #}
    #GenerateAtlasConvexHull = slicer.modules.generateatlasconvexhull
    #slicer.cli.run(GenerateAtlasConvexHull,None, cliparameters, wait_for_completion=True)
    
    
    
    #C:\ChestImagingPlatformPrivate\Build\bin\Debug>RegisterLungAtlas -i 200 -m D:/Po
    # stdoc/Data/LungAtlases/atlasConvexHull.vtk -c  D:/Postdoc/Data/10360K/10360Kinsp
    # .nhdr -o d:/Postdoc/Data/10360K/AtlasTo10360Kinsp.tfm

    #"""
    #Call RegisterLungAtlas cli, tfm intermediate file ?
    #"""
    
    #Define temporary .tfm file
    f = qt.QTemporaryFile( slicer.app.temporaryPath+ "/RegisterLungAtlas-XXXXXX.tfm") #slicer.app.temporaryPath
    f.open() # Create the file
     
    # Get model node by ID
    modelNode = slicer.mrmlScene.GetNodeByID(convexHullVolume.GetID())
    polyData = modelNode.GetPolyData()
    
    cliparameters = {}
    cliparameters['convexHullMeshFileName'] = convexHullVolume.GetID() #modelNode.GetID() #""/Users/rolaharmouche/Documents/Data/LungAtlases/atlasConvexHull.vtk" #
    cliparameters['numberOfIterations'] =  numIterations.value
    cliparameters['boneThreshold'] =  boneThreshold.value
    cliparameters['outputTransformFileName'] = f.fileName()#"/Users/rolaharmouche/Documents/Data/tempdata/Test6.tfm" #outputTransform, slicer.app.temporarypath
    cliparameters['ctFileName'] = inputVolume.GetID()  

    #cliparameters['ctFileName'] = "/Users/rolaharmouche/Documents/Data/COPDGene/14988Y/14988Y_INSP_STD_UAB_COPD/14988Y_INSP_STD_UAB_COPD_downsampled.nrrd"

    #destructor delete stuff
    
    RegisterLungAtlas = slicer.modules.registerlungatlas
    cliNode = slicer.cli.run(RegisterLungAtlas,None, cliparameters, wait_for_completion=True)

    #"""
    #Call ResampleLabelMap cli, save the output volume directly
    #"""
    ##ResampleLabelMap.exe -d D:/Postdoc/Data/10360K/10360Kinsp.nhdr -r D:/Postdoc/Data/10360K/10360KleftAtlas.nrrd -t 
    ##D:/Postdoc/Data/10360K/AtlasTo10360Kinsp.tfm -l D:/Postdoc/Data/LungAtlases/leftLungAtlas.nhdr
    #
    
    cliparameters = {}
    cliparameters['labelMapFileName'] = atlasVolume.GetID() # "/Users/rolaharmouche/Documents/Data/LungAtlases/leftLungAtlas.nhdr"
    cliparameters['transformFileName'] = f.fileName()#"/Users/rolaharmouche/Documents/Data/tempdata/Test6.tfm"
    cliparameters['resampledFileName'] =  outVolume.GetID() #"~/Test.nrrd"  # 
    cliparameters['destinationFileName'] = inputVolume.GetID()  #"/Users/rolaharmouche/Documents/Data/COPDGene/14988Y/14988Y_INSP_STD_UAB_COPD/14988Y_INSP_STD_UAB_COPD_downsampled.nrrd"
    cliparameters['isInvertTransformation']  =True
    ResampleLabelMap = slicer.modules.resamplelabelmap
    cliNode = slicer.cli.run(ResampleLabelMap,None, cliparameters, wait_for_completion=True), #use qt assistant
    
    return True


class LungRegistrationTest(unittest.TestCase):
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
    self.test_LungRegistration1()

  def test_LungRegistration1(self):
    """ Ideally you should have several levels of tests.  At the lowest level
    tests sould exercise the functionality of the logic with different inputs
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
    logic = LungRegistrationLogic()
    self.assertTrue( logic.hasImageData(volumeNode) )
    self.delayDisplay('Test passed!')
