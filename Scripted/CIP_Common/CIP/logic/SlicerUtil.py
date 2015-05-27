'''
Created on Feb 17, 2015
@author: Jorge Onieva
Common functions that can be useful in any Slicer module development
'''

from __main__ import slicer
import os


class SlicerUtil: 
  # Constants  
  try:
    IsDevelopment = slicer.app.settings().value('Developer/DeveloperMode').lower() == 'true'
  except:
    IsDevelopment = False
    
  ACIL_AcknowledgementText = """This work is funded by the National Heart, Lung, And Blood Institute of the National Institutes of Health under Award Number R01HL116931. 
    The content is solely the responsibility of the authors and does not necessarily represent the official views of the National Institutes of Health."""
  
  @staticmethod
  def getModuleFolder(moduleName):
    '''Get the folder where a python scripted module is physically stored''' 
    path = os.path.dirname(slicer.util.getModule(moduleName).path)
    if (os.sys.platform == "win32"):
      path = path.replace("/", "\\")
    return path
 
  @staticmethod
  def setSetting(moduleName, settingName, settingValue):
    '''Set the value of a setting in Slicer'''
    settingPath = "%s/%s" % (moduleName, settingName)   
    slicer.app.settings().setValue(settingPath, settingValue)
   
 
  @staticmethod
  def settingGetOrSetDefault(moduleName, settingName, settingDefaultValue=None):
    '''Try to find the value of a setting in Slicer and, if it does not exist, set it to the settingDefaultValue (optional)'''
    settingPath = "%s/%s" % (moduleName, settingName)
    setting = slicer.app.settings().value(settingPath)
    if setting is not None:
      return setting  # The setting was already initialized
    
    if settingDefaultValue is not None:
      slicer.app.settings().setValue(settingPath, settingDefaultValue)
        
    return settingDefaultValue
  
  @staticmethod   
  def createNewFiducial(x, y, z, radX, radY, radZ, scalarNode):
    '''Create a new fiducial (ROI) that will be visible in the scalar node passed.
    Parameters: 
    - x, y, z: fiducial coordinates
    - radX, radY, radZ: ROI size
    - scalarNode: vtk scalar node where the fiducial will be displayed'''
    fiducial = slicer.mrmlScene.CreateNodeByClass('vtkMRMLAnnotationROINode')
    fiducial.SetXYZ(x, y, z)
    fiducial.SetRadiusXYZ(radX, radY, radZ)
    # Add the fiducial to the scalar node
    displayNodeID = scalarNode.GetDisplayNode().GetID()
    fiducial.AddAndObserveDisplayNodeID(displayNodeID)
    # Get fiducial (Point)
    #f = slicer.mrmlScene.CreateNodeByClass('vtkMRMLMarkupsFiducialNode')
    #f.GetMarkupPointVector(0,0) --> returns a vtkVector3d with the coordinates for the
    # first node where the fidual is displayed (param 0) and the number of markup (param1)
     

    