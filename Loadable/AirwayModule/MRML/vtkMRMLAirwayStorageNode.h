/*=auto=========================================================================

  Portions (c) Copyright 2005 Brigham and Women's Hospital (BWH) All Rights Reserved.

  See COPYRIGHT.txt
  or http://www.slicer.org/copyright/copyright.txt for details.

  Program:   3D Slicer
  Module:    $RCSfile: vtkMRMLAirwayStorageNode.h,v $
  Date:      $Date: 2006/03/19 17:12:29 $
  Version:   $Revision: 1.3 $

=========================================================================auto=*/
///  vtkMRMLAirwayStorageNode - MRML node for fiberBundle storage on disk.
///
/// The storage node has methods to read/write vtkPolyData to/from disk.

#ifndef __vtkMRMLAirwayStorageNode_h
#define __vtkMRMLAirwayStorageNode_h

// MRML includes
#include "vtkMRMLModelStorageNode.h"

class vtkMRMLAirwayStorageNode : public vtkMRMLModelStorageNode
{
  public:
  static vtkMRMLAirwayStorageNode *New();
  vtkTypeMacro(vtkMRMLAirwayStorageNode,vtkMRMLModelStorageNode);
  //void PrintSelf(ostream& os, vtkIndent indent);

  virtual vtkMRMLNode* CreateNodeInstance();

  ///
  /// Get node XML tag name (like Storage, Model)
  virtual const char* GetNodeTagName()  {return "AirwayStorage";};

  ///
  /// Check to see if this storage node can handle the file type in the input
  /// string. If input string is null, check URI, then check FileName.
  /// Subclasses should implement this method.
  virtual int SupportedFileType(const char *fileName);

  ///
  /// Initialize all the supported write file types
  virtual void InitializeSupportedWriteFileTypes();

  ///
  /// Return a default file extension for writting
  virtual const char* GetDefaultWriteFileExtension()
    {
    return "vtk";
    };

protected:
  vtkMRMLAirwayStorageNode(){};
  ~vtkMRMLAirwayStorageNode(){};
  vtkMRMLAirwayStorageNode(const vtkMRMLAirwayStorageNode&);
  void operator=(const vtkMRMLAirwayStorageNode&);
  virtual int ReadDataInternal(vtkMRMLNode *refNode);


};

#endif

