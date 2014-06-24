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

// MyRegionType Logic includes
#include "vtkSlicerMyRegionTypeLogic.h"
#include "vtkSlicerVolumesLogic.h"

// MRML includes
#include <vtkMRMLMyRegionTypeNode.h>
#include <vtkMRMLMyRegionTypeDisplayNode.h>
#include <vtkMRMLChestRTColorTableNode.h>

// VTK includes
#include <vtkNew.h>
#include <vtkImageData.h>
#include <vtkImageThreshold.h>
#include <vtkSmartPointer.h>
#include <vtkWeakPointer.h>

// STD includes
#include <cassert>
#include <iostream>

//----------------------------------------------------------------------------
class vtkSlicerMyRegionTypeLogic::vtkInternal
{
public:
  vtkInternal();

  vtkSlicerVolumesLogic* VolumesLogic;
};

//----------------------------------------------------------------------------
vtkSlicerMyRegionTypeLogic::vtkInternal::vtkInternal()
{
  this->VolumesLogic = 0;
}

//----------------------------------------------------------------------------
vtkStandardNewMacro(vtkSlicerMyRegionTypeLogic);

//----------------------------------------------------------------------------
vtkSlicerMyRegionTypeLogic::vtkSlicerMyRegionTypeLogic()
{
  this->Internal = new vtkInternal;
}

//----------------------------------------------------------------------------
vtkSlicerMyRegionTypeLogic::~vtkSlicerMyRegionTypeLogic()
{
  delete this->Internal;
}

//----------------------------------------------------------------------------
void vtkSlicerMyRegionTypeLogic::PrintSelf(ostream& os, vtkIndent indent)
{
  this->Superclass::PrintSelf(os, indent);
  os << indent << "vtkSlicerMyRegionTypeLogic:             " << this->GetClassName() << "\n";
}

//-----------------------------------------------------------------------------
void vtkSlicerMyRegionTypeLogic::DisplaySelectedRegionType(vtkMRMLMyRegionTypeNode* rtNode, const char* reg, const char* typ)
{
  if (!rtNode) 
  {
	  return;
  }

  this->GetMRMLScene()->StartState(vtkMRMLScene::BatchProcessState);

  vtkMRMLMyRegionTypeDisplayNode* displayNode = vtkMRMLMyRegionTypeDisplayNode::SafeDownCast( rtNode->GetDisplayNode() );
  displayNode->ShowSelectedLabels(rtNode, reg, typ);

  this->GetMRMLScene()->EndState(vtkMRMLScene::BatchProcessState);
}

//---------------------------------------------------------------------------
void vtkSlicerMyRegionTypeLogic::DisplayAllRegionType(vtkMRMLMyRegionTypeNode* rtNode)
{
  if (!rtNode) 
  {
	  return;
  }
  
  this->GetMRMLScene()->StartState(vtkMRMLScene::BatchProcessState);

  vtkMRMLMyRegionTypeDisplayNode* displayNode = vtkMRMLMyRegionTypeDisplayNode::SafeDownCast( rtNode->GetDisplayNode() );
  displayNode->ShowAllRegions();
  displayNode->ShowAllTypes();

  this->GetMRMLScene()->EndState(vtkMRMLScene::BatchProcessState);
}

//---------------------------------------------------------------------------
void vtkSlicerMyRegionTypeLogic::SetMRMLSceneInternal(vtkMRMLScene * newScene)
{
  vtkNew<vtkIntArray> events;
  events->InsertNextValue(vtkMRMLScene::NodeAddedEvent);
  events->InsertNextValue(vtkMRMLScene::NodeRemovedEvent);
  events->InsertNextValue(vtkMRMLScene::EndBatchProcessEvent);
  this->SetAndObserveMRMLSceneEventsInternal(newScene, events.GetPointer());
}

//----------------------------------------------------------------------------
void vtkSlicerMyRegionTypeLogic::SetVolumesLogic(vtkSlicerVolumesLogic* logic)
{
  this->Internal->VolumesLogic = logic;
}

//----------------------------------------------------------------------------
vtkSlicerVolumesLogic* vtkSlicerMyRegionTypeLogic::GetVolumesLogic()
{
  return this->Internal->VolumesLogic;
}

//-----------------------------------------------------------------------------
void vtkSlicerMyRegionTypeLogic::RegisterNodes()
{
  if(!this->GetMRMLScene())
  {
    return;
  }
  vtkMRMLMyRegionTypeNode* rtNode = vtkMRMLMyRegionTypeNode::New();
  vtkMRMLMyRegionTypeDisplayNode* drtNode = vtkMRMLMyRegionTypeDisplayNode::New();
  vtkMRMLChestRTColorTableNode* cNode = vtkMRMLChestRTColorTableNode::New();
  this->GetMRMLScene()->RegisterNodeClass(rtNode);
  this->GetMRMLScene()->RegisterNodeClass(drtNode);
  this->GetMRMLScene()->RegisterNodeClass(cNode);

  rtNode->Delete();
  drtNode->Delete();
  cNode->Delete();
}

//---------------------------------------------------------------------------
void vtkSlicerMyRegionTypeLogic::UpdateFromMRMLScene()
{
  assert(this->GetMRMLScene() != 0);
}

//---------------------------------------------------------------------------
void vtkSlicerMyRegionTypeLogic
::OnMRMLSceneNodeAdded(vtkMRMLNode* vtkNotUsed(node))
{
}

//---------------------------------------------------------------------------
void vtkSlicerMyRegionTypeLogic
::OnMRMLSceneNodeRemoved(vtkMRMLNode* vtkNotUsed(node))
{
}

