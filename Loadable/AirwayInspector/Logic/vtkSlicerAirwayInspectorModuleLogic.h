#ifndef __vtkSlicerAirwayInspectorModuleLogic_h
#define __vtkSlicerAirwayInspectorModuleLogic_h

// Slicer Logic includes
#include "vtkSlicerAirwayInspectorModuleLogicExport.h"
#include "vtkSlicerModuleLogic.h"

#include <vtkNew.h>
#include <vtkObjectFactory.h>

// STD includes
#include <string>

class vtkRenderWindowInteractor;
class vtkMRMLAirwayNode;

/// \ingroup Slicer_QtModules_AirwayInspector
class VTK_SLICER_AIRWAYINSPECTOR_MODULE_LOGIC_EXPORT vtkSlicerAirwayInspectorModuleLogic
  :public vtkSlicerModuleLogic
{
public:

  static vtkSlicerAirwayInspectorModuleLogic *New();
  vtkTypeMacro(vtkSlicerAirwayInspectorModuleLogic,vtkSlicerModuleLogic);
  virtual void PrintSelf(ostream& os, vtkIndent indent);

  /// Called after one of the observable event is invoked
  static void DoInteractorCallback(vtkObject* vtk_obj, unsigned long event,
                                   void* client_data, void* call_data);

  void OnInteractorEvent(int eventid);

  /// Description:
  /// String ID of the volume MRML node
  vtkSetStringMacro(VolumeNodeID);
  vtkGetStringMacro(VolumeNodeID);

  /// Get/Set Threshold
  vtkSetMacro(Threshold, int);
  vtkGetMacro(Threshold, int);

protected:

  vtkSlicerAirwayInspectorModuleLogic();

  virtual ~vtkSlicerAirwayInspectorModuleLogic();

  // Initialize listening to MRML events
  virtual void SetMRMLSceneInternal(vtkMRMLScene * newScene);
  virtual void ObserveMRMLScene();

  void SetAndObserveInteractor(vtkRenderWindowInteractor* newInteractor);

  vtkMRMLAirwayNode* AddAirwayNode(double x, double y, double z);

  vtkRenderWindowInteractor*                Interactor;
  vtkSmartPointer<vtkCallbackCommand>       InteractorCallBackCommand;

  double Threshold;
  char *VolumeNodeID;

private:
};

#endif
