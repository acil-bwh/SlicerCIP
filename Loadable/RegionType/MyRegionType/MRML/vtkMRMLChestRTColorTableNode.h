/*=auto=========================================================================

  Portions (c) Copyright 2006 Brigham and Women's Hospital (BWH) All Rights Reserved.

  See COPYRIGHT.txt
  or http://www.slicer.org/copyright/copyright.txt for details.

  Program:   3D Slicer
  Module:    $RCSfile: vtkMRMLChestRTColorTableNode.h,v $
  Date:      $Date: 2006/03/19 17:12:28 $
  Version:   $Revision: 1.0 $

=========================================================================auto=*/

#ifndef __vtkMRMLChestRTColorTableNode_h
#define __vtkMRMLChestRTColorTableNode_h

#include "vtkMRMLColorNode.h"
#include "vtkSlicerMyRegionTypeModuleMRMLExport.h"

/// \brief MRML node to represent discrete color information for a Chest LabelMap.

class VTK_SLICER_MYREGIONTYPE_MODULE_MRML_EXPORT vtkMRMLChestRTColorTableNode : public vtkMRMLColorNode
{
public:
  static vtkMRMLChestRTColorTableNode *New();
  vtkTypeMacro(vtkMRMLChestRTColorTableNode,vtkMRMLColorNode);
  void PrintSelf(ostream& os, vtkIndent indent);
  
  //--------------------------------------------------------------------------
  /// MRMLNode methods
  //--------------------------------------------------------------------------

  virtual vtkMRMLNode* CreateNodeInstance();

  /// 
  /// Set node attributes
  virtual void ReadXMLAttributes( const char** atts);

  /// 
  /// Write this node's information to a MRML file in XML format.
  virtual void WriteXML(ostream& of, int indent);

  /// 
  /// Copy the node's attributes to this object
  virtual void Copy(vtkMRMLNode *node);

  /// 
  /// Get node XML tag name (like Volume, Model)
  virtual const char* GetNodeTagName() {return "ChestRTColorTable";};

  vtkGetObjectMacro(LookupTable, vtkLookupTable);
  virtual void SetLookupTable(vtkLookupTable* newLookupTable);

  /// 
  /// Get/Set for Type
  void SetType(int type);
  vtkGetMacro(Type,int);
  void SetTypeToChestRTLabels();
  
  void ProcessMRMLEvents ( vtkObject *caller, unsigned long event, void *callData );

  enum
    {
      ChestRTLabels = 0
    };

  /// 
  /// return a text string describing the colour look up table type
  virtual const char * GetTypeAsString();

  /// 
  /// Set the size of the colour table if it's a User table
  //void SetNumberOfColors(int n);

  /// 
  /// Set the size of the colour table 
  virtual int GetNumberOfRegions();
  virtual int GetNumberOfTypes();

  /// 
  /// keep track of where we last added a colour 
  int LastAddedColor;

  /// 
  /// Add a colour to the User colour table, at the end
  //void AddColor(const char* name, double r, double g, double b, double a = 1.0);

  /// 
  /// Set a colour into the User colour table. Return 1 on success, 0 on failure.
  //int SetColor(int entry, const char* name, double r, double g, double b, double a = 1.0);

  /// Retrieve the color associated to the index
  /// Return true if the color exists, false otherwise
  virtual bool GetColor(int entry, double* color);

  /// 
  /// clear out the names list
  void ClearNames();

  /// 
  /// reset when close the scene
  virtual void Reset();

  /// 
  /// return the index associated with this color name, which can then be used
  /// to get the colour. Returns -1 on failure.
  int GetColorIndexByName(const char *name);
 
  /// 
  /// Create default storage node or NULL if does not have one
  virtual vtkMRMLStorageNode* CreateDefaultStorageNode();

protected:
  vtkMRMLChestRTColorTableNode();
  virtual ~vtkMRMLChestRTColorTableNode();
  vtkMRMLChestRTColorTableNode(const vtkMRMLChestRTColorTableNode&);
  void operator=(const vtkMRMLChestRTColorTableNode&);

  ///  
  /// The look up table, constructed according to the Type
  vtkLookupTable *LookupTable;

};

#endif
