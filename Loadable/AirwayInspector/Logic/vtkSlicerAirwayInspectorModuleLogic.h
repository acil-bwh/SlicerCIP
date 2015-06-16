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

  /// Description:
  /// String ID of the volume MRML node
  vtkSetStringMacro(VolumeNodeID);
  vtkGetStringMacro(VolumeNodeID);

  /// Get/Set Threshold
  vtkSetMacro(Threshold, int);
  vtkGetMacro(Threshold, int);

  vtkMRMLAirwayNode* AddAirwayNode(double x, double y, double z);

  void CreateAirway(vtkMRMLAirwayNode *node);

protected:

  vtkSlicerAirwayInspectorModuleLogic();

  virtual ~vtkSlicerAirwayInspectorModuleLogic();

  double Threshold;
  char *VolumeNodeID;

private:
};

#endif
