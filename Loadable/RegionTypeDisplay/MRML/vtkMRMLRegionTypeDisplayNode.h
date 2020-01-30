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
  void PrintSelf(ostream& os, vtkIndent indent) override;

  virtual vtkMRMLNode* CreateNodeInstance() override;

  ///
  /// Get node XML tag name (like Volume, Model)
  virtual const char* GetNodeTagName() override {return "RegionTypeDisplayNode";};

  ///
  /// Sets visibility for specific region/type combination.
  /// specifies color blend: 1 use region color, 0 use type color
  virtual void SetRegionTypeVisibility(unsigned char region, unsigned char type,
                                      int visibility, double regionTypeColorBlend);
  ///
  /// Sets  all regions/types visible.
  virtual void HideAllRegionTypes(vtkMRMLRegionTypeNode* node);

  ///
  /// Sets  all regions/types visible.
  /// specifies color blend: 1 use region color, 0 use type color
  virtual void ShowAllRegionTypes(vtkMRMLRegionTypeNode* node, double regionTypeColorBlend);

  ///
  /// Sets  all types visible for a specified region
  /// specifies color blend: 1 use region color, 0 use type color
  virtual void ShowAllRegions(vtkMRMLRegionTypeNode* node,
                              unsigned char type, double regionTypeColorBlend);

  ///
  /// Sets  all regions visible for a specified type
  /// specifies color blend: 1 use region color, 0 use type color
  virtual void ShowAllTypes(vtkMRMLRegionTypeNode* node,
                            unsigned char region, double regionTypeColorBlend);

  ///
  /// Sets  specified region/type visible
  /// specifies color blend: 1 use region color, 0 use type color
  virtual void ShowSelectedRegionType(vtkMRMLRegionTypeNode* node,
                                      unsigned char region, unsigned char type,
                                      double regionTypeColorBlend);
  ///
  /// Initialize lookup table from region/type values in ImageData
  virtual void InitializeLookupTable(vtkMRMLRegionTypeNode* node, double regionTypeColorBlend);

protected:

  vtkMRMLRegionTypeDisplayNode();
  virtual ~vtkMRMLRegionTypeDisplayNode();
  vtkMRMLRegionTypeDisplayNode(const vtkMRMLRegionTypeDisplayNode&);
  void operator=(const vtkMRMLRegionTypeDisplayNode&);

  ///
  /// returns LUT index for a given region and type
  int GetLUTIndex(unsigned char region, unsigned char type)
  {
    return  type*256 + region;
  };

  int DisplayContours;
};

#endif
