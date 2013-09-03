/*=auto=========================================================================

Portions (c) Copyright 2005 Brigham and Women's Hospital (BWH) All Rights Reserved.

See COPYRIGHT.txt
or http://www.slicer.org/copyright/copyright.txt for details.

Program:   3D Slicer
Module:    $RCSfile: vtkMRMLAirwayNode.cxx,v $
Date:      $Date: 2006/03/03 22:26:39 $
Version:   $Revision: 1.3 $

=========================================================================auto=*/

// VTK includes
#include <vtkCleanPolyData.h>
#include <vtkCommand.h>
#include <vtkExtractPolyDataGeometry.h>
#include <vtkExtractSelectedPolyDataIds.h>
#include <vtkIdTypeArray.h>
#include <vtkInformation.h>
#include <vtkObjectFactory.h>
#include <vtkPlanes.h>
#include <vtkSelection.h>
#include <vtkSelectionNode.h>

// TractographyMRML includes
#include "vtkMRMLAirwayNode.h"
#include "vtkMRMLAirwayStorageNode.h"

// MRML includes
#include <vtkMRMLScene.h>
#include <vtkMRMLAnnotationNode.h>
#include <vtkMRMLAnnotationROINode.h>
#include <vtkMRMLDisplayNode.h>
#include <vtkMRMLModelNode.h>
#include <vtkMRMLModelDisplayNode.h>
#include <vtkMRMLStorageNode.h>

// STD includes
#include <algorithm>
#include <cassert>
#include <math.h>
#include <vector>

//------------------------------------------------------------------------------
vtkCxxSetReferenceStringMacro(vtkMRMLAirwayNode, AnnotationNodeID);

//------------------------------------------------------------------------------
vtkMRMLNodeNewMacro(vtkMRMLAirwayNode);

//------------------------------------------------------------------------------
vtkIdType vtkMRMLAirwayNode::MaxNumberOfFibersToShowByDefault = 10000;

//-----------------------------------------------------------------------------
vtkMRMLAirwayNode::vtkMRMLAirwayNode()
{
  this->ShuffledIds = 0;
  this->ExtractSelectedPolyDataIds = 0;
  this->CleanPolyDataPostSubsampling = 0;
  this->CleanPolyDataPostROISelection = 0;
  this->SubsamplingRatio = 0;
  this->SelectWithAnnotationNode = 0;
  this->SelectionWithAnnotationNodeMode = vtkMRMLAirwayNode::PositiveAnnotationNodeSelection;
  this->AnnotationNode = 0;
  this->AnnotationNodeID = 0;
  this->ExtractPolyDataGeometry = 0;
  this->Planes = 0;
  this->SelectWithAnnotationNode = 0;
  this->EnableShuffleIDs = 1;

  this->PrepareSubsampling();
  this->PrepareROISelection();
}

//-----------------------------------------------------------------------------
vtkMRMLAirwayNode::~vtkMRMLAirwayNode()
{
  this->CleanROISelection();
  this->CleanSubsampling();
}

//----------------------------------------------------------------------------
void vtkMRMLAirwayNode::WriteXML(ostream& of, int nIndent)
{
  // Write all attributes not equal to their defaults
  
  Superclass::WriteXML(of, nIndent);

  vtkIndent indent(nIndent);

  if (this->AnnotationNodeID != NULL) 
    {
    of << indent << " AnnotationNodeRef=\"" << this->AnnotationNodeID << "\"";
    }
  of << indent << " SelectWithAnnotationNode=\"" << this->SelectWithAnnotationNode << "\"";
  of << indent << " SelectionWithAnnotationNodeMode=\"" << this->SelectionWithAnnotationNodeMode << "\"";
  of << indent << " SubsamplingRatio=\"" << this->SubsamplingRatio << "\"";
}



//----------------------------------------------------------------------------
void vtkMRMLAirwayNode::ReadXMLAttributes(const char** atts)
{
  int disabledModify = this->StartModify();

  Superclass::ReadXMLAttributes(atts);
  if (this->AnnotationNodeID != NULL)
    {
    delete[] this->AnnotationNodeID;
    }
  this->SelectWithAnnotationNode = 0;

  const char* attName;
  const char* attValue;
  while (*atts != NULL) 
    {
    attName = *(atts++);
    attValue = *(atts++);

    if (!strcmp(attName, "AnnotationNodeRef")) 
      {
      const size_t n = strlen(attValue) + 1;
      this->AnnotationNodeID = new char[n];
      strcpy(this->AnnotationNodeID, attValue);
      }
    else if (!strcmp(attName, "SelectWithAnnotationNode")) 
      {
      this->SelectWithAnnotationNode = atoi(attValue);
      }
    else if (!strcmp(attName, "SelectionWithAnnotationNodeMode")) 
      {
      this->SelectionWithAnnotationNodeMode = atoi(attValue);
      }
    else if (!strcmp(attName, "SubsamplingRatio")) 
      {
      this->SubsamplingRatio = atof(attValue);
      }
    }


  this->EndModify(disabledModify);
}


//----------------------------------------------------------------------------
// Copy the node's attributes to this object.
// Does NOT copy: ID, FilePrefix, Name, ID
void vtkMRMLAirwayNode::Copy(vtkMRMLNode *anode)
{
  int disabledModify = this->StartModify();

  Superclass::Copy(anode);

  vtkMRMLAirwayNode *node = vtkMRMLAirwayNode::SafeDownCast(anode);

  if (node)
    {
    this->SetSubsamplingRatio(node->SubsamplingRatio);
    this->SetAnnotationNodeID(node->AnnotationNodeID);
    this->SetSelectWithAnnotationNode(node->SelectWithAnnotationNode);
    this->SetSelectionWithAnnotationNodeMode(node->SelectionWithAnnotationNodeMode);
    }

  this->EndModify(disabledModify);
}

//----------------------------------------------------------------------------
void vtkMRMLAirwayNode::PrintSelf(ostream& os, vtkIndent indent)
{
  
  Superclass::PrintSelf(os,indent);

}

//---------------------------------------------------------------------------
void vtkMRMLAirwayNode::ProcessMRMLEvents ( vtkObject *caller,
                                                 unsigned long event,
                                                 void *callData )
{
  if (vtkMRMLAnnotationROINode::SafeDownCast(caller) && (event == vtkCommand::ModifiedEvent))
  {
   vtkDebugMacro("Updating the ROI node");
   this->UpdateROISelection();
  }

  Superclass::ProcessMRMLEvents(caller, event, callData);
  return;
}

//-----------------------------------------------------------
void vtkMRMLAirwayNode::UpdateScene(vtkMRMLScene *scene)
{
   Superclass::UpdateScene(scene);
   int disabledModify = this->StartModify();

  //We are forcing the update of the fields as UpdateScene should only be called after loading data

   if (this->GetAnnotationNodeID() != NULL)
     {
     char* AnnotationNodeID = new char[strlen(this->GetAnnotationNodeID()) + 1];
     strcpy(AnnotationNodeID, this->GetAnnotationNodeID());
     delete[] this->GetAnnotationNodeID();
     this->AnnotationNodeID = NULL;
     this->SetAndObserveAnnotationNodeID(NULL);
     this->SetAndObserveAnnotationNodeID(AnnotationNodeID);
     }
   else
    {
      this->SelectWithAnnotationNode = 0;
    }


   const int ActualSelectWithAnnotationNode = this->SelectWithAnnotationNode;
   this->SelectWithAnnotationNode = -1;
   this->SetSelectWithAnnotationNode(ActualSelectWithAnnotationNode);

   const int ActualSelectionWithAnnotationNodeMode = this->SelectionWithAnnotationNodeMode;
   this->SelectionWithAnnotationNodeMode = -1;
   this->SetSelectionWithAnnotationNodeMode(ActualSelectionWithAnnotationNodeMode);

   double ActualSubsamplingRatio = this->SubsamplingRatio;
   this->SubsamplingRatio = 0.;
   this->SetSubsamplingRatio(ActualSubsamplingRatio);

   this->EndModify(disabledModify);
}

//-----------------------------------------------------------
void vtkMRMLAirwayNode::UpdateReferences()
{
  if (this->AnnotationNodeID != NULL && this->Scene->GetNodeByID(this->AnnotationNodeID) == NULL)
    {
    this->SetAndObserveAnnotationNodeID(NULL);
    }
  this->Superclass::UpdateReferences();
}

//----------------------------------------------------------------------------
void vtkMRMLAirwayNode::UpdateReferenceID(const char *oldID, const char *newID)
{
  this->Superclass::UpdateReferenceID(oldID, newID);
  if (this->AnnotationNodeID && !strcmp(oldID, this->AnnotationNodeID))
    {
    this->SetAnnotationNodeID(newID);
    }
}

//----------------------------------------------------------------------------
vtkPolyData* vtkMRMLAirwayNode::GetFilteredPolyData()
{
  if (this->SelectWithAnnotationNode)
    {
    return this->CleanPolyDataPostROISelection->GetOutput();
    }
  else
    {
    return this->CleanPolyDataPostSubsampling->GetOutput();
    }
}

//----------------------------------------------------------------------------
void vtkMRMLAirwayNode::SetAndObservePolyData(vtkPolyData* polyData)
{
  this->ExtractSelectedPolyDataIds->SetInput(0, polyData);
  this->Superclass::SetAndObservePolyData(polyData);

  if (polyData)
    {
    const vtkIdType numberOfFibers = polyData->GetNumberOfLines();

    std::vector<vtkIdType> idVector;
    for(vtkIdType i = 0;  i < numberOfFibers; i++ )
      {
      idVector.push_back(i);
      }
    random_shuffle ( idVector.begin(), idVector.end() );

    this->ShuffledIds->Initialize();
    this->ShuffledIds->SetNumberOfTuples(numberOfFibers);
    for(vtkIdType i = 0;  i < numberOfFibers; i++ )
      {
      if (this->EnableShuffleIDs)
        {
        this->ShuffledIds->SetValue(i, idVector[i]);
        }
      else
        {
        this->ShuffledIds->SetValue(i, i);
        }
      }
    float subsamplingRatio = this->SubsamplingRatio;

    if (numberOfFibers > this->GetMaxNumberOfFibersToShowByDefault() )
      {
      subsamplingRatio = this->GetMaxNumberOfFibersToShowByDefault() * 1. / numberOfFibers;
      subsamplingRatio = floor(subsamplingRatio * 1e2) / 1e2;
      if (subsamplingRatio < 0.01)
        subsamplingRatio = 0.01;
      }

    this->SetSubsamplingRatio(subsamplingRatio);

    this->UpdateSubsampling();
    }
}

//----------------------------------------------------------------------------
void vtkMRMLAirwayNode
::SetPolyDataToDisplayNode(vtkMRMLModelDisplayNode* modelDisplayNode)
{
  assert(modelDisplayNode->IsA("vtkMRMLAirwayDisplayNode"));
  modelDisplayNode->SetInputPolyData(this->GetFilteredPolyData());
}

//----------------------------------------------------------------------------
void vtkMRMLAirwayNode::SetSubsamplingRatio (float _arg)
  {
  vtkDebugMacro(<< this->GetClassName() << " (" << this << "): setting subsamplingRatio to " << _arg);
  const float oldSubsampling = this->SubsamplingRatio;
  const float newSubsamplingRatio = (_arg<0.?0.:(_arg>1.?1.:_arg));
  if (oldSubsampling != newSubsamplingRatio)
    {
    this->SubsamplingRatio = newSubsamplingRatio;
    this->UpdateSubsampling();
    this->Modified();
    }
  }


//----------------------------------------------------------------------------
void vtkMRMLAirwayNode::SetSelectWithAnnotationNode(int _arg)
{
  vtkDebugMacro(<< this->GetClassName() << " (" << this
                << "): setting SelectWithAnnotationNode  to " << _arg);
  if (this->SelectWithAnnotationNode != _arg)
    {
    this->SelectWithAnnotationNode = _arg;
    this->SetPolyDataToDisplayNodes();
    this->Modified();
    }
}

//----------------------------------------------------------------------------
void vtkMRMLAirwayNode::SetSelectionWithAnnotationNodeMode(int _arg)
{
  vtkDebugMacro(<< this->GetClassName() << " (" << this << "): setting SelectionWithAnnotationNodeMode  to " << _arg); 
  if (this->SelectionWithAnnotationNodeMode != _arg)
    { 
    this->SelectionWithAnnotationNodeMode = _arg;

    if (_arg == vtkMRMLAirwayNode::PositiveAnnotationNodeSelection)
    {
      this->ExtractPolyDataGeometry->ExtractInsideOn();
      this->ExtractPolyDataGeometry->ExtractBoundaryCellsOn();
    } else if (_arg == vtkMRMLAirwayNode::NegativeAnnotationNodeSelection) {
      this->ExtractPolyDataGeometry->ExtractInsideOff();
      this->ExtractPolyDataGeometry->ExtractBoundaryCellsOff();
    }

    this->Modified();
    // \tbd really needed ?
    this->InvokeEvent(vtkMRMLModelNode::PolyDataModifiedEvent, this);
    }
}

//----------------------------------------------------------------------------
vtkMRMLAnnotationNode* vtkMRMLAirwayNode::GetAnnotationNode ( )
{
  vtkMRMLAnnotationNode* node = NULL;

  // Find the node corresponding to the ID we have saved.
  if  ( this->GetScene ( ) && this->GetAnnotationNodeID ( ) )
    {
    vtkMRMLNode* cnode = this->GetScene ( ) -> GetNodeByID ( this->AnnotationNodeID );
    node = vtkMRMLAnnotationNode::SafeDownCast ( cnode );
    }

  return node;
}

//----------------------------------------------------------------------------
void vtkMRMLAirwayNode::SetAndObserveAnnotationNodeID ( const char *id )
{
  if (id)
    {
    vtkDebugMacro("Observing annotation Node: "<<id);
    }
  // Stop observing any old node
  vtkSetAndObserveMRMLObjectMacro (this->AnnotationNode, NULL);

  // Set the ID. This is the "ground truth" reference to the node.
  this->SetAnnotationNodeID ( id );

  // Get the node corresponding to the ID. This pointer is only to observe the object.
  vtkMRMLNode *cnode = this->GetAnnotationNode ( );

  // Observe the node using the pointer.
  vtkSetAndObserveMRMLObjectMacro ( this->AnnotationNode , cnode );
  
  this->UpdateROISelection();

}

//----------------------------------------------------------------------------
void vtkMRMLAirwayNode::PrepareSubsampling()
{
  vtkSelection* sel = vtkSelection::New();
  vtkSelectionNode* node = vtkSelectionNode::New();
  vtkIdTypeArray* arr = vtkIdTypeArray::New();

  this->SubsamplingRatio = 1.;

  this->ShuffledIds = vtkIdTypeArray::New();

  this->ExtractSelectedPolyDataIds = vtkExtractSelectedPolyDataIds::New();

  sel->AddNode(node);

  node->GetProperties()->Set(vtkSelectionNode::CONTENT_TYPE(), vtkSelectionNode::INDICES);
  node->GetProperties()->Set(vtkSelectionNode::FIELD_TYPE(), vtkSelectionNode::CELL);

  arr->SetNumberOfTuples(0);
  node->SetSelectionList(arr);

  this->ExtractSelectedPolyDataIds->SetInput(1, sel);

  this->CleanPolyDataPostSubsampling = vtkCleanPolyData::New();
  this->CleanPolyDataPostSubsampling->ConvertLinesToPointsOff();
  this->CleanPolyDataPostSubsampling->ConvertPolysToLinesOff();
  this->CleanPolyDataPostSubsampling->ConvertStripsToPolysOff();
  this->CleanPolyDataPostSubsampling->PointMergingOff();

  this->CleanPolyDataPostSubsampling->SetInputConnection(
    this->ExtractSelectedPolyDataIds->GetOutputPort());

  arr->Delete();
  node->Delete();
  sel->Delete();
}

//----------------------------------------------------------------------------
void vtkMRMLAirwayNode::UpdateSubsampling()
{
  vtkDebugMacro(<< this->GetClassName() << "Updating the subsampling");
  vtkSelection* sel = vtkSelection::SafeDownCast(this->ExtractSelectedPolyDataIds->GetInput(1));
  vtkPolyData* polyData = this->GetPolyData();
  if (sel && polyData)
    {
    vtkSelectionNode* node = sel->GetNode(0);

    vtkIdTypeArray* arr = vtkIdTypeArray::SafeDownCast(node->GetSelectionList());
    vtkIdType numberOfCellsToKeep = vtkIdType(floor(this->GetPolyData()->GetNumberOfLines() * this->SubsamplingRatio));

    arr->Initialize();
    arr->SetNumberOfTuples(numberOfCellsToKeep);
    if (numberOfCellsToKeep > 0)
      {
      for (vtkIdType i=0; i<numberOfCellsToKeep; i++)
        {
        arr->SetValue(i, this->ShuffledIds->GetValue(i));
        }
      }

    arr->Modified();
    node->Modified();
    sel->Modified();
    }

  /*
  vtkMRMLAirwayDisplayNode *node = this->GetLineDisplayNode();
  if (node != NULL)
    {
      node->SetPolyData(this->GetFilteredPolyData());
    }

  node = this->GetTubeDisplayNode();
  if (node != NULL)
    {
      node->SetPolyData(this->GetFilteredPolyData());
    }
  node = this->GetGlyphDisplayNode();
  if (node != NULL)
    {
      node->SetPolyData(this->GetFilteredPolyData());
    }
  }
    */
    // \tbd why not Modified() instead ?
  this->InvokeEvent(vtkMRMLModelNode::PolyDataModifiedEvent, this);
  //this->Modified();
}

//----------------------------------------------------------------------------
void vtkMRMLAirwayNode::CleanSubsampling()
{
  this->CleanPolyDataPostSubsampling->Delete();
  this->ExtractSelectedPolyDataIds->Delete();
  this->ShuffledIds->Delete();
}

//----------------------------------------------------------------------------
void vtkMRMLAirwayNode::PrepareROISelection()
{
  this->AnnotationNode = NULL;
  this->AnnotationNodeID = NULL;

  this->ExtractPolyDataGeometry = vtkExtractPolyDataGeometry::New();
  this->Planes = vtkPlanes::New();

  this->ExtractPolyDataGeometry->ExtractInsideOn();
  this->ExtractPolyDataGeometry->ExtractBoundaryCellsOn();
  this->ExtractPolyDataGeometry->SetInputConnection(
    this->CleanPolyDataPostSubsampling->GetOutputPort());

  this->SelectionWithAnnotationNodeMode = vtkMRMLAirwayNode::PositiveAnnotationNodeSelection;

  this->CleanPolyDataPostROISelection = vtkCleanPolyData::New();
  this->CleanPolyDataPostROISelection->ConvertLinesToPointsOff();
  this->CleanPolyDataPostROISelection->ConvertPolysToLinesOff();
  this->CleanPolyDataPostROISelection->ConvertStripsToPolysOff();
  this->CleanPolyDataPostROISelection->PointMergingOff();

  this->CleanPolyDataPostROISelection->SetInputConnection(
    this->ExtractPolyDataGeometry->GetOutputPort());

  this->SelectWithAnnotationNode = 0;
}

//----------------------------------------------------------------------------
void vtkMRMLAirwayNode::UpdateROISelection()
{
  vtkMRMLAnnotationROINode* AnnotationROI =
    vtkMRMLAnnotationROINode::SafeDownCast(this->AnnotationNode);
  if (AnnotationROI)
    {
    AnnotationROI->GetTransformedPlanes(this->Planes);
    this->ExtractPolyDataGeometry->SetImplicitFunction(this->Planes);
    }
  if (this->GetSelectWithAnnotationNode())
    {
    this->InvokeEvent(vtkMRMLModelNode::PolyDataModifiedEvent, this);
    }
}


//----------------------------------------------------------------------------
void vtkMRMLAirwayNode::CleanROISelection()
{
  this->SetAndObserveAnnotationNodeID(NULL);
  this->CleanPolyDataPostROISelection->Delete();
  this->ExtractPolyDataGeometry->Delete();
  this->Planes->Delete();
}


//---------------------------------------------------------------------------
vtkMRMLStorageNode* vtkMRMLAirwayNode::CreateDefaultStorageNode()
{
  vtkDebugMacro("vtkMRMLAirwayNode::CreateDefaultStorageNode");
  return vtkMRMLStorageNode::SafeDownCast(vtkMRMLAirwayStorageNode::New());
}

//---------------------------------------------------------------------------
void vtkMRMLAirwayNode::CreateDefaultDisplayNodes()
{
  vtkDebugMacro("vtkMRMLAirwayNode::CreateDefaultDisplayNodes");
  
  //vtkMRMLAirwayDisplayNode *amdn = this->AddDisplayNode();
  //amdn->SetVisibility(1);
}

