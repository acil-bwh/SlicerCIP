from __main__ import vtk, qt, ctk, slicer
import string
import numpy
import math
import operator
import collections

class RenyiDimensions:

    def __init__(self, matrixPadded, matrixPaddedCoordinates, allKeys):
        self.renyiDimensions = collections.OrderedDict()
        self.renyiDimensions["Box-Counting Dimension"] = "self.renyiDimension(self.matrixPadded, self.matrixPaddedCoordinates, 0)"
        self.renyiDimensions["Information Dimension"] = "self.renyiDimension(self.matrixPadded, self.matrixPaddedCoordinates, 1)"
        self.renyiDimensions["Correlation Dimension"] = "self.renyiDimension(self.matrixPadded, self.matrixPaddedCoordinates, 2)"
        
        self.renyiDimensionTiming = collections.OrderedDict()
        
        self.matrixPadded = matrixPadded
        self.matrixPaddedCoordinates = matrixPaddedCoordinates
        self.allKeys = allKeys
        
             
    def EvaluateFeatures(self, printTiming=False, checkStopProcessFunction=None):
        self.checkStopProcessFunction=checkStopProcessFunction
        keys = set(self.allKeys).intersection(list(self.renyiDimensions.keys()))

        # Remove all the keys that must not be evaluated
        for key in set(self.renyiDimensions.keys()).difference(keys):
            self.renyiDimensions[key] = None

        if not printTiming:
            if not keys:
                return self.renyiDimensions
            
            #Evaluate dictionary elements corresponding to user selected keys
            for key in keys:
                self.renyiDimensions[key] = eval(self.renyiDimensions[key])
                if checkStopProcessFunction is not None:
                    checkStopProcessFunction()
            return self.renyiDimensions
        else:
            if not keys:
                return self.renyiDimensions, self.renyiDimensionTiming

            import time
            #Evaluate dictionary elements corresponding to user selected keys
            for key in keys:
                t1 = time.time()
                self.renyiDimensions[key] = eval(self.renyiDimensions[key])
                self.renyiDimensionTiming[key] = time.time() - t1
                if checkStopProcessFunction is not None:
                    checkStopProcessFunction()
            return self.renyiDimensions, self.renyiDimensionTiming
        
            
    def renyiDimension(self, c, matrixCoordinatesPadded, q=0): 
        # computes renyi dimensions for q = 0,1,2 (box-count(default, q=0), information(q=1), and correlation dimensions(q=2))
        # for a padded 3D input array or matrix, c, and the coordinates of values in c, matrixCoordinatesPadded.
        # c must be padded to a cube with shape equal to next greatest power of two 
        # i.e. a 3D array with shape: (3,13,9) is padded to shape: (16,16,16)    
         
        # exception for numpy.sum(c) = 0?
        c = c/float(numpy.sum(c))
        maxDim = c.shape[0]
        p = int(numpy.log2(maxDim))
        n = numpy.zeros(p+1)
        eps = numpy.spacing(1)
        
        # Initialize N(s) value at the finest/voxel-level scale
        if (q==1):
            n[p] = numpy.sum(c[matrixCoordinatesPadded] * numpy.log(1/(c[matrixCoordinatesPadded] + eps)))
        else:
            n[p] = numpy.sum(c[matrixCoordinatesPadded]**q)
                    
        for g in range(p-1, -1, -1):
            siz = 2**(p-g)
            siz2 = round(siz/2)
            for i in range(0, maxDim-siz+1, siz):
                for j in range(0, maxDim-siz+1, siz):
                    for k in range(0, maxDim-siz+1, siz):
                        box = numpy.array([ c[i,j,k], c[i+siz2,j,k], c[i,j+siz2,k], c[i+siz2,j+siz2,k], c[i,j,k+siz2], c[i+siz2,j,k+siz2], c[i,j+siz2,k+siz2], c[i+siz2,j+siz2,k+siz2] ])
                        c[i,j,k] =    numpy.any(box != 0) if (q==0) else numpy.sum(box)**q
                    if self.checkStopProcessFunction is not None:
                        self.checkStopProcessFunction()
                        #print (i, j, k, '                ', c[i,j,k])
            pi = c[0:(maxDim-siz+1):siz, 0:(maxDim-siz+1):siz, 0:(maxDim-siz+1):siz]                            
            if (q == 1):             
                n[g] = numpy.sum(pi * numpy.log(1/(pi+eps)))
            else:
                n[g] = numpy.sum(pi) 
            #print ('p, g, siz, siz2', p, g, siz, siz2, '         n[g]: ', n[g])
        
        r = numpy.log(2.0**(numpy.arange(p+1))) # log(1/scale)
        scaleMatrix = numpy.array([r, numpy.ones(p+1)])             
        #print ('n(s): ', n)
        #print ('log (1/s): ', r)
        
        if (q != 1):     
            n = (1/float(1-q)) * numpy.log(n)
        renyiDimension = numpy.linalg.lstsq(scaleMatrix.T, n)[0][0]
        
        return (renyiDimension)
