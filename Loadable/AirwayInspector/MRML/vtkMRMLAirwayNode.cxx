/*==============================================================================

  Program: 3D Slicer

  Portions (c) Copyright Brigham and Women's Hospital (BWH) All Rights Reserved.

  See COPYRIGHT.txt
  or http://www.slicer.org/copyright/copyright.txt for details.

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.

==============================================================================*/

// MRML includes
#include "vtkMRMLAirwayNode.h"

// Slicer MRML includes
#include "vtkMRMLScene.h"
#include "vtkMRMLScalarVolumeNode.h"

// VTK includes
//#include <vtkNew.h>
#include <vtkObjectFactory.h>
#include <vtkSmartPointer.h>
#include <vtkPointData.h>
#include <vtkPolyData.h>
#include <vtkDoubleArray.h>

// STD includes
#include <sstream>
#include <algorithm>

//----------------------------------------------------------------------------
//vtkCxxSetReferenceStringMacro(vtkMRMLAirwayNode, VolumeNodeID);

vtkMRMLNodeNewMacro(vtkMRMLAirwayNode);

//----------------------------------------------------------------------------
vtkMRMLAirwayNode::vtkMRMLAirwayNode()
{
  XYZ[0] = 0;
  XYZ[1] = 0;
  XYZ[2] = 0;
  OrientationWXYZ[0];
  OrientationWXYZ[1];
  OrientationWXYZ[2];
  OrientationWXYZ[3];
  Threshold = 0;
  VolumeNodeID = 0;

  this->Mean = vtkDoubleArray::New();
  this->Std = vtkDoubleArray::New();
  this->Min = vtkDoubleArray::New();
  this->Max = vtkDoubleArray::New();
  this->Ellipse = vtkDoubleArray::New();

  AirwayImage = 0;
  InnerContour = 0;
  OuterContour = 0;

  this->SetMethodToPhaseCongruency();
  this->AxisMode = HESSIAN;
  this->Reformat = 0;

  this->SegmentPercentage = 0.5;
  this->Resolution = 0.1;

  this->Reconstruction = SMOOTH;

  this->AirwayImagePrefix= NULL;
  this->SaveAirwayImage=0;
}

//----------------------------------------------------------------------------
vtkMRMLAirwayNode::~vtkMRMLAirwayNode()
{
  if (this->VolumeNodeID)
    {
    delete [] this->VolumeNodeID;
    this->VolumeNodeID = NULL;
    }
  this->Mean->Delete();
  this->Std->Delete();
  this->Min->Delete();
  this->Max->Delete();
  this->Ellipse->Delete();
}

//----------------------------------------------------------------------------
void vtkMRMLAirwayNode::WriteXML(ostream& of, int nIndent)
{
  Superclass::WriteXML(of,nIndent);

  vtkIndent indent(nIndent);

  of << indent << " volumeNodeID=\"" << this->VolumeNodeID << "\"";
  of << indent << " threshold=\"" << this->Threshold << "\"";
  of << indent << " xyz=\"" << this->XYZ[0] << " "
                            << this->XYZ[1] << " "
                            << this->XYZ[2] << "\"";
  of << indent << " orientation=\"" << this->OrientationWXYZ[0] << " "
                            << this->OrientationWXYZ[1] << " "
                            << this->OrientationWXYZ[2] << " "
                            << this->OrientationWXYZ[3] << "\"";

  of << indent << " min=\"" << this->Min << "\"";
  of << indent << " max=\"" << this->Max << "\"";
  of << indent << " mean=\"" << this->Mean << "\"";
  of << indent << " mstd=\"" << this->Std << "\"";
}

//----------------------------------------------------------------------------
void vtkMRMLAirwayNode::ReadXMLAttributes(const char** atts)
{
  int disabledModify = this->StartModify();

  Superclass::ReadXMLAttributes(atts);
  const char* attName;
  const char* attValue;

  while (*atts != NULL)
    {
    attName = *(atts++);
    attValue = *(atts++);

    if (!strcmp(attName, "xyz"))
      {
      std::stringstream ss;
      ss << attValue;
      ss >> XYZ[0];
      ss >> XYZ[1];
      ss >> XYZ[2];
      }
    else if (!strcmp(attName, "orientation"))
      {
      std::stringstream ss;
      ss << attValue;
      ss >> OrientationWXYZ[0];
      ss >> OrientationWXYZ[1];
      ss >> OrientationWXYZ[2];
      ss >> OrientationWXYZ[3];
      }
    else if (!strcmp(attName, "threshold"))
      {
      std::stringstream ss;
      ss << attValue;
      ss >> Threshold;
      }
    else if (!strcmp(attName, "min"))
      {
      std::stringstream ss;
      ss << attValue;
      //ss >> Min;
      }
    else if (!strcmp(attName, "max"))
      {
      std::stringstream ss;
      ss << attValue;
      //ss >> Max;
      }
    else if (!strcmp(attName, "mean"))
      {
      std::stringstream ss;
      ss << attValue;
      //ss >> Mean;
      }
    else if (!strcmp(attName, "std"))
      {
      std::stringstream ss;
      ss << attValue;
      //ss >> Std;
      }
    else if (!strcmp(attName, "volumeNodeID"))
      {
      this->SetVolumeNodeID(attValue);
      }
    }
  this->EndModify(disabledModify);
}

//----------------------------------------------------------------------------
void vtkMRMLAirwayNode::Copy(vtkMRMLNode *anode)
{
  Superclass::Copy(anode);

  vtkMRMLAirwayNode *node = (vtkMRMLAirwayNode *) anode;
  if (!node)
    {
    return;
    }

  this->SetVolumeNodeID(node->GetVolumeNodeID());
  this->SetXYZ(node->GetXYZ());
  this->SetOrientationWXYZ(node->GetOrientationWXYZ());
  this->SetThreshold(node->GetThreshold());
  //this->SetMin(node->GetMin());
  //this->SetMax(node->GetMax());
  //this->SetMean(node->GetMean());
  //this->SetStd(node->GetStd());
}

//----------------------------------------------------------------------------
void vtkMRMLAirwayNode::PrintSelf(ostream& os, vtkIndent indent)
{
  Superclass::PrintSelf(os,indent);

  os << indent << "VolumeNodeID: " << this->VolumeNodeID << "\n";
  os << indent << "XYZ: " << this->XYZ << "\n";
  os << indent << "OrientationWXYZ: " << this->OrientationWXYZ << "\n";
  os << indent << "Threshold: " << this->Threshold << "\n";
  os << indent << "Min: " << this->Min << "\n";
  os << indent << "Max: " << this->Max << "\n";
  os << indent << "Mean: " << this->Mean << "\n";
  os << indent << "Std: " << this->Std << "\n";
}

//---------------------------------------------------------------------------
void vtkMRMLAirwayNode::
WriteCLI(std::vector<std::string>& commandLine, std::string prefix,
         int coordinateSystem, int multipleFlag)
{
/**
  // check if the coordinate system flag is set to LPS, otherwise assume RAS
  bool useLPS = false;
  if (coordinateSystem == 1)
    {
    useLPS = true;
    }

    if (prefix.compare("") != 0)
      {
      commandLine.push_back(prefix);
      }
      // avoid scientific notation
      //ss.precision(5);
      //ss << std::fixed << point[0] << "," <<  point[1] << "," <<  point[2] ;
      ss << XYZ[0] << "," <<  XYZ[1] << "," <<  XYZ[2];
      commandLine.push_back(ss.str());
      }
    if (multipleFlag == 0)
      {
      // only print out one markup, but print out all the points in that markup
      // (if have a ruler, need to do 2 points)
      break;
      }
    }
  **/
}
