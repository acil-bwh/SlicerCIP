"""ACIL_GetImage is a module developed for the internal use of the Applied Chest Imaging Laboratory to download
cases stored in MAD server via ssh.
It works both in Unix/Mac/Windows, and it uses an internal SSH key created specifically for this purpose, so it
doesn't need that the user has an authorized SSH key installed.
First version: Jorge Onieva (ACIL, jonieva@bwh.harvard.edu). Sept 2014"""

import os, sys
from __main__ import vtk, qt, ctk, slicer

from collections import OrderedDict
import subprocess

# Add the CIP common library to the path if it has not been loaded yet
try:
    from CIP.logic.SlicerUtil import SlicerUtil
except Exception as ex:
    currentpath = os.path.dirname(os.path.realpath(__file__))
    # We assume that CIP_Common is in the development structure
    path = os.path.normpath(currentpath + '/../../Scripted/CIP_Common')
    if not os.path.exists(path):
        # We assume that CIP is a subfolder (Slicer behaviour)
        path = os.path.normpath(currentpath + '/CIP')
    sys.path.append(path)
    print("The following path was manually added to the PythonPath in CIP_GetImage: " + path)
    from CIP.logic.SlicerUtil import SlicerUtil

from CIP.logic import Util
import CIP.ui as CIPUI


class CIP_GetImage:
    """Load cases from a SSH server or other device"""
    def __init__(self, parent):
        """Constructor for main class"""
        self.parent = parent        
        #ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "CIP GetImage"
        self.parent.categories = ["Chest Imaging Platform.Modules"]
        self.parent.dependencies = []
        self.parent.contributors = ["Jorge Onieva", "Applied Chest Imaging Laboratory", "Brigham and Women's Hospital"] 
        self.parent.helpText = "This is an internal module to load images from MAD repository via SSH"
        self.parent.acknowledgementText = SlicerUtil.ACIL_AcknowledgementText


class CIP_GetImageWidget:
    """Visual object"""
    
    # Study ids. Convention: Descriptive text (key) / Name of the folder in the server 
    studyIds = OrderedDict()
    studyIds["Study 1"] = "Study1"
    studyIds["Study 2"] = "Study2"
    studyIds["Other"] = "Other"
    
    
    # Image types. You can add as many as different volume types you have
    # Convention: 
    #     Descriptive text (key) 
    #     Files extension (example: "processed").     
    imageTypes = OrderedDict()
    imageTypes["CT"] = ""   # Default. No extension
    imageTypes["CT Processed"] = "processed"   # Default. No extension
    
    
    # Label maps types. Idem  
    # Convention: 
    # Descriptive text (key) 
    # Checked by default
    # Files extension (example: case_partialLungLabelMap.nrrd) 
    labelMapTypes = OrderedDict()
    labelMapTypes["Partial Lung"] = (False, "_partialLungLabelMap")
    labelMapTypes["Body Composition"] = (False, "_bodyComposition")
    labelMapTypes["Body Composition (interactive)"] = (False, "_interactiveBodyComposition")

    
    def __init__(self, parent = None):
        """Widget constructor (existing module)"""
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
        """Init the widget """
        self.modulePath = SlicerUtil.getModuleFolder("CIP_GetImage")
        
        self.resourcesPath = os.path.join(self.modulePath, "CIP_GetImage_Resources")
        self.StudyId = ""


        
        self.logic = CIP_GetImageLogic(self.modulePath)
        
        # Widget to load cases faster
        self.loadSaveDatabuttonsWidget = CIPUI.LoadSaveDataWidget(parentWidget=self.parent)
        self.loadSaveDatabuttonsWidget.setup(moduleName="CIP_GetImage")
        
        #
        # Obligatory parameters area
        #
        parametersCollapsibleButton = ctk.ctkCollapsibleButton()
        parametersCollapsibleButton.text = "Image data"
        self.layout.addWidget(parametersCollapsibleButton)        
        parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)
        
        # Study radio buttons
        label = qt.QLabel()
        label.text = "Select the study:"
        parametersFormLayout.addRow(label)        
        
        self.rbgStudy=qt.QButtonGroup() 
        
        for key in self.studyIds:
            rbStudyid = qt.QRadioButton(key)
            self.rbgStudy.addButton(rbStudyid)     
            parametersFormLayout.addWidget(rbStudyid)        
         
        self.txtOtherStudy = qt.QLineEdit()
        self.txtOtherStudy.hide()
        parametersFormLayout.addWidget(self.txtOtherStudy)

        
        # Case id 
        self.txtCaseId = qt.QLineEdit()        
        parametersFormLayout.addRow("Case ID     ", self.txtCaseId)
        
        # Image types
        label = qt.QLabel()
        label.text = "Select the images that you want to load:"
        parametersFormLayout.addRow(label)
        
        self.cbsImageTypes = []
        for key in self.imageTypes:            
            check = qt.QCheckBox()
            check.checked = True
            check.setText(key)
            parametersFormLayout.addWidget(check)
            self.cbsImageTypes.append(check) 
        
        # Label maps    
        label = qt.QLabel()
        label.text = "Select the label maps that you want to load:"
        parametersFormLayout.addRow(label)
        
        # Labelmap types checkboxes
        self.cbsLabelMapTypes = []
        for key in self.labelMapTypes:            
            check = qt.QCheckBox()
            check.setText(key)
            check.checked = self.labelMapTypes[key][0]            
            parametersFormLayout.addWidget(check)        
            self.cbsLabelMapTypes.append(check)         
        
        
        # Load image Button        
        self.downloadButton = qt.QPushButton("Download")                
        self.downloadButton.toolTip = "Load the image"        
        #self.downloadButton.enabled = False
        self.downloadButton.setStyleSheet("background-color: green; font-weight:bold; color:white" )
        parametersFormLayout.addRow(self.downloadButton)
        self.downloadButton.connect('clicked (bool)', self.onDownloadButton)
                

        # Information message
        self.lblDownloading = qt.QLabel()
        self.lblDownloading.text = "Downloading images. Please wait..."
        self.lblDownloading.hide()
        parametersFormLayout.addRow(self.lblDownloading)        
        
        
        #
        # Optional Parameters
        #
        optionalParametersCollapsibleButton = ctk.ctkCollapsibleButton()
        optionalParametersCollapsibleButton.text = "Optional parameters"
        self.layout.addWidget(optionalParametersCollapsibleButton)
        optionalParametersFormLayout = qt.QFormLayout(optionalParametersCollapsibleButton)
     
        # Local storage (Slicer temporary path)                
        self.localStoragePath = "{0}/CIP".format(slicer.app.temporaryPath)        
        if not os.path.exists(self.localStoragePath):            
            os.makedirs(self.localStoragePath)
            # Make sure that everybody has write permissions (sometimes there are problems because of umask)
            os.chmod(self.localStoragePath, 0777)
            
        self.storagePathButton = ctk.ctkDirectoryButton()
        self.storagePathButton.directory = self.localStoragePath

        optionalParametersFormLayout.addRow("Local directory: ", self.storagePathButton)     
        
        # Connection type (SSH, "normal")
        label = qt.QLabel()
        label.text = "Connection type:"
        optionalParametersFormLayout.addRow(label)
        
        self.rbgConnectionType=qt.QButtonGroup() 
        self.rbSSH = qt.QRadioButton("SSH (secure connection)")
        self.rbSSH.setChecked(True)
        self.rbgConnectionType.addButton(self.rbSSH)        
        optionalParametersFormLayout.addWidget(self.rbSSH)
        
        self.rbCP = qt.QRadioButton("Common")
        self.rbgConnectionType.addButton(self.rbCP)
        optionalParametersFormLayout.addWidget(self.rbCP)    
        
     
        
        # SSH Server login
        self.txtServer = qt.QLineEdit()
        s = SlicerUtil.settingGetOrSetDefault("CIP_GetImage", "server", "This is your ssh user and server. Example: myuser@192.168.1.1")
        self.txtServer.text = s     # This is your ssh user and server. Example: myuser@192.168.1.1"
        optionalParametersFormLayout.addRow("Server:", self.txtServer)

        # Server root path
        self.txtServerpath = qt.QLineEdit()
        s = SlicerUtil.settingGetOrSetDefault("CIP_GetImage", "serverRootPath", "This is your root path to search for files. Ex: /Cases/Processed")
        self.txtServerpath.text = s     # This is your root path to search for files. Ex: /Cases/Processed
        optionalParametersFormLayout.addRow("Server root path:", self.txtServerpath)
        
                
        # SSH Private key    
        self.txtPrivateKeySSH = qt.QLineEdit()        
        s = SlicerUtil.settingGetOrSetDefault("CIP_GetImage", "sshKey", "")
        self.txtPrivateKeySSH.text = s # this is the full path to your ssh key if you need it. Be aware of Unix/Windows comaptibility (hint: use os.path.join)
                                        # Please notice that you won't need a SSH key if your computer already has one locally installed"
        optionalParametersFormLayout.addRow("SSH private key (leave blank for computer's default):     ", self.txtPrivateKeySSH)
        
        # Cache mode 
        self.cbCacheMode = qt.QCheckBox("Cache mode activated")
        self.cbCacheMode.setChecked(True)     # Cache mode is activated by default
        optionalParametersFormLayout.addRow("", self.cbCacheMode)        
        
        # Clean cache Button        
        self.cleanCacheButton = qt.QPushButton("Clean cache")                
        self.cleanCacheButton.toolTip = "Remove all the local cached files"
        optionalParametersFormLayout.addRow(self.cleanCacheButton)
        optionalParametersCollapsibleButton.collapsed = True

        if SlicerUtil.IsDevelopment:
            # reload button
            self.reloadButton = qt.QPushButton("Reload (just development)")
            self.reloadButton.toolTip = "Reload this module (for development purposes)."
            self.reloadButton.name = "Reload"
            self.layout.addWidget(self.reloadButton)
            self.reloadButton.connect('clicked()', self.onReload)

        # Add vertical spacer
        self.layout.addStretch(1)


        # Connections
        self.rbgStudy.connect("buttonClicked (QAbstractButton*)", self.onRbStudyClicked)
        self.txtOtherStudy.connect("textEdited (QString)", self.onTxtOtherStudyEdited)
        self.rbgConnectionType.connect("buttonClicked (QAbstractButton*)", self.onRbgConnectionType)         
        
        self.storagePathButton.connect("directorySelected(QString)", self.onTmpDirChanged)
        self.cleanCacheButton.connect('clicked (bool)', self.onCleanCacheButtonClicked)
     
    def saveSettings(self):
        """Save the current values in settings to reuse it in future sessions"""
        SlicerUtil.setSetting("CIP_GetImage", "sshKey", self.txtPrivateKeySSH.text)
        SlicerUtil.setSetting("CIP_GetImage", "server", self.txtServer.text)
        SlicerUtil.setSetting("CIP_GetImage", "serverRootPath", self.txtServerpath.text)

    def cleanup(self):
        self.saveSettings()
        

    # 
    # Events handling
    #
    def onDownloadButton(self):
        """Click in download button"""
        # Check if there is a Study and Case introduced
        self.CaseId = self.txtCaseId.text.strip()
        if self.CaseId and self.StudyId:
            self.lblDownloading.show()
            slicer.app.processEvents()        
            
    
            # Get the selected image types and label maps
            imageTypes = [self.imageTypes[cb.text] for cb in filter(lambda check: check.isChecked(), self.cbsImageTypes)]
            labelMapExtensions = [self.labelMapTypes[cb.text] for cb in filter(lambda check: check.isChecked(), self.cbsLabelMapTypes)]
             
            result = self.logic.loadCase(self.txtServer.text, self.txtServerpath.text, self.StudyId, self.txtCaseId.text, imageTypes, labelMapExtensions, self.localStoragePath, self.cbCacheMode.checkState(), self.rbSSH.isChecked(), self.txtPrivateKeySSH.text)
                    
            self.lblDownloading.hide()
            if (result == Util.ERROR):
                self.msgBox = qt.QMessageBox(qt.QMessageBox.Warning, 'Error', "There was an error when downloading some of the images of this case. It is possible that some of the selected images where not available in the server. Please review the log console for more details.\nSuggested actions:\n-Empty cache\n-Restart Slicer")
                self.msgBox.show()
        else:
            # Show info messsage
            self.msgBox = qt.QMessageBox(qt.QMessageBox.Information, 'Attention', "Please make sure that you have selected a study and a case")
            self.msgBox.show()
        
         
    def onRbStudyClicked(self, button):
        """Study radio buttons clicked (any of them)"""
        self.StudyId = self.studyIds[button.text]        
        self.txtOtherStudy.visible = (button.text == "Other")
        if (self.txtOtherStudy.visible):
            self.StudyId = self.txtOtherStudy.text.strip()
        #self.checkDownloadButtonEnabled()
        
        
    def onRbgConnectionType(self, button):        
        self.txtServer.enabled = self.txtPrivateKeySSH.enabled = self.rbSSH.isChecked()
        #self.txtPrivateKeySSH.enabled = self.rbSSH.checked
        
    def onTxtOtherStudyEdited(self, text):
        """Any letter typed in "Other study" text box """
        self.StudyId = text
        #self.checkDownloadButtonEnabled()
        
    def onCleanCacheButtonClicked(self):
        """Clean cache button clicked. Remove all the files in the current local storage path directory"""
        import shutil
        # Remove directory
        shutil.rmtree(self.localStoragePath, ignore_errors=True)
        # Recreate it (this is a safe method for symbolic links)
        os.makedirs(self.localStoragePath)
        # Make sure that everybody has write permissions (sometimes there are problems because of umask)
        os.chmod(self.localStoragePath, 0777)
    
    def onTmpDirChanged(self, d):
        print ("Temp dir changed. New dir: " + d)
        self.localStoragePath = d


    def onReload(self, moduleName="CIP_GetImage"):
        """Reload the module. Just for development purposes. This is a combination of the old and new style in modules writing"""
        try:
            slicer.util.reloadScriptedModule(moduleName)
        except:
        #Generic reload method for any scripted module.
        #ModuleWizard will subsitute correct default moduleName.    
            import imp, sys
             
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
            # parent = slicer.util.findChildren(name='%s Reload' % moduleName)[0].parent()
            parent = self.parent
            for child in parent.children():
                try:
                    child.hide()
                except AttributeError:
                    pass
            globals()[widgetName.lower()] = eval(
                'globals()["%s"].%s(parent)' % (moduleName, widgetName))
            globals()[widgetName.lower()].setup()
             
#
# CIP_GetImageLogic
# This class makes all the operations not related with the user interface (download and handle volumes, etc.)
#
class CIP_GetImageLogic:
    def __init__(self, modulePath):
        """Constructor. Adapt the module full path to windows convention when necessary"""
        #ScriptedLoadableModuleLogic.__init__(self)
        self.modulePath = modulePath
    
    def loadCase(self, server, serverPath, studyId, caseId, imageTypesExtensions, labelMapExtensions, localStoragePath, cacheOn, sshMode, privateKeySSH):
        """Load all the asked images for a case: main images and label maps.
        Arguments:
        - server -- User and name of the host. Default: copd@mad-replicated1.research.partners.org
        - serverPath -- Root path for all the cases. Default: /mad/store-replicated/clients/copd/Processed
        - studyId -- Code of the study. Ex: COPDGene
        - caseId -- Case id (NOT patient! It will be extracted from here). Example: 12257B_INSP_STD_UIA_COPD
        - imageTypesExtensions -- Extensions of the images that must be appended before 'nrrd' in the filename. Default is blank
        - labelMapExtensions -- Extensions that must be appended to the file name to find the labelmap. Ex: _partialLungLabelMap
        - localStoragePath -- Local folder where all the images will be downloaded
        - cacheOn -- When True, the images are not downloaded if they already exist in local
        - privateKeySSH -- Full path to the file that contains the private key used to connect with SSH to the server     
        
        Returns OK or ERROR 
        """
        try:
            # Extract Patient Id         
            patientId = caseId.split('_')[0]
            
            
            for ext in imageTypesExtensions:
                locPath = self.downloadNrrdFile(server, serverPath, studyId, patientId, caseId, ext, localStoragePath, cacheOn, sshMode, privateKeySSH)             
                if (SlicerUtil.IsDevelopment): print "Loading volume stored in " + locPath
                slicer.util.loadVolume(locPath)            
            for ext in labelMapExtensions:
                locPath = self.downloadNrrdFile(server, serverPath, studyId, patientId, caseId, ext[1], localStoragePath, cacheOn, sshMode, privateKeySSH)             
                if (SlicerUtil.IsDevelopment): print "Loading label map stored in " + locPath
                (code, vtkLabelmapVolumeNode) = slicer.util.loadLabelVolume(locPath, {}, returnNode=True)     # Braces are needed for Windows compatibility... No comments...
            return Util.OK
        except Exception as exception:
            print exception
            return Util.ERROR
            
    def mustSplit(self, labelMapStructure):
        return labelMapStructure[3] is not None     
            
    def downloadNrrdFile(self, server, serverPath, studyId, patientId, caseId, ext, localStoragePath, cacheOn, sshMode=True, privateKeySSH=None):
        """Download Header and Raw data in a Nrrd file.
        Returns the full local path for the nhrd file (header)                 
        """        
        
        localFile = "{0}/{1}{2}.nhdr".format(localStoragePath, caseId, ext)        
        
        # If cache mode is not activated or the file does not exist locally, proceed to download
        if (not cacheOn or not os.path.isfile(localFile)):            
            error = False
            
            try:
                if os.path.isfile(localFile):
                    # Delete file previously to avoid confirmation messages
                    print "Remove cached files: " + localFile                    
                    try:                                
                        os.clear(localFile)
                        os.clear("{0}/{1}{2}.raw.gz".format(localStoragePath, caseId, ext))
                    except:
                        print "Error when deleting local files ({0})".format(localFile)
                
                # Make sure that the ssh key has not too many permissions if it is used (otherwise scp will return an error)
                if privateKeySSH:
                    os.chmod(privateKeySSH, 0600)
                
                # Download header
                if (os.sys.platform == "win32"): 
                    localStoragePath = localStoragePath.replace('/', '\\') + '\\'     
                    
                    if sshMode:
                        if privateKeySSH:
                            privateKeyCommand = "-privatekey={0}".format(privateKeySSH)
                        else:
                            privateKeyCommand = ""
                        params = [("%s\\CIP_GetImage_Resources\\WinSCP.com" % self.modulePath) ,"/command", 'open {0} {1}'.format(server, privateKeyCommand), \
                                    'get {0}/{1}/{2}/{3}/{3}{4}.nhdr {5}'.format(serverPath, studyId, patientId, caseId, ext, localStoragePath), "exit"]         
                    else:
                        params = ['copy',"{0}\\{1}\\{2}\\{3}\\{3}{4}.nhdr".format(serverPath, studyId, patientId, caseId, ext), localStoragePath]
                             
                else:
                    # Unix
                    if sshMode:                    
                        keyCommand = ("-i %s " % privateKeySSH) if privateKeySSH else ""     # Set a command if privateKeySsh has any value (non empty)                         
                        params = ['scp',"{0}{1}:{2}/{3}/{4}/{5}/{5}{6}.nhdr".format(keyCommand, server, serverPath, studyId, patientId, caseId, ext), localStoragePath]
                    else:
                        params = ['cp',"{0}/{1}/{2}/{3}/{3}{4}.nhdr".format(serverPath, studyId, patientId, caseId, ext), localStoragePath]
                    fullStrCommand = " ".join(params)
                
                (result, output, error) = self.executeDownloadCommand(params)            
                
                if (result == Util.ERROR):
                    print "Error when executing download command. Params:"
                    print params
                    if (error == None):
                        error = "Unnknown error"
                    raise Exception(error)                         
                
                # Download raw data (just update a parameter)
                if (os.sys.platform == "win32"):        
                    if sshMode: paramToModify = 3 
                    else: paramToModify = 1                                                            
                else:
                    # Unix
                    paramToModify = 1
                
                # Replace the name of the parameter
                params[paramToModify] = params[paramToModify].replace(".nhdr", ".raw.gz")    
                     
                # Dowload the raw data
                (result, output, error) = self.executeDownloadCommand(params)
                
                if (result == Util.ERROR):
                    print ("Error when executing download command. Params:")
                    print (params)
                    if (error == None):
                        error = "Unnknown error"
                    raise Exception(error)
                
                
                # If everything goes well, check the the path of the Nrrd file to verify that the file have been correctly downlaoded
                missingFiles = ""
                if not os.path.isfile(localFile):
                    missingFiles = missingFiles + localFile + ";"
                if not os.path.isfile(localFile.replace(".nhdr", ".raw.gz")):
                    missingFiles = missingFiles + localFile.replace(".nhdr", ".raw.gz") + ";"
                if missingFiles:
                    raise Exception("The download command did not return any error message, but the following files have not been downloaded: " + missingFiles)
             
            except Exception as ex:
                # There was en error in the preferred method. If we are in a Unix system, we will try the backup method
                if os.sys.platform != "win32":
                    print("There was an error when downloading some of the files: " + error)
                    print("Trying alternative method...")
                    self.executeDowloadCommand_Backup(fullStrCommand)                    
                 
                    # If everything goes well, check the the path of the Nrrd file to verify that the file have been correctly downlaoded
                    missingFiles = ""
                    if not os.path.isfile(localFile): missingFiles = missingFiles + localFile + ";"
                    if not os.path.isfile(localFile.replace(".nhdr", ".raw.gz")): missingFiles = missingFiles + localFile.replace(".nhdr", ".raw.gz") + ";"
                    if missingFiles:
                        raise Exception("After a second attempt, the following files have not been downloaded: " + missingFiles)
                     
                    print "Apparently it worked!"
                else:
                    raise ex
                    
        else:
            print "File {0} already cached".format(localFile)
         
        # Return path to the Nrrd header file
        return localFile
        
    def executeDownloadCommand(self, params):
        """Execute a command to download fisically the file. It will be different depending on the current platform.
        In Unix, we will use the "scp" command.
        In Windows, we will use WinSCP tool (attached to the module in "Resources" folder)
        It returns a tuple: OK/ERROR, StandardOutput, ErrorMessage"""        
        if SlicerUtil.IsDevelopment:
            print ("Attempt to download with these params:")
            print (params)
        try:
            out = err = None
            
            if (os.sys.platform == "win32"):
                # Hide console window
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                proc = subprocess.Popen(params, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo)         
                print ("Launch process")
                # Launch the process            
                (out, err)    = proc.communicate()
                print("End of process")
            else: 
                # Preferred method.
                proc = subprocess.Popen(params, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                # Launch the process            
                (out, err)    = proc.communicate()                
                
             
            if SlicerUtil.IsDevelopment:                
                print "Out: " + out
                print "Err:" + err
            if err:
                print "Error returned by system process: " + err
             
        except Exception as ex:            
            print "FATAL ERROR IN COPY PROCESS:"
            print ex
            # Fatal error
            return (Util.ERROR, out, err)
                        
        # In Unix sometimes if there is some error, stderr will contain some value            
        if err:            
            return (Util.ERROR, out, err)    # ERROR!
        
        ## Everything ok
        return (Util.OK, out, err)
             
    def executeDowloadCommand_Backup(self, command):
        """Backup function that will be used when the preferred method fails"""                    
        subprocess.check_call(command, shell=True)
        subprocess.check_call(command.replace(".nhdr", ".raw.gz"), shell=True)            
        
  