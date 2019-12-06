# -*- coding: utf-8 -*-
import csv, os, time, pprint
from __main__ import qt, ctk, slicer

from CIP.logic.SlicerUtil import SlicerUtil

class PreProcessingWidget():
    
    def __init__(self, moduleName, parentWidget = None):
        """Widget constructor (existing module)"""
#        EventsTrigger.__init__(self)
        
        if not parentWidget:
            self.parent = slicer.qMRMLWidget()
            self.parent.setLayout(qt.QVBoxLayout())
            self.parent.setMRMLScene(slicer.mrmlScene)
        else:
            self.parent = parentWidget
        self.__moduleName__ = moduleName
        self.layout = self.parent.layout()
        self.logic = PreProcessingLogic(moduleName)

    def setup(self):

        self.FilteringFrame = qt.QFrame()
        self.FilteringFrame.setLayout(qt.QVBoxLayout())
        self.FilteringFrame.enabled = False
        self.FilteringFrame.setObjectName('FilteringFrame')
        self.FilteringFrame.setStyleSheet('#FilteringFrame {border: 1px solid lightGray; color: black; }')
        self.layout.addWidget( self.FilteringFrame )    
    
        filterLabel = qt.QLabel()
        filterLabel.setText('Filtering')
        self.FilteringFrame.layout().addWidget(filterLabel)
    
        radioButtonsGroup = qt.QGroupBox()
        radioButtonsGroup.setLayout(qt.QHBoxLayout())
        radioButtonsGroup.setFixedWidth(120)
        radioButtonsGroup.setObjectName('radioButtonsGroup')
        radioButtonsGroup.setStyleSheet('#radioButtonsGroup {border: 1px solid white; color: black; }')   
    
        self.filterOnRadioButton = qt.QRadioButton()
        self.filterOnRadioButton.setText('On')
        self.filterOnRadioButton.setChecked(0)
        radioButtonsGroup.layout().addWidget(self.filterOnRadioButton)
        
        self.filterOffRadioButton = qt.QRadioButton()
        self.filterOffRadioButton.setText('Off')
        self.filterOffRadioButton.setChecked(1)
        radioButtonsGroup.layout().addWidget(self.filterOffRadioButton)
    
        self.FilteringFrame.layout().addWidget(radioButtonsGroup)          
        
        self.filterOptionsFrame = qt.QFrame()
        self.filterOptionsFrame.setLayout(qt.QVBoxLayout())
        self.filterOptionsFrame.setObjectName('filterOptionsFrame')
        self.filterOptionsFrame.setStyleSheet('#filterOptionsFrame {border: 0.5px solid lightGray; color: black; }')   
        self.filterOptionsFrame.hide()
    
        self.FilteringFrame.layout().addWidget(self.filterOptionsFrame)
        
        self.filterApplication = qt.QCheckBox()
        self.filterApplication.setText('Filter for Phenotype Analysis')
        self.filterApplication.setChecked(0)
        self.filterOptionsFrame.layout().addWidget(self.filterApplication)     
        
        filterOptionsGroup = qt.QGroupBox()
        filterOptionsGroup.setLayout(qt.QHBoxLayout())
        filterOptionsGroup.setFixedWidth(220)
        filterOptionsGroup.setObjectName('filterOptionsGroup')
        filterOptionsGroup.setStyleSheet('#filterOptionsGroup {border: 1px solid white; color: black; }')
    
        self.NLMFilterRadioButton = qt.QRadioButton()
        self.NLMFilterRadioButton.setText('NLM')
        self.NLMFilterRadioButton.setChecked(1)
        filterOptionsGroup.layout().addWidget(self.NLMFilterRadioButton)
        
        self.MedianFilterRadioButton = qt.QRadioButton()
        self.MedianFilterRadioButton.setText('Median')
        self.MedianFilterRadioButton.setChecked(0)
        filterOptionsGroup.layout().addWidget(self.MedianFilterRadioButton)
    
        self.GaussianFilterRadioButton = qt.QRadioButton()
        self.GaussianFilterRadioButton.setText('Gaussian')
        self.GaussianFilterRadioButton.setChecked(0)
        filterOptionsGroup.layout().addWidget(self.GaussianFilterRadioButton)
    
        self.filterOptionsFrame.layout().addWidget(filterOptionsGroup)  
    
        # Filter Params    
        FilterParams = qt.QFrame()
        FilterParams.setLayout(qt.QVBoxLayout())
        self.filterOptionsFrame.layout().addWidget(FilterParams)
        
        DimGroupBox = qt.QGroupBox()
        DimGroupBox.setLayout(qt.QHBoxLayout())
        DimGroupBox.setFixedWidth(180)
        DimGroupBox.setObjectName('DimGroupBox')
        DimGroupBox.setStyleSheet('#DimGroupBox {border: 1px solid white; color: black; }')
        FilterParams.layout().addWidget(DimGroupBox)    
    
        FilterDimensionLabel = qt.QLabel()
        FilterDimensionLabel.setText('Dimensions: ')
        FilterDimensionLabel.setToolTip('Choose if the filter has to operate in 2D or 3D.')
        DimGroupBox.layout().addWidget(FilterDimensionLabel)
        
        self.Filt2DOption = qt.QPushButton()
        self.Filt2DOption.setText('2D')
        self.Filt2DOption.setCheckable(1)
        self.Filt2DOption.setChecked(1)
        self.Filt2DOption.setAutoExclusive(1) 
        self.Filt2DOption.setFixedWidth(45)
        DimGroupBox.layout().addWidget(self.Filt2DOption)
    
        self.Filt3DOption = qt.QPushButton()
        self.Filt3DOption.setText('3D')
        self.Filt3DOption.setCheckable(1)
        self.Filt3DOption.setChecked(0)
        self.Filt3DOption.setFixedWidth(45)
        self.Filt3DOption.setAutoExclusive(1)    
        DimGroupBox.layout().addWidget(self.Filt3DOption)
    
        StrengthGroupBox = qt.QGroupBox()
        StrengthGroupBox.setLayout(qt.QHBoxLayout())
        StrengthGroupBox.setFixedWidth(270)
        StrengthGroupBox.setObjectName('StrengthGroupBox')
        StrengthGroupBox.setStyleSheet('#StrengthGroupBox {border: 1px solid white; color: black; }')
        FilterParams.layout().addWidget(StrengthGroupBox)
    
        FilterStrengthLabel = qt.QLabel()
        FilterStrengthLabel.setText('Strength: ')
        FilterStrengthLabel.setToolTip('Choose strength of the filtering process.')
        StrengthGroupBox.layout().addWidget(FilterStrengthLabel)  
    
        self.SmoothOption = qt.QPushButton()
        self.SmoothOption.setText('Smooth')
        self.SmoothOption.setCheckable(1)
        self.SmoothOption.setChecked(1)
        self.SmoothOption.setAutoExclusive(1) 
        self.SmoothOption.setFixedWidth(60)
        StrengthGroupBox.layout().addWidget(self.SmoothOption)
        
        self.MediumOption = qt.QPushButton()
        self.MediumOption.setText('Medium')
        self.MediumOption.setCheckable(1)
        self.MediumOption.setChecked(0)
        self.MediumOption.setFixedWidth(60)
        self.MediumOption.setAutoExclusive(1)    
        StrengthGroupBox.layout().addWidget(self.MediumOption)
    
        self.HeavyOption = qt.QPushButton()
        self.HeavyOption.setText('Heavy')
        self.HeavyOption.setCheckable(1)
        self.HeavyOption.setChecked(0)
        self.HeavyOption.setFixedWidth(60)
        self.HeavyOption.setAutoExclusive(1)    
        StrengthGroupBox.layout().addWidget(self.HeavyOption)
    
        # Downsampling option for label map creation
        self.LMCreationFrame = qt.QFrame()
        self.LMCreationFrame.setLayout(qt.QVBoxLayout())
        self.LMCreationFrame.enabled = False
        self.LMCreationFrame.setObjectName('LMCreationFrame')
        self.LMCreationFrame.setStyleSheet('#LMCreationFrame {border: 1px solid lightGray; color: black; }')
        self.parent.layout().addWidget(self.LMCreationFrame)    
        
        LMCreationLabel = qt.QLabel()
        LMCreationLabel.setText('Label Map Creation:')
        self.LMCreationFrame.layout().addWidget(LMCreationLabel)    
            
        self.DownSamplingGroupBox = qt.QGroupBox()
        self.DownSamplingGroupBox.setLayout(qt.QHBoxLayout())
        self.DownSamplingGroupBox.setFixedWidth(130)
        self.DownSamplingGroupBox.setObjectName('DownSamplingGroupBox')
        self.DownSamplingGroupBox.setStyleSheet('#DownSamplingGroupBox {border: 1px solid white; color: black; }')
        self.DownSamplingGroupBox.setToolTip('Choose between fast and slow label map creation.')
        self.LMCreationFrame.layout().addWidget(self.DownSamplingGroupBox)
     
        self.FastOption = qt.QRadioButton()
        self.FastOption.setText('Fast')
        self.FastOption.setCheckable(1)
        self.FastOption.setChecked(0)
        self.DownSamplingGroupBox.layout().addWidget(self.FastOption)     
    
        self.SlowOption = qt.QRadioButton()
        self.SlowOption.setText('Slow')
        self.SlowOption.setCheckable(1)
        self.SlowOption.setChecked(1)
        self.DownSamplingGroupBox.layout().addWidget(self.SlowOption)
        
        self.filterOnRadioButton.connect('toggled(bool)', self.showFilterParams)
        self.filterOffRadioButton.connect('toggled(bool)', self.hideFilterParams)
        
    def showFilterParams(self):
        self.hideFilterOptions(False)
    
    def hideFilterParams(self):
        self.hideFilterOptions(True)

    def hideFilteringFrame(self, hide):
        """ Show/Hide the filtering frame 
            param show: True/False
        """
        self.FilteringFrame.setHidden(hide)
    
    def enableFilteringFrame(self,enabled):
        """ Enable/Disable the filtering frame 
            param enabled: True/False
        """
        self.FilteringFrame.setEnabled(enabled)

    def hideFilterOptions(self, hide):
        """ Show/Hide the filtering options 
            param show: True/False
        """
        self.filterOptionsFrame.setHidden(hide)
 
    def enableFilterOptions(self,enabled):
        """ Enable/Disable the filtering options 
            param enabled: True/False
        """
        self.filterOptionsFrame.setEnabled(enabled)
        
    def showLMFrame(self,show):
        """ Show/Hide the options for labelmap creation 
            param enabled: True/False
        """
        self.LMCreationFrame.setShown(show)
        
    def enableLMFrame(self,enabled):
        """ Enable/Disable the options for labelmap creation
            param enabled: True/False
        """
        self.LMCreationFrame.setEnabled(enabled)
        
    def filterInputCT(self,inputCT):        
        if self.NLMFilterRadioButton.checked:
            method = 'NLM'
            
            sr = [3,3,3]
            cr = [5,5,5]
            if self.Filt2DOption.checked:
                sr[2] = 1
                cr[2] = 1
            
            noise_power = 3.0 # Smooth filtering
            nlm_h = 0.8
            nlm_ps = 2.0
            if self.MediumOption.checked: # Medium strength
                noise_power = 4.0
                nlm_h = 1.0
            elif self.HeavyOption.checked: # Heavy strength
                noise_power = 5.0
                nlm_h = 1.2
                
            self.logic.filterCT(inputCT,method,s_rad=sr,c_rad=cr,noisePower=noise_power,h=nlm_h,ps=nlm_ps)
            
        elif self.MedianFilterRadioButton.checked: 
            method = 'Median'
            neighborhood = [1,1,1]
            
            if self.MediumOption.checked: # Medium strength
                neighborhood = [2,2,2]
            elif self.HeavyOption.checked: # Heavy strength
                neighborhood = [3,3,3]
            
            if self.Filt2DOption.checked: # 2D filtering
                neighborhood[2] = 1
            
            self.logic.filterCT(inputCT,method,n_rad=neighborhood)
            
        elif self.GaussianFilterRadioButton.checked:
            method = 'Gaussian'            
            s = 1.0      
            
            if self.MediumOption.checked: # Medium strength
                s = 2.0
            elif self.HeavyOption.checked: # Heavy strength
                s = 3.0
            self.logic.filterCT(inputCT,method,sigma=s)
        
    def createPartialLM(self,inputCT,labelMap):
        speed = 'Slow'
        if self.FastOption.checked:
            speed = 'Fast'
        self.logic.generatePartialLungLabelMap(inputCT,labelMap,speed)
        for color in ['Red', 'Yellow', 'Green']:
            slicer.app.layoutManager().sliceWidget(color).sliceLogic().GetSliceCompositeNode().SetBackgroundVolumeID(inputCT.GetID())
        
    def warningMessageForLM(self):
        answer = qt.QMessageBox.question(slicer.util.mainWindow(),self.__moduleName__, 'Do you want to create a lung label map?', qt.QMessageBox.Yes | qt.QMessageBox.No)
        return answer

#############################
##
class PreProcessingLogic(object):

    def __init__(self, moduleName):
        self.__moduleName__ = moduleName
           
    def filterCT(self,input_ct,method,s_rad=[3,3,3],c_rad=[5,5,5],noisePower=3.0,h=0.8,ps=2.0,n_rad=[1,1,1],sigma=1.0):
        if method=='NLM': # NLM Filter
            generatenlmfilteredimage = slicer.modules.generatenlmfilteredimage
            parameters = {
                      "ctFileName": input_ct.GetID(),
                      "outputFileName": input_ct.GetID(),
                      "iSigma": noisePower,
                      "iRadiusSearch": s_rad,
                      "iRadiusComp": c_rad,
                      "iH": h,
                      "iPs": ps,
                      }
            slicer.cli.run(generatenlmfilteredimage,None,parameters,wait_for_completion=True)

        elif method=='Median': # Median Filter
            medianimagefilter = slicer.modules.medianimagefilter
            parameters = {
                        "inputVolume": input_ct.GetID(),
                        "outputVolume": input_ct.GetID(),
                        "neighborhood": n_rad, 
                        }
            slicer.cli.run(medianimagefilter,None,parameters,wait_for_completion=True)
        elif method=='Gaussian':
            gaussianblurimagefilter = slicer.modules.gaussianblurimagefilter       
            parameters = {
                      "inputVolume": input_ct.GetID(),
                      "outputVolume": input_ct.GetID(),
                      "sigma": sigma,
                      }
            slicer.cli.run(gaussianblurimagefilter,None,parameters,wait_for_completion=True)

    def generatePartialLungLabelMap(self, input_ct, label_map, speed):
        """Create partial lung label map from input ct image
        :params input_ct: ct image, speed: fast or slow creation, labelNode: node for 
        created labelmap
        """
        inputNode = input_ct
        if speed=='Fast':          
            inputNode = self.downsampleCT(input_ct)
                      
        generatepartiallunglabelmap = slicer.modules.generatepartiallunglabelmap
#        labelNode = slicer.mrmlScene.AddNode(slicer.vtkMRMLLabelMapVolumeNode())
#        self.CTlabelNode.SetName(self.CTNode.GetName() + '_partialLungLabelMap')
        parameters = {
              "ctFileName": inputNode.GetID(),
              "outputLungMaskFileName": label_map.GetID(),	  
              }
        slicer.cli.run(generatepartiallunglabelmap,None,parameters,wait_for_completion=True)
    
        if speed=='Fast':
            label_map = self.upsampleLabel(label_map)
            slicer.mrmlScene.RemoveNode(inputNode)
        
    def downsampleCT(self, input_image):
        """Downsample input image by factor 2
        :params input_image: image to downsample
        """
        oldSpacing = input_image.GetSpacing()
    
        newSpacing = []    
        newSpacing.append(oldSpacing[0]*2)
        newSpacing.append(oldSpacing[1]*2)
        newSpacing.append(oldSpacing[2])
    
        resamplescalarvolume = slicer.modules.resamplescalarvolume
        upsampledNode = slicer.mrmlScene.AddNode(slicer.vtkMRMLScalarVolumeNode())
    
        parameters = {
              "outputPixelSpacing": newSpacing,
              "InputVolume": input_image.GetID(),
              "OutputVolume": upsampledNode.GetID(),
        }
        slicer.cli.run(resamplescalarvolume,None,parameters,wait_for_completion=True)    
        return upsampledNode
        
    def upsampleLabel(self, labelMap):
        """Upsample input image by factor 2
        :params input_image: image to downsample
        """
        
        oldSpacing = labelMap.GetSpacing()
    
        newSpacing = []    
        newSpacing.append(oldSpacing[0]/2)
        newSpacing.append(oldSpacing[1]/2)
        newSpacing.append(oldSpacing[2])
    
        resamplescalarvolume = slicer.modules.resamplescalarvolume
    
        parameters = {
              "outputPixelSpacing": newSpacing,
              "InputVolume": labelMap.GetID(),
              "OutputVolume": labelMap.GetID(),
              "interpolationType":'nearestNeighbor',
              }
        slicer.cli.run(resamplescalarvolume,None,parameters,wait_for_completion=True)
    
        return labelMap