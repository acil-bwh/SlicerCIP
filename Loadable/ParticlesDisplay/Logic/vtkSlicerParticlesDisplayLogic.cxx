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

#include <vtkMRMLParticlesDisplayNode.h>
#include <vtkMRMLScene.h>

// VTK includes
#include <vtkObjectFactory.h>
#include <vtkNew.h>
#include <vtkImageData.h>
#include <vtkImageThreshold.h>
#include <vtkSmartPointer.h>
#include <vtkWeakPointer.h>

// STD includes
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
  vtkMRMLParticlesDisplayNode* pdNode = vtkMRMLParticlesDisplayNode::New();
  this->GetMRMLScene()->RegisterNodeClass(pdNode);

  pdNode->Delete();
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

