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

// MyParticlesDisplay Logic includes
#include "vtkSlicerParticlesDisplayLogic.h"

// MRML includes
#include <cipChestConventions.h>

#include <vtkMRMLParticlesNode.h>
#include <vtkMRMLParticlesDisplayNode.h>
#include <vtkMRMLModelStorageNode.h>
#include <vtkMRMLScene.h>

// VTK includes
#include <vtkObjectFactory.h>
#include <vtkNew.h>
#include <vtkImageData.h>
#include <vtkImageThreshold.h>
#include <vtkSmartPointer.h>
#include <vtkWeakPointer.h>

// STD includes
#include <itksys/SystemTools.hxx>
#include <itksys/Directory.hxx>

#include <cassert>
#include <iostream>

//----------------------------------------------------------------------------
class vtkSlicerParticlesDisplayLogic::vtkInternal
{
public:
  vtkInternal();
};

//----------------------------------------------------------------------------
vtkSlicerParticlesDisplayLogic::vtkInternal::vtkInternal()
{
}

//----------------------------------------------------------------------------
vtkStandardNewMacro(vtkSlicerParticlesDisplayLogic);

//----------------------------------------------------------------------------
vtkSlicerParticlesDisplayLogic::vtkSlicerParticlesDisplayLogic()
{
  this->Internal = new vtkInternal;
}

//----------------------------------------------------------------------------
vtkSlicerParticlesDisplayLogic::~vtkSlicerParticlesDisplayLogic()
{
  delete this->Internal;
}

//----------------------------------------------------------------------------
void vtkSlicerParticlesDisplayLogic::PrintSelf(ostream& os, vtkIndent indent)
{
  this->Superclass::PrintSelf(os, indent);
  os << indent << "vtkSlicerParticlesDisplayLogic:             " << this->GetClassName() << "\n";
}

//---------------------------------------------------------------------------
void vtkSlicerParticlesDisplayLogic::SetMRMLSceneInternal(vtkMRMLScene * newScene)
{
  vtkNew<vtkIntArray> events;
  events->InsertNextValue(vtkMRMLScene::NodeAddedEvent);
  events->InsertNextValue(vtkMRMLScene::NodeRemovedEvent);
  events->InsertNextValue(vtkMRMLScene::EndBatchProcessEvent);
  this->SetAndObserveMRMLSceneEventsInternal(newScene, events.GetPointer());
}

//-----------------------------------------------------------------------------
void vtkSlicerParticlesDisplayLogic::RegisterNodes()
{
  if(!this->GetMRMLScene())
  {
    return;
  }
  this->GetMRMLScene()->RegisterNodeClass(vtkSmartPointer<vtkMRMLParticlesNode>::New());
  this->GetMRMLScene()->RegisterNodeClass(vtkSmartPointer<vtkMRMLParticlesDisplayNode>::New());
}

//---------------------------------------------------------------------------
void vtkSlicerParticlesDisplayLogic::UpdateFromMRMLScene()
{
  assert(this->GetMRMLScene() != 0);
}

//---------------------------------------------------------------------------
void vtkSlicerParticlesDisplayLogic
::OnMRMLSceneNodeAdded(vtkMRMLNode* vtkNotUsed(node))
{
}

//---------------------------------------------------------------------------
void vtkSlicerParticlesDisplayLogic
::OnMRMLSceneNodeRemoved(vtkMRMLNode* vtkNotUsed(node))
{
}

//----------------------------------------------------------------------------
vtkMRMLParticlesNode* vtkSlicerParticlesDisplayLogic::AddParticlesNode (const char* filename)
{
  vtkDebugMacro("Adding particles from filename " << filename);

  vtkNew<vtkMRMLParticlesNode> particlesNode;
  vtkNew<vtkMRMLParticlesDisplayNode> particlesDisplayNode;
  vtkNew<vtkMRMLModelStorageNode> storageNode;

  storageNode->SetFileName(filename);
  if (storageNode->ReadData(particlesNode.GetPointer()) != 0)
    {
    const std::string fname(filename);
    std::string name = itksys::SystemTools::GetFilenameWithoutExtension(fname);
    std::string uname( this->GetMRMLScene()->GetUniqueNameByString(name.c_str()));
    particlesNode->SetName(uname.c_str());

    particlesDisplayNode->SetVisibility(1);
    particlesNode->SetScene(this->GetMRMLScene());
    storageNode->SetScene(this->GetMRMLScene());
    particlesDisplayNode->SetScene(this->GetMRMLScene());

    std::vector<std::string> scalars;
    particlesNode->GetAvailableScalarNames(scalars);
    if (scalars.size())
      {
      particlesDisplayNode->SetParticlesColorBy(scalars[0].c_str());
      }

    this->GetMRMLScene()->SaveStateForUndo();

    this->GetMRMLScene()->AddNode(storageNode.GetPointer());
    this->GetMRMLScene()->AddNode(particlesDisplayNode.GetPointer());

    particlesNode->SetAndObserveStorageNodeID(storageNode->GetID());

    particlesNode->SetAndObserveDisplayNodeID(particlesDisplayNode->GetID());

    this->GetMRMLScene()->AddNode(particlesNode.GetPointer());
    return particlesNode.GetPointer();
    }
  else
    {
    vtkErrorMacro("Couldn't read file, returning null particles node: " << filename);
    }
  return 0;
}
