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

// .NAME vtkSlicerMyRegionTypeLogic - slicer logic class for volumes manipulation
// .SECTION Description
// This class manages the logic associated with reading, saving,
// and changing propertied of the volumes


#ifndef __vtkSlicerMyRegionTypeLogic_h
#define __vtkSlicerMyRegionTypeLogic_h

// Slicer includes
#include "vtkSlicerModuleLogic.h"

// MRML includes
#include "vtkMRML.h"
#include "vtkMRMLVolumeNode.h"

// STD includes
#include <cstdlib>

#include "vtkSlicerMyRegionTypeModuleLogicExport.h"

class vtkSlicerVolumesLogic;
class vtkMRMLMyRegionTypeNode;
class vtkMRMLScalarVolumeDisplayNode;
class vtkMRMLVolumeHeaderlessStorageNode;
//class vtkStringArray;

/// \ingroup Slicer_QtModules_ExtensionTemplate
class VTK_SLICER_MYREGIONTYPE_MODULE_LOGIC_EXPORT vtkSlicerMyRegionTypeLogic :
  public vtkSlicerModuleLogic
{
public:

  static vtkSlicerMyRegionTypeLogic *New();
  vtkTypeMacro(vtkSlicerMyRegionTypeLogic, vtkSlicerModuleLogic);
  void PrintSelf(ostream& os, vtkIndent indent);

  void SetVolumesLogic(vtkSlicerVolumesLogic* logic);
  vtkSlicerVolumesLogic* GetVolumesLogic();

  void DisplaySelectedRegionType(vtkMRMLMyRegionTypeNode*, const char*, const char*);
  void DisplayAllRegionType(vtkMRMLMyRegionTypeNode*);

  //int Apply(vtkMRMLRegionTypeNode*);

protected:
  vtkSlicerMyRegionTypeLogic();
  virtual ~vtkSlicerMyRegionTypeLogic();

  virtual void SetMRMLSceneInternal(vtkMRMLScene* newScene);
  /// Register MRML Node classes to Scene. Gets called automatically when the MRMLScene is attached to this logic class.
  virtual void RegisterNodes();
  virtual void UpdateFromMRMLScene();
  virtual void OnMRMLSceneNodeAdded(vtkMRMLNode* node);
  virtual void OnMRMLSceneNodeRemoved(vtkMRMLNode* node);
private:

  vtkSlicerMyRegionTypeLogic(const vtkSlicerMyRegionTypeLogic&); // Not implemented
  void operator=(const vtkSlicerMyRegionTypeLogic&);               // Not implemented
  class vtkInternal;
  vtkInternal* Internal;
  vtkSmartPointer<vtkMRMLVolumeNode> ActiveVolumeNode;

};

#endif
