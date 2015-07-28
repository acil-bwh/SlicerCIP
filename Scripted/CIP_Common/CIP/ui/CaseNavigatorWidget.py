import os, subprocess, hashlib
import os.path as path


from __main__ import qt, ctk, slicer
from CIP.logic import SlicerUtil

class CaseNavigatorWidget(object):
    # Events triggered by the widget
    EVENT_BEFORENEXT = 1
    EVENT_NEXT = 2
    EVENT_BEFOREPREVIOUS = 3
    EVENT_AFTERPREVIOUS = 4

    def __init__(self, moduleName="", parentContainer = None):
        """Widget constructor (existing module)"""
        if not parentContainer:
            self.parent = slicer.qMRMLWidget()
            self.parent.setLayout(qt.QVBoxLayout())
            self.parent.setMRMLScene(slicer.mrmlScene)
        else:
            self.parent = parentContainer
        self.layout = self.parent.layout()

        self.logic = CaseNavigatorLogic(moduleName)
        self.__initEvents__()
        self.setup()


    def setup(self):
        self.prevCaseButton = ctk.ctkPushButton()
        self.prevCaseButton.text = "Previous"
        self.layout.addWidget(self.prevCaseButton)

        self.nextCaseButton = ctk.ctkPushButton()
        self.nextCaseButton.text = "Next"
        self.layout.addWidget(self.nextCaseButton)
        #
        # self.prevCaseButton.connect('clicked()', self.onNextCaseClicked)
        self.nextCaseButton.connect('clicked()', self.onNextCaseClicked)

        caseListFile = "/Volumes/Mac500/Data/tempdata/dummyCaseList.txt"


    def __initEvents__(self):
        """Init all the structures required for events mechanism"""
        self.eventsCallbacks = list()
        self.events = [self.EVENT_BEFORENEXT, self.EVENT_NEXT, self.EVENT_BEFOREPREVIOUS, self.EVENT_AFTERPREVIOUS]

    def addObservable(self, event, callback):
        """Add a function that will be invoked when the corresponding event is triggered.
        Ex: myWidget.addObservable(myWidget.EVENT_BEFORENEXT, self.onBeforeNextClicked)"""
        if event not in self.events:
            raise Exception("Event not recognized. It must be one of these: EVENT_BEFORENEXT, EVENT_NEXT, EVENT_BEFOREPREVIOUS, EVENT_AFTERPREVIOUS")

        # Add the event to the list of funcions that will be called when the matching event is triggered
        self.eventsCallbacks.append((event, callback))

    def __triggerEvent__(self, eventType, *params):
        """Trigger one of the possible events from the object.
        Ex:    self.__triggerEvent__(self.EVENT_BEFORENEXT) """
        for callback in (item[1] for item in self.eventsCallbacks if item[0] == eventType):
            callback(*params)


    ######
    # EVENTS
    def onNextCaseClicked(self):
        self.__triggerEvent__(self.EVENT_BEFORENEXT)
        self.logic.nextCase()
        self.__triggerEvent__(self.EVENT_BEFORENEXT)

class CaseNavigatorLogic:
    def __init__(self, modulePath):
        """Constructor. Adapt the module full path to windows convention when necessary"""
        #ScriptedLoadableModuleLogic.__init__(self)
        self.modulePath = modulePath
        self.caseListFile = None
        self.caseListIds = None
        self.caseList = None    # Dictionary of content data for every case
        self.listHash = None    # Hashtag that will define the caselist based on name, creationdate, etc.

        self.currentCaseIndex = -1
        self.previousCases = None
        self.bufferSize = 1     # Number of cases to download in advance
        self.__nextCaseExists__ = None

        self.mainCaseTemplate = None   # Default: curent directory/Case.nhdr
        self.labelMapsTemplates = []  # For each labelmap that we want to load with the case, a tmeplate to define the file path must be specified
        self.additionalFilesTemplates = []  # Other files that will be read as binaries

        self.localStoragePath = "{0}/CaseNavigator/{1}".format(slicer.app.temporaryPath, self.modulePath)

        if not os.path.exists(self.localStoragePath):
            # Create the directory
            os.makedirs(self.localStoragePath)
            # Make sure that everybody has write permissions (sometimes there are problems because of umask)
            os.chmod(self.localStoragePath, 0777)


        # TODO: does this make sense? Try a large case list
        self.loadFullCaseList = True    # By default, read al the cases together

    def readCaseList(self, caseListFullPath):
        """ Load a case list file that will be used to iterate over the cases
        :param caseListFullPath:
        """
        try:
            self.caseListFile = open(caseListFullPath, "r")
            if self.loadFullCaseList:
                # Read the whole case list. This will allow full case navigation
                self.caseListIds = self.caseListFile.readlines()
                self.caseListFile.close()
                # Remove blank lines if any
                # i = 1
                # l = len(self.caseListIds)
                # id = self.caseListIds[l - i]
                #

            else:
                # Load the elements just when next case is requested. Restricted navigation
                # Useful for very large case lists
                self.caseListIds = []
            self.listHash = self.__createListHash__(caseListFullPath)
            self.currentCaseIndex = -1
        except:
            # Error when reading file
            self.caseListFile = None
            raise

    def __createListHash__(self, fileFullPath):
        """ Create a hashtag for a list based on:
        - Name
        - Size
        - Last modification date
        :param fileFullPath:
        :return:
        """
        stats = os.stat(fileFullPath)
        id = "{0}_{1}_{2}".format(path.basename(fileFullPath), stats[6], stats[8])
        # Get a MD5 sum for the concatenated id
        m = hashlib.md5()
        m.update(id)
        return m.hexdigest()

    def nextCase(self):
        """ Read the next case id in the list and load the associated info.
        It also tries to download all the required files for the next case
        :return: True if the case was loaded correctly or False if we are at the end of the list
        """
        if SlicerUtil.IsDevelopment:
            print("DEBUG: Downloading next case...")
            print("DEBUG: current case index: {0}. Current case ID: {1}".format(self.currentCaseIndex, self.currentCaseId))

        if self.caseListIds is None:
            raise Exception("List is not initialized. First, read a caselist with readCaseList method")

        self.currentCaseIndex += 1
        if self.currentCaseIndex >= len(self.caseListIds):
            # End of list
            return False
        self.currentCaseId = self.caseListIds[self.currentCaseIndex].strip()
        if self.currentCaseId == "":
            # Blank line. End of list
            return False

        # Download in background the required files for index+buffer cases
        self.downloadNextCases(self.currentCaseIndex, self.bufferSize)

        return True


    def downloadNextCases(self, caseIndex, bufferSize):
        """ Download the required files for the next "bufferSize" cases after "currentCaseIndex"
        :param currentCaseIndex:
        :param bufferSize:
        :return:
        """
        l = len(self.caseListIds)

        if caseIndex + 1 >= l:
            # End of list
            return
        for i in range(bufferSize):
            caseId = self.caseListIds[caseIndex + i + 1].strip()
            if self.currentCaseId == "":
                return
            # Build the command to execute
            print("DEBUG: downloading case ", caseId)

