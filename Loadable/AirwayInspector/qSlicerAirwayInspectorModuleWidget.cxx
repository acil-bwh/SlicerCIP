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
#include "vtkInteractorObserver.h"

#include "vtkMRMLScene.h"
#include "vtkMRMLScalarVolumeNode.h"
#include "vtkMRMLAirwayNode.h"
#include "vtkMRMLSliceNode.h"

#include "qSlicerApplication.h"
#include "qSlicerLayoutManager.h"
#include "qMRMLSliceWidget.h"
#include "qMRMLSliceView.h"

#include "vtkSlicerAirwayInspectorModuleLogic.h"
//-----------------------------------------------------------------------------
/// \ingroup Slicer_QtModules_AirwayInspector
class qSlicerAirwayInspectorModuleWidgetPrivate: public Ui_qSlicerAirwayInspectorModuleWidget
{
public:
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
  std::cout << "OnInteractorEvent - eventid:" << eventid
             << ", eventname:" << vtkCommand::GetStringFromEventId(eventid) << std::endl;

  vtkSlicerAirwayInspectorModuleLogic *logic = vtkSlicerAirwayInspectorModuleLogic::SafeDownCast(this->logic());
  if (!logic)
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
      }
      vtkMRMLSliceNode* snode = this->interactors[interactor];
      assert(snode);
      //vtkMRMLSliceNode::GetSliceOffset()
      double z = snode->GetSliceOffset();
      logic->AddAirwayNode(x,y,z);
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
    airwayLogic->SetVolumeNodeID(volumeNode->GetID());
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
    //airwayLogic->Compute();
    }
}
