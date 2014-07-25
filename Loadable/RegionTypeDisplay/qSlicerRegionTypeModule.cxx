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

// RegionType Logic includes
#include <vtkSlicerCLIModuleLogic.h>
#include <vtkSlicerRegionTypeLogic.h>
#include <vtkSlicerVolumesLogic.h>

// RegionType includes
#include "qSlicerRegionTypeModule.h"
#include "qSlicerRegionTypeModuleWidget.h"

//-----------------------------------------------------------------------------
Q_EXPORT_PLUGIN2(qSlicerRegionTypeModule, qSlicerRegionTypeModule);

//-----------------------------------------------------------------------------
/// \ingroup Slicer_QtModules_ExtensionTemplate
class qSlicerRegionTypeModulePrivate
{
public:
  qSlicerRegionTypeModulePrivate();
};

//-----------------------------------------------------------------------------
// qSlicerRegionTypeModulePrivate methods

//-----------------------------------------------------------------------------
qSlicerRegionTypeModulePrivate
::qSlicerRegionTypeModulePrivate()
{
}

//-----------------------------------------------------------------------------
// qSlicerRegionTypeModule methods

//-----------------------------------------------------------------------------
qSlicerRegionTypeModule
::qSlicerRegionTypeModule(QObject* _parent)
  : Superclass(_parent)
  , d_ptr(new qSlicerRegionTypeModulePrivate)
{
}

//-----------------------------------------------------------------------------
qSlicerRegionTypeModule::~qSlicerRegionTypeModule()
{
}

//-----------------------------------------------------------------------------
QString qSlicerRegionTypeModule::helpText()const
{
  return "This is a loadable module to display selected region and type";
}

//-----------------------------------------------------------------------------
QString qSlicerRegionTypeModule::acknowledgementText()const
{
  return "This module was developed by Pietro Nardelli";
}

//-----------------------------------------------------------------------------
QStringList qSlicerRegionTypeModule::contributors()const
{
  QStringList moduleContributors;
  moduleContributors << QString("Pietro Nardelli (UCC)");
  return moduleContributors;
}

//-----------------------------------------------------------------------------
QIcon qSlicerRegionTypeModule::icon()const
{
  return QIcon(":/Icons/RegionType.png");
}

//-----------------------------------------------------------------------------
QStringList qSlicerRegionTypeModule::categories() const
{
  return QStringList() << "Converters";
}

//-----------------------------------------------------------------------------
QStringList qSlicerRegionTypeModule::dependencies() const
{
  return QStringList() << "Volumes";
}

//-----------------------------------------------------------------------------
void qSlicerRegionTypeModule::setup()
{
  this->Superclass::setup();

  vtkSlicerRegionTypeLogic* regionTypeLogic =
    vtkSlicerRegionTypeLogic::SafeDownCast(this->logic());

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
qSlicerAbstractModuleRepresentation * qSlicerRegionTypeModule
::createWidgetRepresentation()
{
  return new qSlicerRegionTypeModuleWidget;
}

//-----------------------------------------------------------------------------
vtkMRMLAbstractLogic* qSlicerRegionTypeModule::createLogic()
{
  return vtkSlicerRegionTypeLogic::New();
}
