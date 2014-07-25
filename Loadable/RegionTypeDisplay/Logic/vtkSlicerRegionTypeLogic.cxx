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
#include "vtkSlicerRegionTypeLogic.h"
#include "vtkSlicerVolumesLogic.h"

// MRML includes
#include <cipConventions.h>

#include <vtkMRMLRegionTypeNode.h>
#include <vtkMRMLRegionTypeDisplayNode.h>
#include <vtkMRMLChestRTColorTableNode.h>

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
class vtkSlicerRegionTypeLogic::vtkInternal
{
public:
  vtkInternal();

  vtkSlicerVolumesLogic* VolumesLogic;
};

//----------------------------------------------------------------------------
vtkSlicerRegionTypeLogic::vtkInternal::vtkInternal()
{
  this->VolumesLogic = 0;
}

//----------------------------------------------------------------------------
vtkStandardNewMacro(vtkSlicerRegionTypeLogic);

//----------------------------------------------------------------------------
vtkSlicerRegionTypeLogic::vtkSlicerRegionTypeLogic()
{
  this->Internal = new vtkInternal;
}

//----------------------------------------------------------------------------
vtkSlicerRegionTypeLogic::~vtkSlicerRegionTypeLogic()
{
  delete this->Internal;
}

//----------------------------------------------------------------------------
void vtkSlicerRegionTypeLogic::PrintSelf(ostream& os, vtkIndent indent)
{
  this->Superclass::PrintSelf(os, indent);
  os << indent << "vtkSlicerRegionTypeLogic:             " << this->GetClassName() << "\n";
}

//-----------------------------------------------------------------------------
void vtkSlicerRegionTypeLogic::DisplaySelectedRegionType(vtkMRMLRegionTypeNode* rtNode, const char* reg, const char* typ,
                                                           double regionTypeColorBlend)
{
  if (!rtNode)
  {
	  return;
  }

  this->GetMRMLScene()->StartState(vtkMRMLScene::BatchProcessState);

  vtkMRMLRegionTypeDisplayNode* displayNode = rtNode->GetRegionTypeDisplayNode();

  cip::ChestConventions cc;
  unsigned char region = cc.GetChestRegionValueFromName(std::string(reg));
  unsigned char type = cc.GetChestTypeValueFromName(std::string(typ));
  displayNode->ShowSelectedRegionType(rtNode, region, type, regionTypeColorBlend);

  this->GetMRMLScene()->EndState(vtkMRMLScene::BatchProcessState);
}

//---------------------------------------------------------------------------
void vtkSlicerRegionTypeLogic::DisplayAllRegionType(vtkMRMLRegionTypeNode* rtNode, double regionTypeColorBlend)
{
  if (!rtNode)
  {
	  return;
  }

  this->GetMRMLScene()->StartState(vtkMRMLScene::BatchProcessState);

  vtkMRMLRegionTypeDisplayNode* displayNode = rtNode->GetRegionTypeDisplayNode();
  displayNode->ShowAllRegionTypes(rtNode, regionTypeColorBlend);

  this->GetMRMLScene()->EndState(vtkMRMLScene::BatchProcessState);
}

//---------------------------------------------------------------------------
void vtkSlicerRegionTypeLogic::SetMRMLSceneInternal(vtkMRMLScene * newScene)
{
  vtkNew<vtkIntArray> events;
  events->InsertNextValue(vtkMRMLScene::NodeAddedEvent);
  events->InsertNextValue(vtkMRMLScene::NodeRemovedEvent);
  events->InsertNextValue(vtkMRMLScene::EndBatchProcessEvent);
  this->SetAndObserveMRMLSceneEventsInternal(newScene, events.GetPointer());
}

//----------------------------------------------------------------------------
void vtkSlicerRegionTypeLogic::SetVolumesLogic(vtkSlicerVolumesLogic* logic)
{
  this->Internal->VolumesLogic = logic;
}

//----------------------------------------------------------------------------
vtkSlicerVolumesLogic* vtkSlicerRegionTypeLogic::GetVolumesLogic()
{
  return this->Internal->VolumesLogic;
}

//-----------------------------------------------------------------------------
void vtkSlicerRegionTypeLogic::RegisterNodes()
{
  if(!this->GetMRMLScene())
  {
    return;
  }
  vtkMRMLRegionTypeNode* rtNode = vtkMRMLRegionTypeNode::New();
  vtkMRMLRegionTypeDisplayNode* drtNode = vtkMRMLRegionTypeDisplayNode::New();
  vtkMRMLChestRTColorTableNode* cNode = vtkMRMLChestRTColorTableNode::New();
  this->GetMRMLScene()->RegisterNodeClass(rtNode);
  this->GetMRMLScene()->RegisterNodeClass(drtNode);
  this->GetMRMLScene()->RegisterNodeClass(cNode);

  rtNode->Delete();
  drtNode->Delete();
  cNode->Delete();
}

//---------------------------------------------------------------------------
void vtkSlicerRegionTypeLogic::UpdateFromMRMLScene()
{
  assert(this->GetMRMLScene() != 0);
}

//---------------------------------------------------------------------------
void vtkSlicerRegionTypeLogic
::OnMRMLSceneNodeAdded(vtkMRMLNode* vtkNotUsed(node))
{
}

//---------------------------------------------------------------------------
void vtkSlicerRegionTypeLogic
::OnMRMLSceneNodeRemoved(vtkMRMLNode* vtkNotUsed(node))
{
}

