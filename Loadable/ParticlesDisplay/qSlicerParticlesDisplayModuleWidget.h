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

#ifndef __qSlicerParticlesDisplayModuleWidget_h
#define __qSlicerParticlesDisplayModuleWidget_h

// SlicerQt includes
#include "qSlicerAbstractModuleWidget.h"

#include "qSlicerParticlesDisplayModuleExport.h"
#include <vtkNew.h>
#include <vtkMRMLScalarVolumeNode.h>

class qSlicerParticlesDisplayModuleWidgetPrivate;
class vtkMRMLNode;
class vtkMRMLModelNode;
class vtkMRMLParticlesDisplayNode;

/// \ingroup Slicer_QtModules_ExtensionTemplate
class Q_SLICER_QTMODULES_PARTICLESDISPLAY_EXPORT qSlicerParticlesDisplayModuleWidget :
  public qSlicerAbstractModuleWidget
{
  Q_OBJECT

public:

  typedef qSlicerAbstractModuleWidget Superclass;
  qSlicerParticlesDisplayModuleWidget(QWidget *parent=0);
  virtual ~qSlicerParticlesDisplayModuleWidget();

public slots:

protected:
  QScopedPointer<qSlicerParticlesDisplayModuleWidgetPrivate> d_ptr;

  virtual void setup();
  void createParticlesDisplayNode(vtkMRMLModelNode* modelNode);
  void updateParticlesDisplayNode();
  vtkMRMLParticlesDisplayNode* getParticlesDisplayNode();

protected slots:
  void onInputChanged(vtkMRMLNode*);
  void onOutputChanged(vtkMRMLNode*);
  void onRegionChanged(const QString &);
  void onTypeChanged(const QString &);
  void onGlyphTypeChanged(const QString &);
  void onColorByChanged(const QString &);
  void onScaleChanged(int);

private:
  Q_DECLARE_PRIVATE(qSlicerParticlesDisplayModuleWidget);
  Q_DISABLE_COPY(qSlicerParticlesDisplayModuleWidget);
};

#endif
