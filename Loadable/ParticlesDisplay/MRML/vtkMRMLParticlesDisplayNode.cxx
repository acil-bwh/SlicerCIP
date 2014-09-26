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
#include <vtkAssignAttribute.h>

// STD includes
#include <cassert>
#include <math.h>
#include <vnl/vnl_math.h>

//----------------------------------------------------------------------------
vtkMRMLNodeNewMacro(vtkMRMLParticlesDisplayNode);

//----------------------------------------------------------------------------
vtkMRMLParticlesDisplayNode::vtkMRMLParticlesDisplayNode()
{
  this->AssignScalar = vtkAssignAttribute::New();
  this->AssignVector = vtkAssignAttribute::New();
  this->Glypher = vtkGlyph3DWithScaling::New();
  this->GlyphSource = vtkCylinderSource::New();
  this->ParticlesType = vtkMRMLParticlesDisplayNode::ParticlesTypeAirway;
  this->ParticlesColorBy = 0;

  this->AssignVector->SetInputConnection(this->AssignScalar->GetOutputPort());
  this->Glypher->SetInputConnection(this->AssignVector->GetOutputPort());
  this->Glypher->SetSourceConnection(this->GlyphSource->GetOutputPort());
}

//----------------------------------------------------------------------------
vtkMRMLParticlesDisplayNode::~vtkMRMLParticlesDisplayNode()
{
  this->Glypher->Delete();
  this->GlyphSource->Delete();
  this->AssignScalar->Delete();
  this->AssignVector->Delete();
  this->SetParticlesColorBy(0);
}

//----------------------------------------------------------------------------
void vtkMRMLParticlesDisplayNode::PrintSelf(ostream& os, vtkIndent indent)
{
  Superclass::PrintSelf(os,indent);
}

//----------------------------------------------------------------------------
vtkAlgorithmOutput* vtkMRMLParticlesDisplayNode::GetOutputPolyDataConnection()
{
  return this->Glypher->GetOutputPort();
}

//----------------------------------------------------------------------------
void vtkMRMLParticlesDisplayNode::UpdatePolyDataPipeline()
{
  //this->Superclass::UpdatePolyDataPipeline();

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

  this->Glypher->SetColorModeToColorByScalar();
  this->Glypher->SetOrient(1);
  this->Glypher->SetScaleModeToScaleByScalar();
  this->Glypher->SetVectorModeToUseVector();

  if ( colorByName.c_str() )
    {
    this->SetScalarVisibility(1);
    }
  //this->Glypher->Modified();
  this->Glypher->Update();
}