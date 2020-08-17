import os
from collections import OrderedDict

import vtk, qt, ctk, slicer
import SimpleITK as sitk

from slicer.ScriptedLoadableModule import *

from CIP.ui import CaseReportsWidget
from CIP.ui import PreProcessingWidget
from CIP.ui import PdfReporter
from CIP.logic.SlicerUtil import SlicerUtil
from CIP.logic.Util import Util
from CIP.logic.lung_splitter import LungSplitter as lung_splitter
from functools import reduce

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
Use this module to calculate counts and volumes for different labels of a label map plus statistics on the grayscale background volume.  Note: volumes must have same dimensions.<br>
A quick tutorial of the module can be found <a href='https://chestimagingplatform.org/files/chestimagingplatform/files/parenchymaanalysis_tutorial.pdf'>here</a><br>
See <a href=\"$a/Documentation/$b.$c/Modules/ParenchymaAnalysis\">$a/Documentation/$b.$c/Modules/ParenchymaAnalysis</a> for more information.
    """).substitute({'a': parent.slicerWikiUrl, 'b': slicer.app.majorVersion, 'c': slicer.app.minorVersion})
        parent.acknowledgementText = """
    Supported by NA-MIC, NAC, BIRN, NCIGT, and the Slicer Community. See http://www.slicer.org for details.  Module implemented by Steve Pieper.
    """
        self.parent = parent

#
# qSlicerPythonModuleExampleWidget
#

class CIP_ParenchymaAnalysisWidget(ScriptedLoadableModuleWidget):

    def __init__(self, parent=None):
        ScriptedLoadableModuleWidget.__init__(self, parent)

        self.chartOptions = (
            "LAA%-950", "LAA%-925", "LAA%-910", "LAA%-856", "HAA%-700", "HAA%-600", "HAA%-500", "HAA%-250",
            "HAA%-600-250", "Perc10", "Perc15", "Mean", "Std", "Kurtosis", "Skewness",
            "Ventilation Heterogeneity", "Mass", "Volume")

        # Build the column keys. Here all the columns are declared, but an alternative could be just:
        #self.columnsDict = CaseReportsWidget.getColumnKeysNormalizedDictionary(["Volume Name", "Region", "LAA%-950", ...])
        self.columnsDict = OrderedDict()
        self.columnsDict["VolumeName"] = "Volume Name"
        self.columnsDict["Region"] = "Region"
        self.columnsDict["LAA950"] = "LAA%-950"
        self.columnsDict["LAA925"] = "LAA%-925"
        self.columnsDict["LAA910"] = "LAA%-910"
        self.columnsDict["LAA856"] = "LAA%-856"
        self.columnsDict["HAA700"] = "HAA%-700"
        self.columnsDict["HAA600"] = "HAA%-600"
        self.columnsDict["HAA500"] = "HAA%-500"
        self.columnsDict["HAA250"] = "HAA%-250"
        self.columnsDict["HAA600250"] = "HAA%-600-250"
        self.columnsDict["Perc10"] = "Perc10"
        self.columnsDict["Perc15"] = "Perc15"
        self.columnsDict["Mean"] = "Mean"
        self.columnsDict["Std"] = "Std"
        self.columnsDict["Kurtosis"] = "Kurtosis"
        self.columnsDict["Skewness"] = "Skewness"
        self.columnsDict["VentilationHeterogeneity"] = "Ventilation Heterogeneity"
        self.columnsDict["Mass"] = "Mass"
        self.columnsDict["Volume"] = "Volume"

        self.rTags = (
        "WholeLung", "RightLung", "LeftLung", "RUL", "RML", "RLL", "LUL", "LLL", "LUT", "LMT", "LLT", "RUT", "RMT", "RLT")
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
        #
        # self.splitRadioButton = qt.QRadioButton()
        # self.splitRadioButton.setText('Split Label Map')
        # self.splitRadioButton.setChecked(0)
        # self.parent.layout().addWidget(self.splitRadioButton, 0, 3)

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
        self.HistSection.layout().addWidget(HistSectionTitle)

        self.HistogramFreqOption = qt.QCheckBox()
        self.HistogramFreqOption.setText('Frequency by region volume')
        self.HistogramFreqOption.setChecked(1)
        self.HistogramFreqOption.setToolTip('If checked, histogram multiplied by region volume will be displayed.')
        self.HistogramFreqOption.hide()

        self.histogramCheckBoxes = []
        self.histFrame = qt.QFrame()
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

        for i in range(len(self.histogramCheckBoxes)):
            self.histogramCheckBoxes[i].setText(self.rTags[i])
            self.histogramCheckBoxes[i].hide()

        self.HistSection.layout().addWidget(self.HistogramFreqOption)
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

        self.reportsWidget = CaseReportsWidget(self.moduleName, self.columnsDict, parentWidget=self.parent)
        self.reportsWidget.setup()
        self.reportsWidget.showPrintButton(True)

        # Add vertical spacer
        self.parent.layout().addStretch(1)

        # connections
        self.applyButton.connect('clicked()', self.onApply)

        self.chartButton.connect('clicked()', self.onChart)

        self.reportsWidget.addObservable(self.reportsWidget.EVENT_SAVE_BUTTON_CLICKED, self.onSaveReport)
        self.reportsWidget.addObservable(self.reportsWidget.EVENT_PRINT_BUTTON_CLICKED, self.onPrintReport)
        self.CTSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.onCTSelect)
        self.labelSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.onLabelSelect)

        self.HistogramFreqOption.connect('clicked()', self.changeHistDisplay)
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

    def cleanup(self):
        self.reportsWidget.cleanup()
        self.reportsWidget = None

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

        label_image = self.labelNode.GetImageData()
        shape = list(label_image.GetDimensions())
        input_array = vtk.util.numpy_support.vtk_to_numpy(label_image.GetPointData().GetScalars())
        original_shape = input_array.shape
        input_array = input_array.reshape(shape[2], shape[1], shape[0])  # input_array.transpose([2, 1, 0]) would not work!

        input_image = sitk.GetImageFromArray(input_array)
        input_image.SetSpacing(self.labelNode.GetSpacing())
        input_image.SetOrigin(self.labelNode.GetOrigin())

        my_lung_splitter = lung_splitter(split_thirds=True)
        split_lm = my_lung_splitter.execute(input_image)

        split = sitk.GetArrayFromImage(split_lm)

        input_aa = vtk.util.numpy_support.vtk_to_numpy(label_image.GetPointData().GetScalars())

        input_aa[:] = split.reshape(original_shape)

        self.labelNode.StorableModified()
        self.labelNode.Modified()
        self.labelNode.InvokeEvent(slicer.vtkMRMLVolumeNode.ImageDataModifiedEvent, self.labelNode)

        SlicerUtil.changeLabelmapOpacity(0.5)

    def onApply(self):
        """Calculate the parenchyma analysis
        """
        if not self.inputVolumesAreValid():
            return

        self.HistSection.enabled = False
        self.applyButton.enabled = False
        for i in range(len(self.histogramCheckBoxes)):
            self.histogramCheckBoxes[i].hide()

        if self.preProcessingWidget.filterOnRadioButton.checked and self.preProcessingWidget.filterApplication.checked:
            self.filterInputCT()

        self.applyButton.text = "Analysing..."
        # TODO: why doesn't processEvents alone make the label text change?
        self.applyButton.repaint()
        slicer.app.processEvents()

        self.logic = CIP_ParenchymaAnalysisLogic(self.CTNode, self.labelNode, self.HistogramFreqOption.checked)
        self.populateStats()
        self.logic.createHistogram(self.labelNode)
        for i in range(len(self.histogramCheckBoxes)):
            self.histogramCheckBoxes[i].setChecked(0)
            self.histogramCheckBoxes[i].hide()

        self.HistogramFreqOption.show()
        for tag in self.rTags:
            if tag in self.logic.regionTags:
                self.histogramCheckBoxes[self.rTags.index(tag)].show()
                self.histogramCheckBoxes[self.rTags.index(tag)].setChecked(1)

        self.HistSection.enabled = True
        self.chartBox.enabled = True

        self.applyButton.enabled = True
        self.applyButton.text = "Apply"
        
        for color in ['Red', 'Yellow', 'Green']:
            slicer.app.layoutManager().sliceWidget(color).sliceLogic().GetSliceCompositeNode().SetBackgroundVolumeID(self.CTNode.GetID())
            
        self.labelSelector.setCurrentNode(self.labelNode)

    def changeHistDisplay(self):
        histList = []
        for i in range(len(self.histogramCheckBoxes)):
            if self.histogramCheckBoxes[i].checked:
                histList.append(self.rTags[i])
        self.logic.ChangeHistogramFrequency(histList, byRegionVolume=self.HistogramFreqOption.checked)

    def onHistogram(self):
        """Histogram of the selected region
        """
        histList = []
        for i in range(len(self.histogramCheckBoxes)):
            if self.histogramCheckBoxes[i].checked:
                histList.append(self.rTags[i])

        self.logic.AddSelectedHistograms(histList)

    def onChart(self):
        """chart the parenchyma analysis
        """
        valueToPlot = self.chartOptions[self.chartOption.currentIndex]
        self.logic.createStatsChart(self.labelNode, valueToPlot)

    def onSaveReport(self):
        """ Save the current values in a persistent csv file
        """
        self.logic.statsAsCSV(self.reportsWidget, self.CTNode)

    def onPrintReport(self):
        """
        Print a pdf report
        """
        emphysema_image_path, ct_slice_path = self.logic.computeEmphysemaOnSlice(self.CTNode, self.labelNode,
                                                                                 op=0.5)
        pdfReporter = PdfReporter()
        # Get the values that are going to be inserted in the html template
        caseName = self.CTNode.GetName()

        values = dict()
        values["@@PATH_TO_STATIC@@"] = os.path.join(os.path.dirname(os.path.realpath(__file__)), "Resources/")
        values["@@SUBJECT@@"] = "Subject: " + str(caseName)
        values["@@GLOBAL_LEVEL@@"] = "{:.2f}%".format(self.logic.labelStats['LAA%-950','WholeLung'])
        values["@@SUMMARY@@"] = "Emphysema per region: "

        pdfRows = """"""
        for tag in self.logic.regionTags:
            pdfRows += """<tr>
              <td align="center">{} </td>
              <td align="center">{:.2f} </td>
            </tr>""".format(tag, self.logic.labelStats['LAA%-950', tag])

        values["@@TABLE_ROWS@@"] = pdfRows

        # Get the path to the html template
        htmlTemplatePath = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                        "Resources/CIP_ParenchymaAnalysisReport.html")
        # Get a list of image absolute paths that may be needed for the report. In this case, we get the ACIL logo
        imagesFileList = [SlicerUtil.ACIL_LOGO_PATH]

        values["@@EMPHYSEMA_IMAGE@@"] = emphysema_image_path
        values["@@CT_IMAGE@@"] = ct_slice_path

        # Print the report. Remember that we can optionally specify the absolute path where the report is going to
        # be stored
        pdfReporter.printPdf(htmlTemplatePath, values, self.reportPrinted, imagesFileList=imagesFileList)

    def reportPrinted(self, reportPath):
        Util.openFile(reportPath)

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

    def __init__(self, CTNode, labelNode, freq_by_region_volume=True):
        self.keys = ["LAA%-950", "LAA%-925", "LAA%-910", "LAA%-856", "HAA%-700", "HAA%-600", "HAA%-500", "HAA%-250",
                     "HAA%-600-250", "Perc10", "Perc15", "Mean", "Std", "Kurtosis", "Skewness",
                     "Ventilation Heterogeneity", "Mass", "Volume"]

        rTags = ["WholeLung", "RightLung", "RightLung", "RightLung", "LeftLung", "LeftLung", "RUL", "RML",
                 "RLL", "LUL", "LLL", "LUT", "LMT", "LLT", "RUT", "RMT", "RLT"]
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

        self.regionHists_by_region_volume = {}
        self.regionHists = {}
        self.regionBins = {}

        self.freq_by_region_volume = freq_by_region_volume

        datalabel_arr = vtk.util.numpy_support.vtk_to_numpy(labelNode.GetImageData().GetPointData().GetScalars())
        data_arr = vtk.util.numpy_support.vtk_to_numpy(CTNode.GetImageData().GetPointData().GetScalars())

        for value, tag in zip(self.regionValues, rTags):
            data = data_arr[(datalabel_arr >= value[0]) & (datalabel_arr <= value[1])]

            if data.any():
                mean_data = numpy.mean(data)
                std_data = numpy.std(data)
                self.labelStats['LAA%-950', tag] = 100.0 * (data < -950).sum() / float(data.size)
                self.labelStats['LAA%-925', tag] = 100.0 * (data < -925).sum() / float(data.size)
                self.labelStats['LAA%-910', tag] = 100.0 * (data < -910).sum() / float(data.size)
                self.labelStats['LAA%-856', tag] = 100.0 * (data < -856).sum() / float(data.size)
                self.labelStats['HAA%-700', tag] = 100.0 * (data > -700).sum() / float(data.size)
                self.labelStats['HAA%-600', tag] = 100.0 * (data > -600).sum() / float(data.size)
                self.labelStats['HAA%-500', tag] = 100.0 * (data > -500).sum() / float(data.size)
                self.labelStats['HAA%-250', tag] = 100.0 * (data > -250).sum() / float(data.size)
                self.labelStats['HAA%-600-250', tag] = 100.0 * (numpy.logical_and(data > -600,
                                                                                  data < -250)).sum() / float(data.size)
                # self.labelStats[cycle,'Perc10',tag]=self.percentile(data,.1)
                # self.labelStats[cycle,'Perc15',tag]=self.percentile(data,.15)
                self.labelStats['Perc10',tag]=numpy.percentile(data,10)
                self.labelStats['Perc15',tag]=numpy.percentile(data,15)
                self.labelStats['Mean', tag] = mean_data
                self.labelStats['Std', tag] = std_data
                self.labelStats['Kurtosis', tag] = self.kurt(data, mean_data, std_data)
                self.labelStats['Skewness', tag] = self.skew(data, mean_data, std_data)
                self.labelStats['Ventilation Heterogeneity', tag] =  self.vh(data)
                self.labelStats['Mass',tag] = self.mass(data,cubicMMPerVoxel)
                self.labelStats['Volume', tag] = data.size * cubicMMPerVoxel * litersPerCubicMM

                # Compute histograms
                data = data[data < -350]
                binContainers = numpy.arange(data.min(), data.max() + 2)
                histogram, bins = numpy.histogram(data, bins=binContainers, density=True)
                self.regionHists_by_region_volume[
                    tag] = histogram * data.size * cubicMMPerVoxel * litersPerCubicMM * 1000
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

    @staticmethod
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

    def vh(self, data):
        import numpy
        arr = data[((data > -1000) & (data <= 0))]
        # Convert to float to apply the formula
        #arr = arr.astype(numpy.float)
        # Apply formula
        arr = -arr / (arr + 1000.0)
        arr **= (1/3.0)
        return arr.std()

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

    def mass(self,data,cubicMMPerVoxel):
        # This quantity is computed in a piecewise linear form
        # according to the prescription presented in ref. [1].
        # Mass is computed in grams. First compute the
        # contribution in HU interval from -98 and below.
        import numpy as np
        pheno_val = 0.0
        HU_tmp = data[data < -98].clip(-1000)
        if HU_tmp.shape[0] > 0:
            m = (1.21e-3 - 0.93) / (-1000 + 98)
            b = 1.21e-3 + 1000 * m
            pheno_val += np.sum((m * HU_tmp + b) *  cubicMMPerVoxel * 0.001)

        # Now compute the mass contribution in the interval
        # [-98, 18] HU. Note the in the original paper, the
        # interval is defined from -98HU to 14HU, but we
        # extend in slightly here so there are no gaps in
        # coverage. The values we report in the interval
        # [14, 23] should be viewed as approximate.
        HU_tmp = data[np.logical_and(data >= -98,data <= 18)]
        if HU_tmp.shape[0] > 0:
            pheno_val += \
                np.sum((1.018 + 0.893 * HU_tmp / 1000.0) * cubicMMPerVoxel * 0.001)

        # Compute the mass contribution in the interval
        # (18, 100]
        HU_tmp = data[np.logical_and(data> 18,data <= 100)]
        if HU_tmp.shape[0] > 0:
            pheno_val += np.sum((1.003 + 1.169 * HU_tmp / 1000.0) * cubicMMPerVoxel * 0.001)

        # Compute the mass contribution in the interval > 100
        HU_tmp = data[data > 100]
        if HU_tmp.shape[0] > 0:
            pheno_val += np.sum((1.017 + 0.592 * HU_tmp / 1000.0) * cubicMMPerVoxel * 0.001)

        return pheno_val

    def statsAsCSV(self, repWidget, CTNode):
        if self.labelStats is None:
            qt.QMessageBox.warning(slicer.util.mainWindow(), "Data not existing", "No statistics calculated")
            return

        for tag in self.regionTags:
            e = {}
            e['Volume Name'] = CTNode.GetName()
            e['Region'] = tag
            for k in self.keys:
                e[k] = self.labelStats[k, tag]

            repWidget.insertRow(**e)

        if not self.__preventDialogs__:
            qt.QMessageBox.information(slicer.util.mainWindow(), 'Data saved', 'The data were saved successfully')

    def createStatsChart(self, labelNode, valueToPlot):
        """Make a MRML chart of the current stats
        """
        self.setChartLayout()
        chartViewNode = SlicerUtil.getNode('ChartView')

        arrayNode = slicer.mrmlScene.AddNode(slicer.vtkMRMLDoubleArrayNode())
        array = arrayNode.GetArray()
        samples = len(self.regionTags)
        tuples = samples
        array.SetNumberOfTuples(tuples)
        tuple = 0

        for i in range(samples):
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
        chartNode.SetProperty('default', 'type', 'Bar')
        chartNode.SetProperty('default', 'xAxisType', 'categorical')
        chartNode.SetProperty('default', 'showLegend', 'off')

        # series level properties
        if labelNode.GetDisplayNode() is not None and labelNode.GetDisplayNode().GetColorNode() is not None:
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

            chartNode.SetProperty(valueToPlot, 'lookupTable', newColorNode.GetID())

    def createHistogram(self, labelNode):
        self.setHistogramLayout()

        histogramViewNode = SlicerUtil.getNode('HistogramView')
        histogramViewNode.SetEnablePointMoveAlongX(False)
        histogramViewNode.SetEnablePointMoveAlongY(False)
        histogramViewNode.SetInteractionMode(0)

        # Show histogram
        plotChartNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLPlotChartNode", 'PlotChartNode')
        plotChartNode.SetTitle('Histogram')
        plotChartNode.SetXAxisTitle('Density (HU)')
        plotChartNode.SetYAxisTitle('Frequency')
        plotChartNode.SetYAxisRangeAuto(False)
        plotChartNode.SetYAxisRange(0, 50)

        colorNode = labelNode.GetDisplayNode().GetColorNode()
        newDisplayNode = slicer.vtkMRMLLabelMapVolumeDisplayNode()
        newDisplayNode.SetAndObserveColorNodeID('vtkMRMLColorTableNodeFileGenericAnatomyColors.txt')

        for tag in self.regionTags:
            if self.freq_by_region_volume:
                histogram = self.regionHists_by_region_volume[tag]
            else:
                histogram = self.regionHists[tag]

            bins = self.regionBins[tag]

            tableNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTableNode", 'TableNode_{}'.format(tag))
            table = tableNode.GetTable()

            arrX = vtk.vtkFloatArray()
            arrX.SetName("bins".format(tag))
            table.AddColumn(arrX)

            arrY = vtk.vtkFloatArray()
            arrY.SetName("freq_{}".format(tag))
            table.AddColumn(arrY)

            dataSamples = histogram.size
            table.SetNumberOfRows(dataSamples)

            for i in range(dataSamples):
                table.SetValue(i, 0, float(bins[i]))
                table.SetValue(i, 1, histogram[i])

            plotSeriesNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLPlotSeriesNode", tag)
            plotSeriesNode.SetAndObserveTableNodeID(tableNode.GetID())
            plotSeriesNode.SetXColumnName("bins".format(tag))
            plotSeriesNode.SetYColumnName("freq_{}".format(tag))
            plotSeriesNode.SetPlotType(slicer.vtkMRMLPlotSeriesNode.PlotTypeScatter)
            plotSeriesNode.SetLineStyle(slicer.vtkMRMLPlotSeriesNode.LineStyleSolid)
            plotSeriesNode.SetLineWidth(2.)
            plotSeriesNode.SetMarkerStyle(slicer.vtkMRMLPlotSeriesNode.MarkerStyleNone)
            # plotSeriesNode.SetUniqueColor('vtkMRMLColorTableNodeFileGenericAnatomyColors.txt')
            c = [0,0,0,0]
            if tag == 'WholeLung':
                colorNode.GetColor(0, c)
            elif tag == 'RightLung':
                colorNode.GetColor(1, c)
            elif tag == 'LeftLung':
                colorNode.GetColor(2, c)
            else:
                value = self.valuesDictionary[tag]
                colorNode.GetColor(value[0], c)

            plotSeriesNode.SetColor(c[0], c[1], c[2])
            plotChartNode.AddAndObservePlotSeriesNodeID(plotSeriesNode.GetID())

        histogramViewNode.SetPlotChartNodeID(plotChartNode.GetID())

    def ChangeHistogramFrequency(self, histogramsList, byRegionVolume=True):
        plotChartNode = SlicerUtil.getNode('PlotChartNode')
        plotChartNode.RemoveAllPlotSeriesNodeIDs()
        for tag in self.regionTags:
            if byRegionVolume:
                plotChartNode.SetYAxisRange(0, 50)
                histogram = self.regionHists_by_region_volume[tag]
            else:
                plotChartNode.SetYAxisRange(0, 0.01)
                histogram = self.regionHists[tag]

            bins = self.regionBins[tag]

            tableNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTableNode", 'TableNode_{}'.format(tag))
            table = tableNode.GetTable()

            arrX = vtk.vtkFloatArray()
            arrX.SetName("bins".format(tag))
            table.AddColumn(arrX)

            arrY = vtk.vtkFloatArray()
            arrY.SetName("freq_{}".format(tag))
            table.AddColumn(arrY)

            dataSamples = histogram.size
            table.SetNumberOfRows(dataSamples)

            for i in range(dataSamples):
                table.SetValue(i, 0, float(bins[i]))
                table.SetValue(i, 1, histogram[i])

            plotSeriesNode = SlicerUtil.getNode(tag)
            plotSeriesNode.SetAndObserveTableNodeID(tableNode.GetID())
            plotSeriesNode.SetXColumnName("bins".format(tag))
            plotSeriesNode.SetYColumnName("freq_{}".format(tag))

        self.AddSelectedHistograms(histogramsList)

    def AddSelectedHistograms(self, histogramsList):
        histogramViewNode = SlicerUtil.getNode('HistogramView')
        plotChartNode = SlicerUtil.getNode('PlotChartNode')
        plotChartNode.RemoveAllPlotSeriesNodeIDs()

        for tag in histogramsList:
            plotSeriesNode = SlicerUtil.getNode(tag)
            plotChartNode.AddAndObservePlotSeriesNodeID(plotSeriesNode.GetID())

        histogramViewNode.SetPlotChartNodeID(plotChartNode.GetID())

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
                        "    <view class=\"vtkMRMLPlotViewNode\" singletontag=\"HistogramView\">"
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
                        "    <view class=\"vtkMRMLPlotViewNode\" singletontag=\"HistogramView\">"
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

    def computeEmphysemaOnSlice(self, CTNode, labelNode, op=0.2):
        import tempfile
        import numpy as np
        import SimpleITK as sitk

        image_arr = slicer.util.array(CTNode.GetName()).transpose([2, 1, 0])
        label_arr = slicer.util.array(labelNode.GetName()).transpose([2, 1, 0])

        sl = int(image_arr.shape[2] / 2.0)

        ct_slice = image_arr[:, sl, :]
        slice_label = label_arr[:, sl, :]
        slice_label[np.logical_and(slice_label > 1, slice_label < 512)] = 1
        slice_label[slice_label >= 512] = 0

        emph_slice = ct_slice.copy()

        emph_slice[emph_slice >= -950.0] = 0
        emph_slice[np.logical_and(emph_slice >= -3000.0, emph_slice < -950.0)] = 1
        emph_slice = emph_slice.astype(np.uint8)

        emph_slice *= slice_label

        sitk_ct_slice = sitk.GetImageFromArray(ct_slice.transpose())
        sitk_emph_slice = sitk.GetImageFromArray(emph_slice.transpose())

        sitk_ct_slice = sitk.Cast(sitk.IntensityWindowing(sitk_ct_slice, windowMinimum=-1200, windowMaximum=200,
                                                          outputMinimum=0, outputMaximum=255), sitk.sitkUInt8)

        label_overlay = sitk.LabelOverlay(sitk_ct_slice, sitk_emph_slice, opacity=op, colormap=[255, 51, 51])
        # label_overlay = sitk.LabelOverlay(sitk_ct_slice, sitk_emph_slice, opacity=op)

        tmpFolder = tempfile.mkdtemp()
        img_path = os.path.join(tmpFolder, "tmpImg__.png")
        img_path_CT = os.path.join(tmpFolder, "tmpImgCT__.png")

        sitk.WriteImage(sitk.Flip(label_overlay, flipAxes=(False, True)), img_path)
        sitk.WriteImage(sitk.Flip(sitk_ct_slice, flipAxes=(False, True)), img_path_CT)

        return img_path, img_path_CT


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

    print((sys.argv))

    slicelet = ParenchymaAnalysisSlicelet()
