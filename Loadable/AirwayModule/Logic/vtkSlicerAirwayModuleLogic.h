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

// .NAME vtkSlicerAirwayModuleLogic - slicer logic class for volumes manipulation
// .SECTION Description
// This class manages the logic associated with reading, saving,
// and changing propertied of the volumes


#ifndef __vtkSlicerAirwayModuleLogic_h
#define __vtkSlicerAirwayModuleLogic_h

// Slicer includes
#include "vtkSlicerModuleLogic.h"

// MRML includes

// STD includes
#include <cstdlib>
#include <vector>
#include <string>

#include "vtkSlicerAirwayModuleModuleLogicExport.h"

class vtkMRMLAirwayNode;

/// \ingroup Slicer_QtModules_ExtensionTemplate
class VTK_SLICER_AIRWAYMODULE_MODULE_LOGIC_EXPORT vtkSlicerAirwayModuleLogic :
  public vtkSlicerModuleLogic
{
public:

  static vtkSlicerAirwayModuleLogic *New();
  vtkTypeMacro(vtkSlicerAirwayModuleLogic, vtkSlicerModuleLogic);
  void PrintSelf(ostream& os, vtkIndent indent);

  /// Register MRML Node classes to Scene. Gets called automatically when the MRMLScene is attached to this logic class.
  virtual void RegisterNodes();
  virtual void UpdateFromMRMLScene();
  virtual void OnMRMLSceneNodeAdded(vtkMRMLNode* node);
  virtual void OnMRMLSceneNodeRemoved(vtkMRMLNode* node);

  // Description:
  // Create new mrml airway node and read its polydata from a specified file.
  // Also create the logic object for its display.
  vtkMRMLAirwayNode* AddAirway (const char* filename);

  // Description:
  // Create airway nodes and read their polydata from a specified directory.
  // Files matching suffix are read
  // Internally calls AddAirway for each file.
  int AddAirways (const char* dirname, const char* suffix );
  // Description:
  // Create airway nodes and read their polydata from a specified directory.
  // Files matching all suffixes are read
  // Internally calls AddAirway for each file.
  int AddAirways (const char* dirname, std::vector< std::string > suffix );
  // Description:
  // Write airway's polydata  to a specified file.
  int SaveAirway (const char* filename, vtkMRMLAirwayNode *airwayNode);

protected:
  vtkSlicerAirwayModuleLogic();
  virtual ~vtkSlicerAirwayModuleLogic();
  virtual void SetMRMLSceneInternal(vtkMRMLScene* newScene);
        
private:

  vtkSlicerAirwayModuleLogic(const vtkSlicerAirwayModuleLogic&); // Not implemented
  void operator=(const vtkSlicerAirwayModuleLogic&);               // Not implemented
};

#endif
