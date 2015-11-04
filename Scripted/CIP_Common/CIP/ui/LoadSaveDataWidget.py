'''
Created on Oct 20, 2014

@author: Jorge Onieva
This widget provides with a shortcut to load and save cases and label maps in a faster way than with the generic Slicer interface
'''

from __main__ import vtk, qt, ctk, slicer

import os
import re
from CIP.logic.SlicerUtil import SlicerUtil


class LoadSaveDataWidget(object):
    defaultLabelmapNodeNameExtensions = ["-label", "_partialLung", "_bodyComposition", "_structuresDetection"]
    defaultVolumesFileExtensions = [".nhdr", ".nrrd"]
    #OPERATION_CANCELLED = LoadSaveDataLogic.OPERATION_CANCELLED
    
    '''
    This widget provides with a shortcut to load and save cases and label maps in a faster way than with the generic Slicer interface.
    At the moment it is just ready for label maps, but it is easily extensible to store volumes too
    '''
    def __init__(self, parent = None):                
        """Widget constructor (existing module)"""
        if not parent:
            self.parent = slicer.qMRMLWidget()
            self.parent.setLayout(qt.QVBoxLayout())
            self.parent.setMRMLScene(slicer.mrmlScene)
        else:
            self.parent = parent
        self.layout = self.parent.layout()
        
        # Init variables 
        self.currentVolumeDisplayed = None
        self.currentLabelMapDispayed = None
        self.__saveVolumes__ = False
        self.__saveLabelMaps__ = True
        self.__disabledSave__ = False
        
        self.initEvents()
 
        
    def initEvents(self):
        """Init all the structures required for events mechanism"""
        self.eventsCallbacks = list()
        self.EVENT_LOAD = 0
        self.EVENT_PRE_SAVE = 1     # It will be triggered before attemting to save the current volume/labelmap
        self.EVENT_SAVE = 2
        self.EVENT_SAVEALL = 3
        self.events = [self.EVENT_LOAD, self.EVENT_PRE_SAVE, self.EVENT_SAVE, self.EVENT_SAVEALL]
    
            
    def setup(self, moduleName = "", labelmapNodeNameExtensions=defaultLabelmapNodeNameExtensions, 
                        volumesFileExtensions=defaultVolumesFileExtensions, iconsPath=None):
        """Setup the widget with the desride options.
        Defaults:
        - moduleName = "" --> used just to set the settings (for instance the last directory that was opened in the module). 
        - labelmapNodeNameExtensions = ["_partialLung", "_bodyComposition"] --> node names that will be used to identify a label map
        - volumesFileExtensions = [".nhdr", ".nrrd"] --> extensions of the files that will be allowed to be loaded. The first item will be used to save new label maps
        """
        settings = slicer.app.settings()
        try:
            self.IsDevelopment = settings.value('Developer/DeveloperMode').lower() == 'true'
        except:
            self.IsDevelopment = False            
        
        self.setParameters(moduleName, labelmapNodeNameExtensions, volumesFileExtensions)
     
        if not iconsPath:            
            iconsPath = SlicerUtil.CIP_ICON_DIR
            #print("Imported " + iconsPath)
        
        # ctkCollapsibleButton+frame that wrap everything
        self.loadSaveFilesCollapsibleButton = ctk.ctkCollapsibleButton()
        self.loadSaveFilesCollapsibleButton.text = "Quick Load / Save data (nrrd format)"
        self.layout.addWidget(self.loadSaveFilesCollapsibleButton)        
        loadSaveFilesLayout = qt.QVBoxLayout(self.loadSaveFilesCollapsibleButton) 
        self.buttonsFrame = qt.QFrame(self.parent)
        self.buttonsFrame.setLayout(qt.QHBoxLayout())
        
        # Buttons
        self.btnLoad = ctk.ctkPushButton()
        self.btnLoad.text = "Load cases"
        self.btnLoad.toolTip = "Load one or more cases and their bodyComposition label maps"
        self.btnLoad.setIcon(qt.QIcon("{0}/Load.png".format(iconsPath)))
        self.btnLoad.setIconSize(qt.QSize(32,32))        
        self.btnSave = ctk.ctkPushButton()
        self.btnSave.text = "Save labelmap"
        self.btnSave.toolTip = "Save the current bodyComposition labelmap"
        self.btnSave.setIcon(qt.QIcon("{0}/Save.png".format(iconsPath)))
        self.btnSave.setIconSize(qt.QSize(32,32))        
        self.btnSaveAll = ctk.ctkPushButton()
        self.btnSaveAll.text = "Save all labelmaps"
        self.btnSaveAll.toolTip = "Save all the opened bodyComposition labelmaps"
        self.btnSaveAll.setIcon(qt.QIcon("{0}/SaveAll.png".format(iconsPath)))
        self.btnSaveAll.setIconSize(qt.QSize(32,32))        
        self.buttonsFrame.layout().addWidget(self.btnLoad)
        self.buttonsFrame.layout().addWidget(self.btnSave)
        self.buttonsFrame.layout().addWidget(self.btnSaveAll)
        loadSaveFilesLayout.addWidget(self.buttonsFrame)     
        
        
        # Additional parameters
#         additionalParamsCollapsibleButton = ctk.ctkCollapsibleButton()
#         self.op = qt.QStyleOptionButton()
#         additionalParamsCollapsibleButton.initStyleOptions(self.op)
#         additionalParamsCollapsibleButton.text = "Other params"
#         self.layout.addWidget(additionalParamsCollapsibleButton)        
#         aditionalParamsLayout = qt.QFormLayout(additionalParamsCollapsibleButton)        
#            
#         # Chest regions combo box
#         self.cbFileType = qt.QComboBox(additionalParamsCollapsibleButton)
#         self.cbFileType.addItem("My item")
#         self.cbFileType.setItemData(0, "My key")    
# #         index=0
# #         for key, item in self.logic.regionTypes.iteritems():
# #             self.cbRegion.addItem(item[1])    # Add label description
# #             self.cbRegion.setItemData(index, key)     # Add string code
# #             index += 1
#         aditionalParamsLayout.addRow("Select the file type    ", self.cbFileType)
         
        
        # Connections
        self.btnLoad.connect('clicked()', self.onBtnLoadClicked)
        self.btnSave.connect('clicked()', self.onBtnSaveClicked)
        self.btnSaveAll.connect('clicked()', self.onBtnSaveAllClicked)
        
    def hide(self):
        self.loadSaveFilesCollapsibleButton.visible = False
        
    def show(self):
        self.loadSaveFilesCollapsibleButton.visible = True
    
    
    
    def setParameters(self, moduleName, labelmapNodeNameExtensions, volumesFileExtensions):
        self.logic = LoadSaveDataLogic(moduleName, labelmapNodeNameExtensions, volumesFileExtensions)
        self.labelmapNodeNameExtensions = labelmapNodeNameExtensions
        self.volumesFileExtensions = volumesFileExtensions
        self.moduleName = moduleName        
        
    def addObservable(self, event, callback):
        """Add a function that will be invoked when the corresponding event is triggered.
        The list of possible events are: EVENT_LOAD, EVENT_SAVE, EVENT_SAVEALL.
        Ex: myWidget.addListener(myWidget.EVENT_LOAD, self.onFileLoaded)"""
        if event not in self.events:
            raise Exception("Event not recognized. It must be one of these: EVENT_LOAD, EVENT_SAVE, EVENT_SAVEALL")
        
        # Add the event to the list of funcions that will be called when the matching event is triggered
        self.eventsCallbacks.append((event, callback)) 
    
    def __triggerEvent__(self, eventType, *params):
        """Trigger one of the possible events from the object.
        Ex:    self.__triggerEvent__(self.EVENT_LOAD, vols, errors) """
        for callback in (item[1] for item in self.eventsCallbacks if item[0] == eventType):
            #try:
                # Invoke the callback. The number of parameters of the callback function must match!
            callback(*params)
            #except Exception as ex:
                #print("ERROR: Callback could not be triggered for event. Error message: ", ex)
                #print("Callback that produced the error: ", callback)

    def collapseWidget(self, collapsed=True):
        """Collapse/expand all the items in the widget"""
        self.loadSaveFilesCollapsibleButton.collapsed = collapsed
        
    def disableSaving(self):
        """Disable all the file savings (labelmap and volume)"""
        self.__disabledSave__ = True
        
    def enableSaving(self):
        """Enable all the file savings (labelmap and volume). This is the default behaviour"""
        self.__disabledSave__ = False

    def onBtnLoadClicked(self):
        """Show a file dialog selector filtered by Nrrd files and load all the selected ones"""
        directory = self.logic.getLoadFilesDirectory()
        
        if not directory: directory = "~"
                
        fileNames = qt.QFileDialog.getOpenFileNames(self.parent, "Please select the files to open", 
                                directory, "Volume files (*{0})".format(" *".join(self.volumesFileExtensions)))
        
        # Save the directory for future use
        if fileNames:
            directory = os.path.dirname(fileNames[0])            
            self.logic.setLoadFilesDirectory(directory)
            if (self.IsDevelopment):
                print("Trying to load the following files: ")
                print(fileNames)
            self.disableEvents = True
            (vols, errors) = self.logic.loadVolumes(fileNames)
            self.disableEvents = False
            
            if len(errors) == 0:
                # Success. Inform about the number of files loaded
                numVols = numLabelMaps = 0
                for item in vols.values():
                    if item[0]: numVols += 1
                    if item[1]: numLabelMaps += 1                    
                qt.QMessageBox.information(slicer.util.mainWindow(), 'Files loaded', "{0} volumes and {1} label maps loaded".format(numVols, numLabelMaps))            
            else:
                # Show messagebox informing about the errors
                msg = "The following volumes could not be loaded: " + ", ".join(errors)
                qt.QMessageBox.warning(slicer.util.mainWindow(), 'Error loading files', msg)
                
            # If there is any callback, invoke it ("trigger" the event)    
            self.__triggerEvent__(self.EVENT_LOAD, vols, errors)     
#             for callback in (item for item in self.eventsCallbacks if item[0] == self.EVENT_LOAD):
#                 try:
#                     callback(vols, errors)
#                 except Exception as ex:
#                     print("Load callback could not be triggered for event. Error message: ")
#                     print(ex)
#                     print(callback)            
        else:
            if (self.IsDevelopment): print ("No files selected")
    
    def onBtnSaveClicked(self):
        """Save the current volume and/or labelmap"""
        # Trigger a "Pre_Save" event that could be used for example to set currentVolumeNode and currentLabelMapNode
        self.__triggerEvent__(self.EVENT_PRE_SAVE)

        if self.__disabledSave__:
            print("Saving is disabled")
            return

        currentVolumeNode = currentLabelMapNode = None
        if self.currentVolumeDisplayed == None and self.currentLabelMapDispayed == None:
            # Get the displayed nodes in "Red" slice if no current volume/label map set
            nodes = slicer.mrmlScene.GetNodesByClass("vtkMRMLSliceCompositeNode")
            # Call necessary to allow the iteration.
            nodes.InitTraversal()
            # Get the first CompositeNode (typically Red)
            compositeNode = nodes.GetNextItemAsObject()

            currentVolumeNode = slicer.mrmlScene.GetNodeByID(compositeNode.GetBackgroundVolumeID())
            currentLabelMapNode = slicer.mrmlScene.GetNodeByID(compositeNode.GetLabelVolumeID())
        else:
            currentVolumeNode = self.currentVolumeDisplayed
            currentLabelMapNode = self.currentLabelMapDispayed

        if self.__saveVolumes__ and currentVolumeNode:
            # TODO: save volume
            pass

        if self.__saveLabelMaps__ and currentLabelMapNode:
            try:
                if self.IsDevelopment: print ("Saving the volume: " + currentLabelMapNode.GetName())
                self.logic.saveLabelMap(currentVolumeNode, currentLabelMapNode)
                qt.QMessageBox.information(slicer.util.mainWindow(), "ACIL_LoadSaveData", "Labelmap saved succesfully")

                # If there is any callback, invoke it ("trigger" the event)
                self.__triggerEvent__(self.EVENT_SAVE, currentLabelMapNode.GetName())
            except Exception as ex:
                print (ex)
                qt.QMessageBox.critical(slicer.util.mainWindow(), 'ACIL_LoadSaveData' , 'Error saving files. Please check Python console for more information')
        else:
            if self.IsDevelopment: print("No files to save")

    def onBtnSaveAllClicked(self):    
        """Save all the files (at the moment just label maps)"""
        output = self.logic.saveAllLabelMaps()
        error = False
        savedFiles = len(output)
        for item in output:
            if item[1]:
                print("Error in file {0}: {1}".format(item[0], item[1]))
                savedFiles -= 1
                error = True
        
        if error:
            qt.QMessageBox.critical(slicer.util.mainWindow(), 'ACIL_LoadSaveData' , 'Error saving some files. {0} files were saved successfully. Please check Python console for more information'.format(savedFiles))
        else:
            qt.QMessageBox.information(slicer.util.mainWindow(), 'ACIL_LoadSaveData' , "{0} Labelmaps saved succesfully".format(savedFiles))
        
        # If there is any callback, invoke it ("trigger" the event) 
        self.__triggerEvent__(self.EVENT_SAVEALL, output)
        
        
class LoadSaveDataLogic(object):
    OPERATION_CANCELLED = 1
    
    def __init__(self, parentModuleName, labelmapNodeNameExtensions, filetypeExtensions):
        self.parentModuleName = parentModuleName
        self.labelmapNodeNameExtensions = labelmapNodeNameExtensions
        self.filetypeExtensions = filetypeExtensions
    
    def filesDirectoryKey(self):
        """We will use the Slicer settings with a convention format ACIL_LoadSaveData_[ModuleName]/FilesDirectory."""
        return "ACIL_LoadSaveData_{0}/FilesDirectory".format(self.parentModuleName)
    
    def getSearchPatternRegExp(self):
        '''Return the pattern to extract file names and extensions'''
        return "(?P<fileName>.+?)(?P<labelmapExtension>{0})?(?P<filetypeExtension>{1})$".format(
                str.join("|", self.labelmapNodeNameExtensions), 
                str.join("|", self.filetypeExtensions).replace(".", "\."))

    def getJustLabelmapsSearchPatternRegExp(self):
        '''Return the pattern to extract just file names that match with a labelmap node'''
        return "(?P<fileName>.+?)(?P<labelmapExtension>({0})(.*))".format(
                str.join("|", self.labelmapNodeNameExtensions)) 
                
    
    def getLoadFilesDirectory(self):
        """Get the last directory that the user was using to load/save files inside the module."""
        return slicer.app.settings().value(self.filesDirectoryKey())
    
    def setLoadFilesDirectory(self, value):
        """Set the last directory that the user was using to load/save files inside the module        
        Recall that we don't need to specify the type because it will be a string value (see http://pyqt.sourceforge.net/Docs/PyQt4/pyqt_qsettings.html)"""
        slicer.app.settings().setValue(self.filesDirectoryKey(), value)
    
    def loadVolumes(self, fileNames):        
        """Load a set of volumes and labelmaps.
        It returns two dictionaries:
            - A dictionary like volumes[fileName] = (VolumeNodeID (when exists), LabelMapVolumeID (when exists))
            - A list of the files that could not be loaded"""
        
        volumes = dict()
        errors = list()
        
        for fileName in fileNames:
            # Extract the dictionary key 
            dictKey = os.path.basename(fileName)
            # Get the regular expression pattern to get the data of the file
            pattern = self.getSearchPatternRegExp()            
            m = re.match(pattern, fileName, flags=re.IGNORECASE)
            if m:
                dictKey = m.group("fileName")
                if not volumes.has_key(dictKey):
                    # Create the new entry in the dictionary when not exists
                    volumes[dictKey] = [None,None]
                    print dictKey + " added"
         
                if m.group("labelmapExtension"):
                    # File is a label map                    
                    (success, vtkLabelmapVolumeNode) = slicer.util.loadLabelVolume(fileName, {}, returnNode=True)
                    
                    if success:
                        # The label map was loaded successfully. Store the Node ID in the corresponding entry in the dictionary                                                    
                        volumes[dictKey][1] = vtkLabelmapVolumeNode.GetID()
                    else:
                        # Add the filename to the errors list
                        errors.append(fileName)
                else:
                    # Common volume
                    (success, vtkVolumeNode) = slicer.util.loadVolume(fileName, {}, returnNode=True)
                    if success:
                        # The label map was loaded successfully. Store the Node ID in the corresponding entry in the dictionary                                                    
                        volumes[dictKey][0] = vtkVolumeNode.GetID()
                    else:
                        # Add the filename to the errors list
                        errors.append(fileName)
            
        return(volumes, errors)
                            
                    
    def saveLabelMap(self, currentVolumeNode, labelMapNode):
        """Save a label map node as a NRRD file (with header).
        It will be saved in directory/labelMapNodeName, overwriting existing files"""        
        
        # Check if the file already exists
        labelmapStorageNode = labelMapNode.GetStorageNode() 
        if not labelmapStorageNode:
            # New label map (there is no file saved)
            # Get the directory where the file will be saved. try to save first in the same place as the master volume if it exists
            if currentVolumeNode: 
                storageNode = currentVolumeNode.GetStorageNode()        
                directory = os.path.dirname(storageNode.GetFileName())
            else:
                directory = self.getLoadFilesDirectory()        
            
            print("Creating new storage node")
            storageNode = labelMapNode.CreateDefaultStorageNode()
            #storageNode = slicer.mrmlScene.CreateNodeByClass('vtkMRMLVolumeArchetypeStorageNode')
            storageNode.SetScene(slicer.mrmlScene)
            slicer.mrmlScene.AddNode(storageNode)
            labelMapNode.SetAndObserveStorageNodeID(storageNode.GetID())         
            # Build the file name. When the extension is "nhdr" Slicer saves automatically the NRRD file with header (by default).
            # The default extension is the first one in self.volumesFileExtensions
            fileName = "{0}/{1}{2}".format(directory, labelMapNode.GetName(), self.filetypeExtensions[0]) 
            storageNode.SetFileName(fileName)         
            # Save the file
            storageNode.WriteData(labelMapNode)
            return True
        else:        
            # The label map was loaded from a file. Save in the same file
            fileName = labelmapStorageNode.GetFileName()
            # Save node (it will overwrite the current file)
            return slicer.util.saveNode(labelMapNode, fileName)
        
    def saveAllLabelMaps(self):
        """Search for all the opened label map nodes that match the label map nodes working extension 
        (ex: all the nodes named xxx_bodycomposition).
        Return a list of tuples (labelmapNodeName, [ErrorMessage])
        """    
         
        savedNodes = list()
        # Get the pattern to extract the labelmaps file names
        pattern = self.getJustLabelmapsSearchPatternRegExp()
        nodes = slicer.mrmlScene.GetNodesByClass("vtkMRMLScalarVolumeNode")
        # Call necessary to allow the iteration.
        nodes.InitTraversal()        
        node = nodes.GetNextItemAsObject()
        
        while node:
            # Check if the node is one of our "valid" labelmaps
            m = re.match(pattern, node.GetName(), flags=re.IGNORECASE)
            if m:
                # Volume is a label map
                try:                            
                    result = self.saveLabelMap(None, node)    
                    # If everything ok, store the saved node without errors
                    if result:
                        savedNodes.append((node.GetName(), None))
                    else:
                        savedNodes.append((node.GetName(), "Unknown error"))                
                except Exception as ex:                    
                    savedNodes.append((node.GetName(), ex.message))
                
            node = nodes.GetNextItemAsObject()    
        
        return savedNodes
