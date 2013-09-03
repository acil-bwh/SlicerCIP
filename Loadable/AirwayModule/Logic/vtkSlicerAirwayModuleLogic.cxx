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

// AirwayModule Logic includes
#include "vtkSlicerAirwayModuleLogic.h"

// MRML includes
#include "vtkMRMLAirwayNode.h"
#include "vtkMRMLAirwayDisplayNode.h"
#include "vtkMRMLAirwayStorageNode.h"

// VTK includes
#include <vtkNew.h>
#include <vtkPolyData.h>

#include <itksys/SystemTools.hxx> 
#include <itksys/Directory.hxx> 

// STD includes
#include <cassert>

//----------------------------------------------------------------------------
vtkStandardNewMacro(vtkSlicerAirwayModuleLogic);

//----------------------------------------------------------------------------
vtkSlicerAirwayModuleLogic::vtkSlicerAirwayModuleLogic()
{
}

//----------------------------------------------------------------------------
vtkSlicerAirwayModuleLogic::~vtkSlicerAirwayModuleLogic()
{
}

//----------------------------------------------------------------------------
void vtkSlicerAirwayModuleLogic::PrintSelf(ostream& os, vtkIndent indent)
{
  this->Superclass::PrintSelf(os, indent);
}

//---------------------------------------------------------------------------
void vtkSlicerAirwayModuleLogic::SetMRMLSceneInternal(vtkMRMLScene * newScene)
{
  vtkNew<vtkIntArray> events;
  events->InsertNextValue(vtkMRMLScene::NodeAddedEvent);
  events->InsertNextValue(vtkMRMLScene::NodeRemovedEvent);
  events->InsertNextValue(vtkMRMLScene::EndBatchProcessEvent);
  this->SetAndObserveMRMLSceneEventsInternal(newScene, events.GetPointer());
}

//-----------------------------------------------------------------------------
void vtkSlicerAirwayModuleLogic::RegisterNodes()
{
  if(!this->GetMRMLScene())
    {
    return;
    }
  this->GetMRMLScene()->RegisterNodeClass(vtkNew<vtkMRMLAirwayNode>().GetPointer());
  this->GetMRMLScene()->RegisterNodeClass(vtkNew<vtkMRMLAirwayDisplayNode>().GetPointer());
  this->GetMRMLScene()->RegisterNodeClass(vtkNew<vtkMRMLAirwayStorageNode>().GetPointer());
}

//---------------------------------------------------------------------------
void vtkSlicerAirwayModuleLogic::UpdateFromMRMLScene()
{
  assert(this->GetMRMLScene() != 0);
}

//---------------------------------------------------------------------------
void vtkSlicerAirwayModuleLogic
::OnMRMLSceneNodeAdded(vtkMRMLNode* vtkNotUsed(node))
{
}

//---------------------------------------------------------------------------
void vtkSlicerAirwayModuleLogic
::OnMRMLSceneNodeRemoved(vtkMRMLNode* vtkNotUsed(node))
{
}

//----------------------------------------------------------------------------
int vtkSlicerAirwayModuleLogic::AddAirways (const char* dirname, const char* suffix )
{
  std::string ssuf = suffix;
  itksys::Directory dir;
  dir.Load(dirname);
 
  int nfiles = dir.GetNumberOfFiles();
  int res = 1;
  for (int i=0; i<nfiles; i++) {
    const char* filename = dir.GetFile(i);
    std::string sname = filename;
    if (!itksys::SystemTools::FileIsDirectory(filename))
      {
      if ( sname.find(ssuf) != std::string::npos )
        {
        std::string fullPath = std::string(dir.GetPath())
            + "/" + filename;
        if (this->AddAirway(fullPath.c_str()) == NULL)
          {
          res = 0;
          }
        }
      }
  }
  return res;
}

//----------------------------------------------------------------------------
int vtkSlicerAirwayModuleLogic::AddAirways (const char* dirname, std::vector< std::string > suffix )
{
  itksys::Directory dir;
  dir.Load(dirname);
 
  int nfiles = dir.GetNumberOfFiles();
  int res = 1;
  for (int i=0; i<nfiles; i++) {
    const char* filename = dir.GetFile(i);
    std::string sname = filename;
    if (!itksys::SystemTools::FileIsDirectory(filename))
      {
      for (unsigned int s=0; s<suffix.size(); s++)
        {
        std::string ssuf = suffix[s];
        if ( sname.find(ssuf) != std::string::npos )
          {
          std::string fullPath = std::string(dir.GetPath())
              + "/" + filename;
          if (this->AddAirway(fullPath.c_str()) == NULL)
            {
            res = 0;
            }
          } //if (sname
        } // for (int s=0;
      }
  }
  return res;
}

//----------------------------------------------------------------------------
vtkMRMLAirwayNode* vtkSlicerAirwayModuleLogic::AddAirway (const char* filename)
{
  vtkDebugMacro("Adding airway from filename " << filename);

  if (! this->GetMRMLScene() ) {
    vtkDebugMacro("MRML Scene of the logic is NULL!!!");
    return NULL;
  }

  vtkMRMLAirwayNode *airwayNode = vtkMRMLAirwayNode::New();
  vtkMRMLAirwayDisplayNode *displayNode = vtkMRMLAirwayDisplayNode::New();
  vtkMRMLAirwayStorageNode *storageNode = vtkMRMLAirwayStorageNode::New();

  storageNode->SetFileName(filename);
  if (storageNode->ReadData(airwayNode) != 0)
    {
    const itksys_stl::string fname(filename);
    itksys_stl::string name = itksys::SystemTools::GetFilenameWithoutExtension(fname);
    std::string uname( this->GetMRMLScene()->GetUniqueNameByString(name.c_str()));
    airwayNode->SetName(uname.c_str());
   
    airwayNode->SetScene(this->GetMRMLScene());
    storageNode->SetScene(this->GetMRMLScene());
    displayNode->SetScene(this->GetMRMLScene());
 
    displayNode->SetVisibility(1);

    this->GetMRMLScene()->SaveStateForUndo();

    this->GetMRMLScene()->AddNode(storageNode);
    this->GetMRMLScene()->AddNode(displayNode);

    airwayNode->SetAndObserveStorageNodeID(storageNode->GetID());
    displayNode->SetAndObserveColorNodeID("vtkMRMLColorTableNodeRainbow");

    airwayNode->SetAndObserveDisplayNodeID(displayNode->GetID());
    this->GetMRMLScene()->AddNode(airwayNode);
    displayNode->SetInputPolyData(airwayNode->GetPolyData());

    airwayNode->Delete();
    }
  else
    {
    vtkErrorMacro("Couldn't read file, returning null airway node: " << filename);
    airwayNode->Delete();
    airwayNode = NULL;
    }
  storageNode->Delete();
  displayNode->Delete();

  return airwayNode;  
}
//----------------------------------------------------------------------------
int vtkSlicerAirwayModuleLogic::SaveAirway (const char* filename, vtkMRMLAirwayNode *airwayNode)
{
   if (airwayNode == NULL || filename == NULL)
    {
    return 0;
    }
  
  vtkMRMLAirwayStorageNode *storageNode = NULL;
  vtkMRMLStorageNode *snode = airwayNode->GetStorageNode();
  if (snode != NULL)
    {
    storageNode = vtkMRMLAirwayStorageNode::SafeDownCast(snode);
    }
  if (storageNode == NULL)
    {
    storageNode = vtkMRMLAirwayStorageNode::New();
    storageNode->SetScene(this->GetMRMLScene());
    this->GetMRMLScene()->AddNode(storageNode);  
    airwayNode->SetAndObserveStorageNodeID(storageNode->GetID());
    storageNode->Delete();
    }

  //storageNode->SetAbsoluteFileName(true);
  storageNode->SetFileName(filename);

  int res = storageNode->WriteData(airwayNode);

  
  return res;

}

