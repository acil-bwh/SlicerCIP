from __main__ import vtk, qt, ctk, slicer
import string
import numpy
import math
import operator
import collections
import time


# from decimal import *

class TextureGLCM:
    def __init__(self, grayLevels, numGrayLevels, parameterMatrix, parameterMatrixCoordinates, parameterValues,
                 allKeys, checkStopProcessFunction):
        self.textureFeaturesGLCM = collections.OrderedDict()
        self.textureFeaturesGLCMTiming = collections.OrderedDict()

        self.textureFeaturesGLCM["Autocorrelation"] = "self.autocorrelationGLCM(self.P_glcm, self.prodMatrix)"
        self.textureFeaturesGLCM[
            "Cluster Prominence"] = "self.clusterProminenceGLCM(self.P_glcm, self.sumMatrix, self.ux, self.uy)"
        self.textureFeaturesGLCM[
            "Cluster Shade"] = "self.clusterShadeGLCM(self.P_glcm, self.sumMatrix, self.ux, self.uy)"
        self.textureFeaturesGLCM[
            "Cluster Tendency"] = "self.clusterTendencyGLCM(self.P_glcm, self.sumMatrix, self.ux, self.uy)"
        self.textureFeaturesGLCM["Contrast"] = "self.contrastGLCM(self.P_glcm, self.diffMatrix)"
        self.textureFeaturesGLCM[
            "Correlation"] = "self.correlationGLCM(self.P_glcm, self.prodMatrix, self.ux, self.uy, self.sigx, self.sigy)"
        self.textureFeaturesGLCM["Difference Entropy"] = "self.differenceEntropyGLCM(self.pxSuby, self.eps)"
        self.textureFeaturesGLCM["Dissimilarity"] = "self.dissimilarityGLCM(self.P_glcm, self.diffMatrix)"
        self.textureFeaturesGLCM["Energy (GLCM)"] = "self.energyGLCM(self.P_glcm)"
        self.textureFeaturesGLCM["Entropy(GLCM)"] = "self.entropyGLCM(self.P_glcm, self.pxy, self.eps)"
        self.textureFeaturesGLCM["Homogeneity 1"] = "self.homogeneity1GLCM(self.P_glcm, self.diffMatrix)"
        self.textureFeaturesGLCM["Homogeneity 2"] = "self.homogeneity2GLCM(self.P_glcm, self.diffMatrix)"
        self.textureFeaturesGLCM["IMC1"] = "self.imc1GLCM(self.HXY, self.HXY1, self.HX, self.HY)"
        # self.textureFeaturesGLCM["IMC2"] = "sum(imc2)/len(imc2)" #"self.imc2GLCM(self,)"  # produces a calculation error
        self.textureFeaturesGLCM["IDMN"] = "self.idmnGLCM(self.P_glcm, self.diffMatrix, self.Ng)"
        self.textureFeaturesGLCM["IDN"] = "self.idnGLCM(self.P_glcm, self.diffMatrix, self.Ng)"
        self.textureFeaturesGLCM["Inverse Variance"] = "self.inverseVarianceGLCM(self.P_glcm, self.diffMatrix, self.Ng)"
        self.textureFeaturesGLCM["Maximum Probability"] = "self.maximumProbabilityGLCM(self.P_glcm)"
        self.textureFeaturesGLCM["Sum Average"] = "self.sumAverageGLCM(self.pxAddy, self.kValuesSum)"
        self.textureFeaturesGLCM["Sum Entropy"] = "self.sumEntropyGLCM(self.pxAddy, self.eps)"
        self.textureFeaturesGLCM["Sum Variance"] = "self.sumVarianceGLCM(self.pxAddy, self.kValuesSum)"
        self.textureFeaturesGLCM["Variance (GLCM)"] = "self.varianceGLCM(self.P_glcm, self.ivector, self.u)"

        self.grayLevels = grayLevels
        self.parameterMatrix = parameterMatrix
        self.parameterMatrixCoordinates = parameterMatrixCoordinates
        self.parameterValues = parameterValues
        self.Ng = numGrayLevels
        self.keys = set(allKeys).intersection(list(self.textureFeaturesGLCM.keys()))
        # Callback function to stop the process if the user decided so. CalculateCoefficients can take a long time to run...
        self.checkStopProcessFunction = checkStopProcessFunction

    def CalculateCoefficients(self, printTiming=False):
        """ Calculate generic coefficients that will be reused in different markers
        IMPORTANT!! This method is VERY inefficient when the nodule is big (because
        of the function calculate_glcm at least). If these
        statistics are required it would probably need some optimizations
        :return:
        """
        # generate container for GLCM Matrices, self.P_glcm
        # make distance an optional parameter, as in: distances = numpy.arange(parameter)
        distances = numpy.array([1])
        directions = 26
        self.P_glcm = numpy.zeros((self.Ng, self.Ng, distances.size, directions))
        t1 = time.time()
        self.P_glcm = self.calculate_glcm(self.grayLevels, self.parameterMatrix, self.parameterMatrixCoordinates,
                                          distances, directions, self.Ng, self.P_glcm)
        if printTiming:
            print(("- Time to calculate glmc matrix: {0} secs".format(time.time() - t1)))
        # make each GLCM symmetric an optional parameter
        # if symmetric:
        # Pt = numpy.transpose(P, (1, 0, 2, 3))
        # P = P + Pt

        ##Calculate GLCM Coefficients
        self.ivector = numpy.arange(1, self.Ng + 1)  # shape = (self.Ng, distances.size, directions)
        self.jvector = numpy.arange(1, self.Ng + 1)  # shape = (self.Ng, distances.size, directions)
        self.eps = numpy.spacing(1)

        self.prodMatrix = numpy.multiply.outer(self.ivector, self.jvector)  # shape = (self.Ng, self.Ng)
        self.sumMatrix = numpy.add.outer(self.ivector, self.jvector)  # shape = (self.Ng, self.Ng)
        self.diffMatrix = numpy.absolute(numpy.subtract.outer(self.ivector, self.jvector))  # shape = (self.Ng, self.Ng)
        self.kValuesSum = numpy.arange(2, (self.Ng * 2) + 1)  # shape = (2*self.Ng-1)
        self.kValuesDiff = numpy.arange(0, self.Ng)  # shape = (self.Ng-1)

        # shape = (distances.size, directions)
        self.u = self.P_glcm.mean(0).mean(0)
        # marginal row probabilities #shape = (self.Ng, distances.size, directions)
        self.px = self.P_glcm.sum(1)
        # marginal column probabilities #shape = (self.Ng, distances.size, directions)
        self.py = self.P_glcm.sum(0)

        # shape = (distances.size, directions)
        self.ux = self.px.mean(0)
        # shape = (distances.size, directions)
        self.uy = self.py.mean(0)

        # shape = (distances.size, directions)
        self.sigx = self.px.std(0)
        # shape = (distances.size, directions)
        self.sigy = self.py.std(0)

        # shape = (2*self.Ng-1, distances.size, directions)
        self.pxAddy = numpy.array([numpy.sum(self.P_glcm[self.sumMatrix == k], 0) for k in self.kValuesSum])
        # shape = (self.Ng, distances.size, directions)
        self.pxSuby = numpy.array([numpy.sum(self.P_glcm[self.diffMatrix == k], 0) for k in self.kValuesDiff])

        # entropy of self.px #shape = (distances.size, directions)
        self.HX = (-1) * numpy.sum((self.px * numpy.where(self.px != 0, numpy.log2(self.px), numpy.log2(self.eps))), 0)
        # entropy of py #shape = (distances.size, directions)
        self.HY = (-1) * numpy.sum((self.py * numpy.where(self.py != 0, numpy.log2(self.py), numpy.log2(self.eps))), 0)
        # shape = (distances.size, directions)
        self.HXY = (-1) * numpy.sum(
            numpy.sum((self.P_glcm * numpy.where(self.P_glcm != 0, numpy.log2(self.P_glcm), numpy.log2(self.eps))), 0),
            0)

        self.pxy = numpy.zeros(self.P_glcm.shape)  # shape = (self.Ng, self.Ng, distances.size, directions)
        for a in range(directions):
            for g in range(distances.size):
                self.pxy[:, :, g, a] = numpy.multiply.outer(self.px[:, g, a], self.py[:, g, a])

        self.HXY1 = (-1) * numpy.sum(
            numpy.sum((self.P_glcm * numpy.where(self.pxy != 0, numpy.log2(self.pxy), numpy.log2(self.eps))), 0),
            0)  # shape = (distances.size, directions)
        self.HXY2 = (-1) * numpy.sum(
            numpy.sum((self.pxy * numpy.where(self.pxy != 0, numpy.log2(self.pxy), numpy.log2(self.eps))), 0),
            0)  # shape = (distances.size, directions)
        if printTiming:
            print(("- Time to calculate total glmc coefficients: {0} secs".format(time.time() - t1)))

    def autocorrelationGLCM(self, P_glcm, prodMatrix, meanFlag=True):
        ac = numpy.sum(numpy.sum(P_glcm * prodMatrix[:, :, None, None], 0), 0)
        if meanFlag:
            return (ac.mean())
        else:
            return ac

    def clusterProminenceGLCM(self, P_glcm, sumMatrix, ux, uy, meanFlag=True):
        # Need to validate function
        cp = numpy.sum(
            numpy.sum((P_glcm * ((sumMatrix[:, :, None, None] - ux[None, None, :, :] - uy[None, None, :, :]) ** 4)), 0),
            0)
        if meanFlag:
            return (cp.mean())
        else:
            return cp

    def clusterShadeGLCM(self, P_glcm, sumMatrix, ux, uy, meanFlag=True):
        # Need to validate function
        cs = numpy.sum(
            numpy.sum((P_glcm * ((sumMatrix[:, :, None, None] - ux[None, None, :, :] - uy[None, None, :, :]) ** 3)), 0),
            0)
        if meanFlag:
            return (cs.mean())
        else:
            return cs

    def clusterTendencyGLCM(self, P_glcm, sumMatrix, ux, uy, meanFlag=True):
        # Need to validate function
        ct = numpy.sum(
            numpy.sum((P_glcm * ((sumMatrix[:, :, None, None] - ux[None, None, :, :] - uy[None, None, :, :]) ** 2)), 0),
            0)
        if meanFlag:
            return (ct.mean())
        else:
            return ct

    def contrastGLCM(self, P_glcm, diffMatrix, meanFlag=True):
        cont = numpy.sum(numpy.sum((P_glcm * (diffMatrix[:, :, None, None] ** 2)), 0), 0)
        if meanFlag:
            return (cont.mean())
        else:
            return cont

    def correlationGLCM(self, P_glcm, prodMatrix, ux, uy, sigx, sigy, meanFlag=True):
        # Need to validate function
        uxy = ux * uy
        sigxy = sigx * sigy
        corr = numpy.sum(
            numpy.sum(((P_glcm * prodMatrix[:, :, None, None] - uxy[None, None, :, :]) / (sigxy[None, None, :, :])), 0),
            0)
        if meanFlag:
            return (corr.mean())
        else:
            return corr

    def differenceEntropyGLCM(self, pxSuby, eps, meanFlag=True):
        difent = numpy.sum((pxSuby * numpy.where(pxSuby != 0, numpy.log2(pxSuby), numpy.log2(eps))), 0)
        if meanFlag:
            return (difent.mean())
        else:
            return difent

    def dissimilarityGLCM(self, P_glcm, diffMatrix, meanFlag=True):
        dis = numpy.sum(numpy.sum((P_glcm * diffMatrix[:, :, None, None]), 0), 0)
        if meanFlag:
            return (dis.mean())
        else:
            return dis

    def energyGLCM(self, P_glcm, meanFlag=True):
        ene = numpy.sum(numpy.sum((P_glcm ** 2), 0), 0)
        if meanFlag:
            return (ene.mean())
        else:
            return ene

    def entropyGLCM(self, P_glcm, pxy, eps, meanFlag=True):
        ent = -1 * numpy.sum(numpy.sum((P_glcm * numpy.where(pxy != 0, numpy.log2(pxy), numpy.log2(eps))), 0), 0)
        if meanFlag:
            return (ent.mean())
        else:
            return ent

    def homogeneity1GLCM(self, P_glcm, diffMatrix, meanFlag=True):
        homo1 = numpy.sum(numpy.sum((P_glcm / (1 + diffMatrix[:, :, None, None])), 0), 0)
        if meanFlag:
            return (homo1.mean())
        else:
            return homo1

    def homogeneity2GLCM(self, P_glcm, diffMatrix, meanFlag=True):
        homo2 = numpy.sum(numpy.sum((P_glcm / (1 + diffMatrix[:, :, None, None] ** 2)), 0), 0)
        if meanFlag:
            return (homo2.mean())
        else:
            return homo2

    def imc1GLCM(self, HXY, HXY1, HX, HY, meanFlag=True):
        imc1 = (self.HXY - self.HXY1) / numpy.max(([self.HX, self.HY]), 0)
        if meanFlag:
            return (imc1.mean())
        else:
            return imc1

            # def imc2GLCM(self,):
            # imc2[g,a] = ( 1-numpy.e**(-2*(HXY2[g,a]-HXY[g,a])) )**(0.5) #nan value too high

            # produces Nan(square root of a negative)
            # exponent = decimal.Decimal( -2*(HXY2[g,a]-self.HXY[g,a]) )
            # imc2.append( ( decimal.Decimal(1)-decimal.Decimal(numpy.e)**(exponent) )**(decimal.Decimal(0.5)) )

            # if meanFlag:
            # return (homo2.mean())
            # else:
            # return homo2

    def idmnGLCM(self, P_glcm, diffMatrix, Ng, meanFlag=True):
        idmn = numpy.sum(numpy.sum((P_glcm / (1 + ((diffMatrix[:, :, None, None] ** 2) / (Ng ** 2)))), 0), 0)
        if meanFlag:
            return (idmn.mean())
        else:
            return idmn

    def idnGLCM(self, P_glcm, diffMatrix, Ng, meanFlag=True):
        idn = numpy.sum(numpy.sum((P_glcm / (1 + (diffMatrix[:, :, None, None] / Ng))), 0), 0)
        if meanFlag:
            return (idn.mean())
        else:
            return idn

    def inverseVarianceGLCM(self, P_glcm, diffMatrix, Ng, meanFlag=True):
        maskDiags = numpy.ones(diffMatrix.shape, dtype=bool)
        maskDiags[numpy.diag_indices(Ng)] = False
        inv = numpy.sum((P_glcm[maskDiags] / (diffMatrix[:, :, None, None] ** 2)[maskDiags]), 0)
        if meanFlag:
            return (inv.mean())
        else:
            return inv

    def maximumProbabilityGLCM(self, P_glcm, meanFlag=True):
        maxprob = P_glcm.max(0).max(0)
        if meanFlag:
            return (maxprob.mean())
        else:
            return maxprob

    def sumAverageGLCM(self, pxAddy, kValuesSum, meanFlag=True):
        sumavg = numpy.sum((kValuesSum[:, None, None] * pxAddy), 0)
        if meanFlag:
            return (sumavg.mean())
        else:
            return sumavg

    def sumEntropyGLCM(self, pxAddy, eps, meanFlag=True):
        sumentr = (-1) * numpy.sum((pxAddy * numpy.where(pxAddy != 0, numpy.log2(pxAddy), numpy.log2(eps))), 0)
        if meanFlag:
            return (sumentr.mean())
        else:
            return sumentr

    def sumVarianceGLCM(self, pxAddy, kValuesSum, meanFlag=True):
        sumvar = numpy.sum((pxAddy * ((kValuesSum[:, None, None] - kValuesSum[:, None, None] * pxAddy) ** 2)), 0)
        if meanFlag:
            return (sumvar.mean())
        else:
            return sumvar

    def varianceGLCM(self, P_glcm, ivector, u, meanFlag=True):
        vari = numpy.sum(numpy.sum((P_glcm * ((ivector[:, None] - u) ** 2)[:, None, None, :]), 0), 0)
        if meanFlag:
            return (vari.mean())
        else:
            return vari

    def calculate_glcm(self, grayLevels, matrix, matrixCoordinates, distances, directions, numGrayLevels, out):
        # VERY INEFFICIENT!!
        # 26 GLCM matrices for each image for every direction from the voxel
        # (26 for each neighboring voxel from a reference voxel centered in a 3x3 cube)
        # for GLCM matrices P(i,j;gamma, a), gamma = 1, a = 1...13

        angles_idx = 0
        distances_idx = 0
        r = 0
        c = 0
        h = 0
        rows = matrix.shape[2]
        cols = matrix.shape[1]
        height = matrix.shape[0]
        row = 0
        col = 0
        height = 0

        angles = numpy.array([(1, 0, 0),
                              (-1, 0, 0),
                              (0, 1, 0),
                              (0, -1, 0),
                              (0, 0, 1),
                              (0, 0, -1),
                              (1, 1, 0),
                              (-1, 1, 0),
                              (1, -1, 0),
                              (-1, -1, 0),
                              (1, 0, 1),
                              (-1, 0, 1),
                              (1, 0, -1),
                              (-1, 0, -1),
                              (0, 1, 1),
                              (0, -1, 1),
                              (0, 1, -1),
                              (0, -1, -1),
                              (1, 1, 1),
                              (-1, 1, 1),
                              (1, -1, 1),
                              (1, 1, -1),
                              (-1, -1, 1),
                              (-1, 1, -1),
                              (1, -1, -1),
                              (-1, -1, -1)])

        indices = list(zip(*matrixCoordinates))


        for iteration in range(len(indices)):
        #for h, c, r in indices:
            h, c, r = indices[iteration]
            for angles_idx in range(directions):
                angle = angles[angles_idx]

                for distances_idx in range(distances.size):
                    distance = distances[distances_idx]

                    i = matrix[h, c, r]
                    i_idx = numpy.nonzero(grayLevels == i)

                    row = r + angle[2]
                    col = c + angle[1]
                    height = h + angle[0]

                    # Can introduce Parameter Option for reference voxel(i) and neighbor voxel(j):
                    # Intratumor only: i and j both must be in tumor ROI
                    # Tumor+Surrounding: i must be in tumor ROI but J does not have to be
                    if row >= 0 and row < rows and col >= 0 and col < cols:
                        if tuple((height, col, row)) in indices:
                            j = matrix[height, col, row]
                            j_idx = numpy.nonzero(grayLevels == j)
                            # if i >= grayLevels.min and i <= grayLevels.max and j >= grayLevels.min and j <= grayLevels.max:
                            out[i_idx, j_idx, distances_idx, angles_idx] += 1
            # Check if the user has cancelled the process
            if iteration % 10 == 0:
                self.checkStopProcessFunction()

        return (out)

    def EvaluateFeatures(self, printTiming=False, checkStopProcessFunction=None):
        # Remove all the keys that must not be evaluated
        for key in set(self.textureFeaturesGLCM.keys()).difference(self.keys):
            self.textureFeaturesGLCM[key] = None

        if not self.keys:
            if not printTiming:
                return self.textureFeaturesGLCM
            else:
                return self.textureFeaturesGLCM, self.textureFeaturesGLCMTiming
        # normalization step:
        self.CalculateCoefficients(printTiming)

        if not printTiming:
            # Evaluate dictionary elements corresponding to user selected keys
            for key in self.keys:
                self.textureFeaturesGLCM[key] = eval(self.textureFeaturesGLCM[key])
                if checkStopProcessFunction is not None:
                    checkStopProcessFunction()
            return self.textureFeaturesGLCM
        else:
            # Evaluate dictionary elements corresponding to user selected keys
            for key in self.keys:
                t1 = time.time()
                self.textureFeaturesGLCM[key] = eval(self.textureFeaturesGLCM[key])
                self.textureFeaturesGLCMTiming[key] = time.time() - t1
                if checkStopProcessFunction is not None:
                    checkStopProcessFunction()
            return self.textureFeaturesGLCM, self.textureFeaturesGLCMTiming

