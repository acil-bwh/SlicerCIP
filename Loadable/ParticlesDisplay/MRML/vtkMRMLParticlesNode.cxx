/*=auto=========================================================================

Portions (c) Copyright 2005 Brigham and Women's Hospital (BWH) All Rights Reserved.

See COPYRIGHT.txt
or http://www.slicer.org/copyright/copyright.txt for details.

Program:   3D Slicer
Module:    $RCSfile: vtkMRMLParticlesNode.cxx,v $
Date:      $Date: 2006/03/03 22:26:39 $
Version:   $Revision: 1.3 $

=========================================================================auto=*/

#include <sstream>

// TractographyMRML includes
#include "vtkMRMLParticlesDisplayNode.h"
#include "vtkMRMLParticlesNode.h"
#include "vtkMRMLModelStorageNode.h"

// MRML includes
#include <vtkMRMLScene.h>

// VTK includes
#include <vtkCommand.h>
#include <vtkNew.h>
#include <vtkObjectFactory.h>
#include <vtkPolyData.h>
#include <vtkPointData.h>
#include <vtkVersion.h>

// STD includes
#include <algorithm>
#include <cassert>
#include <math.h>
#include <vector>

//------------------------------------------------------------------------------
vtkMRMLNodeNewMacro(vtkMRMLParticlesNode);

//-----------------------------------------------------------------------------
vtkMRMLParticlesNode::vtkMRMLParticlesNode()
{
}

//-----------------------------------------------------------------------------
vtkMRMLParticlesNode::~vtkMRMLParticlesNode()
{
}

//----------------------------------------------------------------------------
// Copy the node's attributes to this object.
// Does NOT copy: ID, FilePrefix, Name, ID
void vtkMRMLParticlesNode::Copy(vtkMRMLNode *anode)
{
  int disabledModify = this->StartModify();

  Superclass::Copy(anode);

  vtkMRMLParticlesNode *node = vtkMRMLParticlesNode::SafeDownCast(anode);

  if (node)
    {
    }

  this->EndModify(disabledModify);
}

//----------------------------------------------------------------------------
void vtkMRMLParticlesNode::PrintSelf(ostream& os, vtkIndent indent)
{
  Superclass::PrintSelf(os,indent);
}

//---------------------------------------------------------------------------
void vtkMRMLParticlesNode::ProcessMRMLEvents ( vtkObject *caller,
                                                 unsigned long event,
                                                 void *callData )
{
  Superclass::ProcessMRMLEvents(caller, event, callData);
  return;
}

//----------------------------------------------------------------------------
vtkMRMLParticlesDisplayNode* vtkMRMLParticlesNode::GetParticlesDisplayNode()
{
  int nnodes = this->GetNumberOfDisplayNodes();
  vtkMRMLParticlesDisplayNode *node = NULL;
  for (int n=0; n<nnodes; n++)
    {
    node = vtkMRMLParticlesDisplayNode::SafeDownCast(this->GetNthDisplayNode(n));
    if (node)
      {
      break;
      }
    }
  return node;
}
//---------------------------------------------------------------------------
vtkMRMLStorageNode* vtkMRMLParticlesNode::CreateDefaultStorageNode()
{
  vtkDebugMacro("vtkMRMLParticlesNode::CreateDefaultStorageNode");
  return vtkMRMLStorageNode::SafeDownCast(vtkMRMLModelStorageNode::New());
}

//-----------------------------------------------------------------------------
void vtkMRMLParticlesNode::GetAvailableScalarNames(std::vector<std::string> &names)
{
  names.clear();
  vtkPolyData *poly = this->GetPolyData();
  if (poly == 0 || poly->GetPointData() == 0)
    {
    return;
    }

  for (int i=0; i<poly->GetPointData()->GetNumberOfArrays(); i++)
    {
    if (poly->GetPointData()->GetArray(i)->GetNumberOfComponents() == 1)
      {
      if (poly->GetPointData()->GetArrayName(i))
        {
        names.push_back(std::string(poly->GetPointData()->GetArrayName(i)));
        }
      else
        {
        std::stringstream ss;
        ss << "Scalar " << i;
        names.push_back(ss.str());
        }
      }
    }
}
//-----------------------------------------------------------------------------
void vtkMRMLParticlesNode::getAvailableVectorNames(std::vector<std::string> &names)
{
  names.clear();
  vtkPolyData *poly = this->GetPolyData();
  if (poly == 0 || poly->GetPointData() == 0)
    {
    return;
    }

  for (int i=0; i<poly->GetPointData()->GetNumberOfArrays(); i++)
    {
    if (poly->GetPointData()->GetArray(i)->GetNumberOfComponents() == 3)
      {
      if (poly->GetPointData()->GetArrayName(i))
        {
        names.push_back(std::string(poly->GetPointData()->GetArrayName(i)));
        }
      else
        {
        std::stringstream ss;
        ss << "Vector " << i;
        names.push_back(ss.str());
        }
      }
    }
}
