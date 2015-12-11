// Annotation includes
#include "vtkSlicerAirwayInspectorModuleLogic.h"

#include <vtkPNGWriter.h>

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
#include <vtkVersion.h>
#include <vtkImageEllipsoidSource.h>
#include <vtkImageCast.h>
#include <vtkImageMapToColors.h>
#include <vtkLookupTable.h>
#include <vtkEllipseFitting.h>
#include <vtkMatrix4x4.h>
#include <vtkImageThreshold.h>
#include <vtkImageReslice.h>
#include <vtkImageThreshold.h>
#include <vtkImageSeedConnectivity.h>
#include <vtkComputeCentroid.h>

#include <vtkImageResliceWithPlane.h>
#include <vtkComputeAirwayWall.h>

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
                                                                      double x, double y, double z)
{
  vtkMRMLAirwayNode *airwayNode = 0;
  if (volumeNodeID)
  {
    airwayNode = vtkMRMLAirwayNode::New();

    airwayNode->SetVolumeNodeID(volumeNodeID);
    airwayNode->SetXYZ(x, y, z);
    airwayNode->SetCenterXYZ(x, y, z);
    this->GetMRMLScene()->AddNode(airwayNode);

    airwayNode->Delete();
  }
  return airwayNode;
}

////////////////////////////
vtkImageData* vtkSlicerAirwayInspectorModuleLogic::CreateAirwaySlice(vtkMRMLAirwayNode *node)
{
  vtkMRMLScalarVolumeNode *volumeNode = vtkMRMLScalarVolumeNode::SafeDownCast(
    this->GetMRMLScene()->GetNodeByID(node->GetVolumeNodeID()));
  if (volumeNode == 0)
    {
    return 0;
    }

  vtkImageData *inputImage = volumeNode->GetImageData();

  if (node->GetComputeCenter())
    {
    this->ComputeCenter(node);
    }

  double orig[3];
  int dim[3];
  double sp[3], p[3],ijk[3];
  double x[3],y[3],z[3];
  inputImage->GetOrigin(orig);
  inputImage->GetSpacing(sp);
  inputImage->GetDimensions(dim);

  double resolution = node->GetResolution();
  this->Reslicer->SetInPlane(!node->GetReformat());
  this->Reslicer->SetInputData(inputImage);
  this->Reslicer->SetInterpolationModeToCubic();
  this->Reslicer->SetComputeCenter(node->GetRefineCenter());
  this->Reslicer->SetDimensions(256,256,1);
  this->Reslicer->SetSpacing(resolution,resolution,resolution);
  this->Reslicer->ComputeAxesOn();

  // In RAS
  node->GetCenterXYZ(p);

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

  //std::cout <<"Center Ijk: "<<ijk[0]<<" "<<ijk[1]<<" "<<ijk[2]<<std::endl;

  this->Reslicer->SetCenter(ijk[0],ijk[1],ijk[2]);

  this->Reslicer->Update();

  node->SetXAxis(this->Reslicer->GetXAxis());
  node->SetYAxis(this->Reslicer->GetYAxis());
  node->SetZAxis(this->Reslicer->GetZAxis());
  //node->SetAirwayImage(his->Reslicer->GetOutput());

  vtkImageData *image = vtkImageData::New();
  image->DeepCopy(this->Reslicer->GetOutput());
  node->SetAirwayImage(image);
  image->Delete();

  return image;
}

////////////////////////////
void vtkSlicerAirwayInspectorModuleLogic::ComputeAirwayWall(vtkImageData* sliceImage, vtkMRMLAirwayNode *node, int method)
{
  vtkMRMLScalarVolumeNode *volumeNode = vtkMRMLScalarVolumeNode::SafeDownCast(
    this->GetMRMLScene()->GetNodeByID(node->GetVolumeNodeID()));
  if (volumeNode == 0)
    {
    return;
    }

  this->WallSolver->SetMethod(method);
  this->WallSolver->SetDelta(0.1);
  this->WallSolver->SetWallThreshold(node->GetThreshold());

  std::string methodTag;

  if (this->WallSolver->GetMethod() == 0)
  {
    methodTag = "FWHM";
  }
  else if (this->WallSolver->GetMethod() == 1)
  {
    methodTag = "Zero Crossing";
  }
  else if (this->WallSolver->GetMethod() == 2)
  {
    methodTag = "PC-Single Kernel";
  }
  else if (this->WallSolver->GetMethod() == 3)
  {
    methodTag = "PC-Multiple Kernels";
  }

  vtkDoubleArray *mean = node->GetMean(method);
  if (!mean)
    {
    mean = vtkDoubleArray::New();
    node->SetMean(method, mean);
    }
  vtkDoubleArray *std = node->GetStd(method);
  if (!std)
    {
    std = vtkDoubleArray::New();
    node->SetStd(method, std);
    }
  vtkDoubleArray *min = node->GetMin(method);
  if (!min)
    {
    min = vtkDoubleArray::New();
    node->SetMin(method, min);
    }
  vtkDoubleArray *max = node->GetMax(method);
  if (!max)
    {
    max = vtkDoubleArray::New();
    node->SetMax(method, max);
    }

  std::stringstream name;
  name << "airwaymetrics-" << method << "-mean";
  mean->SetName(name.str().c_str());

  name.clear();
  name << "airwaymetrics-" << method << "-std";
  std->SetName(name.str().c_str());

  name.clear();
  name << "airwaymetrics-" << method << "-min";
  min->SetName(name.str().c_str());

  name.clear();
  name << "airwaymetrics-" << method << "-max";
  max->SetName(name.str().c_str());

  name.clear();
  name << "airwaymetrics-" << method << "-ellips";
  node->GetEllipse()->SetName(name.str().c_str());

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
  node->GetEllipse()->SetNumberOfComponents(6);
  node->GetEllipse()->SetNumberOfTuples(np);

  this->WallSolver->SetInputData(sliceImage);

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
     node->GetEllipseInside()->SetInputData(this->WallSolver->GetInnerContour());
     node->GetEllipseInside()->Update();
   }
   //cout<<"Ellipse fitting 2: "<<this->WallSolver->GetOuterContour()->GetNumberOfPoints()<<endl;
    if (this->WallSolver->GetOuterContour()->GetNumberOfPoints() >= 3)
    {
      node->GetEllipseOutside()->SetInputData(this->WallSolver->GetOuterContour());
      node->GetEllipseOutside()->Update();
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

   double resolution = node->GetResolution();

   node->GetEllipse()->SetComponent(0,0,node->GetEllipseInside()->GetMinorAxisLength()*resolution);
   node->GetEllipse()->SetComponent(0,1,node->GetEllipseInside()->GetMajorAxisLength()*resolution);
   node->GetEllipse()->SetComponent(0,2,node->GetEllipseInside()->GetAngle());
   node->GetEllipse()->SetComponent(0,3,node->GetEllipseOutside()->GetMinorAxisLength()*resolution);
   node->GetEllipse()->SetComponent(0,4,node->GetEllipseOutside()->GetMajorAxisLength()*resolution);
   node->GetEllipse()->SetComponent(0,5,node->GetEllipseOutside()->GetAngle());

  return;
}

void vtkSlicerAirwayInspectorModuleLogic::CreateColorImage(vtkImageData *resliceCT,
                                                           vtkImageData *colorImage)
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
  lut->SetTableRange(-1000, -500);
  lut->Build();
  rgbFilter->SetLookupTable(lut);

  rgbFilter->Update();

  vtkImageData *rgbImage=rgbFilter->GetOutput();

  colorImage->DeepCopy(rgbImage);

  lut->Delete();
  rgbFilter->Delete();
}

void vtkSlicerAirwayInspectorModuleLogic::AddEllipsesToImage(vtkImageData *sliceRGBImage,
                                                             vtkMRMLAirwayNode *node,
                                                             vtkImageData *rgbImage)
{
  if (sliceRGBImage == NULL || rgbImage == NULL)
  {
    return;
  }

  rgbImage->DeepCopy(sliceRGBImage);

  //Set Image voxels based on ellipse information
  if (node->GetEllipseInside() && node->GetEllipseOutside())
    {
    double sp[3];
    rgbImage->GetSpacing(sp);
    int npoints=128;

    vtkEllipseFitting *arr[2];
    arr[0]=node->GetEllipseInside();
    arr[1]=node->GetEllipseOutside();
    vtkEllipseFitting *eFit;

    float centerX = (node->GetEllipseInside()->GetCenter()[0] + node->GetEllipseOutside()->GetCenter()[0])/2.0;
    float centerY = (node->GetEllipseInside()->GetCenter()[1] + node->GetEllipseOutside()->GetCenter()[1])/2.0;

    int colorChannel[2];
    colorChannel[0]=0;
    colorChannel[1]=1;
    for (int ii=0;ii<2;ii++)
      {
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
    }
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

/////////////////////////////////
void vtkSlicerAirwayInspectorModuleLogic::ComputeCenter(vtkMRMLAirwayNode* node)
{
  vtkMRMLScalarVolumeNode *volumeNode = vtkMRMLScalarVolumeNode::SafeDownCast(
    this->GetMRMLScene()->GetNodeByID(node->GetVolumeNodeID()));
  if (volumeNode == 0)
    {
    return;
    }

  vtkImageData *inputImage = volumeNode->GetImageData();
  double *p = node->GetXYZ();

  // convert RAS to IJK
  vtkMatrix4x4 *rasToIJK = vtkMatrix4x4::New();
  volumeNode->GetRASToIJKMatrix(rasToIJK);
  double xyz[4];
  xyz[0] = p[0];
  xyz[1] = p[1];
  xyz[2] = p[2];
  xyz[3] = 1;
  double *tmp = rasToIJK->MultiplyDoublePoint(xyz);
  double ijk[3];
  ijk[0] = tmp[0];
  ijk[1] = tmp[1];
  ijk[2] = tmp[2];

  double orig[3];
  int dim[3];
  dim[0] = 128;
  dim[1] = 128;
  dim[2] = 1;
  double outsp[3];
  outsp[0] = 0.25;
  outsp[1] = 0.25;
  outsp[2] = 0.25;

  double unitsp[3];
  double insp[3];

  inputImage->GetOrigin(orig);

  volumeNode->GetSpacing(insp);
  inputImage->GetSpacing(unitsp);

  inputImage->SetSpacing(insp);

  double pixelshift = 0.5;
  double outcenter[3];
  for (int i=0; i<3; i++)
    {
    outcenter[i] = dim[i]*0.5 - pixelshift;
    }

  //Create helper objects
  // Set up options
  vtkImageReslice* rFind = vtkImageReslice::New();
  rFind->SetInputData(inputImage);
  rFind->SetOutputDimensionality( 2 );
  rFind->SetOutputExtent( 0, dim[0]-1,
                          0, dim[1]-1,
                          0, dim[2]-1);
  rFind->SetOutputSpacing(outsp);
  rFind->SetOutputOrigin(-1.0*outcenter[0]*outsp[0],
                         -1.0*outcenter[1]*outsp[1],
                         -1.0*outcenter[2]*outsp[2]);

  rFind->SetResliceAxesDirectionCosines( 1, 0, 0, 0, 1, 0, 0, 0, 1);
  rFind->SetResliceAxesOrigin(orig[0] + ijk[0]*insp[0],
                              orig[1] + ijk[1]*insp[1],
                              orig[2] + ijk[2]*insp[2]);
  rFind->SetInterpolationModeToLinear();
  rFind->Update();

  // Compute Threshold
  vtkImageThreshold *th = vtkImageThreshold::New();
  th->SetInputData(rFind->GetOutput());
  th->ThresholdBetween(node->GetAirBaselineIntensity(),
                       node->GetThreshold());
  th->SetInValue (1);
  th->SetOutValue (0);
  th->ReplaceInOn();
  th->ReplaceOutOn();
  th->SetOutputScalarTypeToUnsignedChar();
  th->Update();

  vtkImageSeedConnectivity *cc = vtkImageSeedConnectivity::New();
  cc->SetInputData(th->GetOutput());
  cc->AddSeed(outcenter[0]+0.5,outcenter[1]+0.5,outcenter[2]+0.5);
  cc->SetInputConnectValue(1);
  cc->SetOutputConnectedValue(1);
  cc->SetOutputUnconnectedValue(0);
  cc->Update();

  //Flag is zero if not CC has been found.
  int flag = cc->GetOutput()->GetScalarRange()[1];

  vtkComputeCentroid *ccen = vtkComputeCentroid::New();
  ccen->SetInputData(cc->GetOutput());
  ccen->Update();
  double *centroid = ccen->GetCentroid();

  // delta IJK
  double wcp[4];
  for (int k=0; k<3; k++)
    {
    wcp[k] = ijk[k] + centroid[k] - outcenter[k];
    }
  wcp[3] = 1;

  // IJK to RAS
  rasToIJK->Invert();
  tmp = rasToIJK->MultiplyDoublePoint(wcp);
  wcp[0] = tmp[0];
  wcp[1] = tmp[1];
  wcp[2] = tmp[2];

  if (flag)
    {
    node->SetCenterXYZ(wcp);
    }

  inputImage->SetSpacing(unitsp);

  rFind->Delete();
  th->Delete();
  cc->Delete();
  ccen->Delete();
}

