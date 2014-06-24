/*=auto=========================================================================

  Portions (c) Copyright 2005 Brigham and Women's Hospital (BWH) All Rights Reserved.

  See COPYRIGHT.txt
  or http://www.slicer.org/copyright/copyright.txt for details.

  Program:   3D Slicer
  Module:    $RCSfile: vtkMRMLLabelMapVolumeDisplayNode.h,v $
  Date:      $Date: 2006/03/19 17:12:29 $
  Version:   $Revision: 1.3 $

=========================================================================auto=*/

#ifndef __vtkMRMLMyRegionTypeDisplayNode_h
#define __vtkMRMLMyRegionTypeDisplayNode_h

#include "vtkMRMLLabelMapVolumeDisplayNode.h"
#include "vtkSlicerMyRegionTypeModuleMRMLExport.h"

// ITK includes
//#include "cipConventions.h"

//class cip::Conventions;
class vtkMRMLMyRegionTypeNode;

/// \brief MRML node for representing a volume display attributes.
///
/// vtkMRMLMyRegionTypeDisplayNode nodes describe how volume is displayed.
class VTK_SLICER_MYREGIONTYPE_MODULE_MRML_EXPORT vtkMRMLMyRegionTypeDisplayNode : public vtkMRMLLabelMapVolumeDisplayNode
{
  public:
  static vtkMRMLMyRegionTypeDisplayNode *New();
  vtkTypeMacro(vtkMRMLMyRegionTypeDisplayNode,vtkMRMLVolumeDisplayNode);
  void PrintSelf(ostream& os, vtkIndent indent);
  
  virtual vtkMRMLNode* CreateNodeInstance();

  /// 
  /// Get node XML tag name (like Volume, Model)
  virtual const char* GetNodeTagName() {return "MyRegionTypeDisplayNode";};

  /// 
  /// alternative method to propagate events generated in Display nodes
  virtual void ProcessMRMLEvents ( vtkObject * /*caller*/, 
                                   unsigned long /*event*/, 
                                   void * /*callData*/ );

  /// Gets the pipeline output
  virtual void ShowSelectedLabels(vtkMRMLMyRegionTypeNode*, const char*, const char*);
  virtual void ShowAllRegions();
  virtual void ShowAllTypes();
  virtual void SetRegionToShow(const char*);
  virtual void SetTypeToShow(const char*);
  //virtual void SetPairToShow(REGIONANDTYPE); 

protected:
  vtkMRMLMyRegionTypeDisplayNode();
  virtual ~vtkMRMLMyRegionTypeDisplayNode();
  vtkMRMLMyRegionTypeDisplayNode(const vtkMRMLMyRegionTypeDisplayNode&);
  void operator=(const vtkMRMLMyRegionTypeDisplayNode&);

  struct REGIONANDTYPE
  {
    const char *RegionName;
    const char *TypeName;
  };
 
  vtkLookupTable *LUT;
  std::vector<const char *> regionsToShow; //* or not?
  std::vector<const char *> typesToShow;
  std::vector<REGIONANDTYPE> pairsToShow;

};

#endif
