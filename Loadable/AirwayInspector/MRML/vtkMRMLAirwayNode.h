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

#include "vtkMRMLNode.h"
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
  /// Get/Set for Point
  vtkSetVector3Macro(XYZ,float);
  vtkGetVectorMacro(XYZ,float,3);

  ///
  /// Get/Set for orientation
  vtkSetVector4Macro(OrientationWXYZ,float);
  vtkGetVectorMacro(OrientationWXYZ,float,4);
  //void SetOrientationWXYZFromMatrix4x4(vtkMatrix4x4 *mat);

  /// Get/Set Threshold
  vtkSetMacro(Threshold, int);
  vtkGetMacro(Threshold, int);

protected:
  vtkMRMLAirwayNode();
  ~vtkMRMLAirwayNode();
  vtkMRMLAirwayNode(const vtkMRMLAirwayNode&);
  void operator=(const vtkMRMLAirwayNode&);

private:
  /// Data
  float XYZ[3];
  float OrientationWXYZ[4];
  double Threshold;
  char *VolumeNodeID;
};

#endif
