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
#include <QtPlugin>

// AirwayModule Logic includes
#include <vtkSlicerAirwayModuleLogic.h>

// AirwayModule includes
#include "qSlicerAirwayModuleModule.h"
#include "qSlicerAirwayModuleModuleWidget.h"

//-----------------------------------------------------------------------------
#if (QT_VERSION < QT_VERSION_CHECK(5, 0, 0))
#include <QtPlugin>
Q_EXPORT_PLUGIN2(qSlicerAirwayModuleModule, qSlicerAirwayModuleModule);
#endif

//-----------------------------------------------------------------------------
/// \ingroup Slicer_QtModules_ExtensionTemplate
class qSlicerAirwayModuleModulePrivate
{
public:
  qSlicerAirwayModuleModulePrivate();
};

//-----------------------------------------------------------------------------
// qSlicerAirwayModuleModulePrivate methods

//-----------------------------------------------------------------------------
qSlicerAirwayModuleModulePrivate
::qSlicerAirwayModuleModulePrivate()
{
}

//-----------------------------------------------------------------------------
// qSlicerAirwayModuleModule methods

//-----------------------------------------------------------------------------
qSlicerAirwayModuleModule
::qSlicerAirwayModuleModule(QObject* _parent)
  : Superclass(_parent)
  , d_ptr(new qSlicerAirwayModuleModulePrivate)
{
}

//-----------------------------------------------------------------------------
qSlicerAirwayModuleModule::~qSlicerAirwayModuleModule()
{
}

//-----------------------------------------------------------------------------
QString qSlicerAirwayModuleModule::helpText()const
{
  return "This is a loadable module bundled in an extension";
}

//-----------------------------------------------------------------------------
QString qSlicerAirwayModuleModule::acknowledgementText()const
{
  return "This work was was partially funded by NIH grant 3P41RR013218-12S1";
}

//-----------------------------------------------------------------------------
QStringList qSlicerAirwayModuleModule::contributors()const
{
  QStringList moduleContributors;
  moduleContributors << QString("Jean-Christophe Fillion-Robin (Kitware)");
  return moduleContributors;
}

//-----------------------------------------------------------------------------
QIcon qSlicerAirwayModuleModule::icon()const
{
  return QIcon(":/Icons/AirwayModule.png");
}

//-----------------------------------------------------------------------------
QStringList qSlicerAirwayModuleModule::categories() const
{
  return QStringList() << "Examples";
}

//-----------------------------------------------------------------------------
QStringList qSlicerAirwayModuleModule::dependencies() const
{
  return QStringList();
}

//-----------------------------------------------------------------------------
void qSlicerAirwayModuleModule::setup()
{
  this->Superclass::setup();
}

//-----------------------------------------------------------------------------
qSlicerAbstractModuleRepresentation * qSlicerAirwayModuleModule
::createWidgetRepresentation()
{
  return new qSlicerAirwayModuleModuleWidget;
}

//-----------------------------------------------------------------------------
vtkMRMLAbstractLogic* qSlicerAirwayModuleModule::createLogic()
{
  return vtkSlicerAirwayModuleLogic::New();
}
