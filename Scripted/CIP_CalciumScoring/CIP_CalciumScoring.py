from slicer.ScriptedLoadableModule import *
from CIP.logic.SlicerUtil import SlicerUtil
import vtk, qt, ctk, slicer
import SimpleITK as sitk
import sitkUtils
import numpy as np
np.set_printoptions(threshold=np.nan)

from CIP.ui import CaseReportsWidget
from collections import OrderedDict
import json


class CIP_CalciumScoring(ScriptedLoadableModule):
    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent = parent
        self.parent.title = "Calcium Scoring"
        self.parent.contributors = ["Alex Yarmarkovich and Raul San Jose", "Applied Chest Imaging Laboratory",
                                    "Brigham and Women's Hospital", "Carlos Cano Espinosa and German Gonzalez Serrano", "Sierra Research S.L."]
        self.parent.categories = SlicerUtil.CIP_ModulesCategory
        self.parent.dependencies = [SlicerUtil.CIP_ModuleName]
        self.parent.helpText = "Compute the Agatston score to measure the level of calcification in the coronary artery"
        self.parent.acknowledgementText = SlicerUtil.ACIL_AcknowledgementText


class CIP_CalciumScoringWidget(ScriptedLoadableModuleWidget):
    def __init__(self, parent=None):
        print "init"
        ScriptedLoadableModuleWidget.__init__(self, parent)

        # Default variables
        # -----------------
        self.calcificationType = 0
        self.ThresholdMin = 130.0
        self.ThresholdMax = 1000.0
        self.MinimumLesionSize = 1
        self.MaximumLesionSize = 500

        self.selectedLabelList = []
        self.selectedLabels = {}
        self.modelNodes = []
        self.selectedRGB = [1, 0, 0]

        self.summary_reports = ["Agatston Score 2D", "Agatston Score 3D", "Mass Score", "Volume"]

        self.labelScores = dict()
        self.totalScores = dict()
        for sr in self.summary_reports:
            self.labelScores[sr] = []
            self.totalScores[sr] = 0

        self.columnsDict = OrderedDict()
        self.columnsDict["CaseID"] = "CaseID"
        for sr in self.summary_reports:
            self.columnsDict[sr.replace(" ", "")] = sr


    def setup(self):
        print "setup()"
        self.setInteractor()
        # Instantiate and connect widgets
        # -------------------------------
        ScriptedLoadableModuleWidget.setup(self)

        # Parameters Area
        # ---------------
        parametersCollapsibleButton = ctk.ctkCollapsibleButton()
        parametersCollapsibleButton.text = "Parameters"
        self.layout.addWidget(parametersCollapsibleButton)
        parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)

        # Target volume selector
        # ----------------------
        self.inputSelector = slicer.qMRMLNodeComboBox()
        self.inputSelector.nodeTypes = (("vtkMRMLScalarVolumeNode"), "")
        self.inputSelector.addEnabled = False
        self.inputSelector.removeEnabled = False
        self.inputSelector.noneEnabled = False
        self.inputSelector.showHidden = False
        self.inputSelector.showChildNodeTypes = False
        self.inputSelector.setMRMLScene(slicer.mrmlScene)
        self.inputSelector.setToolTip("Pick the input to the algorithm.")
        parametersFormLayout.addRow("Target Volume: ", self.inputSelector)
        self.inputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onVolumeChanged)
        self.volumeNode = self.inputSelector.currentNode()

        # Thresholds selectors
        # --------------------
        self.ThresholdRange = ctk.ctkRangeWidget()
        self.ThresholdRange.minimum = 0
        self.ThresholdRange.maximum = 2000
        self.ThresholdRange.setMinimumValue(self.ThresholdMin)
        self.ThresholdRange.setMaximumValue(self.ThresholdMax)
        self.ThresholdRange.connect("minimumValueChanged(double)", self.onThresholdMinChanged)
        self.ThresholdRange.connect("maximumValueChanged(double)", self.onThresholdMaxChanged)
        parametersFormLayout.addRow("Threshold Value", self.ThresholdRange)
        self.ThresholdRange.setMinimumValue(self.ThresholdMin)
        self.ThresholdRange.setMaximumValue(self.ThresholdMax)

        self.LesionSizeRange = ctk.ctkRangeWidget()
        self.LesionSizeRange.minimum = 0.5
        self.LesionSizeRange.maximum = 2000  # 1000
        self.LesionSizeRange.setMinimumValue(self.MinimumLesionSize)
        self.LesionSizeRange.setMaximumValue(self.MaximumLesionSize)
        self.LesionSizeRange.connect("minimumValueChanged(double)", self.onMinSizeChanged)
        self.LesionSizeRange.connect("maximumValueChanged(double)", self.onMaxSizeChanged)
        parametersFormLayout.addRow("Lesion Size (mm^3)", self.LesionSizeRange)
        self.LesionSizeRange.setMinimumValue(self.MinimumLesionSize)
        self.LesionSizeRange.setMaximumValue(self.MaximumLesionSize)

        # Summary Fields
        # --------------------------
        self.scoreField = dict()
        for sr in self.summary_reports:
            self.scoreField[sr] = qt.QLineEdit()
            self.scoreField[sr].setText(0)
            parametersFormLayout.addRow("Total " + sr, self.scoreField[sr])

        # Update button
        # -------------
        self.updateButton = qt.QPushButton("Update")
        self.updateButton.toolTip = "Update calcium score computation"
        self.updateButton.enabled = True
        self.updateButton.setFixedSize(100, 50)
        self.updateButton.connect('clicked()', self.onUpdate)

        # Select table
        # ------------
        self.selectLabels = qt.QTableWidget()
        self.selectLabels.verticalHeader().hide()
        self.selectLabels.setColumnCount(6)
        self.selectLabels.itemClicked.connect(self.handleItemClicked)
        col_names = ["", "Agatston Score 2D", "Agatston Score 3D", "Mass Score", "Volume (mm^3)", "Mean HU", "Max HU"]
        self.selectLabels.setHorizontalHeaderLabels(col_names)

        parametersFormLayout.addRow(self.updateButton, self.selectLabels)

        # Save button
        # -----------
        self.reportsWidget = CaseReportsWidget(self.moduleName, self.columnsDict, parentWidget=self.parent)
        self.reportsWidget.setup()
        self.reportsWidget.showPrintButton(False)
        self.reportsWidget.addObservable(self.reportsWidget.EVENT_SAVE_BUTTON_CLICKED, self.onSaveReport)

        # ROI Area
        # --------
        self.roiCollapsibleButton = ctk.ctkCollapsibleButton()
        self.roiCollapsibleButton.text = "ROI"
        self.roiCollapsibleButton.setChecked(False)
        self.layout.addWidget(self.roiCollapsibleButton)

        # Layout within the dummy collapsible button
        roiFormLayout = qt.QFormLayout(self.roiCollapsibleButton)

        # ROI
        # ---
        self.ROIWidget = slicer.qMRMLAnnotationROIWidget()
        self.roiNode = slicer.vtkMRMLAnnotationROINode()
        slicer.mrmlScene.AddNode(self.roiNode)
        self.ROIWidget.setMRMLAnnotationROINode(self.roiNode)
        roiFormLayout.addRow("", self.ROIWidget)

        # Add vertical spacer
        self.layout.addStretch(1)

        # Add temp nodes
        self.croppedNode = slicer.vtkMRMLScalarVolumeNode()
        self.croppedNode.SetHideFromEditors(1)
        slicer.mrmlScene.AddNode(self.croppedNode)
        self.labelsNode = slicer.vtkMRMLLabelMapVolumeNode()
        slicer.mrmlScene.AddNode(self.labelsNode)

        if self.inputSelector.currentNode():
            self.onVolumeChanged(self.inputSelector.currentNode())

    def setInteractor(self):
        slice_views = ["Red", "Yellow", "Green"]
        for sv in slice_views:
            slice_view_interactor = slicer.app.layoutManager().sliceWidget(sv).sliceView().renderWindow().GetInteractor()
            slice_view_interactor.AddObserver("LeftButtonReleaseEvent", self.processEvent)
            slice_view_interactor.TAG = "three views: %s" % sv
            slice_view_interactor.Node = slicer.app.layoutManager().sliceWidget(sv).sliceLogic().GetLabelLayer().GetSliceNode()

    def processEvent(self, observee, event):
        xy = observee.GetEventPosition()

        transformationMatrix = observee.Node.GetXYToRAS()
        xyRAS = np.array(transformationMatrix.MultiplyPoint([xy[0], xy[1], 0, 1]))

        transformationMatrix = vtk.vtkMatrix4x4()
        self.labelsNode.GetRASToIJKMatrix(transformationMatrix)

        numpy_data = slicer.util.array(self.labelsNode.GetName())

        ijk_coords = transformationMatrix.MultiplyPoint(xyRAS)
        ijk_coords = np.array(np.rint(ijk_coords), dtype=np.int16)

        value = numpy_data[ijk_coords[2], ijk_coords[1], ijk_coords[0]]

        table_item = self.selectLabels.takeItem(value-1, 0)
        if table_item.checkState() == qt.Qt.Checked:
            table_item.setCheckState(qt.Qt.Unchecked)
        else:
            table_item.setCheckState(qt.Qt.Checked)

        self.selectLabels.setItem(value-1, 0, table_item)
        self.handleItemClicked(table_item)


    def computeTotalScore(self):
        for sr in self.summary_reports:
            self.totalScores[sr] = 0

        for n in range(0, len(self.selectedLabelList)):
            if self.selectedLabelList[n] == 1:
                for sr in self.summary_reports:
                    self.totalScores[sr] = self.totalScores[sr] + self.labelScores[sr][n]

        for sr in self.summary_reports:
            self.scoreField[sr].setText(self.totalScores[sr])

    def updateModels(self):
        for n in range(0, len(self.selectedLabelList)):
            model = self.modelNodes[n]
            dnode = model.GetDisplayNode()
            rgb = [1,0,0]
            if self.selectedLabelList[n] == 1:
                rgb = self.selectedRGB
            else:
                ct = slicer.mrmlScene.GetNodeByID('vtkMRMLColorTableNodeLabels')
                ct.GetLookupTable().GetColor(n+1, rgb)

            dnode.SetColor(rgb)

    def deleteModels(self):
        for m in self.modelNodes:
            m.SetAndObservePolyData(None)
            slicer.mrmlScene.RemoveNode(m.GetDisplayNode())
            slicer.mrmlScene.RemoveNode(m)
        self.modelNodes = []
        self.selectedLabels = {}

    def handleItemClicked(self, item):
        """Select a candidate from list and re-compute the total score"""
        if item.checkState() == qt.Qt.Checked:
            self.selectedLabelList[item.row()] = 1
        else:
            self.selectedLabelList[item.row()] = 0
        self.computeTotalScore()
        self.updateModels()

    def addLabel(self, row, rgb, values):
        self.selectLabels.setRowCount(row+1)

        item0 = qt.QTableWidgetItem('')
        item0.setFlags(qt.Qt.ItemIsUserCheckable | qt.Qt.ItemIsEnabled)
        item0.setCheckState(qt.Qt.Unchecked)
        self.selectLabels.setItem(row, 0, item0)

        for ii,val in enumerate(values):
          item1 = qt.QTableWidgetItem('')
          color = qt.QColor()
          color.setRgbF(rgb[0], rgb[1],rgb[2])
          item1.setData(qt.Qt.BackgroundRole, color)
          item1.setText("%.02f" % val)
          self.selectLabels.setItem(row, 1+ii, item1)

    def computeDensityScore(self, d):
        score = 0
        if d > 129 and d < 200:
            score = 1
        elif d < 300:
            score = 2
        elif d < 400:
            score = 3
        else:
            score = 4
        return score

    def agatston_computation(self, n, relabelImage, croppedImage, prod_spacing):
        croppedImage_arr = sitk.GetArrayFromImage(croppedImage)
        relabelImage_arr = sitk.GetArrayFromImage(relabelImage)
        ii = np.where(relabelImage_arr == n)
        min_coord = np.min(ii, axis=1)
        max_coord = np.max(ii, axis=1)

        max_coord += 1

        # crop_label = (np.array(relabelImage_arr[min_coord[0]:max_coord[0], min_coord[1]:max_coord[1], min_coord[2]:max_coord[2]]) == n)
        crop_label = relabelImage_arr[min_coord[0]:max_coord[0], min_coord[1]:max_coord[1], min_coord[2]:max_coord[2]] == n
        crop_img = croppedImage_arr[min_coord[0]:max_coord[0], min_coord[1]:max_coord[1], min_coord[2]:max_coord[2]]

        crop_img *= (crop_label == 1)
        agatston = 0
        volume = 0
        mass_score = 0
        for sl in crop_img:
            max_HU = np.max(sl)

            size = np.count_nonzero(sl)
            layer_volume = size * prod_spacing
            volume += layer_volume
            agatston += layer_volume * self.computeDensityScore(max_HU)
            mass_score += layer_volume * np.mean(sl)

        return agatston, volume, mass_score

    def statsAsCSV(self, repWidget, volumeNode):
        if self.totalScores is None:
            qt.QMessageBox.warning(slicer.util.mainWindow(), "Data not existing", "No statistics calculated")
            return

        row = {}
        row['CaseID'] = volumeNode.GetName()
        for sr in self.summary_reports:
            row[sr.replace(" ", "")] = self.totalScores[sr]

        print row
        storageNode = self.volumeNode.GetStorageNode()
        filepath = str(storageNode.GetFullNameFromFileName())
        split_path = filepath.split('.')
        output_path = split_path[0]
        with open("%s_cac.%s" % (output_path, "json"), 'w') as f:
            json.dump(row, f)
        # repWidget.insertRow(**row)

        # qt.QMessageBox.information(slicer.util.mainWindow(), 'Data saved', 'The data were saved successfully')

    # def saveSegmentationAsNrrd(self):
    def saveSegmentation(self):
        roiCenter = [0, 0, 0]
        self.roiNode.GetXYZ(roiCenter)

        transformationMatrix = vtk.vtkMatrix4x4()
        self.volumeNode.GetRASToIJKMatrix(transformationMatrix)

        roiCenter_ijk = transformationMatrix.MultiplyPoint([roiCenter[0], roiCenter[1], roiCenter[2], 1])

        roiCenter_ijk = np.array(np.rint(roiCenter_ijk), dtype=np.int16)

        numpy_data = np.array(slicer.util.array(self.labelsNode.GetName()))
        lbs = np.argwhere(np.array(self.selectedLabelList) == 1).flatten() + 1
        numpy_data[np.logical_not(np.isin(numpy_data, lbs))] = 0

        saved_array = np.array(slicer.util.array(self.volumeNode.GetName()))

        slicer.util.array(self.volumeNode.GetName()).fill(0)
        slicer.util.array(self.volumeNode.GetName())[roiCenter_ijk[2] - numpy_data.shape[0]/2:roiCenter_ijk[2] + (numpy_data.shape[0]+1)/2,
        roiCenter_ijk[1] - numpy_data.shape[1]/2:roiCenter_ijk[1] + (numpy_data.shape[1]+1)/2,
        roiCenter_ijk[0] - numpy_data.shape[2]/2:roiCenter_ijk[0] + (numpy_data.shape[2]+1)/2] = numpy_data

        storageNode = self.volumeNode.GetStorageNode()
        filepath = str(storageNode.GetFullNameFromFileName())
        split_path = filepath.split('.')
        output_path = split_path[0]
        extension = split_path[1]

        result = slicer.util.saveNode(self.volumeNode, "%s_cac.%s" % (output_path, extension))
        slicer.util.array(self.volumeNode.GetName())[:, :, :] = saved_array

    def onVolumeChanged(self, value):
        self.volumeNode = self.inputSelector.currentNode()
        if self.volumeNode != None:
            xyz = [0, 0, 0]
            c = [0, 0, 0]
            slicer.vtkMRMLSliceLogic.GetVolumeRASBox(self.volumeNode, xyz, c)
            xyz[:] = [x * 0.2 for x in xyz]
            self.roiNode.SetXYZ(c)
            self.roiNode.SetRadiusXYZ(xyz)
            sp = self.volumeNode.GetSpacing()
            self.voxelVolume = sp[0] * sp[1] * sp[2]
            self.sx = sp[0]
            self.sy = sp[1]
            self.sz = sp[2]

    def onMinSizeChanged(self, value):
        self.MinimumLesionSize = value
        #self.createModels()

    def onMaxSizeChanged(self, value):
        self.MaximumLesionSize = value
        #self.createModels()

    def onThresholdMinChanged(self, value):
        self.ThresholdMin = value
        #self.createModels()

    def onThresholdMaxChanged(self, value):
        self.ThresholdMax = value
        #self.createModels()

    def onUpdate(self):
        self.createModels()

    def onSaveReport(self):
        """Save the current values in a persistent csv file"""
        self.statsAsCSV(self.reportsWidget, self.volumeNode)
        self.saveSegmentation()

    def createModels(self):
        # Reset previous model and labels
        self.deleteModels()
        for sr in self.summary_reports:
            self.labelScores[sr] = []
        self.selectedLabelList = []

        if self.calcificationType == 0 and self.volumeNode and self.roiNode:
            slicer.vtkSlicerCropVolumeLogic().CropVoxelBased(self.roiNode, self.volumeNode, self.croppedNode)
            croppedImage = sitk.ReadImage(sitkUtils.GetSlicerITKReadWriteAddress(self.croppedNode.GetName()))
            thresholdImage = sitk.BinaryThreshold(croppedImage, self.ThresholdMin, self.ThresholdMax, 1, 0)
            connectedCompImage = sitk.ConnectedComponent(thresholdImage, True)
            relabelImage = sitk.RelabelComponent(connectedCompImage)
            labelStatFilter = sitk.LabelStatisticsImageFilter()
            labelStatFilter.Execute(croppedImage, relabelImage)
            if relabelImage.GetPixelID() != sitk.sitkInt16:
                relabelImage = sitk.Cast(relabelImage, sitk.sitkInt16)
            sitk.WriteImage(relabelImage, sitkUtils.GetSlicerITKReadWriteAddress(self.labelsNode.GetName()))

            prod_spacing = np.prod(croppedImage.GetSpacing())

            nLabels = labelStatFilter.GetNumberOfLabels()
            self.totalScore = 0
            count = 0
            for n in range(0, nLabels):
                max = labelStatFilter.GetMaximum(n)
                mean = labelStatFilter.GetMean(n)
                size = labelStatFilter.GetCount(n)
                volume = size * self.voxelVolume

                # current label is discarted if volume not meet the maximum allowed threshold
                if volume > self.MaximumLesionSize:
                    continue

                # As ordered, we stop here if the volume of the current label is less than threshold
                if volume < self.MinimumLesionSize:
                    nLabels = n + 1
                    break
                score2d, volume, mass_score = self.agatston_computation(n, relabelImage, croppedImage, prod_spacing)
                # Agatston 3d:
                # -----------
                density_score = self.computeDensityScore(max)
                score3d = size*(self.sx*self.sy)*density_score
                mass_score = mean*volume

                # self.labelScores["Agatston Score"].append(score)
                self.labelScores["Agatston Score 3D"].append(score3d)
                self.labelScores["Agatston Score 2D"].append(score2d)
                self.labelScores["Mass Score"].append(mass_score)
                self.labelScores["Volume"].append(volume)
                self.selectedLabelList.append(0)

                # generate the contour
                marchingCubes = vtk.vtkDiscreteMarchingCubes()
                marchingCubes.SetInputData(self.labelsNode.GetImageData())
                marchingCubes.SetValue(0, count+1)
                marchingCubes.Update()

                transformPolyData = vtk.vtkTransformPolyDataFilter()
                transformPolyData.SetInputData(marchingCubes.GetOutput())
                mat = vtk.vtkMatrix4x4()
                self.labelsNode.GetIJKToRASMatrix(mat)
                trans = vtk.vtkTransform()
                trans.SetMatrix(mat)
                transformPolyData.SetTransform(trans)
                transformPolyData.Update()
                poly = vtk.vtkPolyData()
                poly.DeepCopy(transformPolyData.GetOutput())

                modelNode = slicer.vtkMRMLModelNode()
                slicer.mrmlScene.AddNode(modelNode)
                dnode = slicer.vtkMRMLModelDisplayNode()
                slicer.mrmlScene.AddNode(dnode)
                modelNode.AddAndObserveDisplayNodeID(dnode.GetID())
                modelNode.SetAndObservePolyData(poly)

                ct = slicer.mrmlScene.GetNodeByID('vtkMRMLColorTableNodeLabels')
                rgb = [0, 0, 0]
                ct.GetLookupTable().GetColor(count + 1, rgb)
                dnode.SetColor(rgb)
                # Enable Slice intersection
                dnode.SetSliceDisplayMode(0)
                dnode.SetSliceIntersectionVisibility(1)

                # self.addLabel(count, rgb, [score, mass_score, volume, mean, max])
                self.addLabel(count, rgb, [score2d, score3d, mass_score, volume, mean, max])
                count = count + 1

                self.modelNodes.append(modelNode)
                self.selectedLabels[poly] = n

            for sr in self.summary_reports:
                self.scoreField[sr].setText(self.totalScores[sr])