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
#include <sstream>

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
#include <vtkNew.h>
#include <vtkPointData.h>
#include <vtkPolyData.h>

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

  connect( d->ParticlesScaleSlider, SIGNAL(valueChanged(double)),
	  this, SLOT( onScaleChanged(double) ) );

  connect( d->ParticlesSizeSlider, SIGNAL(valueChanged(double)),
	  this, SLOT( onSizeChanged(double) ) );

  d->ParticlesScaleSlider->setDecimals(1);
  d->ParticlesSizeSlider->setDecimals(1);

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

  this->updateParticlesDisplayNode();

  std::vector<std::string> scalars;
  this->getAvailableScalarNames(scalars);

  for (int i=0; i< scalars.size(); i++)
    {
    d->ColorComboBox->addItem(QString(scalars[i].c_str()));
    }

  std::vector<std::string> vectors;
  this->getAvailableScalarNames(vectors);

  d->RegionComboBox->setCurrentIndex(0);
  d->TypeComboBox->setCurrentIndex(0);
  if (scalars.size())
    {
    this->onColorByChanged(QString(scalars[0].c_str()));
    }
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
    d->OutputModelComboBox->setCurrentNode(0);
    return;
    }

  this->createParticlesDisplayNode(vtkMRMLModelNode::SafeDownCast(node));

   this->onColorByChanged(d->ColorComboBox->currentText());
}

//-----------------------------------------------------------------------------
void qSlicerParticlesDisplayModuleWidget::onGlyphTypeChanged(const QString & glyph)
{
  Q_D(qSlicerParticlesDisplayModuleWidget);
  vtkMRMLParticlesDisplayNode* particlesDisplayNode = this->getParticlesDisplayNode();
  if (particlesDisplayNode)
    {
    particlesDisplayNode->SetGlyphType(d->GlyphTypeComboBox->currentIndex());
    }
}

//-----------------------------------------------------------------------------
void qSlicerParticlesDisplayModuleWidget::onColorByChanged(const QString & color)
{
  Q_D(qSlicerParticlesDisplayModuleWidget);
  vtkMRMLParticlesDisplayNode* particlesDisplayNode = this->getParticlesDisplayNode();
  if (particlesDisplayNode)
    {
    particlesDisplayNode->SetParticlesColorBy(d->ColorComboBox->currentText().toStdString().c_str());
    }
}

//-----------------------------------------------------------------------------
void qSlicerParticlesDisplayModuleWidget::onTypeChanged(const QString & type)
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
void qSlicerParticlesDisplayModuleWidget::onScaleChanged(double value)
{
  Q_D(qSlicerParticlesDisplayModuleWidget);
  vtkMRMLParticlesDisplayNode* particlesDisplayNode = this->getParticlesDisplayNode();
  if (particlesDisplayNode)
    {
    particlesDisplayNode->SetScaleFactor(value);
    }
}

//-----------------------------------------------------------------------------
void qSlicerParticlesDisplayModuleWidget::onSizeChanged(double value)
{
  Q_D(qSlicerParticlesDisplayModuleWidget);
  vtkMRMLParticlesDisplayNode* particlesDisplayNode = this->getParticlesDisplayNode();
  if (particlesDisplayNode)
    {
    particlesDisplayNode->SetParticleSize(value);
    }
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
  vtkMRMLParticlesDisplayNode *particlesDisplayNode = vtkMRMLParticlesDisplayNode::SafeDownCast(
    particleNode->GetModelDisplayNode());

  particleNode->SetAndObservePolyData(modelNode->GetPolyData());

  vtkMRMLModelDisplayNode *dnode = modelNode->GetModelDisplayNode();

  dnode->SetVisibility(0);
  particlesDisplayNode->SetVisibility(1);
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

//-----------------------------------------------------------------------------
void qSlicerParticlesDisplayModuleWidget::getAvailableScalarNames(std::vector<std::string> &names)
{
  Q_D(qSlicerParticlesDisplayModuleWidget);

  names.clear();

  vtkMRMLModelNode *model = vtkMRMLModelNode::SafeDownCast(d->InputModelComboBox->currentNode());
  vtkPolyData *poly = 0;
  if (model)
    {
    poly = model->GetPolyData();
    }
  if (poly == 0 || poly->GetPointData() == 0)
    {
    return;
    }

  for (int i=0; i<poly->GetPointData()->GetNumberOfArrays(); i++)
    {
    if (poly->GetPointData()->GetArray(i)->GetNumberOfComponents() == 1)
      {
      if (poly->GetPointData()->GetArrayName(i))
        {
        names.push_back(std::string(poly->GetPointData()->GetArrayName(i)));
        }
      else
        {
        std::stringstream ss;
        ss << "Scalar " << i;
        names.push_back(ss.str());
        }
      }
    }
}
//-----------------------------------------------------------------------------
void qSlicerParticlesDisplayModuleWidget::getAvailableVectorNames(std::vector<std::string> &names)
{
  Q_D(qSlicerParticlesDisplayModuleWidget);

  names.clear();

  vtkMRMLModelNode *model = vtkMRMLModelNode::SafeDownCast(d->InputModelComboBox->currentNode());
  vtkPolyData *poly = 0;
  if (model)
    {
    poly = model->GetPolyData();
    }
  if (poly == 0 || poly->GetPointData() == 0)
    {
    return;
    }

  for (int i=0; i<poly->GetPointData()->GetNumberOfArrays(); i++)
    {
    if (poly->GetPointData()->GetArray(i)->GetNumberOfComponents() == 3)
      {
      if (poly->GetPointData()->GetArrayName(i))
        {
        names.push_back(std::string(poly->GetPointData()->GetArrayName(i)));
        }
      else
        {
        std::stringstream ss;
        ss << "Vector " << i;
        names.push_back(ss.str());
        }
      }
    }
}
