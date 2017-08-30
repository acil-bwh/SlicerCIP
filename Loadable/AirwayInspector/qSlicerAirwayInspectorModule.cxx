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
#include <QDebug>
#include <QtPlugin>

// SlicerQt includes
#include <qSlicerCoreApplication.h>
#include <qSlicerIOManager.h>
#include <qSlicerModuleManager.h>
#include <qSlicerNodeWriter.h>

// AirwayInspector Logic includes
#include <vtkSlicerAirwayInspectorModuleLogic.h>

// AirwayInspector QTModule includes
#include "qSlicerAirwayInspectorModule.h"
#include "qSlicerAirwayInspectorModuleWidget.h"

// MRML includes
#include <vtkMRMLScene.h>

//-----------------------------------------------------------------------------
Q_EXPORT_PLUGIN2(qSlicerAirwayInspectorModule, qSlicerAirwayInspectorModule);

//-----------------------------------------------------------------------------
/// \ingroup Slicer_QtModules_AirwayInspector
class qSlicerAirwayInspectorModulePrivate
{
public:
};

//-----------------------------------------------------------------------------
qSlicerAirwayInspectorModule::qSlicerAirwayInspectorModule(QObject* _parent)
  : Superclass(_parent)
  , d_ptr(new qSlicerAirwayInspectorModulePrivate)
{
}

//-----------------------------------------------------------------------------
qSlicerAirwayInspectorModule::~qSlicerAirwayInspectorModule()
{
}

//-----------------------------------------------------------------------------
QString qSlicerAirwayInspectorModule::helpText()const
{
  QString help = QString(
    "The AirwayInspector Module detects airway walls and computes their parameters.<br>"
    "To analyze an airway select a volume, point your mouse in the center or an aiway in the Red slice view and press 'a' key.<br>"
    "<a href=\"%1/Documentation/%2.%3/Modules/AirwayInspector\">"
    "%1/Documentation/%2.%3/Modules/AirwayInspector</a><br>");
  return help.arg(this->slicerWikiUrl()).arg(Slicer_VERSION_MAJOR).arg(Slicer_VERSION_MINOR);
}

//-----------------------------------------------------------------------------
QString qSlicerAirwayInspectorModule::acknowledgementText()const
{
  QString acknowledgement = QString(
    "<center><table border=\"0\"><tr>"
    "<td><img src=\":Logos/NAMIC.png\" alt\"NA-MIC\"></td>"
    "<td><img src=\":Logos/NAC.png\" alt\"NAC\"></td>"
    "</tr><tr>"
    "<td><img src=\":Logos/BIRN-NoText.png\" alt\"BIRN\"></td>"
    "<td><img src=\":Logos/NCIGT.png\" alt\"NCIGT\"></td>"
    "</tr></table></center>"
    "This work was supported by NA-MIC, NAC, BIRN, NCIGT, and the Slicer "
    "Community. See <a href=\"http://www.slicer.org\">http://www.slicer.org"
    "</a> for details.<br>"
    "The AirwayInspector module was contributed by Alex Yarmarkovich, Isomics Inc. "
    "(Steve Pieper) and Julien Finet, Kitware Inc. with help from others at "
    "SPL, BWH (Ron Kikinis).<br><br>");
  return acknowledgement;
}

//-----------------------------------------------------------------------------
QStringList qSlicerAirwayInspectorModule::contributors()const
{
  QStringList moduleContributors;
  moduleContributors << QString("Alex Yarmarkovich (BWH)");
  return moduleContributors;
}

//-----------------------------------------------------------------------------
QIcon qSlicerAirwayInspectorModule::icon()const
{
  return QIcon(":/Icons/AirwayInspector.png");
}

//-----------------------------------------------------------------------------
QStringList qSlicerAirwayInspectorModule::categories() const
{
  return QStringList() << "Chest Imaging Platform";
}

//-----------------------------------------------------------------------------
QStringList qSlicerAirwayInspectorModule::dependencies() const
{
  QStringList moduleDependencies;
  moduleDependencies << "Colors" << "Units";
  return moduleDependencies;
}

//-----------------------------------------------------------------------------
void qSlicerAirwayInspectorModule::setup()
{
  this->Superclass::setup();
  //vtkSlicerAirwayInspectorModuleLogic* AirwayInspectorLogic =
  //  vtkSlicerAirwayInspectorModuleLogic::SafeDownCast(this->logic());

  /**
  qSlicerCoreIOManager* ioManager =
    qSlicerCoreApplication::application()->coreIOManager();
  ioManager->registerIO(new qSlicerAirwayInspectorReader(AirwayInspectorLogic,this));
  ioManager->registerIO(new qSlicerNodeWriter(
    "AirwayInspector", QString("VolumeFile"),
    QStringList() << "vtkMRMLVolumeNode", this));
**/
}

//-----------------------------------------------------------------------------
qSlicerAbstractModuleRepresentation* qSlicerAirwayInspectorModule::createWidgetRepresentation()
{
  return new qSlicerAirwayInspectorModuleWidget;
}

//-----------------------------------------------------------------------------
vtkMRMLAbstractLogic* qSlicerAirwayInspectorModule::createLogic()
{
  return vtkSlicerAirwayInspectorModuleLogic::New();
}
