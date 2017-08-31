
class CIP_:
  """Module template for ACIL Slicer Modules"""
  def __init__(self, parent):
    """Constructor for main class"""
    self.parent = parent    
    #ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "CIP_"
    self.parent.categories = ["CIP"]
    self.parent.dependencies = []
    self.parent.contributors = ["Jorge Onieva", "Applied Chest Imaging Laboratory", "Brigham and Women's Hospital"] 
    #self.parent.helpText = "Text displayed in Help tab"
    #self.parent.acknowledgementText = ACIL_AcknowledgementText
    self.parent.hidden = True   # Hide the module. It just works as a container for the CIP python library
  
class CIP_Widget:
  def __init__(self, parent = None):
    self.parent = parent
  
  def setup(self):
    # don't display anything for this widget - it will be hidden anyway
    print ("ok")    
    pass
  def enter(self):
    pass
  def exit(self):
    pass
  def cleanup(self):
    pass
