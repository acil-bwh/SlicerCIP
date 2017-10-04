/*=auto=========================================================================

Portions (c) Copyright 2005 Brigham and Women\"s Hospital (BWH) All Rights Reserved.

See COPYRIGHT.txt
or http://www.slicer.org/copyright/copyright.txt for details.

Program:   3D Slicer
Module:    $RCSfile: vtkMRMLVolumeDisplayNode.cxx,v $
Date:      $Date: 2006/03/17 15:10:10 $
Version:   $Revision: 1.2 $

=========================================================================auto=*/
#include "vtkMRMLParticlesDisplayNode.h"
//#include "vtkMRMLProceduralColorNode.h"
#include "vtkMRMLScene.h"

#include "vtkMRMLParticlesDisplayNode.h"

// VTK includes
#include <vtkObjectFactory.h>
#include <vtkPointData.h>
#include <vtkGlyph3DWithScaling.h>
#include <vtkCylinderSource.h>
#include <vtkSphereSource.h>
#include <vtkAssignAttribute.h>
#include <vtkTransformPolyDataFilter.h>
#include <vtkTransform.h>

// STD includes
#include <cassert>
#include <math.h>
#include <vnl/vnl_math.h>

#include <sstream>

//----------------------------------------------------------------------------
vtkMRMLNodeNewMacro(vtkMRMLParticlesDisplayNode);

//----------------------------------------------------------------------------
vtkMRMLParticlesDisplayNode::vtkMRMLParticlesDisplayNode()
{
  this->ParticleSize = 0.4;

  this->AssignScalar = vtkSmartPointer<vtkAssignAttribute>::New();
  this->AssignVector = vtkSmartPointer<vtkAssignAttribute>::New();
  this->Glypher = vtkSmartPointer<vtkGlyph3DWithScaling>::New();
  this->SphereSource = vtkSmartPointer<vtkSphereSource>::New();
  this->SphereSource->SetRadius( this->ParticleSize );
  this->SphereSource->SetCenter( 0, 0, 0 );

  this->CylinderSource = vtkSmartPointer<vtkCylinderSource>::New();
  this->CylinderSource->SetHeight( this->ParticleSize); //25
  this->CylinderSource->SetRadius( 1.0 );
  this->CylinderSource->SetCenter( 0, 0, 0 );
  this->CylinderSource->SetResolution( 20 );
  this->CylinderSource->CappingOn();

  this->CylinderRotator = vtkSmartPointer<vtkTransform>::New();
  this->CylinderRotator->RotateZ( 90 );

  this->TransformPolyData = vtkSmartPointer<vtkTransformPolyDataFilter>::New();
  this->TransformPolyData->SetInputConnection(this->CylinderSource->GetOutputPort() );
  this->TransformPolyData->SetTransform( this->CylinderRotator );
  this->TransformPolyData->Update();

  this->ParticlesType = vtkMRMLParticlesDisplayNode::ParticlesTypeAirway;
  this->ParticlesColorBy = 0;

  this->GlyphType = 0; //cylinder
  this->GlyphSource = this->CylinderSource;

  this->AssignVector->SetInputConnection(this->AssignScalar->GetOutputPort());
  this->Glypher->SetInputConnection(this->AssignVector->GetOutputPort());
  this->Glypher->SetSourceConnection(this->GlyphSource->GetOutputPort());

  this->Glypher->ScalingXOff();
  this->Glypher->ScalingYOn();
  this->Glypher->ScalingZOn();
  this->ScaleFactor = 1.0;
  this->Glypher->SetScaleFactor( this->ScaleFactor );

  this->SetScalarVisibility(1);

  this->ParticlesColorBy = 0;
}

//----------------------------------------------------------------------------
vtkMRMLParticlesDisplayNode::~vtkMRMLParticlesDisplayNode()
{
  this->SetParticlesColorBy(0);
}

//----------------------------------------------------------------------------
void vtkMRMLParticlesDisplayNode::PrintSelf(ostream& os, vtkIndent indent)
{
  Superclass::PrintSelf(os,indent);

  os << indent << "ParticlesType:             " << this->ParticlesType << "\n";
  os << indent << "GlyphType:                 " << this->GlyphType << "\n";
  os << indent << "ScaleFactor:               " << this->ScaleFactor << "\n";
  os << indent << "ParticleSize:              " << this->ParticleSize << "\n";
  os << indent << "ParticlesColorBy:          " << this->ParticlesColorBy << "\n";
}

//----------------------------------------------------------------------------
vtkAlgorithmOutput* vtkMRMLParticlesDisplayNode::GetOutputPolyDataConnection()
{
  return this->Glypher->GetOutputPort();
}

//----------------------------------------------------------------------------
void vtkMRMLParticlesDisplayNode::ReadXMLAttributes(const char** atts)
{
  int disabledModify = this->StartModify();

  Superclass::ReadXMLAttributes(atts);

  const char* attName;
  const char* attValue;
  while (*atts != NULL)
    {
    attName = *(atts++);
    attValue = *(atts++);

    if (!strcmp(attName, "particlesType"))
      {
      std::stringstream ss;
      ss << attValue;
      ss >> ParticlesType;
      }
    else if (!strcmp(attName, "glyphType"))
      {
      std::stringstream ss;
      ss << attValue;
      ss >> GlyphType;
      }
    else if (!strcmp(attName, "scaleFactor"))
      {
      std::stringstream ss;
      ss << attValue;
      ss >> ScaleFactor;
      }
    else if (!strcmp(attName, "particleSize"))
      {
      std::stringstream ss;
      ss << attValue;
      ss >> ParticleSize;
      }

    else if (!strcmp(attName, "particlesColorBy"))
      {
      this->SetParticlesColorBy(attValue);
      }
    }
  this->EndModify(disabledModify);
}

//----------------------------------------------------------------------------
void vtkMRMLParticlesDisplayNode::WriteXML(ostream& of, int nIndent)
{
  // Write all attributes not equal to their defaults

  Superclass::WriteXML(of, nIndent);

  vtkIndent indent(nIndent);

  of << indent << " particlesType=\"" << this->ParticlesType << "\"";

  of << indent << " glyphType=\"" << this->GlyphType << "\"";

  of << indent << " scaleFactor=\"" << this->ScaleFactor << "\"";

  of << indent << " particleSize=\"" << this->ParticleSize << "\"";

  of << indent << " particlesColorBy=\"" << this->ParticlesColorBy << "\"";

  of << " ";
}

//----------------------------------------------------------------------------
// Copy the node's attributes to this object.
// Does NOT copy: ID, FilePrefix, Name, ID
void vtkMRMLParticlesDisplayNode::Copy(vtkMRMLNode *anode)
{
  int disabledModify = this->StartModify();

  Superclass::Copy(anode);
  vtkMRMLParticlesDisplayNode *node = vtkMRMLParticlesDisplayNode::SafeDownCast(anode);

  if (node)
    {
    this->SetParticlesColorBy(node->ParticlesColorBy);
    this->SetParticlesType(node->ParticlesType);
    this->SetGlyphType(node->GlyphType);
    this->SetScaleFactor(node->ScaleFactor);
    this->SetParticleSize(node->ParticleSize);
    }

  this->EndModify(disabledModify);
}

//----------------------------------------------------------------------------
void vtkMRMLParticlesDisplayNode::UpdatePolyDataPipeline()
{
  this->SphereSource->SetRadius( this->ParticleSize );
  this->CylinderSource->SetHeight( this->ParticleSize);

  if (this->GetGlyphType() == 0)
    {
    this->GlyphSource = this->CylinderSource;
    }
  else if (this->GetGlyphType() == 1)
    {
    this->GlyphSource = this->SphereSource;
    }

  int type = this->GetParticlesType();
  std::string vectorName;
  if (type == vtkMRMLParticlesDisplayNode::ParticlesTypeAirway)
    {
    vectorName = std::string("hevec2");
    }
  else if (type == vtkMRMLParticlesDisplayNode::ParticlesTypeVessel)
    {
    vectorName = std::string("hevec0");
    }
  else if (type == vtkMRMLParticlesDisplayNode::ParticlesTypeFissure)
    {
    vectorName = std::string("hevec1");
    }

  std::string colorByName;
  if (this->GetParticlesColorBy())
    {
    colorByName = std::string(this->GetParticlesColorBy());
    }

  this->AssignScalar->Assign(
      colorByName.c_str(),
      colorByName.c_str() ? vtkDataSetAttributes::SCALARS : -1,
      vtkAssignAttribute::POINT_DATA);

  this->AssignVector->Assign(
      vectorName.c_str(),
      vectorName.c_str() ? vtkDataSetAttributes::VECTORS : -1,
      vtkAssignAttribute::POINT_DATA);

  this->AssignScalar->SetInputConnection(this->GetInputPolyDataConnection());

  this->AssignScalar->Update();
  this->AssignVector->Update();

  this->Glypher->SetSourceConnection(this->GlyphSource->GetOutputPort());
  this->Glypher->SetColorModeToColorByScalar();
  this->Glypher->SetOrient(1);
  this->Glypher->SetScaleModeToScaleByScalar();
  this->Glypher->SetVectorModeToUseVector();
  this->Glypher->SetScaleFactor(this->GetScaleFactor());

  if ( colorByName.c_str() )
    {
    this->SetScalarVisibility(1);
    }
  //this->Glypher->Modified();
  this->Glypher->Update();
}
