from __main__ import vtk, qt, ctk, slicer

#
# ParenchymaAnalysis
#

class ParenchymaAnalysis:
  def __init__(self, parent):
    import string
    parent.title = "Parenchyma Analysis"
    parent.categories = ["Chest Imaging Platform"]
    parent.contributors = ["Applied Chest Imaging Laboratory"]
    parent.helpText = string.Template("""
Use this module to calculate counts and volumes for different labels of a label map plus statistics on the grayscale background volume.  Note: volumes must have same dimensions.  See <a href=\"$a/Documentation/$b.$c/Modules/ParenchymaAnalysis\">$a/Documentation/$b.$c/Modules/ParenchymaAnalysis</a> for more information.
    """).substitute({ 'a':parent.slicerWikiUrl, 'b':slicer.app.majorVersion, 'c':slicer.app.minorVersion })
    parent.acknowledgementText = """
    Supported by NA-MIC, NAC, BIRN, NCIGT, and the Slicer Community. See http://www.slicer.org for details.  Module implemented by Steve Pieper.
    """
    self.parent = parent

#
# qSlicerPythonModuleExampleWidget
#

class ParenchymaAnalysisWidget:
  def __init__(self, parent=None):
    self.chartOptions = ("LAA%-950","LAA%-910","LAA%-856","HAA%-700","HAA%-600","Mean","Std","Kurtosis","Skewness","Volume")
    if not parent:
      self.parent = slicer.qMRMLWidget()
      self.parent.setLayout(qt.QVBoxLayout())
      self.parent.setMRMLScene(slicer.mrmlScene)
    else:
      self.parent = parent
    self.logic = None
    self.inspNode = None
    self.insplabelNode = None
    self.expNode = None
    self.explabelNode = None
    self.fileName = None
    self.fileDialog = None
    if not parent:
      self.setup()
      self.inspSelector.setMRMLScene(slicer.mrmlScene)
      self.expSelector.setMRMLScene(slicer.mrmlScene)
      self.insplabelSelector.setMRMLScene(slicer.mrmlScene)
      self.explabelSelector.setMRMLScene(slicer.mrmlScene)
      self.parent.show()

  def setup(self):

    #
    # Reload and Test area
    #
    #reloadCollapsibleButton = ctk.ctkCollapsibleButton()
    #reloadCollapsibleButton.text = "Reload && Test"
    #self.layout.addWidget(reloadCollapsibleButton)
    #self.layout.setSpacing(6)
    #reloadFormLayout = qt.QFormLayout(reloadCollapsibleButton)
    
    # reload button
    # (use this during development, but remove it when delivering
    #  your module to users)
    #self.reloadButton = qt.QPushButton("Reload")
    #self.reloadButton.toolTip = "Reload this module."
    #self.reloadButton.name = "InteractiveLobeSegmentation Reload"
    #reloadFormLayout.addWidget(self.reloadButton)
    #self.reloadButton.connect('clicked()', self.onReload)
    
    # reload and test button
    # (use this during development, but remove it when delivering
    #  your module to users)
    #self.reloadAndTestButton = qt.QPushButton("Reload and Test")
    #self.reloadAndTestButton.toolTip = "Reload this module and then run the self tests."
    #reloadFormLayout.addWidget(self.reloadAndTestButton)
    #self.reloadAndTestButton.connect('clicked()', self.onReloadAndTest)
    
    
    #
    # the inps volume selector
    #
    self.inspSelectorFrame = qt.QFrame(self.parent)
    self.inspSelectorFrame.setLayout(qt.QHBoxLayout())
    self.parent.layout().addWidget(self.inspSelectorFrame)

    self.inspSelectorLabel = qt.QLabel("Inspiratory CT: ", self.inspSelectorFrame)
    self.inspSelectorLabel.setToolTip( "Select the Inspiratory CT for parenchymal analysis")
    self.inspSelectorFrame.layout().addWidget(self.inspSelectorLabel)

    self.inspSelector = slicer.qMRMLNodeComboBox(self.inspSelectorFrame)
    self.inspSelector.nodeTypes = ( ("vtkMRMLScalarVolumeNode"), "" )
    self.inspSelector.addAttribute( "vtkMRMLScalarVolumeNode", "LabelMap", 0 )
    self.inspSelector.selectNodeUponCreation = False
    self.inspSelector.addEnabled = False
    self.inspSelector.removeEnabled = False
    self.inspSelector.noneEnabled = True
    self.inspSelector.showHidden = False
    self.inspSelector.showChildNodeTypes = False
    self.inspSelector.setMRMLScene( slicer.mrmlScene )
    # TODO: need to add a QLabel
    # self.inspSelector.SetLabelText( "Master Volume:" )
    self.inspSelectorFrame.layout().addWidget(self.inspSelector)

    
    #
    # the exp volume selector
    #
    self.expSelectorFrame = qt.QFrame(self.parent)
    self.expSelectorFrame.setLayout(qt.QHBoxLayout())
    self.parent.layout().addWidget(self.expSelectorFrame)
    
    self.expSelectorLabel = qt.QLabel("Expiratory CT: ", self.expSelectorFrame)
    self.expSelectorLabel.setToolTip( "Select the Expiratory CT for parenchymal analysis")
    self.expSelectorFrame.layout().addWidget(self.expSelectorLabel)
    
    self.expSelector = slicer.qMRMLNodeComboBox(self.expSelectorFrame)
    self.expSelector.nodeTypes = ( ("vtkMRMLScalarVolumeNode"), "" )
    self.expSelector.addAttribute( "vtkMRMLScalarVolumeNode", "LabelMap", 0 )
    self.expSelector.selectNodeUponCreation = False
    self.expSelector.addEnabled = False
    self.expSelector.removeEnabled = False
    self.expSelector.noneEnabled = True
    self.expSelector.showHidden = False
    self.expSelector.showChildNodeTypes = False
    self.expSelector.setMRMLScene( slicer.mrmlScene )
    # TODO: need to add a QLabel
    # self.inspSelector.SetLabelText( "Master Volume:" )
    self.expSelectorFrame.layout().addWidget(self.expSelector)
    
    
    #
    # the insp label volume selector
    #
    self.insplabelSelectorFrame = qt.QFrame()
    self.insplabelSelectorFrame.setLayout( qt.QHBoxLayout() )
    self.parent.layout().addWidget( self.insplabelSelectorFrame )

    self.insplabelSelectorLabel = qt.QLabel()
    self.insplabelSelectorLabel.setText( "Inspiratory Label Map: " )
    self.insplabelSelectorFrame.layout().addWidget( self.insplabelSelectorLabel )

    self.insplabelSelector = slicer.qMRMLNodeComboBox()
    #self.insplabelSelector.nodeTypes = ( "vtkMRMLScalarVolumeNode", "" )
    #self.insplabelSelector.addAttribute( "vtkMRMLScalarVolumeNode", "LabelMap", "1" )
    self.insplabelSelector.nodeTypes = ( "vtkMRMLLabelMapVolumeNode", "" )

    # todo addAttribute
    self.insplabelSelector.selectNodeUponCreation = False
    self.insplabelSelector.addEnabled = False
    self.insplabelSelector.noneEnabled = True
    self.insplabelSelector.removeEnabled = False
    self.insplabelSelector.showHidden = False
    self.insplabelSelector.showChildNodeTypes = False
    self.insplabelSelector.setMRMLScene( slicer.mrmlScene )
    self.insplabelSelector.setToolTip( "Inspiratory label map" )
    self.insplabelSelectorFrame.layout().addWidget( self.insplabelSelector )

    #
    # the exp label volume selector
    #
    self.explabelSelectorFrame = qt.QFrame()
    self.explabelSelectorFrame.setLayout( qt.QHBoxLayout() )
    self.parent.layout().addWidget( self.explabelSelectorFrame )
    
    self.explabelSelectorLabel = qt.QLabel()
    self.explabelSelectorLabel.setText( "Expiratory Label Map: " )
    self.explabelSelectorFrame.layout().addWidget( self.explabelSelectorLabel )
    
    self.explabelSelector = slicer.qMRMLNodeComboBox()
    #self.explabelSelector.nodeTypes = ( "vtkMRMLScalarVolumeNode", "" )
    #self.explabelSelector.addAttribute( "vtkMRMLScalarVolumeNode", "LabelMap", "1" )
    self.explabelSelector.nodeTypes = ( "vtkMRMLLabelMapVolumeNode", "" )

    # todo addAttribute
    self.explabelSelector.selectNodeUponCreation = False
    self.explabelSelector.addEnabled = False
    self.explabelSelector.noneEnabled = True
    self.explabelSelector.removeEnabled = False
    self.explabelSelector.showHidden = False
    self.explabelSelector.showChildNodeTypes = False
    self.explabelSelector.setMRMLScene( slicer.mrmlScene )
    self.explabelSelector.setToolTip( "Expiratory label map" )
    self.explabelSelectorFrame.layout().addWidget( self.explabelSelector )
    
    # Apply button
    self.applyButton = qt.QPushButton("Apply")
    self.applyButton.toolTip = "Calculate Parenchyma Phenotypes."
    self.applyButton.enabled = False
    self.parent.layout().addWidget(self.applyButton)

    # model and view for INSP stats table
    self.view = qt.QTableView()
    self.view.sortingEnabled = True
    self.parent.layout().addWidget(self.view)

    # model and view for EXP stats table
    self.viewexp = qt.QTableView()
    self.viewexp.sortingEnabled = True
    self.parent.layout().addWidget(self.viewexp)
    
    # Chart button
    self.chartFrame = qt.QFrame()
    self.chartFrame.setLayout(qt.QHBoxLayout())
    self.parent.layout().addWidget(self.chartFrame)
    self.chartButton = qt.QPushButton("Chart")
    self.chartButton.toolTip = "Make a chart from the current statistics."
    self.chartFrame.layout().addWidget(self.chartButton)
    self.chartOption = qt.QComboBox()
    self.chartOption.addItems(self.chartOptions)
    self.chartFrame.layout().addWidget(self.chartOption)
    self.chartIgnoreZero = qt.QCheckBox()
    self.chartIgnoreZero.setText('Ignore Zero')
    self.chartIgnoreZero.checked = False
    self.chartIgnoreZero.setToolTip('Do not include the zero index in the chart to avoid dwarfing other bars')
    #self.chartFrame.layout().addWidget(self.chartIgnoreZero)
    self.chartFrame.enabled = False


    # Save button
    self.saveButton = qt.QPushButton("Save")
    self.saveButton.toolTip = "Save Statistics as a csv file."
    self.saveButton.enabled = False
    self.parent.layout().addWidget(self.saveButton)

    # Add vertical spacer
    self.parent.layout().addStretch(1)

    # connections
    self.applyButton.connect('clicked()', self.onApply)
    self.chartButton.connect('clicked()', self.onChart)
    self.saveButton.connect('clicked()', self.onSave)
    self.inspSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.onInspSelect)
    self.insplabelSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.onInspLabelSelect)
    self.expSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.onExpSelect)
    self.explabelSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.onExpLabelSelect)

  def onInspSelect(self, node):
    self.inspNode = node
    self.applyButton.enabled = bool(self.inspNode) and bool(self.insplabelNode)

  def onInspLabelSelect(self, node):
    self.insplabelNode = node
    self.applyButton.enabled = bool(self.inspNode) and bool(self.insplabelNode)

  def onExpSelect(self, node):
    self.expNode = node
    self.applyButton.enabled = bool(self.expNode) and bool(self.explabelNode)

  def onExpLabelSelect(self, node):
    self.explabelNode = node
    self.applyButton.enabled = bool(self.expNode) and bool(self.explabelNode)


  def inspvolumesAreValid(self):
    """Verify that volumes are compatible with label calculation
    algorithm assumptions"""
    if not self.inspNode or not self.insplabelNode:
      return False
    if not self.inspNode.GetImageData() or not self.insplabelNode.GetImageData():
      return False
    if self.inspNode.GetImageData().GetDimensions() != self.insplabelNode.GetImageData().GetDimensions():
      return False
    return True

  def expvolumesAreValid(self):
    """Verify that volumes are compatible with label calculation
      algorithm assumptions"""
    if not self.expNode or not self.explabelNode:
      return False
    if not self.expNode.GetImageData() or not self.explabelNode.GetImageData():
      return False
    if self.expNode.GetImageData().GetDimensions() != self.explabelNode.GetImageData().GetDimensions():
      return False
    return True

  def onApply(self):
    """Calculate the parenchyma analysis
    """
    if not self.inspvolumesAreValid():
      qt.QMessageBox.warning(slicer.util.mainWindow(),
          "Parenchyma Analysis", "Inspiratory Volumes do not have the same geometry.")
      return

    if not self.expvolumesAreValid():
      qt.QMessageBox.warning(slicer.util.mainWindow(),
          "Parenchyma Analysis", "Expiratory Volumes do not have the same geometry.")
      return
    
    self.applyButton.text = "Working..."
    # TODO: why doesn't processEvents alone make the label text change?
    self.applyButton.repaint()
    slicer.app.processEvents()
    self.logic = ParenchymaAnalysisLogic(self.inspNode, self.insplabelNode,self.expNode,self.explabelNode)
    self.populateStats()
    self.chartFrame.enabled = True
    self.saveButton.enabled = True
    self.applyButton.text = "Apply"

  def onChart(self):
    """chart the parenchyma analysis
    """
    valueToPlot = self.chartOptions[self.chartOption.currentIndex]
    ignoreZero = self.chartIgnoreZero.checked
    self.logic.createStatsChart(self.insplabelNode,valueToPlot,ignoreZero)

  def onSave(self):
    """save the parenchyma analysis
    """
    if not self.fileDialog:
      self.fileDialog = qt.QFileDialog(self.parent)
      self.fileDialog.options = self.fileDialog.DontUseNativeDialog
      self.fileDialog.acceptMode = self.fileDialog.AcceptSave
      self.fileDialog.defaultSuffix = "csv"
      self.fileDialog.setNameFilter("Comma Separated Values (*.csv)")
      self.fileDialog.connect("fileSelected(QString)", self.onFileSelected)
    self.fileDialog.show()

  def onFileSelected(self,fileName):
    self.logic.saveStats(fileName)

  def populateStats(self):
    if not self.logic:
      return
    displayNode = self.insplabelNode.GetDisplayNode()
    colorNode = displayNode.GetColorNode()
    lut = colorNode.GetLookupTable()
    self.items = []
    self.model = qt.QStandardItemModel()
    self.view.setModel(self.model)
    self.view.verticalHeader().visible = False
    row = 0
    
    cycle=['insp']
      
    for i in cycle:
      for regionTag,regionValue in zip(self.logic.regionTags,self.logic.regionValues):
        color = qt.QColor()
        rgb = lut.GetTableValue(regionValue[0])
        color.setRgb(rgb[0]*255,rgb[1]*255,rgb[2]*255)
        item = qt.QStandardItem()
        item.setData(color,1)
        item.setText(str(regionTag))
        item.setData(regionTag,1)
        item.setToolTip(regionTag)
        self.model.setItem(row,0,item)
        self.items.append(item)
        col = 1
        for k in self.logic.keys:
          item = qt.QStandardItem()
          item.setText("%.3f" % self.logic.labelStats[i,k,regionTag])
          self.model.setItem(row,col,item)
          self.items.append(item)
          col += 1
        row += 1

    self.view.setColumnWidth(0,30)
    self.model.setHeaderData(0,1,"INSP")
    col = 1
    for k in self.logic.keys:
      self.view.setColumnWidth(col,15*len(k))
      self.model.setHeaderData(col,1,k)
      col += 1

  
    self.itemsexp = []
    self.modelexp = qt.QStandardItemModel()
    self.viewexp.setModel(self.modelexp)
    self.viewexp.verticalHeader().visible = False
    row = 0
    
    cycle=['exp']
    
    for i in cycle:
      for regionTag,regionValue in zip(self.logic.regionTags,self.logic.regionValues):
        color = qt.QColor()
        rgb = lut.GetTableValue(regionValue[0])
        color.setRgb(rgb[0]*255,rgb[1]*255,rgb[2]*255)
        item = qt.QStandardItem()
        item.setData(color,1)
        item.setText(str(regionTag))
        item.setData(regionTag,1)
        item.setToolTip(regionTag)
        self.modelexp.setItem(row,0,item)
        self.itemsexp.append(item)
        col = 1
        for k in self.logic.keys:
          item = qt.QStandardItem()
          item.setText("%.3f" % self.logic.labelStats[i,k,regionTag])
          self.modelexp.setItem(row,col,item)
          self.itemsexp.append(item)
          col += 1
        row += 1
    
    self.viewexp.setColumnWidth(0,30)
    self.modelexp.setHeaderData(0,1,"EXP")
    col = 1
    for k in self.logic.keys:
      self.viewexp.setColumnWidth(col,15*len(k))
      self.modelexp.setHeaderData(col,1,k)
      col += 1

  def onReload(self,moduleName="ParenchymaAnalysis"):
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
  
  def onReloadAndTest(self,moduleName="ParenchymaAnalysis"):
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


class ParenchymaAnalysisLogic:
  """Implement the logic to perform a parenchyma analysis
  Nodes are passed in as arguments.
  Results are stored as 'statistics' instance variable.
  """

  def __init__(self, inspNode, insplabelNode,expNode, explabelNode, fileName=None):
    #import numpy

    self.keys = ["LAA%-950","LAA%-910","LAA%-856","HAA%-700","HAA%-600","Mean","Std","Kurtosis","Skewness","Volume"]
    
    self.regionTags=["Global","Right","Left","RUL","RLL","RML","LUL","LLL"]
    self.regionValues=[(4,8),(4,6),(7,8),(4,4),(5,5),(6,6),(7,7),(8,8)]
    cubicMMPerVoxel = reduce(lambda x,y: x*y, insplabelNode.GetSpacing())
    litersPerCubicMM = 0.000001

    # TODO: progress and status updates
    # this->InvokeEvent(vtkParenchymaAnalysisLogic::StartLabelStats, (void*)"start label stats")

    ## Call CLI to compute parenchyma phenotypes
    ## INSP scan
    # GenerateRegionHistogramsAndParenchymaPhenotypes --max 0 --min -1200 --op insppheno.csv --oh insphisto.csv -l insplabelNode -c inspNode
    inspPhenoFile = '/var/tmp/insppheno.csv'
    inspHistoFile = '/var/tmp/insphisto.csv'
    print insplabelNode.GetID()
    print inspNode.GetID()
    parameters=dict()
    parameters['max']=0
    parameters['min']=-1200
    parameters['ipl']=insplabelNode.GetID()
    parameters['ic']=inspNode.GetID()
    parameters['op']=inspPhenoFile
    parameters['oh']=inspHistoFile

    #cliNode = slicer.cli.run(slicer.modules.generateregionhistogramsandparenchymaphenotypes,None,parameters,wait_for_completion=True)
    
    ## Get data from numpy
    
    import vtk.util.numpy_support, numpy
    
    self.labelStats = {}

    
    for cycle in ["insp","exp"]:
      if cycle == "insp":
        datalabel_arr=vtk.util.numpy_support.vtk_to_numpy(insplabelNode.GetImageData().GetPointData().GetScalars())
        data_arr=vtk.util.numpy_support.vtk_to_numpy(inspNode.GetImageData().GetPointData().GetScalars())
      if cycle == "exp":
        datalabel_arr=vtk.util.numpy_support.vtk_to_numpy(explabelNode.GetImageData().GetPointData().GetScalars())
        data_arr=vtk.util.numpy_support.vtk_to_numpy(expNode.GetImageData().GetPointData().GetScalars())
  
      for value,tag in zip(self.regionValues,self.regionTags):
        data=data_arr[(datalabel_arr>=value[0]) & (datalabel_arr<=value[1])]
        mean_data=numpy.mean(data)
        std_data=numpy.std(data)
        self.labelStats[cycle,'Mean',tag]=mean_data
        self.labelStats[cycle,'Std',tag]=std_data
        self.labelStats[cycle,'Kurtosis',tag]=self.kurt(data,mean_data,std_data)
        self.labelStats[cycle,'Skewness',tag]=self.skew(data,mean_data,std_data)
        self.labelStats[cycle,'LAA%-950',tag]=100.0*(data<-950).sum()/float(data.size)
        self.labelStats[cycle,'LAA%-910',tag]=100.0*(data<-910).sum()/float(data.size)
        self.labelStats[cycle,'LAA%-856',tag]=100.0*(data<-856).sum()/float(data.size)
        self.labelStats[cycle,'HAA%-700',tag]=100.0*(data>-700).sum()/float(data.size)
        self.labelStats[cycle,'HAA%-600',tag]=100.0*(data>-600).sum()/float(data.size)
        #self.labelStats[cycle,'Perc10',tag]=self.percentile(data,.1)
        #sefl.labelStats[cycle,'Perc15',tag]=self.percentile(data,.15)
        self.labelStats[cycle,'Volume',tag]=data.size*cubicMMPerVoxel*litersPerCubicMM;
    
    ## EXP scan
    # GenerateRegionHistogramsAndParenchymaPhenotypes --max 0 --min -1200 --op insppheno.csv --oh insphisto.csv -l insplabelNode -c inspNode
    #expPhenoFile = '/var/tmp/exppheno.csv'
    #expHistoFile = '/var/tmp/exphisto.csv'
    
    #parameters=dict()
    #parameters['max']=0
    #parameters['min']=-1200
    #parameters['ipl']=explabelNode.GetID()
    #parameters['ic']=expNode.GetID()
    #parameters['op']=expPhenoFile
    #parameters['oh']=expHistoFile

  #slicer.cli.run(slicer.modules.generateregionhistogramsandparenchymaphenotypes,None,parameters,wait_for_completion=True)
    

    ## Read files and populate array
    

    # add an entry to the LabelStats list
    #self.labelStats["Labels"].append(i)
    #self.labelStats[i,"Index"] = i
    #self.labelStats[i,"Count"] = stat1.GetVoxelCount()
    #self.labelStats[i,"Volume mm^3"] = self.labelStats[i,"Count"] * cubicMMPerVoxel
    #self.labelStats[i,"Volume cc"] = self.labelStats[i,"Volume mm^3"] * ccPerCubicMM
    #self.labelStats[i,"Min"] = stat1.GetMin()[0]
    #self.labelStats[i,"Max"] = stat1.GetMax()[0]
    #self.labelStats[i,"Mean"] = stat1.GetMean()[0]
    #self.labelStats[i,"StdDev"] = stat1.GetStandardDeviation()[0]

        # this.InvokeEvent(vtkParenchymaAnalysisLogic::LabelStatsInnerLoop, (void*)"1")

    # this.InvokeEvent(vtkParenchymaAnalysisLogic::EndLabelStats, (void*)"end label stats")

  def percentile(N, percent, key=lambda x:x):
    """
      Find the percentile of a list of values.
      
      @parameter N - is a list of values. Note N MUST BE already sorted.
      @parameter percent - a float value from 0.0 to 1.0.
      @parameter key - optional key function to compute value from each element of N.
      
      @return - the percentile of the values
      """
    import numpy
    N.sort()
    if not N:
      return None
    k = (len(N)-1) * percent
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
      return key(N[int(k)])
    d0 = key(N[int(f)]) * (c-k)
    d1 = key(N[int(c)]) * (k-f)
    return d0+d1



  def kurt(self,obs,meanVal,stdDev):
    import numpy as np
    n = float(len(obs))
    if stdDev < 0.0000001:
      kurt=1
      return kurt
    
    kurt = (n+1)*n/((n-1)*(n-2)*(n-3)) * np.sum((obs - meanVal)**4)/stdDev**4  - 3* (n-1)**2/((n-2)*(n-3))
      #num = np.sqrt((1. / len(obs)) * np.sum((obs - meanVal) ** 4))
      #denom = stdDev ** 4  # avoid losing precision with np.sqrt call
    return kurt

  def skew(self,obs,meanVal,stdDev):
    import numpy as np
    if stdDev < 0.00001:
      skew = 1
      return skew
    
    n = float(len(obs))
    num = 1/n* np.sum((obs - meanVal) ** 3)
    denom = stdDev** 3 # avoid losing precision with np.sqrt call
    return num / denom

  def createStatsChart(self, labelNode, valueToPlot, ignoreZero=False):
    """Make a MRML chart of the current stats
    """
    layoutNodes = slicer.mrmlScene.GetNodesByClass('vtkMRMLLayoutNode')
    layoutNodes.SetReferenceCount(layoutNodes.GetReferenceCount()-1)
    layoutNodes.InitTraversal()
    layoutNode = layoutNodes.GetNextItemAsObject()
    layoutNode.SetViewArrangement(slicer.vtkMRMLLayoutNode.SlicerLayoutConventionalQuantitativeView)

    chartViewNodes = slicer.mrmlScene.GetNodesByClass('vtkMRMLChartViewNode')
    chartViewNodes.SetReferenceCount(chartViewNodes.GetReferenceCount()-1)
    chartViewNodes.InitTraversal()
    chartViewNode = chartViewNodes.GetNextItemAsObject()

    arrayNode = slicer.mrmlScene.AddNode(slicer.vtkMRMLDoubleArrayNode())
    array = arrayNode.GetArray()
    samples = len(self.regionTags)
    tuples = samples
    array.SetNumberOfTuples(tuples)
    tuple = 0
    cycle = 'insp'
    for i in xrange(samples):
        index = self.regionTags[i]
        array.SetComponent(tuple, 0, i)
        array.SetComponent(tuple, 1, self.labelStats[cycle,valueToPlot,index])
        array.SetComponent(tuple, 2, 0)
        tuple += 1

    chartNode = slicer.mrmlScene.AddNode(slicer.vtkMRMLChartNode())
    chartNode.AddArray(valueToPlot, arrayNode.GetID())

    chartViewNode.SetChartNodeID(chartNode.GetID())

    chartNode.SetProperty('default', 'title', 'Parenchyma Statistics')
    chartNode.SetProperty('default', 'xAxisLabel', 'Label')
    chartNode.SetProperty('default', 'yAxisLabel', valueToPlot)
    chartNode.SetProperty('default', 'type', 'Bar');
    chartNode.SetProperty('default', 'xAxisType', 'categorical')
    chartNode.SetProperty('default', 'showLegend', 'off')

    # series level properties
    if labelNode.GetDisplayNode() != None and labelNode.GetDisplayNode().GetColorNode() != None:
      chartNode.SetProperty(valueToPlot, 'lookupTable', labelNode.GetDisplayNode().GetColorNodeID());


  def statsAsCSV(self):
    """
    print comma separated value file with header keys in quotes
    """
    csv = ""
    header = ""
    for k in self.keys[:-1]:
      header += "\"%s\"" % k + ","
    header += "\"%s\"" % self.keys[-1] + "\n"
    csv = header
    for i in self.labelStats["Labels"]:
      line = ""
      for k in self.keys[:-1]:
        line += str(self.labelStats[i,k]) + ","
      line += str(self.labelStats[i,self.keys[-1]]) + "\n"
      csv += line
    return csv

  def saveStats(self,fileName):
    fp = open(fileName, "w")
    fp.write(self.statsAsCSV())
    fp.close()


class Slicelet(object):
  """A slicer slicelet is a module widget that comes up in stand alone mode
  implemented as a python class.
  This class provides common wrapper functionality used by all slicer modlets.
  """
  # TODO: put this in a SliceletLib
  # TODO: parse command line arge


  def __init__(self, widgetClass=None):
    self.parent = qt.QFrame()
    self.parent.setLayout( qt.QVBoxLayout() )

    # TODO: should have way to pop up python interactor
    self.buttons = qt.QFrame()
    self.buttons.setLayout( qt.QHBoxLayout() )
    self.parent.layout().addWidget(self.buttons)
    self.addDataButton = qt.QPushButton("Add Data")
    self.buttons.layout().addWidget(self.addDataButton)
    self.addDataButton.connect("clicked()",slicer.app.ioManager().openAddDataDialog)
    self.loadSceneButton = qt.QPushButton("Load Scene")
    self.buttons.layout().addWidget(self.loadSceneButton)
    self.loadSceneButton.connect("clicked()",slicer.app.ioManager().openLoadSceneDialog)

    if widgetClass:
      self.widget = widgetClass(self.parent)
      self.widget.setup()
    self.parent.show()

class ParenchymaAnalysisSlicelet(Slicelet):
  """ Creates the interface when module is run as a stand alone gui app.
  """

  def __init__(self):
    super(ParenchymaAnalysisSlicelet,self).__init__(ParenchymaAnalysisWidget)


if __name__ == "__main__":
  # TODO: need a way to access and parse command line arguments
  # TODO: ideally command line args should handle --xml

  import sys
  print( sys.argv )

  slicelet = ParenchymaAnalysisSlicelet()
