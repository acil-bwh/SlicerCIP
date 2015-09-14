from __main__ import vtk, qt, ctk, slicer
import string
import numpy
import math
import operator
import collections

class FirstOrderStatistics:

  def __init__(self, parameterValues, bins, grayLevels, allKeys):
    self.firstOrderStatistics = collections.OrderedDict()
    self.firstOrderStatistics["Voxel Count"] = "self.voxelCount(self.parameterValues)"
    self.firstOrderStatistics["Gray Levels"] = "self.grayLevelCount(self.grayLevels)"
    self.firstOrderStatistics["Energy"] = "self.energyValue(self.parameterValues)"
    self.firstOrderStatistics["Entropy"] = "self.entropyValue(self.bins)" 
    self.firstOrderStatistics["Minimum Intensity"] = "self.minIntensity(self.parameterValues)"
    self.firstOrderStatistics["Maximum Intensity"] = "self.maxIntensity(self.parameterValues)"  
    self.firstOrderStatistics["Mean Intensity"] = "self.meanIntensity(self.parameterValues)"
    self.firstOrderStatistics["Median Intensity"] = "self.medianIntensity(self.parameterValues)"
    self.firstOrderStatistics["Range"] = "self.rangeIntensity(self.parameterValues)"
    self.firstOrderStatistics["Mean Deviation"] = "self.meanDeviation(self.parameterValues)"
    self.firstOrderStatistics["Root Mean Square"] = "self.rootMeanSquared(self.parameterValues)"
    self.firstOrderStatistics["Standard Deviation"] = "self.standardDeviation(self.parameterValues)"
    self.firstOrderStatistics["Skewness"] = "self.skewnessValue(self.parameterValues)"
    self.firstOrderStatistics["Kurtosis"] = "self.kurtosisValue(self.parameterValues)"
    self.firstOrderStatistics["Variance"] = "self.varianceValue(self.parameterValues)"
    self.firstOrderStatistics["Uniformity"] = "self.uniformityValue(self.bins)"
    
    self.parameterValues = parameterValues
    self.bins = bins
    self.grayLevels = grayLevels
    self.keys = set(allKeys).intersection(self.firstOrderStatistics.keys())
          
  def voxelCount(self, parameterArray):
    return (parameterArray.size)
      
  def grayLevelCount(self, grayLevels):
    return (grayLevels)
      
  def energyValue(self, parameterArray):
    return (numpy.sum(parameterArray**2))
     
  def entropyValue(self, bins):
    return (numpy.sum(bins*numpy.where(bins!=0,numpy.log2(bins),0)))
      
  def minIntensity(self, parameterArray):
    return (numpy.min(parameterArray))
  
  def maxIntensity(self, parameterArray):
    return (numpy.max(parameterArray))
      
  def meanIntensity(self, parameterArray):
    return (numpy.mean(parameterArray))
      
  def medianIntensity (self, parameterArray):
    return (numpy.median(parameterArray))
      
  def rangeIntensity (self, parameterArray):
    return (numpy.max(parameterArray) - numpy.min(parameterArray))
  
  def meanDeviation(self, parameterArray):
    return ( numpy.mean(numpy.absolute( (numpy.mean(parameterArray) - parameterArray) )) )
  
  def rootMeanSquared(self, parameterArray): 
    return ( ((numpy.sum(parameterArray**2))/(parameterArray.size) )**(1/2.0) )
  
  def standardDeviation(self, parameterArray):
    return (numpy.std(parameterArray))
  
  def _moment(self, a, moment=1, axis=0):
    # Modified from SciPy module
    
    if moment == 1:
      return numpy.float64(0.0)
    else:
      mn = numpy.expand_dims(numpy.mean(a,axis), axis)
      s = numpy.power((a-mn), moment)
      return numpy.mean(s, axis)

  def skewnessValue(self, a, axis=0):
    # Modified from SciPy module
    # Computes the skewness of a dataset
     
    m2 = self._moment(a, 2, axis)
    m3 = self._moment(a, 3, axis)
    
    # Control Flow: if m2==0 then vals = 0; else vals = m3/m2**1.5
    zero = (m2 == 0)
    vals = numpy.where(zero, 0, m3 / m2**1.5)
    
    if vals.ndim == 0:
        return vals.item()
    return vals

  def kurtosisValue(self, a, axis=0, fisher=True):
    # Modified from SciPy module
    
    m2 = self._moment(a,2,axis)
    m4 = self._moment(a,4,axis)
    zero = (m2 == 0)
    
    # Set Floating-Point Error Handling
    olderr = numpy.seterr(all='ignore')
    try:
      vals = numpy.where(zero, 0, m4 / m2**2.0)
    finally:
      numpy.seterr(**olderr)
    if vals.ndim == 0:
      vals = vals.item() # array scalar

    if fisher:
      return vals - 3
    else:
      return vals
      
  def varianceValue(self, parameterArray):
    return (numpy.std(parameterArray)**2)
  
  def uniformityValue(self, bins):
    return (numpy.sum(bins**2))
    
  def EvaluateFeatures(self):
    # Evaluate dictionary elements corresponding to user-selected keys
       
    if not self.keys:
      return(self.firstOrderStatistics)
    
    for key in self.keys:
      self.firstOrderStatistics[key] = eval(self.firstOrderStatistics[key])
    return(self.firstOrderStatistics)
            
