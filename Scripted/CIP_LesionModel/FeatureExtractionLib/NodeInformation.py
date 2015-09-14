from __main__ import vtk, qt, ctk, slicer
import string
import numpy
import collections

class NodeInformation:

  def __init__(self, dataNode, labelNode, allKeys):
    self.nodeInformation = collections.OrderedDict()
    self.nodeInformation["Node"] = "self.nodeName(self.dataNode)"
    
    self.dataNode = dataNode
    self.labelNode = labelNode
    self.keys = set(allKeys).intersection(self.nodeInformation.keys())
             
  def nodeName (self, dataNode):
    return (dataNode.GetName())
    
  def EvaluateFeatures(self):
    # Evaluate dictionary elements corresponding to user-selected keys
       
    if not self.keys:
      return(self.nodeInformation)
       
    for key in self.keys:
      self.nodeInformation[key] = eval(self.nodeInformation[key])
    return(self.nodeInformation)
