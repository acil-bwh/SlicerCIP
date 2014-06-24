/*=auto=========================================================================

Portions (c) Copyright 2005 Brigham and Women's Hospital (BWH) All Rights Reserved.

See COPYRIGHT.txt
or http://www.slicer.org/copyright/copyright.txt for details.

Program:   3D Slicer
Module:    $RCSfile: vtkMRMLChestRTColorTableNode.cxx,v $
Date:      $Date: 2006/03/03 22:26:39 $
Version:   $Revision: 1.0 $

=========================================================================auto=*/

// MRML includes
#include "vtkMRMLChestRTColorTableNode.h"
#include "vtkMRMLColorTableStorageNode.h"

// VTK includes
#include <vtkLookupTable.h>
#include <vtkObjectFactory.h>

#include <math.h>
#include <vnl/vnl_math.h>
// STD includes
#include <sstream>

vtkCxxSetObjectMacro(vtkMRMLChestRTColorTableNode, LookupTable, vtkLookupTable);

//------------------------------------------------------------------------------
vtkMRMLNodeNewMacro(vtkMRMLChestRTColorTableNode);

//----------------------------------------------------------------------------
vtkMRMLChestRTColorTableNode::vtkMRMLChestRTColorTableNode()
{
  this->SetName("");
  this->SetDescription("Chest Region/Type Color Table");
  this->LookupTable = NULL;
  this->LastAddedColor = -1;
}

//----------------------------------------------------------------------------
vtkMRMLChestRTColorTableNode::~vtkMRMLChestRTColorTableNode()
{
  if (this->LookupTable)
    {
    this->LookupTable->Delete();
    }
}

//----------------------------------------------------------------------------
void vtkMRMLChestRTColorTableNode::WriteXML(ostream& of, int nIndent)
{
  // Write all attributes not equal to their FullRainbows

  Superclass::WriteXML(of, nIndent);

  vtkIndent indent(nIndent);

  // only print out the look up table size so that the table can be
  // initialized properly
  if (this->LookupTable != NULL)
    {
    of << " numcolors=\"" << this->LookupTable->GetNumberOfTableValues() << "\"";
    }
}

//----------------------------------------------------------------------------
void vtkMRMLChestRTColorTableNode::ReadXMLAttributes(const char** atts)
{
  int disabledModify = this->StartModify();

  Superclass::ReadXMLAttributes(atts);

  const char* attName;
  const char* attValue;
  int numColours;
  while (*atts != NULL)
  {
      attName = *(atts++);
      attValue = *(atts++);
      if (!strcmp(attName, "numcolors"))
        {
        std::stringstream ss;
        ss << attValue;
        ss >> numColours;
        vtkDebugMacro("Setting the look up table size to " << numColours << "\n");
        //this->SetNumberOfColors(numColours);
        // init the table to black/opacity 0 with no name, just in case we're missing values
        const char *noName = this->GetNoName();
        if (!noName)
          {
          noName = "(none)";
          }
        for (int i = 0; i < numColours; i++)
          {
          //this->SetColor(i, noName, 0.0, 0.0, 0.0, 0.0);
          }
        }
      else  if (!strcmp(attName, "colors"))
      {
      std::stringstream ss;
      for (int i = 0; i < this->LookupTable->GetNumberOfTableValues(); i++)
        {
        vtkDebugMacro("Reading colour " << i << " of " << this->LookupTable->GetNumberOfTableValues() << endl);
        ss << attValue;
        // index name r g b a
        int index;
        std::string name;
        double r, g, b, a;
        ss >> index;
        ss >> name;
        ss >> r;
        ss >> g;
        ss >> b;
        ss >> a;
        // might have a version of a mrml file that has tick marks around
        // the name
        const char *tickPtr = strstr(name.c_str(), "'");
        if (tickPtr)
          {
          size_t firstValidChar = name.find_first_not_of("'");
          size_t lastValidChar = name.find_last_not_of("'");
          name = name.substr(firstValidChar, 1 + lastValidChar - firstValidChar);
          }
        vtkDebugMacro("Adding colour at index " << index << ", r = " << r << ", g = " << g << ", b = " << b << ", a = " << a << " and then setting name to " << name.c_str() << endl);

        if (this->SetColorNameWithSpaces(index, name.c_str(), "_") != 0)
          {
          this->LookupTable->SetTableValue(index, r, g, b, a);
          }
        }
      // set the table range
      if ( this->LookupTable->GetNumberOfTableValues() > 0 )
        {
        this->LookupTable->SetRange(0,  this->LookupTable->GetNumberOfTableValues() - 1);
        }
      this->NamesInitialisedOn();
      }
      else if (!strcmp(attName, "type"))
      {
      int type;
      std::stringstream ss;
      ss << attValue;
      ss >> type;
      this->SetType(type);
      }
      else
      {
          vtkDebugMacro ("Unknown attribute name " << attName << endl);
      }
  }
  this->EndModify(disabledModify);
}

//----------------------------------------------------------------------------
// Copy the node's attributes to this object.
// Does NOT copy: ID, FilePrefix, Name, ID
void vtkMRMLChestRTColorTableNode::Copy(vtkMRMLNode *anode)
{
  int disabledModify = this->StartModify();

  Superclass::Copy(anode);
  vtkMRMLChestRTColorTableNode *node = (vtkMRMLChestRTColorTableNode *) anode;
  if (node->LookupTable)
    {
    this->SetLookupTable(node->LookupTable);
    }
  this->EndModify(disabledModify);

}

//----------------------------------------------------------------------------
void vtkMRMLChestRTColorTableNode::PrintSelf(ostream& os, vtkIndent indent)
{
  Superclass::PrintSelf(os,indent);

  if (this->LookupTable != NULL)
    {
    os << indent << "Look up table:\n";
    this->LookupTable->PrintSelf(os, indent.GetNextIndent());
    }
}


//----------------------------------------------------------------------------
void vtkMRMLChestRTColorTableNode::SetTypeToChestRTLabels()
{
    this->SetType(this->ChestRTLabels);
}

//----------------------------------------------------------------------------
const char* vtkMRMLChestRTColorTableNode::GetTypeAsString()
{  
  if (this->Type == this->ChestRTLabels)
    {
    return "Chest RT Labels";
    }
  
  return "(unknown)";
}

//---------------------------------------------------------------------------
void vtkMRMLChestRTColorTableNode::ProcessMRMLEvents ( vtkObject *caller,
                                           unsigned long event,
                                           void *callData )
{
  Superclass::ProcessMRMLEvents(caller, event, callData);
  return;
}

//---------------------------------------------------------------------------
void vtkMRMLChestRTColorTableNode::SetType(int type)
{ 
  if (this->GetLookupTable() != NULL && this->Type == type)
  {
    vtkDebugMacro("SetType: type is already set to " << type <<  " = " << this->GetTypeAsString());
    return;
  }

  this->Type = type;
  vtkDebugMacro(<< this->GetClassName() << " (" << this << "): setting Type to " << type << " = " << this->GetTypeAsString());

  
  if (this->GetLookupTable() == NULL)
  {
      vtkDebugMacro("vtkMRMLChestRTColorTableNode::SetType Creating a new lookup table (was null) of type " << this->GetTypeAsString() << "\n");
      vtkLookupTable *table = vtkLookupTable::New();
      this->SetLookupTable(table);
      table->Delete();
      this->GetLookupTable()->SetTableRange(0, 65535);
  }

  if (this->Type == this->ChestRTLabels)
  {
      this->GetLookupTable()->SetNumberOfTableValues(65000);
      this->GetLookupTable()->SetTableRange(0,65000);
      this->Names.clear();
      this->Names.resize(this->GetLookupTable()->GetNumberOfTableValues());

      if (this->SetColorName(0, "UNDEFINEDREGION") != 0)
      {
 	double* r001 = new double[4]; r001[0] = 0.00; r001[1] = 0.00; r001[2] = 0.00; r001[3] = 1.00;
        this->GetLookupTable()->SetTableValue(0, r001);
      }

      if (this->SetColorName(1, "WHOLELUNG") != 0)
      {
	double* r002 = new double[4]; r002[0] = 0.42; r002[1] = 0.38; r002[2] = 0.75; r002[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(1, r002);
      }
      if (this->SetColorName(2, "RIGHTLUNG") != 0)
      {
	double* r003 = new double[4]; r003[0] = 0.26; r003[1] = 0.64; r003[2] = 0.10;r003[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(2, r003);
      }
      if (this->SetColorName(3, "LEFTLUNG") != 0)
      {
	double* r004 = new double[4]; r004[0] = 0.80; r004[1] = 0.11; r004[2] = 0.36; r004[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(3, r004);
      }
      if (this->SetColorName(4, "RIGHTSUPERIORLOBE") != 0)
      {
      	double* r005 = new double[4]; r005[0] = 0.04; r005[1] = 0.00; r005[2] = 0.00; r005[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(4, r005);
      }
      if (this->SetColorName(5, "RIGHTMIDDLELOBE") != 0)
      {
      	double* r006 = new double[4]; r006[0] = 0.05; r006[1] = 0.00; r006[2] = 0.00; r006[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(5, r006);
      }
      if (this->SetColorName(6, "RIGHTINFERIORLOBE") != 0)
      {
	double* r007 = new double[4]; r007[0] = 0.06; r007[1] = 0.00; r007[2] = 0.00; r007[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(6, r007);
      }
      if (this->SetColorName(7, "LEFTSUPERIORLOBE") != 0)
      {
	double* r008 = new double[4]; r008[0] = 0.07; r008[1] = 0.00; r008[2] = 0.00; r008[3] = 1.00;
        this->GetLookupTable()->SetTableValue(7, r008);
      }
      if (this->SetColorName(8, "LEFTINFERIORLOBE") != 0)
      {
	double* r009 = new double[4]; r009[0] = 0.08; r009[1] = 0.00; r009[2] = 0.00; r009[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(8, r009);
      }
      if (this->SetColorName(9, "LEFTUPPERTHIRD") != 0)
      {
        double* r010 = new double[4]; r010[0] = 0.95; r010[1] = 0.03; r010[2] = 0.03; r010[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(9, r010);
      }
      if (this->SetColorName(10, "LEFTMIDDLETHIRD") != 0)
      {
        double* r011 = new double[4]; r011[0] = 0.95; r011[1] = 0.89; r011[2] = 0.03; r011[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(10, r011);
      }
      if (this->SetColorName(11, "LEFTLOWERTHIRD") != 0)
      {
        double* r012 = new double[4]; r012[0] = 0.03; r012[1] = 0.34; r012[2] = 0.95; r012 [3] = 1.00; 
        this->GetLookupTable()->SetTableValue(11, r012);
      }
      if (this->SetColorName(12, "RIGHTUPPERTHIRD") != 0)
      {
	double* r013 = new double[4]; r013[0] = 0.06; r013[1] = 0.91; r013[2] = 0.91; r013 [3] = 1.00; 
        this->GetLookupTable()->SetTableValue(12, r013);
      }
      if (this->SetColorName(13, "RIGHTMIDDLETHIRD") != 0)
      {
        double* r014 = new double[4]; r014[0] = 1.00; r014[1] = 0.00; r014[2] = 0.91; r014[3] = 1.00;
        this->GetLookupTable()->SetTableValue(13, r014);
      }
      if (this->SetColorName(14, "RIGHTLOWERTHIRD") != 0)
      {
        double* r015 = new double[4]; r015[0] = 0.34; r015[1] = 0.41; r015[2] = 0.09; r015[3] = 1.00;
        this->GetLookupTable()->SetTableValue(14, r015);
      }
      if (this->SetColorName(15, "MEDIASTINUM") != 0)
      {
	  double* r016 = new double[4]; r016[0] = 0.00; r016[1] = 0.06; r016[2] = 0.00; r016[3] = 1.00; 
          this->GetLookupTable()->SetTableValue(15, r016);
          }
      if (this->SetColorName(16, "WHOLEHEART") != 0)
      {
        double* r017 = new double[4]; r017[0] = 0.00; r017[1] = 0.07; r017[2] = 0.00; r017[3] = 1.00; //
        this->GetLookupTable()->SetTableValue(16, 0.5, 0.8, 0.2, 1.0);
      }
      if (this->SetColorName(17, "AORTA") != 0)
      {
        double* r018 = new double[4]; r018[0] = 0.00; r018[1] = 0.08; r018[2] = 0.00; r018[3] = 1.00; //
        this->GetLookupTable()->SetTableValue(17, r018);
      }
      if (this->SetColorName(18, "PULMONARYARTERY") != 0)
      {
        double* r019 = new double[4]; r019[0] = 0.00; r019[1] = 0.09; r019[2] = 0.00; r019[3] = 1.00; //
        this->GetLookupTable()->SetTableValue(18, r019);
      }
      if (this->SetColorName(19, "PULMONARYVEIN") != 0)
      {
        double* r020 = new double[4]; r020[0] = 0.00; r020[1] = 0.00; r020[2] = 0.01; r020[3] = 1.00; //
        this->GetLookupTable()->SetTableValue(19, r020);
      }
      if (this->SetColorName(20, "UPPERTHIRD") != 0)
      {
        double* r021 = new double[4]; r021[0] = 0.00; r021[1] = 0.00; r021[2] = 0.02; r021[3] = 1.00; //
        this->GetLookupTable()->SetTableValue(20, r021);
      }
      if (this->SetColorName(21, "MIDDLETHIRD") != 0)
      {
        double* r022 = new double[4]; r022[0] = 0.00; r022[1] = 0.00; r022[2] = 0.03; r022[3] = 1.00; //
        this->GetLookupTable()->SetTableValue(21, r022);
      }
      if (this->SetColorName(22, "LOWERTHIRD") != 0)
      {
        double* r023 = new double[4]; r023[0] = 0.00; r023[1] = 0.00; r023[2] = 0.04; r023[3] = 1.00; //
        this->GetLookupTable()->SetTableValue(22, r023);
      }
      if (this->SetColorName(23, "LEFT") != 0)
      {
        double* r024 = new double[4]; r024[0] = 0.34; r024[1] = 0.33; r024[2] = 0.80; r024[3] = 1.00; //
        this->GetLookupTable()->SetTableValue(23, r024);
      }
      if (this->SetColorName(24, "RIGHT") != 0)
      {
        double* r025 = new double[4]; r025[0] = 0.74; r025[1] = 0.34; r025[2] = 0.14; r025[3] = 1.00; //
        this->GetLookupTable()->SetTableValue(24, r025);
      }
      if (this->SetColorName(25, "LIVER") != 0)
      {
        double* r026 = new double[4]; r026[0] = 0.66; r026[1] = 0.36; r026[2] = 0.40; r026[3] = 1.00; //
        this->GetLookupTable()->SetTableValue(25, r026);
      }
      if (this->SetColorName(26, "SPLEEN") != 0)
      {
        double* r027 = new double[4]; r027[0] = 1.00; r027[1] = 1.00; r027[2] = 0.01; r027[3] = 1.00; //
        this->GetLookupTable()->SetTableValue(26, r027);
      }
      if (this->SetColorName(27, "ABDOMEN") != 0)
      {
        double* r028 = new double[4]; r028[0] = 1.00; r028[1] = 0.50; r028[2] = 0.01; r028[3] = 1.00; //
        this->GetLookupTable()->SetTableValue(27, r028);
      }
      for( int i = 28; i < 256; i++ )
      {
      	if (this->SetColorName(i, "UNDEFINEDREGION") != 0)
      	{
 		double* r = new double[4]; r[0] = 0.00; r[1] = 0.00; r[2] = 0.00; r[3] = 1.00;
        	this->GetLookupTable()->SetTableValue(i, r);
	}
      }

	int typePlaces[8];
	std::vector<unsigned short> value;
	

	for( int typeValue = 1; typeValue<81; typeValue++ )
	{
		unsigned short binaryValue = 0; 
		int v = typeValue;
		for ( int i=0; i<8; i++ )
      		{
        		typePlaces[i] = 0;
      		}
		for ( int j=7; j>=0; j-- )
      		{
			int power = static_cast< int >( vcl_pow( static_cast< float >(2), static_cast< float >(j) ) );
			if ( power <= v )
        		{
          			typePlaces[j] = 1;
				v = v % power;
				//std::cout<<v<<std::endl;
			}
      		}
		for(int k = 8; k < 16; k++ )
      		{
			binaryValue += static_cast< unsigned short >( typePlaces[k-8] )*static_cast< unsigned short >( vcl_pow( static_cast< float >(2), static_cast< float >(k) ) );
      		}
		value.push_back(binaryValue);
        }      
      
      int index = 0;
      if (this->SetColorName(value.at(index), "NORMALPARENCHYMA") != 0)
      {
	double* t002 = new double[4]; t002[0] = 0.99; t002[1] = 0.99; t002[2] = 0.99; t002[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(value.at(index), t002);
	index++;
      }
      if (this->SetColorName(value.at(index), "AIRWAY") != 0)
      {
	double* t003 = new double[4]; t003[0] = 0.98; t003[1] = 0.98; t003[2] = 0.98; t003[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(value.at(index), t003);
	index++;
      }
      if (this->SetColorName(value.at(index), "VESSEL") != 0)
      {
	double* t004 = new double[4]; t004[0] = 0.97; t004[1] = 0.97; t004[2] = 0.97; t004[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(value.at(index), t004);
	index++;
      }
      if (this->SetColorName(value.at(index), "EMPHYSEMATOUS") != 0)
      {
	double* t005 = new double[4]; t005[0] = 0.96; t005[1] = 0.96; t005[2] = 0.96; t005[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(value.at(index), t005);
	index++;
      }
      if (this->SetColorName(value.at(index), "GROUNDGLASS") != 0)
      {
	double* t006 = new double[4]; t006[0] = 0.95; t006[1] = 0.95; t006[2] = 0.95; t006[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(value.at(index), t006);
	index++;
      }
      if (this->SetColorName(value.at(index), "RETICULAR") != 0)
      {
	double* t007 = new double[4]; t007[0] = 0.94; t007[1] = 0.94; t007[2] = 0.94; t007[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(value.at(index), t007);
	index++;
      }
      if (this->SetColorName(value.at(index), "NODULAR") != 0)
      {
	double* t008 = new double[4]; t008[0] = 0.93; t008[1] = 0.93; t008[2] = 0.93; t008[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(value.at(index), t008);
	index++;
      }
      if (this->SetColorName(value.at(index), "OBLIQUEFISSURE") != 0)
      {
	double* t009 = new double[4]; t009[0] = 0.92; t009[1] = 0.92; t009[2] = 0.92; t009[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(value.at(index), t009);
	index++;
      }
      if (this->SetColorName(value.at(index), "HORIZONTALFISSURE") != 0)
      {
	double* t010 = new double[4]; t010[0] = 0.91; t010[1] = 0.91; t010[2] = 0.91; t010[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(value.at(index), t010);
	index++;
      }
      if (this->SetColorName(value.at(index), "MILDPARASEPTALEMPHYSEMA") != 0)
      {
	double* t011 = new double[4]; t011[0] = 0.90; t011[1] = 0.90; t011[2] = 0.90; t011[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(value.at(index), t011);
	index++;
      }
      if (this->SetColorName(value.at(index), "MODERATEPARASEPTALEMPHYSEMA") != 0)
      {
	double* t012 = new double[4]; t012[0] = 0.89; t012[1] = 0.89; t012[2] = 0.89; t012[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(value.at(index), t012);
	index++;
      }
      if (this->SetColorName(value.at(index), "SEVEREPARASEPTALEMPHYSEMA") != 0)
      {
	double* t013 = new double[4]; t013[0] = 0.88; t013[1] = 0.88; t013[2] = 0.88; t013[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(value.at(index), t013);
	index++;
      }
      if (this->SetColorName(value.at(index), "MILDBULLA") != 0)
      {
	double* t014 = new double[4]; t014[0] = 0.87; t014[1] = 0.87; t014[2] = 0.87; t014[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(value.at(index), t014);
	index++;
      }
      if (this->SetColorName(value.at(index), "MODERATEBULLA") != 0)
      {
	double* t015 = new double[4]; t015[0] = 0.86; t015[1] = 0.86; t015[2] = 0.86; t015[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(value.at(index), t015);
	index++;
      }
      if (this->SetColorName(value.at(index), "SEVEREBULLA") != 0)
      {
	double* t016 = new double[4]; t016[0] = 0.85; t016[1] = 0.85; t016[2] = 0.85; t016[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(value.at(index), t016);
	index++;
      }
      if (this->SetColorName(value.at(index), "MILDCENTRILOBULAREMPHYSEMA") != 0)
      {
	double* t017 = new double[4]; t017[0] = 0.84; t017[1] = 0.84; t017[2] = 0.84; t017[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(value.at(index), t017);
	index++;
      }
      if (this->SetColorName(value.at(index), "MODERATECENTRILOBULAREMPHYSEMA") != 0)
      {
	double* t018 = new double[4]; t018[0] = 0.83; t018[1] = 0.83; t018[2] = 0.83; t018[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(value.at(index), t018);
	index++;
      }
      if (this->SetColorName(value.at(index), "SEVERECENTRILOBULAREMPHYSEMA") != 0)
      {
	double* t019 = new double[4]; t019[0] = 0.82; t019[1] = 0.82; t019[2] = 0.82; t019[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(value.at(index), t019);
	index++;
      }
      if (this->SetColorName(value.at(index), "MILDPANLOBULAREMPHYSEMA") != 0)
      {
	double* t020 = new double[4]; t020[0] = 0.81; t020[1] = 0.81; t020[2] = 0.81; t020[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(value.at(index), t020);
	index++;
      }
      if (this->SetColorName(value.at(index), "MODERATEPANLOBULAREMPHYSEMA") != 0)
      {
	double* t021 = new double[4]; t021[0] = 0.80; t021[1] = 0.70; t021[2] = 0.80; t021[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(value.at(index), t021);
	index++;
      }
      if (this->SetColorName(value.at(index), "SEVEREPANLOBULAREMPHYSEMA") != 0)
      {
	double* t022 = new double[4]; t022[0] = 0.79; t022[1] = 0.79; t022[2] = 0.79; t022[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(value.at(index), t022);
	index++;
      }
      if (this->SetColorName(value.at(index), "AIRWAYWALLTHICKENING") != 0)
      {
	double* t023 = new double[4]; t023[0] = 0.78; t023[1] = 0.78; t023[2] = 0.78; t023[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(value.at(index), t023);
	index++;
      }
      if (this->SetColorName(value.at(index), "AIRWAYCYLINDRICALDILATION") != 0)
      {
	double* t024 = new double[4]; t024[0] = 0.77; t024[1] = 0.77; t024[2] = 0.77; t024[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(value.at(index), t024);
	index++;
      }
      if (this->SetColorName(value.at(index), "VARICOSEBRONCHIECTASIS") != 0)
      {
	double* t025 = new double[4]; t025[0] = 0.76; t025[1] = 0.76; t025[2] = 0.76; t025[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(value.at(index), t025);
	index++;
      }
      if (this->SetColorName(value.at(index), "CYSTICBRONCHIECTASIS") != 0)
      {
	double* t026 = new double[4]; t026[0] = 0.75; t026[1] = 0.75; t026[2] = 0.75; t026[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(537, t026);
	value.at(index)++;
      }
      if (this->SetColorName(value.at(index), "CENTRILOBULARNODULE") != 0)
      {
	double* t027 = new double[4]; t027[0] = 0.74; t027[1] = 0.74; t027[2] = 0.74; t027[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(value.at(index), t027);
	index++;
      }
      if (this->SetColorName(value.at(index), "MOSAICING") != 0)
      {
	double* t028 = new double[4]; t028[0] = 0.73; t028[1] = 0.73; t028[2] = 0.73; t028[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(value.at(index), t028);
	index++;
      }
      if (this->SetColorName(value.at(index), "EXPIRATORYMALACIA") != 0)
      {
	double* t029 = new double[4]; t029[0] = 0.72; t029[1] = 0.72; t029[2] = 0.72; t029[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(value.at(index), t029);
	index++;
      }
      if (this->SetColorName(value.at(index), "SABERSHEATH") != 0)
      {
	double* t030 = new double[4]; t030[0] = 0.71; t030[1] = 0.71; t030[2] = 0.71; t030[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(value.at(index), t030);
	index++;
      }
      if (this->SetColorName(value.at(index), "OUTPOUCHING") != 0)
      {
	double* t031 = new double[4]; t031[0] = 0.70; t031[1] = 0.70; t031[2] = 0.70; t031[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(value.at(index), t031);
	index++;
      }
      if (this->SetColorName(value.at(index), "MUCOIDMATERIAL") != 0)
      {
	double* t032 = new double[4]; t032[0] = 0.69; t032[1] = 0.69; t032[2] = 0.69; t032[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(value.at(index), t032);
	index++;
      }
      if (this->SetColorName(value.at(index), "PATCHYGASTRAPPING") != 0)
      {
	double* t033 = new double[4]; t033[0] = 0.68; t033[1] = 0.68; t033[2] = 0.68; t033[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(value.at(index), t033);
	index++;
      }
      if (this->SetColorName(value.at(index), "DIFFUSEGASTRAPPING") != 0)
      {
	double* t034 = new double[4]; t034[0] = 0.67; t034[1] = 0.67; t034[2] = 0.67; t034[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(value.at(index), t034);
	index++;
      }
      if (this->SetColorName(value.at(index), "LINEARSCAR") != 0)
      {
	double* t035 = new double[4]; t035[0] = 0.66; t035[1] = 0.66; t035[2] = 0.66; t035[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(value.at(index), t035);
	index++;
      }
      if (this->SetColorName(value.at(index), "CYST") != 0)
      {
	double* t036 = new double[4]; t036[0] = 0.65; t036[1] = 0.65; t036[2] = 0.65; t036[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(value.at(index), t036);
	index++;
      }
      if (this->SetColorName(value.at(index), "ATELECTASIS") != 0)
      {
	double* t037 = new double[4]; t037[0] = 0.64; t037[1] = 0.64; t037[2] = 0.64; t037[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(value.at(index), t037);
	index++;
      }
      if (this->SetColorName(value.at(index), "HONEYCOMBING") != 0)
      {
	double* t038 = new double[4]; t038[0] = 0.63; t038[1] = 0.63; t038[2] = 0.63; t038[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(value.at(index), t038);
	index++;
      }
      if (this->SetColorName(value.at(index), "TRACHEA") != 0)
      {
	double* t039 = new double[4]; t039[0] = 0.51; t039[1] = 0.50; t039[2] = 0.50; t039[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(value.at(index), t039);
	index++;
      } 
      if (this->SetColorName(value.at(index), "MAINBRONCHUS") != 0)
      {
	double* t040 = new double[4]; t040[0] = 0.55; t040[1] = 0.27; t040[2] = 0.07; t040[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(value.at(index), t040);
	index++;
      } 
      if (this->SetColorName(value.at(index), "UPPERLOBEBRONCHUS") != 0)
      {
	double* t041 = new double[4]; t041[0] = 1.00; t041[1] = 0.65; t041[2] = 0.00; t041[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(value.at(index), t041);
	index++;
      } 
      if (this->SetColorName(value.at(index), "AIRWAYGENERATION3") != 0)
      {
	double* t042 = new double[4]; t042[0] = 1.00; t042[1] = 1.00; t042[2] = 0.01; t042[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(value.at(index), t042);
	index++;
      }   
      if (this->SetColorName(value.at(index), "AIRWAYGENERATION4") != 0)
      {
	double* t043 = new double[4]; t043[0] = 1.00; t043[1] = 0.01; t043[2] = 1.00; t043[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(value.at(index), t043);
	index++;
      }  
      if (this->SetColorName(value.at(index), "AIRWAYGENERATION5") != 0)
      {
	double* t044 = new double[4]; t044[0] = 0.51; t044[1] = 1.00; t044[2] = 0.00; t044[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(value.at(index), t044);
	index++;
      }  
      if (this->SetColorName(value.at(index), "AIRWAYGENERATION6") != 0)
      {
	double* t045 = new double[4]; t045[0] = 0.01; t045[1] = 0.50; t045[2] = 1.00; t045[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(value.at(index), t045);
	index++;
      }  
      if (this->SetColorName(value.at(index), "AIRWAYGENERATION7") != 0)
      {
	double* t046 = new double[4]; t046[0] = 0.51; t046[1] = 0.00; t046[2] = 0.50; t046[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(value.at(index), t046);
	index++;
      }  
      if (this->SetColorName(value.at(index), "AIRWAYGENERATION8") != 0)
      {
	double* t047 = new double[4]; t047[0] = 0.51; t047[1] = 0.50; t047[2] = 0.00; t047[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(value.at(index), t047);
	index++;
      }  
      if (this->SetColorName(value.at(index), "AIRWAYGENERATION9") != 0)
      {
	double* t048 = new double[4]; t048[0] = 0.01; t048[1] = 0.50; t048[2] = 0.50; t048[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(value.at(index), t048);
	index++;
      }  
      if (this->SetColorName(value.at(index), "AIRWAYGENERATION10") != 0)
      {
	double* t049 = new double[4]; t049[0] = 0.45; t049[1] = 0.44; t049[2] = 0.44; t049[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(value.at(index), t049);
	index++;
      }  
      if (this->SetColorName(value.at(index), "CALCIFICATION") != 0)
      {
	double* t050 = new double[4]; t050[0] = 0.51; t050[1] = 0.51; t050[2] = 0.51; t050[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(value.at(index), t050);
	index++;
      }
      if (this->SetColorName(value.at(index), "ARTERY") != 0)
      {
	double* t051 = new double[4]; t051[0] = 0.40; t051[1] = 0.50; t051[2] = 0.50; t051[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(value.at(index), t051);
	index++;
      }
      if (this->SetColorName(value.at(index), "VEIN") != 0)
      {
	double* t052 = new double[4]; t052[0] = 0.49; t052[1] = 0.49; t052[2] = 0.49; t052[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(value.at(index), t052);
	index++;
      }
      if (this->SetColorName(value.at(index), "PECTORALISMINOR") != 0)
      {
	double* t053 = new double[4]; t053[0] = 0.48; t053[1] = 0.48; t053[2] = 0.48; t053[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(value.at(index), t053);
	index++;
      }  
      if (this->SetColorName(value.at(index), "PECTORALISMAJOR") != 0)
      {
	double* t054 = new double[4]; t054[0] = 0.47; t054[1] = 0.47; t054[2] = 0.47; t054[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(value.at(index), t054);
	index++;
      }  
      if (this->SetColorName(value.at(index), "ANTERIORSCALENE") != 0)
      {
	double* t055 = new double[4]; t055[0] = 0.46; t055[1] = 0.46; t055[2] = 0.46; t055[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(value.at(index), t055);
	index++;
      }  
      if (this->SetColorName(value.at(index), "FISSURE") != 0)
      {
	double* t056 = new double[4]; t056[0] = 0.45; t056[1] = 0.45; t056[2] = 0.45; t056[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(value.at(index), t056);
	index++;
      }  
      if (this->SetColorName(value.at(index), "VESSELGENERATION0") != 0)
      {
	double* t057 = new double[4]; t057[0] = 0.00; t057[1] = 0.00; t057[2] = 0.00; t057[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(value.at(index), t057);
	index++;
      } 
      if (this->SetColorName(value.at(index), "VESSELGENERATION1") != 0)
      {
	double* t058 = new double[4]; t058[0] = 0.00; t058[1] = 1.00; t058[2] = 0.00; t058[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(value.at(index), t058);
	index++;
      } 
      if (this->SetColorName(value.at(index), "VESSELGENERATION2") != 0)
      {
	double* t059 = new double[4]; t059[0] = 0.00; t059[1] = 1.00; t059[2] = 1.00; t059[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(value.at(index), t059);
	index++;
      } 
      if (this->SetColorName(value.at(index), "VESSELGENERATION3") != 0)
      {
	double* t060 = new double[4]; t060[0] = 1.00; t060[1] = 1.00; t060[2] = 0.00; t060[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(value.at(index), t060);
	index++;
      } 
      if (this->SetColorName(value.at(index), "VESSELGENERATION4") != 0)
      {
	double* t061 = new double[4]; t061[0] = 1.00; t061[1] = 0.00; t061[2] = 1.00; t061[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(value.at(index), t061);
	index++;
      } 
      if (this->SetColorName(value.at(index), "VESSELGENERATION5") != 0)
      {
	double* t062 = new double[4]; t062[0] = 0.50; t062[1] = 1.00; t062[2] = 0.00; t062[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(value.at(index), t062);
	index++;
      }
      if (this->SetColorName(value.at(index), "VESSELGENERATION6") != 0)
      {
	double* t063 = new double[4]; t063[0] = 0.00; t063[1] = 0.50; t063[2] = 1.00; t063[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(value.at(index), t063);
	index++;
      }
      if (this->SetColorName(value.at(index), "VESSELGENERATION7") != 0)
      {
	double* t064 = new double[4]; t064[0] = 0.50; t064[1] = 0.00; t064[2] = 0.50; t064[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(value.at(index), t064);
	index++;
      }
      if (this->SetColorName(value.at(index), "VESSELGENERATION8") != 0)
      {
	double* t065 = new double[4]; t065[0] = 0.50; t065[1] = 0.50; t065[2] = 0.00; t065[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(value.at(index), t065);
	index++;
      }
      if (this->SetColorName(value.at(index), "VESSELGENERATION9") != 0)
      {
	double* t066 = new double[4]; t066[0] = 0.00; t066[1] = 0.50; t066[2] = 0.50; t066[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(value.at(index), t066);
	index++;
      }
      if (this->SetColorName(value.at(index), "VESSELGENERATION10") != 0)
      {
	double* t067 = new double[4]; t067[0] = 0.44; t067[1] = 0.44; t067[2] = 0.44; t067[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(value.at(index), t067);
	index++;
      }
      if (this->SetColorName(value.at(index), "PARASEPTALEMPHYSEMA") != 0)
      {
	double* t068 = new double[4]; t068[0] = 0.00; t068[1] = 0.68; t068[2] = 0.00; t068[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(value.at(index), t068);
	index++;
      }
      if (this->SetColorName(value.at(index), "CENTRILOBULAREMPHYSEMA") != 0)
      {
	double* t069 = new double[4]; t069[0] = 0.00; t069[1] = 0.69; t069[2] = 0.69; t069[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(value.at(index), t069);
	index++;
      }
      if (this->SetColorName(value.at(index), "PANLOBULAREMPHYSEMA") != 0)
      {
	double* t070 = new double[4]; t070[0] = 0.00; t070[1] = 0.00; t070[2] = 0.70; t070[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(value.at(index), t070);
	index++;
      }
      if (this->SetColorName(value.at(index), "SUBCUTANEOUSFAT") != 0)
      {
	double* t071 = new double[4]; t071[0] = 0.59; t071[1] = 0.65; t071[2] = 0.20; t071[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(value.at(index), t071);
	index++;
      }
      if (this->SetColorName(value.at(index), "VISCERALFAT") != 0)
      {
	double* t072 = new double[4]; t072[0] = 0.58; t072[1] = 0.65; t072[2] = 0.20; t072[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(value.at(index), t072);
	index++;
      }
      if (this->SetColorName(value.at(index), "INTERMEDIATEBRONCHUS") != 0)
      {
	double* t073 = new double[4]; t073[0] = 0.85; t073[1] = 0.75; t073[2] = 0.85; t073[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(value.at(index), t073);
	index++;
      }
      if (this->SetColorName(value.at(index), "LOWERLOBEBRONCHUS") != 0)
      {
	double* t074 = new double[4]; t074[0] = 1.00; t074[1] = 0.02; t074[2] = 0.00; t074[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(value.at(index), t074);
	index++;
      }
      if (this->SetColorName(value.at(index), "SUPERIORDIVISIONBRONCHUS") != 0)
      {
	double* t075 = new double[4]; t075[0] = 0.98; t075[1] = 0.50; t075[2] = 0.45; t075[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(value.at(index), t075);
	index++;
      }
      if (this->SetColorName(value.at(index), "LINGULARBRONCHUS") != 0)
      {
	double* t076 = new double[4]; t076[0] = 0.00; t076[1] = 0.03; t076[2] = 1.00; t076[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(value.at(index), t076);
	index++;
      }
      if (this->SetColorName(value.at(index), "MIDDLELOBEBRONCHUS") != 0)
      {
	double* t077 = new double[4]; t077[0] = 0.25; t077[1] = 0.88; t077[2] = 0.82; t077[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(value.at(index), t077);
	index++;
      }
      if (this->SetColorName(value.at(index), "BRONCHIECTATICAIRWAY") != 0)
      {
	double* t078 = new double[4]; t078[0] = 0.25; t078[1] = 0.88; t078[2] = 0.81; t078[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(value.at(index), t078);
	index++;
      }
      if (this->SetColorName(value.at(index), "NONBRONCHIECTATICAIRWAY") != 0)
      {
	double* t079 = new double[4]; t079[0] = 0.25; t079[1] = 0.87; t079[2] = 0.81; t079[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(value.at(index), t079);
	index++;
      }
      if (this->SetColorName(value.at(index), "NONBRONCHIECTATICAIRWAY") != 0)
      {
	double* t080 = new double[4]; t080[0] = 0.25; t080[1] = 0.86; t080[2] = 0.81; t080[3] = 1.00; 
        this->GetLookupTable()->SetTableValue(value.at(index), t080);
	index++;
      }

     /*for( int i = 208; i < 256; i++ )
      {
      	if (this->SetColorName(i, "UNDEFINEDTYPE") != 0)
      	{
 		double* t = new double[4]; t[0] = 1.00; t[1] = 1.00; t[2] = 1.00; t[3] = 0.00;
        	this->GetLookupTable()->SetTableValue(i, t);
	}
      }*/
 
      this->NamesInitialisedOn();
      this->SetDescription("A legacy colour table that contains some anatomical mapping for a Chest LabelMap");
    }
    else
    {
      vtkErrorMacro("vtkMRMLChestRTColorTableNode: SetType ERROR, unknown type " << type << endl);
      return;
    }
    // invoke a modified event
    this->Modified();

    // invoke a type  modified event
    this->InvokeEvent(vtkMRMLChestRTColorTableNode::TypeModifiedEvent);
}

//---------------------------------------------------------------------------
int vtkMRMLChestRTColorTableNode::GetNumberOfRegions()
{
  if (this->GetLookupTable() != NULL)
  {
    return 256;
  }
  else
  {
    return 0;
  }
}

//---------------------------------------------------------------------------
int vtkMRMLChestRTColorTableNode::GetNumberOfTypes()
{
  if (this->GetLookupTable() != NULL)
  {
    return 80;
  }
  else
  {
    return 0;
  }
}

//---------------------------------------------------------------------------
/*void vtkMRMLChestRTColorTableNode::AddColor(const char *name, double r, double g, double b, double a)
{
 if (this->GetType() != this->User &&
     this->GetType() != this->File)
    {
      vtkErrorMacro("vtkMRMLChestRTColorTableNode::AddColor: ERROR: can't add a colour if not a user defined colour table, reset the type first to User or File\n");
      return;
    }
 this->LastAddedColor++;
 this->SetColor(this->LastAddedColor, name, r, g, b, a);
}*/

//---------------------------------------------------------------------------
/*int vtkMRMLChestRTColorTableNode::SetColor(int entry, const char *name, double r, double g, double b, double a)
{
  if (this->GetType() != this->User &&
      this->GetType() != this->File)
    {
      vtkErrorMacro( "vtkMRMLChestRTColorTableNode::SetColor: ERROR: can't set a colour if not a user defined colour table, reset the type first to User or File\n");
      return 0;
    }
  if (entry < 0 ||
      entry >= this->GetLookupTable()->GetNumberOfTableValues())
    {
    vtkErrorMacro( "vtkMRMLChestRTColorTableNode::SetColor: requested entry " << entry << " is out of table range: 0 - " << this->GetLookupTable()->GetNumberOfTableValues() << ", call SetNumberOfColors" << endl);
      return 0;
    }

  this->GetLookupTable()->SetTableValue(entry, r, g, b, a);
  if (!this->GetNamesInitialised())
    {
    this->SetNamesFromColors();
    }
  if (this->SetColorName(entry, name) == 0)
    {
    vtkWarningMacro("SetColor: error setting color name " << name << " for entry " << entry);
    return 0;
    }

  // trigger a modified event
  this->Modified();
  return 1;
}

//---------------------------------------------------------------------------
int vtkMRMLChestRTColorTableNode::SetColor(int entry, double r, double g, double b, double a)
{
  if (this->GetType() != this->User &&
      this->GetType() != this->File)
    {
      vtkErrorMacro( "vtkMRMLChestRTColorTableNode::SetColor: ERROR: can't set a colour if not a user defined colour table, reset the type first to User or File\n");
      return 0;
    }
  if (entry < 0 ||
      entry >= this->GetLookupTable()->GetNumberOfTableValues())
    {
    vtkErrorMacro( "vtkMRMLChestRTColorTableNode::SetColor: requested entry " << entry << " is out of table range: 0 - " << this->GetLookupTable()->GetNumberOfTableValues() << ", call SetNumberOfColors" << endl);
      return 0;
    }
  double* rgba = this->GetLookupTable()->GetTableValue(entry);
  if (rgba[0] == r && rgba[1] == g && rgba[2] == b && rgba[3] == a)
    {
    return 1;
    }
  this->GetLookupTable()->SetTableValue(entry, r, g, b, a);
  if (this->HasNameFromColor(entry))
    {
    this->SetNameFromColor(entry);
    }

  // trigger a modified event
  this->Modified();
  return 1;
}

//---------------------------------------------------------------------------
int vtkMRMLChestRTColorTableNode::SetColor(int entry, double r, double g, double b)
{
  if (entry < 0 ||
      entry >= this->GetLookupTable()->GetNumberOfTableValues())
    {
    vtkErrorMacro( "vtkMRMLChestRTColorTableNode::SetColor: requested entry " << entry << " is out of table range: 0 - " << this->GetLookupTable()->GetNumberOfTableValues() << ", call SetNumberOfColors" << endl);
      return 0;
    }
  double* rgba = this->GetLookupTable()->GetTableValue(entry);
  return this->SetColor(entry, r,g,b,rgba[3]);
}*/

//---------------------------------------------------------------------------
bool vtkMRMLChestRTColorTableNode::GetColor(int entry, double* color)
{
  if (entry < 0 || entry >= this->GetNumberOfColors())
  {
    vtkErrorMacro("vtkMRMLChestRTColorTableNode::SetColor: requested entry " << entry << " is out of table range: 0 - " << this->GetLookupTable()->GetNumberOfTableValues() << ", call SetNumberOfColors" << endl);
    return false;
  }
  this->GetLookupTable()->GetTableValue(entry, color);
  return true;
}

//---------------------------------------------------------------------------
void vtkMRMLChestRTColorTableNode::ClearNames()
{
  this->Names.clear();
  this->NamesInitialisedOff();
}

//---------------------------------------------------------------------------
void vtkMRMLChestRTColorTableNode::Reset()
{
  int disabledModify = this->StartModify();

  // only call reset if this is a user node
  if (this->GetType() == vtkMRMLChestRTColorTableNode::ChestRTLabels)
  {
    int type = this->GetType();
    Superclass::Reset();
    this->SetType(type);
  }

  this->EndModify(disabledModify);
}

//---------------------------------------------------------------------------
int vtkMRMLChestRTColorTableNode::GetColorIndexByName(const char *name)
{
  if (this->GetNamesInitialised() && name != NULL)
  {
    std::string strName = name;
    for (unsigned int i = 0; i < this->Names.size(); i++)
    {
      if (strName.compare(this->GetColorName(i)) == 0)
      {
        return i;
      }
    }
  }
  return -1;
}

//---------------------------------------------------------------------------
vtkMRMLStorageNode* vtkMRMLChestRTColorTableNode::CreateDefaultStorageNode()
{
  return vtkMRMLColorTableStorageNode::New();
};
