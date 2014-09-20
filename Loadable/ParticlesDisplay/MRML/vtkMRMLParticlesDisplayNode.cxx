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

// STD includes
#include <cassert>
#include <math.h>
#include <vnl/vnl_math.h>

//----------------------------------------------------------------------------
vtkMRMLNodeNewMacro(vtkMRMLParticlesDisplayNode);

//----------------------------------------------------------------------------
vtkMRMLParticlesDisplayNode::vtkMRMLParticlesDisplayNode()
{
  this->Glypher = vtkGlyph3DWithScaling::New();
  this->GlyphSource = vtkCylinderSource::New();
  this->ParticlesType = vtkMRMLParticlesDisplayNode::ParticlesTypeAirway;
}

//----------------------------------------------------------------------------
vtkMRMLParticlesDisplayNode::~vtkMRMLParticlesDisplayNode()
{
  this->Glypher->Delete();
  this->GlyphSource->Delete();
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

  vtkPolyData *poly = this->GetInputPolyData();

  if (poly == 0)
    {
    return;
    }

  if (poly->GetPointData())
    {
    vtkDataArray *vectorData = poly->GetPointData()->GetArray(vectorName.c_str());
    poly->GetPointData()->SetVectors(vectorData);
    poly->Modified();
    }

  this->Glypher->SetInputConnection(this->GetInputPolyDataConnection());

  this->Glypher->SetSourceConnection(this->GlyphSource->GetOutputPort());

  this->Glypher->SetColorModeToColorByScalar();
  this->Glypher->SetOrient(1);
  this->Glypher->SetScaleModeToScaleByScalar();
  this->Glypher->SetVectorModeToUseVector();

  this->Glypher->Update();
}