'''
Widget that allows CIP modules to update automatically when any of the modules is loaded or when the user
clicks in a button.
Every module can have its own "Autoupdate at startup" setting, but all the CIP modules will be updated
at the same time to keep source code consistency (Git update).


Created on February 2015.

@author: Jorge Onieva (ACIL, Brigham and Women's Hospital)
'''

import os
from git import Repo
import shutil
from distutils import dir_util

from __main__ import qt, slicer, ctk

from ..logic import Util, SlicerUtil

class AutoUpdateWidget(object):
  def __init__(self, parent = None, autoUpdate=1):
    """ Widget constructor
    :param parent: parent widget where this one will be embedded
    :param autoUpdate: auto update at startup
    """
    if not parent:
      self.parent = slicer.qMRMLWidget()
      self.parent.setLayout(qt.QVBoxLayout())
      self.parent.setMRMLScene(slicer.mrmlScene)
    else:
      self.parent = parent
    self.layout = self.parent.layout()

    # Default values
    self.autoUpdate = int(autoUpdate)
    self.updateFolder = SlicerUtil.CIP_DEFAULT_GIT_REPO_FOLDER
    self.lastCommit = SlicerUtil.settingGetOrSetDefault("CIP", "lastCommit")

    self.autoUpdateCheckObserver = None
    self.forceUpdate = False

    if self.autoUpdate:
      self.update()
    self.__createGUI__()

  def __createGUI__(self):
    """Add the GUI components"""
    self.autoupdateCollapsibleButton = ctk.ctkCollapsibleButton()
    self.autoupdateCollapsibleButton.text = "Auto update"
    self.autoupdateCollapsibleButton.collapsed = True
    self.layout.addWidget(self.autoupdateCollapsibleButton)

    #self.mainLayout = qt.QHBoxLayout(self.autoupdateCollapsibleButton)
    self.mainLayout = qt.QFormLayout(self.autoupdateCollapsibleButton)


    self.checkAutoUpdate = qt.QCheckBox()
    self.checkAutoUpdate.checked = self.autoUpdate
    self.checkAutoUpdate.text = "Auto update CIP at startup"

    self.checkForceUpdate = qt.QCheckBox()
    self.checkForceUpdate.checked = False
    self.checkForceUpdate.text = "Force update"
    self.mainLayout.addRow(self.checkAutoUpdate, self.checkForceUpdate)

    self.btnUpdate = ctk.ctkPushButton()
    self.btnUpdate.text = "Update CIP now"
    self.mainLayout.addWidget(self.btnUpdate)

    self.btnUpdate.connect('clicked()', self.onbtnUpdateClicked)
    self.checkAutoUpdate.connect('stateChanged(int)', self.onCheckAutoUpdateClicked)

  def update(self):
    """
    Launch the update process
    """
    try:
        if os.path.exists(self.updateFolder):
          # Remove folder if it already exists (use shutil because the directory is not empty)
          shutil.rmtree(self.updateFolder)
    
        os.makedirs(self.updateFolder)
        os.chmod(self.updateFolder, 0o777)
    
        repo = Repo.clone_from(SlicerUtil.CIP_GIT_REMOTE_URL, self.updateFolder)
        currentCommit = repo.head.commit.hexsha
        if self.lastCommit != currentCommit or self.forceUpdate:
          for folder in (d for d in os.listdir(self.updateFolder) if not d.startswith('.')):
            src = os.path.join(self.updateFolder,folder)
            dst = os.path.realpath(os.path.join(Util.CIP_MODULE_ROOT_DIR, '..', folder))
            #print("Copy %s in %s" % (src,dst))
            dir_util.copy_tree(src, dst)
    
          print(("CIP updated! Last commit: %s" % currentCommit))
          SlicerUtil.setSetting("CIP", "lastCommit", currentCommit)
    
          # Show informative message
          qt.QMessageBox.information(slicer.util.mainWindow(), 'CIP updated', "CIP modules have been updated. The changes will be effective when you restart Slicer.")
    
          return True
        # No changes
        else:
          print("No changes in CIP")
          return False
    except Exception as ex:
        print("Error when trying to update the modules")
        print(ex)
        return False

  def onbtnUpdateClicked(self):
    self.forceUpdate = self.checkForceUpdate.isChecked()
    self.update()

  def onCheckAutoUpdateClicked(self, state):
    """ The autoupdate checkbox was clicked.
    :param state: 0 = not checked; 2 = checked
    :return:
    """
    if self.autoUpdateCheckObserver is not None:
      if state==2:
        self.autoUpdateCheckObserver(1)
      else:
        self.autoUpdateCheckObserver(0)

  def addAutoUpdateCheckObserver(self, observer):
    """ Add an observer to capture the signal when the autoupdate checkbox is clicked.
    The function 'observer' will be invoked with:
    - 1 checkbox checked
    - 0 otherwise
    :param observer: function that will be invoked when the autoupdate checkbox is clicked.
    """
    self.autoUpdateCheckObserver = observer

