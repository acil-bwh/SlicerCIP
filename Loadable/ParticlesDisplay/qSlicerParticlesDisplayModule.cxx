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

// ParticlesDisplay Logic includes
#include <vtkSlicerCLIModuleLogic.h>
#include <vtkSlicerParticlesDisplayLogic.h>
#include <vtkSlicerVolumesLogic.h>

// ParticlesDisplay includes
#include "qSlicerParticlesDisplayModule.h"
#include "qSlicerParticlesDisplayModuleWidget.h"

//-----------------------------------------------------------------------------
Q_EXPORT_PLUGIN2(qSlicerParticlesDisplayModule, qSlicerParticlesDisplayModule);

//-----------------------------------------------------------------------------
/// \ingroup Slicer_QtModules_ExtensionTemplate
class qSlicerParticlesDisplayModulePrivate
{
public:
  qSlicerParticlesDisplayModulePrivate();
};

//-----------------------------------------------------------------------------
// qSlicerParticlesDisplayModulePrivate methods

//-----------------------------------------------------------------------------
qSlicerParticlesDisplayModulePrivate
::qSlicerParticlesDisplayModulePrivate()
{
}

//-----------------------------------------------------------------------------
// qSlicerParticlesDisplayModule methods

//-----------------------------------------------------------------------------
qSlicerParticlesDisplayModule
::qSlicerParticlesDisplayModule(QObject* _parent)
  : Superclass(_parent)
  , d_ptr(new qSlicerParticlesDisplayModulePrivate)
{
}

//-----------------------------------------------------------------------------
qSlicerParticlesDisplayModule::~qSlicerParticlesDisplayModule()
{
}

//-----------------------------------------------------------------------------
QString qSlicerParticlesDisplayModule::helpText()const
{
  return "This is a loadable module to display selected region and type";
}

//-----------------------------------------------------------------------------
QString qSlicerParticlesDisplayModule::acknowledgementText()const
{
  return "This module was developed by Pietro Nardelli";
}

//-----------------------------------------------------------------------------
QStringList qSlicerParticlesDisplayModule::contributors()const
{
  QStringList moduleContributors;
  moduleContributors << QString("Pietro Nardelli (UCC)");
  return moduleContributors;
}

//-----------------------------------------------------------------------------
QIcon qSlicerParticlesDisplayModule::icon()const
{
  return QIcon(":/Icons/ParticlesDisplay.png");
}

//-----------------------------------------------------------------------------
QStringList qSlicerParticlesDisplayModule::categories() const
{
  return QStringList() << "Converters";
}

//-----------------------------------------------------------------------------
QStringList qSlicerParticlesDisplayModule::dependencies() const
{
  return QStringList() << "RegionType";
}

//-----------------------------------------------------------------------------
void qSlicerParticlesDisplayModule::setup()
{
  this->Superclass::setup();

  vtkSlicerParticlesDisplayLogic* particlesDisplayLogic =
    vtkSlicerParticlesDisplayLogic::SafeDownCast(this->logic());
}

//-----------------------------------------------------------------------------
qSlicerAbstractModuleRepresentation * qSlicerParticlesDisplayModule
::createWidgetRepresentation()
{
  return new qSlicerParticlesDisplayModuleWidget;
}

//-----------------------------------------------------------------------------
vtkMRMLAbstractLogic* qSlicerParticlesDisplayModule::createLogic()
{
  return vtkSlicerParticlesDisplayLogic::New();
}
