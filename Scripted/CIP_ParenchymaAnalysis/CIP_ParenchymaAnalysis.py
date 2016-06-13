import os

import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *

from CIP.ui import CaseReportsWidget
from CIP.ui import PreProcessingWidget
from CIP.logic.SlicerUtil import SlicerUtil

#
# CIP_ParenchymaAnalysis
#

class CIP_ParenchymaAnalysis(ScriptedLoadableModule):
    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        import string
        parent.title = "Parenchyma Analysis"
        parent.categories = SlicerUtil.CIP_ModulesCategory
        parent.contributors = ["Applied Chest Imaging Laboratory"]
        parent.dependencies = [SlicerUtil.CIP_ModuleName]
        parent.helpText = string.Template("""
Use this module to calculate counts and volumes for different labels of a label map plus statistics on the grayscale background volume.  Note: volumes must have same dimensions.  See <a href=\"$a/Documentation/$b.$c/Modules/ParenchymaAnalysis\">$a/Documentation/$b.$c/Modules/ParenchymaAnalysis</a> for more information.
    """).substitute({'a': parent.slicerWikiUrl, 'b': slicer.app.majorVersion, 'c': slicer.app.minorVersion})
        parent.acknowledgementText = """
    Supported by NA-MIC, NAC, BIRN, NCIGT, and the Slicer Community. See http://www.slicer.org for details.  Module implemented by Steve Pieper.
    """
        self.parent = parent

#
# qSlicerPythonModuleExampleWidget
#

class CIP_ParenchymaAnalysisWidget(ScriptedLoadableModuleWidget):
    @property
    def moduleName(self):
        return os.path.basename(__file__).replace(".py", "")

    def __init__(self, parent=None):
        ScriptedLoadableModuleWidget.__init__(self, parent)

        self.chartOptions = (
        "LAA%-950", "LAA%-910", "LAA%-856", "HAA%-700", "HAA%-600", "Mean", "Std", "Kurtosis", "Skewness", "Volume")
        self.storedColumnNames = ["Region", "LAA%-950", "LAA%-910", "LAA%-856", "HAA%-700", "HAA%-600", "Mean", "Std",
                                  "Kurtosis", "Skewness", "Volume"]
        self.rTags = (
        "Global", "Right", "Left", "RUL", "RLL", "RML", "LUL", "LLL", "LUT", "LMT", "LLT", "RUT", "RMT", "RLT")
        if not parent:
            self.parent = slicer.qMRMLWidget()
            self.parent.setLayout(qt.QVBoxLayout())
            self.parent.setMRMLScene(slicer.mrmlScene)
        else:
            self.parent = parent
        self.logic = None
        self.CTNode = None
        self.labelNode = None
        # self.expNode = None
        # self.explabelNode = None
        self.fileName = None
        self.fileDialog = None

        if not parent:
            self.setup()
            self.CTSelector.setMRMLScene(slicer.mrmlScene)
            # self.expSelector.setMRMLScene(slicer.mrmlScene)
            self.labelSelector.setMRMLScene(slicer.mrmlScene)
            # self.explabelSelector.setMRMLScene(slicer.mrmlScene)
            self.parent.show()
            
    def enter(self):
        if self.labelSelector.currentNode():
            for color in ['Red', 'Yellow', 'Green']:
                slicer.app.layoutManager().sliceWidget(color).sliceLogic().GetSliceCompositeNode().SetLabelVolumeID(self.labelSelector.currentNode().GetID())            
    def exit(self):
        for color in ['Red', 'Yellow', 'Green']:
                slicer.app.layoutManager().sliceWidget(color).sliceLogic().GetSliceCompositeNode().SetLabelVolumeID('None')

    def setup(self):
        ScriptedLoadableModuleWidget.setup(self)

        #
        # the inps volume selector
        #
        parametersCollapsibleButton = ctk.ctkCollapsibleButton()
        parametersCollapsibleButton.text = "IO Volumes"
        self.parent.layout().addWidget(parametersCollapsibleButton)

        # Layout within the dummy collapsible button
        parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)
        parametersFormLayout.setVerticalSpacing(5)

        self.CTSelector = slicer.qMRMLNodeComboBox()
        self.CTSelector.nodeTypes = (("vtkMRMLScalarVolumeNode"), "")
        self.CTSelector.addAttribute("vtkMRMLScalarVolumeNode", "LabelMap", 0)
        self.CTSelector.selectNodeUponCreation = False
        self.CTSelector.addEnabled = False
        self.CTSelector.removeEnabled = False
        self.CTSelector.noneEnabled = True
        self.CTSelector.showHidden = False
        self.CTSelector.showChildNodeTypes = False
        self.CTSelector.setMRMLScene(slicer.mrmlScene)
        self.CTSelector.setToolTip("Pick the CT image to work on.")
        parametersFormLayout.addRow("Input CT Volume: ", self.CTSelector)

        #
        # the label map volume selector
        #
        self.labelSelector = slicer.qMRMLNodeComboBox()
        # self.labelSelector.nodeTypes = ( ("vtkMRMLScalarVolumeNode"), "" )
        # self.labelSelector.addAttribute( "vtkMRMLScalarVolumeNode", "LabelMap", 1 )
        self.labelSelector.nodeTypes = (("vtkMRMLLabelMapVolumeNode"), "")
        self.labelSelector.selectNodeUponCreation = True
        self.labelSelector.addEnabled = False
        self.labelSelector.removeEnabled = False
        self.labelSelector.noneEnabled = True
        self.labelSelector.showHidden = False
        self.labelSelector.showChildNodeTypes = False
        self.labelSelector.setMRMLScene(slicer.mrmlScene)
        self.labelSelector.setToolTip("Pick the label map to the algorithm.")
        parametersFormLayout.addRow("Label Map Volume: ", self.labelSelector)

        # Image filtering section
        self.preProcessingWidget = PreProcessingWidget(self.moduleName, parentWidget=self.parent)
        self.preProcessingWidget.setup()

        # Apply button
        self.applyButton = qt.QPushButton("Apply")
        self.applyButton.toolTip = "Calculate Parenchyma Phenotypes."
        self.applyButton.enabled = False
        self.applyButton.setFixedSize(300, 30)
        self.parent.layout().addWidget(self.applyButton, 0, 4)

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
        # HistSectionTitle.setStyleSheet('border: 1px solid white; color: black')
        self.HistSection.layout().addWidget(HistSectionTitle)

        self.histogramCheckBoxes = []
        self.histFrame = qt.QFrame()
        # self.histFrame.setStyleSheet('border: 1px solid white')
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
        self.chartBox.enabled = False

        self.reportsWidget = CaseReportsWidget(self.moduleName, columnNames=self.storedColumnNames,
                                               parentWidget=self.parent)
        self.reportsWidget.setup()
        self.reportsWidget.saveButton.enabled = False
        self.reportsWidget.openButton.enabled = False
        self.reportsWidget.exportButton.enabled = False
        self.reportsWidget.removeButton.enabled = False
        #    self.reportsWidget.openButton.hide()

        # Add vertical spacer
        self.parent.layout().addStretch(1)

        # connections
        self.applyButton.connect('clicked()', self.onApply)
        self.chartButton.connect('clicked()', self.onChart)

        self.reportsWidget.addObservable(self.reportsWidget.EVENT_SAVE_BUTTON_CLICKED, self.onSaveReport)
        self.CTSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.onCTSelect)
        self.labelSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.onLabelSelect)

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
        self.applyButton.enabled = bool(self.CTNode)  # and bool(self.labelNode)
        self.preProcessingWidget.enableFilteringFrame(bool(self.CTNode))
        self.preProcessingWidget.enableLMFrame(bool(not self.labelNode))
        if self.CTNode:
            for color in ['Red', 'Yellow', 'Green']:
                slicer.app.layoutManager().sliceWidget(color).sliceLogic().GetSliceCompositeNode().SetBackgroundVolumeID(self.CTNode.GetID())
        else:
            for color in ['Red', 'Yellow', 'Green']:
                slicer.app.layoutManager().sliceWidget(color).sliceLogic().GetSliceCompositeNode().SetBackgroundVolumeID('None')
            

    def onLabelSelect(self, node):
        self.labelNode = node
        self.applyButton.enabled = bool(self.CTNode)  # and bool(self.labelNode)
        self.preProcessingWidget.enableFilteringFrame(bool(self.CTNode))
        self.preProcessingWidget.enableLMFrame(bool(not self.labelNode))        
        SlicerUtil.changeLabelmapOpacity(0.5)
        if self.labelNode:
            self.preProcessingWidget.filterApplication.setChecked(1)
            self.preProcessingWidget.filterApplication.setEnabled(0)
            for color in ['Red', 'Yellow', 'Green']:
                slicer.app.layoutManager().sliceWidget(color).sliceLogic().GetSliceCompositeNode().SetLabelVolumeID(self.labelNode.GetID())
        else:
            self.preProcessingWidget.filterApplication.setChecked(0)
            self.preProcessingWidget.filterApplication.setEnabled(1)
            for color in ['Red', 'Yellow', 'Green']:
                slicer.app.layoutManager().sliceWidget(color).sliceLogic().GetSliceCompositeNode().SetLabelVolumeID('None')            

    def inputVolumesAreValid(self):
        """Verify that volumes are compatible with label calculation
        algorithm assumptions"""
        if not self.CTNode:  # or not self.labelNode:
            qt.QMessageBox.warning(slicer.util.mainWindow(),
                                   "Parenchyma Analysis", "Please select a CT Input Volume.")
            return False
        if not self.CTNode.GetImageData():  # or not self.labelNode.GetImageData():
            qt.QMessageBox.warning(slicer.util.mainWindow(),
                                   "Parenchyma Analysis", "Please select a CT Input Volume.")
            return False
        if not self.labelNode or not self.labelNode.GetImageData():
            warning = self.preProcessingWidget.warningMessageForLM()
            if warning == 16384:
                self.createLungLabelMap()
            else:
                qt.QMessageBox.warning(slicer.util.mainWindow(),
                                       "Parenchyma Analysis", "Please select a Lung Label Map.")
                return False
            return True
        if self.CTNode.GetImageData().GetDimensions() != self.labelNode.GetImageData().GetDimensions():
            qt.QMessageBox.warning(slicer.util.mainWindow(),
                                   "Parenchyma Analysis", "Input Volumes do not have the same geometry.")
            return False

#        if self.preProcessingWidget.filterOnRadioButton.checked:
#            self.preProcessingWidget.filterApplication.setChecked(1)
        return True

    def filterInputCT(self):
        self.applyButton.enabled = False
        self.applyButton.text = "Filtering..."
        # TODO: why doesn't processEvents alone make the label text change?
        self.applyButton.repaint()
        slicer.app.processEvents()

        self.preProcessingWidget.filterInputCT(self.CTNode)

    def createLungLabelMap(self):
        """Create the lung label map
        """
        self.applyButton.enabled = False
        if self.preProcessingWidget.filterOnRadioButton.checked: # and not self.preProcessingWidget.filterApplication.checked:
            self.filterInputCT()

        inputNode = self.CTNode

        self.applyButton.text = "Creating Label Map..."
        # TODO: why doesn't processEvents alone make the label text change?
        self.applyButton.repaint()
        slicer.app.processEvents()

        self.labelNode = slicer.mrmlScene.AddNode(slicer.vtkMRMLLabelMapVolumeNode())
        name = inputNode.GetName() + '_partialLungLabelMap'
        self.labelNode.SetName(slicer.mrmlScene.GenerateUniqueName(name))

        self.preProcessingWidget.createPartialLM(inputNode, self.labelNode)
        SlicerUtil.changeLabelmapOpacity(0.5)

    def onApply(self):
        """Calculate the parenchyma analysis
        """
        if not self.inputVolumesAreValid():
            return

        self.applyButton.enabled = False

        if self.preProcessingWidget.filterOnRadioButton.checked and self.preProcessingWidget.filterApplication.checked:
            self.filterInputCT()

        self.applyButton.text = "Analysing..."
        # TODO: why doesn't processEvents alone make the label text change?
        self.applyButton.repaint()
        slicer.app.processEvents()

        self.logic = CIP_ParenchymaAnalysisLogic(self.CTNode, self.labelNode)
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
        self.reportsWidget.saveButton.enabled = True
        self.reportsWidget.openButton.enabled = True
        self.reportsWidget.exportButton.enabled = True
        self.reportsWidget.removeButton.enabled = True

        self.applyButton.enabled = True
        self.applyButton.text = "Apply"
        
        for color in ['Red', 'Yellow', 'Green']:
            slicer.app.layoutManager().sliceWidget(color).sliceLogic().GetSliceCompositeNode().SetBackgroundVolumeID(self.CTNode.GetID())
            
        self.labelSelector.setCurrentNode(self.labelNode)

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
        self.logic.createStatsChart(self.labelNode, valueToPlot)

    def onSaveReport(self):
        """ Save the current values in a persistent csv file
        """
        self.logic.statsAsCSV(self.reportsWidget)

    def onFileSelected(self, fileName):
        self.logic.saveStats(fileName)

    def populateStats(self):
        if not self.logic:
            return
        displayNode = self.labelNode.GetDisplayNode()
        colorNode = displayNode.GetColorNode()
        lut = colorNode.GetLookupTable()
        self.items = []
        self.model = qt.QStandardItemModel()
        self.view.setModel(self.model)
        self.view.verticalHeader().visible = False
        row = 0

        for regionTag, regionValue in zip(self.logic.regionTags, self.logic.regionValues):
            color = qt.QColor()
            rgb = lut.GetTableValue(regionValue[0])
            color.setRgb(rgb[0] * 255, rgb[1] * 255, rgb[2] * 255)
            item = qt.QStandardItem()
            item.setData(color, 1)
            item.setText(str(regionTag))
            item.setData(regionTag, 1)
            item.setToolTip(regionTag)
            item.setTextAlignment(1)
            self.model.setItem(row, 0, item)
            self.items.append(item)
            col = 1
            for k in self.logic.keys:
                item = qt.QStandardItem()
                item.setText("%.3f" % self.logic.labelStats[k, regionTag])
                item.setTextAlignment(4)
                self.view.setColumnWidth(col, 15 * len(item.text()))
                self.model.setItem(row, col, item)
                self.items.append(item)
                col += 1
            row += 1

        self.view.setColumnWidth(0, 15 * len('Region'))
        self.model.setHeaderData(0, 1, "Region")
        col = 1
        for k in self.logic.keys:
            # self.view.setColumnWidth(col,15*len(k))
            self.model.setHeaderData(col, 1, k)
            col += 1

class CIP_ParenchymaAnalysisLogic(ScriptedLoadableModuleLogic):
    """Implement the logic to perform a parenchyma analysis
    Nodes are passed in as arguments.
    Results are stored as 'statistics' instance variable.
    """
    __preventDialogs__ = False

    def __init__(self, CTNode, labelNode, fileName=None):
        self.keys = ["LAA%-950", "LAA%-910", "LAA%-856", "HAA%-700", "HAA%-600", "Mean", "Std", "Kurtosis", "Skewness",
                     "Volume"]

        rTags = ["Global", "Right", "Right", "Right", "Left", "Left", "RUL", "RLL", "RML", "LUL", "LLL", "LUT", "LMT",
                 "LLT", "RUT", "RMT", "RLT"]
        self.regionTags = []
        self.regionValues = [(1, 14), (2, 2), (4, 6), (12, 14), (3, 3), (7, 11), (4, 4), (5, 5), (6, 6), (7, 7), (8, 8),
                             (9, 9), (10, 10), (11, 11), (12, 12), (13, 13), (14, 14)]
        self.valuesDictionary = {}
        cubicMMPerVoxel = reduce(lambda x, y: x * y, CTNode.GetSpacing())
        litersPerCubicMM = 0.000001

        # TODO: progress and status updates
        # this->InvokeEvent(vtkParenchymaAnalysisLogic::StartLabelStats, (void*)"start label stats")

        ## Call CLI to compute parenchyma phenotypes
        ## CT scan
        # GenerateRegionHistogramsAndParenchymaPhenotypes --max 0 --min -1200 --op CTpheno.csv --oh CThisto.csv -l labelNode -c CTNode
        CTPhenoFile = '/var/tmp/CTpheno.csv'
        CTHistoFile = '/var/tmp/CThisto.csv'

        parameters = dict()
        parameters['max'] = 0
        parameters['min'] = -1200
        parameters['ipl'] = labelNode.GetID()
        parameters['ic'] = CTNode.GetID()
        parameters['op'] = CTPhenoFile
        parameters['oh'] = CTHistoFile

        # cliNode = slicer.cli.run(slicer.modules.generateregionhistogramsandparenchymaphenotypes,None,parameters,wait_for_completion=True)

        ## Get data from numpy
        import vtk.util.numpy_support, numpy

        self.labelStats = {}

        self.regionHists = {}
        self.regionBins = {}

        datalabel_arr = vtk.util.numpy_support.vtk_to_numpy(labelNode.GetImageData().GetPointData().GetScalars())
        data_arr = vtk.util.numpy_support.vtk_to_numpy(CTNode.GetImageData().GetPointData().GetScalars())

        for value, tag in zip(self.regionValues, rTags):
            data = data_arr[(datalabel_arr >= value[0]) & (datalabel_arr <= value[1])]

            if data.any():
                mean_data = numpy.mean(data)
                std_data = numpy.std(data)
                self.labelStats['Mean', tag] = mean_data
                self.labelStats['Std', tag] = std_data
                self.labelStats['Kurtosis', tag] = self.kurt(data, mean_data, std_data)
                self.labelStats['Skewness', tag] = self.skew(data, mean_data, std_data)
                self.labelStats['LAA%-950', tag] = 100.0 * (data < -950).sum() / float(data.size)
                self.labelStats['LAA%-910', tag] = 100.0 * (data < -910).sum() / float(data.size)
                self.labelStats['LAA%-856', tag] = 100.0 * (data < -856).sum() / float(data.size)
                self.labelStats['HAA%-700', tag] = 100.0 * (data > -700).sum() / float(data.size)
                self.labelStats['HAA%-600', tag] = 100.0 * (data > -600).sum() / float(data.size)
                # self.labelStats[cycle,'Perc10',tag]=self.percentile(data,.1)
                # self.labelStats[cycle,'Perc15',tag]=self.percentile(data,.15)
                self.labelStats['Volume', tag] = data.size * cubicMMPerVoxel * litersPerCubicMM;

                # Compute histograms
                data = data[data < -350]
                binContainers = numpy.arange(data.min(), data.max() + 2)
                histogram, bins = numpy.histogram(data, bins=binContainers, density=False)
                self.regionHists[tag] = histogram
                self.regionBins[tag] = bins

                self.regionTags.append(tag)

                self.valuesDictionary[tag] = value

                ## Read files and populate array

                # add an entry to the LabelStats list
                # self.labelStats["Labels"].append(i)
                # self.labelStats[i,"Index"] = i
                # self.labelStats[i,"Count"] = stat1.GetVoxelCount()
                # self.labelStats[i,"Volume mm^3"] = self.labelStats[i,"Count"] * cubicMMPerVoxel
                # self.labelStats[i,"Volume cc"] = self.labelStats[i,"Volume mm^3"] * ccPerCubicMM
                # self.labelStats[i,"Min"] = stat1.GetMin()[0]
                # self.labelStats[i,"Max"] = stat1.GetMax()[0]
                # self.labelStats[i,"Mean"] = stat1.GetMean()[0]
                # self.labelStats[i,"StdDev"] = stat1.GetStandardDeviation()[0]

                # this.InvokeEvent(vtkParenchymaAnalysisLogic::LabelStatsInnerLoop, (void*)"1")

                # this.InvokeEvent(vtkParenchymaAnalysisLogic::EndLabelStats, (void*)"end label stats")

    def percentile(N, percent, key=lambda x: x):
        """
          Find the percentile of a list of values.

          @parameter N - is a list of values. Note N MUST BE already sorted.
          @parameter percent - a float value from 0.0 to 1.0.
          @parameter key - optional key function to compute value from each element of N.

          @return - the percentile of the values
          """
        import math
        N.sort()
        if not N:
            return None
        k = (len(N) - 1) * percent
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return key(N[int(k)])
        d0 = key(N[int(f)]) * (c - k)
        d1 = key(N[int(c)]) * (k - f)
        return d0 + d1

    def kurt(self, obs, meanVal, stdDev):
        import numpy as np
        n = float(len(obs))
        if stdDev < 0.0000001:
            kurt = 1
            return kurt

        kurt = (n + 1) * n / ((n - 1) * (n - 2) * (n - 3)) * np.sum((obs - meanVal) ** 4) / stdDev ** 4 - 3 * (
                                                                                                              n - 1) ** 2 / (
                                                                                                          (n - 2) * (
                                                                                                          n - 3))
        # num = np.sqrt((1. / len(obs)) * np.sum((obs - meanVal) ** 4))
        # denom = stdDev ** 4  # avoid losing precision with np.sqrt call
        return kurt

    def skew(self, obs, meanVal, stdDev):
        import numpy as np
        if stdDev < 0.00001:
            skew = 1
            return skew

        n = float(len(obs))
        num = 1 / n * np.sum((obs - meanVal) ** 3)
        denom = stdDev ** 3  # avoid losing precision with np.sqrt call
        return num / denom

    def statsAsCSV(self, repWidget):
        if self.labelStats is None:
            qt.QMessageBox.warning(slicer.util.mainWindow(), "Data not existing", "No statistics calculated")
            return

        for tag in self.regionTags:
            e = {}
            e['Region'] = tag
            for k in self.keys:
                e[k] = self.labelStats[k, tag]

            repWidget.saveCurrentValues(**e)

        if not self.__preventDialogs__:
            qt.QMessageBox.information(slicer.util.mainWindow(), 'Data saved', 'The data were saved successfully')

    def createStatsChart(self, labelNode, valueToPlot):
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

        for i in xrange(samples):
            index = self.regionTags[i]
            array.SetComponent(tuple, 0, i)
            array.SetComponent(tuple, 1, self.labelStats[valueToPlot, index])
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
            colorNode = labelNode.GetDisplayNode().GetColorNode()

            newDisplayNode = slicer.vtkMRMLLabelMapVolumeDisplayNode()
            newDisplayNode.SetAndObserveColorNodeID('vtkMRMLColorTableNodeFileGenericAnatomyColors.txt')
            slicer.mrmlScene.AddNode(newDisplayNode)
            newColorNode = newDisplayNode.GetColorNode()

            colorNumber = 0
            for tag in self.regionTags:
                c = [0, 0, 0, 0]
                value = self.valuesDictionary[tag]
                if value[0] == value[1]:
                    colorNode.SetColorName(value[0], tag)
                    colorNode.GetColor(value[0], c)
                    newColorNode.SetColor(colorNumber, c[0], c[1], c[2])

                newColorNode.SetColorName(colorNumber, tag)
                colorNumber += 1

            #      chartNode.SetProperty(valueToPlot, 'lookupTable', labelNode.GetDisplayNode().GetColorNodeID())
            chartNode.SetProperty(valueToPlot, 'lookupTable', newColorNode.GetID())

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
        self.parent.setLayout(qt.QVBoxLayout())

        # TODO: should have way to pop up python interactor
        self.buttons = qt.QFrame()
        self.buttons.setLayout(qt.QHBoxLayout())
        self.parent.layout().addWidget(self.buttons)
        self.addDataButton = qt.QPushButton("Add Data")
        self.buttons.layout().addWidget(self.addDataButton)
        self.addDataButton.connect("clicked()", slicer.app.ioManager().openAddDataDialog)
        self.loadSceneButton = qt.QPushButton("Load Scene")
        self.buttons.layout().addWidget(self.loadSceneButton)
        self.loadSceneButton.connect("clicked()", slicer.app.ioManager().openLoadSceneDialog)

        if widgetClass:
            self.widget = widgetClass(self.parent)
            self.widget.setup()
        self.parent.show()


class ParenchymaAnalysisSlicelet(Slicelet):
    """ Creates the interface when module is run as a stand alone gui app.
    """

    def __init__(self):
        super(ParenchymaAnalysisSlicelet, self).__init__(CIP_ParenchymaAnalysisWidget)


if __name__ == "__main__":
    # TODO: need a way to access and parse command line arguments
    # TODO: ideally command line args should handle --xml

    import sys

    print(sys.argv)

    slicelet = ParenchymaAnalysisSlicelet()
