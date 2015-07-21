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
#include "vtkImageMapToColors.h"
#include "vtkImageMapper.h"
#include "vtkLookupTable.h"
#include "vtkMatrix4x4.h"

#include "QPainter.h"
#include "QMainWindow.h"
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
}

//-----------------------------------------------------------------------------
qSlicerAirwayInspectorModuleWidget::~qSlicerAirwayInspectorModuleWidget()
{
  // Remove observers
  this->removeInteractorObservers();
}
//-----------------------------------------------------------------------------
void qSlicerAirwayInspectorModuleWidget::setup()
{
  Q_D(qSlicerAirwayInspectorModuleWidget);
  d->setupUi(this);

  // VTK/Qt
  vtkSmartPointer<vtkRenderer> renderer =
    vtkSmartPointer<vtkRenderer>::New();
  d->qvtkWidget = new QVTKWidget;
  d->qvtkWidget->GetRenderWindow()->AddRenderer(renderer);
  d->qvtkWidget->setFixedSize(200,200);
  d->reportCollapsibleButton->layout()->addWidget(d->qvtkWidget);

  QObject::connect(d->InputVolumeComboBox, SIGNAL(currentNodeChanged(vtkMRMLNode*)),
                   this, SLOT(setMRMLVolumeNode(vtkMRMLNode*)));

  QObject::connect(d->AirwayComboBox, SIGNAL(currentNodeChanged(vtkMRMLNode*)),
                   this, SLOT(setMRMLAirwayNode(vtkMRMLNode*)));
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
        logic->AddAirwayNode(d->InputVolumeComboBox->currentNode()->GetID(),
        x,y,z, d->ThresholdSpinBox->value());

      d->AirwayComboBox->setCurrentNode(airwayNode);
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

  vtkSlicerAirwayInspectorModuleLogic *airwayLogic = vtkSlicerAirwayInspectorModuleLogic::SafeDownCast(this->logic());
  if (airwayLogic && airwayNode)
    {
    airwayLogic->CreateAirway(airwayNode);
    }

  this->updateReport(airwayNode);
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
  d->MinSpinBox->setValue(airwayNode->GetMin());
  d->MaxSpinBox->setValue(airwayNode->GetMax());
  d->MeanSpinBox->setValue(airwayNode->GetMean());
  d->StdSpinBox->setValue(airwayNode->GetStd());

  vtkImageData *image= airwayNode->GetAirwayImage();

  vtkRenderer *renderer= d->qvtkWidget->GetRenderWindow()->GetRenderers()->GetFirstRenderer();

  renderer->RemoveAllViewProps();

  vtkSmartPointer<vtkImageMapper> imageMapper = vtkSmartPointer<vtkImageMapper>::New();

  imageMapper->SetInputData(image);

  imageMapper->SetColorWindow(255);
  imageMapper->SetColorLevel(127.5);

  vtkSmartPointer<vtkActor2D> imageActor = vtkSmartPointer<vtkActor2D>::New();
  imageActor->SetMapper(imageMapper);

  //renderer->AddViewProp(imageActor);
  renderer->AddActor2D(imageActor);
  //renderer->Render();
  d->qvtkWidget->GetRenderWindow()->Render();

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