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
#include <vtkImageEllipsoidSource.h>
#include <vtkImageCast.h>

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

vtkMRMLAirwayNode* vtkSlicerAirwayInspectorModuleLogic::AddAirwayNode(char *volumeNodeID,
                                                                      double x, double y, double z,
                                                                      double threshold)
{
  vtkMRMLAirwayNode *airwayNode = 0;
  if (volumeNodeID)
  {
    airwayNode = vtkMRMLAirwayNode::New();

    airwayNode->SetVolumeNodeID(volumeNodeID);
    airwayNode->SetThreshold(threshold);
    airwayNode->SetXYZ(x, y, z);
    this->GetMRMLScene()->AddNode(airwayNode);

    airwayNode->Delete();
  }
  return airwayNode;
}

void vtkSlicerAirwayInspectorModuleLogic::CreateAirway(vtkMRMLAirwayNode *node)
{
  ///TODO: add airway pipeline
  // for now just fake
  node->SetMin(2.5);
  node->SetMax(7.5);
  node->SetMean(5.5);
  node->SetStd(0.5);

  // Simple data source
  vtkSmartPointer<vtkImageEllipsoidSource> source =
        vtkSmartPointer<vtkImageEllipsoidSource>::New();
  source->SetOutputScalarTypeToUnsignedShort();
  source->SetInValue(1000);
  source->SetOutValue(0);
  source->SetCenter(20,20,20);
  source->SetRadius(9,10,11);
  source->SetWholeExtent(0, 14, 0, 29, 0, 49);
  source->Update();

  vtkSmartPointer<vtkImageCast> imCast = vtkSmartPointer<vtkImageCast>::New();
  imCast->SetOutputScalarTypeToUnsignedChar();
  imCast->SetInputConnection(source->GetOutputPort());
  imCast->Update();

  vtkImageData *image = vtkImageData::New();
  image->DeepCopy(imCast->GetOutput());
  node->SetAirwayImage(image);
}