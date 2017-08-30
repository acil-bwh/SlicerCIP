/*=auto=========================================================================

Portions (c) Copyright 2005 Brigham and Women\"s Hospital (BWH) All Rights Reserved.

See COPYRIGHT.txt
or http://www.slicer.org/copyright/copyright.txt for details.

Program:   3D Slicer
Module:    $RCSfile: vtkMRMLVolumeDisplayNode.cxx,v $
Date:      $Date: 2006/03/17 15:10:10 $
Version:   $Revision: 1.2 $

=========================================================================auto=*/
#include "vtkMRMLRegionTypeDisplayNode.h"
//#include "vtkMRMLProceduralColorNode.h"
#include "vtkMRMLScene.h"

#include "vtkMRMLRegionTypeNode.h"
#include "vtkMRMLColorNode.h"

// VTK includes
#include <vtkImageData.h>
#include <vtkImageMapToColors.h>
#include <vtkLookupTable.h>
#include <vtkObjectFactory.h>

// STD includes
#include <cassert>
#include <math.h>
#include <vnl/vnl_math.h>

//----------------------------------------------------------------------------
vtkMRMLNodeNewMacro(vtkMRMLRegionTypeDisplayNode);

//----------------------------------------------------------------------------
vtkMRMLRegionTypeDisplayNode::vtkMRMLRegionTypeDisplayNode()
{
}

//----------------------------------------------------------------------------
vtkMRMLRegionTypeDisplayNode::~vtkMRMLRegionTypeDisplayNode()
{
}

//----------------------------------------------------------------------------
void vtkMRMLRegionTypeDisplayNode::PrintSelf(ostream& os, vtkIndent indent)
{
  Superclass::PrintSelf(os,indent);
}

//-------------------------------------------
void vtkMRMLRegionTypeDisplayNode::SetRegionTypeVisibility(unsigned char region, unsigned char type,
                                                             int visibility, double regionTypeColorBlend)
{
  vtkMRMLColorNode* colorNode = vtkMRMLColorNode::SafeDownCast( this->GetColorNode() );
  if (colorNode == 0)
  {
    return;
  }

  vtkLookupTable *lut = colorNode->GetLookupTable();
  if (lut == 0)
  {
    return;
  }

  double color[4];
  double typeColor[4];
  double regionColor[4];
  cip::ChestConventions cc;
  cc.GetChestTypeColor(type, typeColor);
  cc.GetChestRegionColor(region, regionColor);
  for (int i=0; i<4; i++)
  {
    color[i] = (1.0 - regionTypeColorBlend) * regionColor[i] +
                      regionTypeColorBlend * typeColor[i];
  }
  color[3] = visibility;
  int index = this->GetLUTIndex(region, type);
  lut->SetTableValue(index, color);
}

//-------------------------------------------
void vtkMRMLRegionTypeDisplayNode::HideAllRegionTypes(vtkMRMLRegionTypeNode* node)
{
  std::vector<unsigned char> regions = node->GetAvailableRegions();
  std::vector<unsigned char> types = node->GetAvailableTypes();
  for (size_t t=0; t<types.size(); t++)
  {
    for (size_t r=0; r<regions.size(); r++)
    {
      this->SetRegionTypeVisibility(regions[r], types[t], 0, 0);
    }
  }
  this->Modified();
}

//-------------------------------------------
void vtkMRMLRegionTypeDisplayNode::ShowAllRegionTypes(vtkMRMLRegionTypeNode* node, double regionTypeColorBlend)
{
  std::vector<unsigned char> regions = node->GetAvailableRegions();
  std::vector<unsigned char> types = node->GetAvailableTypes();
  for (size_t t=0; t<types.size(); t++)
  {
    for (size_t r=0; r<regions.size(); r++)
    {
      this->SetRegionTypeVisibility(regions[r], types[t], 1, regionTypeColorBlend);
    }
  }
  this->Modified();
}

//-------------------------------------------
void vtkMRMLRegionTypeDisplayNode::ShowSelectedRegionType(vtkMRMLRegionTypeNode* node,
                                                            unsigned char region, unsigned char type,
                                                            double regionTypeColorBlend)
{
  this->HideAllRegionTypes(node);
  this->SetRegionTypeVisibility(region, type, 1, regionTypeColorBlend);
  this->Modified();
}

//-------------------------------------------
void vtkMRMLRegionTypeDisplayNode::ShowAllRegions(vtkMRMLRegionTypeNode* node,
                                                    unsigned char type,
                                                    double regionTypeColorBlend)
{
  this->HideAllRegionTypes(node);
  std::vector<unsigned char> regions = node->GetAvailableRegions();
  for (size_t r=0; r<regions.size(); r++)
  {
    this->SetRegionTypeVisibility(regions[r], type, 1, regionTypeColorBlend);
  }
  this->Modified();
}

//-------------------------------------------
void vtkMRMLRegionTypeDisplayNode::ShowAllTypes(vtkMRMLRegionTypeNode* node,
                                                  unsigned char region,
                                                  double regionTypeColorBlend)
{
  this->HideAllRegionTypes(node);
  std::vector<unsigned char> types = node->GetAvailableTypes();
  for (size_t t=0; t<types.size(); t++)
  {
    this->SetRegionTypeVisibility(region, types[t], 1, regionTypeColorBlend);
  }
  this->Modified();
}

//-------------------------------------------
void vtkMRMLRegionTypeDisplayNode::InitializeLookupTable(vtkMRMLRegionTypeNode* node, double regionTypeColorBlend)
{
  vtkMRMLColorNode* colorNode = vtkMRMLColorNode::SafeDownCast( this->GetColorNode() );
  if (colorNode == 0)
  {
    return;
  }

  vtkLookupTable *lut = colorNode->GetLookupTable();
  if (lut == 0)
  {
    return;
  }

  std::vector<unsigned char> regions = node->GetAvailableRegions();
  std::vector<unsigned char> types = node->GetAvailableTypes();

  int index;
  int maxIndex = 0;
  for (size_t t=0; t<types.size(); t++)
  {
    for (size_t r=0; r<regions.size(); r++)
    {
      index = this->GetLUTIndex(regions[r], types[t]);
      maxIndex = index > maxIndex? index : maxIndex;
    }
  }
  lut = colorNode->GetLookupTable();
  lut->SetNumberOfTableValues(maxIndex);
  lut->SetTableRange(0,maxIndex);
}
