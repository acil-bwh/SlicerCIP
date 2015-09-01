import os, string
import unittest
from __main__ import vtk, qt, ctk, slicer
import numpy as np

#
# CompareVolumes
#

class VolumeProbe:
  def __init__(self, parent):
    parent.title = "Volume Probe"
    parent.categories = ["Wizards"]
    parent.dependencies = []
    parent.contributors = ["Alex Yarmarkovich"] # replace with "Firstname Lastname (Org)"
    parent.helpText = """
    """
    parent.helpText = string.Template("""
    This module helps organize layouts and volume compositing to help compare images

Please refer to <a href=\"$a/Documentation/$b.$c/Modules/VolumeProbe\"> the documentation</a>.

    """).substitute({ 'a':parent.slicerWikiUrl, 'b':slicer.app.majorVersion, 'c':slicer.app.minorVersion })
    parent.acknowledgementText = """
    This file was originally developed by Alex Yarmarkovich.
    It was partially funded by NIH grant 9999999
""" # replace with organization, grant and thanks.
    self.parent = parent

    # Add this test to the SelfTest module's list for discovery when the module
    # is created.  Since this module may be discovered before SelfTests itself,
    # create the list if it doesn't already exist.
    try:
      slicer.selfTests
    except AttributeError:
      slicer.selfTests = {}
    slicer.selfTests['VolumeProbe'] = self.runTest

  def runTest(self):
    tester = VolumeProbeTest()
    tester.runTest()
    print "runTest"

#
# qVolumeProbeWidget
#

class VolumeProbeWidget:
  def __init__(self, parent = None):
    settings = qt.QSettings()
    self.developerMode = settings.value('Developer/DeveloperMode').lower() == 'true'
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
    self.roiManager = None
    self.ROIRadius = 20.0

  def setup(self):
    # Instantiate and connect widgets ...

    if self.developerMode:
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
      self.reloadButton.name = "VolumeProbe Reload"
      reloadFormLayout.addWidget(self.reloadButton)
      self.reloadButton.connect('clicked()', self.onReload)

      # reload and test button
      # (use this during development, but remove it when delivering
      #  your module to users)
      self.reloadAndTestButton = qt.QPushButton("Reload and Test All")
      self.reloadAndTestButton.toolTip = "Reload this module and then run the self tests."
      reloadFormLayout.addWidget(self.reloadAndTestButton)
      self.reloadAndTestButton.connect('clicked()', self.onReloadAndTest)

      # reload and run specific tests
      scenarios = ("Three Volume", "View Watcher", "ROIManager",)
      for scenario in scenarios:
        button = qt.QPushButton("Reload and Test %s" % scenario)
        self.reloadAndTestButton.toolTip = "Reload this module and then run the %s self test." % scenario
        reloadFormLayout.addWidget(button)
        button.connect('clicked()', lambda s=scenario: self.onReloadAndTest(scenario=s))

    #
    # Parameters Area
    #
    parametersCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersCollapsibleButton.text = "Parameters"
    self.layout.addWidget(parametersCollapsibleButton)

    # Layout within the dummy collapsible button
    parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)

    """
    #
    # target volume selector
    #
    self.inputSelector = slicer.qMRMLNodeComboBox()
    self.inputSelector.nodeTypes = ( ("vtkMRMLVolumeNode"), "" )
    self.inputSelector.selectNodeUponCreation = True
    self.inputSelector.addEnabled = False
    self.inputSelector.removeEnabled = False
    self.inputSelector.noneEnabled = False
    self.inputSelector.showHidden = False
    self.inputSelector.showChildNodeTypes = True
    self.inputSelector.setMRMLScene( slicer.mrmlScene )
    self.inputSelector.setToolTip( "Pick the input to the algorithm." )
    parametersFormLayout.addRow("Target Volume: ", self.inputSelector)
    """

    #
    # Add ROI
    #
    self.drawROICheck = qt.QCheckBox()
    parametersFormLayout.addRow("Draw ROI", self.drawROICheck)
    self.drawROICheck.connect("toggled(bool)", self.onDrawROIToggled)

    self.ROIRadiusSlider = ctk.ctkSliderWidget()
    #self.ROIRadiusSlider.setMinimum(1)
    #self.ROIRadiusSlider.setMaximum(100)
    self.ROIRadiusSlider.setValue(self.ROIRadius)
    parametersFormLayout.addRow("ROI Radius", self.ROIRadiusSlider)
    self.ROIRadiusSlider.connect("valueChanged(double)", self.onROIRadiusChanged)

    #
    # Add Histogram
    self.numBins = qt.QSpinBox()
    self.numBins.setRange(0, 200)
    self.numBins.setEnabled(1)
    self.numBins.setValue(20)
    parametersFormLayout.addRow("Number of Bins", self.numBins)

    self.histogramArray = vtk.vtkDoubleArray()
    self.histogramArray.SetNumberOfComponents(1)
    self.histogramArray.SetNumberOfTuples(0)

    self.histogram = ctk.ctkVTKHistogram()
    self.histogram.setDataArray(self.histogramArray)
    self.histogram.numberOfBins = self.numBins.value

    self.histogramView = ctk.ctkTransferFunctionView()
    self.histogramItem = ctk.ctkTransferFunctionBarsItem(self.histogram)
    self.histogramItem.barWidth = 0.7

    self.histogramView.scene().addItem(self.histogramItem)
    parametersFormLayout.addRow("Histogram", self.histogramView)
    self.histogramView.show()


    self.minField = qt.QSpinBox()
    self.minField.setRange(-100000, 100000)
    self.minField.setEnabled(0)
    parametersFormLayout.addRow("Min Value", self.minField)

    self.maxField = qt.QSpinBox()
    self.maxField.setRange(-100000, 100000)
    self.maxField.setEnabled(0)
    parametersFormLayout.addRow("Max Value", self.maxField)

    self.meanField = qt.QSpinBox()
    self.meanField.setRange(-100000, 100000)
    self.meanField.setEnabled(0)
    parametersFormLayout.addRow("Mean Value", self.meanField)
    
    self.medianField = qt.QSpinBox()
    self.medianField.setRange(-100000, 100000)
    self.medianField.setEnabled(0)
    parametersFormLayout.addRow("Median Value", self.medianField)
  
    self.stdField = qt.QSpinBox()
    self.stdField.setRange(-100000, 100000)
    self.stdField.setEnabled(0)
    parametersFormLayout.addRow("STD Value", self.stdField)
    
    # Add vertical spacer
    self.layout.addStretch(1)

  def reportROIStats(self, pixelArray):
    min = 0
    max = 0
    mean = 0
    med = 0
    self.histogramArray.SetNumberOfTuples(0)
    if len(pixelArray):
      pixels = np.array(pixelArray)
      min = pixels.min()
      max = pixels.max()
      mean = pixels.mean()
      standardDeviation = pixels.std()
      med = self.median(pixelArray)
      for i in range(len(pixelArray)):
        self.histogramArray.InsertNextTuple1(pixels[i])

    self.minField.setValue(min)
    self.maxField.setValue(max)
    self.meanField.setValue(mean)
    self.medianField.setValue(med)
    self.stdField.SetValue(standardDeviation)
    self.histogram.numberOfBins = self.numBins.value
    # This causes crash in slicer starting end of April 2015
    #self.histogram.build()
    self.histogramView.show()
    
  def median(self, data):
    """Return the median (middle value) of numeric data.
    When the number of data points is odd, return the middle data point.
    When the number of data points is even, the median is interpolated by
    taking the average of the two middle values:
    >>> median([1, 3, 5])
    3
    >>> median([1, 3, 5, 7])
    4.0
    """
    data = sorted(data)
    n = len(data)
    if n == 0:
        return 0
    if n%2 == 1:
        return data[n//2]
    else:
        i = n//2
        return (data[i - 1] + data[i])/2

  def onDrawROIToggled(self):
    if self.drawROICheck.checked:
      self.roiManager = ROIManager()
      self.roiManager.setROIRadius(self.ROIRadius)
      self.roiManager.setVolumeProbeWidget(self)
    else:
      self.roiManager.tearDown()
      self.roiManager = None

  def onROIRadiusChanged(self,value):
    self.ROIRadius = value
    self.roiManager.setROIRadius(self.ROIRadius)

  def onReload(self,moduleName="VolumeProbe"):
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
    # create new widget inside existing parent
    globals()[widgetName.lower()] = eval(
        'globals()["%s"].%s(parent)' % (moduleName, widgetName))
    globals()[widgetName.lower()].setup()

  def onReloadAndTest(self,moduleName="VolumeProbe",scenario=None):
    try:
      self.onReload()
      evalString = 'globals()["%s"].%sTest()' % (moduleName, moduleName)
      tester = eval(evalString)
      tester.runTest(scenario=scenario)
    except Exception, e:
      import traceback
      traceback.print_exc()
      qt.QMessageBox.warning(slicer.util.mainWindow(),
          "Reload and Test", 'Exception!\n\n' + str(e) + "\n\nSee Python Console for Stack Trace")


#
# VolumeProbeLogic
#

class VolumeProbeLogic:
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget
  """
  def __init__(self):
    self.sliceViewItemPattern = """
      <item><view class="vtkMRMLSliceNode" singletontag="{viewName}">
        <property name="orientation" action="default">{orientation}</property>
        <property name="viewlabel" action="default">{viewName}</property>
        <property name="viewcolor" action="default">{color}</property>
      </view></item>
     """
    # use a nice set of colors
    self.colors = slicer.util.getNode('GenericColors')
    self.lookupTable = self.colors.GetLookupTable()
    print "VolumeProbeLogic CREATED"


class ViewWatcher(object):
  """A helper class to manage observers on slice views"""

  def __init__(self):
    # the currentLayoutName is tag on the slice node that corresponds
    # view which should currently be shown in the DataProbe window.
    # Keeping track of this allows us to respond to non-interactor updates
    # to the slice (like from an external tracker) but only in the view where
    # the mouse has most recently entered.
    self.currentLayoutName = None

    # Default observer priority is 0.0, and the widgets have a 0.5 priority
    # so we set this to 1 in order to get events that would
    # otherwise be swallowed.  Since we do not abort the event, this is harmless.
    self.priority = 2

    # keep list of pairs: [observee,tag] so they can be removed easily
    self.observerTags = []
    # keep a map of interactor styles to sliceWidgets so we can easily get sliceLogic
    self.sliceWidgetsPerStyle = {}
    self.refreshObservers()

    # saved cursor for restoring custom after overlays
    self.savedCursor = None

    layoutManager = slicer.app.layoutManager()
    layoutManager.connect('layoutChanged(int)', self.refreshObservers)

    # instance variables filled in by processEvent
    self.sliceWidget = None
    self.sliceView = None
    self.sliceLogic = None
    self.sliceNode = None
    self.interactor = None
    self.xy = (0,0)
    self.xyz = (0,0,0)
    self.ras = (0,0,0)
    self.layerLogics = {}
    self.layerVolumeNodes = {}
    self.savedWidget = None

    print "ViewWatcher CREATED"

  def __del__(self):
    self.tearDown()

  def removeObservers(self):
    # remove observers and reset
    for observee,tag in self.observerTags:
      observee.RemoveObserver(tag)
    self.observerTags = []
    self.sliceWidgetsPerStyle = {}

  def refreshObservers(self):
    """ When the layout changes, drop the observers from
    all the old widgets and create new observers for the
    newly created widgets"""
    self.removeObservers()
    # get new slice nodes
    layoutManager = slicer.app.layoutManager()
    sliceNodeCount = slicer.mrmlScene.GetNumberOfNodesByClass('vtkMRMLSliceNode')
    for nodeIndex in xrange(sliceNodeCount):
      # find the widget for each node in scene
      sliceNode = slicer.mrmlScene.GetNthNodeByClass(nodeIndex, 'vtkMRMLSliceNode')
      sliceWidget = layoutManager.sliceWidget(sliceNode.GetLayoutName())
      if sliceWidget:
        # add obserservers and keep track of tags
        style = sliceWidget.sliceView().interactorStyle().GetInteractor()
        self.sliceWidgetsPerStyle[style] = sliceWidget
        events = ("MouseMoveEvent", "EnterEvent", "LeaveEvent")
        for event in events:
          tag = style.AddObserver(event, self.processEvent, self.priority)
          self.observerTags.append([style,tag])
        tag = sliceNode.AddObserver("ModifiedEvent", self.processEvent, self.priority)
        self.observerTags.append([sliceNode,tag])
        sliceLogic = sliceWidget.sliceLogic()
        compositeNode = sliceLogic.GetSliceCompositeNode()
        tag = compositeNode.AddObserver("ModifiedEvent", self.processEvent, self.priority)
        self.observerTags.append([compositeNode,tag])


  def processEvent(self,observee,event):
    if event == 'LeaveEvent':
      self.currentLayoutName = None
    if event == 'EnterEvent':
      sliceWidget = self.sliceWidgetsPerStyle[observee]
      self.currentLayoutName = None
      sliceLogic = sliceWidget.sliceLogic()
      sliceNode = sliceWidget.mrmlSliceNode()
      self.currentLayoutName = sliceNode.GetLayoutName()
    nodeEvent = (observee.IsA('vtkMRMLSliceNode') or
                observee.IsA('vtkMRMLSliceCompositeNode'))
    if nodeEvent:
      # for a slice node, get the corresponding style and
      # set it as the observee so update is made for that sliceWidget
      # if it is the current layout name
      layoutManager = slicer.app.layoutManager()
      sliceWidget = layoutManager.sliceWidget(observee.GetLayoutName())
      if sliceWidget and observee.GetLayoutName() == self.currentLayoutName:
        observee = sliceWidget.sliceView().interactor()
    if self.sliceWidgetsPerStyle.has_key(observee):
      self.sliceWidget = self.sliceWidgetsPerStyle[observee]
      self.sliceView = self.sliceWidget.sliceView()
      self.sliceLogic = self.sliceWidget.sliceLogic()
      self.sliceNode = self.sliceWidget.mrmlSliceNode()
      self.interactor = observee
      self.xy = self.interactor.GetEventPosition()
      self.xyz = self.sliceWidget.sliceView().convertDeviceToXYZ(self.xy);
      self.ras = self.sliceWidget.sliceView().convertXYZToRAS(self.xyz)

      self.layerLogics = {}
      self.layerVolumeNodes = {}
      layerLogicCalls = (('L', self.sliceLogic.GetLabelLayer),
                         ('F', self.sliceLogic.GetForegroundLayer),
                         ('B', self.sliceLogic.GetBackgroundLayer))
      for layer,logicCall in layerLogicCalls:
        self.layerLogics[layer] = logicCall()
        self.layerVolumeNodes[layer] = self.layerLogics[layer].GetVolumeNode()

      self.onSliceWidgetEvent(event)

  def onSliceWidgetEvent(self,event):
    """ virtual method called when an event occurs
    on a slice widget.  The instance variables of the class
    will have been filled by the processEvent method above
    """
    pass

  def tearDown(self):
    """Virtual method meant to be overridden by the subclass
    Cleans up any observers (or widgets and other instances).
    This is needed because __del__ does not reliably get called.
    """
    layoutManager = slicer.app.layoutManager()
    layoutManager.disconnect('layoutChanged(int)', self.refreshObservers)
    self.removeObservers()

  def cursorOff(self,widget):
    """Turn off and save the current cursor so
    the user can see an overlay that tracks the mouse"""
    if self.savedWidget == widget:
      return
    else:
      self.cursorOn()
    self.savedWidget = widget
    self.savedCursor = widget.cursor
    qt_BlankCursor = 10
    widget.setCursor(qt.QCursor(qt_BlankCursor))

  def cursorOn(self):
    """Restore the saved cursor if it exists, otherwise
    just restore the default cursor"""
    if self.savedWidget:
      if self.savedCursor:
        self.savedWidget.setCursor(self.savedCursor)
      else:
        self.savedWidget.unsetCursor()
    self.savedWidget = None
    self.savedCursor = None

class ROIManager(ViewWatcher):
  """Track the mouse and show a reveal view"""

  def __init__(self,parent=None,width=400,height=400,showWidget=False,scale=False):
    super(ROIManager,self).__init__()
    self.width = width
    self.height = height
    self.showWidget = showWidget
    self.scale = scale
    self.renderer = None
    self.ROIRadius = 20.0
    self.minValueBG=0
    self.maxValueBG=0
    self.minValueFG=0
    self.maxValueFG=0
    self.probeWidget = None
    self.drawOverlay = 0

    # utility Qt instances for use in methods
    self.gray = qt.QColor()
    self.gray.setRedF(0.5)
    self.gray.setGreenF(0.5)
    self.gray.setBlueF(0.5)
    # a painter to use for various jobs
    self.painter = qt.QPainter()


    # make a qwidget display
    if self.showWidget:
      self.frame = qt.QFrame(parent)
      mw = slicer.util.mainWindow()
      self.frame.setGeometry(mw.x, mw.y, self.width, self.height)
      self.frameLayout = qt.QVBoxLayout(self.frame)
      self.label = qt.QLabel()
      self.frameLayout.addWidget(self.label)
      self.frame.show()

    # make an image actor in the slice view
    self.vtkImage = vtk.vtkImageData()

    self.mrmlUtils = slicer.qMRMLUtils()
    self.imageMapper = vtk.vtkImageMapper()
    self.imageMapper.SetColorLevel(128)
    self.imageMapper.SetColorWindow(255)
    if vtk.VTK_MAJOR_VERSION <= 5:
      self.imageMapper.SetInput(self.vtkImage)
    else:
      self.imageMapper.SetInputData(self.vtkImage)
    self.actor2D = vtk.vtkActor2D()
    self.actor2D.SetMapper(self.imageMapper)

    # make a circle actor
    self.circle = vtk.vtkRegularPolygonSource()
    self.circle.SetNumberOfSides(50)
    self.circle.SetRadius(5)
    self.circle.SetCenter(0,0,0)
    self.circle.GeneratePolylineOn()
    self.circle.GeneratePolygonOff()
    self.circle.Update()
    self.mapper = vtk.vtkPolyDataMapper2D()
    self.actor = vtk.vtkActor2D()
    if vtk.VTK_MAJOR_VERSION <= 5:
      self.mapper.SetInput(self.circle.GetOutput())
    else:
      self.mapper.SetInputConnection(self.circle.GetOutputPort())
    self.actor.SetMapper(self.mapper)
    property_ = self.actor.GetProperty()
    property_.SetColor(1,1,0)
    property_.SetLineWidth(1)

  def tearDown(self):
    # clean up widget
    self.frame = None
    self.probeWidget = None
    # clean up image actor
    if self.renderer:
      #self.renderer.RemoveActor(self.actor2D)
      self.renderer.RemoveActor(self.actor)
    self.cursorOn()
    if self.sliceView:
      self.sliceView.scheduleRender()
    super(ROIManager,self).tearDown()

  def setROIRadius(self, radius=20):
    self.ROIRadius = radius

  def setVolumeProbeWidget(self, probeWidget):
    self.probeWidget = probeWidget

  def onSliceWidgetEvent(self,event):
    if self.drawOverlay: 
      overlayPixmap = self.overlayPixmap(self.xy)

    #widget
    if self.showWidget:
      self.label.setPixmap(overlayPixmap)

    # actor
    self.renderWindow = self.sliceView.renderWindow()
    self.renderer = self.renderWindow.GetRenderers().GetItemAsObject(0)

    #if event == "LeaveEvent" or not self.layerVolumeNodes['F']:
    if event == "LeaveEvent":
      if self.drawOverlay: 
        self.renderer.RemoveActor(self.actor2D)
      self.renderer.RemoveActor(self.actor)
      self.cursorOn()
      self.sliceView.forceRender()
    elif event == "EnterEvent":
      if self.drawOverlay: 
        self.renderer.AddActor2D(self.actor2D)
      self.renderer.AddActor2D(self.actor)
      if self.layerVolumeNodes['F'] and (self.layerVolumeNodes['F'] != self.layerVolumeNodes['B']):
        self.cursorOff(self.sliceWidget)
    else:
      if self.drawOverlay: 
        self.mrmlUtils.qImageToVtkImageData(overlayPixmap.toImage(),self.vtkImage)
        if vtk.VTK_MAJOR_VERSION <= 5:
          self.imageMapper.SetInput(self.vtkImage)
        else:
          self.imageMapper.SetInputData(self.vtkImage)
          x,y = self.xy
          self.actor2D.SetPosition(x-self.width/2,y-self.height/2)

      #draw ROI
      x,y = self.xy
      self.circle.GeneratePolylineOn()
      self.circle.GeneratePolygonOff()
      self.circle.SetRadius(self.ROIRadius)
      self.circle.SetCenter(x,y,0)
      self.circle.Update()

      self.computeROIStats(self.xy, self.ROIRadius)

      self.sliceView.forceRender()

  def computeROIStats(self, xy, radius):
    """compute stats for an image inside ROI
    at xy with radius"""

    # Get vtkImages for F/B/L layers
    bgVTKImage = self.layerLogics['B'].GetReslice().GetOutput()
    if not bgVTKImage:
      bgVTKImage = self.layerLogics['F'].GetReslice().GetOutput()
    if not bgVTKImage:
      bgVTKImage = self.layerLogics['L'].GetReslice().GetOutput()
      
    x,y=xy
    radius2 = radius*radius
    roiPixels = []

    if bgVTKImage:
      dims = bgVTKImage.GetDimensions()
      for i in range(dims[0]):
        for j in range(dims[1]):
          dist2 = (i-x)*(i-x) + (j-y)*(j-y)
          if dist2 < radius2:
            value = bgVTKImage.GetScalarComponentAsDouble(i,j,0,0);
            roiPixels.append(value)

    self.probeWidget.reportROIStats(roiPixels)


  def overlayPixmap(self, xy):
    """fill a pixmap with an image that has a reveal pattern
    at xy with the fg drawn over the bg"""

    # Get QImages for the two layers
    bgVTKImage = self.layerLogics['B'].GetImageData()
    fgVTKImage = self.layerLogics['F'].GetImageData()
    bgQImage = qt.QImage()
    fgQImage = qt.QImage()
    slicer.qMRMLUtils().vtkImageDataToQImage(bgVTKImage, bgQImage)
    slicer.qMRMLUtils().vtkImageDataToQImage(fgVTKImage, fgQImage)

    # get the geometry of the focal point (xy) and images
    # noting that vtk has the origin at the bottom left and qt has
    # it at the top left.  yy is the flipped version of y
    imageWidth = bgQImage.width()
    imageHeight = bgQImage.height()
    x,y=xy
    yy = imageHeight-y

    #
    # make a generally transparent image,
    # then fill quadrants with the fg image
    #
    overlayImage = qt.QImage(imageWidth, imageHeight, qt.QImage().Format_ARGB32)
    overlayImage.fill(0)

    halfWidth = imageWidth/2
    halfHeight = imageHeight/2
    topLeft = qt.QRect(0,0, x, yy)
    bottomRight = qt.QRect(x, yy, imageWidth-x-1, imageHeight-yy-1)

    self.painter.begin(overlayImage)
    self.painter.drawImage(topLeft, fgQImage, topLeft)
    self.painter.drawImage(bottomRight, fgQImage, bottomRight)
    self.painter.end()

    # draw the bg and fg on top of gray background
    compositePixmap = qt.QPixmap(self.width,self.height)
    compositePixmap.fill(self.gray)
    self.painter.begin(compositePixmap)
    self.painter.drawImage(
        -1 * (x  -self.width/2),
        -1 * (yy -self.height/2),
        bgQImage)
    self.painter.drawImage(
        -1 * (x  -self.width/2),
        -1 * (yy -self.height/2),
        overlayImage)
    self.painter.end()

    if self.scale:
      compositePixmap = self.scalePixmap(compositePixmap)

    # draw a border around the pixmap
    self.painter.begin(compositePixmap)
    self.pen = qt.QPen()
    self.color = qt.QColor("#FF0")
    self.color.setAlphaF(0.3)
    self.pen.setColor(self.color)
    self.pen.setWidth(5)
    self.pen.setStyle(3) # dotted line (Qt::DotLine)
    self.painter.setPen(self.pen)
    rect = qt.QRect(1, 1, self.width-2, self.height-2)
    self.painter.drawRect(rect)
    self.painter.drawArc(rect, 0, 360*16)
    self.painter.end()

    return compositePixmap

  def scalePixmap(self,pixmap):
    # extract the center of the pixmap and then zoom
    halfWidth = self.width/2
    halfHeight = self.height/2
    quarterWidth = self.width/4
    quarterHeight = self.height/4
    centerPixmap = qt.QPixmap(halfWidth,halfHeight)
    centerPixmap.fill(self.gray)
    self.painter.begin(centerPixmap)
    fullRect = qt.QRect(0,0,halfWidth,halfHeight)
    centerRect = qt.QRect(quarterWidth, quarterHeight, halfWidth, halfHeight)
    self.painter.drawPixmap(fullRect, pixmap, centerRect)
    self.painter.end()
    scaledPixmap = centerPixmap.scaled(self.width, self.height)

    return scaledPixmap


class VolumeProbeTest(unittest.TestCase):
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

