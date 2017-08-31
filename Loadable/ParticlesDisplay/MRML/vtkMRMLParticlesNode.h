/*=auto=========================================================================

  Portions (c) Copyright 2005 Brigham and Women's Hospital (BWH) All Rights Reserved.

  See COPYRIGHT.txt
  or http://www.slicer.org/copyright/copyright.txt for details.

  Program:   3D Slicer
  Module:    $RCSfile: vtkMRMLParticlesNode.h,v $
  Date:      $Date: 2006/03/19 17:12:28 $
  Version:   $Revision: 1.6 $

=========================================================================auto=*/
///  vtkMRMLParticlesNode - MRML node to represent a fiber bundle from tractography in DTI data.
///
/// Particles nodes contain trajectories ("fibers") from tractography, internally represented as vtkPolyData.
/// A Particles node contains many fibers and forms the smallest logical unit of tractography
/// that MRML will manage/read/write. Each fiber has accompanying tensor data.
/// Visualization parameters for these nodes are controlled by the vtkMRMLParticlesDisplayNode class.
//

#ifndef __vtkMRMLParticlesNode_h
#define __vtkMRMLParticlesNode_h

#include "vtkMRMLModelNode.h"

#include "vtkSlicerParticlesDisplayModuleMRMLExport.h"

// ITK includes

class vtkMRMLParticlesDisplayNode;

class VTK_SLICER_PARTICLESDISPLAY_MODULE_MRML_EXPORT vtkMRMLParticlesNode : public vtkMRMLModelNode
{
public:
  static vtkMRMLParticlesNode *New();
  vtkTypeMacro(vtkMRMLParticlesNode,vtkMRMLModelNode);
  //vtkTypeMacro(vtkMRMLParticlesNode,vtkMRMLTransformableNode);
  void PrintSelf(ostream& os, vtkIndent indent);

  //--------------------------------------------------------------------------
  /// MRMLNode methods
  //--------------------------------------------------------------------------

  virtual vtkMRMLNode* CreateNodeInstance();

  ///
  /// Copy the node's attributes to this object
  virtual void Copy ( vtkMRMLNode *node );

  ///
  /// alternative method to propagate events generated in Display nodes
  virtual void ProcessMRMLEvents ( vtkObject * /*caller*/,
                                   unsigned long /*event*/,
                                   void * /*callData*/ );

  ///
  /// Get node XML tag name (like Volume, Model)
  virtual const char* GetNodeTagName() {return "Particles";};

  ///
  /// get associated line display node or NULL if not set
  vtkMRMLParticlesDisplayNode* GetParticlesDisplayNode();

  /// Create default display nodes
  virtual vtkMRMLStorageNode* CreateDefaultStorageNode();

  /// Get all point scalar arrays in particles vtkPolyData
  void GetAvailableScalarNames(std::vector<std::string> &names);

  /// Get all point vector arrays in particles vtkPolyData
  void getAvailableVectorNames(std::vector<std::string> &names);

protected:
  vtkMRMLParticlesNode();
  ~vtkMRMLParticlesNode();
  vtkMRMLParticlesNode(const vtkMRMLParticlesNode&);
  void operator=(const vtkMRMLParticlesNode&);
};

#endif
