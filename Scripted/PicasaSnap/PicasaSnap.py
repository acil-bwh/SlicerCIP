from __main__ import vtk, qt, ctk, slicer
# import unittest
import os, sys

# Picasa API
import gdata.photos.service

# Add the CIP common library to the path if it has not been loaded yet
try:
    import CIP.logic
except Exception as ex:
    currentpath = os.path.dirname(os.path.realpath(__file__))
    # We assume that CIP_Common is in the development structure
    path = os.path.normpath(currentpath + '/../../../SlicerCIP/Scripted/CIP_Common')
    if not os.path.exists(path):
        # We assume that CIP is a subfolder (Slicer behaviour)
        path = os.path.normpath(currentpath + '/CIP')
    sys.path.append(path)
    print("The following path was manually added to the PythonPath in Picasa Snap: " + path)
    import CIP.logic

#from CIP.ui import AutoUpdateWidget

class PicasaSnap:
  """Module template for ACIL Slicer Modules"""
  def __init__(self, parent):
    """Constructor for main class"""
    self.parent = parent    
    # ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "Picasa Snap"
    self.parent.categories = ["Chest Imaging Platform.Modules"]
    self.parent.dependencies = []
    self.parent.contributors = ["Jorge Onieva", "Applied Chest Imaging Laboratory", "Brigham and Women's Hospital"] 
    self.parent.helpText = "Export your screenshots to Google Picasa"
    self.parent.acknowledgementText = SlicerUtil.ACIL_AcknowledgementText
   
#
# PicasaSnapWidget. User interface
#
class PicasaSnapWidget:
  # Constants (snapshots state)
  SNAPSHOT_NAME = 0
  SNAPSHOT_DESCRIPTION = 1
  SNAPSHOT_UPLOADED = 2
  SNAPSHOT_WIDGET = 3
  MODULE_NAME = "PicasaSnap"

  def __init__(self, parent=None):
    """Widget constructor (existing module)"""
    self.BASE_PATH = os.path.dirname(slicer.util.modulePath("PicasaSnap"))
    self.CIP_ICON_DIR = self.BASE_PATH + "/Resources/Icons"
        
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
    
    # We have to define here the callback functions in order that we can access the node info in the events.
    # More info: http://www.slicer.org/slicerWiki/index.php/Documentation/Nightly/Developers/FAQ/Python_Scripting#How_can_I_access_callData_argument_in_a_VTK_object_observer_callback_function
    from functools import partial
    def onNodeAdded(self, caller, eventId, callData):
      """Node added to the Slicer scene"""
      if callData.GetClassName() == 'vtkMRMLAnnotationSnapshotNode':  
        if SlicerUtil.IsDevelopment: print "New snapshot node added to scene: {0}".format(callData.GetName())
        self.__addNewSnapshot__(callData)
    
    def onNodeRemoved(self, caller, eventId, callData):
      """Node removed from the Slicer scene"""
      if callData.GetClassName() == 'vtkMRMLAnnotationSnapshotNode':      
        if SlicerUtil.IsDevelopment: print "Snapshot node {0} removed".format(callData.GetName())
        self.__removeSnapshot__(callData)
    
    self.onNodeAdded = partial(onNodeAdded, self)
    self.onNodeAdded.CallDataType = vtk.VTK_OBJECT
    
    self.onNodeRemoved = partial(onNodeRemoved, self)
    self.onNodeRemoved.CallDataType = vtk.VTK_OBJECT
  
  def setup(self):
    """Init the widget """
    # ScriptedLoadableModuleWidget.setup(self)
         
    settings = qt.QSettings()

    if (SlicerUtil.IsDevelopment):
      # reload button      
      self.reloadButton = qt.QPushButton("Reload")
      self.reloadButton.toolTip = "Reload this module."
      self.reloadButton.name = "Reload"
      self.layout.addWidget(self.reloadButton)      
      self.reloadButton.connect('clicked()', self.onBtnReloadClicked)  
    
    self.logic = PicasaSnapLogic()    
    self.__addObservers__()
   
    ######## Credentials
    self.credentialsCollapsibleButton = ctk.ctkCollapsibleButton()
    self.credentialsCollapsibleButton.text = "Credentials"
    self.layout.addWidget(self.credentialsCollapsibleButton)    
    self.credentialsLayout = qt.QFormLayout(self.credentialsCollapsibleButton)
    
    self.isUserLogged = False
    
    self.loginLineEdit = qt.QLineEdit()
    self.credentialsLayout.addRow("Login:   ", self.loginLineEdit)
    self.passwordLineEdit = qt.QLineEdit()
    self.passwordLineEdit.setEchoMode(qt.QLineEdit.Password)
    self.credentialsLayout.addRow("Password:   ", self.passwordLineEdit)    
    
    self.rememberCredentialsCheckBox = qt.QCheckBox()
    self.rememberCredentialsCheckBox.checked = True
    self.rememberCredentialsCheckBox.setText("Remember my credentials")
    self.rememberCredentialsCheckBox.toolTip = "Check for an automatic login when the application starts"
    self.loginButton = qt.QPushButton("Login")        
    self.loginButton.toolTip = "Login in Picassa service (Google credentials)"    
    self.logoutButton = qt.QPushButton("Logout")        
    self.logoutButton.toolTip = "Logout to connect with another user's credentials"   
    # Add all the items, they will be shown/hidden in refreshCredentialsUI function
    self.credentialsLayout.addRow(self.rememberCredentialsCheckBox, self.loginButton)
    self.credentialsLayout.addRow(None, self.logoutButton)   
    
    ######## Snapshots (main frame)
    self.mainCollapsibleButton = ctk.ctkCollapsibleButton()
    self.mainCollapsibleButton.text = "Snapshots"
    self.layout.addWidget(self.mainCollapsibleButton)    
    self.mainLayout = qt.QVBoxLayout(self.mainCollapsibleButton)
         
    ############### Current snapshots
    self.currentSnapshotsFrame = qt.QFrame()
    self.currentSnapshotsLayout = qt.QVBoxLayout()
    self.currentSnapshotsFrame.setLayout(self.currentSnapshotsLayout)
    self.currentSnapshotsFrame.setFrameShape(qt.QFrame.StyledPanel)
    self.mainLayout.addWidget(self.currentSnapshotsFrame)
      
    self.snapshotsLabel = qt.QLabel("Snapshots to upload:")
    self.snapshotsLabel.setStyleSheet("font-weight:bold; font-size:14px; margin-bottom:10px")
    self.currentSnapshotsLayout.addWidget(self.snapshotsLabel)
    
    # Subframe that contains the checkbox list
    self.currentSnapshotsInnerFrame = qt.QFrame()
    self.currentSnapshotsInnerLayout = qt.QVBoxLayout()
    self.currentSnapshotsInnerFrame.setLayout(self.currentSnapshotsInnerLayout)
    self.currentSnapshotsLayout.addWidget(self.currentSnapshotsInnerFrame)
    
    
    self.noItemsLabel = qt.QLabel("(There are not any snapshots at the moment)")
    # Add the label by default. It will be hidden if there is any snapshot
    self.currentSnapshotsInnerLayout.addWidget(self.noItemsLabel)
    
    self.loadExistingSnapshotsFirstLoad()
    
    ############### Albums
    # Try to login before getting the albums
    self.login()
    
    msgBox = None
    if self.isUserLogged:
      # Show message box while loading the data
      msgBox = qt.QMessageBox(qt.QMessageBox.Information, 'Login','Connecting with Picasa. Please wait...', qt.QMessageBox.Cancel)
      msgBox.show()
    
    try:
      self.albumNameFrame = qt.QFrame()
      self.albumNameLayout = qt.QHBoxLayout()
      self.albumNameFrame.setLayout(self.albumNameLayout)
      self.albumNameFrame.setFrameShape(qt.QFrame.StyledPanel)    
      
      self.albumNameLabel = qt.QLabel("Album name:")    
      self.albumNameLabel.setStyleSheet("font-weight:bold;")
      self.albumNamesComboBox = qt.QComboBox()
      self.loadAlbums()
      self.albumNameLayout.addWidget(self.albumNameLabel)
      self.albumNameLayout.addWidget(self.albumNamesComboBox)
      self.mainLayout.addWidget(self.albumNameFrame)
      
      ############### Tags
      self.tagsFrame = qt.QFrame()
      self.tagsLayout = qt.QGridLayout()
      self.tagsFrame.setLayout(self.tagsLayout)
      self.tagsFrame.setFrameShape(qt.QFrame.StyledPanel)
       
      self.tagsLabel = qt.QLabel("Tags (select all that apply, you can filter o create new tags):")
      self.tagsLabel.setStyleSheet("font-weight: bold; margin-bottom: 10px; margin-top: 5px")
      self.tagsLayout.addWidget(self.tagsLabel, 0, 0, 1, 3)
      
      # Add input to filter tags and button to add a new one
      self.tagsFilterLineEdit = qt.QLineEdit()
      self.tagsFilterLineEdit.toolTip = "Type here to filter your tags. If you press the return key all the visible tags will be checked"
      #self.tagsFilterLineEdit.setStyleSheet(style)
      self.tagsLayout.addWidget(self.tagsFilterLineEdit, 1, 0, 1, 2)
      self.newTagButton = qt.QPushButton("New tag")
      #self.newTagButton.setStyleSheet("background-color: #5D74C6; color:white")
      self.newTagButton.setIconSize(qt.QSize(20,20))
      self.newTagButton.setIcon(qt.QIcon(self.CIP_ICON_DIR + "/Plus - 48.png"))
      self.newTagButton.setFixedWidth(75)
      self.newTagButton.toolTip = "Add a new tag (the tag will not be created until you upload any picture with it)"
      self.tagsLayout.addWidget(self.newTagButton, 1, 2)
        
      self.loadTags()
      
      ############### Upload snapshots controls    
      self.uploadSnapsButtonFrame = qt.QFrame()
      self.uploadSnapsLayout = qt.QHBoxLayout()
      self.uploadSnapsButtonFrame.setLayout(self.uploadSnapsLayout)
      #self(qt.QFrame.HLine)
      self.mainLayout.addWidget(self.uploadSnapsButtonFrame)
      
      self.uploadSnapshotsButton = qt.QPushButton()
      self.uploadSnapshotsButton.text = "Upload to Picasa!"        
      self.uploadSnapshotsButton.toolTip = "Upload selected screenshots to Picassa"      
      self.uploadSnapshotsButton.setStyleSheet("background-color: #5D74C6; color: white; font-weight: bold; font-size:14px")
      self.uploadSnapshotsButton.setIcon(qt.QIcon(self.CIP_ICON_DIR + "/Upload - 64.png"))
      self.uploadSnapshotsButton.setIconSize(qt.QSize(24,24))   
      self.uploadSnapshotsButton.setFixedSize(170, 35)
      self.uploadSnapsLayout.addWidget(self.uploadSnapshotsButton)
      
      ############### Progress bar     
      self.progressBar = qt.QProgressDialog()
      self.progressBar.setMinimum(0)
      self.progressBar.setMinimumDuration(0)
      self.progressBar.setWindowModality(True)

      # Check for updates in CIP
      #autoUpdate = SlicerUtil.settingGetOrSetDefault("PicasaSnap", "AutoUpdate", 1)
      #uw = AutoUpdateWidget(parent=self.parent, autoUpdate=autoUpdate)
      #uw.addAutoUpdateCheckObserver(self.onAutoUpdateStateChanged)

#     self.uploadProgressFrame = qt.QFrame()
#     self.uploadProgressLayout = qt.QVBoxLayout()
#     self.uploadProgressFrame.setLayout(self.uploadProgressLayout)
#        
#     # Gif image   
#     self.imUploading = qt.QMovie("%s/loading.gif" % self.CIP_ICON_DIR, qt.QByteArray())
#     # Label to contain the gif
#     self.lblImLoading = qt.QLabel()
#     # Fix the dimensions of the image (by fixing the dimensions of the label that contains it)
#     self.lblImLoading.setFixedWidth(40)
#     # Other image parameters
#     self.imUploading.setCacheMode(qt.QMovie.CacheAll)
#     self.imUploading.setSpeed(100)
#     # Assign the label to the image (don't start it yet, it will be started when we are uploading)
#     self.lblImLoading.setMovie(self.imUploading)
#     #self.imUploading.start()
#     self.uploadProgressLayout.addWidget(self.lblImLoading)
#     
#     # Label that will show the progress
#     self.lblUploading = qt.QLabel("Uploading %i/%i images...")
#     self.uploadProgressLayout.addWidget(self.lblUploading)
#  
    # Cancel uploading button
#     self.btnCancelUpload = qt.QPushButton("Cancel")        
#     self.btnCancelUpload.toolTip = "Cancel the process"
#     self.btnCancelUpload.setFixedWidth(100)
#     self.uploadProgressLayout.addWidget(self.btnCancelUpload)    
#     self.mainLayout.addWidget(self.uploadProgressFrame)
#      
#     # Hide the progress frame
#     self.uploadProgressFrame.hide() 
     
      ######## Connections
      self.uploadSnapshotsButton.connect('clicked (bool)', self.onUploadSnapshotsButtonClicked)
      self.loginButton.connect('clicked (bool)', self.onLoginButtonClicked)
      self.logoutButton.connect('clicked (bool)', self.onLogoutButtonClicked)
      self.loginLineEdit.returnPressed.connect(self.onLoginPasswordReturnKeyPressed)
      self.passwordLineEdit.returnPressed.connect(self.onLoginPasswordReturnKeyPressed)
      self.albumNamesComboBox.connect("currentIndexChanged (int)", self.onAlbumsCurrentIndexChanged)
      self.newTagButton.connect('clicked (bool)', self.onNewTagButtonClicked)
      self.tagsFilterLineEdit.connect('textEdited (QString)', self.onFilterTagsEdited)
      self.tagsFilterLineEdit.returnPressed.connect(self.onFilterTagsReturnKeyPressed)
      
      # Add vertical spacer
      self.layout.addStretch(1)   
    finally:         
      # Hide MesageBox if it was visible
      if msgBox:
        msgBox.close()
    
  
  def __addNewSnapshot__(self, snapshotNode):
    """Add a new snapshot node. It adds an entry in self.snapshotsCached and creates a new Checkbox object"""
    nodeID = snapshotNode.GetID()
    print "Added new node " + nodeID
    
    name = snapshotNode.GetName()
    description = snapshotNode.GetSnapshotDescription()
    ckb = qt.QCheckBox()
    ckb.checked = True    
    ckb.text = name    
    ckb.toolTip = "%s. Uploaded to Picasa: NO" % description
    # Add the checkbox to the layout
    self.currentSnapshotsInnerLayout.addWidget(ckb)
    # Add a new snapshot node to the cached collection (Name, Description, Uploaded, Widget)    
    self.snapshotsCached[nodeID] = [name, description, False, ckb]  
    
    # Add an observer in case the node is modified (example: renamed)
    self.__addModifiedObserver__(snapshotNode)
    
    # Remove no items label if visible
    self.noItemsLabel.hide()
    
  def __removeSnapshot__(self, snapshotNode):
    """Remove an existing snapshot node. It removes the entry from self.snapshotsCached and removes the checkbox"""
    # Hide checkbox
    self.snapshotsCached[snapshotNode.GetID()][self.SNAPSHOT_WIDGET].deleteLater()
    # Remove element from cache
    del self.snapshotsCached[snapshotNode.GetID()]
    # Show no items label if collection is empty
    if len(self.snapshotsCached) == 0:
      self.noItemsLabel.show()
    
  def login(self, login=None, password=None):
    """Login in Picasa. If no credentials are passed, the system will try to recover login/password previously saved in settings"""
    # Search for previously stored settings if values are not passed
    if not login: login = slicer.app.settings().value("%s/login" % self.MODULE_NAME)
    if not password: password = slicer.app.settings().value("%s/password" % self.MODULE_NAME)
    
    if (login and password):           
      self.loginLineEdit.text = login
      self.passwordLineEdit.text = password
      
      # Open info window      
      self.isUserLogged = self.logic.picasaLogin(self.loginLineEdit.text, self.passwordLineEdit.text)  
      
      if self.rememberCredentialsCheckBox.checked:
        # Remember credentials for next login
        slicer.app.settings().setValue("%s/login" % self.MODULE_NAME, login)
        slicer.app.settings().setValue("%s/password" % self.MODULE_NAME, password)
    else:
      self.isUserLogged = False
    
    self.refreshCredentialsUI()

  def logout(self):
    """Logout the current logged user. It removes stored settings"""
    slicer.app.settings().remove("%s/login" % self.MODULE_NAME)
    slicer.app.settings().remove("%s/password" % self.MODULE_NAME)
    slicer.app.settings().remove("%s/lastAlbum" % self.MODULE_NAME)
    
    self.loginLineEdit.text = self.passwordLineEdit.text = ""
    self.isUserLogged = False
    self.logic.picasaLogout()
    self.refreshCredentialsUI()
    
    
  def loadExistingSnapshotsFirstLoad(self):
    """Loads all the existing snapshot nodes currently present in the scene.
    It initializes the object self.snapshotsCached that will store the state for all the snapshots.
    It also creates the Reload snapshots button"""  
    self.snapshotsCached = dict()         
    # Get the nodes of type Snapshot   
    snapshotNodes = slicer.mrmlScene.GetNodesByClass('vtkMRMLAnnotationSnapshotNode')
    
    snapshotNodes.InitTraversal()
    snapshotNode = snapshotNodes.GetNextItemAsObject() 
    if not snapshotNode:
      # There is not any snapshot
      self.noItemsLabel.show()    
    else:
      # Add all the nodes
      self.noItemsLabel.hide()     
      while snapshotNode:
        self.__addNewSnapshot__(snapshotNode)
        snapshotNode = snapshotNodes.GetNextItemAsObject() 
          
    # Reload button
    self.btnReloadSnaps = qt.QPushButton("Reload snapshots")
    self.btnReloadSnaps.toolTip = ("Reload all the current snapshots and set them to the initial state (equivalent to the first load of the module)."  
                                  "\nThis is useful if you want to re-upload any snapshots")
    self.btnReloadSnaps.setIcon(qt.QIcon(self.CIP_ICON_DIR + "/Reload - 16.png"))
    self.btnReloadSnaps.setStyleSheet("margin-top: 15px")
    self.btnReloadSnaps.setFixedSize(150,40)
    
    self.currentSnapshotsLayout.addWidget(self.btnReloadSnaps)
    
    self.btnReloadSnaps.connect('clicked (bool)', self.onbtnReloadSnapsClicked)
  
  def loadAlbums(self):
    """Load all the Picasa albums and load them in the albums combo box.
    If there is any default albumId cached in settings, select that one by default"""    
    self.albumNamesComboBox.clear()
    
    if self.isUserLogged:      
      # Search for cached album Id
      albumId = slicer.app.settings().value("%s/lastAlbum" % self.MODULE_NAME)
      
      self.albums = self.logic.picasaGetAlbums()      
      for i in range(len(self.albums)):
        self.albumNamesComboBox.addItem(self.albums[i][1])              # Display the album name
        self.albumNamesComboBox.setItemData(i, self.albums[i][0])       # Store the Album Id in item data
        if self.albums[i][0] == albumId:
          # The album was previously cached. This will be the selected album by default
          self.albumNamesComboBox.currentIndex = i 
    else:
      self.albums = []
      self.albumNamesComboBox.addItem("Please login to get your Picasa albums")
  
  
  def loadTags(self):
    """Get the list of tags for this user in Picasa and create a button for each one of them"""
    if (self.isUserLogged):      
      self.tags = self.logic.picasaGetTags()
      self.btnTags = []   
      for pos in range(len(self.tags)):
        self.addTagButton(pos)
      self.tagsFrame.visible = True        
    else:
      self.tagsFrame.visible = False
      
    self.mainLayout.addWidget(self.tagsFrame)
    
  def filterTags(self, text):
    """Hide the tag buttons that do not contain the text received (ignoring lowercase). 
    If 'text' is blank, show all the tagbuttons"""
    if text == '':
      for btn in self.btnTags: btn.show()
    else:
      for btn in self.btnTags:
        btn.visible = (text.lower() in btn.text.lower())  
  
  def addTagButton(self, pos):
    """Add a new tag button to the current list"""
    btn = qt.QPushButton()
    btn.setCheckable(True)
    btn.text = self.tags[pos]
    btn.toolTip = self.tags[pos]
    btn.setStyleSheet("background-color: #2A83A4; color: white")
    self.tagsLayout.addWidget(btn, int(pos / 3) + 3, pos % 3)
    self.btnTags.append(btn)
    
  
  
  def uploadSnapshots(self):
    """Upload the checked snapshots to Picasa (avoiding upload the ones already uploaded).
    Remember that """   
    # Store the albums that must be uploaded    
    ids = []    
     
    # Add to the list of uploads just the ones that are visible, checked and not have been already uploaded
    for key,value in self.snapshotsCached.iteritems():
      cb = value[self.SNAPSHOT_WIDGET]
      if cb.visible and cb.checked and not value[self.SNAPSHOT_UPLOADED]:    
        ids.append(key)

    self.imagesToUploadCount = len(ids)    
    
    if self.imagesToUploadCount == 0:
      # No albums to upload. Display information message
      qt.QMessageBox.warning(slicer.util.mainWindow(), 'Warning', 'There are not any new snapshopts to upload to Picasa at this moment')      
    else:
      self.imagesUploadedCount = 0
      
      # Get the selected album id
      albumId = self.albumNamesComboBox.itemData(self.albumNamesComboBox.currentIndex)
     
      # Get the selected tags (pressed buttons)
      tags = [b.text for b in filter(lambda btn: btn.checked, self.btnTags)]
                  
      self.progressBar.setMaximum(self.imagesToUploadCount)
      self.progressBar.setValue(0)        
          
      self.progressBar.show()     
          
     
      # Upload
      #self.logic.picasaUploadPictures(ids, albumId, tags, self.onImageUploaded)
      for snapshotNodeId in ids:     
        self.progressBar.labelText = "Uploading %i / %i images..." % (self.imagesUploadedCount + 1, self.imagesToUploadCount)   
        slicer.app.processEvents()
        self.logic.picasaUploadPicture(snapshotNodeId, self.snapshotsCached[snapshotNodeId][self.SNAPSHOT_NAME], self.snapshotsCached[snapshotNodeId][self.SNAPSHOT_DESCRIPTION], albumId, tags)
        self.imagesUploadedCount += 1
        
        # Update the state of the new uploaded snap
        self.snapshotsCached[snapshotNodeId][self.SNAPSHOT_UPLOADED] = True
        self.snapshotsCached[snapshotNodeId][self.SNAPSHOT_WIDGET].toolTip = "%s. Uploaded to Picasa: YES" % self.snapshotsCached[snapshotNodeId][self.SNAPSHOT_DESCRIPTION]
        self.snapshotsCached[snapshotNodeId][self.SNAPSHOT_WIDGET].checked = True
        self.snapshotsCached[snapshotNodeId][self.SNAPSHOT_WIDGET].enabled = False
        slicer.app.processEvents()
        if self.progressBar.wasCanceled:
          # The process was cancelled by the user
          qt.QMessageBox.warning(slicer.util.mainWindow(), 'Warning', 'The process was cancelled, but %i images were uploaded' % self.imagesUploadedCount)
          return 
        
        self.progressBar.setValue(self.imagesUploadedCount)
        #self.progressBar.setFormat("Uploading %i / %i images..." % (self.imagesUploadedCount + 1, self.imagesToUploadCount))
        #self.progressBar.labelText = "Uploading %i / %i images..." % (self.imagesUploadedCount + 1, self.imagesToUploadCount)
        #slicer.app.processEvents()
                
      # Inform the user
      self.msgBox = qt.QMessageBox(qt.QMessageBox.Information, 'Images uploaded', '%i images were uploaded succesfully' % self.imagesUploadedCount)  
      self.msgBox.setModal(True)
      self.msgBox.show()      
    
      
  def refreshCredentialsUI(self):
    """Show/hide login and logout controls depending on the user is logged in or not"""   
    self.credentialsCollapsibleButton.collapsed = self.isUserLogged
    self.mainCollapsibleButton.collapsed = not self.isUserLogged            
    self.rememberCredentialsCheckBox.visible = self.loginButton.visible = not self.isUserLogged
    self.logoutButton.visible = not self.isUserLogged
    self.logoutButton.visible = self.isUserLogged      
    self.loginLineEdit.readOnly = self.passwordLineEdit.readOnly = self.isUserLogged
   
  
  def refreshUI(self):  
    """Refresh all the user interface""" 
    self.refreshCredentialsUI()
    self.loadAlbums()
    self.loadTags()
  
  def cleanup(self):
    self.__removeObservers__()

  def __addObservers__(self):
    """Add all the node observers to the scene (node added and node removed).
    It also initializes the list of observers that will listen to the snapshot nodes modifications"""
    self.__sceneObservers__ = []
    self.__sceneObservers__.append(slicer.mrmlScene.AddObserver(slicer.vtkMRMLScene.NodeAddedEvent, self.onNodeAdded))
    self.__sceneObservers__.append(slicer.mrmlScene.AddObserver(slicer.vtkMRMLScene.NodeRemovedEvent, self.onNodeRemoved))
    
    # Observers for the individual nodes (for example in case of renaming)
    # It will contain a list of tuples (Node, Observer)
    self.__individualNodeObservers__ = []
  
  def __addModifiedObserver__(self, node):
    """Add an observer for a modified node (in case that a snapshot node is modified)"""
    self.__individualNodeObservers__.append((node, node.AddObserver(vtk.vtkCommand.ModifiedEvent, self.onSnapshotNodeModified)))
    
  def __removeObservers__(self):
    """Remove all the observers of the widget"""
    for ob in self.__sceneObservers__:
      slicer.mrmlScene.RemoveObserver(ob)
    
    for ob in self.__individualNodeObservers__:
      ob[0].RemoveObserver(ob[1])



  ##################################
  ## EVENTS HANDLING
  ##################################
  def onSnapshotNodeModified(self, node, event):    
    nodeID = node.GetID()
    print ("Node %s modified" % nodeID)
    print(event)
    name = node.GetName()
    description = node.GetSnapshotDescription()
    self.snapshotsCached[nodeID][self.SNAPSHOT_NAME] = name
    self.snapshotsCached[nodeID][self.SNAPSHOT_DESCRIPTION] = description
    
    # Refresh the checkbox
    ckb = self.snapshotsCached[nodeID][self.SNAPSHOT_WIDGET]
    ckb.text = name
    ckb.toolTip = "%s. Uploaded to Picasa: %s" % (description, "YES" if self.snapshotsCached[nodeID][self.SNAPSHOT_UPLOADED] else "NO")
    
  
  def onLoginButtonClicked(self):    
    self.login(self.loginLineEdit.text, self.passwordLineEdit.text)    
    self.refreshUI()
    
  def onLoginPasswordReturnKeyPressed(self):
    # If the user is logged we don't have to do anything (the fields are in readonly mode but still the user can press enter)
    if not self.isUserLogged:      
      self.login(self.loginLineEdit.text, self.passwordLineEdit.text)    
      self.refreshUI()
  
  def onLogoutButtonClicked(self):    
    self.logout()
    self.refreshUI()    
  
  def onbtnReloadSnapsClicked(self):
    # Clean all the current snapshots
    for item in self.snapshotsCached.itervalues():
      item[self.SNAPSHOT_WIDGET].deleteLater()
    # Remove the Refresh button
    self.btnReloadSnaps.deleteLater()
    
    
    # Load all the snapshots as in a first load (all the images could be uploaded again)
    self.loadExistingSnapshotsFirstLoad()
    
    
  def onUploadSnapshotsButtonClicked(self):
    if self.isUserLogged:
      self.uploadSnapshots()
    else: 
      qt.QMessageBox.warning(slicer.util.mainWindow(), 'Warning', 'You must be logged in to Picasa to upload your snapshots (please review "Credentials" section in this module)')
    
  
  def onAlbumsCurrentIndexChanged(self, index):
    """Triggered when the selected item in albums combobox is changed.
     Store in cache the selected album for the next time the user is logged"""
    albumId = self.albumNamesComboBox.itemData(index)
    slicer.app.settings().setValue("%s/lastAlbum" % self.MODULE_NAME, albumId)
  
  def onImageUploaded(self):
    """Callback that will be invoked every time a file is uploaded to Picasa"""
    self.imagesUploadedCount += 1
    self.lblImLoading.text = "Uploading %i / %i images..." % (self.imagesUploadedCount + 1, self.imagesToUploadCount)
    slicer.app.processEvents()
  
  def onFilterTagsEdited(self, text):
    self.filterTags(text)
  
  def onFilterTagsReturnKeyPressed(self):  
    for btn in self.btnTags:
      btn.checked = btn.visible
  
  def onNewTagButtonClicked(self):
    # Open a new Dialog window to get the name of the new tag
    text = qt.QInputDialog.getText(slicer.util.mainWindow(), "Add new tag to Picasa", "\nPlease introduce the name of the new tag.\n\nRecall that the new tag will not be created in Picasa until a snapshot with this tag is uploaded.\n")
    if text != '':
      # Add the new tag to the list of tags
      self.tags.append(text)
      # Create a new tag button in the last position
      self.addTagButton(len(self.tags) - 1)

  def onAutoUpdateStateChanged(self, isAutoUpdate):
    SlicerUtil.setSetting(self.MODULE_NAME, "AutoUpdate", isAutoUpdate)

  def onBtnReloadClicked(self):
    """Reload the module. Just for development purposes."""
    slicer.util.reloadScriptedModule(self.MODULE_NAME)




##############################################################################################################
#
# ACIL_BlankLogic
# This class makes all the operations not related with the user interface (download and handle volumes, etc.)
##############################################################################################################
class PicasaSnapLogic:
  def __init__(self):
    """Constructor. """
    self.gd_client = None   # Object that will store the credentials of the user and will make all the Picasa ops
    self.isUserLogged = False
    self.__createTempFolder__()
    # ScriptedLoadableModuleLogic.__init__(self)  
  
  def __createTempFolder__(self):
    """Create a temp folder to store the images if it does not exist"""
    self.localStoragePath = "{0}/ExportPicasa".format(slicer.app.temporaryPath)
    if not os.path.exists(self.localStoragePath):      
      os.makedirs(self.localStoragePath)
      # Make sure that everybody has write permissions (sometimes there are problems because of umask)
      os.chmod(self.localStoragePath, 0777)
  
  def picasaLogin(self, email, password):
    """Login to Picasa with Gmail credentials (login + password)"""
    try:
      self.gd_client = gdata.photos.service.PhotosService()
      self.gd_client.email = email
      self.gd_client.password = password
      self.gd_client.source = 'Slicer-PicasaSnap'
      self.gd_client.ProgrammaticLogin()
      self.isUserLogged = True
      if SlicerUtil.IsDevelopment:
        print("User {0} logged succesfully".format(email))      
    except Exception as ex:
      print(ex)
      self.isUserLogged = False
    
    return self.isUserLogged
  
  def picasaLogout(self):
    """Invalidate Picasa credentials"""
    self.gd_client = None
    self.isUserLogged = False
  
  def checkLogin(self):
    """Check that the user is logged and raise an exception otherwise"""
    if not self.isUserLogged:
      raise Exception("User not logged. You must authenticate through the 'picasaLogin' method") 

  def picasaGetAlbums(self):
    """Load all the Picasa albums for the logged user.
    It returns a list of tuples (Id, Name)"""
    self.checkLogin() 
    
    result = []
    albums = self.gd_client.GetUserFeed()      

    for album in albums.entry:
      albumId = album.gphoto_id.text
      albumName = album.title.text
      result.append((albumId,albumName))
    
    return result
       
#         print 'title: %s, number of photos: %s, id: %s' % (album.title.text,
#             album.numphotos.text, album.gphoto_id.text)
   
  
  def picasaGetTags(self):
    """Load all the Picasa tags for the logged user (sorted by name)"""
    self.checkLogin()
    
    tagsFeed = self.gd_client.GetFeed('/data/feed/api/user/default?kind=tag')
    tags = []
    for tag in tagsFeed.entry:
      tags.append(tag.title.text)      
    
    # Sort alphabetically
    tags.sort()
    return tags
  
#   def picasaUploadPictures(self, snapshotNodeIds, albumId, tags=[], callback=None):
#     """Upload a list of snapshot nodes Ids to the specified album, with a list of tags."""
#     self.checkLogin()
#    
#     if (SlicerUtil.IsDevelopment):
#       print ("Uploading images to Picasa")
#       print ("Ids:")
#       print (snapshotNodeIds)      
#       print ("Album: %s" % albumId)
#       print ("Tags:")
#       print (tags)    
#        
#     # Init required objects
#     pngWriter = vtk.vtkPNGWriter()
#     uploadedPictures = []
#         
#     for snapshotNodeId in snapshotNodeIds:
#       #print ("Analyzing node %s" % snapshotNodeId)
#       snapshotNode = slicer.mrmlScene.GetNodeByID(snapshotNodeId)
#       snapShotImage = snapshotNode.GetScreenShot()
#       snapShotDescription = snapshotNode.GetSnapshotDescription()     
#       pngWriter.SetInputData(snapShotImage)
#       fileName = snapshotNode.GetName()
#       filePath = "{0}/{1}.png".format(self.localStoragePath, fileName)
#       pngWriter.SetFileName(filePath)
#       pngWriter.Write()
#       #print("Image {0} saved".format(fileName))
#       self.picasaUploadPicture(albumId, filePath, snapShotDescription, callback)
#       uploadedPictures.append(snapshotNodeId)
#   
#     return uploadedPictures
#       
#   def picasaUploadPicture(self, albumId, filePath, description, callback):
#     """Upload a file to picasa server"""
#     self.checkLogin()
#     
#     albumUrl = '/data/feed/api/user/default/albumid/' + albumId
#     
#     self.gd_client.InsertPhotoSimple(albumUrl,
#       os.path.basename(filePath),
#       description,
#       filePath,
#       content_type='image/png',
#       keywords=['slicer', 'lungs'])  
#     
#     if SlicerUtil.IsDevelopment: print ('{0} uploaded!'.format(os.path.basename(filePath)))
#     
#     if callback:
#       # Invoke the callbak if present (for example to inform the user about the progress)
#       callback()
#     # print(photo)
  def picasaUploadPicture(self, snapshotNodeId, snapshotName, snapshotDescription, albumId, tags=[]):
    """Upload a snapshot node to the specified album, with a list of tags."""
    self.checkLogin()
   
    if (SlicerUtil.IsDevelopment):
      print ("Uploading image to Picasa")
      print ("Id: %s" % snapshotNodeId)
      print ("Name: %s" % snapshotName)
      print ("Description: %s" % snapshotDescription)
      print ("Album: %s" % albumId)
      print ("Tags:")
      print (tags)    
       
#     time.sleep(3)
#     return
   
    snapshotNode = slicer.mrmlScene.GetNodeByID(snapshotNodeId)
    
    # Save the image to a temp file
    pngWriter = vtk.vtkPNGWriter()  
    snapShotImage = snapshotNode.GetScreenShot()
    pngWriter.SetInputData(snapShotImage)
    filePath = "{0}/{1}.png".format(self.localStoragePath, snapshotName)
    pngWriter.SetFileName(filePath)
    pngWriter.Write()
    
    albumUrl = '/data/feed/api/user/default/albumid/' + albumId
    
    # Upload to Picasa
    self.gd_client.InsertPhotoSimple(albumUrl,
      snapshotName,
      snapshotDescription,
      filePath,
      content_type='image/png',
      keywords=tags)  
 