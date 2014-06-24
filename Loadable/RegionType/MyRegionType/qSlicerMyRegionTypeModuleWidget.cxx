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
#include "qSlicerMyRegionTypeModuleWidget.h"
#include "ui_qSlicerMyRegionTypeModuleWidget.h"

#include <vtkSlicerMyRegionTypeLogic.h>

#include <vtkMRMLMyRegionTypeNode.h>
#include <vtkMRMLMyRegionTypeDisplayNode.h>
#include <vtkMRMLScalarVolumeNode.h>
#include <vtkMRMLLabelMapVolumeDisplayNode.h>
#include <vtkMRMLChestRTColorTableNode.h>

#include <vtkMRMLVolumeNode.h>

#include <vtkMatrix4x4.h>
#include <vtkSmartPointer.h>
#include <vtkImageData.h>
#include <vtkNew.h>
#include <vtkImageThreshold.h>

//-----------------------------------------------------------------------------
/// \ingroup Slicer_QtModules_ExtensionTemplate
class qSlicerMyRegionTypeModuleWidgetPrivate: public Ui_qSlicerMyRegionTypeModuleWidget
{
  Q_DECLARE_PUBLIC(qSlicerMyRegionTypeModuleWidget);
protected:
  qSlicerMyRegionTypeModuleWidget* const q_ptr;
public:

  qSlicerMyRegionTypeModuleWidgetPrivate(qSlicerMyRegionTypeModuleWidget& object);
  ~qSlicerMyRegionTypeModuleWidgetPrivate();

  vtkSlicerMyRegionTypeLogic* logic() const;

  bool checkForVolumeParentTransform() const;

};

//-----------------------------------------------------------------------------
// qSlicerMyRegionTypeModuleWidgetPrivate methods

//-----------------------------------------------------------------------------
qSlicerMyRegionTypeModuleWidgetPrivate::qSlicerMyRegionTypeModuleWidgetPrivate(qSlicerMyRegionTypeModuleWidget& object) : q_ptr(&object)
{
}

//-----------------------------------------------------------------------------
qSlicerMyRegionTypeModuleWidgetPrivate::~qSlicerMyRegionTypeModuleWidgetPrivate()
{
}

//-----------------------------------------------------------------------------
vtkSlicerMyRegionTypeLogic* qSlicerMyRegionTypeModuleWidgetPrivate::logic() const
{
  Q_Q(const qSlicerMyRegionTypeModuleWidget);
  return vtkSlicerMyRegionTypeLogic::SafeDownCast(q->logic());
}

//-----------------------------------------------------------------------------
bool qSlicerMyRegionTypeModuleWidgetPrivate::checkForVolumeParentTransform() const
{
  Q_ASSERT(this->InputVolumeComboBox);


  vtkSmartPointer<vtkMRMLVolumeNode> inputVolume = vtkMRMLVolumeNode::SafeDownCast(this->InputVolumeComboBox->currentNode());

  if(!inputVolume)
    return false;

   //vtkSmartPointer<vtkMRMLLinearTransformNode> volTransform  = vtkMRMLLinearTransformNode::SafeDownCast(inputVolume->GetParentTransformNode());

   //if(volTransform)
   return true;

   //return false;
}

//-----------------------------------------------------------------------------
// qSlicerMyRegionTypeModuleWidget methods

//-----------------------------------------------------------------------------
qSlicerMyRegionTypeModuleWidget::qSlicerMyRegionTypeModuleWidget(QWidget* _parent)
  : Superclass( _parent )
  , d_ptr( new qSlicerMyRegionTypeModuleWidgetPrivate(*this) )
{
  //this->regionTypeNode = NULL;
}

//-----------------------------------------------------------------------------
qSlicerMyRegionTypeModuleWidget::~qSlicerMyRegionTypeModuleWidget()
{
	this->regionTypeNode->Delete();
}

//-----------------------------------------------------------------------------
void qSlicerMyRegionTypeModuleWidget::setup()
{
  Q_D(qSlicerMyRegionTypeModuleWidget);
  d->setupUi(this);

  //ctkFlowLayout* flowLayout = ctkFlowLayout::replaceLayout(d->InterpolatorWidget);
  //flowLayout->setPreferredExpandingDirections(Qt::Vertical);

  this->Superclass::setup();

  connect( d->ShowButton, SIGNAL( clicked() ), 
	  this, SLOT( onApply() ) );
  connect( d->InputVolumeComboBox, SIGNAL( currentNodeChanged(vtkMRMLNode*) ),
	  this, SLOT( onInputVolumeChanged() ) );
}

//-----------------------------------------------------------------------------
void qSlicerMyRegionTypeModuleWidget::enter()
{
  this->Superclass::enter();
this->initialize = 0;	
  this->onInputVolumeChanged();
}

//-----------------------------------------------------------------------------
void qSlicerMyRegionTypeModuleWidget::setMRMLScene(vtkMRMLScene* scene)
{

  this->Superclass::setMRMLScene(scene);
  if(scene == NULL)
    {
    return;
    }

  this->initializeRegionTypeNode(scene);
}

//-----------------------------------------------------------------------------
void qSlicerMyRegionTypeModuleWidget::initializeRegionTypeNode(vtkMRMLScene* scene)
{
  vtkCollection* regionTypeNodes = scene->GetNodesByClass("vtkMRMLScalarVolumeNode");
std::cout<<"in initializeRegionTypeNode"<<std::endl;
  if( regionTypeNodes->GetNumberOfItems() > 0 )
  {
	vtkMRMLScalarVolumeNode* scalarNode = vtkMRMLScalarVolumeNode::SafeDownCast( regionTypeNodes->GetItemAsObject(0) );
	this->regionTypeNode = vtkMRMLMyRegionTypeNode::New();
	if( scalarNode->GetLabelMap() )
	{
		this->regionTypeNode->CopyWithScene(scalarNode);
		scene->AddNode(this->regionTypeNode);
  		this->regionTypeNode->RemoveAllDisplayNodeIDs();
  		this->regionTypeNode->SetAndObserveStorageNodeID(NULL);		

                vtkNew<vtkImageData> imageData;
  		imageData->DeepCopy( scalarNode->GetImageData() );
  		this->regionTypeNode->SetAndObserveImageData( imageData.GetPointer() );
		this->regionTypeNode->SetName( scalarNode->GetName() );
		this->regionTypeNode->SetAndObserveStorageNodeID( scalarNode->GetStorageNodeID() );
		
                vtkMRMLMyRegionTypeDisplayNode* displayNode = vtkMRMLMyRegionTypeDisplayNode::New();
		displayNode->CopyWithScene(scalarNode->GetDisplayNode());
		scene->AddNode( displayNode ); 

		vtkMRMLChestRTColorTableNode* colorTableNode = vtkMRMLChestRTColorTableNode::New();
		colorTableNode->SetTypeToChestRTLabels();
		scene->AddNode( colorTableNode );

 		displayNode->SetAndObserveColorNodeID( colorTableNode->GetID() );
		displayNode->SetInterpolation( scalarNode->GetDisplayNode()->GetInterpolation() );
		//displayNode->GetImageData()->CopyStructure( scalarNode->GetImageData() );
		
                this->regionTypeNode->SetAndObserveDisplayNodeID( displayNode->GetID() );

                scene->RemoveNode( scalarNode->GetDisplayNode() );
		scene->RemoveNode( scalarNode );
      		
		displayNode->Delete();
		colorTableNode->Delete();

		if(!this->regionTypeNode->GetID())
		{
			qCritical() << "FATAL ERROR: Cannot instantiate RegionTypeNode";
			Q_ASSERT(this->regionTypeNode);
		}

		this->updateWidget();
	}
	this->regionTypeNode->Delete();
	this->initialize = 1;
  }
  else
  {
	  qDebug() << "No RegionType nodes found!";
  }
  regionTypeNodes->Delete();
  if( this->initialize != 1 )
  {
	this->initialize = 0;	
  }
  std::cout<<this->initialize<<std::endl;
}

//-----------------------------------------------------------------------------
void qSlicerMyRegionTypeModuleWidget::onInputVolumeChanged()
{
  Q_D(qSlicerMyRegionTypeModuleWidget);
  Q_ASSERT(d->InputVolumeComboBox);

  vtkSlicerMyRegionTypeLogic *logic = d->logic();

  vtkMRMLNode* node = d->InputVolumeComboBox->currentNode();

  std::cout<<"in onInputVolumeChanged"<<std::endl;
  if( node )
  {	  
	  std::cout<<this->initialize<<std::endl;
	  if( node->IsA( "vtkMRMLMyRegionTypeNode" ) && d->InputVolumeComboBox->nodes().count() > 1 )
	  {		  

		  d->TypeLabelsComboBox->clear();
  		  d->RegionLabelsComboBox->clear(); 		
		  this->regionTypeNode = vtkMRMLMyRegionTypeNode::SafeDownCast( node );
          logic->DisplayAllRegionType( this->regionTypeNode );  
		  this->updateWidget();
	  }
	  else if( node->IsA( "vtkMRMLScalarVolumeNode" ) && d->InputVolumeComboBox->nodes().count() > 1)
	  {
          d->TypeLabelsComboBox->clear();
  		  d->RegionLabelsComboBox->clear();
		  vtkMRMLScalarVolumeNode* scalarNode = vtkMRMLScalarVolumeNode::SafeDownCast( node );
		  if( scalarNode->GetLabelMap() )
		  {
			  this->convertToRegionTypeNode(scalarNode);
		  }
	  }
	  else if( d->InputVolumeComboBox->nodes().count() == 1 && this->initialize == 0 && node->IsA( "vtkMRMLScalarVolumeNode" ) )
	 {      	
		vtkMRMLScalarVolumeNode* scalarNode = vtkMRMLScalarVolumeNode::SafeDownCast( node );
		if( scalarNode->GetLabelMap() )
		{
			if( node->IsA( "vtkMRMLMyRegionTypeNode" ) )
			{
				this->initialize = 1;
				d->TypeLabelsComboBox->clear();
  		  		d->RegionLabelsComboBox->clear(); 		
                this->regionTypeNode = vtkMRMLMyRegionTypeNode::SafeDownCast( node );
				this->updateWidget();
			}
			else
			{
		 		this->convertToRegionTypeNode(scalarNode);
			}		  
		}		
	 }
  }
}

//-----------------------------------------------------------------------------
void qSlicerMyRegionTypeModuleWidget::convertToRegionTypeNode(vtkMRMLScalarVolumeNode* scalarVolume)
{
	std::cout<<"in convertToRegionTypeNode"<<std::endl;
    this->regionTypeNode = vtkMRMLMyRegionTypeNode::New();			
	this->regionTypeNode->CopyWithScene(scalarVolume);
    scalarVolume->GetScene()->AddNode(this->regionTypeNode);
  	this->regionTypeNode->RemoveAllDisplayNodeIDs();
  	this->regionTypeNode->SetAndObserveStorageNodeID(NULL);

    vtkNew<vtkImageData> imageData;
  	imageData->DeepCopy( scalarVolume->GetImageData() );
  	this->regionTypeNode->SetAndObserveImageData( imageData.GetPointer() );
	this->regionTypeNode->SetName( scalarVolume->GetName() );
	this->regionTypeNode->SetAndObserveStorageNodeID( scalarVolume->GetStorageNodeID() );
	

	/*vtkMRMLMyRegionTypeDisplayNode* displayNode = vtkMRMLMyRegionTypeDisplayNode::New();
	displayNode->CopyWithScene(scalarVolume->GetDisplayNode()); 
	scalarVolume->GetScene()->AddNode( displayNode );

	vtkMRMLChestRTColorTableNode* colorTableNode = vtkMRMLChestRTColorTableNode::New();
	colorTableNode->SetTypeToChestRTLabels();
	scalarVolume->GetScene()->AddNode( colorTableNode );

 	displayNode->SetAndObserveColorNodeID( colorTableNode->GetID() );

        scalarVolume->GetScene()->RemoveNode( scalarVolume->GetDisplayNode() );
        this->regionTypeNode->SetAndObserveDisplayNodeID( displayNode->GetID() );*/                

        scalarVolume->GetScene()->RemoveNode( scalarVolume );
		
	if(!this->regionTypeNode->GetID())
	{
		qCritical() << "FATAL ERROR: Cannot instantiate RegionTypeNode";
		Q_ASSERT(this->regionTypeNode);
	}
	//this->regionTypeNode->Delete();
	
//	displayNode->Delete();
//	colorTableNode->Delete();
	
}

//-----------------------------------------------------------------------------
void qSlicerMyRegionTypeModuleWidget::updateRegionList()
{
  Q_D(qSlicerMyRegionTypeModuleWidget);
  if( this->regionTypeNode ) //node
  {
          if( !this->regionTypeNode->GetDisplayNode() )
	  {		
		return;
	  }
	  if( this->regionTypeNode->GetDisplayNode()->IsA( "vtkMRMLMyRegionTypeDisplayNode" ) )
	  {	  
		  vtkMRMLMyRegionTypeDisplayNode* labelMapNode = vtkMRMLMyRegionTypeDisplayNode::SafeDownCast( this->regionTypeNode->GetDisplayNode() );
		  vtkImageData* im = labelMapNode->GetInputImageData();
		  vtkMRMLChestRTColorTableNode* colorNode = vtkMRMLChestRTColorTableNode::SafeDownCast( labelMapNode->GetColorNode() );
		  int numberOfColors = colorNode->GetNumberOfRegions();
		  this->regionTypeNode->SetAvailableRegionsValues( im, numberOfColors );
		  if( labelMapNode->GetColorNode()->IsA( "vtkMRMLChestRTColorTableNode" ) ) //not need of this?
		  {
			  this->regionTypeNode->SetAvailableRegionsNames( labelMapNode->GetColorNode() );
		  }

		  if( this->regionTypeNode->RegionNamesList.size()  > 0 )
		  {
		  	const char* noneName = "NO REGIONS";
		  	const char* allName = "ALL REGIONS";

		  	d->RegionLabelsComboBox->addItem(noneName);
		  	d->RegionLabelsComboBox->addItem(allName);

		  	//populate the combo-box here?
		  	for( unsigned int i = 0; i < this->regionTypeNode->RegionNamesList.size(); i++ )
		  	{
				const char* name = this->regionTypeNode->RegionNamesList[i];
				d->RegionLabelsComboBox->addItem(name);
		  	}
		  }

		  labelMapNode->Delete();
	  }
  }
}

//-----------------------------------------------------------------------------
void qSlicerMyRegionTypeModuleWidget::updateTypeList()
{
  Q_D(qSlicerMyRegionTypeModuleWidget);
  if( this->regionTypeNode )
  {
	  if( !this->regionTypeNode->GetDisplayNode() )
	  {		
		return;
	  }
	  if( this->regionTypeNode->GetDisplayNode()->IsA( "vtkMRMLMyRegionTypeDisplayNode" ) )
	  {
		  vtkMRMLMyRegionTypeDisplayNode* labelMapNode = vtkMRMLMyRegionTypeDisplayNode::SafeDownCast( this->regionTypeNode->GetDisplayNode() );
		  vtkImageData* im = labelMapNode->GetInputImageData();
		  vtkMRMLChestRTColorTableNode* colorNode = vtkMRMLChestRTColorTableNode::SafeDownCast( labelMapNode->GetColorNode() );
		  int numberOfColors = colorNode->GetNumberOfTypes();
		  this->regionTypeNode->SetAvailableTypesValues( im, numberOfColors );
		  if( labelMapNode->GetColorNode()->IsA( "vtkMRMLChestRTColorTableNode" ) )//not need of this?
		  {
			  this->regionTypeNode->SetAvailableTypesNames( labelMapNode->GetColorNode() );
		  }

		  if( this->regionTypeNode->TypeNamesList.size() > 0 )
		  {
			  const char* noneName = "NO TYPES";
			  const char* allName = "ALL TYPES";

			  d->TypeLabelsComboBox->addItem(noneName);
			  d->TypeLabelsComboBox->addItem(allName);

			  //populate the combo-box here?
			  for( unsigned int i = 0; i < this->regionTypeNode->TypeNamesList.size(); i++ )
			  {
				  const char* name = this->regionTypeNode->TypeNamesList[i];
				  d->TypeLabelsComboBox->addItem(name);
			  }
		  }

		  labelMapNode->Delete();
	  }
  }
}

//-----------------------------------------------------------------------------
void qSlicerMyRegionTypeModuleWidget::onEndCloseEvent()
{
  this->initializeRegionTypeNode(this->mrmlScene());
}

//-----------------------------------------------------------------------------
void qSlicerMyRegionTypeModuleWidget::onApply()
{
  Q_D(const qSlicerMyRegionTypeModuleWidget);
  vtkSlicerMyRegionTypeLogic *logic = d->logic();

  if( !d->InputVolumeComboBox->currentNode() )
    return;

  if( d->RegionLabelsComboBox->count() == 0 && d->TypeLabelsComboBox->count() == 0 )
  {
	return;
  }

  if( d->RegionLabelsComboBox->count() != 0 && d->TypeLabelsComboBox->count() != 0 )
  {
  	int rindex = d->RegionLabelsComboBox->currentIndex();
	QString rname = d->RegionLabelsComboBox->itemText(rindex);
  	QByteArray ra = rname.toLatin1();
  	const char* regionName = ra.data();

	int tindex = d->TypeLabelsComboBox->currentIndex();
  	QString tname = d->TypeLabelsComboBox->itemText(tindex);
  	QByteArray ta = tname.toLatin1();
  	const char* typeName = ta.data();
	
	logic->DisplaySelectedRegionType( this->regionTypeNode, regionName, typeName );
  }
  else if( d->RegionLabelsComboBox->count() != 0)
  {
  	int rindex = d->RegionLabelsComboBox->currentIndex();
	QString rname = d->RegionLabelsComboBox->itemText(rindex);
  	QByteArray ra = rname.toLatin1();
  	const char* regionName = ra.data();

	logic->DisplaySelectedRegionType( this->regionTypeNode, regionName, NULL );
  }
  else
  {
	int tindex = d->TypeLabelsComboBox->currentIndex();
  	QString tname = d->TypeLabelsComboBox->itemText(tindex);
  	QByteArray ta = tname.toLatin1();
  	const char* typeName = ta.data();
	
	logic->DisplaySelectedRegionType( this->regionTypeNode, NULL, typeName );
  }

}

//-----------------------------------------------------------------------------
void qSlicerMyRegionTypeModuleWidget::updateWidget()
{
  	if(!this->mrmlScene())
    	{
    		qDebug()<<"No RegionType node in updateWidget";
    		return;
    	}      

        this->regionTypeNode->RegionNamesList.clear();
  	this->regionTypeNode->RegionValuesList.clear();
  	this->regionTypeNode->TypeNamesList.clear();
  	this->regionTypeNode->TypeValuesList.clear();

   	this->updateRegionList();
    	this->updateTypeList();
}



