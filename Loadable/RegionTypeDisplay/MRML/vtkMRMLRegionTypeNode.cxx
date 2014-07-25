/*=auto=========================================================================

Portions (c) Copyright 2005 Brigham and Women's Hospital (BWH) All Rights Reserved.

See COPYRIGHT.txt
or http://www.slicer.org/copyright/copyright.txt for details.

Program:   3D Slicer
Module:    $RCSfile: vtkMRMLAirwayNode.cxx,v $
Date:      $Date: 2006/03/03 22:26:39 $
Version:   $Revision: 1.3 $

=========================================================================auto=*/
// MRML includes
#include "vtkMRMLRegionTypeNode.h"

#include "vtkMRMLRegionTypeDisplayNode.h"
// MRML includes
#include <vtkMRMLNRRDStorageNode.h>
#include "vtkMRMLColorTableNode.h"
#include "vtkMRMLScene.h"

// VTK includes
#include <vtkObjectFactory.h>
#include <vtkImageIterator.h>
#include <vtkImageAccumulate.h>
#include <vtkImageData.h>
#include <vtkPointData.h>
#include <vtkUnsignedShortArray.h>
#include <vtkCallbackCommand.h>
#include <vtkAlgorithmOutput.h>

#include <cipConventions.h>

// STD includes
#include <cassert>
#include <list>

#include <math.h>
#include <vnl/vnl_math.h>

//------------------------------------------------------------------------------
vtkMRMLNodeNewMacro(vtkMRMLRegionTypeNode);

//-----------------------------------------------------------------------------
vtkMRMLRegionTypeNode::vtkMRMLRegionTypeNode()
{
  this->SetAttribute("LabelMap", "1");
}

//-----------------------------------------------------------------------------
vtkMRMLRegionTypeNode::~vtkMRMLRegionTypeNode()
{
}

//----------------------------------------------------------------------------
void vtkMRMLRegionTypeNode::PrintSelf(ostream& os, vtkIndent indent)
{
  Superclass::PrintSelf(os,indent);
}

//---------------------------------------------------------------------------
void vtkMRMLRegionTypeNode::ProcessMRMLEvents ( vtkObject *caller,
                                           unsigned long event,
                                           void *callData )
{
  Superclass::ProcessMRMLEvents(caller, event, callData);

  // did the image data change?
#if (VTK_MAJOR_VERSION <= 5)
  if (this->GetImageData() == vtkImageData::SafeDownCast(caller) &&
#else
  if (this->ImageDataConnection != 0 &&
      this->ImageDataConnection->GetProducer() == vtkAlgorithm::SafeDownCast(caller) &&
#endif
    event ==  vtkCommand::ModifiedEvent)
    {
    this->UpdateAvailableRegionsAndTypes();
    }

  return;
}
//----------------------------------------------------------------------------
void vtkMRMLRegionTypeNode::UpdateAvailableRegionsAndTypes()
{
  AvailableRegionNames.clear();
  AvailableTypeNames.clear();
  AvailableRegions.clear();
  AvailableTypes.clear();

  vtkImageData* image = this->GetImageData();
  if (image == 0)
  {
    return;
  }

  int extent[6];
  image->GetExtent(extent);

  cip::ChestConventions cc;

  vtkImageIterator<unsigned short> iIter(image,extent);

  if (image->GetNumberOfScalarComponents() != 1)
    {
    vtkErrorMacro("Only one component data is supported by this module");
    return;
    }
  if (image->GetScalarType() != VTK_UNSIGNED_SHORT)
    {
    vtkErrorMacro("Only VTK_UNSIGNED_SHORT data is supported by this module");
    return;
    }

  vtkUnsignedShortArray* a =
    vtkUnsignedShortArray::SafeDownCast(image->GetPointData()->GetScalars());

  unsigned char regionMap[256];
  unsigned char typeMap[256];

  for (int i=0; i< 256; i++)
    {
    regionMap[i] = 0;
    typeMap[i] = 0;
    }
  regionMap[0] = 1;
  typeMap[0] = 1;

  int nvals = a->GetNumberOfTuples();

  for (int i=0; i<nvals; i++)
    {
    unsigned short v = a->GetValue(i);
    if (v)
      {
      unsigned char region = this->GetChestRegionFromValue(v);
      regionMap[region] = 1;

      unsigned char type = this->GetChestTypeFromValue(v);
      typeMap[type] = 1;
      }
    }

  for (int i=0; i< 256; i++)
    {
    if (regionMap[i])
      {
      AvailableRegions.push_back( i );
      AvailableRegionNames.push_back(cc.GetChestRegionName( i) );
      }
    if (typeMap[i])
      {
      AvailableTypes.push_back( i );
      AvailableTypeNames.push_back(cc.GetChestTypeName( i ) );
      }
    }
}

vtkMRMLRegionTypeDisplayNode* vtkMRMLRegionTypeNode::GetRegionTypeDisplayNode()
{
  return vtkMRMLRegionTypeDisplayNode::SafeDownCast(this->GetDisplayNode());
}

