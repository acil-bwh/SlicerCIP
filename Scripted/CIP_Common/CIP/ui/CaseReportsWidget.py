
import csv, os, time
from __main__ import qt, ctk, slicer

class CaseReportsWidget(object):
    # Events triggered by the widget
    EVENT_SAVE = 1
    EVENT_SHOW = 2
    EVENT_DOWNLOAD = 2


    def __init__(self, moduleName, columnNames, parent = None):
        """Widget constructor (existing module)"""
        if not parent:
            self.parent = slicer.qMRMLWidget()
            self.parent.setLayout(qt.QVBoxLayout())
            self.parent.setMRMLScene(slicer.mrmlScene)
        else:
            self.parent = parent
        self.layout = self.parent.layout()

        self.logic = CaseReportsLogic(moduleName, columnNames)
        self.__initEvents__()
        self.reportWindow = CaseReportsWindow(self)



    def setup(self):
        self.saveValuesButton = ctk.ctkPushButton()
        self.saveValuesButton.text = "Save"
        self.layout.addWidget(self.saveValuesButton)


        self.openButton = ctk.ctkPushButton()
        self.openButton.text = "Open"
        self.layout.addWidget(self.openButton)

        self.exportButton = ctk.ctkPushButton()
        self.exportButton.text = "Export"
        self.layout.addWidget(self.exportButton)

        self.saveValuesButton.connect('clicked()', self.onSave)
        self.exportButton.connect('clicked()', self.onDownload)
        self.openButton.connect('clicked()', self.onShowStoredData)

    def __initEvents__(self):
        """Init all the structures required for events mechanism"""
        self.eventsCallbacks = list()
        self.events = [self.EVENT_SAVE, self.EVENT_SHOW, self.EVENT_DOWNLOAD]

    def addObservable(self, event, callback):
        """Add a function that will be invoked when the corresponding event is triggered.
        The list of possible events are: EVENT_LOAD, EVENT_SAVE, EVENT_SAVEALL.
        Ex: myWidget.addObservable(myWidget.EVENT_LOAD, self.onFileLoaded)"""
        if event not in self.events:
            raise Exception("Event not recognized. It must be one of these: EVENT_SAVE, EVENT_SHOW, EVENT_DOWNLOAD")

        # Add the event to the list of funcions that will be called when the matching event is triggered
        self.eventsCallbacks.append((event, callback))

    def __triggerEvent__(self, eventType, *params):
        """Trigger one of the possible events from the object.
        Ex:    self.__triggerEvent__(self.EVENT_SAVE) """
        for callback in (item[1] for item in self.eventsCallbacks if item[0] == eventType):
            callback(*params)

    def saveCurrentValues(self, **kwargs):
        self.logic.saveValues(**kwargs)

    def setColumnNames(self, columnNames):
        self.logic.setColumnNames(columnNames)

    def onSave(self):
        self.__triggerEvent__(self.EVENT_SAVE)


    def onDownload(self):
        fileName = qt.QFileDialog.getSaveFileName(self.parent, "Export to CSV file")
        if fileName:
            self.logic.exportCSV(fileName)

    def onShowStoredData(self):
        self.reportWindow.load(self.logic.columnNamesExtended, self.logic.loadValues())
        self.reportWindow.show()



class CaseReportsLogic(object):
    def __init__(self, moduleName, columnNames):
        self.__moduleName__ = moduleName
        p = os.path.dirname(slicer.util.getModule(moduleName).path)
        if os.sys.platform == "win32":
            p = p.replace("/", "\\")
        self.__csvFilePath__ = os.path.join(p, "Resources", moduleName + ".storage.csv")
        self.__columnNames__ = columnNames

    @property
    def columnNames(self):
        return self.__columnNames__

    def setColumnNames(self, columnNames):
        self.__columnNames__ = columnNames

    @property
    def columnNamesExtended(self):
        columns = ["Date"]
        columns.extend(self.columnNames)
        return columns

    @property
    def _csvFilePath_(self):
        return self.__csvFilePath__


    def saveValues(self, **kwargs):
        # Check that we have all the "columns"
        if len(kwargs) != len(self.columnNames):
            print("There is a wrong number of arguments. Total columns: {0}. Columns passed: {1}".format(len(self.columnNames), len(kwargs)))
            return False


        for key in kwargs:
            if key not in self.columnNames:
                print("Column {0} is not included in the list of columns".format(key))
                return False
        # Add the values in the right order (there are not obligatory fields)
        orderedColumns = []
        # Always add a timestamp as the first value
        orderedColumns.append(time.strftime("%Y/%m/%d %H:%M:%S"))
        for column in self.columnNames:
            if kwargs.has_key(column):
                orderedColumns.append(kwargs[column])
            else:
                orderedColumns.append('')



        with open(self._csvFilePath_, 'a+b') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(orderedColumns)

    def exportCSV(self, filePath):
        with open(self._csvFilePath_, 'r+b') as csvfileReader:
            reader = csv.reader(csvfileReader)
            with open(filePath, 'a+b') as csvfileWriter:
                writer = csv.writer(csvfileWriter)
                writer.writerow(self.columnNamesExtended)
                for row in reader:
                    writer.writerow(row)

    def loadValues(self):
        data = []
        with open(self._csvFilePath_, 'r+b') as csvfileReader:
            reader = csv.reader(csvfileReader)
            for row in reader:
                data.append(row)
        return data





class CaseReportsWindow(qt.QWidget):
    def __init__(self, parent):
        super(CaseReportsWindow, self).__init__()

        self.mainLayout = qt.QVBoxLayout(self)
        self.setLayout(self.mainLayout)
        self.resize(400, 300)

        self.label = qt.QLabel("Data stored in the module: ")
        self.label.setStyleSheet("margin: 10px 0 15px 0")
        self.mainLayout.addWidget(self.label)

        self.tableView = qt.QTableView()
        self.tableView.setColumnWidth(0,120)

        self.tableView.setSizePolicy(qt.QSizePolicy.Expanding, qt.QSizePolicy.Expanding)
        self.mainLayout.addWidget(self.tableView)

        self.exportButton = ctk.ctkPushButton()
        self.exportButton.text = "Export"
        self.mainLayout.addWidget(self.exportButton)

        self.exportButton.connect('clicked()', parent.onDownload)




    def load(self, columnNames, data):

        self.items = []

        self.statisticsTableModel = qt.QStandardItemModel()
        self.tableView.setModel(self.statisticsTableModel)
        self.tableView.verticalHeader().visible = False
        self.tableView.sortingEnabled = True

        policy = self.tableView.sizePolicy
        policy.setVerticalPolicy(qt.QSizePolicy.Expanding)
        policy.setHorizontalPolicy(qt.QSizePolicy.Expanding)
        policy.setVerticalStretch(0)
        self.tableView.setSizePolicy(policy)

        # Header
        self.statisticsTableModel.setHorizontalHeaderLabels(columnNames)


        for row in range(len(data)):
            rowData = data[row]
            for col in range(len(rowData)):
                item = qt.QStandardItem()
                item.setData(data[row][col], qt.Qt.DisplayRole)
                item.setEditable(False)
                self.statisticsTableModel.setItem(row, col,item)
                self.items.append(item)


