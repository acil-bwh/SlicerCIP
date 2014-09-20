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

// Qt includes
#include <QDebug>
#include <QString>
#include <QByteArray>

// CTK includes
#include <ctkFlowLayout.h>

// SlicerQt includes
#include "qSlicerParticlesDisplayModuleWidget.h"
#include "ui_qSlicerParticlesDisplayModuleWidget.h"

#include <vtkSlicerParticlesDisplayLogic.h>
#include <vtkMRMLScene.h>
#include <vtkMRMLModelNode.h>
#include <vtkMRMLModelDisplayNode.h>
#include <vtkMRMLParticlesDisplayNode.h>

#include <cipChestConventions.h>

#include <vtkMatrix4x4.h>
#include <vtkSmartPointer.h>
#include <vtkImageData.h>
#include <vtkNew.h>
#include <vtkImageThreshold.h>

//-----------------------------------------------------------------------------
/// \ingroup Slicer_QtModules_ExtensionTemplate
class qSlicerParticlesDisplayModuleWidgetPrivate: public Ui_qSlicerParticlesDisplayModuleWidget
{
  Q_DECLARE_PUBLIC(qSlicerParticlesDisplayModuleWidget);
protected:
  qSlicerParticlesDisplayModuleWidget* const q_ptr;
public:

  qSlicerParticlesDisplayModuleWidgetPrivate(qSlicerParticlesDisplayModuleWidget& object);
  ~qSlicerParticlesDisplayModuleWidgetPrivate();

  vtkSlicerParticlesDisplayLogic* logic() const;
};

//-----------------------------------------------------------------------------
// qSlicerParticlesDisplayModuleWidgetPrivate methods

//-----------------------------------------------------------------------------
qSlicerParticlesDisplayModuleWidgetPrivate::qSlicerParticlesDisplayModuleWidgetPrivate(qSlicerParticlesDisplayModuleWidget& object) : q_ptr(&object)
{
}

//-----------------------------------------------------------------------------
qSlicerParticlesDisplayModuleWidgetPrivate::~qSlicerParticlesDisplayModuleWidgetPrivate()
{
}

//-----------------------------------------------------------------------------
vtkSlicerParticlesDisplayLogic* qSlicerParticlesDisplayModuleWidgetPrivate::logic() const
{
  Q_Q(const qSlicerParticlesDisplayModuleWidget);
  return vtkSlicerParticlesDisplayLogic::SafeDownCast(q->logic());
}

//-----------------------------------------------------------------------------
// qSlicerParticlesDisplayModuleWidget methods

//-----------------------------------------------------------------------------
qSlicerParticlesDisplayModuleWidget::qSlicerParticlesDisplayModuleWidget(QWidget* _parent)
  : Superclass( _parent )
  , d_ptr( new qSlicerParticlesDisplayModuleWidgetPrivate(*this) )
{
}

//-----------------------------------------------------------------------------
qSlicerParticlesDisplayModuleWidget::~qSlicerParticlesDisplayModuleWidget()
{
}

//-----------------------------------------------------------------------------
void qSlicerParticlesDisplayModuleWidget::setup()
{
  Q_D(qSlicerParticlesDisplayModuleWidget);
  d->setupUi(this);

  //ctkFlowLayout* flowLayout = ctkFlowLayout::replaceLayout(d->InterpolatorWidget);
  //flowLayout->setPreferredExpandingDirections(Qt::Vertical);

  this->Superclass::setup();

  connect( d->InputModelComboBox, SIGNAL( currentNodeChanged(vtkMRMLNode*) ),
	  this, SLOT( onInputChanged(vtkMRMLNode*) ) );

  connect( d->OutputModelComboBox, SIGNAL( currentNodeChanged(vtkMRMLNode*) ),
	  this, SLOT( onOutputChanged(vtkMRMLNode*) ) );

  connect( d->RegionComboBox, SIGNAL( currentIndexChanged(const QString &) ),
	  this, SLOT( onRegionChanged(const QString &) ) );

  connect( d->TypeComboBox, SIGNAL( currentIndexChanged(const QString &) ),
	  this, SLOT( onTypeChanged(const QString &) ) );

  connect( d->GlyphTypeComboBox, SIGNAL( currentIndexChanged(const QString &) ),
	  this, SLOT( onGlyphTypeChanged(const QString &) ) );

  connect( d->ColorComboBox, SIGNAL( currentIndexChanged(const QString &) ),
	  this, SLOT( onColorByChanged(const QString &) ) );

  connect( d->ParticlesScaleSlider, SIGNAL( valueChanged(int) ),
	  this, SLOT( onScaleChanged(int) ) );

  d->TypeComboBox->addItem("Airway");
  d->TypeComboBox->addItem("Vessels");
  d->TypeComboBox->addItem("Fissures");
}

//-----------------------------------------------------------------------------
void qSlicerParticlesDisplayModuleWidget::onInputChanged(vtkMRMLNode* node)
{
  Q_D(qSlicerParticlesDisplayModuleWidget);
  Q_ASSERT(d->InputModelComboBox);

  if( node == 0)
    {
    return;
    }

  d->RegionComboBox->setCurrentIndex(0);
  d->TypeComboBox->setCurrentIndex(0);
  this->updateParticlesDisplayNode();
}

//-----------------------------------------------------------------------------
void qSlicerParticlesDisplayModuleWidget::onOutputChanged(vtkMRMLNode* node)
{
  Q_D(qSlicerParticlesDisplayModuleWidget);
  Q_ASSERT(d->OutputModelComboBox);

  if( node == 0)
    {
    return;
    }

 // do not overwrite the input node
  if (node == d->InputModelComboBox->currentNode())
    {
    //d->OutputModelComboBox->setCurrentNode(0);
    //return;
    }

  this->createParticlesDisplayNode(vtkMRMLModelNode::SafeDownCast(node));
}

//-----------------------------------------------------------------------------
void qSlicerParticlesDisplayModuleWidget::onGlyphTypeChanged(const QString & regionName)
{
  Q_D(qSlicerParticlesDisplayModuleWidget);
}

//-----------------------------------------------------------------------------
void qSlicerParticlesDisplayModuleWidget::onColorByChanged(const QString & regionName)
{
  Q_D(qSlicerParticlesDisplayModuleWidget);
}

//-----------------------------------------------------------------------------
void qSlicerParticlesDisplayModuleWidget::onTypeChanged(const QString & regionName)
{
  Q_D(qSlicerParticlesDisplayModuleWidget);
  vtkMRMLParticlesDisplayNode* particlesDisplayNode = this->getParticlesDisplayNode();
  if (particlesDisplayNode)
    {
    particlesDisplayNode->SetParticlesType(d->TypeComboBox->currentIndex());
    }
}

//-----------------------------------------------------------------------------
void qSlicerParticlesDisplayModuleWidget::onRegionChanged(const QString & regionName)
{
  Q_D(qSlicerParticlesDisplayModuleWidget);
}

//-----------------------------------------------------------------------------
void qSlicerParticlesDisplayModuleWidget::onScaleChanged(int value)
{
  Q_D(qSlicerParticlesDisplayModuleWidget);
}

//-----------------------------------------------------------------------------
void qSlicerParticlesDisplayModuleWidget::createParticlesDisplayNode(vtkMRMLModelNode* modelNode)
{
  if (modelNode == 0)
    {
    return;
    }

  vtkMRMLModelDisplayNode *dnode = modelNode->GetModelDisplayNode();

  if (dnode && dnode->IsA("vtkMRMLParticlesDisplayNode"))
  {
    this->updateParticlesDisplayNode();
    return;
  }

  vtkMRMLScene *scene = modelNode->GetScene();

  vtkMRMLParticlesDisplayNode *particlesDisplayNode = vtkMRMLParticlesDisplayNode::New();

  if (dnode)
    {
	  particlesDisplayNode->CopyWithScene(dnode);
    }

  std::string name;
  if (modelNode->GetName())
    {
    name = std::string(modelNode->GetName());
    }
  name += "_ParticlesDisplay";
	particlesDisplayNode->SetName( name.c_str() );
  scene->AddNode(particlesDisplayNode);
  particlesDisplayNode->Delete();

  modelNode->SetAndObserveDisplayNodeID(particlesDisplayNode->GetID());

  this->updateParticlesDisplayNode();
}

//-----------------------------------------------------------------------------
void qSlicerParticlesDisplayModuleWidget::updateParticlesDisplayNode()
{
  Q_D(qSlicerParticlesDisplayModuleWidget);

  vtkMRMLModelNode *modelNode = vtkMRMLModelNode::SafeDownCast(d->InputModelComboBox->currentNode());
  vtkMRMLModelNode *particleNode = vtkMRMLModelNode::SafeDownCast(d->OutputModelComboBox->currentNode());
  if (modelNode == 0 || particleNode == 0 )
    {
    return;
    }
  particleNode->CopyWithSceneWithSingleModifiedEvent(modelNode);

  vtkMRMLModelDisplayNode *dnode = modelNode->GetModelDisplayNode();
  vtkMRMLParticlesDisplayNode *particlesDisplayNode = vtkMRMLParticlesDisplayNode::SafeDownCast(
    particleNode->GetModelDisplayNode());

  if (dnode == 0 || particlesDisplayNode == 0)
    {
    return;
    }
	particlesDisplayNode->CopyWithScene(dnode);
}

//-----------------------------------------------------------------------------
vtkMRMLParticlesDisplayNode* qSlicerParticlesDisplayModuleWidget::getParticlesDisplayNode()
{
  Q_D(qSlicerParticlesDisplayModuleWidget);

  vtkMRMLParticlesDisplayNode *particlesDisplayNode = 0;

  vtkMRMLModelNode *particleNode = vtkMRMLModelNode::SafeDownCast(d->OutputModelComboBox->currentNode());
  if (particleNode)
    {
    particlesDisplayNode = vtkMRMLParticlesDisplayNode::SafeDownCast(
                            particleNode->GetModelDisplayNode());
    }
  return particlesDisplayNode;
}
