// Annotation includes
#include "vtkSlicerAirwayInspectorModuleLogic.h"

// QSlicer includes
#include "qSlicerApplication.h"
#include "qSlicerLayoutManager.h"
#include "qMRMLSliceWidget.h"
#include "qMRMLSliceView.h"

// MRML includes
#include <vtkMRMLInteractionNode.h>
#include <vtkMRMLScene.h>
#include <vtkMRMLAirwayNode.h>
#include <vtkMRMLSliceNode.h>

// Logic includes
#include <vtkSlicerFiducialsLogic.h>

// VTK includes
#include <vtkImageData.h>
#include <vtkCallbackCommand.h>
#include <vtkObjectFactory.h>
#include <vtkPNGWriter.h>
#include <vtkVersion.h>
#include <vtkInteractorObserver.h>
#include <vtkRenderWindow.h>

// STD includes
#include <algorithm>
#include <string>
#include <iostream>
#include <sstream>

//-----------------------------------------------------------------------------
vtkStandardNewMacro(vtkSlicerAirwayInspectorModuleLogic)

//-----------------------------------------------------------------------------
// vtkSlicerAirwayInspectorModuleLogic methods
//-----------------------------------------------------------------------------
vtkSlicerAirwayInspectorModuleLogic::vtkSlicerAirwayInspectorModuleLogic()
{
  this->Interactor = 0;
  this->InteractorCallBackCommand = vtkSmartPointer<vtkCallbackCommand>::New();
  this->InteractorCallBackCommand->SetCallback(
      vtkSlicerAirwayInspectorModuleLogic::DoInteractorCallback);
  this->InteractorCallBackCommand->SetClientData(this);

  VolumeNodeID = 0;
  Threshold = 0;
}

//-----------------------------------------------------------------------------
vtkSlicerAirwayInspectorModuleLogic::~vtkSlicerAirwayInspectorModuleLogic()
{
}

//-----------------------------------------------------------------------------
void vtkSlicerAirwayInspectorModuleLogic::PrintSelf(ostream& os, vtkIndent indent)
{
  Superclass::PrintSelf(os, indent);
}

//----------------------------------------------------------------------------
void vtkSlicerAirwayInspectorModuleLogic::DoInteractorCallback(
    vtkObject* vtk_obj, unsigned long event, void* client_data, void* vtkNotUsed(call_data))
{
  // vtkInteractor is expected to be source of the event
  assert(vtkRenderWindowInteractor::SafeDownCast(vtk_obj));

  vtkSlicerAirwayInspectorModuleLogic* self =
      reinterpret_cast<vtkSlicerAirwayInspectorModuleLogic*>(client_data);
  assert(self);

  self->OnInteractorEvent(event);
}

//----------------------------------------------------------------------------
void vtkSlicerAirwayInspectorModuleLogic::SetAndObserveInteractor(
                                vtkRenderWindowInteractor* newInteractor)
{
  if (this->Interactor == newInteractor)
    {
    return;
    }

  // Remove existing interactor observer
  if (this->Interactor)
    {
    this->Interactor->RemoveObserver(this->InteractorCallBackCommand);
    this->Interactor->UnRegister(this);
    }

  // Install observers
  if (newInteractor)
    {
    newInteractor->Register(this);
    newInteractor->AddObserver(vtkCommand::KeyReleaseEvent, this->InteractorCallBackCommand);
    }

  this->Interactor = newInteractor;
}

//---------------------------------------------------------------------------
void vtkSlicerAirwayInspectorModuleLogic::OnInteractorEvent(int eventid)
{
  std::cout << "OnInteractorEvent - eventid:" << eventid
             << ", eventname:" << vtkCommand::GetStringFromEventId(eventid) << std::endl;

  if (eventid == vtkCommand::KeyPressEvent &&
    this->Interactor->GetKeyCode() == 'a'  )
    {
    double x = this->Interactor->GetEventPosition()[0];
    double y = this->Interactor->GetEventPosition()[1];

    double windowWidth = this->Interactor->GetRenderWindow()->GetSize()[0];
    double windowHeight = this->Interactor->GetRenderWindow()->GetSize()[1];

    if (x < windowWidth && y < windowHeight)
      {
      // it's a 3D displayable manager and the click could have been on a node
      double yNew = windowHeight - y - 1;
      }
      //vtkMRMLSliceNode::GetSliceOffset()
      double z = 0;
      this->AddAirwayNode(x,y,z);
    }
}

//---------------------------------------------------------------------------
// Set the internal mrml scene adn observe events on it
//---------------------------------------------------------------------------
void vtkSlicerAirwayInspectorModuleLogic::SetMRMLSceneInternal(vtkMRMLScene * newScene)
{
}

//---------------------------------------------------------------------------
void vtkSlicerAirwayInspectorModuleLogic::ObserveMRMLScene()
{
  vtkRenderWindowInteractor *ineractor = qSlicerApplication::application()->layoutManager()->sliceWidget("Red")->sliceView()->interactorStyle()->GetInteractor();

  this->SetAndObserveInteractor(ineractor);
  // Superclass::ObserveMRMLScene calls UpdateFromMRMLScene();
  this->Superclass::ObserveMRMLScene();
}

vtkMRMLAirwayNode* vtkSlicerAirwayInspectorModuleLogic::AddAirwayNode(double x, double y, double z)
{
  vtkMRMLAirwayNode *airwayNode = 0;
  if (this->GetVolumeNodeID())
  {
    airwayNode = vtkMRMLAirwayNode::New();

    airwayNode->SetVolumeNodeID(this->GetVolumeNodeID());
    airwayNode->SetThreshold(this->GetThreshold());
    airwayNode->SetXYZ(x, y, z);
    this->GetMRMLScene()->AddNode(airwayNode);

    airwayNode->Delete();
  }
  return airwayNode;
}
