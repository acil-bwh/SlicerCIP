// Annotation includes
#include "vtkSlicerAirwayInspectorModuleLogic.h"

// MRML includes
#include <vtkMRMLScene.h>
#include <vtkMRMLAirwayNode.h>
#include <vtkMRMLSliceNode.h>

// Logic includes
#include <vtkSlicerFiducialsLogic.h>

// VTK includes
#include <vtkImageData.h>
#include <vtkObjectFactory.h>
#include <vtkPNGWriter.h>
#include <vtkVersion.h>

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

void vtkSlicerAirwayInspectorModuleLogic::CreateAirway(vtkMRMLAirwayNode *node)
{
  ///TODO: add airway pipeline
}