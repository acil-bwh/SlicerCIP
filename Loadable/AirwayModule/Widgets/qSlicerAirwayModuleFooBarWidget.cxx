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

// FooBar Widgets includes
#include "qSlicerAirwayModuleFooBarWidget.h"
#include "ui_qSlicerAirwayModuleFooBarWidget.h"

//-----------------------------------------------------------------------------
/// \ingroup Slicer_QtModules_AirwayModule
class qSlicerAirwayModuleFooBarWidgetPrivate
  : public Ui_qSlicerAirwayModuleFooBarWidget
{
  Q_DECLARE_PUBLIC(qSlicerAirwayModuleFooBarWidget);
protected:
  qSlicerAirwayModuleFooBarWidget* const q_ptr;

public:
  qSlicerAirwayModuleFooBarWidgetPrivate(
    qSlicerAirwayModuleFooBarWidget& object);
  virtual void setupUi(qSlicerAirwayModuleFooBarWidget*);
};

// --------------------------------------------------------------------------
qSlicerAirwayModuleFooBarWidgetPrivate
::qSlicerAirwayModuleFooBarWidgetPrivate(
  qSlicerAirwayModuleFooBarWidget& object)
  : q_ptr(&object)
{
}

// --------------------------------------------------------------------------
void qSlicerAirwayModuleFooBarWidgetPrivate
::setupUi(qSlicerAirwayModuleFooBarWidget* widget)
{
  this->Ui_qSlicerAirwayModuleFooBarWidget::setupUi(widget);
}

//-----------------------------------------------------------------------------
// qSlicerAirwayModuleFooBarWidget methods

//-----------------------------------------------------------------------------
qSlicerAirwayModuleFooBarWidget
::qSlicerAirwayModuleFooBarWidget(QWidget* parentWidget)
  : Superclass( parentWidget )
  , d_ptr( new qSlicerAirwayModuleFooBarWidgetPrivate(*this) )
{
  Q_D(qSlicerAirwayModuleFooBarWidget);
  d->setupUi(this);
}

//-----------------------------------------------------------------------------
qSlicerAirwayModuleFooBarWidget
::~qSlicerAirwayModuleFooBarWidget()
{
}
