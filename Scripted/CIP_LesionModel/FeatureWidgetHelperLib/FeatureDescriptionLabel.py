from __main__ import vtk, qt, ctk, slicer
import string


class FeatureDescriptionLabel(qt.QLabel):
  def __init__(self, parent=None):
    super(FeatureDescriptionLabel, self).__init__(parent)
    
    self.setFixedWidth(300)
    self.setFrameStyle(qt.QFrame.Box)
    self.setWordWrap(True) 
  
  def setDescription(self, featureName):
    self.description = featureName + ' Description:\n\n' 
    
    # First-Order Statistics
    if featureName == "Voxel Count":
      self.description += "Voxel Count is the total number of voxels within the ROI of the grayscale image or parameter map."
    elif featureName == "Gray Levels":
      self.description += "Gray Levels is a the number of discrete voxel values within the ROI of the grayscale image or parameter map."  
    elif featureName == "Energy":
      self.description += "Energy is a measure of the magnitude of values in an image. A greater amount larger values implies a greater sum of the squares of these values."
    elif featureName == "Entropy":
      self.description += "Entropy of the image histogram specifies the uncertainty in the image values. It measures the average amount of information required to encode the image values."
    elif featureName == "Minimum Intensity":
      self.description += "Minimum Intensity is the value of the voxel(s) in the image ROI with the least value."
    elif featureName == "Maximum Intensity":
      self.description += "Maximum Intensity is the value of the voxel(s) in the image ROI with the greatest value."
    elif featureName == "Mean Intensity":
      self.description += "Mean Intensity is the mean of the intensity or parameter values within the image ROI."
    elif featureName == "Median Intensity":
      self.description += "Median Intensity is the median of the intensity or parameter values within the image ROI."
    elif featureName == "Range":
      self.description += "Range is the difference between the highest and lowest voxel values within the image ROI."
    elif featureName == "Mean Deviation":
      self.description += "Mean Deviation is the mean of the distances of each image value from the mean of all the values in the image ROI."
    elif featureName == "Root Mean Square":
      self.description += "Root Mean Square is the square-root of the mean of the squares of the values in the image ROI. It is another measure of the magnitude of the image values."
    elif featureName == "Standard Deviation":
      self.description += "Standard Deviation measures the amount of variation or dispersion from the mean of the image values"
    elif featureName == "Skewness":
      self.description += "Skewness measures the asymmetry of the distribution of values in the image ROI about the mean of the values. Depending on where the tail is elongated and the mass of the distribution is concentrated, this value can be positive or negative."
    elif featureName == "Kurtosis":
      self.description += "Kurtosis is a measure of the 'peakedness' of the distribution of values in the image ROI. A higher kurtosis implies that the mass of the distribution is concentrated towards the tail(s) rather than towards the mean. A lower kurtosis implies the reverse, that the mass of the distribution is concentrated towards a spike the mean."
    elif featureName == "Variance":
      self.description += "Variance is the mean of the squared distances of each value in the image ROI from the mean of the values. This is a measure of the spread of the distribution about the mean."
    elif featureName == "Uniformity":
      self.description += "Uniformity is a measure of the sum of the squares of each discrete value in the image ROI. This is a measure of the heterogeneity of an image, where a greater uniformity implies a greater heterogeneity or a greater range of discrete image values."
    
    # Morphology and Shape features
    elif featureName == "Volume mm^3":
      self.description += "The volume of the specified ROI of the image in cubic millimeters."
    elif featureName == "Volume cc":
      self.description += "The volume of the specified ROI of the image in cubic centimeters."
    elif featureName == "Surface Area":
      self.description += "The surface area of the specified ROI of the image in square millimeters."
    elif featureName == "Surface:Volume Ratio":
      self.description += "The ratio of the surface area (square millimeters) to the volume (cubic millimeters) of the specified image ROI."
    elif featureName == "Compactness 1":
      self.description += "Compactness 1 is a dimensionless measure, independent of scale and orientation. Compactness 1 is defined as the ratio of volume to the (surface area)^(1.5). This is a measure of the compactness of the shape of the image ROI."
    elif featureName == "Compactness 2":
      self.description += "Compactness 2 is a dimensionless measure, independent of scale and orientation. This is a measure of the compactness of the shape of the image ROI."
    elif featureName == "Maximum 3D Diameter":
      self.description += "Maximum 3D Diameter is the maximum, pairwise euclidean distance between surface voxels of the image ROI."
    elif featureName == "Spherical Disproportion":
      self.description += "Spherical Disproportion is defined as the ratio of the surface area of the image ROI to the surface area of a sphere with the same volume as the image ROI."
    elif featureName == "Sphericity":
      self.description += "Sphericity is a measure of the roundness or spherical nature of the image ROI, where the sphericity of a sphere is the maximum value of 1."
    
    # Gray-Level Co-ocurrence Matrices (GLCM)
    elif featureName == "Autocorrelation":
      self.description += "Autocorrelation is a measure of the magnitude of the fineness and coarseness of texture."
    elif featureName == "Cluster Prominence":
      self.description += "Cluster Prominence is a measure of the skewness and asymmetry of the GLCM. A higher values implies more asymmetry about the mean value while a lower value indicates a peak around the mean value and less variation about the mean."
    elif featureName == "Cluster Shade":
      self.description += "Cluster Shade is a measure of the skewness and uniformity of the GLCM. A higher cluster shade implies greater asymmetry."
    elif featureName == "Cluster Tendency":
      self.description += "Cluster Tendency indicates the number of potential clusters present in the image."
    elif featureName == "Contrast":
      self.description += "Contrast is a measure of the local intensity variation, favoring P(i,j) values away from the diagonal (i != j), with a larger value correlating with larger image variation."
    elif featureName == "Correlation":
      self.description += "Correlation is a value between 0 (uncorrelated) and 1 (perfectly correlated) showing the linear dependency of gray level values in the GLCM. For a symfeatureal GLCM, ux = uy (means of px and py) and sigx = sigy (standard deviations of px and py)."
    elif featureName == "Difference Entropy":
      self.description += "Difference Entropy is.."
    elif featureName == "Dissimilarity":
      self.description += "Dissimilarity is.."
    elif featureName == "Energy (GLCM)":
      self.description += "Energy (for GLCM) is also the Angular Second Moment and is a measure of the homogeneity of an image. A homogeneous image will contain less discrete gray levels, producing a GLCM with fewer but relatively greater values of P(i,j), and a greater sum of the squares."   
    elif featureName == "Entropy (GLCM)":
      self.description += "Entropy (GLCM) indicates the uncertainty of the GLCM. It measures the average amount of information required to encode the image values."
    elif featureName == "Homogeneity 1":
      self.description += "Homogeneity 1 is a measure of local homogeneity that increases with less contrast in the window."
    elif featureName == "Homogeneity 2":
      self.description += "Homogeneity 2 is a measure of local homogeneity."
    elif featureName == "IMC1":
      self.description += "Informational Measure of Correlation 1 (IMC1) is.."
    elif featureName == "IMC2":
      self.description += "Informational Measure of Correlation 2 (IMC2) is.."
    elif featureName == "IDMN":
      self.description += "Inverse Difference Moment Normalized (IDMN) is a measure of the local homogeneity of an image. IDMN weights are the inverse of the Contrast weights (decreasing exponentially from the diagonal i=j in the GLCM). Unlike Homogeneity 2, IDMN normalizes the square of the difference between values by dividing over the square of the total number of discrete values."
    elif featureName == "IDN":
      self.description += "Inverse Difference Normalized (IDN) is another measure of the local homogeneity of an image. Unlike Homogeneity 1, IDN normalizes the difference between the values by dividing over the total number of discrete values."
    elif featureName == "Inverse Variance":
      self.description += "Inverse Variance is.."
    elif featureName == "Maximum Probability":
      self.description += "Maximum Probability is.."
    elif featureName == "Sum Average":
      self.description += "Sum Average is.."
    elif featureName == "Sum Entropy":
      self.description += "Sum Entropy is.."
    elif featureName == "Sum Variance":
      self.description += "Sum Variance weights elements that differ from the average value of the GLCM."
    elif featureName == "Variance (GLCM)":
      self.description += "Variance (for GLCM) is the dispersion of the parameter values around the mean of the combinations of reference and neighborhood pixels, with values farther from the mean weighted higher. A high variance indicates greater distances of values from the mean."
    
    # Gray-Level Run Length (GLRL) Matrices
    elif featureName == "SRE":
     self.description +="Short Run Emphasis (SRE) is a measure of the distribution of short run lengths, with a greater value indicative of shorter run lengths and more fine textural textures."    
    elif featureName == "LRE":
      self.description +="Long Run Emphasis (LRE) is a measure of the distribution of long run lengths, with a greater value indicative of longer run lengths and more coarse structural textures."
    elif featureName == "GLN":
      self.description +="Gray Level Non-Uniformity (GLN) measures the similarity of gray-level intensity values in the image, where a lower GLN value correlates with a greater similarity in intensity values."   
    elif featureName == "RLN":
      self.description +="Run Length Non-Uniformity (RLN) measures the similarity of run lengths throughout the image, with a lower value indicating more homogeneity among run lengths in the image."     
    elif featureName == "RP":
      self.description +="Run Percentage (RP) measures the homogeneity and distribution of runs of an image for a certain direction."     
    elif featureName == "LGLRE":
      self.description +="Low Gray Level Run Emphasis (LGLRE) measures the distribution of low gray-level values, with a higher value indicating a greater concentration of low gray-level values in the image."     
    elif featureName == "HGLRE":
      self.description +="High Gray Level Run Emphasis (HGLRE) measures the distribution of the higher gray-level values, with a higher value indicating a greater concentration of high gray-level values in the image."     
    elif featureName == "SRLGLE":
      self.description +="Short Run Low Gray Level Emphasis (SRLGLE) measures the joint distribution of shorter run lengths with lower gray-level values." 
    elif featureName == "SRHGLE":
      self.description +="Short Run High Gray Level Emphasis (SRHGLE)E) measures the joint distribution of shorter run lengths with higher gray-level values."    
    elif featureName == "LRLGLE":
      self.description +="Long Run Low Gray Level Emphasis (LRLGLE) measures the joint distribution of long run lengths with lower gray-level values."   
    elif featureName == "LRHGLE":
      self.description +="Long Run High Gray Level Emphasis (LRHGLE) measures the joint distribution of long run lengths with higher gray-level values."
      
    # Renyi Dimensions
    elif featureName == "Box-Counting Dimension":
      self.description += "Box-Counting Dimension is part of the family of Renyi Dimensions, where q=0 for Renyi Entropy calculations. This represents the fractal dimension: the slope of the curve on a plot of log(N) vs. log(1/s) where 'N' is the number of boxes occupied by the image ROI at each scale, 's', of an overlaid grid."
    elif featureName == "Information Dimension":
      self.description += "Information Dimension is part of the family of Renyi Dimensions, where q=1 for Renyi Entropy calculations."
    elif featureName == "Correlation Dimension":
      self.description += "Correlation Dimension is part of the family of Renyi Dimensions, where q=2 for Renyi Entropy calculations."
    
    # Geometrical Measures
    elif featureName == "Extruded Surface Area":
      self.description += "Extruded Surface Area is the surface area of the binary object when the image ROI is 'extruded' into 4D, where the parameter or intensity value defines the shape of the Fourth dimension."   
    elif featureName == "Extruded Volume":
      self.description += "Extruded Volume is the volume of the binary object when the image ROI is 'extruded' into 4D, where the parameter or intensity value defines the shape of the Fourth dimension."
    elif featureName == "Extruded Surface:Volume Ratio":
      self.description += "Extruded Surface:Volume Ratio is the ratio of the surface area to the volume of the binary object when the image ROI is 'extruded' into 4D, where the parameter or intensity value defines the shape of the Fourth dimension."
    
    self.setText(self.description) 
     
        
class FeatureClassDescriptionLabel(qt.QLabel):
  def __init__(self, parent=None):
    super(FeatureClassDescriptionLabel, self).__init__(parent)
    
    self.setFixedWidth(300)
    self.setFrameStyle(qt.QFrame.Box)
    self.setWordWrap(True) 
  
  def setDescription(self, featureClassName):
    self.description = featureClassName + ' Description:\n\n' 
    
    if featureClassName == "First-Order Statistics":
      self.description += "First-Order Statistics based on a Histogram Distribution Summary"
      
    elif featureClassName == "Morphology and Shape":
      self.description += "3-Dimensional features based on Volume and Surface-Area"
        
    elif featureClassName == "Texture: GLCM":
      self.description += "Edit parameters for or Toggle the generation of Gray-Level Co-ocurrence Matrices (GLCM) needed to calculate features for this class. If this is unchecked, there will be no features computed for this Feature Class."
        
    elif featureClassName == "Texture: GLRL":
     self.description +="Edit parameters for or Toggle the generation of Gray-Level Run Length (GLRL) matrices needed to calculate features for this class. If this is unchecked, there will be no features computed for this Feature Class."
      
    elif featureClassName == "Renyi Dimensions":
      self.description += "Renyi Dimensions also known as Fractal Dimensions"
      
    elif featureClassName == "Geometrical Measures":
      self.description += "Edit parameters for or Toggle the generation of the extruded, binary 4D object needed to calculate features for this class. If this is unchecked, there will be no features computed for this Feature Class." 
    
    self.setText(self.description)     
    
