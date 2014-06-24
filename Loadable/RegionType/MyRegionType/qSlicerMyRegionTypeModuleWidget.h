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

#ifndef __qSlicerMyRegionTypeModuleWidget_h
#define __qSlicerMyRegionTypeModuleWidget_h

// SlicerQt includes
#include "qSlicerAbstractModuleWidget.h"

#include "qSlicerMyRegionTypeModuleExport.h"
#include <vtkNew.h>
#include <vtkMRMLScalarVolumeNode.h>

class qSlicerMyRegionTypeModuleWidgetPrivate;
class vtkMRMLNode;
class vtkMRMLMyRegionTypeNode;

/// \ingroup Slicer_QtModules_ExtensionTemplate
class Q_SLICER_QTMODULES_MYREGIONTYPE_EXPORT qSlicerMyRegionTypeModuleWidget :
  public qSlicerAbstractModuleWidget
{
  Q_OBJECT

public:

  typedef qSlicerAbstractModuleWidget Superclass;
  qSlicerMyRegionTypeModuleWidget(QWidget *parent=0);
  virtual ~qSlicerMyRegionTypeModuleWidget();

public slots:

protected:
  QScopedPointer<qSlicerMyRegionTypeModuleWidgetPrivate> d_ptr;
  
  virtual void setup();
  virtual void enter();
  virtual void setMRMLScene(vtkMRMLScene*);

  void initializeRegionTypeNode(vtkMRMLScene*);
  void convertToRegionTypeNode(vtkMRMLScalarVolumeNode*);

protected slots:
  void onInputVolumeChanged();
  void onApply();
  void updateRegionList();
  void updateTypeList();
  void updateWidget();
  //void updateRegionType();
  void onEndCloseEvent();

private:
  Q_DECLARE_PRIVATE(qSlicerMyRegionTypeModuleWidget);
  Q_DISABLE_COPY(qSlicerMyRegionTypeModuleWidget);

  vtkMRMLMyRegionTypeNode* regionTypeNode;
  //vtkNew<vtkMRMLMyRegionTypeNode> regionTypeNode;
  int initialize;

};

#endif
