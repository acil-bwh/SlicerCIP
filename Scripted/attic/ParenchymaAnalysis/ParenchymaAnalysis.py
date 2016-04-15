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
    self.rTags = ("Global","Right","Left","RUL","RLL","RML","LUL","LLL","LUT","LMT","LLT","RUT","RMT","RLT")
    if not parent:
      self.parent = slicer.qMRMLWidget()
      self.parent.setLayout(qt.QVBoxLayout())
      self.parent.setMRMLScene(slicer.mrmlScene)
    else:
      self.parent = parent
    self.logic = None
    self.CTNode = None
    self.CTlabelNode = None
    #self.expNode = None
    #self.explabelNode = None
    self.fileName = None
    self.fileDialog = None

    if not parent:
      self.setup()
      self.CTSelector.setMRMLScene(slicer.mrmlScene)
      #self.expSelector.setMRMLScene(slicer.mrmlScene)
      self.CTlabelSelector.setMRMLScene(slicer.mrmlScene)
      #self.explabelSelector.setMRMLScene(slicer.mrmlScene)
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
    self.CTSelectorFrame = qt.QFrame(self.parent)
    self.CTSelectorFrame.setLayout(qt.QHBoxLayout())
    self.parent.layout().addWidget(self.CTSelectorFrame)

    self.CTSelectorLabel = qt.QLabel("Input CT: ", self.CTSelectorFrame)
    self.CTSelectorLabel.setToolTip( "Select the input CT for parenchymal analysis")
    self.CTSelectorFrame.layout().addWidget(self.CTSelectorLabel)

    self.CTSelector = slicer.qMRMLNodeComboBox(self.CTSelectorFrame)
    self.CTSelector.nodeTypes = ( ("vtkMRMLScalarVolumeNode"), "" )
    self.CTSelector.addAttribute( "vtkMRMLScalarVolumeNode", "LabelMap", 0 )
    self.CTSelector.selectNodeUponCreation = False
    self.CTSelector.addEnabled = False
    self.CTSelector.removeEnabled = False
    self.CTSelector.noneEnabled = True
    self.CTSelector.showHidden = False
    self.CTSelector.showChildNodeTypes = False
    self.CTSelector.setMRMLScene( slicer.mrmlScene )
    # TODO: need to add a QLabel
    # self.CTSelector.SetLabelText( "Master Volume:" )
    self.CTSelectorFrame.layout().addWidget(self.CTSelector) 
    
    #
    # the CT label volume selector
    #
    self.CTlabelSelectorFrame = qt.QFrame()
    self.CTlabelSelectorFrame.setLayout( qt.QHBoxLayout() )
    self.parent.layout().addWidget( self.CTlabelSelectorFrame )

    self.CTlabelSelectorLabel = qt.QLabel()
    self.CTlabelSelectorLabel.setText( "Select the CT Label Map: " )
    self.CTlabelSelectorFrame.layout().addWidget( self.CTlabelSelectorLabel )

    self.CTlabelSelector = slicer.qMRMLNodeComboBox()
    #self.CTlabelSelector.nodeTypes = ( "vtkMRMLScalarVolumeNode", "" )
    #self.CTlabelSelector.addAttribute( "vtkMRMLScalarVolumeNode", "LabelMap", "1" )
    self.CTlabelSelector.nodeTypes = ( "vtkMRMLLabelMapVolumeNode", "" )

    # todo addAttribute
    self.CTlabelSelector.selectNodeUponCreation = False
    self.CTlabelSelector.addEnabled = False
    self.CTlabelSelector.noneEnabled = True
    self.CTlabelSelector.removeEnabled = False
    self.CTlabelSelector.showHidden = False
    self.CTlabelSelector.showChildNodeTypes = False
    self.CTlabelSelector.setMRMLScene( slicer.mrmlScene )
    self.CTlabelSelector.setToolTip( "CT label map" )
    self.CTlabelSelectorFrame.layout().addWidget( self.CTlabelSelector )

    # Image filtering section
    self.FilteringCollapsibleButton = ctk.ctkCollapsibleButton()
    self.FilteringCollapsibleButton.text = "CT Image Filtering"
    self.FilteringCollapsibleButton.setChecked(False)
    self.FilteringCollapsibleButton.enabled = True
    self.parent.layout().addWidget(self.FilteringCollapsibleButton)
    filteringFormLayout = qt.QVBoxLayout(self.FilteringCollapsibleButton)
    self.filteringOption = qt.QComboBox()
    self.filteringOptions = ("NLM Filter", "Median Filter", "Gaussian Blur Filter")
    self.filteringOption.addItems(self.filteringOptions)
    filteringFormLayout.layout().addWidget(self.filteringOption)

    # NLM Filter Params    
    self.NLMParams = qt.QFrame()
    self.NLMParams.setLayout(qt.QVBoxLayout())
    self.NLMParams.show()
    filteringFormLayout.layout().addWidget(self.NLMParams)
    self.NLMDimensionBox = qt.QFrame()
    self.NLMDimensionBox.setLayout(qt.QHBoxLayout())
    self.NLMDimensionLabel = qt.QLabel()
    self.NLMDimensionLabel.setText('Dimensions: ')
    self.NLMDimensionLabel.setToolTip('Choose if the filter has to operate in 2D or 3D.')
    self.NLMDimensionBox.layout().addWidget(self.NLMDimensionLabel)
    self.NLMDimOption = qt.QComboBox()
    self.DimOptions = ("2D","3D")
    self.NLMDimOption.addItems(self.DimOptions)
    self.NLMDimensionBox.layout().addWidget(self.NLMDimOption,0)
    self.NLMParams.layout().addWidget(self.NLMDimensionBox)
    
    self.NLMStrengthBox = qt.QFrame()
    self.NLMStrengthBox.setLayout(qt.QHBoxLayout())
    self.NLMStrengthLabel = qt.QLabel()
    self.NLMStrengthLabel.setText('Filter Strength: ')
    self.NLMStrengthLabel.setToolTip('Choose strength of the filtering process.')
    self.NLMStrengthBox.layout().addWidget(self.NLMStrengthLabel)
    self.NLMStrengthOption= qt.QComboBox()
    self.StrengthOptions = ("Smooth","Medium","Heavy")
    self.NLMStrengthOption.addItems(self.StrengthOptions)
    self.NLMStrengthBox.layout().addWidget(self.NLMStrengthOption,0)
    self.NLMParams.layout().addWidget(self.NLMStrengthBox)

    # Median Filter Params    
    self.medianParams = qt.QFrame()
    self.medianParams.setLayout(qt.QVBoxLayout())
    self.medianParams.hide()
    filteringFormLayout.layout().addWidget(self.medianParams)
    self.medianBox = qt.QFrame()
    self.medianBox.setLayout(qt.QHBoxLayout())
    self.medianLabel = qt.QLabel()
    self.medianLabel.setText('Neighborhood Size: ')
    self.medianLabel.setToolTip('The size of the neighborhood in each dimension')
    self.medianBox.layout().addWidget(self.medianLabel)
    self.medianSpinBox = qt.QDoubleSpinBox()
    self.medianSpinBox.setValue(1.0)
    self.medianSpinBox.setDecimals(1)
    self.medianSpinBox.setSingleStep(0.1)
    self.medianBox.layout().addWidget(self.medianSpinBox)
    self.medianParams.layout().addWidget(self.medianBox)
    
    # Gaussian Blur Filter Params    
    self.gaussianParams = qt.QFrame()
    self.gaussianParams.setLayout(qt.QVBoxLayout())
    self.gaussianParams.hide()
    filteringFormLayout.layout().addWidget(self.gaussianParams)
    self.gaussianBox = qt.QFrame()
    self.gaussianBox.setLayout(qt.QHBoxLayout())
    self.gaussianLabel = qt.QLabel()
    self.gaussianLabel.setText('Sigma: ')
    self.gaussianLabel.setToolTip('Sigma value in physical units (e.g. mm) of the Gaussian kernel')
    self.gaussianBox.layout().addWidget(self.gaussianLabel)
    self.gaussianSpinBox = qt.QDoubleSpinBox()
    self.gaussianSpinBox.setValue(1.0)
    self.gaussianSpinBox.setDecimals(1)
    self.gaussianSpinBox.setSingleStep(0.1)
    self.gaussianBox.layout().addWidget(self.gaussianSpinBox)
    self.gaussianParams.layout().addWidget(self.gaussianBox)
           
    # Apply Filtering button
    self.filterButton = qt.QPushButton("Apply Filter")
    self.filterButton.toolTip = "Filter the input CT image."
    self.filterButton.enabled = False
    self.filterButton.setFixedSize(150,40)
    filteringFormLayout.layout().addWidget(self.filterButton,0,4)
    
    # Add space between the two buttons
    stretchBox = qt.QFrame()
    stretchBox.setFixedHeight(20)
    filteringFormLayout.layout().addWidget(stretchBox)
 
    # Apply button
    self.applyButton = qt.QPushButton("Apply")
    self.applyButton.toolTip = "Calculate Parenchyma Phenotypes."
    self.applyButton.enabled = False
    self.applyButton.setFixedSize(300,30)
    self.parent.layout().addWidget(self.applyButton,0,4)

    # model and view for stats table
    self.view = qt.QTableView()
    self.view.sortingEnabled = True
    self.parent.layout().addWidget(self.view)

    # model and view for EXP stats table
    """self.viewexp = qt.QTableView()
    self.viewexp.sortingEnabled = True
    self.parent.layout().addWidget(self.viewexp)"""
    
    # Histogram Selection   
    self.HistSection = qt.QFrame()
    self.HistSection.setLayout(qt.QVBoxLayout())
    self.parent.layout().addWidget(self.HistSection)
    self.HistSection.setObjectName('HistSection')
    self.HistSection.setStyleSheet('#HistSection {border: 0.5px solid lightGray; }')
    HistSectionTitle = qt.QLabel()
    HistSectionTitle.setText('Histogram Section')
    #HistSectionTitle.setStyleSheet('border: 1px solid white; color: black')
    self.HistSection.layout().addWidget(HistSectionTitle)
    
    self.histogramCheckBoxes = []
    self.histFrame = qt.QFrame()
    #self.histFrame.setStyleSheet('border: 1px solid white')
    self.histFrame.setLayout(qt.QHBoxLayout())
    
    self.GlobalHistCheckBox = qt.QCheckBox()
    self.histogramCheckBoxes.append(self.GlobalHistCheckBox)
    self.histFrame.layout().addWidget(self.GlobalHistCheckBox)
   
    self.RightHistCheckBox = qt.QCheckBox()
    self.histogramCheckBoxes.append(self.RightHistCheckBox)
    self.histFrame.layout().addWidget(self.RightHistCheckBox)

    self.LeftHistCheckBox = qt.QCheckBox()
    self.histogramCheckBoxes.append(self.LeftHistCheckBox)
    self.histFrame.layout().addWidget(self.LeftHistCheckBox)

    self.RULHistCheckBox = qt.QCheckBox()
    self.histogramCheckBoxes.append(self.RULHistCheckBox)
    self.histFrame.layout().addWidget(self.RULHistCheckBox)

    self.RLLHistCheckBox = qt.QCheckBox()
    self.histogramCheckBoxes.append(self.RLLHistCheckBox)
    self.histFrame.layout().addWidget(self.RLLHistCheckBox)

    self.RMLHistCheckBox = qt.QCheckBox()
    self.histogramCheckBoxes.append(self.RMLHistCheckBox)
    self.histFrame.layout().addWidget(self.RMLHistCheckBox)

    self.LULHistCheckBox = qt.QCheckBox()
    self.histogramCheckBoxes.append(self.LULHistCheckBox)
    self.histFrame.layout().addWidget(self.LULHistCheckBox)
    
    self.LLLHistCheckBox = qt.QCheckBox()
    self.histogramCheckBoxes.append(self.LLLHistCheckBox)
    self.histFrame.layout().addWidget(self.LLLHistCheckBox)

    self.LUTHistCheckBox = qt.QCheckBox()
    self.histogramCheckBoxes.append(self.LUTHistCheckBox)
    self.histFrame.layout().addWidget(self.LUTHistCheckBox)

    self.LMTHistCheckBox = qt.QCheckBox()
    self.histogramCheckBoxes.append(self.LMTHistCheckBox)
    self.histFrame.layout().addWidget(self.LMTHistCheckBox)

    self.LLTHistCheckBox = qt.QCheckBox()
    self.histogramCheckBoxes.append(self.LLTHistCheckBox)
    self.histFrame.layout().addWidget(self.LLTHistCheckBox)

    self.RUTHistCheckBox = qt.QCheckBox()
    self.histogramCheckBoxes.append(self.RUTHistCheckBox)
    self.histFrame.layout().addWidget(self.RUTHistCheckBox)

    self.RMTHistCheckBox = qt.QCheckBox()
    self.histogramCheckBoxes.append(self.RMTHistCheckBox)
    self.histFrame.layout().addWidget(self.RMTHistCheckBox)
    
    self.RLTHistCheckBox = qt.QCheckBox()
    self.histogramCheckBoxes.append(self.RLTHistCheckBox)
    self.histFrame.layout().addWidget(self.RLTHistCheckBox)
    
    for i in xrange(len(self.histogramCheckBoxes)):
      self.histogramCheckBoxes[i].setText(self.rTags[i])
      self.histogramCheckBoxes[i].hide()   
    
    self.HistSection.layout().addWidget(self.histFrame)
    self.HistSection.enabled = False
    
    # Chart button
    self.chartBox = qt.QFrame()
    self.chartBox.setObjectName("chartBox")
    self.chartBox.setStyleSheet('#chartBox {border: 0.5px solid lightGray;}') 
    self.chartBox.setLayout(qt.QVBoxLayout())
    self.parent.layout().addWidget(self.chartBox)
    chartSectionTitle = qt.QLabel()
    chartSectionTitle.setText('Chart Section')
    self.chartBox.layout().addWidget(chartSectionTitle) 
    chartFrame = qt.QFrame()
    chartFrame.setLayout(qt.QHBoxLayout())
    self.chartBox.layout().addWidget(chartFrame)  
    self.chartButton = qt.QPushButton("Chart")
    self.chartButton.toolTip = "Make a chart from the current statistics."
    chartFrame.layout().addWidget(self.chartButton)
    self.chartOption = qt.QComboBox()
    self.chartOption.addItems(self.chartOptions)
    chartFrame.layout().addWidget(self.chartOption)
    self.chartIgnoreZero = qt.QCheckBox()
    self.chartIgnoreZero.setText('Ignore Zero')
    self.chartIgnoreZero.checked = False
    self.chartIgnoreZero.setToolTip('Do not include the zero index in the chart to avoid dwarfing other bars')
    #self.chartFrame.layout().addWidget(self.chartIgnoreZero)
    self.chartBox.enabled = False

    # Save button
    self.saveButton = qt.QPushButton("Save Statistics")
    self.saveButton.toolTip = "Save statistics as a csv file."
    self.saveButton.setFixedSize(300,30)
    self.saveButton.enabled = False
    self.parent.layout().addWidget(self.saveButton,0,4)

    # Add vertical spacer
    self.parent.layout().addStretch(1)

    # connections
    self.applyButton.connect('clicked()', self.onApply)
    self.chartButton.connect('clicked()', self.onChart)
    self.saveButton.connect('clicked()', self.onSave)
    self.CTSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.onCTSelect)
    self.CTlabelSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.onCTLabelSelect)
    #self.expSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.onExpSelect)
    #self.explabelSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.onExpLabelSelect)
    
    self.filteringOption.connect('currentIndexChanged(int)',self.showFilterParams)
    self.filterButton.connect('clicked()', self.onFilterButton)
    
    self.GlobalHistCheckBox.connect('clicked()', self.onHistogram)
    self.RightHistCheckBox.connect('clicked()', self.onHistogram)
    self.LeftHistCheckBox.connect('clicked()', self.onHistogram)
    self.RULHistCheckBox.connect('clicked()', self.onHistogram)
    self.RLLHistCheckBox.connect('clicked()', self.onHistogram)
    self.RMLHistCheckBox.connect('clicked()', self.onHistogram)
    self.LULHistCheckBox.connect('clicked()', self.onHistogram)
    self.LLLHistCheckBox.connect('clicked()', self.onHistogram)
    self.LUTHistCheckBox.connect('clicked()', self.onHistogram)
    self.LMTHistCheckBox.connect('clicked()', self.onHistogram)
    self.LLTHistCheckBox.connect('clicked()', self.onHistogram)
    self.RUTHistCheckBox.connect('clicked()', self.onHistogram)
    self.RMTHistCheckBox.connect('clicked()', self.onHistogram)
    self.RLTHistCheckBox.connect('clicked()', self.onHistogram)
    

  def onCTSelect(self, node):
    self.CTNode = node
    self.applyButton.enabled = bool(self.CTNode) #and bool(self.CTlabelNode)
    self.filterButton.enabled = bool(self.CTNode)

  def onCTLabelSelect(self, node):
    self.CTlabelNode = node
    self.applyButton.enabled = bool(self.CTNode) #and bool(self.CTlabelNode)

  """def onExpSelect(self, node):
    self.expNode = node
    self.applyButton.enabled = bool(self.expNode) and bool(self.explabelNode)

  def onExpLabelSelect(self, node):
    self.explabelNode = node
    self.applyButton.enabled = bool(self.expNode) and bool(self.explabelNode)
  """
  
  def showFilterParams(self,f):
    if self.filteringOption.currentIndex == 0:
      self.gaussianParams.hide()    
      self.medianParams.hide() 
      self.NLMParams.show()
    elif self.filteringOption.currentIndex == 1:      
      self.NLMParams.hide()
      self.gaussianParams.hide()
      self.medianParams.show()
    elif self.filteringOption.currentIndex == 2:
      self.medianParams.hide()
      self.NLMParams.hide()
      self.gaussianParams.show()     
      
  def onFilterButton(self):
    self.applyButton.enabled = False
    self.filterButton.text = "Filtering..."
    # TODO: why doesn't processEvents alone make the label text change?
    self.filterButton.repaint()
    slicer.app.processEvents()  
      
    if self.filteringOption.currentIndex == 0: # NLM filter
      generatenlmfilteredimage = slicer.modules.generatenlmfilteredimage

      searchRadius = [3,3,3]
      comparisonRadius   = [5,5,5]   
      if self.NLMDimOption.currentIndex == 0: #2D filtering
        searchRadius[2] = 1
        comparisonRadius[2] = 1
   
      noisePower = 3.0
      h = 0.8
      ps = 2.0
      
      if self.NLMStrengthOption == 1:
        noisePower = 4.0
        h = 1.0
      elif self.NLMStrengthOption == 2:
        noisePower = 5.0
        h = 1.2
      
      parameters = {
          "ctFileName": self.CTNode.GetID(),
          "outputFileName": self.CTNode.GetID(),
          "iSigma": noisePower,
          "iRadiusSearch": searchRadius,
          "iRadiusComp": comparisonRadius,
          "iH": h,
          "iPs": ps,
          }
      slicer.cli.run(generatenlmfilteredimage,None,parameters,wait_for_completion=True)
    elif self.filteringOption.currentIndex == 1: # Median Filter
      generatemedianfilteredimage = slicer.modules.generatemedianfilteredimage
      parameters = {
          "ctFileName": self.CTNode.GetID(),
          "outputFileName": self.CTNode.GetID(),
          "radiusValue": self.medianSpinBox.value,
          }
      slicer.cli.run(generatemedianfilteredimage,None,parameters,wait_for_completion=True)
    elif self.filteringOption.currentIndex == 2: # Gaussian Blur Filter
      gaussianblurimagefilter = slicer.modules.gaussianblurimagefilter
      parameters = {
          "inputVolume": self.CTNode.GetID(),
          "outputVolume": self.CTNode.GetID(),
          "sigma": self.gaussianSpinBox.value,
          }
      slicer.cli.run(gaussianblurimagefilter,None,parameters,wait_for_completion=True)
      
    self.filterButton.text = "Apply Filter" 
    self.applyButton.enabled = True
      
  def inputVolumesAreValid(self):
    """Verify that volumes are compatible with label calculation
    algorithm assumptions"""
    if not self.CTNode: #or not self.CTlabelNode:
      qt.QMessageBox.warning(slicer.util.mainWindow(),
          "Parenchyma Analysis", "Please select a CT Input Volume.")
      return False
    if not self.CTNode.GetImageData(): #or not self.CTlabelNode.GetImageData():
      qt.QMessageBox.warning(slicer.util.mainWindow(),
          "Parenchyma Analysis", "Please select a CT Input Volume.")
      return False
    if not self.CTlabelNode or not self.CTlabelNode.GetImageData():
      answer = qt.QMessageBox.question(slicer.util.mainWindow(),'Parenchyma Analysis', 'Do you want to create a lung label map?', qt.QMessageBox.Yes | qt.QMessageBox.No)
      if answer == 16384:
          self.createLungLabelMap()
      else:
        qt.QMessageBox.warning(slicer.util.mainWindow(),
          "Parenchyma Analysis", "Please select a CT Label Map.")   
      return False
      
    if self.CTNode.GetImageData().GetDimensions() != self.CTlabelNode.GetImageData().GetDimensions():
      qt.QMessageBox.warning(slicer.util.mainWindow(),
          "Parenchyma Analysis", "Input Volumes do not have the same geometry.")
      return False         
    
    return True

  """def expvolumesAreValid(self):
    Verify that volumes are compatible with label calculation
      algorithm assumptions
    if not self.expNode or not self.explabelNode:
      return False
    if not self.expNode.GetImageData() or not self.explabelNode.GetImageData():
      return False
    if self.expNode.GetImageData().GetDimensions() != self.explabelNode.GetImageData().GetDimensions():
      return False
    return True"""
  
  def createLungLabelMap(self):
    """Create the lung label map
    """
    generatepartiallunglabelmap = slicer.modules.generatepartiallunglabelmap
    outputNode = slicer.mrmlScene.AddNode(slicer.vtkMRMLLabelMapVolumeNode())
    outputNode.SetName(self.CTNode.GetName() + '_partialLungLabelMap')
    parameters = {
          "ctFileName": self.CTNode.GetID(),
          "outputLungMaskFileName": outputNode.GetID(),	  
          }
    slicer.cli.run(generatepartiallunglabelmap,None,parameters,wait_for_completion=True)

  def onApply(self):
    """Calculate the parenchyma analysis
    """    
    if not self.inputVolumesAreValid():
      return

    """if not self.expvolumesAreValid():
      qt.QMessageBox.warning(slicer.util.mainWindow(),
          "Parenchyma Analysis", "Expiratory Volumes do not have the same geometry.")
      return
    """
    self.filterButton.enabled = False
    self.applyButton.text = "Working..."
    # TODO: why doesn't processEvents alone make the label text change?
    self.applyButton.repaint()
    slicer.app.processEvents()
    #self.logic = ParenchymaAnalysisLogic(self.CTNode, self.CTlabelNode,self.expNode,self.explabelNode)
    self.logic = ParenchymaAnalysisLogic(self.CTNode, self.CTlabelNode)
    self.populateStats()
    self.logic.createHistogram()
    for i in xrange(len(self.histogramCheckBoxes)):
      self.histogramCheckBoxes[i].setChecked(0)
      self.histogramCheckBoxes[i].hide()
    
    for tag in self.rTags:
      if tag in self.logic.regionTags:
        self.histogramCheckBoxes[self.rTags.index(tag)].show()    
    
    self.HistSection.enabled = True
    self.chartBox.enabled = True
    self.saveButton.enabled = True
    self.applyButton.text = "Apply" 
    self.filterButton.enabled = True
    
  def onHistogram(self):
    """Histogram of the selected region
    """    
    self.histList = []
    for i in xrange(len(self.histogramCheckBoxes)):
      if self.histogramCheckBoxes[i].checked == True:
        self.histList.append(self.rTags[i])
        
    self.logic.AddSelectedHistograms(self.histList)
    
  def onChart(self):
    """chart the parenchyma analysis
    """
    valueToPlot = self.chartOptions[self.chartOption.currentIndex]
    ignoreZero = self.chartIgnoreZero.checked
    self.logic.createStatsChart(self.CTlabelNode,valueToPlot,ignoreZero)

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
    displayNode = self.CTlabelNode.GetDisplayNode()
    colorNode = displayNode.GetColorNode()
    lut = colorNode.GetLookupTable()
    self.items = []
    self.model = qt.QStandardItemModel()
    self.view.setModel(self.model)
    self.view.verticalHeader().visible = False
    row = 0
            
    for regionTag,regionValue in zip(self.logic.regionTags,self.logic.regionValues):
      color = qt.QColor()
      rgb = lut.GetTableValue(regionValue[0])
      color.setRgb(rgb[0]*255,rgb[1]*255,rgb[2]*255)
      item = qt.QStandardItem()
      item.setData(color,1)
      item.setText(str(regionTag))
      item.setData(regionTag,1)
      item.setToolTip(regionTag)
      item.setTextAlignment(1)
      self.model.setItem(row,0,item)
      self.items.append(item)
      col = 1
      for k in self.logic.keys:
        item = qt.QStandardItem()
        item.setText("%.3f" % self.logic.labelStats[k,regionTag])
        item.setTextAlignment(4)
        self.view.setColumnWidth(col,15*len(item.text()))
        self.model.setItem(row,col,item)
        self.items.append(item)
        col += 1
      row += 1

    self.view.setColumnWidth(0,15*len('Region'))
    self.model.setHeaderData(0,1,"Region")
    col = 1
    for k in self.logic.keys:
      #self.view.setColumnWidth(col,15*len(k))
      self.model.setHeaderData(col,1,k)
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

  #def __init__(self, CTNode, CTlabelNode,expNode, explabelNode, fileName=None):
  def __init__(self, CTNode, CTlabelNode, fileName=None):
    #import numpy

    self.keys = ["LAA%-950","LAA%-910","LAA%-856","HAA%-700","HAA%-600","Mean","Std","Kurtosis","Skewness","Volume"]
    
    rTags=["Global","Right","Right","Right","Left","Left","RUL","RLL","RML","LUL","LLL","LUT","LMT","LLT","RUT","RMT","RLT"]
    self.regionTags = []
    self.regionValues=[(1,14),(2,2),(4,6),(12,14),(3,3),(7,11),(4,4),(5,5),(6,6),(7,7),(8,8),(9,9),(10,10),(10,10),(11,11),(12,12),(13,13),(14,14)]
    cubicMMPerVoxel = reduce(lambda x,y: x*y, CTlabelNode.GetSpacing())
    litersPerCubicMM = 0.000001
    
    

    # TODO: progress and status updates
    # this->InvokeEvent(vtkParenchymaAnalysisLogic::StartLabelStats, (void*)"start label stats")

    ## Call CLI to compute parenchyma phenotypes
    ## CT scan
    # GenerateRegionHistogramsAndParenchymaPhenotypes --max 0 --min -1200 --op CTpheno.csv --oh CThisto.csv -l CTlabelNode -c CTNode
    CTPhenoFile = '/var/tmp/CTpheno.csv'
    CTHistoFile = '/var/tmp/CThisto.csv'
    print CTlabelNode.GetID()
    print CTNode.GetID()
    parameters=dict()
    parameters['max']=0
    parameters['min']=-1200
    parameters['ipl']=CTlabelNode.GetID()
    parameters['ic']=CTNode.GetID()
    parameters['op']=CTPhenoFile
    parameters['oh']=CTHistoFile

    #cliNode = slicer.cli.run(slicer.modules.generateregionhistogramsandparenchymaphenotypes,None,parameters,wait_for_completion=True)
    
    ## Get data from numpy
    
    import vtk.util.numpy_support, numpy
    
    self.labelStats = {}
    
    self.regionHists = {}
    self.regionBins = {}
    
    #for cycle in ["CT"]: #"exp"]:
     # if cycle == "CT":
    datalabel_arr=vtk.util.numpy_support.vtk_to_numpy(CTlabelNode.GetImageData().GetPointData().GetScalars())
    data_arr=vtk.util.numpy_support.vtk_to_numpy(CTNode.GetImageData().GetPointData().GetScalars())
    #  if cycle == "exp":
    #    datalabel_arr=vtk.util.numpy_support.vtk_to_numpy(explabelNode.GetImageData().GetPointData().GetScalars())
    #    data_arr=vtk.util.numpy_support.vtk_to_numpy(expNode.GetImageData().GetPointData().GetScalars())
  
    for value,tag in zip(self.regionValues,rTags):
      data=data_arr[(datalabel_arr>=value[0]) & (datalabel_arr<=value[1])]
	
      if data.any():
        mean_data=numpy.mean(data)
        std_data=numpy.std(data)
        self.labelStats['Mean',tag]=mean_data
        self.labelStats['Std',tag]=std_data
        self.labelStats['Kurtosis',tag]=self.kurt(data,mean_data,std_data)
        self.labelStats['Skewness',tag]=self.skew(data,mean_data,std_data)
        self.labelStats['LAA%-950',tag]=100.0*(data<-950).sum()/float(data.size)
        self.labelStats['LAA%-910',tag]=100.0*(data<-910).sum()/float(data.size)
        self.labelStats['LAA%-856',tag]=100.0*(data<-856).sum()/float(data.size)
        self.labelStats['HAA%-700',tag]=100.0*(data>-700).sum()/float(data.size)
        self.labelStats['HAA%-600',tag]=100.0*(data>-600).sum()/float(data.size)
        #self.labelStats[cycle,'Perc10',tag]=self.percentile(data,.1)
        #self.labelStats[cycle,'Perc15',tag]=self.percentile(data,.15)
        self.labelStats['Volume',tag]=data.size*cubicMMPerVoxel*litersPerCubicMM;
      
        #Compute histograms      
        binContainers = numpy.arange(data.min(), data.max()+2)    
        histogram,bins = numpy.histogram(data, bins=binContainers)
        self.regionHists[tag] = histogram
        self.regionBins[tag] = bins
        
        self.regionTags.append(tag)

    
    ## EXP scan
    # GenerateRegionHistogramsAndParenchymaPhenotypes --max 0 --min -1200 --op CTpheno.csv --oh CThisto.csv -l CTlabelNode -c CTNode
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
    self.setChartLayout()
    chartViewNode = slicer.util.getNode('ChartView')

    arrayNode = slicer.mrmlScene.AddNode(slicer.vtkMRMLDoubleArrayNode())
    array = arrayNode.GetArray()
    samples = len(self.regionTags)
    tuples = samples
    array.SetNumberOfTuples(tuples)
    tuple = 0
    #cycle = 'CT'
    for i in xrange(samples):
        index = self.regionTags[i]
        array.SetComponent(tuple, 0, i)
        array.SetComponent(tuple, 1, self.labelStats[valueToPlot,index])
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
    
  def createHistogram(self):    
    self.setHistogramLayout()
    
    histogramViewNode = slicer.util.getNode('HistogramView')      
      
    # Show histogram
    self.histogramArrays = {}
    
    HistNode = slicer.mrmlScene.AddNode(slicer.vtkMRMLChartNode())
   
    for tag in self.regionTags:
      arrayDataNode = slicer.mrmlScene.AddNode(slicer.vtkMRMLDoubleArrayNode())
      arrayData = arrayDataNode.GetArray()
  
      histogram = self.regionHists[tag]
      bins = self.regionBins[tag]

      dataSamples = histogram.size
      dataTuples = dataSamples
      arrayData.SetNumberOfTuples(dataTuples)
      tuple = 0
    
      for i in xrange(dataSamples):
        arrayData.SetComponent(tuple, 0, bins[i])
        arrayData.SetComponent(tuple, 1, histogram[i])
        arrayData.SetComponent(tuple, 2, 0)
        tuple += 1

      self.histogramArrays[tag] = arrayDataNode   
      HistNode.AddArray(tag, arrayDataNode.GetID())

    histogramViewNode.SetChartNodeID(HistNode.GetID())

    HistNode.SetProperty('default', 'title', 'Lung Density Histogram')
    HistNode.SetProperty('default', 'xAxisLabel', 'Density (HU)')
    HistNode.SetProperty('default', 'yAxisLabel', 'Frequency')
    HistNode.SetProperty('default', 'type', 'Line');
    HistNode.SetProperty('default', 'xAxisType', 'quantitative')
    HistNode.SetProperty('default', 'showLegend', 'on')  
          
      
  def AddSelectedHistograms(self, histogramsList):
    histogramViewNode = slicer.util.getNode('HistogramView') 

    HistNode = slicer.mrmlScene.AddNode(slicer.vtkMRMLChartNode())

    for tag in histogramsList:
      HistNode.AddArray(tag, self.histogramArrays[tag].GetID())

    histogramViewNode.SetChartNodeID(HistNode.GetID())
    
    HistNode.SetProperty('default', 'title', 'Lung Density Histogram')
    HistNode.SetProperty('default', 'xAxisLabel', 'Density (HU)')
    HistNode.SetProperty('default', 'yAxisLabel', 'Frequency')
    HistNode.SetProperty('default', 'type', 'Line');
    HistNode.SetProperty('default', 'xAxisType', 'quantitative')
    HistNode.SetProperty('default', 'showLegend', 'on')
    
    
  def setHistogramLayout(self):
    customLayout = ("<layout type=\"vertical\" split=\"false\" >"
                    " <item>"
                    "  <layout type=\"horizontal\">"
                    "   <item>"
                    "    <view class=\"vtkMRMLViewNode\" singletontag=\"1\">"
                    "     <property name=\"viewlabel\" action=\"default\">1</property>"
                    "    </view>"
                    "   </item>"
                    "   <item>"
                    "    <view class=\"vtkMRMLChartViewNode\" singletontag=\"HistogramView\">"
                    "     <property name=\"viewlabel\" action=\"default\">HV</property>"
                    "    </view>"
                    "   </item>"
                    "  </layout>"
                    " </item>"
                    " <item>"
                    "  <layout type=\"horizontal\">"
                    "   <item>"
                    "    <view class=\"vtkMRMLSliceNode\" singletontag=\"Red\">"
                    "     <property name=\"orientation\" action=\"default\">Axial</property>"
                    "     <property name=\"viewlabel\" action=\"default\">R</property>"
                    "     <property name=\"viewcolor\" action=\"default\">#F34A33</property>"
                    "    </view>"
                    "   </item>"
                    "   <item>"
                    "    <view class=\"vtkMRMLSliceNode\" singletontag=\"Yellow\">"
                    "     <property name=\"orientation\" action=\"default\">Sagittal</property>"
                    "     <property name=\"viewlabel\" action=\"default\">Y</property>"
                    "     <property name=\"viewcolor\" action=\"default\">#EDD54C</property>"
                    "    </view>"
                    "   </item>"
                    "   <item>"
                    "    <view class=\"vtkMRMLSliceNode\" singletontag=\"Green\">"
                    "     <property name=\"orientation\" action=\"default\">Coronal</property>"
                    "     <property name=\"viewlabel\" action=\"default\">G</property>"
                    "     <property name=\"viewcolor\" action=\"default\">#6EB04B</property>"
                    "    </view>"
                    "   </item>"
                    "  </layout>"
                    " </item>"
                    "</layout>")
    
    layoutManager = slicer.app.layoutManager()
    customLayoutId = 501
    layoutManager.layoutLogic().GetLayoutNode().AddLayoutDescription(customLayoutId, customLayout)
    layoutManager.setLayout(customLayoutId)
    
  def setChartLayout(self):
    customLayout = ("<layout type=\"vertical\" split=\"false\" >"
                    " <item>"
                    "  <layout type=\"horizontal\">"
                    "   <item>"
                    "    <view class=\"vtkMRMLViewNode\" singletontag=\"1\">"
                    "     <property name=\"viewlabel\" action=\"default\">1</property>"
                    "    </view>"
                    "   </item>"
                    "   <item>"
                    "    <view class=\"vtkMRMLChartViewNode\" singletontag=\"HistogramView\">"
                    "     <property name=\"viewlabel\" action=\"default\">HV</property>"
                    "    </view>"
                    "   </item>"
                    "   <item>"
                    "    <view class=\"vtkMRMLChartViewNode\" singletontag=\"ChartView\">"
                    "     <property name=\"viewlabel\" action=\"default\">CV</property>"
                    "    </view>"
                    "   </item>"
                    "  </layout>"
                    " </item>"
                    " <item>"
                    "  <layout type=\"horizontal\">"
                    "   <item>"
                    "    <view class=\"vtkMRMLSliceNode\" singletontag=\"Red\">"
                    "     <property name=\"orientation\" action=\"default\">Axial</property>"
                    "     <property name=\"viewlabel\" action=\"default\">R</property>"
                    "     <property name=\"viewcolor\" action=\"default\">#F34A33</property>"
                    "    </view>"
                    "   </item>"
                    "   <item>"
                    "    <view class=\"vtkMRMLSliceNode\" singletontag=\"Yellow\">"
                    "     <property name=\"orientation\" action=\"default\">Sagittal</property>"
                    "     <property name=\"viewlabel\" action=\"default\">Y</property>"
                    "     <property name=\"viewcolor\" action=\"default\">#EDD54C</property>"
                    "    </view>"
                    "   </item>"
                    "   <item>"
                    "    <view class=\"vtkMRMLSliceNode\" singletontag=\"Green\">"
                    "     <property name=\"orientation\" action=\"default\">Coronal</property>"
                    "     <property name=\"viewlabel\" action=\"default\">G</property>"
                    "     <property name=\"viewcolor\" action=\"default\">#6EB04B</property>"
                    "    </view>"
                    "   </item>"
                    "  </layout>"
                    " </item>"
                    "</layout>")
    
    layoutManager = slicer.app.layoutManager()
    customLayoutId = 502
    layoutManager.layoutLogic().GetLayoutNode().AddLayoutDescription(customLayoutId, customLayout)
    layoutManager.setLayout(customLayoutId)


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
