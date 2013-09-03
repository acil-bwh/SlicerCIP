import os
import unittest
from __main__ import vtk, qt, ctk, slicer

#
# TestAirwayModule
#
class test_airwaymodule_loadsave:
  def __init__(self, parent):
    parent.title = "Test AirwayModule Load and Save" # TODO make this more human readable by adding spaces
    parent.categories = ["Testing.TestCases"]
    parent.dependencies = []
    parent.contributors = ["Demian Wassermann (Brigham and Women's Hospital)"] # replace with "Firstname Lastname (Org)"
    parent.helpText = """
    This is a scripted loadable module bundled in an extension.
    """
    parent.acknowledgementText = """
    This file was originally developed by Demian Wassermann
""" # replace with organization, grant and thanks.
    self.parent = parent

    # Add this test to the SelfTest module's list for discovery when the module
    # is created.  Since this module may be discovered before SelfTests itself,
    # create the list if it doesn't already exist.
    try:
      slicer.selfTests
    except AttributeError:
      slicer.selfTests = {}
    slicer.selfTests['test_airwaymodule_loadsave'] = self.runTest

  def runTest(self):
    tester = TestAirwayModuleLoadSave()
    tester.runTest()


class TestAirwayModuleLoadSave(unittest.TestCase):
    def test_load(self):
        pass
