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

#ifndef __qSlicerRegionTypeModuleWidget_h
#define __qSlicerRegionTypeModuleWidget_h

// SlicerQt includes
#include "qSlicerAbstractModuleWidget.h"

#include "qSlicerRegionTypeModuleExport.h"
#include <vtkNew.h>
#include <vtkMRMLScalarVolumeNode.h>

class qSlicerRegionTypeModuleWidgetPrivate;
class vtkMRMLNode;
class vtkMRMLScalarVolumeNode;
class vtkMRMLRegionTypeNode;

/// \ingroup Slicer_QtModules_ExtensionTemplate
class Q_SLICER_QTMODULES_REGIONTYPE_EXPORT qSlicerRegionTypeModuleWidget :
  public qSlicerAbstractModuleWidget
{
  Q_OBJECT

public:

  typedef qSlicerAbstractModuleWidget Superclass;
  qSlicerRegionTypeModuleWidget(QWidget *parent=0);
  virtual ~qSlicerRegionTypeModuleWidget();

public slots:

protected:
  QScopedPointer<qSlicerRegionTypeModuleWidgetPrivate> d_ptr;

  virtual void setup();

protected slots:
  void onInputVolumeChanged(vtkMRMLNode*);
  void onOutputVolumeChanged(vtkMRMLNode*);
  void onRegionChanged(const QString &);
  void onTypeChanged(const QString &);
  void onColorChanged(int);

private:
  Q_DECLARE_PRIVATE(qSlicerRegionTypeModuleWidget);
  Q_DISABLE_COPY(qSlicerRegionTypeModuleWidget);

  void updateRegionList();
  void updateTypeList();
  void updateDisplay();
  void createRegionTypeNode(vtkMRMLScalarVolumeNode* scalarVolume);
  void updateRegionTypeNode(vtkMRMLScalarVolumeNode* scalarVolume);

  vtkMRMLRegionTypeNode* regionTypeNode;
};

#endif
