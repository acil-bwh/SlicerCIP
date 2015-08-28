import os
import unittest
from __main__ import vtk, qt, ctk, slicer
import cip_python.segmentation.pectoralis_segmentor as pectoralis_segmentor
import numpy as np ##temporary for debugging
from vtk.util import numpy_support as VN
# PectoralisSegmentation
#

class PectoralisSegmentation:
  def __init__(self, parent):
    parent.title = "PectoralisSegmentation" # TODO make this more human readable by adding spaces
    parent.categories = ["Chest Imaging Platform"]
    parent.dependencies = []
    parent.contributors = ["Applied Chest Imaging Laboratory, Brigham and Women's Hopsital"] # replace with "Firstname Lastname (Org)"
    parent.helpText = """
    This is an example of scripted loadable module bundled in an extension.
    """
    parent.acknowledgementText = """
       This work is funded by the National Heart, Lung, And Blood Institute of the National Institutes of Health under Award Number R01HL116931. The content is solely the responsibility of the authors and does not necessarily represent the official views of the National Institutes of Health.
""" # replace with organization, grant and thanks.
    self.parent = parent

    # Add this test to the SelfTest module's list for discovery when the module
    # is created.  Since this module may be discovered before SelfTests itself,
    # create the list if it doesn't already exist.
    try:
      slicer.selfTests
    except AttributeError:
      slicer.selfTests = {}
    slicer.selfTests['PectoralisSegmentation'] = self.runTest

  def runTest(self):
    tester = PectoralisSegmentationTest()
    tester.runTest()

#
# qPectoralisSegmentationWidget
#

class PectoralisSegmentationWidget:
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

    # reload buttonino
    # (use this during development, but remove it when delivering
    #  your module to users)
    self.reloadButton = qt.QPushButton("Reload")
    self.reloadButton.toolTip = "Reload this module."
    self.reloadButton.name = "PectoralisSegmentation Reload"
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
    # input volume selector
    #
    self.inputSelector = slicer.qMRMLNodeComboBox()
    self.inputSelector.nodeTypes = ( ("vtkMRMLScalarVolumeNode"), "" )
    self.inputSelector.selectNodeUponCreation = True
    self.inputSelector.addEnabled = False
    self.inputSelector.removeEnabled = False
    self.inputSelector.noneEnabled = False
    self.inputSelector.showHidden = False
    self.inputSelector.showChildNodeTypes = False
    self.inputSelector.setMRMLScene( slicer.mrmlScene )
    self.inputSelector.setToolTip( "Pick the input to the algorithm." )
    parametersFormLayout.addRow("Input Volume: ", self.inputSelector)
    
      
    #
    # output segmentation selector
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

    #text file with all the labelmaps
      #self.labelMapFileSelector = qt.QFileDialog()
        #label_file = self.labelMapFileSelector.getOpenFileNames(
        #                            self.labelMapFileSelector,
        #                            "Select files to open",
        #                            "/home",
      #                            "text (*.txt)");
      #text = str(combobox1.currentText())

      #parametersFormLayout.addRow("Text file with labelmap names: ", self.labelMapFileSelector)
      
      
    self.descriptionEdit = qt.QLineEdit("/Users/rolaharmouche/Documents/Caselists/INSP_STD_PECS_training_atlas_filename.txt")
    parametersFormLayout.addRow("Training Labelmaps file name:", self.descriptionEdit)
    #Add parameters:
      
    self.similarityThreshold = qt.QDoubleSpinBox()
    self.similarityThreshold.setRange(0,1)
    self.similarityThreshold.setSingleStep(0.1)
    self.similarityThreshold.setValue(1)
    self.similarityThreshold.setToolTip( "Maximum NCC similarity value to include." )
    parametersFormLayout.addRow("Maximum NCC similarity value to include: ", self.similarityThreshold)
      

    self.numTrainingLabels = qt.QSpinBox()
    self.numTrainingLabels.setRange(1,100)
    self.numTrainingLabels.setValue(10)
    self.numTrainingLabels.setToolTip( "Specify the number of training labels used to build the atlas." )
    parametersFormLayout.addRow("Number of labels for atlas generation: ", self.numTrainingLabels)

   
    #
    # Apply Button
    #
    self.applyButton = qt.QPushButton("Segment")
    self.applyButton.toolTip = "Run the segmentation algorithm."
    self.applyButton.enabled = False
    parametersFormLayout.addRow(self.applyButton)

    # connections
    self.applyButton.connect('clicked(bool)', self.onApplyButton)
    self.inputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.outputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)

    # Add vertical spacer
    self.layout.addStretch(1)

  def cleanup(self):
    pass

  def onSelect(self):
    self.applyButton.enabled = self.inputSelector.currentNode() and self.outputSelector.currentNode() 

  def onApplyButton(self):
    print(self.descriptionEdit.text)
    logic = PectoralisSegmentationLogic()
    print("Run the algorithm")
    logic.run(self.inputSelector.currentNode(), self.outputSelector.currentNode(), self.descriptionEdit.text)

  def onReload(self,moduleName="PectoralisSegmentation"):
    """Generic reload method for any scripted module.
    ModuleWizard will subsitute correct default moduleName.
    """
    globals()[moduleName] = slicer.util.reloadScriptedModule(moduleName)

  def onReloadAndTest(self,moduleName="PectoralisSegmentation"):
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
# PectoralisSegmentationLogic
#

class PectoralisSegmentationLogic:
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

  def takeScreenshot(self,name,description,type=-1):
    # show the message even if not taking a screen shot
    self.delayDisplay(description)

    if self.enableScreenshots == 0:
      return

    lm = slicer.app.layoutManager()
    # switch on the type to get the requested window
    widget = 0
    if type == -1:
      # full window
      widget = slicer.util.mainWindow()
    elif type == slicer.qMRMLScreenShotDialog().FullLayout:
      # full layout
      widget = lm.viewport()
    elif type == slicer.qMRMLScreenShotDialog().ThreeD:
      # just the 3D window
      widget = lm.threeDWidget(0).threeDView()
    elif type == slicer.qMRMLScreenShotDialog().Red:
      # red slice window
      widget = lm.sliceWidget("Red")
    elif type == slicer.qMRMLScreenShotDialog().Yellow:
      # yellow slice window
      widget = lm.sliceWidget("Yellow")
    elif type == slicer.qMRMLScreenShotDialog().Green:
      # green slice window
      widget = lm.sliceWidget("Green")

    # grab and convert to vtk image data
    qpixMap = qt.QPixmap().grabWidget(widget)
    qimage = qpixMap.toImage()
    imageData = vtk.vtkImageData()
    slicer.qMRMLUtils().qImageToVtkImageData(qimage,imageData)

    annotationLogic = slicer.modules.annotations.logic()
    annotationLogic.CreateSnapShot(name, description, type, self.screenshotScaleFactor, imageData)

  def rev(self, a, axis = -1):
        a = np.asarray(a).swapaxes(axis, 0)
        a = a[::-1,...]
        a = a.swapaxes(0, axis)
        return a
        
  def run(self,inputVolume,outputVolume,labelmaps_filename):
    """
    Run the actual algorithm
    """
    # get the shape     
    input_image = inputVolume.GetImageData()
    shape = list(input_image.GetDimensions())
    shape.reverse()
    input_array = vtk.util.numpy_support.vtk_to_numpy(input_image.GetPointData().GetScalars()).reshape(shape)
    
    outputVolume_temp = np.ones(shape)
    print("input volume shape")
    print(np.shape(input_array))
    #self.delayDisplay('Running the aglorithm '+str(shape))

    #outputArray = slicer.util.array(outputVolume.GetID())
    
    #call a function that takes as input the volume and a list of labelmaps
    my_pectoralis_segmentor = pectoralis_segmentor.pectoralis_segmentor(input_array, labelmaps_filename)
    outputVolume_temp = my_pectoralis_segmentor.execute()

    #outputVolume_temp2 = np.asarray(outputVolume_temp).swapaxes(0, 0)
    #outputVolume_temp2 = outputVolume_temp[::-1,...]
    #outputVolume_temp2 = outputVolume_temp.swapaxes(0, 0)
        
    outputVolume_temp2 = self.rev(outputVolume_temp, 0)
    print("out volume shape")
    print(np.shape(outputVolume_temp2))
    outputVolume_temp2 = outputVolume_temp
    shape = list(input_image.GetDimensions())
    
    volumesLogic = slicer.modules.volumes.logic()
    outputVolume = volumesLogic.CloneVolume(slicer.mrmlScene, inputVolume, 'Volume_Out')
    outputArray = slicer.util.array(outputVolume.GetID())
    print(np.shape(outputArray))
    outputArray[:]  = outputVolume_temp2.squeeze().reshape()
    outputVolume.GetImageData().Modified()
    #print(outputVolume) #vtkMRMLScalarVolumeNode
    #outputVolume.SetDimensions(shape)
    outputVolume.Modified()
    
    #set the vtk volume information

    print("output_shape")
    print(np.shape(outputVolume_temp))
    print(np.amax(outputVolume_temp))
    print(shape)
    #create a vtk volume to return
    #dataImporter = vtk.vtkImageImport()
    #dataImporter.CopyImportVoidPointer(outputVolume_temp,outputVolume_temp.nbytes)
    #dataImporter.SetDataScalarTypeToInt()
    #dataImporter.SetNumberOfScalarComponents(1)
    #dataImporter.SetDataExtent(0,shape[0], 0, shape[1], 0, shape[2])
    #dataImporter.SetWholeExtent(0,shape[0], 0, shape[1], 0, shape[2])
    
    
    #outputVolume.SetImageDataConnection() = inputVolume.GetImageDataConnection()
    
    return True


class PectoralisSegmentationTest(unittest.TestCase):
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
    self.test_PectoralisSegmentation1()

  def test_PectoralisSegmentation1(self):
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
    logic = PectoralisSegmentationLogic()
    self.assertTrue( logic.hasImageData(volumeNode) )
    self.delayDisplay('Test passed!')
