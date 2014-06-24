/*=auto=========================================================================

Portions (c) Copyright 2005 Brigham and Women\"s Hospital (BWH) All Rights Reserved.

See COPYRIGHT.txt
or http://www.slicer.org/copyright/copyright.txt for details.

Program:   3D Slicer
Module:    $RCSfile: vtkMRMLVolumeDisplayNode.cxx,v $
Date:      $Date: 2006/03/17 15:10:10 $
Version:   $Revision: 1.2 $

=========================================================================auto=*/
#include "vtkMRMLMyRegionTypeDisplayNode.h"
//#include "vtkMRMLProceduralColorNode.h"
#include "vtkMRMLScene.h"

#include "vtkMRMLMyRegionTypeNode.h"
#include "vtkMRMLColorNode.h"

// VTK includes
#include <vtkImageData.h>
#include <vtkImageMapToColors.h>
#include <vtkLookupTable.h>
#include <vtkObjectFactory.h>

// STD includes
#include <cassert>
#include <math.h>
#include <vnl/vnl_math.h>

//----------------------------------------------------------------------------
vtkMRMLNodeNewMacro(vtkMRMLMyRegionTypeDisplayNode);

//----------------------------------------------------------------------------
vtkMRMLMyRegionTypeDisplayNode::vtkMRMLMyRegionTypeDisplayNode()
{  
}

//----------------------------------------------------------------------------
vtkMRMLMyRegionTypeDisplayNode::~vtkMRMLMyRegionTypeDisplayNode()
{
  /*double c[4];
  for( int i = 1; i < LUT->GetNumberOfTableValues(); i++ )
  {
    LUT->GetTableValue(i,c);
    c[3] = 1.0;
    LUT->GetTableValue(i,c);
    LUT->Modified();    
   }*/
}

//----------------------------------------------------------------------------
void vtkMRMLMyRegionTypeDisplayNode::PrintSelf(ostream& os, vtkIndent indent)
{
  Superclass::PrintSelf(os,indent);
}

//----------------------------------------------------------------------------
void vtkMRMLMyRegionTypeDisplayNode::ProcessMRMLEvents ( vtkObject *caller,
                                           unsigned long event, 
                                           void *callData )
{
  Superclass::ProcessMRMLEvents(caller, event, callData);
}

//----------------------------------------------------------------------------
void vtkMRMLMyRegionTypeDisplayNode::SetRegionToShow(const char* region)
{
  this->regionsToShow.push_back(region);
}

//----------------------------------------------------------------------------
void vtkMRMLMyRegionTypeDisplayNode::SetTypeToShow(const char* type)
{
  this->typesToShow.push_back(type);
}

//----------------------------------------------------------------------------
/*void vtkMRMLMyRegionTypeDisplayNode::SetPairToShow(REGIONANDTYPE pair)
{
  this->pairsToShow.push_back(pair);
}*/

//----------------------------------------------------------------------------
void vtkMRMLMyRegionTypeDisplayNode::ShowSelectedLabels(vtkMRMLMyRegionTypeNode* node, const char* region, const char* type)
{  

  this->regionsToShow.clear();
  this->typesToShow.clear();
  
  double c[4];

  if( region != NULL && type != NULL && std::string(region) != std::string("NO REGIONS") && std::string(type) != std::string("NO TYPES") && std::string(region) != std::string("ALL REGIONS") && std::string(region) != std::string("ALL TYPES") )
  {
	std::list<unsigned int>::iterator rlistIt;
	rlistIt = node->RegionValuesList.begin();  
  	vtkMRMLColorNode* colorNode = vtkMRMLColorNode::SafeDownCast( this->GetColorNode() );
  	this->LUT = colorNode->GetLookupTable();

  	while( rlistIt != node->RegionValuesList.end() )
  	{ 
   	 	unsigned int index = (unsigned int) *rlistIt; 
    		this->LUT->GetTableValue(index,c);
    		c[3] = 0;
    		this->LUT->SetTableValue(index,c);
    		this->LUT->Modified();
    		rlistIt++;       
  	}

	std::list<unsigned int>::iterator tlistIt;
	tlistIt = node->TypeValuesList.begin();
  	while( tlistIt != node->TypeValuesList.end() )
  	{ 
    		unsigned int index = (unsigned int) *tlistIt; 
   		this->LUT->GetTableValue(index,c);
    		c[3] = 0;
    		this->LUT->SetTableValue(index,c);
    		this->LUT->Modified();
    		tlistIt++;       
  	}

	std::vector<unsigned int> r;
	this->SetRegionToShow(region);
	rlistIt = node->RegionValuesList.begin();
	for( unsigned int i = 0; i < this->regionsToShow.size(); i++ )
	{    
		for( unsigned int j = 0; j < node->RegionNamesList.size(); j++)
	      	{
			if( std::string( node->GetNthRegionNameByIndex(j) ) == std::string( this->regionsToShow[i] ) )
			{
			  	r.push_back( (unsigned int) *rlistIt ); 
			}
			else
			{
			  	rlistIt++;
			}
		 }
	}

	std::vector<unsigned int> t;
	this->SetTypeToShow(type);
   	tlistIt = node->TypeValuesList.begin();
  	for( unsigned int i = 0; i < this->typesToShow.size(); i++ )
  	{  
		for( unsigned int j = 0; j < node->TypeNamesList.size(); j++)
		{  
	 		if( std::string( node->GetNthTypeNameByIndex(j) ) == std::string( typesToShow[i] ) )
		  	{
			 	t.push_back( (unsigned int) *tlistIt ); 
			}
		  	else
		  	{
				tlistIt++;
		  	}
	  	}
  	}

	for( unsigned int f = 0; f < r.size(); f++ )
	{
		for( unsigned int g = 0; g < t.size(); g++ )
		{
			c[0] = 1.00; c[1] = 1.00; c[2] = 1.00; c[3] = 1.00; 
			unsigned int index = r.at(f) + t.at(g);
			this->LUT->SetTableValue(index,c);
			node->TypeValuesList.push_back( index );
			std::string name = std::string( std::string( node->GetNthTypeNameByIndex(g) + std::string("_IN_") + node->GetNthRegionNameByIndex(f) ) );
			const char* charName = name.c_str();
			colorNode->SetColorName( index, charName );
		}
	}
  }

  else 
  {
	if( region != NULL )
	{
	        std::list<unsigned int>::iterator rlistIt;
		rlistIt = node->RegionValuesList.begin();  
	  	vtkMRMLColorNode* colorNode = vtkMRMLColorNode::SafeDownCast( this->GetColorNode() );
	  	this->LUT = colorNode->GetLookupTable();
	
	  	while( rlistIt != node->RegionValuesList.end() )
	  	{ 
	   	 	unsigned int index = (unsigned int) *rlistIt; 
	    		this->LUT->GetTableValue(index,c);
	    		c[3] = 0;
	    		this->LUT->SetTableValue(index,c);
	    		this->LUT->Modified();
	    		rlistIt++;       
	  	}
		if( std::string(region) != std::string("NO REGIONS") )
		{
			if( std::string(region) == std::string("ALL REGIONS") )
			{
				this->ShowAllRegions();
			}
			else
			{
				this->SetRegionToShow(region);
				rlistIt = node->RegionValuesList.begin();
		  		for( unsigned int i = 0; i < this->regionsToShow.size(); i++ )
		  		{    
			  		for( unsigned int j = 0; j < node->RegionNamesList.size(); j++)
		      			{
					  	if( std::string( node->GetNthRegionNameByIndex(j) ) == std::string( this->regionsToShow[i] ) )
					  	{
						  	unsigned int index = (unsigned int) *rlistIt; 
						  	this->LUT->GetTableValue(index,c);
						  	c[3] = 1;
						  	this->LUT->SetTableValue(index,c);
						  	this->LUT->Modified();
						  	break;
					  	}
					  	else
					  	{
						  	rlistIt++;
					  	}
			 		}
		  		}
			}
		}
	}

  	if( type != NULL )
  	{
  		std::list<unsigned int>::iterator tlistIt;
		tlistIt = node->TypeValuesList.begin();
  		while( tlistIt != node->TypeValuesList.end() )
  		{ 
    			unsigned int index = (unsigned int) *tlistIt; 
   			this->LUT->GetTableValue(index,c);
    			c[3] = 0;
    			this->LUT->SetTableValue(index,c);
    			this->LUT->Modified();
    			tlistIt++;       
  		}
		if( std::string(type) != std::string("NO TYPES") )
		{
			if( std::string(type) == std::string("ALL TYPES") )
			{
				this->ShowAllTypes();
			}
			else
			{
				this->SetTypeToShow(type);
   				tlistIt = node->TypeValuesList.begin();
  				for( unsigned int i = 0; i < this->typesToShow.size(); i++ )
  				{  
		  			for( unsigned int j = 0; j < node->TypeNamesList.size(); j++)
		  			{  
			  			if( std::string( node->GetNthTypeNameByIndex(j) ) == std::string( typesToShow[i] ) )
			  			{
				  			unsigned int index = (unsigned int) *tlistIt; 
				  			this->LUT->GetTableValue(index,c);
				  			c[3] = 1;
				  			this->LUT->SetTableValue(index,c);
				  			this->LUT->Modified();
				  			break;
			  			}
			  			else
			  			{
					  		tlistIt++;
			  			}
		  			}
  				}
			}
		}
  	}
  }
}

//----------------------------------------------------------------------------
void vtkMRMLMyRegionTypeDisplayNode::ShowAllRegions()
{
  	double c[4];
	std::cout<<"in ShowAllRegions"<<std::endl;
	vtkMRMLColorNode* colorNode = vtkMRMLColorNode::SafeDownCast( this->GetColorNode() );
	if( colorNode )
	{
  		for( int i = 1; i < 256; i++ )
  		{ 
   			this->LUT->GetTableValue(i,c);
 			if( c[3] == 0 )
			{
				c[3] = 1;
    				this->LUT->SetTableValue(i,c);
    				this->LUT->Modified();
			}   
  		} 
	}
}

//----------------------------------------------------------------------------
void vtkMRMLMyRegionTypeDisplayNode::ShowAllTypes()
{
	vtkMRMLColorNode* colorNode = vtkMRMLColorNode::SafeDownCast( this->GetColorNode() );
	double c[4];	
	std::cout<<"in ShowAllTypes"<<std::endl;
	if( colorNode )
	{
		int nOfColors = 80;
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


  		this->LUT = colorNode->GetLookupTable();
      
  		for( int i = 256; i < binaryValue; i++ )
  		{ 
   			this->LUT->GetTableValue(i,c);
 			if( c[3] == 0 )
			{
				c[3] = 1;
    				this->LUT->SetTableValue(i,c);
    				this->LUT->Modified();
			}   
  		} 
	}
}
