/*==============================================================================

  Program: 3D Slicer

  Portions (c) Copyright Brigham and Women's Hospital (BWH) All Rights Reserved.

  See COPYRIGHT.txt
  or http://www.slicer.org/copyright/copyright.txt for details.

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.

==============================================================================*/

#ifndef __vtkMRMLAirwayNode_h
#define __vtkMRMLAirwayNode_h

// Markups includes
#include "vtkSlicerAirwayInspectorModuleMRMLExport.h"

#include "vtkImageData.h"
#include "vtkPolyData.h"
#include "vtkEllipseFitting.h"

#include "vtkMRMLNode.h"
#include "vtkMRMLModelNode.h"

// VTK includes
#include <vtkSmartPointer.h>

class  VTK_SLICER_AIRWAYINSPECTOR_MODULE_MRML_EXPORT vtkMRMLAirwayNode : public vtkMRMLNode
{
public:
  static vtkMRMLAirwayNode *New();
  vtkTypeMacro(vtkMRMLAirwayNode,vtkMRMLNode);

  void PrintSelf(ostream& os, vtkIndent indent);

  virtual const char* GetIcon() {return "";};

  //--------------------------------------------------------------------------
  // MRMLNode methods
  //--------------------------------------------------------------------------

  virtual vtkMRMLNode* CreateNodeInstance();

  /// Read node attributes from XML file
  virtual void ReadXMLAttributes( const char** atts);

  /// Write this node's information to a MRML file in XML format.
  virtual void WriteXML(ostream& of, int indent);

  /// Write this node's information to a vector of strings for passing to a CLI,
  /// precede each datum with the prefix if not an empty string
  /// coordinateSystemFlag = 0 for RAS, 1 for LPS
  /// multipleFlag = 1 for the whole list, 1 for the first selected markup
  virtual void WriteCLI(std::vector<std::string>& commandLine,
                        std::string prefix, int coordinateSystem = 0,
                        int multipleFlag = 1);

  /// Copy the node's attributes to this object
  virtual void Copy(vtkMRMLNode *node);

  ///
  /// Get node XML tag name (like Volume, Model)
  virtual const char* GetNodeTagName() {return "Airway";};

  /// Description:
  /// String ID of the volume MRML node
  vtkSetStringMacro(VolumeNodeID);
  vtkGetStringMacro(VolumeNodeID);

  ///
  /// Get/Set for user picked point
  vtkSetVector3Macro(XYZ,double);
  vtkGetVectorMacro(XYZ,double,3);

  ///
  /// Get/Set for computed center
  vtkSetVector3Macro(CenterXYZ,double);
  vtkGetVectorMacro(CenterXYZ,double,3);

  ///
  /// Get/Set for orientation
  vtkSetVector3Macro(XAxis,double);
  vtkGetVectorMacro(XAxis,double,3);

  vtkSetVector3Macro(YAxis,double);
  vtkGetVectorMacro(YAxis,double,3);

  vtkSetVector3Macro(ZAxis,double);
  vtkGetVectorMacro(ZAxis,double,3);

  /// Get/Set Threshold
  vtkSetMacro(Threshold, int);
  vtkGetMacro(Threshold, int);

  // Description:
  // Reformat airway along airway long axis
  vtkBooleanMacro(Reformat,int);
  vtkSetMacro(Reformat,int);
  vtkGetMacro(Reformat,int);

  // Description:
  // Compute Center of reslice
  vtkBooleanMacro(ComputeCenter,int);
  vtkSetMacro(ComputeCenter,int);
  vtkGetMacro(ComputeCenter,int);

  // Description:
  // Compute Center of reslice
  vtkBooleanMacro(RefineCenter,int);
  vtkSetMacro(RefineCenter,int);
  vtkGetMacro(RefineCenter,int);

  // Description:
  // SegmentPercentage
  vtkSetMacro(SegmentPercentage,double);
  vtkGetMacro(SegmentPercentage,double);

  // Description:
  // AirBaselineIntensity
  vtkSetMacro(AirBaselineIntensity,double);
  vtkGetMacro(AirBaselineIntensity,double);

  // Description:
  // Resolution
  vtkSetMacro(Resolution,double);
  vtkGetMacro(Resolution,double);

  // Description:
  // Axis computation model:
  // 0 = Hessian.
  // 1 = from vktPolyData line.
  // 2 = from Vector field in PolyData pointData.
  vtkSetMacro(AxisMode,int);
  vtkGetMacro(AxisMode,int);
  void SetAxisModeToHessian() {this->SetAxisMode(HESSIAN);};
  void SetAxisModeToPolyData() {this->SetAxisMode(POLYDATA);};
  void SetAxisModeToVector() {this->SetAxisMode(VECTOR);};

  // Description:
  // Reconstruction kernel from image
  // 0 = Smooth
  // 1 = Sharp
  vtkSetMacro(Reconstruction,int);
  vtkGetMacro(Reconstruction,int);
  void SetReconstructionToSmooth() {this->SetReconstruction(SMOOTH);};
  void SetReconstructionToSharp() {this->SetReconstruction(SHARP);};

  // Description:
  // Reconstruction method
  // 0 = FWHM
  // 1 = ZeroCrossing
  // 2 = PhaseCongruency
  // 3 = PhaseCongruencyMultipleKernels
  vtkSetMacro(Method,int);
  vtkGetMacro(Method,int);
  void SetMethodToFWHM() {this->SetMethod(FWHM);};
  void SetMethodToZeroCrossing() {this->SetMethod(ZeroCrossing);};
  void SetMethodToPhaseCongruency() {this->SetMethod(PhaseCongruency);};
  void SetMethodToPhaseCongruencyMultipleKernels() {this->SetMethod(PhaseCongruencyMultipleKernels);};

  // Description:
  // Save a png image with the airway segmentation results for quality control
  vtkBooleanMacro(SaveAirwayImage,int);
  vtkSetMacro(SaveAirwayImage,int);
  vtkGetMacro(SaveAirwayImage,int);

  // Description:
  // File prefix for the airway image
  vtkSetStringMacro(AirwayImagePrefix);
  vtkGetStringMacro(AirwayImagePrefix);

  vtkGetObjectMacro(AirwayImage, vtkImageData);
  vtkSetObjectMacro(AirwayImage, vtkImageData);

  vtkGetObjectMacro(InnerContour, vtkPolyData);
  vtkSetObjectMacro(InnerContour, vtkPolyData);

  vtkGetObjectMacro(OuterContour, vtkPolyData);
  vtkSetObjectMacro(OuterContour, vtkPolyData);

  vtkDoubleArray* GetMean(int methodName);
  vtkDoubleArray* GetStd(int methodName);
  vtkDoubleArray* GetMin(int methodName);
  vtkDoubleArray* GetMax(int methodName);

  void SetMean(int methodName, vtkDoubleArray* values);
  void SetStd(int methodName, vtkDoubleArray* values);
  void SetMin(int methodName, vtkDoubleArray* values);
  void SetMax(int methodName, vtkDoubleArray* values);

  vtkGetObjectMacro(Ellipse, vtkDoubleArray);

  vtkEllipseFitting* GetEllipseInside(int methodName);
  vtkEllipseFitting* GetEllipseOutside(int methodName);
  void SetEllipseOutside(int methodName,vtkEllipseFitting* value);
  void SetEllipseInside(int methodName,vtkEllipseFitting* value);

  enum AxisMode { HESSIAN, POLYDATA, VECTOR};
  enum ReconstructionMode {SMOOTH, SHARP};
  enum Method { FWHM, ZeroCrossing, PhaseCongruency, PhaseCongruencyMultipleKernels};

protected:
  vtkMRMLAirwayNode();
  ~vtkMRMLAirwayNode();
  vtkMRMLAirwayNode(const vtkMRMLAirwayNode&);
  void operator=(const vtkMRMLAirwayNode&);

private:
  /// Data
  double XYZ[3];
  double CenterXYZ[3];
  double XAxis[3];
  double YAxis[3];
  double ZAxis[3];
  double Threshold;
  char *VolumeNodeID;

  double Resolution;
  int    Reformat;
  int    AxisMode;
  int    ComputeCenter;
  int    RefineCenter;
  int    Reconstruction;
  int    Method;
  double SegmentPercentage;
  int    SaveAirwayImage;
  char   *AirwayImagePrefix;

  double AirBaselineIntensity;

  vtkImageData *AirwayImage;
  vtkPolyData  *InnerContour;
  vtkPolyData  *OuterContour;
  std::map<int, vtkDoubleArray*> Mean;
  std::map<int, vtkDoubleArray*> Std;
  std::map<int, vtkDoubleArray*> Min;
  std::map<int, vtkDoubleArray*> Max;
  vtkDoubleArray *Ellipse;

  std::map<int, vtkEllipseFitting*> EllipseInside;
  std::map<int, vtkEllipseFitting*> EllipseOutside;
};

#endif
