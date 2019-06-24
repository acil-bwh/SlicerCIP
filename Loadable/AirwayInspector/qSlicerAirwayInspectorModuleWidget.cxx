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
#include "vtkTeemNRRDWriter.h"
#include "vtkPNGWriter.h"
#include "vtkImageFlip.h"
#include "vtkImageCast.h"
#include "vtkReflectionFilter.h"
#include "vtkTransformPolyDataFilter.h"
#include "vtkTransform.h"
#include "qpainter.h"
#include "qmainwindow.h"
//#include "QVTKWidget.h"
#include "QVTKOpenGLWidget.h"

#include "vtkMRMLScene.h"
#include "vtkMRMLScalarVolumeNode.h"
#include "vtkMRMLScalarVolumeDisplayNode.h"
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

  QVTKOpenGLWidget *qvtkWidget;
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

  this->isUpdating = false;
  this->VolumeDisplayNode = 0;
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

  statsLabels = QString("Mean;Std;Min;Max").split(";");
  valuesLabels = QString("Inner Radius (mm);Outer Radius (mm);Wall Thickness (mm);" \
          "Wall Intensity (HU);WA%;Pi (mm);sqrt(WA) (mm);Ai (mm^2);Ao (mm^2);" \
          "Peak WI (HU);Inner WI (HU);Outer WI (HU);Vessel Intensity (HU);" \
           "RL Inner Diam (mm);RL Outer Diam (mm);AP Inner Diam (mm);AP Outer Diam (mm);" \
           "Lumen I (HU);Parenchyma I (HU);Energy;Power").split(";");

  d->ThresholdSpinBox->setRange(-1000, -300);
  d->ThresholdSpinBox->setValue(-850);
  // VTK/Qt
  d->qvtkWidget = new QVTKOpenGLWidget;
  d->qvtkWidget->GetRenderWindow()->AddRenderer(this->Renderer);
  d->qvtkWidget->setFixedSize(256,256);
  d->horizontalLayout->addWidget(d->qvtkWidget);

  d->ReportTable->setEditTriggers(QAbstractItemView::NoEditTriggers);
  d->ReportTable->setSizePolicy(QSizePolicy::Expanding,QSizePolicy::Expanding);
  d->ReportTable->setColumnCount(this->statsLabels.size());
  d->ReportTable->setVerticalHeaderLabels(this->valuesLabels);
	d->ReportTable->setHorizontalHeaderLabels(this->statsLabels);

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

  QObject::connect(d->ShowEllipsesCheckBox, SIGNAL(toggled(bool)),
                   this, SLOT(onDrawCahnged(bool)));

  QObject::connect(d->ShowPolylineCheckBox, SIGNAL(toggled(bool)),
                   this, SLOT(onDrawCahnged(bool)));
}

//-----------------------------------------------------------------------------
void qSlicerAirwayInspectorModuleWidget::setMRMLScene(vtkMRMLScene *newScene)
{
  Q_D(qSlicerAirwayInspectorModuleWidget);

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
      vtkMRMLSliceNode* snode = this->interactors[interactor];
      vtkMatrix4x4 *xyToRAS = snode->GetXYToRAS();
      double xyz[4];
      xyz[0] = x;
      xyz[1] = y;
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
  Q_UNUSED(mrmlNode);
  Q_D(qSlicerAirwayInspectorModuleWidget);

  vtkMRMLScalarVolumeNode* volumeNode = vtkMRMLScalarVolumeNode::SafeDownCast(
    d->InputVolumeComboBox->currentNode());

  vtkSlicerAirwayInspectorModuleLogic *airwayLogic = vtkSlicerAirwayInspectorModuleLogic::SafeDownCast(this->logic());
  if (airwayLogic && volumeNode)
    {
    vtkMRMLScalarVolumeDisplayNode *dnode = vtkMRMLScalarVolumeDisplayNode::SafeDownCast(volumeNode->GetDisplayNode());
    vtkMRMLAirwayNode* airwayNode = vtkMRMLAirwayNode::SafeDownCast(
                                                d->AirwayComboBox->currentNode());

    // each time the node is modified, the qt widgets are updated
    this->qvtkReconnect(this->VolumeDisplayNode, dnode, vtkCommand::ModifiedEvent,
                      this, SLOT(onWindowLevelChanged()));

    this->VolumeDisplayNode = dnode;

    this->updateViewer(airwayNode);
    }
}

//-----------------------------------------------------------------------------
void qSlicerAirwayInspectorModuleWidget::setMRMLAirwayNode(vtkMRMLNode* mrmlNode)
{
  Q_UNUSED(mrmlNode);
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
void qSlicerAirwayInspectorModuleWidget::onDrawCahnged(bool)
{
  Q_D(qSlicerAirwayInspectorModuleWidget);

  vtkMRMLAirwayNode *airwayNode = vtkMRMLAirwayNode::SafeDownCast(d->AirwayComboBox->currentNode());
  this->updateViewer(airwayNode);
}

//-----------------------------------------------------------------------------
void qSlicerAirwayInspectorModuleWidget::onWindowLevelChanged()
{
  Q_D(qSlicerAirwayInspectorModuleWidget);

  vtkMRMLAirwayNode *airwayNode = vtkMRMLAirwayNode::SafeDownCast(d->AirwayComboBox->currentNode());
  this->updateViewer(airwayNode);
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
  Q_D(qSlicerAirwayInspectorModuleWidget);

  vtkMRMLAirwayNode *airwayNode = vtkMRMLAirwayNode::SafeDownCast(d->AirwayComboBox->currentNode());

  this->updateAirwaySlice();
  this->updateReport(airwayNode);
}

//-----------------------------------------------------------------------------
void qSlicerAirwayInspectorModuleWidget::updateWidgetFromMRML(vtkMRMLAirwayNode* airwayNode)
{
  if (this->isUpdating)
    {
    return;
    }
  this->isUpdating = true;

  Q_D(qSlicerAirwayInspectorModuleWidget);

  if (airwayNode)
    {
    d->RefineCenterCheckBox->setChecked(airwayNode->GetRefineCenter());
    d->ComputeCenterCheckBox->setChecked(airwayNode->GetComputeCenter());
    d->ThresholdSpinBox->setValue(airwayNode->GetThreshold());
    d->MethodComboBox->setCurrentIndex(airwayNode->GetMethod());
    d->ReformatCheckBox->setChecked(airwayNode->GetReformat());
    }
  this->isUpdating = false;
}

//-----------------------------------------------------------------------------
void qSlicerAirwayInspectorModuleWidget::updateMRMLFromWidget(vtkMRMLAirwayNode* airwayNode)
{
  if (this->isUpdating)
    {
    return;
    }
  this->isUpdating = true;

  Q_D(qSlicerAirwayInspectorModuleWidget);

  if (airwayNode)
    {
    airwayNode->SetComputeCenter(d->ComputeCenterCheckBox->isChecked());
    airwayNode->SetRefineCenter(d->RefineCenterCheckBox->isChecked());
    airwayNode->SetThreshold(d->ThresholdSpinBox->value());
    airwayNode->SetMethod(d->MethodComboBox->currentIndex());
    airwayNode->SetReformat(d->ReformatCheckBox->isChecked());
    }
  this->isUpdating = false;
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

    if (d->ComputeAllMethodsCheckBox->isChecked())
      {
      for (int method=0; method < 4; method++)
        {
        airwayLogic->ComputeAirwayWall(airwayNode->GetAirwayImage(), airwayNode, method);
        }
      }
    airwayLogic->ComputeAirwayWall(airwayNode->GetAirwayImage(), airwayNode, airwayNode->GetMethod());
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

  for (size_t i=0; i<nodes.size(); i++)
    {
    vtkMRMLAirwayNode* airwayNode = vtkMRMLAirwayNode::SafeDownCast(nodes[i]);

    this->updateMRMLFromWidget(airwayNode);

    if (d->ComputeAllMethodsCheckBox->isChecked())
      {
      for (int method=0; method < 4; method++)
        {
        airwayLogic->ComputeAirwayWall(airwayNode->GetAirwayImage(), airwayNode, method);
        }
      }

    airwayLogic->ComputeAirwayWall(airwayNode->GetAirwayImage(), airwayNode, airwayNode->GetMethod());

    if (d->WriteAirwaysCheckBox->isChecked())
      {
      this->saveAirwayImage(airwayNode);
      }
    }

  vtkMRMLAirwayNode* airwayNode = vtkMRMLAirwayNode::SafeDownCast(
    d->AirwayComboBox->currentNode());

  airwayLogic->ComputeAirwayWall(airwayNode->GetAirwayImage(), airwayNode, airwayNode->GetMethod());

  this->updateReport(airwayNode);

  this->updateViewer(airwayNode);
}

//-----------------------------------------------------------------------------
void qSlicerAirwayInspectorModuleWidget::updateReport(vtkMRMLAirwayNode* airwayNode)
{
  Q_D(qSlicerAirwayInspectorModuleWidget);
  if (airwayNode == 0)
    {
    d->ReportTable->clear();
    return;
    }

  // report the results
  d->ReportTable->setSizePolicy(QSizePolicy::Expanding,QSizePolicy::Expanding);

  if (airwayNode->GetMin(airwayNode->GetMethod()) == 0 ||
      airwayNode->GetMax(airwayNode->GetMethod()) == 0 ||
      airwayNode->GetMean(airwayNode->GetMethod()) == 0 ||
      airwayNode->GetStd(airwayNode->GetMethod()) == 0 ||
      airwayNode->GetMin(airwayNode->GetMethod())->GetNumberOfTuples() == 0 ||
      airwayNode->GetMax(airwayNode->GetMethod())->GetNumberOfTuples() == 0 ||
      airwayNode->GetMean(airwayNode->GetMethod())->GetNumberOfTuples() == 0 ||
      airwayNode->GetStd(airwayNode->GetMethod())->GetNumberOfTuples() == 0)
  {
    return;
  }
  int numRows = airwayNode->GetMin(airwayNode->GetMethod())->GetNumberOfComponents();
  numRows = numRows < airwayNode->GetMax(airwayNode->GetMethod())->GetNumberOfComponents() ? numRows : airwayNode->GetMax(airwayNode->GetMethod())->GetNumberOfComponents();
  numRows = numRows < airwayNode->GetMean(airwayNode->GetMethod())->GetNumberOfComponents() ? numRows : airwayNode->GetMean(airwayNode->GetMethod())->GetNumberOfComponents();
  numRows = numRows < airwayNode->GetStd(airwayNode->GetMethod())->GetNumberOfComponents() ? numRows : airwayNode->GetStd(airwayNode->GetMethod())->GetNumberOfComponents();

  d->ReportTable->setRowCount(numRows);
  d->ReportTable->setVerticalHeaderLabels(this->valuesLabels);
	d->ReportTable->setHorizontalHeaderLabels(this->statsLabels);

	//Add Table items here
  for (int i=0; i<numRows; i++)
    {
    QTableWidgetItem *meanItem = new QTableWidgetItem();
    meanItem->setData(0, airwayNode->GetMean(airwayNode->GetMethod())->GetValue(i));
    d->ReportTable->setItem(i,0,meanItem);

    QTableWidgetItem *stdItem = new QTableWidgetItem();
    stdItem->setData(0, airwayNode->GetStd(airwayNode->GetMethod())->GetValue(i));
    d->ReportTable->setItem(i,1,stdItem);

    QTableWidgetItem *minItem = new QTableWidgetItem();
    minItem->setData(0, airwayNode->GetMin(airwayNode->GetMethod())->GetValue(i));
	  d->ReportTable->setItem(i,2,minItem);

    QTableWidgetItem *maxItem = new QTableWidgetItem();
    maxItem->setData(0, airwayNode->GetMax(airwayNode->GetMethod())->GetValue(i));
	  d->ReportTable->setItem(i,3,maxItem);

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

  this->Renderer->RemoveAllViewProps();

  vtkSlicerAirwayInspectorModuleLogic *logic = vtkSlicerAirwayInspectorModuleLogic::SafeDownCast(this->logic());

  if (!logic || !airwayNode || !airwayNode->GetAirwayImage())
    {
    this->Renderer->Render();
    d->qvtkWidget->GetRenderWindow()->Render();
    return;
    }

  vtkImageData *image= airwayNode->GetAirwayImage();

  vtkImageData *colorImage = vtkImageData::New();

  vtkImageData *viewImage = vtkImageData::New();

  this->createColorImage(image, colorImage);

  if (d->ShowEllipsesCheckBox->isChecked())
    {
    logic->AddEllipsesToImage(colorImage, airwayNode, viewImage);
    }
  else
    {
    viewImage->DeepCopy(colorImage);
    }

  vtkImageFlip *flip = vtkImageFlip::New();
  flip->SetInputData(viewImage);
  flip->SetFilteredAxis(1);
  flip->Update();

  vtkSmartPointer<vtkImageMapper> imageMapper = vtkSmartPointer<vtkImageMapper>::New();

  imageMapper->SetInputData(flip->GetOutput());

  // DEBUG:
  //this->saveAirwayImage(airwayNode, "C:\\tmp\\flip.png", flip->GetOutput());

  // get windowlevel from the input volume
  double colorWindow = 256;
  double colorLevel = 128;
  vtkMRMLVolumeNode *vnode = vtkMRMLVolumeNode::SafeDownCast(
    this->mrmlScene()->GetNodeByID(airwayNode->GetVolumeNodeID()));
  if (vnode)
    {
    double *range = vnode->GetImageData()->GetScalarRange();
    vtkMRMLScalarVolumeDisplayNode *dnode = vtkMRMLScalarVolumeDisplayNode::SafeDownCast(vnode->GetDisplayNode());
    if (dnode)
      {
      colorWindow = dnode->GetWindow();
      colorLevel = dnode->GetLevel();
      double scale = 256/(range[1] - range[0]);
      colorLevel = scale*(colorLevel - range[0]);
      colorWindow = scale * colorWindow;
      }
    }
  imageMapper->SetColorWindow(colorWindow);
  imageMapper->SetColorLevel(colorLevel);

  vtkSmartPointer<vtkActor2D> imageActor = vtkSmartPointer<vtkActor2D>::New();
  imageActor->SetMapper(imageMapper);

  //this-Renderer->AddViewProp(imageActor);
  this->Renderer->AddActor2D(imageActor);

  // add ellipse polydata
  if (d->ShowPolylineCheckBox->isChecked())
    {
    int *ext = viewImage->GetExtent();
    if (airwayNode->GetEllipseInside(airwayNode->GetMethod()) && airwayNode->GetEllipseInside(airwayNode->GetMethod())->GetInput())
      {
      vtkPolyData *poly = vtkPolyData::SafeDownCast(airwayNode->GetEllipseInside(airwayNode->GetMethod())->GetInput());
      vtkPolyData *polyFlipped = vtkPolyData::New();
      polyFlipped->DeepCopy(poly);
      this->flipPolyData(polyFlipped, (ext[3]-ext[2]));

      vtkSmartPointer<vtkPolyDataMapper2D> polyMapper = vtkSmartPointer<vtkPolyDataMapper2D>::New();
      vtkSmartPointer<vtkActor2D> polyActor = vtkSmartPointer<vtkActor2D>::New();
      polyMapper->SetInputData(polyFlipped);
      polyActor->SetMapper(polyMapper);
      polyActor->GetProperty()->SetColor(1, 0.5, 0.05);
      this->Renderer->AddActor2D(polyActor);
      }

    if (airwayNode->GetEllipseOutside(airwayNode->GetMethod()) && airwayNode->GetEllipseOutside(airwayNode->GetMethod())->GetInput())
      {
      vtkPolyData *poly = vtkPolyData::SafeDownCast(airwayNode->GetEllipseOutside(airwayNode->GetMethod())->GetInput());
      vtkPolyData *polyFlipped = vtkPolyData::New();
      polyFlipped->DeepCopy(poly);
      this->flipPolyData(polyFlipped, (ext[3]-ext[2]));

      vtkSmartPointer<vtkPolyDataMapper2D> polyMapper = vtkSmartPointer<vtkPolyDataMapper2D>::New();
      vtkSmartPointer<vtkActor2D> polyActor = vtkSmartPointer<vtkActor2D>::New();
      polyMapper->SetInputData(polyFlipped);
      polyActor->SetMapper(polyMapper);
      polyActor->GetProperty()->SetColor(0.99, 0.99, 0.05);
      this->Renderer->AddActor2D(polyActor);
      }
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

void qSlicerAirwayInspectorModuleWidget::flipPolyData(vtkPolyData *poly, double shift)
{
  vtkIdType numPts = poly->GetNumberOfPoints();
  double point[3];
  vtkPoints *points = vtkPoints::New();
  for (vtkIdType i = 0; i < numPts; i++)
    {
    poly->GetPoint(i, point);
    point[1] = -point[1] + shift;
    points->InsertNextPoint(point);
    }
  poly->SetPoints(points);
  points->Delete();
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
  //lut->SetTableRange(-1000, -500);
  lut->Build();
  rgbFilter->SetLookupTable(lut);

  rgbFilter->Update();

  vtkImageData *rgbImage=rgbFilter->GetOutput();

  colorImage->DeepCopy(rgbImage);
  colorImage->SetOrigin(image->GetOrigin());
  colorImage->SetSpacing(image->GetSpacing());

  lut->Delete();
  rgbFilter->Delete();
}

void qSlicerAirwayInspectorModuleWidget::saveAirwayImage(vtkMRMLAirwayNode* airwayNode, char *name, vtkImageData *img)
{
  Q_D(qSlicerAirwayInspectorModuleWidget);
  if (airwayNode == 0 || airwayNode->GetAirwayImage() == 0 ||
      d->OutputDirectoryButton->directory().toStdString().empty())
    {
    return;
    }

  char fileName[10*256];
  vtkPNGWriter *writer = vtkPNGWriter::New();
  if (name)
  {
  sprintf(fileName,"%s", name);
  }
  else
   {
   sprintf(fileName,"%s/%s_%s.png", d->OutputDirectoryButton->directory().toStdString().c_str(),
                                    d->FilePrefixLineEdit->text().toStdString().c_str(), airwayNode->GetName());
   }

  if (img == 0)
  {
  img = airwayNode->GetAirwayImage();
  }

  vtkImageData *colorImage = vtkImageData::New();

  this->createColorImage(img, colorImage);

  vtkImageFlip *flip = vtkImageFlip::New();
  flip->SetInputData(colorImage);
  flip->SetFilteredAxis(1);
  flip->Update();

  vtkImageCast *imgCast = vtkImageCast::New();
  imgCast->SetInputData(flip->GetOutput());
  imgCast->SetOutputScalarTypeToUnsignedChar();
  writer->SetInputData(imgCast->GetOutput());
  writer->SetFileName(fileName);

  imgCast->Update();
  writer->Write();

  colorImage->Delete();
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

  // header
  ofs << "airway_id, method";
  for (int n=0; n<this->valuesLabels.size(); n++)
    {
    std::string valueLabel = this->valuesLabels.at(n).toStdString();
    for (int m=0; m<this->statsLabels.size(); m++)
      {
      ofs << "," << valueLabel << "_" << this->statsLabels.at(m).toStdString();
      }
    }
  ofs << "\n";

  std::vector<vtkMRMLNode *> nodes;
  this->mrmlScene()->GetNodesByClass("vtkMRMLAirwayNode", nodes);

  for (size_t i=0; i<nodes.size(); i++)
    {
    vtkMRMLAirwayNode* node = vtkMRMLAirwayNode::SafeDownCast(nodes[i]);
    std::map<int, vtkDoubleArray*>::iterator it;
    for (int method=0; method < 4; method++)
      {
      if (node->GetMean(method))
        {
        ofs << node->GetName() << "," << method;
        int numVals = node->GetMean(method)->GetNumberOfComponents();
        if (numVals != this->valuesLabels.size())
          {
          std::cerr << "Incorrect number of computed components. Table is misformed\n";
          return;
          }
        for (int n=0; n<numVals; n++)
          {
          ofs << ","
              << node->GetMean(method)->GetValue(n) << ","
              << node->GetStd(method)->GetValue(n) << ","
              << node->GetMin(method)->GetValue(n) << ","
              << node->GetMax(method)->GetValue(n);
          }
        ofs << "\n";
        }
      }
    }
  ofs.flush();
  ofs.close();
}

