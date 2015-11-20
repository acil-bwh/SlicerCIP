/*==============================================================================

  Program: 3D Slicer

  Copyright (c) Kitware Inc.

  See COPYRIGHT.txt
  or http://www.slicer.org/copyright/copyright.txt for details.

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.

  This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc.
  and was partially funded by NIH grant 3P41RR013218-12S1

==============================================================================*/

// Qt includes

// CTK includes
//#include <ctkModelTester.h>

#include "qSlicerAirwayInspectorModuleWidget.h"
#include "ui_qSlicerAirwayInspectorModuleWidget.h"

#include "vtkRenderWindowInteractor.h"
#include "vtkRenderWindow.h"
#include "vtkRendererCollection.h"
#include "vtkInteractorObserver.h"
#include "vtkActor2D.h"
#include "vtkPolyDataMapper2D.h"
#include "vtkProperty2D.h"
#include "vtkImageMapToColors.h"
#include "vtkImageMapper.h"
#include "vtkLookupTable.h"
#include "vtkMatrix4x4.h"
#include "vtkImageReader.h"
#include "vtkNRRDWriter.h"
#include "vtkPNGWriter.h"
#include "vtkImageFlip.h"
#include "vtkImageCast.h"

#include "qpainter.h"
#include "qmainwindow.h"
#include "QVTKWidget.h"

#include "vtkMRMLScene.h"
#include "vtkMRMLScalarVolumeNode.h"
#include "vtkMRMLAirwayNode.h"
#include "vtkMRMLSliceNode.h"

#include "qSlicerApplication.h"
#include "qSlicerLayoutManager.h"
#include "qMRMLSliceWidget.h"
#include "qMRMLSliceView.h"
#include "qMRMLUtils.h"

#include "vtkSlicerAirwayInspectorModuleLogic.h"
//-----------------------------------------------------------------------------
/// \ingroup Slicer_QtModules_AirwayInspector
class qSlicerAirwayInspectorModuleWidgetPrivate: public Ui_qSlicerAirwayInspectorModuleWidget
{
public:

  QVTKWidget *qvtkWidget;
};

//-----------------------------------------------------------------------------
qSlicerAirwayInspectorModuleWidget::qSlicerAirwayInspectorModuleWidget(QWidget* _parent)
  : Superclass(_parent)
  , d_ptr(new qSlicerAirwayInspectorModuleWidgetPrivate)
{
  this->interactors.clear();
  this->interactorCallBackCommand = vtkSmartPointer<vtkCallbackCommand>::New();
  this->interactorCallBackCommand->SetCallback(
      qSlicerAirwayInspectorModuleWidget::DoInteractorCallback);
  this->interactorCallBackCommand->SetClientData(this);

  this->Renderer =
    vtkSmartPointer<vtkRenderer>::New();
}

//-----------------------------------------------------------------------------
qSlicerAirwayInspectorModuleWidget::~qSlicerAirwayInspectorModuleWidget()
{
  // Remove observers
  //this->removeInteractorObservers();
}
//-----------------------------------------------------------------------------
void qSlicerAirwayInspectorModuleWidget::setup()
{
  Q_D(qSlicerAirwayInspectorModuleWidget);
  d->setupUi(this);

  d->ThresholdSpinBox->setRange(-1000, -300);
  d->ThresholdSpinBox->setValue(-850);
  // VTK/Qt
  d->qvtkWidget = new QVTKWidget;
  d->qvtkWidget->GetRenderWindow()->AddRenderer(this->Renderer);
  d->qvtkWidget->setFixedSize(200,200);
  d->horizontalLayout->addWidget(d->qvtkWidget);

  d->ReportTable->setEditTriggers(QAbstractItemView::NoEditTriggers);
  d->ReportTable->setSizePolicy(QSizePolicy::Expanding,QSizePolicy::Expanding);
  d->ReportTable->setColumnCount(4);
	d->ReportTable->setHorizontalHeaderLabels(QString("Min;Max;Mean;Std").split(";"));
  d->ReportTable->setVerticalHeaderLabels(QString("Inner Radius (mm);Outer Radius (mm);Wall Thickness (mm);" \
          "Wall Intensity (HU);Peak WI (HU);Inner WI (HU);Outer WI (HU);WA%;Pi (mm);" \
           "sqrt(WA) (mm);Ai (mm^2);Ao (mm^2);Vessel Intensity (HU);RL Inner Diam (mm);" \
           "RL Outer Diam (mm);AP Inner Diam (mm);AP Outer Diam (mm);Lumen I (HU);Parenchyma I (HU);Energy;Power").split(";"));

  //d->ReportTable

  QObject::connect(d->InputVolumeComboBox, SIGNAL(currentNodeChanged(vtkMRMLNode*)),
                   this, SLOT(setMRMLVolumeNode(vtkMRMLNode*)));

  QObject::connect(d->AnalyzeButton, SIGNAL(pressed()),
                   this, SLOT(analyzeSelected()));

  QObject::connect(d->AnalyzeAllButton, SIGNAL(pressed()),
                   this, SLOT(analyzeAll()));

  QObject::connect(d->WriteCSVFileButton, SIGNAL(pressed()),
                   this, SLOT(writeCSV()));

  QObject::connect(d->AirwayComboBox, SIGNAL(currentNodeChanged(vtkMRMLNode*)),
                   this, SLOT(setMRMLAirwayNode(vtkMRMLNode*)));

  QObject::connect(d->ThresholdSpinBox, SIGNAL(valueChanged(double)),
                   this, SLOT(onThresholdChanged(double)));

  QObject::connect(d->ComputeCenterCheckBox, SIGNAL(toggled(bool)),
                   this, SLOT(onToggled(bool)));

  QObject::connect(d->RefineCenterCheckBox, SIGNAL(toggled(bool)),
                   this, SLOT(onToggled(bool)));

  QObject::connect(d->ReformatCheckBox, SIGNAL(toggled(bool)),
                   this, SLOT(onToggled(bool)));

  QObject::connect(d->MethodComboBox, SIGNAL(currentIndexChanged(int)),
                   this, SLOT(onMethodChanged(int)));
}

//-----------------------------------------------------------------------------
void qSlicerAirwayInspectorModuleWidget::setMRMLScene(vtkMRMLScene *newScene)
{
  Q_D(qSlicerAirwayInspectorModuleWidget);

  vtkMRMLScene* oldScene = this->mrmlScene();

  this->Superclass::setMRMLScene(newScene);

  vtkSlicerAirwayInspectorModuleLogic *logic = vtkSlicerAirwayInspectorModuleLogic::SafeDownCast(this->logic());
  if (!logic)
    {
    return;
    }
  qSlicerApplication * app = qSlicerApplication::application();
  if (!app)
    {
    return;
    }
  qSlicerLayoutManager * layoutManager = app->layoutManager();
  if (!layoutManager)
    {
    return;
    }

  this->removeInteractorObservers();

  this->addAndObserveInteractors();

  // Need to listen for any new slice or view nodes being added
  //this->qvtkReconnect(oldScene, newScene, vtkMRMLScene::NodeAddedEvent,
  //                    this, SLOT(onNodeAddedEvent(vtkObject*,vtkObject*)));

  // Need to listen for any slice or view nodes being removed
  //this->qvtkReconnect(oldScene, newScene, vtkMRMLScene::NodeRemovedEvent,
  //                    this, SLOT(onNodeRemovedEvent(vtkObject*,vtkObject*)));

  // Listen to changes in the Layout so we only show controllers for
  // the visible nodes
  QObject::connect(layoutManager, SIGNAL(layoutChanged(int)), this,
                   SLOT(onLayoutChanged(int)));
}

//-----------------------------------------------------------------------------
void qSlicerAirwayInspectorModuleWidget::addAndObserveInteractors()
{
  vtkMRMLScene* scene = this->mrmlScene();

  // Search the scene for the available view nodes and create a
  // Controller and connect it up

  scene->InitTraversal();
  for (vtkMRMLNode *sn = NULL; (sn=scene->GetNextNodeByClass("vtkMRMLSliceNode"));)
    {
    vtkMRMLSliceNode *snode = vtkMRMLSliceNode::SafeDownCast(sn);
    if (snode)
      {
      qMRMLSliceWidget *sliceWidget = qSlicerApplication::application()->layoutManager()->sliceWidget(snode->GetLayoutName());
      if (sliceWidget)
        {
        vtkRenderWindowInteractor *ineractor =  sliceWidget->sliceView()->interactorStyle()->GetInteractor();
        this->addAndObserveInteractor(ineractor, snode);
        }
      }
    }
}

//----------------------------------------------------------------------------
void qSlicerAirwayInspectorModuleWidget::DoInteractorCallback(
    vtkObject* vtk_obj, unsigned long event, void* client_data, void* vtkNotUsed(call_data))
{
  // vtkInteractor is expected to be source of the event
  vtkRenderWindowInteractor *interactor =   vtkRenderWindowInteractor::SafeDownCast(vtk_obj);

  assert(interactor);

  qSlicerAirwayInspectorModuleWidget* self =
      reinterpret_cast<qSlicerAirwayInspectorModuleWidget*>(client_data);
  assert(self);

  self->onInteractorEvent(interactor, event);
}

//-----------------------------------------------------------------------------
void qSlicerAirwayInspectorModuleWidget::removeInteractorObservers()
{
  for (std::map<vtkRenderWindowInteractor*, vtkMRMLSliceNode*>::iterator it = this->interactors.begin();
       it != this->interactors.end();
       it++)
    {
     it->first->RemoveObserver(this->interactorCallBackCommand);
    }
}

//----------------------------------------------------------------------------
void qSlicerAirwayInspectorModuleWidget::addAndObserveInteractor(vtkRenderWindowInteractor* newInteractor,
                                         vtkMRMLSliceNode* snode)
{
  if (newInteractor)
    {
    newInteractor->AddObserver(vtkCommand::KeyReleaseEvent, this->interactorCallBackCommand);
    }
  this->interactors[newInteractor] = snode;
}

//---------------------------------------------------------------------------
void qSlicerAirwayInspectorModuleWidget::onInteractorEvent(vtkRenderWindowInteractor* interactor, int eventid)
{
  Q_D(qSlicerAirwayInspectorModuleWidget);

  vtkSlicerAirwayInspectorModuleLogic *logic = vtkSlicerAirwayInspectorModuleLogic::SafeDownCast(this->logic());
  if (!logic)
    {
    return;
    }
  if (d->InputVolumeComboBox->currentNode() == 0)
  {
    return;
  }

  if (eventid == vtkCommand::KeyReleaseEvent &&
    interactor->GetKeyCode() == 'a'  )
    {
    double x = interactor->GetEventPosition()[0];
    double y = interactor->GetEventPosition()[1];

    double windowWidth = interactor->GetRenderWindow()->GetSize()[0];
    double windowHeight = interactor->GetRenderWindow()->GetSize()[1];

    if (x < windowWidth && y < windowHeight)
      {
      // it's a 3D displayable manager and the click could have been on a node
      double yNew = windowHeight - y - 1;

      vtkMRMLSliceNode* snode = this->interactors[interactor];
      vtkMatrix4x4 *xyToRAS = snode->GetXYToRAS();
      double xyz[4];
      xyz[0] = x;
      xyz[1] = y;
      //xyz[1] = yNew;
      xyz[2] = 0;
      xyz[3] = 1;
      double *xyzRAS = xyToRAS->MultiplyDoublePoint(xyz);

      x = xyzRAS[0];
      y = xyzRAS[1];
      double z = snode->GetSliceOffset();

      //xyToRAS->Print(std::cout);
      //std::cout << "Event xyz =" << xyz[0] << "," << xyz[1] << "," << xyz[2] << std::endl;
      //std::cout << "RAS xyz =" << x << "," << y << "," << z << std::endl;

      vtkMRMLAirwayNode *airwayNode =
        logic->AddAirwayNode(d->InputVolumeComboBox->currentNode()->GetID(), x,y,z);

      this->updateMRMLFromWidget(airwayNode);

      logic->CreateAirwaySlice(airwayNode);

      d->AirwayComboBox->setCurrentNode(airwayNode);
      //this->updateViewer(airwayNode);

      if (d->DetectAutomaticallyCheckBox->isChecked())
        {
        this->analyzeSelected();
        }
      if (d->WriteAirwaysCheckBox->isChecked())
        {
        this->saveAirwayImage(airwayNode);
        }
      }
    }
}

// --------------------------------------------------------------------------
void qSlicerAirwayInspectorModuleWidget::onLayoutChanged(int)
{
  if (!this->mrmlScene() || this->mrmlScene()->IsBatchProcessing())
    {
    return;
    }
  this->removeInteractorObservers();

  this->addAndObserveInteractors();
}

//-----------------------------------------------------------------------------
void qSlicerAirwayInspectorModuleWidget::setMRMLVolumeNode(vtkMRMLNode* mrmlNode)
{
  Q_D(qSlicerAirwayInspectorModuleWidget);

  vtkMRMLScalarVolumeNode* volumeNode = vtkMRMLScalarVolumeNode::SafeDownCast(
    d->InputVolumeComboBox->currentNode());

  vtkSlicerAirwayInspectorModuleLogic *airwayLogic = vtkSlicerAirwayInspectorModuleLogic::SafeDownCast(this->logic());
  if (airwayLogic && volumeNode)
    {
    /// TODO: do we need to do anything here?
    }
}

//-----------------------------------------------------------------------------
void qSlicerAirwayInspectorModuleWidget::setMRMLAirwayNode(vtkMRMLNode* mrmlNode)
{
  Q_D(qSlicerAirwayInspectorModuleWidget);

  vtkMRMLAirwayNode* airwayNode = vtkMRMLAirwayNode::SafeDownCast(
    d->AirwayComboBox->currentNode());

   this->updateWidgetFromMRML(airwayNode);

   this->updateReport(airwayNode);

   this->updateViewer(airwayNode);
}

//-----------------------------------------------------------------------------
void qSlicerAirwayInspectorModuleWidget::updateAirwaySlice()
{
  Q_D(qSlicerAirwayInspectorModuleWidget);

  vtkMRMLAirwayNode *airwayNode = vtkMRMLAirwayNode::SafeDownCast(d->AirwayComboBox->currentNode());
  vtkSlicerAirwayInspectorModuleLogic *logic = vtkSlicerAirwayInspectorModuleLogic::SafeDownCast(this->logic());

  if (!logic || !airwayNode)
    {
    return;
    }

  this->updateMRMLFromWidget(airwayNode);

  logic->CreateAirwaySlice(airwayNode);

  this->updateViewer(airwayNode);

  if (d->DetectAutomaticallyCheckBox->isChecked())
    {
    this->analyzeSelected();
    }
  if (d->WriteAirwaysCheckBox->isChecked())
    {
    this->saveAirwayImage(airwayNode);
    }

  return;
}

//-----------------------------------------------------------------------------
void qSlicerAirwayInspectorModuleWidget::onThresholdChanged(double)
{
  this->updateAirwaySlice();
}

//-----------------------------------------------------------------------------
void qSlicerAirwayInspectorModuleWidget::onToggled(bool)
{
  this->updateAirwaySlice();
}

//-----------------------------------------------------------------------------
void qSlicerAirwayInspectorModuleWidget::onMethodChanged(int)
{
  this->updateAirwaySlice();
}

//-----------------------------------------------------------------------------
void qSlicerAirwayInspectorModuleWidget::updateWidgetFromMRML(vtkMRMLAirwayNode* airwayNode)
{
  Q_D(qSlicerAirwayInspectorModuleWidget);

  if (airwayNode)
    {
    d->RefineCenterCheckBox->setChecked(airwayNode->GetRefineCenter());
    d->ComputeCenterCheckBox->setChecked(airwayNode->GetComputeCenter());
    d->ThresholdSpinBox->setValue(airwayNode->GetThreshold());
    d->MethodComboBox->setCurrentIndex(airwayNode->GetMethod());
    d->ReformatCheckBox->setChecked(airwayNode->GetReformat());
    }
}

//-----------------------------------------------------------------------------
void qSlicerAirwayInspectorModuleWidget::updateMRMLFromWidget(vtkMRMLAirwayNode* airwayNode)
{
  Q_D(qSlicerAirwayInspectorModuleWidget);

  if (airwayNode)
    {
    airwayNode->SetComputeCenter(d->ComputeCenterCheckBox->isChecked());
    airwayNode->SetRefineCenter(d->RefineCenterCheckBox->isChecked());
    airwayNode->SetThreshold(d->ThresholdSpinBox->value());
    airwayNode->SetMethod(d->MethodComboBox->currentIndex());
    airwayNode->SetReformat(d->ReformatCheckBox->isChecked());
    }
}

//-----------------------------------------------------------------------------
void qSlicerAirwayInspectorModuleWidget::analyzeSelected()
{
  Q_D(qSlicerAirwayInspectorModuleWidget);

  vtkMRMLAirwayNode* airwayNode = vtkMRMLAirwayNode::SafeDownCast(
    d->AirwayComboBox->currentNode());

  vtkSlicerAirwayInspectorModuleLogic *airwayLogic = vtkSlicerAirwayInspectorModuleLogic::SafeDownCast(this->logic());
  if (airwayLogic)
    {
    this->updateMRMLFromWidget(airwayNode);

    airwayLogic->ComputeAirwayWall(airwayNode->GetAirwayImage(), airwayNode);
    }

  this->updateReport(airwayNode);

  this->updateViewer(airwayNode);

  if (d->WriteAirwaysCheckBox->isChecked())
  {
    this->saveAirwayImage(airwayNode);
  }
}

//-----------------------------------------------------------------------------
void qSlicerAirwayInspectorModuleWidget::analyzeAll()
{
  Q_D(qSlicerAirwayInspectorModuleWidget);
  vtkSlicerAirwayInspectorModuleLogic *airwayLogic = vtkSlicerAirwayInspectorModuleLogic::SafeDownCast(this->logic());
  if (!airwayLogic || !this->mrmlScene() )
    {
    return;
    }

  std::vector<vtkMRMLNode *> nodes;
  this->mrmlScene()->GetNodesByClass("vtkMRMLAirwayNode", nodes);

  for (int i=0; i<nodes.size(); i++)
    {
    vtkMRMLAirwayNode* airwayNode = vtkMRMLAirwayNode::SafeDownCast(nodes[i]);

    this->updateMRMLFromWidget(airwayNode);

    airwayLogic->ComputeAirwayWall(airwayNode->GetAirwayImage(), airwayNode);

    if (d->WriteAirwaysCheckBox->isChecked())
      {
      this->saveAirwayImage(airwayNode);
      }
    }

  vtkMRMLAirwayNode* airwayNode = vtkMRMLAirwayNode::SafeDownCast(
    d->AirwayComboBox->currentNode());

  this->updateReport(airwayNode);

  this->updateViewer(airwayNode);
}

//-----------------------------------------------------------------------------
void qSlicerAirwayInspectorModuleWidget::updateReport(vtkMRMLAirwayNode* airwayNode)
{
  Q_D(qSlicerAirwayInspectorModuleWidget);
  if (airwayNode == 0)
    {
    return;
    }

  // report the results
  d->ReportTable->setSizePolicy(QSizePolicy::Expanding,QSizePolicy::Expanding);

	int numCols = 4;

  if (airwayNode->GetMin()->GetNumberOfTuples() == 0 ||
      airwayNode->GetMax()->GetNumberOfTuples() == 0 ||
      airwayNode->GetMean()->GetNumberOfTuples() == 0 ||
      airwayNode->GetStd()->GetNumberOfTuples() == 0)
  {
    return;
  }
  int numRows = airwayNode->GetMin()->GetNumberOfComponents();
  numRows = numRows < airwayNode->GetMax()->GetNumberOfComponents() ? numRows : airwayNode->GetMax()->GetNumberOfComponents();
  numRows = numRows < airwayNode->GetMean()->GetNumberOfComponents() ? numRows : airwayNode->GetMean()->GetNumberOfComponents();
  numRows = numRows < airwayNode->GetStd()->GetNumberOfComponents() ? numRows : airwayNode->GetStd()->GetNumberOfComponents();

  d->ReportTable->setRowCount(numRows);
  d->ReportTable->setVerticalHeaderLabels(QString("Inner Radius (mm);Outer Radius (mm);Wall Thickness (mm);" \
          "Wall Intensity (HU);Peak WI (HU);Inner WI (HU);Outer WI (HU);WA%;Pi (mm);" \
           "sqrt(WA) (mm);Ai (mm^2);Ao (mm^2);Vessel Intensity (HU);RL Inner Diam (mm);" \
           "RL Outer Diam (mm);AP Inner Diam (mm);AP Outer Diam (mm);Lumen I (HU);Parenchyma I (HU);Energy;Power").split(";"));

	//Add Table items here
  for (int i=0; i<numRows; i++)
    {
    QTableWidgetItem *minItem = new QTableWidgetItem();
    minItem->setData(0, airwayNode->GetMin()->GetValue(i));
	  d->ReportTable->setItem(i,0,minItem);

    QTableWidgetItem *maxItem = new QTableWidgetItem();
    maxItem->setData(0, airwayNode->GetMax()->GetValue(i));
	  d->ReportTable->setItem(i,1,maxItem);

    QTableWidgetItem *meanItem = new QTableWidgetItem();
    meanItem->setData(0, airwayNode->GetMean()->GetValue(i));
	  d->ReportTable->setItem(i,2,meanItem);

    QTableWidgetItem *stdItem = new QTableWidgetItem();
    stdItem->setData(0, airwayNode->GetStd()->GetValue(i));
	  d->ReportTable->setItem(i,3,stdItem);
    }

  d->ReportTable->setMinimumHeight(420);
  //d->ReportTable->setMaximumHeight(1000);
  d->ReportTable->resizeColumnsToContents();
  d->ReportTable->resizeRowsToContents();

  //d->MinSpinBox->setValue(airwayNode->GetMin());
  //d->MaxSpinBox->setValue(airwayNode->GetMax());
  //d->MeanSpinBox->setValue(airwayNode->GetMean());
  //d->StdSpinBox->setValue(airwayNode->GetStd());
  if (d->WriteAirwaysCheckBox->isChecked())
  {
    this->saveAirwayImage(airwayNode);
  }
}

//-----------------------------------------------------------------------------
void qSlicerAirwayInspectorModuleWidget::updateViewer(vtkMRMLAirwayNode* airwayNode)
{
  Q_D(qSlicerAirwayInspectorModuleWidget);

  vtkSlicerAirwayInspectorModuleLogic *logic = vtkSlicerAirwayInspectorModuleLogic::SafeDownCast(this->logic());
  if (!logic || !airwayNode || !airwayNode->GetAirwayImage())
    {
    return;
    }

  vtkImageData *image= airwayNode->GetAirwayImage();

  vtkImageData *colorImage = vtkImageData::New();

  vtkImageData *viewImage = vtkImageData::New();

  this->createColorImage(image, colorImage);

  logic->AddEllipsesToImage(colorImage, airwayNode, viewImage);

  vtkImageFlip *flip = vtkImageFlip::New();
  flip->SetInputData(viewImage);
  flip->SetFilteredAxis(1);
  flip->Update();

  this->Renderer->RemoveAllViewProps();

  vtkSmartPointer<vtkImageMapper> imageMapper = vtkSmartPointer<vtkImageMapper>::New();

  imageMapper->SetInputData(flip->GetOutput());

  imageMapper->SetColorWindow(256);
  imageMapper->SetColorLevel(128);

  vtkSmartPointer<vtkActor2D> imageActor = vtkSmartPointer<vtkActor2D>::New();
  imageActor->SetMapper(imageMapper);

  //this-Renderer->AddViewProp(imageActor);
  this->Renderer->AddActor2D(imageActor);

  // add ellipse polydata
  if (airwayNode->GetEllipseInside() && airwayNode->GetEllipseInside()->GetInput())
    {
    vtkPolyData *poly = vtkPolyData::SafeDownCast(airwayNode->GetEllipseInside()->GetInput());
    vtkSmartPointer<vtkPolyDataMapper2D> polyMapper = vtkSmartPointer<vtkPolyDataMapper2D>::New();
    vtkSmartPointer<vtkActor2D> polyActor = vtkSmartPointer<vtkActor2D>::New();
    polyMapper->SetInputData(poly);
    polyActor->SetMapper(polyMapper);
    polyActor->GetProperty()->SetColor(1, 0.5, 0.05);
    this->Renderer->AddActor2D(polyActor);
    }

  if (airwayNode->GetEllipseOutside() && airwayNode->GetEllipseOutside()->GetInput())
    {
    vtkPolyData *poly = vtkPolyData::SafeDownCast(airwayNode->GetEllipseOutside()->GetInput());
    vtkSmartPointer<vtkPolyDataMapper2D> polyMapper = vtkSmartPointer<vtkPolyDataMapper2D>::New();
    vtkSmartPointer<vtkActor2D> polyActor = vtkSmartPointer<vtkActor2D>::New();
    polyMapper->SetInputData(poly);
    polyActor->SetMapper(polyMapper);
    this->Renderer->AddActor2D(polyActor);
    polyActor->GetProperty()->SetColor(0.99, 0.99, 0.05);
    }

  this->Renderer->Render();
  d->qvtkWidget->GetRenderWindow()->Render();

  flip->Delete();
  colorImage->Delete();
  viewImage->Delete();

    /***
 QPixmap imagePixmap;
 if (image)
    {
    QImage qImage;
    qMRMLUtils::vtkImageDataToQImage(image, qImage);
    imagePixmap = imagePixmap.fromImage(qImage);
    imagePixmap = imagePixmap.scaled(d->ImageLabel->size(), Qt::KeepAspectRatio, Qt::FastTransformation);

    // draw poliline
    QPainter painter;
    painter.begin(&imagePixmap);
    //painter.drawPolyline(points,count);
    painter.end();

    d->ImageLabel->setPixmap(imagePixmap);
    d->ImageLabel->show();
    }
    ***/
}

void qSlicerAirwayInspectorModuleWidget::createColorImage(vtkImageData *image,
                                                           vtkImageData *colorImage)
{
  vtkImageMapToColors *rgbFilter = vtkImageMapToColors::New();
  vtkLookupTable *lut = vtkLookupTable::New();

  rgbFilter->SetInputData(image);
  rgbFilter->SetOutputFormatToRGB();

  double *range = image->GetScalarRange();

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

void qSlicerAirwayInspectorModuleWidget::saveAirwayImage(vtkMRMLAirwayNode* airwayNode)
{
  Q_D(qSlicerAirwayInspectorModuleWidget);
  if (airwayNode == 0 || airwayNode->GetAirwayImage() == 0 ||
      d->OutputDirectoryButton->directory().toStdString().empty())
    {
    return;
    }

   char fileName[10*256];
   vtkPNGWriter *writer = vtkPNGWriter::New();
   sprintf(fileName,"%s/%s_%s.png", d->OutputDirectoryButton->directory().toStdString().c_str(),
                                    d->FilePrefixLineEdit->text().toStdString().c_str(), airwayNode->GetName());

   vtkImageCast *imgCast = vtkImageCast::New();
   imgCast->SetInputData(airwayNode->GetAirwayImage());
   imgCast->SetOutputScalarTypeToUnsignedChar();
   writer->SetInputData(imgCast->GetOutput());
   writer->SetFileName(fileName);

   imgCast->Update();
   writer->Write();

   imgCast->Delete();
   writer->Delete();
 }

//-----------------------------------------------------------------------------
void qSlicerAirwayInspectorModuleWidget::writeCSV()
{
  Q_D(qSlicerAirwayInspectorModuleWidget);
  if (!this->mrmlScene() )
    {
    return;
    }

  QString path = d->CSVFilePathEdit->currentPath();
  std::ofstream ofs(path.toStdString().c_str());
  if (ofs.fail())
    {
    std::cerr << "Output file doesn't exist: " <<  path.toStdString() << std::endl;
    return;
    }

  std::vector<vtkMRMLNode *> nodes;
  this->mrmlScene()->GetNodesByClass("vtkMRMLAirwayNode", nodes);

  for (int i=0; i<nodes.size(); i++)
    {
    vtkMRMLAirwayNode* node = vtkMRMLAirwayNode::SafeDownCast(nodes[i]);
    ofs << node->GetName() << "," << node->GetMethod() << ","
        << node->GetMean()->GetValue(0) << ","
        << node->GetStd()->GetValue(0) << ","
        << node->GetMin()->GetValue(0) << ","
        << node->GetMax()->GetValue(0) << "\n";
    }
  ofs.flush();
  ofs.close();
}

