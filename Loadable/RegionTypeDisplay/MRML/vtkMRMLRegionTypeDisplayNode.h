/*=auto=========================================================================

  Portions (c) Copyright 2005 Brigham and Women's Hospital (BWH) All Rights Reserved.

  See COPYRIGHT.txt
  or http://www.slicer.org/copyright/copyright.txt for details.

  Program:   3D Slicer
  Module:    $RCSfile: vtkMRMLLabelMapVolumeDisplayNode.h,v $
  Date:      $Date: 2006/03/19 17:12:29 $
  Version:   $Revision: 1.3 $

=========================================================================auto=*/

#ifndef __vtkMRMLRegionTypeDisplayNode_h
#define __vtkMRMLRegionTypeDisplayNode_h

#include "vtkMRMLLabelMapVolumeDisplayNode.h"
#include "vtkSlicerRegionTypeModuleMRMLExport.h"

// ITK includes

#include "cipChestConventions.h"

//class cip::Conventions;
class vtkMRMLRegionTypeNode;

/// \brief MRML node for representing a volume display attributes.
///
/// vtkMRMLRegionTypeDisplayNode nodes describe how volume is displayed.
class VTK_SLICER_REGIONTYPE_MODULE_MRML_EXPORT vtkMRMLRegionTypeDisplayNode   : public vtkMRMLLabelMapVolumeDisplayNode
{
  public:
  static vtkMRMLRegionTypeDisplayNode *New();
  vtkTypeMacro(vtkMRMLRegionTypeDisplayNode,vtkMRMLVolumeDisplayNode);
  void PrintSelf(ostream& os, vtkIndent indent);

  virtual vtkMRMLNode* CreateNodeInstance();

  ///
  /// Get node XML tag name (like Volume, Model)
  virtual const char* GetNodeTagName() {return "RegionTypeDisplayNode";};

  ///
  /// sets visibility for specific region/type combination.
  /// specifies color blend: 1 use region color, 0 use type color
  virtual void SetRegionTypeVisibility(unsigned char region, unsigned char type,
                                      int visibility, double regionTypeColorBlend);
  ///
  /// sets  all regions/types visible.
  virtual void HideAllRegionTypes(vtkMRMLRegionTypeNode* node);

  ///
  /// sets  all regions/types visible.
  /// specifies color blend: 1 use region color, 0 use type color
  virtual void ShowAllRegionTypes(vtkMRMLRegionTypeNode* node, double regionTypeColorBlend);

  ///
  /// sets  all types visible for a specified region
  /// specifies color blend: 1 use region color, 0 use type color
  virtual void ShowAllRegions(vtkMRMLRegionTypeNode* node,
                              unsigned char type, double regionTypeColorBlend);

  ///
  /// sets  all regions visible for a specified type
  /// specifies color blend: 1 use region color, 0 use type color
  virtual void ShowAllTypes(vtkMRMLRegionTypeNode* node,
                            unsigned char region, double regionTypeColorBlend);

  ///
  /// sets  specified region/type visible
  /// specifies color blend: 1 use region color, 0 use type color
  virtual void ShowSelectedRegionType(vtkMRMLRegionTypeNode* node,
                                      unsigned char region, unsigned char type,
                                      double regionTypeColorBlend);

  virtual void InitializeLookupTable(vtkMRMLRegionTypeNode* node, double regionTypeColorBlend);

protected:

  vtkMRMLRegionTypeDisplayNode();
  virtual ~vtkMRMLRegionTypeDisplayNode();
  vtkMRMLRegionTypeDisplayNode(const vtkMRMLRegionTypeDisplayNode&);
  void operator=(const vtkMRMLRegionTypeDisplayNode&);

  int GetLUTIndex(unsigned char region, unsigned char type)
  {
    return  type*256 + region;
  };
};

#endif
