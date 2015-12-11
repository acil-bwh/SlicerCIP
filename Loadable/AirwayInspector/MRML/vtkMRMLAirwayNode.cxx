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
#include <vtkEllipseFitting.h>

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
  CenterXYZ[0] = 0;
  CenterXYZ[1] = 0;
  CenterXYZ[2] = 0;
  XAxis[0] = 0;
  XAxis[1] = 0;
  XAxis[2] = 0;
  Threshold = -850;
  VolumeNodeID = 0;

  this->Ellipse = vtkDoubleArray::New();

  this->EllipseInside = vtkEllipseFitting::New();
  this->EllipseOutside = vtkEllipseFitting::New();

  AirwayImage = 0;
  InnerContour = 0;
  OuterContour = 0;

  this->Method = 1;
  this->AxisMode = HESSIAN;
  this->Reformat = 0;
  this->Threshold = -850;
  this->ComputeCenter = 1;
  this->RefineCenter = 1;

  this->AirBaselineIntensity = -1024;

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
  std::map<int, vtkDoubleArray*>::iterator it;
  for (it=this->Mean.begin(); it != this->Mean.end(); it++)
    {
    it->second->Delete();
    }
  for (it=this->Std.begin(); it != this->Std.end(); it++)
    {
    it->second->Delete();
    }
  for (it=this->Min.begin(); it != this->Min.end(); it++)
    {
    it->second->Delete();
    }
  for (it=this->Max.begin(); it != this->Max.end(); it++)
    {
    it->second->Delete();
    }

  this->Ellipse->Delete();
  this->EllipseInside->Delete();
  this->EllipseOutside->Delete();
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
  of << indent << " centerxyz=\"" << this->CenterXYZ[0] << " "
                            << this->CenterXYZ[1] << " "
                            << this->CenterXYZ[2] << "\"";
  of << indent << " xaxis=\"" << this->XAxis[0] << " "
                            << this->XAxis[1] << " "
                            << this->XAxis[2] << "\"";

  of << indent << " yaxis=\"" << this->YAxis[0] << " "
                            << this->YAxis[1] << " "
                            << this->ZAxis[2] << "\"";

  of << indent << " zaxis=\"" << this->ZAxis[0] << " "
                            << this->ZAxis[1] << " "
                            << this->ZAxis[2] << "\"";

  of << indent << " method=\"" << this->Method << "\"";
  of << indent << " axisMode=\"" << this->AxisMode << "\"";
  of << indent << " reformat=\"" << this->Reformat << "\"";
  of << indent << " computeCenter=\"" << this->ComputeCenter << "\"";
  of << indent << " refineCenter=\"" << this->RefineCenter << "\"";
  of << indent << " airBaselineIntensity=\"" << this->AirBaselineIntensity << "\"";
  of << indent << " segmentPercentage=\"" << this->SegmentPercentage << "\"";
  of << indent << " resolution=\"" << this->Resolution << "\"";
  of << indent << " reconstruction=\"" << this->Reconstruction << "\"";
  if (this->AirwayImagePrefix)
    {
    of << indent << " airwayImagePrefix=\"" << this->AirwayImagePrefix << "\"";
    }
  of << indent << " saveAirwayImage=\"" << this->SaveAirwayImage << "\"";
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
    if (!strcmp(attName, "centerxyz"))
      {
      std::stringstream ss;
      ss << attValue;
      ss >> CenterXYZ[0];
      ss >> CenterXYZ[1];
      ss >> CenterXYZ[2];
      }
    else if (!strcmp(attName, "xaxis"))
      {
      std::stringstream ss;
      ss << attValue;
      ss >> XAxis[0];
      ss >> XAxis[1];
      ss >> XAxis[2];
      }
    else if (!strcmp(attName, "yaxis"))
      {
      std::stringstream ss;
      ss << attValue;
      ss >> YAxis[0];
      ss >> YAxis[1];
      ss >> YAxis[2];
      }
    else if (!strcmp(attName, "zaxis"))
      {
      std::stringstream ss;
      ss << attValue;
      ss >> ZAxis[0];
      ss >> ZAxis[1];
      ss >> ZAxis[2];
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
    else if (!strcmp(attName, "method"))
      {
      std::stringstream ss;
      ss << attValue;
      ss >> Method;
      }
    else if (!strcmp(attName, "axisMode"))
      {
      std::stringstream ss;
      ss << attValue;
      ss >> AxisMode;
      }
    else if (!strcmp(attName, "reformat"))
      {
      std::stringstream ss;
      ss << attValue;
      ss >> Reformat;
      }
    else if (!strcmp(attName, "computeCenter"))
      {
      std::stringstream ss;
      ss << attValue;
      ss >> ComputeCenter;
      }
    else if (!strcmp(attName, "refineCenter"))
      {
      std::stringstream ss;
      ss << attValue;
      ss >> RefineCenter;
      }
    else if (!strcmp(attName, "airBaselineIntensity"))
      {
      std::stringstream ss;
      ss << attValue;
      ss >> AirBaselineIntensity;
      }
    else if (!strcmp(attName, "segmentPercentage"))
      {
      std::stringstream ss;
      ss << attValue;
      ss >> SegmentPercentage;
      }
    else if (!strcmp(attName, "resolution"))
      {
      std::stringstream ss;
      ss << attValue;
      ss >> Resolution;
      }
    else if (!strcmp(attName, "reconstruction"))
      {
      std::stringstream ss;
      ss << attValue;
      ss >> Reconstruction;
      }
    else if (!strcmp(attName, "airwayImagePrefix"))
      {
      std::stringstream ss;
      ss << attValue;
      ss >> AirwayImagePrefix;
      }
    else if (!strcmp(attName, "saveAirwayImage"))
      {
      std::stringstream ss;
      ss << attValue;
      ss >> SaveAirwayImage ;
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
  this->SetCenterXYZ(node->GetCenterXYZ());
  this->SetXAxis(node->GetXAxis());
  this->SetYAxis(node->GetYAxis());
  this->SetZAxis(node->GetZAxis());
  this->SetThreshold(node->GetThreshold());
  this->SetMethod(node->GetMethod());
  this->SetAxisMode(node->GetAxisMode());
  this->SetReformat(node->GetReformat());
  this->SetComputeCenter(node->GetComputeCenter());
  this->SetRefineCenter(node->GetRefineCenter());
  this->SetAirBaselineIntensity(node->GetAirBaselineIntensity());
  this->SetSegmentPercentage(node->GetSegmentPercentage());
  this->SetResolution(node->GetResolution());
  this->SetReconstruction(node->GetReconstruction());
  this->SetAirwayImagePrefix(node->GetAirwayImagePrefix());
  this->SetSaveAirwayImage(node->GetSaveAirwayImage());
}

//----------------------------------------------------------------------------
void vtkMRMLAirwayNode::PrintSelf(ostream& os, vtkIndent indent)
{
  Superclass::PrintSelf(os,indent);

  os << indent << "VolumeNodeID: " << this->VolumeNodeID << "\n";
  os << indent << "XYZ: " << this->XYZ << "\n";
  os << indent << "CenterXYZ: " << this->CenterXYZ << "\n";
  os << indent << "XAxis: " << this->XAxis << "\n";
  os << indent << "YAxis: " << this->YAxis << "\n";
  os << indent << "ZAxis: " << this->ZAxis << "\n";
  os << indent << "Threshold: " << this->Threshold << "\n";
  os << indent << "Method: " << this->Method << "\n";
  os << indent << "AxisMode: " << this->AxisMode << "\n";
  os << indent << "Reformat: " << this->Reformat << "\n";
  os << indent << "ComputeCenter: " << this->ComputeCenter << "\n";
  os << indent << "RefineCenter: " << this->RefineCenter << "\n";
  os << indent << "AirBaselineIntensity: " << this->AirBaselineIntensity << "\n";
  os << indent << "SegmentPercentage: " << this->SegmentPercentage << "\n";
  os << indent << "Resolution: " << this->Resolution << "\n";
  os << indent << "Reconstruction: " << this->Reconstruction << "\n";
  os << indent << "AirwayImagePrefix: " << this->AirwayImagePrefix << "\n";
  os << indent << "SaveAirwayImage: " << this->SaveAirwayImage << "\n";
  //os << indent << "Min: " << this->Min << "\n";
  //os << indent << "Max: " << this->Max << "\n";
  //os << indent << "Mean: " << this->Mean << "\n";
  //os << indent << "Std: " << this->Std << "\n";
}

vtkDoubleArray*
vtkMRMLAirwayNode::GetMean(int methodName)
{
  std::map<int, vtkDoubleArray*>::iterator it =
    this->Mean.find(methodName);
  return (it == this->Mean.end()) ? 0 : it->second;
}
vtkDoubleArray*
vtkMRMLAirwayNode::GetStd(int methodName)
{
  std::map<int, vtkDoubleArray*>::iterator it =
    this->Std.find(methodName);
  return (it == this->Std.end()) ? 0 : it->second;
}
vtkDoubleArray*
vtkMRMLAirwayNode::GetMin(int methodName)
{
  std::map<int, vtkDoubleArray*>::iterator it =
    this->Min.find(methodName);
  return (it == this->Min.end()) ? 0 : it->second;
}
vtkDoubleArray*
vtkMRMLAirwayNode::GetMax(int methodName)
{
  std::map<int, vtkDoubleArray*>::iterator it =
    this->Max.find(methodName);
  return (it == this->Max.end()) ? 0 : it->second;
}

void vtkMRMLAirwayNode::SetMean(int methodName, vtkDoubleArray* values)
{
  this->Mean[methodName] = values;
}

void vtkMRMLAirwayNode::SetStd(int methodName, vtkDoubleArray* values)
{
  this->Std[methodName] = values;
}

void vtkMRMLAirwayNode::SetMin(int methodName, vtkDoubleArray* values)
{
  this->Min[methodName] = values;
}
void vtkMRMLAirwayNode::SetMax(int methodName, vtkDoubleArray* values)
{
  this->Max[methodName] = values;
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
