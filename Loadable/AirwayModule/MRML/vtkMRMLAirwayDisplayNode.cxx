/*=auto=========================================================================

Portions (c) Copyright 2005 Brigham and Women's Hospital (BWH) All Rights Reserved.

See COPYRIGHT.txt
or http://www.slicer.org/copyright/copyright.txt for details.

Program:   3D Slicer
Module:    $RCSfile: vtkMRMLAirwayDisplayNode.cxx,v $
Date:      $Date: 2006/03/03 22:26:39 $
Version:   $Revision: 1.3 $

=========================================================================auto=*/

// MRMLTractography includes
#include "vtkMRMLAirwayDisplayNode.h"
#include "vtkMRMLScene.h"
#include "vtkMRMLNode.h"

// MRML includes
#include "vtkMRMLDisplayableNode.h"
#include "vtkMRMLScene.h"
#include "vtkMRMLModelDisplayNode.h"

// VTK includes
#include <vtkCommand.h>
#include <vtkObjectFactory.h>
#include <vtkTensorGlyph.h>
#include <vtkSphereSource.h>
#include <vtkPolyData.h>
#include <vtkPointData.h>
#include <vtkFieldData.h>

// STD includes
#include <sstream>

//----------------------------------------------------------------------------
vtkMRMLNodeNewMacro(vtkMRMLAirwayDisplayNode);

//----------------------------------------------------------------------------
vtkMRMLAirwayDisplayNode::vtkMRMLAirwayDisplayNode()
{
  this->TensorGlyph = vtkTensorGlyph::New();

  this->BackfaceCulling = 0;

  // Enumerated
  this->ColorMode = this->colorModeSolid;
  this->SetColor(1,0.157,0);

  this->ScalarRange[0] = 0.;
  this->ScalarRange[1] = 1.;
}

//----------------------------------------------------------------------------
vtkMRMLAirwayDisplayNode::~vtkMRMLAirwayDisplayNode()
{
  this->TensorGlyph->Delete();
}

//----------------------------------------------------------------------------
void vtkMRMLAirwayDisplayNode::WriteXML(ostream& of, int nIndent)
{
  // Write all attributes not equal to their defaults
  
  Superclass::WriteXML(of, nIndent);

  vtkIndent indent(nIndent);

  of << indent << " colorMode =\"" << this->ColorMode << "\"";

}

//----------------------------------------------------------------------------
void vtkMRMLAirwayDisplayNode::ReadXMLAttributes(const char** atts)
{
  int disabledModify = this->StartModify();

  Superclass::ReadXMLAttributes(atts);

  const char* attName;
  const char* attValue;
  while (*atts != NULL) 
    {
    attName = *(atts++);
    attValue = *(atts++);

    if (!strcmp(attName, "colorMode")) 
      {
      std::stringstream ss;
      ss << attValue;
      int colorMode;
      ss >> colorMode;
      this->SetColorMode(colorMode);
      }

    }

  this->EndModify(disabledModify);
}

//----------------------------------------------------------------------------
// Copy the node's attributes to this object.
// Does NOT copy: ID, FilePrefix, Name, ID
void vtkMRMLAirwayDisplayNode::Copy(vtkMRMLNode *anode)
{
  int disabledModify = this->StartModify();

 vtkMRMLAirwayDisplayNode *node = (vtkMRMLAirwayDisplayNode *) anode;
 this->SetColorMode(node->ColorMode); // do this first, since it affects how events are processed in glyphs

  Superclass::Copy(anode);

  this->EndModify(disabledModify);
  }

//----------------------------------------------------------------------------
void vtkMRMLAirwayDisplayNode::PrintSelf(ostream& os, vtkIndent indent)
{
  //int idx;
  
  Superclass::PrintSelf(os,indent);
  os << indent << "ColorMode:             " << this->ColorMode << "\n";
}

//-----------------------------------------------------------
void vtkMRMLAirwayDisplayNode::UpdateScene(vtkMRMLScene *scene)
{
   Superclass::UpdateScene(scene);

}

//-----------------------------------------------------------
void vtkMRMLAirwayDisplayNode::UpdateReferences()
{
  Superclass::UpdateReferences();

}

//----------------------------------------------------------------------------
void vtkMRMLAirwayDisplayNode::UpdateReferenceID(const char *oldID, const char *newID)
{
  this->Superclass::UpdateReferenceID(oldID, newID);
}


//----------------------------------------------------------------------------
std::vector<int> vtkMRMLAirwayDisplayNode::GetSupportedColorModes()
{
  std::vector<int> modes;

  modes.clear();
  //modes.push_back(vtkMRMLDiffusionTensorDisplayPropertiesNode::FractionalAnisotropy);

  return modes;
}

//----------------------------------------------------------------------------
void vtkMRMLAirwayDisplayNode::UpdatePolyDataPipeline()
{
  if (!this->GetInputPolyData())
    return;


 this->TensorGlyph->SetInputConnection(
    this->Superclass::GetOutputPort()
  );

 vtkSphereSource* sphere = vtkSphereSource::New();
 this->TensorGlyph->SetSource(sphere->GetOutput());
 sphere->Delete();
}

//----------------------------------------------------------------------------
vtkAlgorithmOutput* vtkMRMLAirwayDisplayNode::GetOutputPort()
{
  return this->TensorGlyph->GetOutputPort();
}


