/*=auto=========================================================================

  Portions (c) Copyright 2005 Brigham and Women's Hospital (BWH) All Rights Reserved.

  See COPYRIGHT.txt
  or http://www.slicer.org/copyright/copyright.txt for details.

  Program:   3D Slicer
  Module:    $RCSfile: vtkMRMLAirwayNode.h,v $
  Date:      $Date: 2006/03/19 17:12:28 $
  Version:   $Revision: 1.6 $

=========================================================================auto=*/
///  vtkMRMLAirwayNode - MRML node to represent a fiber bundle from tractography in DTI data.
///
/// RegionType nodes contain general convetions for the extraction of specified regions types from a LabelMap.
/// A Airway node contains many fibers and forms the smallest logical unit of tractography
/// that MRML will manage/read/write. Each fiber has accompanying tensor data.
/// Visualization parameters for these nodes are controlled by the vtkMRMLRegionTypeNode class.
//

#ifndef __vtkMRMLRegionTypeNode_h
#define __vtkMRMLRegionTypeNode_h

#include "vtkMRMLLabelMapVolumeNode.h"
#include "vtkSlicerRegionTypeModuleMRMLExport.h"

// STD includes
#include <vector>
#include <list>
#include <string>

class vtkMRMLStorageNode;
class vtkMRMLColorNode;
class vtkMRMLRegionTypeDisplayNode;

class VTK_SLICER_REGIONTYPE_MODULE_MRML_EXPORT vtkMRMLRegionTypeNode : public vtkMRMLLabelMapVolumeNode
{
public:
  static vtkMRMLRegionTypeNode *New();
  vtkTypeMacro(vtkMRMLRegionTypeNode,vtkMRMLLabelMapVolumeNode);
  void PrintSelf(ostream& os, vtkIndent indent);

  //--------------------------------------------------------------------------
  /// MRMLNode methods
  //--------------------------------------------------------------------------

  virtual vtkMRMLNode* CreateNodeInstance();

  ///
  /// Get node XML tag name (like Volume, Model)
  virtual const char* GetNodeTagName() {return "RegionType";};

  ///
  /// Returns RegionType Display node
  vtkMRMLRegionTypeDisplayNode* GetRegionTypeDisplayNode();

  ///
  /// In addition to Supercalss SetAndObserveImageData also
  /// call UpdateAvailableRegionsAndTypes
  virtual void SetAndObserveImageData(vtkImageData *ImageData);

  ///
  /// Call UpdateAvailableRegionsAndTypes when image data changes
  virtual void ProcessMRMLEvents ( vtkObject * /*caller*/,
                                   unsigned long /*event*/,
                                   void * /*callData*/ );

  ///
  /// Returns vector of all regions encoded in ImageData
  std::vector<unsigned char> &  GetAvailableRegions()
  {
    return AvailableRegions;
  }

  ///
  /// Returns vector of all types encoded in ImageData
  std::vector<unsigned char> &  GetAvailableTypes()
  {
    return AvailableTypes;
  }

  ///
  /// Returns vector of all region names encoded in ImageData
  std::vector<std::string>&  GetAvailableRegionNames()
  {
    return AvailableRegionNames;
  }

  ///
  /// Returns vector of all type names encoded in ImageData
  std::vector<std::string>&  GetAvailableTypeNames()
  {
    return AvailableTypeNames;
  }

  ///
  /// Returns region given a voxel image value
  unsigned char GetChestRegionFromValue(unsigned short value)
  {
    return value - ((value >> 8) << 8);
  }

  ///
  /// Returns type given a voxel image value
  unsigned char GetChestTypeFromValue(unsigned short value)
  {
    return (value >> 8);
  }

  ///
  /// Returns range of region values encoded in ImageData
  void GetAvailableRegionsRange(unsigned char &min, unsigned char &max);

  ///
  /// Returns range of type values encoded in ImageData
  void GetAvailableTypesRange(unsigned char &min, unsigned char &max);

  ///
  /// Updates all internal caches of regions and types
  void UpdateAvailableRegionsAndTypes();

protected:
  vtkMRMLRegionTypeNode();
  virtual ~vtkMRMLRegionTypeNode();
  vtkMRMLRegionTypeNode(const vtkMRMLRegionTypeNode&);
  void operator=(const vtkMRMLRegionTypeNode&);

  std::vector<unsigned char> AvailableRegions;
  std::vector<unsigned char> AvailableTypes;

  std::vector<std::string> AvailableRegionNames;
  std::vector<std::string> AvailableTypeNames;
};

#endif
