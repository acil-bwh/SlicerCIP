/*=auto=========================================================================

  Portions (c) Copyright 2005 Brigham and Women's Hospital (BWH) All Rights Reserved.

  See COPYRIGHT.txt
  or http://www.slicer.org/copyright/copyright.txt for details.

  Program:   3D Slicer
  Module:    $RCSfile: vtkMRMLLabelMapVolumeDisplayNode.h,v $
  Date:      $Date: 2006/03/19 17:12:29 $
  Version:   $Revision: 1.3 $

=========================================================================auto=*/

#ifndef __vtkMRMLParticlesDisplayNode_h
#define __vtkMRMLParticlesDisplayNode_h

#include "vtkMRMLModelDisplayNode.h"
#include "vtkSlicerParticlesDisplayModuleMRMLExport.h"

// ITK includes

#include "cipChestConventions.h"

//class cip::Conventions;
class vtkGlyph3DWithScaling;
class vtkCylinderSource;

/// \brief MRML node for representing a volume display attributes.
///
/// vtkMRMLParticlesDisplayNode nodes describe how volume is displayed.
class VTK_SLICER_PARTICLESDISPLAY_MODULE_MRML_EXPORT vtkMRMLParticlesDisplayNode   : public vtkMRMLModelDisplayNode
{
  public:
  static vtkMRMLParticlesDisplayNode *New();
  vtkTypeMacro(vtkMRMLParticlesDisplayNode,vtkMRMLModelDisplayNode);
  void PrintSelf(ostream& os, vtkIndent indent);

  virtual vtkMRMLNode* CreateNodeInstance();

  ///
  /// Get node XML tag name (like Volume, Model)
  virtual const char* GetNodeTagName() {return "ParticlesDisplayNode";};

  /// Update the pipeline based on this node attributes
  virtual void UpdatePolyDataPipeline();

  enum
  {
    ParticlesTypeAirway = 0,
    ParticlesTypeVessel = 1,
    ParticlesTypeFissure = 2,
  };

  /// Description:
  /// Particles Type to dispaly from the enum above. The Particles Types are mutually exclusive.
  vtkGetMacro ( ParticlesType, int );
  vtkSetMacro ( ParticlesType, int );

protected:

  vtkMRMLParticlesDisplayNode();
  virtual ~vtkMRMLParticlesDisplayNode();
  vtkMRMLParticlesDisplayNode(const vtkMRMLParticlesDisplayNode&);
  void operator=(const vtkMRMLParticlesDisplayNode&);

  /// Gets result in glyph PolyData
  virtual vtkAlgorithmOutput* GetOutputPolyDataConnection();

  ///
  /// returns LUT index for a given region and type
  int GetLUTIndex(unsigned char region, unsigned char type)
  {
    return  type*256 + region;
  };

  int ParticlesType;

  vtkGlyph3DWithScaling        *Glypher;
  vtkCylinderSource *GlyphSource;
};

#endif
