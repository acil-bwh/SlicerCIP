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

#ifndef __qSlicerAirwayInspectorModuleWidget_h
#define __qSlicerAirwayInspectorModuleWidget_h

// SlicerQt includes
#include "qSlicerAbstractModuleWidget.h"

#include "qSlicerAirwayInspectorModuleExport.h"

class qSlicerAirwayInspectorModuleWidgetPrivate;
class vtkMRMLNode;

/// \ingroup Slicer_QtModules_AirwayInspector
class Q_SLICER_QTMODULES_AIRWAYINSPECTOR_EXPORT qSlicerAirwayInspectorModuleWidget :
  public qSlicerAbstractModuleWidget
{
  Q_OBJECT

public:

  typedef qSlicerAbstractModuleWidget Superclass;
  qSlicerAirwayInspectorModuleWidget(QWidget *parent=0);
  virtual ~qSlicerAirwayInspectorModuleWidget();

protected:
  virtual void setup();

protected slots:
  void setMRMLVolumeNode(vtkMRMLNode*);
  void setMRMLAirwayNode(vtkMRMLNode*);

protected:
  QScopedPointer<qSlicerAirwayInspectorModuleWidgetPrivate> d_ptr;

private:
  Q_DECLARE_PRIVATE(qSlicerAirwayInspectorModuleWidget);
  Q_DISABLE_COPY(qSlicerAirwayInspectorModuleWidget);
};

#endif
