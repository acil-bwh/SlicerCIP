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
#include <QtPlugin>

// Slicer includes
#include <qSlicerCoreApplication.h>
#include <qSlicerModuleManager.h>

// MyRegionType Logic includes
#include <vtkSlicerCLIModuleLogic.h>
#include <vtkSlicerMyRegionTypeLogic.h>
#include <vtkSlicerVolumesLogic.h>

// MyRegionType includes
#include "qSlicerMyRegionTypeModule.h"
#include "qSlicerMyRegionTypeModuleWidget.h"

//-----------------------------------------------------------------------------
Q_EXPORT_PLUGIN2(qSlicerMyRegionTypeModule, qSlicerMyRegionTypeModule);

//-----------------------------------------------------------------------------
/// \ingroup Slicer_QtModules_ExtensionTemplate
class qSlicerMyRegionTypeModulePrivate
{
public:
  qSlicerMyRegionTypeModulePrivate();
};

//-----------------------------------------------------------------------------
// qSlicerMyRegionTypeModulePrivate methods

//-----------------------------------------------------------------------------
qSlicerMyRegionTypeModulePrivate
::qSlicerMyRegionTypeModulePrivate()
{
}

//-----------------------------------------------------------------------------
// qSlicerMyRegionTypeModule methods

//-----------------------------------------------------------------------------
qSlicerMyRegionTypeModule
::qSlicerMyRegionTypeModule(QObject* _parent)
  : Superclass(_parent)
  , d_ptr(new qSlicerMyRegionTypeModulePrivate)
{
}

//-----------------------------------------------------------------------------
qSlicerMyRegionTypeModule::~qSlicerMyRegionTypeModule()
{
}

//-----------------------------------------------------------------------------
QString qSlicerMyRegionTypeModule::helpText()const
{
  return "This is a loadable module to display selected region and type";
}

//-----------------------------------------------------------------------------
QString qSlicerMyRegionTypeModule::acknowledgementText()const
{
  return "This module was developed by Pietro Nardelli";
}

//-----------------------------------------------------------------------------
QStringList qSlicerMyRegionTypeModule::contributors()const
{
  QStringList moduleContributors;
  moduleContributors << QString("Pietro Nardelli (UCC)");
  return moduleContributors;
}

//-----------------------------------------------------------------------------
QIcon qSlicerMyRegionTypeModule::icon()const
{
  return QIcon(":/Icons/MyRegionType.png");
}

//-----------------------------------------------------------------------------
QStringList qSlicerMyRegionTypeModule::categories() const
{
  return QStringList() << "Converters";
}

//-----------------------------------------------------------------------------
QStringList qSlicerMyRegionTypeModule::dependencies() const
{
  return QStringList() << "Volumes";
}

//-----------------------------------------------------------------------------
void qSlicerMyRegionTypeModule::setup()
{
  this->Superclass::setup();
  
  vtkSlicerMyRegionTypeLogic* regionTypeLogic =
    vtkSlicerMyRegionTypeLogic::SafeDownCast(this->logic());

  qSlicerAbstractCoreModule* volumesModule =
    qSlicerCoreApplication::application()->moduleManager()->module("Volumes");
  if (volumesModule)
    {
    vtkSlicerVolumesLogic* volumesLogic = 
      vtkSlicerVolumesLogic::SafeDownCast(volumesModule->logic());
    regionTypeLogic->SetVolumesLogic(volumesLogic);
    }
  else
    {
    qWarning() << "Volumes module is not found";
    }
}

//-----------------------------------------------------------------------------
qSlicerAbstractModuleRepresentation * qSlicerMyRegionTypeModule
::createWidgetRepresentation()
{
  return new qSlicerMyRegionTypeModuleWidget;
}

//-----------------------------------------------------------------------------
vtkMRMLAbstractLogic* qSlicerMyRegionTypeModule::createLogic()
{
  return vtkSlicerMyRegionTypeLogic::New();
}
