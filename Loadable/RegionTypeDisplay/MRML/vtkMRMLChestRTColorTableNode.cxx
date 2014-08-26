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

#include <cipChestConventions.h>

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
    int size = 256;

    this->GetLookupTable()->SetNumberOfTableValues(size);
    this->GetLookupTable()->SetTableRange(0,size);
    this->Names.clear();
    this->Names.resize(this->GetLookupTable()->GetNumberOfTableValues());

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
