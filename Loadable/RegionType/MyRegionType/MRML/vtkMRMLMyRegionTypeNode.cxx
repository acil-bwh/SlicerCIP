/*=auto=========================================================================

Portions (c) Copyright 2005 Brigham and Women's Hospital (BWH) All Rights Reserved.

See COPYRIGHT.txt
or http://www.slicer.org/copyright/copyright.txt for details.

Program:   3D Slicer
Module:    $RCSfile: vtkMRMLAirwayNode.cxx,v $
Date:      $Date: 2006/03/03 22:26:39 $
Version:   $Revision: 1.3 $

=========================================================================auto=*/
// MRML includes
#include "vtkMRMLMyRegionTypeNode.h"

// MRML includes
#include <vtkMRMLNRRDStorageNode.h>
#include "vtkMRMLColorTableNode.h"
#include "vtkMRMLScene.h"

// VTK includes
#include <vtkObjectFactory.h>
#include <vtkImageIterator.h>
#include <vtkImageAccumulate.h>
#include <vtkImageThreshold.h>
#include <vtkImageData.h>

// STD includes
#include <cassert>
#include <list>

#include <math.h>
#include <vnl/vnl_math.h>

//------------------------------------------------------------------------------
vtkMRMLNodeNewMacro(vtkMRMLMyRegionTypeNode);

//-----------------------------------------------------------------------------
vtkMRMLMyRegionTypeNode::vtkMRMLMyRegionTypeNode()
{
  this->SetAttribute("LabelMap", "1");
  /*this->RegionValuesList = NULL;
  this->RegionNamesList = NULL;
  this->TypeValuesList = NULL;
  this->TypeNamesList = NULL;*/
}

//-----------------------------------------------------------------------------
vtkMRMLMyRegionTypeNode::~vtkMRMLMyRegionTypeNode()
{ 
}

//----------------------------------------------------------------------------
void vtkMRMLMyRegionTypeNode::WriteXML(ostream& of, int nIndent)  //to be modified
{
  // Write all attributes not equal to their defaults
  
  Superclass::WriteXML(of, nIndent);

  vtkIndent indent(nIndent);
    
  /*std::list<unsigned int>::iterator listIt;
  
  listIt = this->RegionValuesList.begin();
  while( listIt != this->RegionValuesList.end() )
  {
    of << indent << " Region Values=\"" <<  *listIt << "\"";
    listIt++;
   }
  
  listIt = this->TypeValuesList.begin();
  while( listIt != this->TypeValuesList.end() )
  {
    of << indent << " Type Values=\"" <<  *listIt << "\"";
    listIt++;
   }

  for( unsigned int i = 0; i < this->RegionNamesList.size(); i++ )
  {
    of << indent << " Region Names=\"" << this->RegionNamesList[i] << "\"";
  }

  for( unsigned int i = 0; i < this->TypeNamesList.size(); i++ )
  {
    of << indent << " Type Names=\"" << this->TypeNamesList[i] << "\"";
  }*/
}

//----------------------------------------------------------------------------
void vtkMRMLMyRegionTypeNode::ReadXMLAttributes(const char** atts)
{
  int disabledModify = this->StartModify();

  Superclass::ReadXMLAttributes(atts);

  /*const char* attValue;
  const char* attName;

  std::list<unsigned int>::iterator listIt;

  while (*atts != NULL) 
    {
    attName = *(atts++);
    attValue = *(atts++);
    if (!strcmp(attName, "Region Values")) 
      {
      std::stringstream ss;
      unsigned int val;
      ss << attValue;
      for( int i = 0; i < 3; i++ )
        {
        ss >> val;
        this->RegionValuesList.push_back( val );
        }   
      }
    else if (!strcmp(attName, "Region Names")) 
      {
      std::stringstream ss;
      char* val;
      ss << attValue;
      for( int i = 0; i < 3; i++ )
        {
        ss >> val;
        this->RegionNamesList.push_back( val );
        }   
      }
    else if (!strcmp(attName, "Type Values")) 
      {
      std::stringstream ss;
      unsigned int val;
      ss << attValue;
      for( int i = 0; i < 3; i++ )
        {
        ss >> val;
        this->TypeValuesList.push_back( val );
        }   
      }
    else if (!strcmp(attName, "Type Names")) 
      {
      std::stringstream ss;
      char* val;
      ss << attValue;
      for( int i = 0; i < 3; i++ )
        {
        ss >> val;
        this->TypeNamesList.push_back( val );
        }    
      }
    }*/

  this->EndModify(disabledModify);
}


//----------------------------------------------------------------------------
// Copy the node's attributes to this object.
// Does NOT copy: ID, FilePrefix, Name, ID
void vtkMRMLMyRegionTypeNode::Copy(vtkMRMLNode *anode)
{
  int disabledModify = this->StartModify();

  Superclass::Copy(anode);

  vtkMRMLMyRegionTypeNode *node = vtkMRMLMyRegionTypeNode::SafeDownCast(anode);

  if (node)
    {
    for( unsigned int i = 0; i < node->RegionNamesList.size(); i++)
      {
      this->RegionNamesList.push_back(node->RegionNamesList[i]);
      }
    for( unsigned int i = 0; i < node->TypeNamesList.size(); i++)
      {
      this->TypeNamesList.push_back(node->TypeNamesList[i]);
      }

    std::list<unsigned int>::iterator listIt;

    listIt = node->RegionValuesList.begin();
    while( listIt != node->RegionValuesList.end())
      {
      this->RegionValuesList.push_back(*listIt);
      listIt++;
      }
    
    listIt = node->TypeValuesList.begin();
    while( listIt != node->RegionValuesList.end())
      {
      this->TypeValuesList.push_back(*listIt);
      listIt++;
      }    
    }

  this->EndModify(disabledModify);
}

//----------------------------------------------------------------------------
void vtkMRMLMyRegionTypeNode::PrintSelf(ostream& os, vtkIndent indent) //to be modified
{
  
  Superclass::PrintSelf(os,indent);

  /*os << " Region Values: "<<this->RegionValuesList<< "\"";
  os << " Region Names: "<<this->RegionNamesList<< "\"";
  os << " Type Values: "<<this->TypeValuesList<< "\"";
  os << " Type Names: "<<this->TypeNamesList<< "\"";*/
}


//-----------------------------------------------------------
//void vtkMRMLMyRegionTypeNode::UpdateScene(vtkMRMLScene *scene)
//{
//   Superclass::UpdateScene(scene);
//   int disabledModify = this->StartModify();
//
//  //We are forcing the update of the fields as UpdateScene should only be called after loading data
//
//   if (this->GetAnnotationNodeID() != NULL)
//     {
//     char* AnnotationNodeID = new char[strlen(this->GetAnnotationNodeID()) + 1];
//     strcpy(AnnotationNodeID, this->GetAnnotationNodeID());
//     delete[] this->GetAnnotationNodeID();
//     this->AnnotationNodeID = NULL;
//     this->SetAndObserveAnnotationNodeID(NULL);
//     this->SetAndObserveAnnotationNodeID(AnnotationNodeID);
//     }
//   else
//    {
//      this->SelectWithAnnotationNode = 0;
//    }
//
//
//   const int ActualSelectWithAnnotationNode = this->SelectWithAnnotationNode;
//   this->SelectWithAnnotationNode = -1;
//   this->SetSelectWithAnnotationNode(ActualSelectWithAnnotationNode);
//
//   const int ActualSelectionWithAnnotationNodeMode = this->SelectionWithAnnotationNodeMode;
//   this->SelectionWithAnnotationNodeMode = -1;
//   this->SetSelectionWithAnnotationNodeMode(ActualSelectionWithAnnotationNodeMode);
//
//   double ActualSubsamplingRatio = this->SubsamplingRatio;
//   this->SubsamplingRatio = 0.;
//   this->SetSubsamplingRatio(ActualSubsamplingRatio);
//
//   this->EndModify(disabledModify);
//}

//----------------------------------------------------------------------------
const char* vtkMRMLMyRegionTypeNode::GetNthRegionNameByIndex(int r)
{
  return this->RegionNamesList[r];
}

//----------------------------------------------------------------------------
const char* vtkMRMLMyRegionTypeNode::GetNthRegionNameByValue(unsigned int r)
{  
  std::list<unsigned int>::iterator listIt;
  listIt = this->RegionValuesList.begin();
  int index = 0;
  while( listIt != this->RegionValuesList.end() )
  {
    if( *listIt == r )
    {
      return this->RegionNamesList[index];
    }
    listIt++;
    index++;
  }
}

//----------------------------------------------------------------------------
const char* vtkMRMLMyRegionTypeNode::GetNthTypeNameByIndex(int t)
{
  return this->TypeNamesList[t];
}

//----------------------------------------------------------------------------
const char* vtkMRMLMyRegionTypeNode::GetNthTypeNameByValue(unsigned int t)
{
  std::list<unsigned int>::iterator listIt;
  listIt = this->TypeValuesList.begin();
  int index = 0;
  while( listIt != this->TypeValuesList.end() )
  {
    if( *listIt == t )
    {
      return this->TypeNamesList[index];
    }
    listIt++;
    index++;
  }
}

//----------------------------------------------------------------------------
//REGIONANDTYPE vtkMRMLMyRegionTypeNode::GetNthPairNameByIndex(int index)
//{
//  return this->RegionAndTypeNames[index];
//}
//
////----------------------------------------------------------------------------
//REGIONANDTYPE vtkMRMLMyRegionTypeNode::GetNthPairNameByValue(unsigned short* index)
//{
//  return this->RegionAndTypeNames[index];
//}

//----------------------------------------------------------------------------
void vtkMRMLMyRegionTypeNode::SetAvailableRegionsValues(vtkImageData* image, int nOfColors)
{
  // First collect the values in the label map. We will then figure out
  // how to map them to output values based on the user requests


  int extent[6];
  image->GetExtent(extent);
  
  vtkImageIterator<unsigned short> iIter(image,extent);
  int numC = image->GetNumberOfScalarComponents();
  unsigned int min = VTK_INT_MAX;
  unsigned int max = 0;        
 
  while (!iIter.IsAtEnd())
  {
  	unsigned short *iPtr = iIter.BeginSpan();
      	unsigned short *spanEndPtr = iIter.EndSpan();

      	while (iPtr != spanEndPtr)
      	{
        	// find the bin for this pixel.
        	for (int idxC = 0; idxC < numC; ++idxC)
          	{
          		unsigned int v = static_cast<unsigned int>(*iPtr++);
          		if (v != 0 && v<nOfColors)
            		{           
            			if (v > max)
              			{
              				max = v;
              			}
            			if (v < min)
              			{
              				min = v;
              			}	                                     
			}
		}          	
        }      
    	iIter.NextSpan();
  }
  
  for( unsigned int i = min; i <= max ; i++ )
  {
	this->RegionValuesList.push_back( i );
  }
 
  this->RegionValuesList.unique();
  this->RegionValuesList.sort();
  this->RegionValuesList.unique(); 
}

//---------------------------------------------------------------------------
void vtkMRMLMyRegionTypeNode::SetAvailableTypesValues(vtkImageData* image, int nOfColors)
{
  // First collect the values in the label map. We will then figure out
  // how to map them to output values based on the user requests
  
  int typePlaces[8];
  unsigned short binaryValue = 0;

	for ( int i=0; i<8; i++ )
	{
       		typePlaces[i] = 0;
	}

	for ( int j=7; j>=0; j-- )
	{
		int power = static_cast< int >( vcl_pow( static_cast< float >(2), static_cast< float >(j) ) );
		if ( power <= nOfColors )
       		{
       			typePlaces[j] = 1;
			nOfColors = nOfColors % power;

		}
      	}
	for(int k = 8; k < 16; k++ )
      	{
		binaryValue += static_cast< unsigned short >( typePlaces[k-8] )*static_cast< unsigned short >( vcl_pow( static_cast< float >(2), static_cast< float >(k) ) );
      	}

  int extent[6];
  image->GetExtent(extent);
  
  vtkImageIterator<unsigned short> iIter(image,extent);
  int numC = image->GetNumberOfScalarComponents();
  unsigned int min = VTK_INT_MAX;
  unsigned int max = 0; 
 
  while (!iIter.IsAtEnd())
  {
  	unsigned short *iPtr = iIter.BeginSpan();
      	unsigned short *spanEndPtr = iIter.EndSpan();

      	while (iPtr != spanEndPtr)
      	{
        	// find the bin for this pixel.
        	for (int idxC = 0; idxC < numC; ++idxC)
          	{
          		unsigned int v = static_cast<unsigned int>(*iPtr++);
			
          		if (v != 0 && v>255 && v<binaryValue)
            		{    
            			if (v > max)
              			{
              				max = v;
              			}
            			if (v < min)
              			{
              				min = v;
              			}				
                     	}          		
            	}      
        }      
    	iIter.NextSpan();
  }   

  for( unsigned int i = min; i <= max ; i+=256 )
  {
	this->TypeValuesList.push_back( i );
  }

  this->TypeValuesList.unique();
  this->TypeValuesList.sort();
  this->TypeValuesList.unique(); 
					
}

//---------------------------------------------------------------------------
void vtkMRMLMyRegionTypeNode::SetAvailableRegionsNames(vtkMRMLColorNode* table)
{
  //assert(table->isA("vtkMRMLColorTableNode")); // change to your own LUT node
   
  std::list<unsigned int>::iterator listIt;
  
  listIt = this->RegionValuesList.begin();

  while ( listIt != RegionValuesList.end() )
  {   
    const char *name = table->GetColorName(*listIt);
    this->RegionNamesList.push_back(name);
    listIt++;
  } 
} 

//---------------------------------------------------------------------------
void vtkMRMLMyRegionTypeNode::SetAvailableTypesNames(vtkMRMLColorNode* table)
{
  //assert(table->isA("vtkMRMLColorTableNode")); // change to your own LUT node
  std::list<unsigned int>::iterator listIt;
  listIt = this->TypeValuesList.begin();

  while ( listIt != TypeValuesList.end() )
  { 
    const char *name = table->GetColorName(*listIt);
    this->TypeNamesList.push_back(name);
    listIt++;
  } 
} 

//----------------------------------------------------------------------------
/*void vtkMRMLMyRegionTypeNode::SetAvailablePairsValues()
{
  REGIONANDTYPE Pair;

  for( int i = 0; i = this->RegionValuesList.size(); i++ )
  { 
    Pair.RegionName = RegionNamesList[i];
    Pair.TypeName   = TypeNamesList[i];
    this->RegionAndTypeNames.push_back( Pair );
  }  
}*/

//----------------------------------------------------------------------------
vtkMRMLStorageNode* vtkMRMLMyRegionTypeNode::CreateDefaultStorageNode()
{
  return vtkMRMLNRRDStorageNode::New();
  // return vtkMRMLStorageNode::New();
}

