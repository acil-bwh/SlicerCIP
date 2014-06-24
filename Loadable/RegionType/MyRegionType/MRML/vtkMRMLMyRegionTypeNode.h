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
/// Visualization parameters for these nodes are controlled by the vtkMRMLMyRegionTypeDisplayNode class.
//

#ifndef __vtkMRMLMyRegionTypeNode_h
#define __vtkMRMLMyRegionTypeNode_h

#include "vtkMRMLScalarVolumeNode.h"
#include "vtkSlicerMyRegionTypeModuleMRMLExport.h"

// STD includes
#include <vector>
#include <list>

class vtkMRMLStorageNode; 
class vtkMRMLColorNode;

class VTK_SLICER_MYREGIONTYPE_MODULE_MRML_EXPORT vtkMRMLMyRegionTypeNode : public vtkMRMLScalarVolumeNode
{
public:
  static vtkMRMLMyRegionTypeNode *New();
  vtkTypeMacro(vtkMRMLMyRegionTypeNode,vtkMRMLScalarVolumeNode);
  void PrintSelf(ostream& os, vtkIndent indent);

  //--------------------------------------------------------------------------
  /// MRMLNode methods
  //--------------------------------------------------------------------------

  virtual vtkMRMLNode* CreateNodeInstance();

  ///
  /// Read node attributes from XML (MRML) file
  virtual void ReadXMLAttributes ( const char** atts );

  ///
  /// Write this node's information to a MRML file in XML format.
  virtual void WriteXML ( ostream& of, int indent );

  ///
  /// Copy the node's attributes to this object
  virtual void Copy ( vtkMRMLNode *node );

  /// 
  /// Get node XML tag name (like Volume, Model)
  virtual const char* GetNodeTagName() {return "RegionType";};

  ///
  /// Updates this node if it depends on other nodes
  /// when the node is deleted in the scene
  virtual void UpdateReferences()
    { Superclass::UpdateReferences(); };

  ///
  /// Finds the storage node and read the data
  //virtual void UpdateScene(vtkMRMLScene *scene);

  ///
  /// Update the stored reference to another node in the scene
   virtual void UpdateReferenceID(const char *oldID, const char *newID) 
    { Superclass::UpdateReferenceID(oldID, newID); };

   virtual void ProcessMRMLEvents ( vtkObject *caller,
                                    unsigned long event,
                                    void *callData )
    { 
      Superclass::ProcessMRMLEvents(caller, event, callData); 
    }; 

  /// Get region/type name
  virtual const char* GetNthRegionNameByIndex(int);
  virtual const char* GetNthTypeNameByIndex(int);
  //virtual REGIONANDTYPE GetNthPairNameByIndex(int);

  virtual const char* GetNthRegionNameByValue(unsigned int);
  virtual const char* GetNthTypeNameByValue(unsigned int);
  //virtual REGIONANDTYPE  GetNthPairNameByValue(unsigned int*)
  
  //--------------------------------------------------------------------------
  /// Interactive Selection Support
  //--------------------------------------------------------------------------
  
  ///
  /// Set a new "code" for regions and types available in the label map 
  virtual void SetAvailableRegionsValues(vtkImageData*, int); 
  virtual void SetAvailableRegionsNames(vtkMRMLColorNode*); 

  virtual void SetAvailableTypesValues(vtkImageData*, int); 
  virtual void SetAvailableTypesNames(vtkMRMLColorNode*); 

  //virtual void SetAvailablePairsValues();
  //virtual void SetAvailablePairsNames();

  ///
  /// Create and return default storage node or NULL if does not have one
  virtual vtkMRMLStorageNode* CreateDefaultStorageNode();

  std::list<unsigned int> RegionValuesList;
  std::list<unsigned int> TypeValuesList;
  
  std::vector<const char *> RegionNamesList;
  std::vector<const char *> TypeNamesList;

  
protected:
  vtkMRMLMyRegionTypeNode();
  virtual ~vtkMRMLMyRegionTypeNode();
  vtkMRMLMyRegionTypeNode(const vtkMRMLMyRegionTypeNode&);
  void operator=(const vtkMRMLMyRegionTypeNode&); 
  
  struct REGIONANDTYPE
  {
    const char *RegionName;
    const char *TypeName;
  };    

  std::vector<REGIONANDTYPE> RegionAndTypeNames; 

};

#endif
