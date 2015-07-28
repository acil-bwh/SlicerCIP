// Annotation includes
#include "vtkSlicerAirwayInspectorModuleLogic.h"

// MRML includes
#include <vtkMRMLScene.h>
#include <vtkMRMLAirwayNode.h>
#include <vtkMRMLSliceNode.h>
#include <vtkMRMLScalarVolumeNode.h>

// Logic includes
#include <vtkSlicerFiducialsLogic.h>

// VTK includes
#include <vtkImageData.h>
#include <vtkObjectFactory.h>
#include <vtkPNGWriter.h>
#include <vtkVersion.h>
#include <vtkImageEllipsoidSource.h>
#include <vtkImageCast.h>
#include <vtkImageMapToColors.h>
#include <vtkLookupTable.h>
#include <vtkEllipseFitting.h>
#include <vtkMatrix4x4.h>

#include <vtkImageResliceWithPlane.h>
#include <vtkComputeAirwayWall.h>

#include <vtkNRRDWriter.h>

// STD includes
#include <algorithm>
#include <string>
#include <iostream>
#include <sstream>

#ifdef WIN32
#define round(x) floor((x)+0.5)
#endif

//-----------------------------------------------------------------------------
vtkStandardNewMacro(vtkSlicerAirwayInspectorModuleLogic)

//-----------------------------------------------------------------------------
// vtkSlicerAirwayInspectorModuleLogic methods
//-----------------------------------------------------------------------------
vtkSlicerAirwayInspectorModuleLogic::vtkSlicerAirwayInspectorModuleLogic()
{
  this->SelfTuneModelSmooth[0]=0.0017;
  this->SelfTuneModelSmooth[1]=454.0426;
  this->SelfTuneModelSmooth[2]=3.0291;
  this->SelfTuneModelSharp[0]=0.0020;
  this->SelfTuneModelSharp[1]=493.6570;
  this->SelfTuneModelSharp[2]=2.9639;

  this->Reslicer = vtkImageResliceWithPlane::New();
  this->WallSolver = vtkComputeAirwayWall::New();
  this->WallSolver->SetMethod(1);
}

//-----------------------------------------------------------------------------
vtkSlicerAirwayInspectorModuleLogic::~vtkSlicerAirwayInspectorModuleLogic()
{
  this->Reslicer->Delete();
  this->WallSolver->Delete();
}

//-----------------------------------------------------------------------------
void vtkSlicerAirwayInspectorModuleLogic::PrintSelf(ostream& os, vtkIndent indent)
{
  Superclass::PrintSelf(os, indent);
}

vtkMRMLAirwayNode* vtkSlicerAirwayInspectorModuleLogic::AddAirwayNode(char *volumeNodeID,
                                                                      double x, double y, double z,
                                                                      double threshold)
{
  vtkMRMLAirwayNode *airwayNode = 0;
  if (volumeNodeID)
  {
    airwayNode = vtkMRMLAirwayNode::New();

    airwayNode->SetVolumeNodeID(volumeNodeID);
    airwayNode->SetThreshold(threshold);
    airwayNode->SetXYZ(x, y, z);
    this->GetMRMLScene()->AddNode(airwayNode);

    airwayNode->Delete();
  }
  return airwayNode;
}

////////////////////////////
void vtkSlicerAirwayInspectorModuleLogic::CreateAirway(vtkMRMLAirwayNode *node)
{
  vtkMRMLScalarVolumeNode *volumeNode = vtkMRMLScalarVolumeNode::SafeDownCast(
    this->GetMRMLScene()->GetNodeByID(node->GetVolumeNodeID()));
  if (volumeNode == 0)
    {
    return;
    }

  vtkImageData *inputImage = volumeNode->GetImageData();

  double orig[3];
  int dim[3];
  double sp[3], p[3],ijk[3];
  double x[3],y[3],z[3];
  inputImage->GetOrigin(orig);
  inputImage->GetSpacing(sp);
  inputImage->GetDimensions(dim);

  double resolution = node->GetResolution();

  //Create helper objects
  // Set up options
  if (node->GetReformat())
    {
    this->Reslicer->InPlaneOff();
    }
  else
    {
    this->Reslicer->InPlaneOn();
    }

  this->Reslicer->SetInputData(inputImage);
  this->Reslicer->SetInterpolationModeToCubic();
  this->Reslicer->ComputeCenterOff();
  this->Reslicer->SetDimensions(256,256,1);
  this->Reslicer->SetSpacing(resolution,resolution,resolution);
  //this->Reslicer->ComputeAxesOn();
  this->Reslicer->ComputeAxesOff();

  /***
  switch(this->GetAxisMode()) {
    case VTK_HESSIAN:
      this->Reslicer->ComputeAxesOn();
      break;
    case VTK_POLYDATA:
      if (input->GetLines() == NULL) {
        this->Reslicer->ComputeAxesOn();
        this->SetAxisMode(VTK_HESSIAN);
      } else {
        this->ComputeAirwayAxisFromLines();
        this->Reslicer->ComputeAxesOff();
      }
      break;
    case VTK_VECTOR:
      if (input->GetPointData()->GetVectors() == NULL)
       {
        this->Reslicer->ComputeAxesOn();
        this->SetAxisMode(VTK_HESSIAN);
       } else {
        this->Reslicer->ComputeAxesOff();
	cout<<"Using vectors"<<endl;
       }
      break;
   }
  */

  // Allocate data
  //Create point Data for each stats

  vtkDoubleArray *mean;
  vtkDoubleArray *std;
  vtkDoubleArray *min;
  vtkDoubleArray *max;
  vtkDoubleArray *ellipse;

  std::string methodTag;

  if (this->WallSolver->GetMethod() == 0)
  {
    methodTag = "FWHM";
  } else if (this->WallSolver->GetMethod() == 1)
  {
    methodTag = "ZC";
  } else if (this->WallSolver->GetMethod() == 2)
  {
    methodTag = "PC";
  }

  std::stringstream name;
  name << "airwaymetrics-" << methodTag.c_str() << "-mean";
  mean = vtkDoubleArray::New();
  mean->SetName(name.str().c_str());

  name.clear();
  name << "airwaymetrics-" << methodTag.c_str() << "-std";
  std = vtkDoubleArray::New();
  std->SetName(name.str().c_str());

  name.clear();
  name << "airwaymetrics-" << methodTag.c_str() << "-min";
  min = vtkDoubleArray::New();
  min->SetName(name.str().c_str());

  name.clear();
  name << "airwaymetrics-" << methodTag.c_str() << "-max";
  max = vtkDoubleArray::New();
  max->SetName(name.str().c_str());

  name.clear();
  name << "airwaymetrics-" << methodTag.c_str() << "-ellips";
  ellipse = vtkDoubleArray::New();
  ellipse->SetName(name.str().c_str());

  int nc = this->WallSolver->GetNumberOfQuantities();
  int np = 1;

  mean->SetNumberOfComponents(nc);
  mean->SetNumberOfTuples(np);
  std->SetNumberOfComponents(nc);
  std->SetNumberOfTuples(np);
  min->SetNumberOfComponents(nc);
  min->SetNumberOfTuples(np);
  max->SetNumberOfComponents(nc);
  max->SetNumberOfTuples(np);
  ellipse->SetNumberOfComponents(6);
  ellipse->SetNumberOfTuples(np);

  vtkEllipseFitting *eifit = vtkEllipseFitting::New();
  vtkEllipseFitting *eofit = vtkEllipseFitting::New();

  // In RAS
  node->GetXYZ(p);

  vtkMatrix4x4 *rasToIJK = vtkMatrix4x4::New();
  volumeNode->GetRASToIJKMatrix(rasToIJK);
  double xyz[4];
  xyz[0] = p[0];
  xyz[1] = p[1];
  xyz[2] = p[2];
  xyz[3] = 1;
  double *tmp = rasToIJK->MultiplyDoublePoint(xyz);

  ijk[0] = tmp[0];
  ijk[1] = tmp[1];
  ijk[2] = tmp[2];

  //this->Reslicer->SetCenter(0.5+(p[0]+orig[0])/sp[0],511-((p[1]+orig[1])/sp[1])+0.5,(p[2]-orig[2])/sp[2]);
  //ijk[0]=(p[0]-orig[0])/sp[0] ;
  //ijk[1]= (dim[1]-1) - (p[1]-orig[1])/sp[1];  // j coordinate has to be reflected (vtk origin is lower left and DICOM origing is upper left).
  //ijk[2]=(p[2]-orig[2])/sp[2];

  std::cout <<"Center Ijk: "<<ijk[0]<<" "<<ijk[1]<<" "<<ijk[2]<<std::endl;

  this->Reslicer->SetCenter(ijk[0],ijk[1],ijk[2]);

  /***
   switch(this->GetAxisMode()) {
     case VTK_HESSIAN:
       this->Reslicer->ComputeAxesOn();
       break;
     case VTK_POLYDATA:
       z[0]=this->AxisArray->GetComponent(0,0);
       z[1]=this->AxisArray->GetComponent(0,1);
       z[2]=this->AxisArray->GetComponent(0,2);
       //cout<<"Tangent: "<<z[0]<<" "<<z[1]<<" "<<z[2]<<endl;
       vtkMath::Perpendiculars(z,x,y,0);
       this->Reslicer->SetXAxis(x);
       this->Reslicer->SetYAxis(y);
       this->Reslicer->SetZAxis(z);
       break;
     case VTK_VECTOR:
       z[0]=input->GetPointData()->GetVectors()->GetComponent(0,0);
       z[1]=input->GetPointData()->GetVectors()->GetComponent(0,1);
       z[2]=input->GetPointData()->GetVectors()->GetComponent(0,2);
       //cout<<"Tangent: "<<z[0]<<" "<<z[1]<<" "<<z[2]<<endl;

       vtkMath::Perpendiculars(z,x,y,0);
       this->Reslicer->SetXAxis(x);
       this->Reslicer->SetYAxis(y);
       this->Reslicer->SetZAxis(z);
       break;
   }
   **/

   //cout<<"Before reslice"<<endl;
   this->Reslicer->Update();
   //cout<<"After reslice"<<endl;

   vtkImageData *img = this->Reslicer->GetOutput();

   double val = img->GetScalarComponentAsDouble(128, 128, 0, 0);

   vtkNRRDWriter *writer = vtkNRRDWriter::New();
   writer->SetFileName("C:\\tmp\\airay_slice.nrrd");
   writer->SetInputData(img);
   writer->Write();

   //this->Reslicer->GetOutput()->Print(std::cout);

   this->WallSolver->SetInputData(this->Reslicer->GetOutput());

   //this->WallSolver->SetInputData(this->Reslicer->GetOutput());
   //Maybe we have to update the threshold depending on the center value.
   if (this->WallSolver->GetMethod()==2)
   {
     // Use self tune phase congruency
     vtkComputeAirwayWall *tmp = vtkComputeAirwayWall::New();
     this->SetWallSolver(this->WallSolver,tmp);
     tmp->SetInputData(this->Reslicer->GetOutput());
     tmp->ActivateSectorOff();
     tmp->SetBandwidth(1.577154);
     tmp->SetNumberOfScales(12);
     tmp->SetMultiplicativeFactor(1.27);
     tmp->SetMinimumWavelength(2);
     tmp->UseWeightsOn();
     vtkDoubleArray *weights = vtkDoubleArray::New();
     weights->SetNumberOfTuples(12);
     double tt[12]={1.249966,0.000000,0.000000,0.734692,0.291580,0.048616,0.718651,0.000000,0.620357,0.212188,0.000000,1.094157};
     for (int i=0;i<12;i++)
     {
       weights->SetValue(i,tt[i]);
     }
     tmp->SetWeights(weights);
     tmp->Update();
     double wt = tmp->GetStatsMean()->GetComponent(4,0);
     tmp->Delete();
     weights->Delete();
     double ml;
     double *factors;
     switch (node->GetReconstruction())
     {
       case vtkMRMLAirwayNode::SMOOTH:
         factors = this->SelfTuneModelSmooth;
         break;
       case vtkMRMLAirwayNode::SHARP:
         factors = this->SelfTuneModelSharp;
         break;
     }
     ml = exp(factors[0]*pow(log(wt*factors[1]),factors[2]));
     this->WallSolver->SetMultiplicativeFactor(ml);
   }

   //cout<<"Update solver"<<endl;
   this->WallSolver->Update();
   //cout<<"Done solver"<<endl;

   //cout<<"Ellipse fitting 1: "<<this->WallSolver->GetInnerContour()->GetNumberOfPoints()<<endl;
   if (this->WallSolver->GetInnerContour()->GetNumberOfPoints() >= 3)
   {
     eifit->SetInputData(this->WallSolver->GetInnerContour());
     eifit->Update();
   }
   //cout<<"Ellipse fitting 2: "<<this->WallSolver->GetOuterContour()->GetNumberOfPoints()<<endl;
    if (this->WallSolver->GetOuterContour()->GetNumberOfPoints() >= 3)
    {
      eofit->SetInputData(this->WallSolver->GetOuterContour());
      eofit->Update();
    }
   //cout<<"Done ellipse fitting"<<endl;

   // Collect results and assign them to polydata
   for (int c = 0; c < this->WallSolver->GetNumberOfQuantities();c++)
   {
     mean->SetComponent(0,c,this->WallSolver->GetStatsMean()->GetComponent(2*c,0));
     std->SetComponent(0,c,this->WallSolver->GetStatsMean()->GetComponent((2*c)+1,0));
     min->SetComponent(0,c,this->WallSolver->GetStatsMinMax()->GetComponent(2*c,0));
     max->SetComponent(0,c,this->WallSolver->GetStatsMinMax()->GetComponent((2*c)+1,0));
   }

   ellipse->SetComponent(0,0,eifit->GetMinorAxisLength()*resolution);
   ellipse->SetComponent(0,1,eifit->GetMajorAxisLength()*resolution);
   ellipse->SetComponent(0,2,eifit->GetAngle());
   ellipse->SetComponent(0,3,eofit->GetMinorAxisLength()*resolution);
   ellipse->SetComponent(0,4,eofit->GetMajorAxisLength()*resolution);
   ellipse->SetComponent(0,5,eofit->GetAngle());

   vtkImageData *airwayImage = vtkImageData::New();
   this->CreateAirwayImage(this->Reslicer->GetOutput(),eifit,eofit,airwayImage);

   //if (node->GetSaveAirwayImage())
   node->SetAirwayImagePrefix("C:\\tmp\\airwayImage");
   if (0)
   {
     char fileName[10*256];
     vtkPNGWriter *writer = vtkPNGWriter::New();
     unsigned char *val = (unsigned char *)airwayImage->GetScalarPointer(128,128,0);
     //writer->SetInputData(this->Reslicer->GetOutput());
     writer->SetInputData(airwayImage);
     sprintf(fileName,"%s%03lld.png",node->GetAirwayImagePrefix(),0);
     writer->SetFileName(fileName);
     writer->Write();
     writer->Delete();
  }

  node->SetMin(min->GetValue(0));
  node->SetMax(max->GetValue(0));
  node->SetMean(mean->GetValue(0));
  node->SetStd(std->GetValue(0));
  node->SetAirwayImage(airwayImage);

  //Compute stats for each line if lines are available
  /***
  if (input->GetLines())
  {
    this->ComputeCellData();
  }
  **/

  eifit->Delete();
  eofit->Delete();
  airwayImage->Delete();
  rasToIJK->Delete();

  return;
}

void vtkSlicerAirwayInspectorModuleLogic::CreateAirwayImage(vtkImageData *resliceCT,
                                                            vtkEllipseFitting *eifit,
                                                            vtkEllipseFitting *eofit,
                                                            vtkImageData *airwayImage)
{
  vtkImageMapToColors *rgbFilter = vtkImageMapToColors::New();
  vtkLookupTable *lut = vtkLookupTable::New();

  rgbFilter->SetInputData(resliceCT);
  rgbFilter->SetOutputFormatToRGB();

  double *range = resliceCT->GetScalarRange();

  lut->SetSaturationRange(0,0);
  lut->SetHueRange(0,0);
  lut->SetValueRange(0,1);
  //lut->SetTableRange(-150,1500);
  lut->SetTableRange(range[0], range[1]);
  lut->Build();
  rgbFilter->SetLookupTable(lut);

  rgbFilter->Update();

  vtkImageData *rgbImage=rgbFilter->GetOutput();

  //Set Image voxels based on ellipse information

  /***
  double sp[3];
  rgbImage->GetSpacing(sp);
  int npoints=128;

  vtkEllipseFitting *arr[2];
  arr[0]=eifit;
  arr[1]=eofit;
  vtkEllipseFitting *eFit;

  float centerX = (eifit->GetCenter()[0] + eofit->GetCenter()[0])/2.0;
  float centerY = (eifit->GetCenter()[1] + eofit->GetCenter()[1])/2.0;

  int colorChannel[2];
  colorChannel[0]=0;
  colorChannel[1]=1;
  for (int ii=0;ii<2;ii++) {
    //eFit = static_cast <vtkEllipseFitting > (arr->GetNextItemAsObject());
    eFit =arr[ii];
    int rx,ry;
    for (int k=0;k<npoints;k++) {
      float t = -3.14159 + 2.0 * 3.14159 * k/(npoints -1.0);
      float angle = eFit->GetAngle();
      float px = centerX + eFit->GetMajorAxisLength() *cos(t) * cos(angle) -
                           eFit->GetMinorAxisLength() * sin(t) * sin(angle);
      float py = centerY + eFit->GetMajorAxisLength() *cos(t) * sin(angle) +
                           eFit->GetMinorAxisLength() * sin(t) * cos(angle);

      //Set Image Value with antialiasing
      //rx= floor(px);
      //ry= floor(py);
      //rgbImage->SetScalarComponentFromFloat(rx,ry,0,colorChannel[ii],255*(1-(rx-px))*(1-(ry-py)));
      //So on and so forth...
      // Simple NN
      for (int cc=0;cc<rgbImage->GetNumberOfScalarComponents();cc++)
        {
	      rgbImage->SetScalarComponentFromFloat(round(px),round(py),0,cc,0);
        }

      rgbImage->SetScalarComponentFromFloat(round(px),round(py),0,colorChannel[ii],255);
    }
  }
  **/
  airwayImage->DeepCopy(rgbImage);

  lut->Delete();
  rgbFilter->Delete();
}

void vtkSlicerAirwayInspectorModuleLogic::SetWallSolver(vtkComputeAirwayWall *ref, vtkComputeAirwayWall *out)
{
  out->SetMethod(ref->GetMethod());
  out->SetWallThreshold(ref->GetWallThreshold());
  out->SetNumberOfScales(ref->GetNumberOfScales());
  out->SetBandwidth(ref->GetBandwidth());
  out->SetMinimumWavelength(ref->GetMinimumWavelength());
  out->SetMultiplicativeFactor(ref->GetMultiplicativeFactor());
  out->SetUseWeights(ref->GetUseWeights());
  out->SetWeights(ref->GetWeights());
  out->SetThetaMax(ref->GetThetaMax());
  out->SetThetaMin(ref->GetThetaMin());
  out->SetRMin(ref->GetRMin());
  out->SetRMax(ref->GetRMax());
  out->SetDelta(ref->GetDelta());
  out->SetScale(ref->GetScale());
  out->SetNumberOfThetaSamples(ref->GetNumberOfThetaSamples());
  out->SetAlpha(out->GetAlpha());
  out->SetT(out->GetT());
  out->SetActivateSector(ref->GetActivateSector());
}
