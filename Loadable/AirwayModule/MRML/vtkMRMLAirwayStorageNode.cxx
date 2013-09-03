/*=auto=========================================================================

Portions (c) Copyright 2005 Brigham and Women's Hospital (BWH) All Rights Reserved.

See COPYRIGHT.txt
or http://www.slicer.org/copyright/copyright.txt for details.

Program:   3D Slicer
Module:    $RCSfile: vtkMRMLAirwayStorageNode.cxx,v $
Date:      $Date: 2006/03/17 15:10:09 $
Version:   $Revision: 1.2 $

=========================================================================auto=*/


#include "vtkObjectFactory.h"
#include "vtkMRMLAirwayStorageNode.h"
#include "vtkMRMLAirwayNode.h"
#include "vtkMRMLAirwayDisplayNode.h"
#include <vtkPolyData.h>
#include <vtkPointData.h>
#include <vtkFieldData.h>
#include <vtkRearrangeFields.h>
#include <vtkAssignAttribute.h>

//----------------------------------------------------------------------------
vtkMRMLNodeNewMacro(vtkMRMLAirwayStorageNode);

//----------------------------------------------------------------------------
int vtkMRMLAirwayStorageNode::SupportedFileType(const char *fileName)
{
  return this->Superclass::SupportedFileType(fileName);
  //return 0;
}

//----------------------------------------------------------------------------
void vtkMRMLAirwayStorageNode::InitializeSupportedWriteFileTypes()
{
  this->Superclass::InitializeSupportedWriteFileTypes();
}

//----------------------------------------------------------------------------
int vtkMRMLAirwayStorageNode::ReadDataInternal(vtkMRMLNode *refNode){
  vtkDebugMacro("Internal data read");

  int res = vtkMRMLModelStorageNode::ReadDataInternal(refNode);
  if (res == 0)
    return 0;

  vtkDebugMacro("airway data read");

  vtkMRMLAirwayNode* airwayNode = vtkMRMLAirwayNode::SafeDownCast(refNode);

  airwayNode->GetPolyData()->Update();

  if (! (
        (airwayNode != NULL ) &&
        (airwayNode->GetPolyData() != NULL) &&
        (airwayNode->GetPolyData()->GetFieldData() != NULL)
        //(airwayNode->GetPolyData()->GetFieldData()->GetArray('hess') != NULL)
      ))
    {
        vtkDebugMacro("The airway node has to have a field data array with name 'hess'");
        return 0;
    }
  vtkRearrangeFields* rf = vtkRearrangeFields::New();
  vtkAssignAttribute* aa = vtkAssignAttribute::New();

  rf->SetInput(airwayNode->GetPolyData());
  rf->AddOperation(vtkRearrangeFields::COPY, "hess", 
                  vtkRearrangeFields::DATA_OBJECT, 
                  vtkRearrangeFields::POINT_DATA);

  aa->SetInput(rf->GetOutput());
  aa->Assign("hess", vtkDataSetAttributes::TENSORS,
           vtkAssignAttribute::POINT_DATA);
  aa->GetOutput()->Update();

  airwayNode->SetAndObservePolyData(dynamic_cast<vtkPolyData*>(aa->GetOutput()));

  rf->Delete();
  aa->Delete();

  if (airwayNode->GetDisplayNode())
    dynamic_cast<vtkMRMLAirwayDisplayNode*>(airwayNode->GetDisplayNode())->SetInputPolyData(airwayNode->GetPolyData());

  return 1;
}

