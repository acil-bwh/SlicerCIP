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
#include "qSlicerRegionTypeModuleWidget.h"
#include "ui_qSlicerRegionTypeModuleWidget.h"

#include <vtkSlicerRegionTypeLogic.h>
#include <vtkMRMLColorTableNode.h>
#include <vtkMRMLScene.h>
#include <vtkMRMLSelectionNode.h>
#include <vtkMRMLRegionTypeNode.h>
#include <vtkMRMLRegionTypeDisplayNode.h>
#include <vtkMRMLLabelMapVolumeNode.h>
#include <vtkMRMLStorageNode.h>
#include <vtkMRMLLabelMapVolumeDisplayNode.h>

#include <vtkMRMLVolumeNode.h>

#include <cipChestConventions.h>

#include <vtkMatrix4x4.h>
#include <vtkSmartPointer.h>
#include <vtkImageData.h>
#include <vtkLookupTable.h>
#include <vtkNew.h>
#include <vtkImageThreshold.h>

//-----------------------------------------------------------------------------
/// \ingroup Slicer_QtModules_ExtensionTemplate
class qSlicerRegionTypeModuleWidgetPrivate: public Ui_qSlicerRegionTypeModuleWidget
{
  Q_DECLARE_PUBLIC(qSlicerRegionTypeModuleWidget);
protected:
  qSlicerRegionTypeModuleWidget* const q_ptr;
public:

  qSlicerRegionTypeModuleWidgetPrivate(qSlicerRegionTypeModuleWidget& object);
  ~qSlicerRegionTypeModuleWidgetPrivate();

  vtkSlicerRegionTypeLogic* logic() const;
};

//-----------------------------------------------------------------------------
// qSlicerRegionTypeModuleWidgetPrivate methods

//-----------------------------------------------------------------------------
qSlicerRegionTypeModuleWidgetPrivate::qSlicerRegionTypeModuleWidgetPrivate(qSlicerRegionTypeModuleWidget& object) : q_ptr(&object)
{
}

//-----------------------------------------------------------------------------
qSlicerRegionTypeModuleWidgetPrivate::~qSlicerRegionTypeModuleWidgetPrivate()
{
}

//-----------------------------------------------------------------------------
vtkSlicerRegionTypeLogic* qSlicerRegionTypeModuleWidgetPrivate::logic() const
{
  Q_Q(const qSlicerRegionTypeModuleWidget);
  return vtkSlicerRegionTypeLogic::SafeDownCast(q->logic());
}

//-----------------------------------------------------------------------------
// qSlicerRegionTypeModuleWidget methods

//-----------------------------------------------------------------------------
qSlicerRegionTypeModuleWidget::qSlicerRegionTypeModuleWidget(QWidget* _parent)
  : Superclass( _parent )
  , d_ptr( new qSlicerRegionTypeModuleWidgetPrivate(*this) )
{
  this->regionTypeNode = NULL;
}

//-----------------------------------------------------------------------------
qSlicerRegionTypeModuleWidget::~qSlicerRegionTypeModuleWidget()
{
}

//-----------------------------------------------------------------------------
void qSlicerRegionTypeModuleWidget::setup()
{
  Q_D(qSlicerRegionTypeModuleWidget);
  d->setupUi(this);

//  Load a colormap from a file that contains all the possible combinations
//  qSlicerModuleManager * moduleManager = qSlicerCoreApplication::application()->moduleManager();
//  qSlicerAbstractCoreModule *colorsModule = moduleManager->module("Colors");
//  vtkMRMLColorLogic *colorsLogic = vtkMRMLColorLogic::SafeDownCast(colorsModule->logic());
//  QString name = QString("/Applications/SlicerCIP.app/Contents/share/Slicer-4.7/ColorFiles/CIPColors.txt");
//  vtkMRMLColorNode* colorNode = colorsLogic->LoadColorFile(name.toLatin1());
//  colorNode->SetName("CIP_ColorMap");

  //ctkFlowLayout* flowLayout = ctkFlowLayout::replaceLayout(d->InterpolatorWidget);
  //flowLayout->setPreferredExpandingDirections(Qt::Vertical);

  this->Superclass::setup();

  connect( d->InputVolumeComboBox, SIGNAL( currentNodeChanged(vtkMRMLNode*) ),
	  this, SLOT( onInputVolumeChanged(vtkMRMLNode*) ) );

  connect( d->OutputVolumeComboBox, SIGNAL( currentNodeChanged(vtkMRMLNode*) ),
	  this, SLOT( onOutputVolumeChanged(vtkMRMLNode*) ) );

  connect( d->RegionLabelsComboBox, SIGNAL( currentIndexChanged(const QString &) ),
	  this, SLOT( onRegionChanged(const QString &) ) );

  connect( d->TypeLabelsComboBox, SIGNAL( currentIndexChanged(const QString &) ),
	  this, SLOT( onTypeChanged(const QString &) ) );

  connect( d->RegionTypeSlider, SIGNAL( valueChanged(int) ),
	  this, SLOT( onColorChanged(int) ) );
}

//-----------------------------------------------------------------------------
void qSlicerRegionTypeModuleWidget::updateRegionList()
{
  Q_D(qSlicerRegionTypeModuleWidget);
  if( this->regionTypeNode == 0)
    {
    return;
    }
  if( !this->regionTypeNode->GetRegionTypeDisplayNode() )
    {
	  return;
    }

  std::vector<std::string>&regions = this->regionTypeNode->GetAvailableRegionNames();

	const char* allName = "ALL REGIONS";
  d->RegionLabelsComboBox->addItem(allName);

	//populate the combo-box here
	for( unsigned int i = 0; i < regions.size(); i++ )
	  {
	  const char* name = regions[i].c_str();
	  d->RegionLabelsComboBox->addItem(name);
	  }
}

//-----------------------------------------------------------------------------
void qSlicerRegionTypeModuleWidget::updateTypeList()
{
  Q_D(qSlicerRegionTypeModuleWidget);
  if( this->regionTypeNode == 0)
    {
    return;
    }
  if( !this->regionTypeNode->GetRegionTypeDisplayNode() )
    {
	  return;
    }

  std::vector<std::string>&types = this->regionTypeNode->GetAvailableTypeNames();

	const char* allName = "ALL TYPES";
  d->TypeLabelsComboBox->addItem(allName);

	//populate the combo-box here
	for( unsigned int i = 0; i < types.size(); i++ )
	  {
	  const char* name = types[i].c_str();
	  d->TypeLabelsComboBox->addItem(name);
	  }
}

//-----------------------------------------------------------------------------
void qSlicerRegionTypeModuleWidget::onInputVolumeChanged(vtkMRMLNode* node)
{
  Q_D(qSlicerRegionTypeModuleWidget);
  Q_ASSERT(d->InputVolumeComboBox);

  if( node == 0)
    {
    return;
    }

  vtkMRMLLabelMapVolumeNode* scalarNode = vtkMRMLLabelMapVolumeNode::SafeDownCast( node );

  if (this->regionTypeNode == 0)
    {
    this->createRegionTypeNode(scalarNode);
    //d->OutputVolumeComboBox->setCurrentNode(this->regionTypeNode);
    }
  else
    {
    this->updateRegionTypeNode(scalarNode);
    }

  d->TypeLabelsComboBox->clear();
  d->RegionLabelsComboBox->clear();
  this->updateRegionList();
  this->updateTypeList();

  if (this->regionTypeNode->GetRegionTypeDisplayNode())
    {
    double colorBlend = d->RegionTypeSlider->value()/100.0;
    this->regionTypeNode->GetRegionTypeDisplayNode()->ShowAllRegionTypes(this->regionTypeNode, colorBlend);
    }
  d->RegionLabelsComboBox->setCurrentIndex(0);
  d->TypeLabelsComboBox->setCurrentIndex(0);
}

//-----------------------------------------------------------------------------
void qSlicerRegionTypeModuleWidget::onOutputVolumeChanged(vtkMRMLNode* node)
{
  Q_D(qSlicerRegionTypeModuleWidget);
  Q_ASSERT(d->OutputVolumeComboBox);

  if( node == 0)
    {
    return;
    }

  vtkMRMLRegionTypeNode* regionTypeNode = vtkMRMLRegionTypeNode::SafeDownCast( node );

  this->regionTypeNode = regionTypeNode;

  if (this->regionTypeNode && vtkMRMLLabelMapVolumeNode::SafeDownCast(d->InputVolumeComboBox->currentNode()))
    {
    this->regionTypeNode->CopyOrientation(vtkMRMLLabelMapVolumeNode::SafeDownCast(d->InputVolumeComboBox->currentNode()));
    }

  this->updateRegionTypeNode(vtkMRMLLabelMapVolumeNode::SafeDownCast(d->InputVolumeComboBox->currentNode()));
}

//-----------------------------------------------------------------------------
void qSlicerRegionTypeModuleWidget::onTypeChanged(const QString & regionName)
{
  Q_UNUSED(regionName);
  this->updateDisplay();
}

//-----------------------------------------------------------------------------
void qSlicerRegionTypeModuleWidget::onRegionChanged(const QString & regionName)
{
  Q_UNUSED(regionName);
  this->updateDisplay();
}

//-----------------------------------------------------------------------------
void qSlicerRegionTypeModuleWidget::onColorChanged(int value)
{
  Q_UNUSED(value);
  this->updateDisplay();
}

//-----------------------------------------------------------------------------
void qSlicerRegionTypeModuleWidget::updateDisplay()
{
  Q_D(qSlicerRegionTypeModuleWidget);

  if (this->regionTypeNode && this->regionTypeNode->GetRegionTypeDisplayNode())
    {
    cip::ChestConventions cc;
    std::string regionString = d->RegionLabelsComboBox->currentText().toStdString();
    std::string typeString = d->TypeLabelsComboBox->currentText().toStdString();
    double colorBlend = d->RegionTypeSlider->value()/100.0;
    if (regionString == std::string("ALL REGIONS") && typeString == std::string("ALL TYPES"))
      {
      this->regionTypeNode->GetRegionTypeDisplayNode()->ShowAllRegionTypes(this->regionTypeNode, colorBlend);
      }
    else if (regionString == std::string("ALL REGIONS"))
      {
      unsigned char type = cc.GetChestTypeValueFromName(typeString);
      this->regionTypeNode->GetRegionTypeDisplayNode()->ShowAllRegions(this->regionTypeNode, type, colorBlend);
      }
    else if (typeString == std::string("ALL TYPES"))
      {
      unsigned char region = cc.GetChestRegionValueFromName(regionString);
      this->regionTypeNode->GetRegionTypeDisplayNode()->ShowAllTypes(this->regionTypeNode, region, colorBlend);
      }
    else
      {
      unsigned char region = cc.GetChestRegionValueFromName(regionString);
      unsigned char type = cc.GetChestTypeValueFromName(typeString);
      this->regionTypeNode->GetRegionTypeDisplayNode()->ShowSelectedRegionType(this->regionTypeNode,
                                                        region, type, colorBlend);
      }
    }
}

//-----------------------------------------------------------------------------
void qSlicerRegionTypeModuleWidget::createRegionTypeNode(vtkMRMLLabelMapVolumeNode* scalarVolume)
{
  if (scalarVolume == 0)
    {
    this->regionTypeNode  = 0;
    return;
    }

  vtkMRMLScene *scene = scalarVolume->GetScene();

  this->regionTypeNode = vtkMRMLRegionTypeNode::New();
	this->regionTypeNode->CopyWithScene(scalarVolume);

  std::string name;
  if (scalarVolume->GetName())
    {
    name = std::string(scalarVolume->GetName());
    }
  name += "_RegionType";
	this->regionTypeNode->SetName( name.c_str() );
  scene->AddNode(this->regionTypeNode);
  this->regionTypeNode->Delete();

  this->updateRegionTypeNode(scalarVolume);
}

//-----------------------------------------------------------------------------
void qSlicerRegionTypeModuleWidget::updateRegionTypeNode(vtkMRMLLabelMapVolumeNode* scalarVolume)
{
  Q_D(qSlicerRegionTypeModuleWidget);

  if (scalarVolume == 0 || this->regionTypeNode == 0)
    {
    return;
    }

  vtkMRMLScene *scene = scalarVolume->GetScene();

  if (scalarVolume->GetImageData())
    {
    vtkNew<vtkImageData> imageData;
    imageData->DeepCopy( scalarVolume->GetImageData() );
    this->regionTypeNode->SetAndObserveImageData( imageData.GetPointer() );
    }

  if (this->regionTypeNode->GetStorageNode() == 0 )
    {
    vtkMRMLStorageNode *storageNode = this->regionTypeNode->CreateDefaultStorageNode();
    scene->AddNode(storageNode);
	  this->regionTypeNode->SetAndObserveStorageNodeID( storageNode->GetID() );
    storageNode->Delete();
    }

  if (this->regionTypeNode->GetRegionTypeDisplayNode() == 0)
    {
    vtkMRMLRegionTypeDisplayNode* displayNode = vtkMRMLRegionTypeDisplayNode::New();

    displayNode->CopyWithScene(scalarVolume->GetDisplayNode());
		scene->AddNode( displayNode );

    // Create custom color rable
    vtkNew<vtkMRMLColorTableNode> colorNode;
    colorNode->SetTypeToUser();
    colorNode->SetName(scene->GenerateUniqueName("ChestRTColorTable").c_str());
    colorNode->SetDescription("A legacy colour table that contains some anatomical mapping for a Chest LabelMap");
    int size = 256;
    colorNode->SetNumberOfColors(size);
    colorNode->GetLookupTable()->SetTableRange(0, size);
    colorNode->NamesInitialisedOn();
    scene->AddNode(colorNode.GetPointer());

    displayNode->SetAndObserveColorNodeID( colorNode->GetID() );

    this->regionTypeNode->SetAndObserveDisplayNodeID( displayNode->GetID() );

		displayNode->Delete();

    //this->regionTypeNode->GetImageData()->Modified();
    this->regionTypeNode->UpdateAvailableRegionsAndTypes();

    double colorBlend = d->RegionTypeSlider->value()/100.0;

    displayNode->InitializeLookupTable(this->regionTypeNode, colorBlend);
    displayNode->ShowAllRegionTypes(this->regionTypeNode, colorBlend);
    }

  // make output node active label map node
  std::vector<vtkMRMLNode *> nodes;
  this->regionTypeNode->GetScene()->GetNodesByClass("vtkMRMLSelectionNode", nodes);
  if (nodes.size() > 0)
    {
    vtkMRMLSelectionNode *selectionNode = vtkMRMLSelectionNode::SafeDownCast(nodes[0]);
    selectionNode->SetReferenceActiveLabelVolumeID(this->regionTypeNode->GetID());
    selectionNode->Modified();
    }
}

