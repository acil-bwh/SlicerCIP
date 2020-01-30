from __main__ import vtk, qt, ctk, slicer
import string
import numpy
import math
import operator
import collections
import FeatureExtractionLib
from functools import reduce


class TextureGLRL:
    def __init__(self, grayLevels, numGrayLevels, parameterMatrix, parameterMatrixCoordinates, parameterValues,
                 allKeys):
        self.textureFeaturesGLRL = collections.OrderedDict()
        self.textureFeaturesGLRLTiming = collections.OrderedDict()
        self.textureFeaturesGLRL["SRE"] = "self.shortRunEmphasis(self.P_glrl, self.jvector, self.sumP_glrl)"
        self.textureFeaturesGLRL["LRE"] = "self.longRunEmphasis(self.P_glrl, self.jvector, self.sumP_glrl)"
        self.textureFeaturesGLRL["GLN"] = "self.grayLevelNonUniformity(self.P_glrl, self.sumP_glrl)"
        self.textureFeaturesGLRL["RLN"] = "self.runLengthNonUniformity(self.P_glrl, self.sumP_glrl)"
        self.textureFeaturesGLRL["RP"] = "self.runPercentage(self.P_glrl, self.Np)"
        self.textureFeaturesGLRL["LGLRE"] = "self.lowGrayLevelRunEmphasis(self.P_glrl, self.ivector, self.sumP_glrl)"
        self.textureFeaturesGLRL["HGLRE"] = "self.highGrayLevelRunEmphasis(self.P_glrl, self.ivector, self.sumP_glrl)"
        self.textureFeaturesGLRL[
            "SRLGLE"] = "self.shortRunLowGrayLevelEmphasis(self.P_glrl, self.ivector, self.jvector, self.sumP_glrl)"
        self.textureFeaturesGLRL[
            "SRHGLE"] = "self.shortRunHighGrayLevelEmphasis(self.P_glrl, self.ivector, self.jvector, self.sumP_glrl)"
        self.textureFeaturesGLRL[
            "LRLGLE"] = "self.longRunLowGrayLevelEmphasis(self.P_glrl, self.ivector, self.jvector, self.sumP_glrl)"
        self.textureFeaturesGLRL[
            "LRHGLE"] = "self.longRunHighGrayLevelEmphasis(self.P_glrl, self.ivector, self.jvector, self.sumP_glrl)"

        self.grayLevels = grayLevels
        self.parameterMatrix = parameterMatrix
        self.parameterMatrixCoordinates = parameterMatrixCoordinates
        self.parameterValues = parameterValues
        self.numGrayLevels = numGrayLevels
        self.keys = set(allKeys).intersection(list(self.textureFeaturesGLRL.keys()))

    def CalculateCoefficients(self):
        self.angles = 13
        self.Ng = self.numGrayLevels
        self.Nr = numpy.max(self.parameterMatrix.shape)
        self.Np = self.parameterValues.size
        self.eps = numpy.spacing(1)

        self.P_glrl = numpy.zeros(
            (self.Ng, self.Nr, self.angles))  # maximum run length in P matrix initialized to highest gray level
        self.P_glrl = self.calculate_glrl(self.grayLevels, self.Ng, self.parameterMatrix,
                                          self.parameterMatrixCoordinates, self.angles, self.P_glrl)

        self.sumP_glrl = numpy.sum(numpy.sum(self.P_glrl, 0), 0) + self.eps
        self.ivector = numpy.arange(self.Ng) + 1
        self.jvector = numpy.arange(self.Nr) + 1

    def shortRunEmphasis(self, P_glrl, jvector, sumP_glrl, meanFlag=True):
        try:
            sre = numpy.sum(numpy.sum((P_glrl / ((jvector ** 2)[None, :, None])), 0), 0) / (sumP_glrl[None, None, :])
        except ZeroDivisionError:
            sre = 0
        if meanFlag:
            return (sre.mean())
        else:
            return sre

    def longRunEmphasis(self, P_glrl, jvector, sumP_glrl, meanFlag=True):
        try:
            lre = numpy.sum(numpy.sum((P_glrl * ((jvector ** 2)[None, :, None])), 0), 0) / (sumP_glrl[None, None, :])
        except ZeroDivisionError:
            lre = 0
        if meanFlag:
            return (lre.mean())
        else:
            return lre

    def grayLevelNonUniformity(self, P_glrl, sumP_glrl, meanFlag=True):
        try:
            gln = numpy.sum((numpy.sum(P_glrl, 1) ** 2), 0) / (sumP_glrl[None, None, :])
        except ZeroDivisionError:
            gln = 0
        if meanFlag:
            return (gln.mean())
        else:
            return gln

    def runLengthNonUniformity(self, P_glrl, sumP_glrl, meanFlag=True):
        try:
            rln = numpy.sum((numpy.sum(P_glrl, 0) ** 2), 0) / (sumP_glrl[None, None, :])
        except ZeroDivisionError:
            rln = 0
        if meanFlag:
            return (rln.mean())
        else:
            return rln

    def runPercentage(self, P_glrl, Np, meanFlag=True):
        try:
            rp = numpy.sum(numpy.sum((P_glrl / (Np)), 0), 0)
        except ZeroDivisionError:
            rp = 0
        if meanFlag:
            return (rp.mean())
        else:
            return rp

    def lowGrayLevelRunEmphasis(self, P_glrl, ivector, sumP_glrl, meanFlag=True):
        try:
            lglre = numpy.sum(numpy.sum((P_glrl / ((ivector ** 2)[:, None, None])), 0), 0) / (sumP_glrl[None, None, :])
        except ZeroDivisionError:
            lglre = 0
        if meanFlag:
            return (lglre.mean())
        else:
            return lglre

    def highGrayLevelRunEmphasis(self, P_glrl, ivector, sumP_glrl, meanFlag=True):
        try:
            hglre = numpy.sum(numpy.sum((P_glrl * ((ivector ** 2)[:, None, None])), 0), 0) / (sumP_glrl[None, None, :])
        except ZeroDivisionError:
            hglre = 0
        if meanFlag:
            return (hglre.mean())
        else:
            return hglre

    def shortRunLowGrayLevelEmphasis(self, P_glrl, ivector, jvector, sumP_glrl, meanFlag=True):
        try:
            srlgle = numpy.sum(numpy.sum((P_glrl / ((jvector ** 2)[None, :, None] * (ivector ** 2)[:, None, None])), 0),
                               0) / (sumP_glrl[None, None, :])
        except ZeroDivisionError:
            srlgle = 0
        if meanFlag:
            return (srlgle.mean())
        else:
            return srlgle

    def shortRunHighGrayLevelEmphasis(self, P_glrl, ivector, jvector, sumP_glrl, meanFlag=True):
        try:
            srhgle = numpy.sum(
                numpy.sum(((P_glrl * (ivector ** 2)[:, None, None]) / ((jvector ** 2)[None, :, None])), 0), 0) / (
                     sumP_glrl[None, None, :])
        except ZeroDivisionError:
            srhgle = 0
        if meanFlag:
            return (srhgle.mean())
        else:
            return srhgle

    def longRunLowGrayLevelEmphasis(self, P_glrl, ivector, jvector, sumP_glrl, meanFlag=True):
        try:
            lrlgle = numpy.sum(
                numpy.sum(((P_glrl * (jvector ** 2)[None, :, None]) / ((ivector ** 2)[:, None, None])), 0), 0) / (
                     sumP_glrl[None, None, :])
        except ZeroDivisionError:
            lrlgle = 0
        if meanFlag:
            return (lrlgle.mean())
        else:
            return lrlgle

    def longRunHighGrayLevelEmphasis(self, P_glrl, ivector, jvector, sumP_glrl, meanFlag=True):
        try:
            lrhgle = numpy.sum(numpy.sum((P_glrl * (ivector ** 2)[:, None, None] * (jvector ** 2)[None, :, None]), 0),
                               0) / (sumP_glrl[None, None, :])
        except ZeroDivisionError:
            lrhgle = 0
        if meanFlag:
            return (lrhgle.mean())
        else:
            return lrhgle

    def calculate_glrl(self, grayLevels, numGrayLevels, matrix, matrixCoordinates, angles, P_out):
        padVal = 0  # use eps or NaN to pad matrix
        matrixDiagonals = list()

        # TODO: try using itertools list merging with lists of GLRL diagonal    
        # i.e.: self.heterogeneityFeatureWidgets = list(itertools.chain.from_iterable(self.featureWidgets.values()))

        # For a single direction or diagonal (aDiags, bDiags...lDiags, mDiags):   
        # Generate a 1D array for each valid offset of the diagonal, a, in the range specified by lowBound and highBound  
        # Convert each 1D array to a python list ( matrix.diagonal(a,,).tolist() ) 
        # Join lists using reduce(lamda x,y: x+y, ...) to represent all 1D arrays for the direction/diagonal       
        # Use filter(lambda x: numpy.nonzero(x)[0].size>1, ....) to filter 1D arrays of size < 2 or value == 0 or padValue

        # Should change from nonzero() to filter for the padValue specifically (NaN, eps, etc)

        # (1,0,0), #(-1,0,0),
        aDiags = reduce(lambda x, y: x + y, [a.tolist() for a in numpy.transpose(matrix, (1, 2, 0))])
        matrixDiagonals.append([x for x in aDiags if numpy.nonzero(x)[0].size > 1])

        # (0,1,0), #(0,-1,0),
        bDiags = reduce(lambda x, y: x + y, [a.tolist() for a in numpy.transpose(matrix, (0, 2, 1))])
        matrixDiagonals.append([x for x in bDiags if numpy.nonzero(x)[0].size > 1])

        # (0,0,1), #(0,0,-1), 
        cDiags = reduce(lambda x, y: x + y, [a.tolist() for a in numpy.transpose(matrix, (0, 1, 2))])
        matrixDiagonals.append([x for x in cDiags if numpy.nonzero(x)[0].size > 1])

        # (1,1,0),#(-1,-1,0),
        lowBound = -matrix.shape[0] + 1
        highBound = matrix.shape[1]

        dDiags = reduce(lambda x, y: x + y, [matrix.diagonal(a, 0, 1).tolist() for a in range(lowBound, highBound)])
        matrixDiagonals.append([x for x in dDiags if numpy.nonzero(x)[0].size > 1])

        # (1,0,1), #(-1,0-1),
        lowBound = -matrix.shape[0] + 1
        highBound = matrix.shape[2]

        eDiags = reduce(lambda x, y: x + y, [matrix.diagonal(a, 0, 2).tolist() for a in range(lowBound, highBound)])
        matrixDiagonals.append([x for x in eDiags if numpy.nonzero(x)[0].size > 1])

        # (0,1,1), #(0,-1,-1),
        lowBound = -matrix.shape[1] + 1
        highBound = matrix.shape[2]

        fDiags = reduce(lambda x, y: x + y, [matrix.diagonal(a, 1, 2).tolist() for a in range(lowBound, highBound)])
        matrixDiagonals.append([x for x in fDiags if numpy.nonzero(x)[0].size > 1])

        # (1,-1,0), #(-1,1,0),    
        lowBound = -matrix.shape[0] + 1
        highBound = matrix.shape[1]

        gDiags = reduce(lambda x, y: x + y,
                        [matrix[:, ::-1, :].diagonal(a, 0, 1).tolist() for a in range(lowBound, highBound)])
        matrixDiagonals.append([x for x in gDiags if numpy.nonzero(x)[0].size > 1])

        # (-1,0,1), #(1,0,-1),
        lowBound = -matrix.shape[0] + 1
        highBound = matrix.shape[2]

        hDiags = reduce(lambda x, y: x + y,
                        [matrix[:, :, ::-1].diagonal(a, 0, 2).tolist() for a in range(lowBound, highBound)])
        matrixDiagonals.append([x for x in hDiags if numpy.nonzero(x)[0].size > 1])

        # (0,1,-1), #(0,-1,1),
        lowBound = -matrix.shape[1] + 1
        highBound = matrix.shape[2]

        iDiags = reduce(lambda x, y: x + y,
                        [matrix[:, :, ::-1].diagonal(a, 1, 2).tolist() for a in range(lowBound, highBound)])
        matrixDiagonals.append([x for x in iDiags if numpy.nonzero(x)[0].size > 1])

        # (1,1,1), #(-1,-1,-1)
        lowBound = -matrix.shape[0] + 1
        highBound = matrix.shape[1]

        jDiags = [numpy.diagonal(h, x, 0, 1).tolist() for h in
                  [matrix.diagonal(a, 0, 1) for a in range(lowBound, highBound)] for x in
                  range(-h.shape[0] + 1, h.shape[1])]
        matrixDiagonals.append([x for x in jDiags if numpy.nonzero(x)[0].size > 1])

        # (-1,1,-1), #(1,-1,1),
        lowBound = -matrix.shape[0] + 1
        highBound = matrix.shape[1]

        kDiags = [numpy.diagonal(h, x, 0, 1).tolist() for h in
                  [matrix[:, ::-1, :].diagonal(a, 0, 1) for a in range(lowBound, highBound)] for x in
                  range(-h.shape[0] + 1, h.shape[1])]
        matrixDiagonals.append([x for x in kDiags if numpy.nonzero(x)[0].size > 1])

        # (1,1,-1), #(-1,-1,1),
        lowBound = -matrix.shape[0] + 1
        highBound = matrix.shape[1]

        lDiags = [numpy.diagonal(h, x, 0, 1).tolist() for h in
                  [matrix[:, :, ::-1].diagonal(a, 0, 1) for a in range(lowBound, highBound)] for x in
                  range(-h.shape[0] + 1, h.shape[1])]
        matrixDiagonals.append([x for x in lDiags if numpy.nonzero(x)[0].size > 1])

        # (-1,1,1), #(1,-1,-1),
        lowBound = -matrix.shape[0] + 1
        highBound = matrix.shape[1]
    
        mDiags = [numpy.diagonal(h, x, 0, 1).tolist() for h in
                  [matrix[:, ::-1, ::-1].diagonal(a, 0, 1) for a in range(lowBound, highBound)] for x in
                  range(-h.shape[0] + 1, h.shape[1])]
        matrixDiagonals.append([x for x in mDiags if numpy.nonzero(x)[0].size > 1])

        # [n for n in mDiags if numpy.nonzero(n)[0].size>1] instead of filter(lambda x: numpy.nonzero(x)[0].size>1, mDiags)?

        # Run-Length Encoding (rle) for the 13 list of diagonals (1 list per 3D direction/angle)
        for angle in range(0, len(matrixDiagonals)):
            P = P_out[:, :, angle]
            for diagonal in matrixDiagonals[angle]:
                diagonal = numpy.array(diagonal, dtype='int')
                pos, = numpy.where(
                    numpy.diff(diagonal) != 0)  # can use instead of using map operator._ on np.where tuples
                pos = numpy.concatenate(([0], pos + 1, [len(diagonal)]))

                # a or pos[:-1] = run start #b or pos[1:] = run stop #diagonal[a] is matrix value       
                # adjust condition for pos[:-1] != padVal = 0 to != padVal = eps or NaN or whatever pad value
                rle = list(zip([n for n in diagonal[pos[:-1]] if n != padVal], pos[1:] - pos[:-1]))
                rle = [[numpy.where(grayLevels == x)[0][0], y - 1] for x, y in
                       rle]  # rle = map(lambda (x,y): [voxelToIndexDict[x],y-1], rle)

                # Increment GLRL matrix counter at coordinates defined by the run-length encoding               
                P[list(zip(*rle))] += 1

        return (P_out)

    def EvaluateFeatures(self, printTiming=False, checkStopProcessFunction=None):
        # Remove all the keys that must not be evaluated
        for key in set(self.textureFeaturesGLRL.keys()).difference(self.keys):
            self.textureFeaturesGLRL[key] = None

        if not self.keys:
            if not printTiming:
                return self.textureFeaturesGLRL
            else:
                return self.textureFeaturesGLRL, self.textureFeaturesGLRLTiming
        
        if not printTiming:
            self.CalculateCoefficients()
        else:
            import time
            t1 = time.time()
            self.CalculateCoefficients()
            print(("- Time to calculate coefficients in GLRL: {0} seconds".format(time.time() - t1)))

        if not printTiming:
            # Evaluate dictionary elements corresponding to user selected keys
            for key in self.keys:
                self.textureFeaturesGLRL[key] = eval(self.textureFeaturesGLRL[key])
                if checkStopProcessFunction is not None:
                    checkStopProcessFunction()
            return self.textureFeaturesGLRL
        else:
            # Evaluate dictionary elements corresponding to user selected keys
            for key in self.keys:
                t1 = time.time()
                self.textureFeaturesGLRL[key] = eval(self.textureFeaturesGLRL[key])
                self.textureFeaturesGLRLTiming[key] = time.time() - t1
                if checkStopProcessFunction is not None:
                    checkStopProcessFunction()
            return self.textureFeaturesGLRL, self.textureFeaturesGLRLTiming
