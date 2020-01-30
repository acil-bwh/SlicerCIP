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

// .NAME vtkSlicerParticlesDisplayLogic - slicer logic class for volumes manipulation
// .SECTION Description
// This class manages the logic associated with reading, saving,
// and changing propertied of the volumes

#ifndef __vtkSlicerParticlesDisplayLogic_h
#define __vtkSlicerParticlesDisplayLogic_h

// Slicer includes
#include "vtkSlicerModuleLogic.h"

// MRML includes
#include "vtkMRML.h"
#include "vtkMRMLVolumeNode.h"

// STD includes
#include <cstdlib>

#include "vtkSlicerParticlesDisplayModuleLogicExport.h"

class vtkSlicerVolumesLogic;
class vtkMRMLParticlesNode;
class vtkMRMLParticlesDisplayNode;

/// \ingroup Slicer_QtModules_ExtensionTemplate
class VTK_SLICER_PARTICLESDISPLAY_MODULE_LOGIC_EXPORT vtkSlicerParticlesDisplayLogic :
  public vtkSlicerModuleLogic
{
public:

  static vtkSlicerParticlesDisplayLogic *New();
  vtkTypeMacro(vtkSlicerParticlesDisplayLogic, vtkSlicerModuleLogic);
  void PrintSelf(ostream& os, vtkIndent indent) override;

  // Description:
  // Create new mrml fiber bundle node and read its polydata from a specified file.
  // Also create the logic object for its display.
  vtkMRMLParticlesNode* AddParticlesNode (const char* filename);

protected:
  vtkSlicerParticlesDisplayLogic();
  virtual ~vtkSlicerParticlesDisplayLogic();

  virtual void SetMRMLSceneInternal(vtkMRMLScene* newScene) override;
  /// Register MRML Node classes to Scene. Gets called automatically when the MRMLScene is attached to this logic class.
  virtual void RegisterNodes() override;
  virtual void UpdateFromMRMLScene() override;
  virtual void OnMRMLSceneNodeAdded(vtkMRMLNode* node) override;
  virtual void OnMRMLSceneNodeRemoved(vtkMRMLNode* node) override;
private:

  vtkSlicerParticlesDisplayLogic(const vtkSlicerParticlesDisplayLogic&); // Not implemented
  void operator=(const vtkSlicerParticlesDisplayLogic&);               // Not implemented
  class vtkInternal;
  vtkInternal* Internal;
};

#endif
