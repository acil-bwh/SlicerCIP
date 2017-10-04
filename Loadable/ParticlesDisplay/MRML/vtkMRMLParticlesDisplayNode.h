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
class vtkSphereSource;
class vtkPolyDataAlgorithm;
class vtkAssignAttribute;
class vtkTransformPolyDataFilter;
class vtkTransform;

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

  /// Read node attributes from XML file.
  /// \sa vtkMRMLParser
  virtual void ReadXMLAttributes( const char** atts);

  /// Write this node's information to a MRML file in XML format.
  /// \sa vtkMRMLScene::Commit()
  virtual void WriteXML(ostream& of, int indent);

  /// Copy the node's attributes to this object.
  virtual void Copy(vtkMRMLNode *node);

  /// Update the pipeline based on this node attributes
  virtual void UpdatePolyDataPipeline();

  enum
  {
    ParticlesTypeAirway = 0,
    ParticlesTypeVessel = 1,
    ParticlesTypeFissure = 2,
  };

  enum
  {
    ParticlesColorByScale = 0,
    ParticlesColorByStrength = 1,
    ParticlesColorByType = 2,
    ParticlesColorByRegion = 3,
  };

  /// Description:
  /// Particles Type to dispaly from the enum above. The Particles Types are mutually exclusive.
  vtkGetMacro ( ParticlesType, int );
  vtkSetMacro ( ParticlesType, int );

  /// Description:
  /// Glyph Type, 0 cylinder, 1 sphere
  vtkGetMacro ( GlyphType, int );
  vtkSetMacro ( GlyphType, int );

  /// Description:
  /// Particles ScaleFactor along the Y and Z axis.
  vtkGetMacro ( ScaleFactor, double );
  vtkSetMacro ( ScaleFactor, double );

  /// Description:
  /// Particles size along the X axis.
  vtkGetMacro ( ParticleSize, double );
  vtkSetMacro ( ParticleSize, double );

  /// Description:
  /// Particles ColorBy to dispaly from the enum above. The Particles ColorBy are mutually exclusive.
  vtkGetStringMacro ( ParticlesColorBy );
  vtkSetStringMacro ( ParticlesColorBy );

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

  int     ParticlesType;
  char*   ParticlesColorBy;
  int     GlyphType;
  double  ScaleFactor;
  double  ParticleSize;

  vtkSmartPointer<vtkGlyph3DWithScaling>        Glypher;
  vtkSmartPointer<vtkSphereSource>              SphereSource;
  vtkSmartPointer<vtkCylinderSource>            CylinderSource;
  vtkSmartPointer<vtkPolyDataAlgorithm>         GlyphSource;
  vtkSmartPointer<vtkAssignAttribute>           AssignScalar;
  vtkSmartPointer<vtkAssignAttribute>           AssignVector;
  vtkSmartPointer<vtkTransformPolyDataFilter>   TransformPolyData;
  vtkSmartPointer<vtkTransform>                 CylinderRotator;
};

#endif
