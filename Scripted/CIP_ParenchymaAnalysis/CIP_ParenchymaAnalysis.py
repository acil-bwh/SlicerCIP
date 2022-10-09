import logging, os
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

        if not parent:
            self.parent = slicer.qMRMLWidget()
            self.parent.setLayout(qt.QVBoxLayout())
            self.parent.setMRMLScene(slicer.mrmlScene)
        else:
            self.parent = parent
        self.logic = None
        self.CTNode = None
        self.lungMaskNode = None  # segmentation node or labelmap volume node of the lung
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
        if self.labelSelector.currentNode() and self.labelSelector.currentNode().GetClassName() == "vtkMRMLLabelMapVolumeNode":
            slicer.util.setSliceViewerLayers(label=self.labelSelector.currentNode(), labelOpacity=0.5)

    def exit(self):
        if self.labelSelector.currentNode() and self.labelSelector.currentNode().GetClassName() == "vtkMRMLLabelMapVolumeNode":
            slicer.util.setSliceViewerLayers(label=None)

    def setup(self):
        ScriptedLoadableModuleWidget.setup(self)

        #
        # The input volume selector
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
        # The input sgmentation / labelmap  volume selector
        #
        self.labelSelector = slicer.qMRMLNodeComboBox()
        self.labelSelector.nodeTypes = ["vtkMRMLLabelMapVolumeNode", "vtkMRMLSegmentationNode"]
        self.labelSelector.selectNodeUponCreation = True
        self.labelSelector.addEnabled = False
        self.labelSelector.removeEnabled = False
        self.labelSelector.noneEnabled = True
        self.labelSelector.showHidden = False
        self.labelSelector.showChildNodeTypes = False
        self.labelSelector.setMRMLScene(slicer.mrmlScene)
        self.labelSelector.setToolTip("Pick the lung segmentation or labelmap volume.")
        parametersFormLayout.addRow("Lung mask: ", self.labelSelector)
        #
        # Image filtering section
        #
        self.preProcessingWidget = PreProcessingWidget(self.moduleName, parentWidget=self.parent)
        self.preProcessingWidget.setup()
        #
        # self.splitRadioButton = qt.QRadioButton()
        # self.splitRadioButton.setText('Split Label Map')
        # self.splitRadioButton.setChecked(0)
        # self.parent.layout().addWidget(self.splitRadioButton, 0, 3)
        #
        # Apply button
        #
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
        self.HistogramFreqOption.setChecked(True)
        self.HistogramFreqOption.setToolTip('If checked, histogram multiplied by region volume will be displayed.')
        self.HistogramFreqOption.hide()

        self.histogramCheckBoxes = []
        self.histFrame1 = qt.QFrame()
        self.histFrame1.setLayout(qt.QHBoxLayout())
        self.histFrame2 = qt.QFrame()
        self.histFrame2.setLayout(qt.QHBoxLayout())

        self.GlobalHistCheckBox = qt.QCheckBox()
        self.histogramCheckBoxes.append(self.GlobalHistCheckBox)
        self.histFrame1.layout().addWidget(self.GlobalHistCheckBox)

        self.RightHistCheckBox = qt.QCheckBox()
        self.histogramCheckBoxes.append(self.RightHistCheckBox)
        self.histFrame1.layout().addWidget(self.RightHistCheckBox)

        self.LeftHistCheckBox = qt.QCheckBox()
        self.histogramCheckBoxes.append(self.LeftHistCheckBox)
        self.histFrame1.layout().addWidget(self.LeftHistCheckBox)

        self.RULHistCheckBox = qt.QCheckBox()
        self.histogramCheckBoxes.append(self.RULHistCheckBox)
        self.histFrame1.layout().addWidget(self.RULHistCheckBox)

        self.RLLHistCheckBox = qt.QCheckBox()
        self.histogramCheckBoxes.append(self.RLLHistCheckBox)
        self.histFrame1.layout().addWidget(self.RLLHistCheckBox)

        self.RMLHistCheckBox = qt.QCheckBox()
        self.histogramCheckBoxes.append(self.RMLHistCheckBox)
        self.histFrame1.layout().addWidget(self.RMLHistCheckBox)

        self.LULHistCheckBox = qt.QCheckBox()
        self.histogramCheckBoxes.append(self.LULHistCheckBox)
        self.histFrame1.layout().addWidget(self.LULHistCheckBox)

        self.LLLHistCheckBox = qt.QCheckBox()
        self.histogramCheckBoxes.append(self.LLLHistCheckBox)
        self.histFrame2.layout().addWidget(self.LLLHistCheckBox)

        self.LUTHistCheckBox = qt.QCheckBox()
        self.histogramCheckBoxes.append(self.LUTHistCheckBox)
        self.histFrame2.layout().addWidget(self.LUTHistCheckBox)

        self.LMTHistCheckBox = qt.QCheckBox()
        self.histogramCheckBoxes.append(self.LMTHistCheckBox)
        self.histFrame2.layout().addWidget(self.LMTHistCheckBox)

        self.LLTHistCheckBox = qt.QCheckBox()
        self.histogramCheckBoxes.append(self.LLTHistCheckBox)
        self.histFrame2.layout().addWidget(self.LLTHistCheckBox)

        self.RUTHistCheckBox = qt.QCheckBox()
        self.histogramCheckBoxes.append(self.RUTHistCheckBox)
        self.histFrame2.layout().addWidget(self.RUTHistCheckBox)

        self.RMTHistCheckBox = qt.QCheckBox()
        self.histogramCheckBoxes.append(self.RMTHistCheckBox)
        self.histFrame2.layout().addWidget(self.RMTHistCheckBox)

        self.RLTHistCheckBox = qt.QCheckBox()
        self.histogramCheckBoxes.append(self.RLTHistCheckBox)
        self.histFrame2.layout().addWidget(self.RLTHistCheckBox)

        for i in range(len(self.histogramCheckBoxes)):
            self.histogramCheckBoxes[i].setText(CIP_ParenchymaAnalysisLogic.allUniqueRegionTags[i])
            self.histogramCheckBoxes[i].hide()

        self.HistSection.layout().addWidget(self.HistogramFreqOption)
        self.HistSection.layout().addWidget(self.histFrame1)
        self.HistSection.layout().addWidget(self.histFrame2)
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
        slicer.util.setSliceViewerLayers(background=self.CTNode, fit=True)
        self.updateButtonStates()

    def onLabelSelect(self, node):

        self.lungMaskNode = node
        if (not node) or (node.GetClassName() == "vtkMRMLLabelMapVolumeNode"):
            slicer.util.setSliceViewerLayers(label=self.lungMaskNode, labelOpacity=0.5)

        self.preProcessingWidget.filterApplication.setChecked(self.lungMaskNode is not None)
        self.updateButtonStates()

    def updateButtonStates(self):
        self.applyButton.enabled = bool(self.CTNode)  # and bool(self.lungMaskNode)
        self.preProcessingWidget.enableFilteringFrame(bool(self.CTNode))
        self.preProcessingWidget.enableLMFrame(self.lungMaskNode is None)
        self.preProcessingWidget.filterApplication.setEnabled(self.lungMaskNode is None)

    def inputVolumesAreValid(self):
        """Verify that volumes are compatible with label calculation
        algorithm assumptions"""

        # Check input CT
        if not self.CTNode:
            qt.QMessageBox.warning(slicer.util.mainWindow(),
                                   "Parenchyma Analysis", "Please select a CT Input Volume.")
            return False
        if not self.CTNode.GetImageData():
            qt.QMessageBox.warning(slicer.util.mainWindow(),
                                   "Parenchyma Analysis", "Please select a CT Input Volume.")
            return False

        # Check input lung mask

        if self.lungMaskNode and self.lungMaskNode.GetClassName() == "vtkMRMLSegmentationNode":
            # Lung mask is a segmentation node
            segmentation = self.lungMaskNode.GetSegmentation()
            validSegmentation = (segmentation.GetSegmentIdBySegmentName('right lung')
                and segmentation.GetSegmentIdBySegmentName('left lung')
                and segmentation.GetSegmentIdBySegmentName('other'))
            if not validSegmentation:
                qt.QMessageBox.warning(slicer.util.mainWindow(), "Parenchyma Analysis",
                    "Input segmentation not valid. It must contain segments: right lung, left lung, other.")
                return False

        else:
            # Lung mask is a labelmap node (or not set)
            if not self.lungMaskNode or not self.lungMaskNode.GetImageData():
                warning = self.preProcessingWidget.warningMessageForLM()
                if warning == 16384:
                    self.createLungLabelMap()
                else:
                    qt.QMessageBox.warning(slicer.util.mainWindow(), "Parenchyma Analysis", "Please select a Lung Label Map.")
                    return False
                return True
            if self.CTNode.GetImageData().GetDimensions() != self.lungMaskNode.GetImageData().GetDimensions():
                qt.QMessageBox.warning(slicer.util.mainWindow(), "Parenchyma Analysis", "Input Volumes do not have the same geometry.")
                return False

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

        self.lungMaskNode = slicer.mrmlScene.AddNode(slicer.vtkMRMLLabelMapVolumeNode())
        name = inputNode.GetName() + '_partialLungLabelMap'
        self.lungMaskNode.SetName(slicer.mrmlScene.GenerateUniqueName(name))

        self.preProcessingWidget.createPartialLM(inputNode, self.lungMaskNode)

        label_image = self.lungMaskNode.GetImageData()
        shape = list(label_image.GetDimensions())
        input_array = vtk.util.numpy_support.vtk_to_numpy(label_image.GetPointData().GetScalars())
        original_shape = input_array.shape
        input_array = input_array.reshape(shape[2], shape[1], shape[0])  # input_array.transpose([2, 1, 0]) would not work!

        input_image = sitk.GetImageFromArray(input_array)
        input_image.SetSpacing(self.lungMaskNode.GetSpacing())
        input_image.SetOrigin(self.lungMaskNode.GetOrigin())

        my_lung_splitter = lung_splitter(split_thirds=True)
        split_lm = my_lung_splitter.execute(input_image)

        split = sitk.GetArrayFromImage(split_lm)

        input_aa = vtk.util.numpy_support.vtk_to_numpy(label_image.GetPointData().GetScalars())

        input_aa[:] = split.reshape(original_shape)

        self.lungMaskNode.StorableModified()
        self.lungMaskNode.Modified()
        self.lungMaskNode.InvokeEvent(slicer.vtkMRMLVolumeNode.ImageDataModifiedEvent, self.lungMaskNode)

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

        self.logic = CIP_ParenchymaAnalysisLogic(self.CTNode, self.lungMaskNode, self.HistogramFreqOption.checked)
        self.populateStats()
        self.logic.computeEmphysemaOnSlice(self.CTNode, self.logic.labelNode)
        self.logic.createHistogram(self.logic.labelNode)
        for i in range(len(self.histogramCheckBoxes)):
            self.histogramCheckBoxes[i].setChecked(False)
            self.histogramCheckBoxes[i].hide()

        self.HistogramFreqOption.show()
        for regionTag in CIP_ParenchymaAnalysisLogic.allUniqueRegionTags:
            if regionTag in self.logic.regionTags:
                self.histogramCheckBoxes[CIP_ParenchymaAnalysisLogic.allUniqueRegionTags.index(regionTag)].show()
                self.histogramCheckBoxes[CIP_ParenchymaAnalysisLogic.allUniqueRegionTags.index(regionTag)].setChecked(True)

        self.HistSection.enabled = True
        self.chartBox.enabled = True
        self.applyButton.enabled = True
        self.applyButton.text = "Apply"

        slicer.util.setSliceViewerLayers(background=self.CTNode)

        if self.lungMaskNode and self.lungMaskNode.GetClassName() != "vtkMRMLSegmentationNode":
            self.logic.deleteLabelNode()
            self.lungMaskNode = None
        else:
            self.labelSelector.setCurrentNode(self.logic.labelNode)

    def changeHistDisplay(self):
        histList = []
        for i in range(len(self.histogramCheckBoxes)):
            if self.histogramCheckBoxes[i].checked:
                histList.append(CIP_ParenchymaAnalysisLogic.allUniqueRegionTags[i])
        self.logic.ChangeHistogramFrequency(histList, byRegionVolume=self.HistogramFreqOption.checked)

    def onHistogram(self):
        """Histogram of the selected region
        """
        histList = []
        for i in range(len(self.histogramCheckBoxes)):
            if self.histogramCheckBoxes[i].checked:
                histList.append(CIP_ParenchymaAnalysisLogic.allUniqueRegionTags[i])

        self.logic.AddSelectedHistograms(histList)

    def onChart(self):
        """chart the parenchyma analysis
        """
        valueToPlot = self.chartOptions[self.chartOption.currentIndex]
        self.logic.createStatsChart(valueToPlot)

    def onSaveReport(self):
        """ Save the current values in a persistent csv file
        """
        self.logic.statsAsCSV(self.reportsWidget, self.CTNode)

    def onPrintReport(self):
        """
        Print a pdf report
        """
        emphysema_image_path, ct_slice_path = self.logic.writeEmphysemaOnSliceToFiles(op=0.5)
        pdfReporter = PdfReporter()
        # Get the values that are going to be inserted in the html template
        caseName = self.CTNode.GetName()

        values = dict()
        values["@@PATH_TO_STATIC@@"] = os.path.join(os.path.dirname(os.path.realpath(__file__)), "Resources/")
        values["@@SUBJECT@@"] = "Subject: " + str(caseName)
        values["@@GLOBAL_LEVEL@@"] = "{:.2f}%".format(self.logic.labelStats['LAA%-950','WholeLung'])
        values["@@SUMMARY@@"] = "Emphysema per region: "

        pdfRows = """"""
        for regionTag in self.logic.regionTags:
            pdfRows += """<tr>
              <td align="center">{} </td>
              <td align="center">{:.2f} </td>
            </tr>""".format(regionTag, self.logic.labelStats['LAA%-950', regionTag])

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
        logging.info(f"PDF report generated: {reportPath}")
        Util.openFile(reportPath)

    def onFileSelected(self, fileName):
        self.logic.saveStats(fileName)

    def populateStats(self):
        if not self.logic:
            return
        self.items = []
        self.model = qt.QStandardItemModel()
        self.view.setModel(self.model)
        self.view.verticalHeader().visible = False
        row = 0

        for regionTag in self.logic.regionTags:
            rgb = self.logic.regionColors[regionTag]
            regionValue = self.logic.regionValues[regionTag]
            color = qt.QColor.fromRgbF(*rgb)
            item = qt.QStandardItem()
            item.setData(color, 1)
            item.setText(str(regionTag))
            item.setData(regionTag, 1)
            item.setToolTip(regionTag)
            item.setTextAlignment(1)
            self.model.setItem(row, 0, item)
            self.items.append(item)
            col = 1
            for statsColumnKey in CIP_ParenchymaAnalysisLogic.statsColumnKeys:
                item = qt.QStandardItem()
                item.setText("%.3f" % self.logic.labelStats[statsColumnKey, regionTag])
                item.setTextAlignment(4)
                self.view.setColumnWidth(col, 15 * len(item.text()))
                self.model.setItem(row, col, item)
                self.items.append(item)
                col += 1
            row += 1

        self.view.setColumnWidth(0, 15 * len('Region'))
        self.model.setHeaderData(0, 1, "Region")
        col = 1
        for statsColumnKey in CIP_ParenchymaAnalysisLogic.statsColumnKeys:
            # self.view.setColumnWidth(col,15*len(statsColumnKey))
            self.model.setHeaderData(col, 1, statsColumnKey)
            col += 1

class CIP_ParenchymaAnalysisLogic(ScriptedLoadableModuleLogic):
    """Implement the logic to perform a parenchyma analysis
    Nodes are passed in as arguments.
    Results are stored as 'statistics' instance variable.
    """
    __preventDialogs__ = False

    statsColumnKeys = ["LAA%-950", "LAA%-925", "LAA%-910", "LAA%-856", "HAA%-700", "HAA%-600", "HAA%-500", "HAA%-250",
                     "HAA%-600-250", "Perc10", "Perc15", "Mean", "Std", "Kurtosis", "Skewness",
                     "Ventilation Heterogeneity", "Mass", "Volume"]

    # From ChestConventions.xml:
    #   WHOLELUNG: 1
    #   RIGHTLUNG: 2
    #   LEFTLUNG: 3
    #   RIGHTSUPERIORLOBE: 4
    #   RIGHTMIDDLELOBE: 5
    #   RIGHTINFERIORLOBE: 6
    #   LEFTSUPERIORLOBE: 7
    #   LEFTINFERIORLOBE: 8
    #   LEFTUPPERTHIRD: 9
    #   LEFTMIDDLETHIRD: 10
    #   LEFTLOWERTHIRD: 11
    #   RIGHTUPPERTHIRD: 12
    #   RIGHTMIDDLETHIRD: 13
    #   RIGHTLOWERTHIRD: 14

    allRegionTags = ["WholeLung", "RightLung", "RightLung", "RightLung", "LeftLung", "LeftLung", "RUL", "RML",
                 "RLL", "LUL", "LLL", "LUT", "LMT", "LLT", "RUT", "RMT", "RLT"]

    allUniqueRegionTags = ["WholeLung", "RightLung", "LeftLung", "RUL", "RML",
                 "RLL", "LUL", "LLL", "LUT", "LMT", "LLT", "RUT", "RMT", "RLT"]

    allRegionValues = [
        (1, 14),  # all lung labels
        (2, 2),   # right lung in one segment
        (4, 6),   # right lung as 3 lobes
        (12, 14), # right lung as 3 thirds
        (3, 3),   # left lung as one segment
        (7, 11),  # left lung as 2 lobes and 3 thirds
        # Right lobes
        (4, 4),   # RUL (RSL)
        (5, 5),   # RML
        (6, 6),   # RLL (RIL)
        # Left lobes
        (7, 7),   # LUL (LSL)
        (8, 8),   # LLL (LIL)
        # Right thirds
        (9, 9),   # LUT
        (10, 10), # LMT
        (11, 11), # LLT
        # Left thirds
        (12, 12), # RUT
        (13, 13), # RMT
        (14, 14)  # RLT
        ]

    def __init__(self, CTNode, lungMaskNode, freq_by_region_volume=True):

        self.regionTags = [] # Found regions
        self.regionColors = {} # map regionTag to RGB color
        self.regionValues = {}  # map regionTag to label value range
        cubicMMPerVoxel = reduce(lambda x, y: x * y, CTNode.GetSpacing())
        litersPerCubicMM = 0.000001

        # Center slices, can be used for creating images for reporting
        self.sitk_ct_slice = None
        self.sitk_emph_slice = None
        self.colorTableNode = None

        if lungMaskNode and lungMaskNode.GetClassName() == "vtkMRMLSegmentationNode":
            # Got a segmentation node, create a label node from it
            self.labelNode, self.colorTableNode = self.convertSegmentsToCipLabelmapNode(CTNode, lungMaskNode)
        else:
            # Got a label node, use it as is
            self.labelNode = lungMaskNode

        if not self.labelNode:
            raise ValueError("Invalid lungMaskNode")

        displayNode = self.labelNode.GetDisplayNode()
        colorNode = displayNode.GetColorNode()
        lut = colorNode.GetLookupTable()

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
        parameters['ipl'] = self.labelNode.GetID()
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

        datalabel_arr = vtk.util.numpy_support.vtk_to_numpy(self.labelNode.GetImageData().GetPointData().GetScalars())
        data_arr = vtk.util.numpy_support.vtk_to_numpy(CTNode.GetImageData().GetPointData().GetScalars())

        for value, regionTag in zip(CIP_ParenchymaAnalysisLogic.allRegionValues, CIP_ParenchymaAnalysisLogic.allRegionTags):
            data = data_arr[(datalabel_arr >= value[0]) & (datalabel_arr <= value[1])]

            if data.any():
                mean_data = numpy.mean(data)
                std_data = numpy.std(data)
                self.labelStats['LAA%-950', regionTag] = 100.0 * (data < -950).sum() / float(data.size)
                self.labelStats['LAA%-925', regionTag] = 100.0 * (data < -925).sum() / float(data.size)
                self.labelStats['LAA%-910', regionTag] = 100.0 * (data < -910).sum() / float(data.size)
                self.labelStats['LAA%-856', regionTag] = 100.0 * (data < -856).sum() / float(data.size)
                self.labelStats['HAA%-700', regionTag] = 100.0 * (data > -700).sum() / float(data.size)
                self.labelStats['HAA%-600', regionTag] = 100.0 * (data > -600).sum() / float(data.size)
                self.labelStats['HAA%-500', regionTag] = 100.0 * (data > -500).sum() / float(data.size)
                self.labelStats['HAA%-250', regionTag] = 100.0 * (data > -250).sum() / float(data.size)
                self.labelStats['HAA%-600-250', regionTag] = 100.0 * (numpy.logical_and(data > -600,
                                                                                  data < -250)).sum() / float(data.size)
                # self.labelStats[cycle,'Perc10',regionTag]=self.percentile(data,.1)
                # self.labelStats[cycle,'Perc15',regionTag]=self.percentile(data,.15)
                self.labelStats['Perc10',regionTag]=numpy.percentile(data,10)
                self.labelStats['Perc15',regionTag]=numpy.percentile(data,15)
                self.labelStats['Mean', regionTag] = mean_data
                self.labelStats['Std', regionTag] = std_data
                self.labelStats['Kurtosis', regionTag] = self.kurt(data, mean_data, std_data)
                self.labelStats['Skewness', regionTag] = self.skew(data, mean_data, std_data)
                self.labelStats['Ventilation Heterogeneity', regionTag] =  self.vh(data)
                self.labelStats['Mass',regionTag] = self.mass(data,cubicMMPerVoxel)
                self.labelStats['Volume', regionTag] = data.size * cubicMMPerVoxel * litersPerCubicMM

                # Compute histograms
                data = data[data < -350]
                binContainers = numpy.arange(data.min(), data.max() + 2)
                histogram, bins = numpy.histogram(data, bins=binContainers, density=True)
                self.regionHists_by_region_volume[
                    regionTag] = histogram * data.size * cubicMMPerVoxel * litersPerCubicMM * 1000
                self.regionHists[regionTag] = histogram

                self.regionBins[regionTag] = bins

                self.regionTags.append(regionTag)

                rgb = lut.GetTableValue(value[0])
                self.regionColors[regionTag] = [rgb[0], rgb[1], rgb[2]]

                self.regionValues[regionTag] = value

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

        for regionTag in self.regionTags:
            e = {}
            e['Volume Name'] = CTNode.GetName()
            e['Region'] = regionTag
            for statsColumnKey in CIP_ParenchymaAnalysisLogic.statsColumnKeys:
                e[statsColumnKey] = self.labelStats[statsColumnKey, regionTag]

            repWidget.insertRow(**e)

        if not self.__preventDialogs__:
            qt.QMessageBox.information(slicer.util.mainWindow(), 'Data saved', 'The data were saved successfully')

    def createStatsChart(self, valueToPlot):
        """Make a MRML chart of the current stats
        """
        # self.setChartLayout()
        #chartViewNode = SlicerUtil.getNode('ChartView')

        tableNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTableNode", valueToPlot +" data")
        col1=tableNode.AddColumn()
        col1.SetName("Label")
        col2=tableNode.AddColumn()
        col2.SetName("Value")
        
        tableNode.SetColumnType("Label",vtk.VTK_STRING)
        tableNode.SetColumnType("Value",vtk.VTK_FLOAT)
                      
        for i, regionTag in enumerate(self.regionTags):
            tableNode.AddEmptyRow()
            tableNode.SetCellText(i,0,regionTag)
            tableNode.SetCellText(i,1,str(self.labelStats[valueToPlot, regionTag]))

        barPlotSeries = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLPlotSeriesNode", valueToPlot + " bar plot")
        barPlotSeries.SetAndObserveTableNodeID(tableNode.GetID())
        barPlotSeries.SetPlotType(slicer.vtkMRMLPlotSeriesNode.PlotTypeBar)
        barPlotSeries.SetLabelColumnName("Label") #displayed when hovering mouse
        barPlotSeries.SetYColumnName("Value") # for bar plots, index is the x-value
        barPlotSeries.SetColor(0, 0.6, 1.0)
        
        chartNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLPlotChartNode", valueToPlot + " chart")
        chartNode.SetTitle("Parenchyma Statistics")
        chartNode.SetLegendVisibility(False)
        chartNode.SetYAxisTitle(valueToPlot)
        chartNode.SetXAxisTitle("Label")
        chartNode.AddAndObservePlotSeriesNodeID(barPlotSeries.GetID())
    
        # Show plot in layout
        slicer.modules.plots.logic().ShowChartInLayout(chartNode)

        # Create plot
        #plotSeriesNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLChartNode", "Bar chart")
        #plotSeriesNode.SetAndObserveTableNodeID(tableNode.GetID())
        #plotSeriesNode.SetXColumnName("Regions")
        #plotSeriesNode.SetYColumnName("Values")
        #plotSeriesNode.SetPlotType(plotSeriesNode.PlotTypeBar)
        #plotSeriesNode.SetColor(0, 0.6, 1.0)

        # Create chart and add plot
        #plotChartNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLPlotChartNode")
        #plotChartNode.AddAndObservePlotSeriesNodeID(plotSeriesNode.GetID())
        #plotChartNode.YAxisRangeAutoOff()
        #plotChartNode.SetYAxisRange(0, 500000)

        # Show plot in layout
        #slicer.modules.plots.logic().ShowChartInLayout(plotChartNode)

        #chartNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLPlotChartNode", 'PlotChartNode') 
        #chartNode.AddArray(valueToPlot, arrayNode.GetID())

        #chartViewNode.SetChartNodeID(chartNode.GetID())

        #chartNode.SetProperty('default', 'title', 'Parenchyma Statistics')
        #chartNode.SetProperty('default', 'xAxisLabel', 'Label')
        #chartNode.SetProperty('default', 'yAxisLabel', valueToPlot)
        #chartNode.SetProperty('default', 'type', 'Bar')
        #chartNode.SetProperty('default', 'xAxisType', 'categorical')
        #chartNode.SetProperty('default', 'showLegend', 'off')

        # series level properties
        #colorTableNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLColorTableNode", "StatsChartColors")
        #colorTableNode.SetTypeToUser()
        #colorTableNode.HideFromEditorsOff()
        #colorTableNode.SetNumberOfColors(len(self.regionTags))
        #for colorIndex, regionTag in enumerate(self.regionTags):
        #    color = self.regionColors[regionTag]
        #    colorTableNode.SetColor(colorIndex, regionTag, color[0], color[1], color[2], 1.0)
        #colorTableNode.NamesInitialisedOn()

        #chartNode.SetProperty(valueToPlot, 'lookupTable', colorTableNode.GetID())

    def convertSegmentsToCipLabelmapNode(self, CTNode, segmentationNode):
        colorTableNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLColorTableNode", "__temp__chest_region_colors_basic")
        colorTableNode.SetTypeToUser()
        colorTableNode.HideFromEditorsOff()
        colorTableNode.SetNumberOfColors(69)
        colorTableNode.SetColor( 0, "background", 0.0, 0.0, 0.0, 0.0)
        colorTableNode.SetColor( 1, "whole lung", 0.42, 0.38, 0.75, 1.0)
        colorTableNode.SetColor( 2, "right lung", 0.26, 0.64, 0.10, 1.0)
        colorTableNode.SetColor( 3, "left lung",  0.80, 0.11, 0.36, 1.0)
        colorTableNode.SetColor(58, "trachea",    0.49, 0.49, 0.79, 1.0)
        colorTableNode.NamesInitialisedOn()
        labelmapNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLLabelMapVolumeNode", "__temp__" + segmentationNode.GetName() + "_LabelMap")
        segmentIdList = ["right lung", "left lung", "other"]
        # Segment ids must be converted into a vtkStringArray to be used in ExportSegmentsToLabelmapNode
        segmentIds = vtk.vtkStringArray()
        for segmentId in segmentIdList:
          segmentIds.InsertNextValue(segmentId)
        slicer.modules.segmentations.logic().ExportSegmentsToLabelmapNode(segmentationNode, segmentIds, labelmapNode, \
            CTNode, slicer.vtkSegmentation.EXTENT_REFERENCE_GEOMETRY, colorTableNode)
        return labelmapNode, colorTableNode

    def deleteLabelNode(self):
        # cleanup
        if self.labelNode:
            slicer.mrmlScene.RemoveNode(self.labelNode)
        if self.colorTableNode: 
            slicer.mrmlScene.RemoveNode(self.colorTableNode)

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

        for regionTag in self.regionTags:
            if self.freq_by_region_volume:
                histogram = self.regionHists_by_region_volume[regionTag]
            else:
                histogram = self.regionHists[regionTag]

            bins = self.regionBins[regionTag]

            tableNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTableNode", 'TableNode_{}'.format(regionTag))
            table = tableNode.GetTable()

            arrX = vtk.vtkFloatArray()
            arrX.SetName("bins".format(regionTag))
            table.AddColumn(arrX)

            arrY = vtk.vtkFloatArray()
            arrY.SetName("freq_{}".format(regionTag))
            table.AddColumn(arrY)

            dataSamples = histogram.size
            table.SetNumberOfRows(dataSamples)

            for i in range(dataSamples):
                table.SetValue(i, 0, float(bins[i]))
                table.SetValue(i, 1, histogram[i])

            plotSeriesNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLPlotSeriesNode", regionTag)
            plotSeriesNode.SetAndObserveTableNodeID(tableNode.GetID())
            plotSeriesNode.SetXColumnName("bins".format(regionTag))
            plotSeriesNode.SetYColumnName("freq_{}".format(regionTag))
            plotSeriesNode.SetPlotType(slicer.vtkMRMLPlotSeriesNode.PlotTypeScatter)
            plotSeriesNode.SetLineStyle(slicer.vtkMRMLPlotSeriesNode.LineStyleSolid)
            plotSeriesNode.SetLineWidth(2.)
            plotSeriesNode.SetMarkerStyle(slicer.vtkMRMLPlotSeriesNode.MarkerStyleNone)
            # plotSeriesNode.SetUniqueColor('vtkMRMLColorTableNodeFileGenericAnatomyColors.txt')
            rgb = self.regionColors[regionTag]
            plotSeriesNode.SetColor(*rgb)
            plotChartNode.AddAndObservePlotSeriesNodeID(plotSeriesNode.GetID())

        histogramViewNode.SetPlotChartNodeID(plotChartNode.GetID())

    def ChangeHistogramFrequency(self, histogramsList, byRegionVolume=True):
        plotChartNode = SlicerUtil.getNode('PlotChartNode')
        plotChartNode.RemoveAllPlotSeriesNodeIDs()
        for regionTag in self.regionTags:
            if byRegionVolume:
                plotChartNode.SetYAxisRange(0, 50)
                histogram = self.regionHists_by_region_volume[regionTag]
            else:
                plotChartNode.SetYAxisRange(0, 0.01)
                histogram = self.regionHists[regionTag]

            bins = self.regionBins[regionTag]

            tableNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTableNode", 'TableNode_{}'.format(regionTag))
            table = tableNode.GetTable()

            arrX = vtk.vtkFloatArray()
            arrX.SetName("bins".format(regionTag))
            table.AddColumn(arrX)

            arrY = vtk.vtkFloatArray()
            arrY.SetName("freq_{}".format(regionTag))
            table.AddColumn(arrY)

            dataSamples = histogram.size
            table.SetNumberOfRows(dataSamples)

            for i in range(dataSamples):
                table.SetValue(i, 0, float(bins[i]))
                table.SetValue(i, 1, histogram[i])

            plotSeriesNode = SlicerUtil.getNode(regionTag)
            plotSeriesNode.SetAndObserveTableNodeID(tableNode.GetID())
            plotSeriesNode.SetXColumnName("bins".format(regionTag))
            plotSeriesNode.SetYColumnName("freq_{}".format(regionTag))

        self.AddSelectedHistograms(histogramsList)

    def AddSelectedHistograms(self, histogramsList):
        histogramViewNode = SlicerUtil.getNode('HistogramView')
        plotChartNode = SlicerUtil.getNode('PlotChartNode')
        plotChartNode.RemoveAllPlotSeriesNodeIDs()

        for regionTag in histogramsList:
            plotSeriesNode = SlicerUtil.getNode(regionTag)
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

    def computeEmphysemaOnSlice(self, CTNode, labelNode):
        """Get a center slice of the CT and the emphysema label and save into
        self.sitk_ct_slice and self.sitk_emph_slice.
        """

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

        emph_slice[slice_label==0] = 0

        sitk_ct_slice = sitk.GetImageFromArray(ct_slice.transpose())
        self.sitk_ct_slice = sitk.Cast(sitk.IntensityWindowing(sitk_ct_slice, windowMinimum=-1200, windowMaximum=200,
                                                          outputMinimum=0, outputMaximum=255), sitk.sitkUInt8)

        self.sitk_emph_slice = sitk.GetImageFromArray(emph_slice.transpose())

    def writeEmphysemaOnSliceToFiles(self, op=0.2):

        label_overlay = sitk.LabelOverlay(self.sitk_ct_slice, self.sitk_emph_slice, opacity=op, colormap=[255, 51, 51])
        # label_overlay = sitk.LabelOverlay(sitk_ct_slice, sitk_emph_slice, opacity=op)

        label_ovelay_img = sitk.Flip(label_overlay, flipAxes=(False, True))
        ct_img = sitk.Flip(self.sitk_ct_slice, flipAxes=(False, True))

        import tempfile
        tmpFolder = tempfile.mkdtemp()
        img_path = os.path.join(tmpFolder, "tmpImg__.png")
        img_path_CT = os.path.join(tmpFolder, "tmpImgCT__.png")

        sitk.WriteImage(label_ovelay_img, img_path)
        sitk.WriteImage(ct_img, img_path_CT)

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
