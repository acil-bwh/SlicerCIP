
import csv, os, time, pprint
from __main__ import qt, ctk, slicer

from CIP.logic import EventsTrigger
from CIP.logic.SlicerUtil import SlicerUtil

class CaseReportsWidget(EventsTrigger):
    # Events triggered by the widget
    EVENT_SAVE_BUTTON_CLICKED = 1
    EVENT_SHOW_REPORT = 2
    EVENT_CLEAN_CACHE = 3

    @property
    def TIMESTAMP_COLUMN_NAME(self):
        return self.logic.TIMESTAMP_COLUMN_NAME

    def __init__(self, moduleName, columnNames, parentWidget = None, filePreffix=""):
        """Widget constructor (existing module)"""
        EventsTrigger.__init__(self)
        
        if not parentWidget:
            self.parent = slicer.qMRMLWidget()
            self.parent.setLayout(qt.QVBoxLayout())
            self.parent.setMRMLScene(slicer.mrmlScene)
        else:
            self.parent = parentWidget
        self.layout = self.parent.layout()

        self.__showWarningWhenIncompleteColumns__ = True
        self.logic = CaseReportsLogic(moduleName, columnNames, filePreffix)
        self.__initEvents__()
        self.reportWindow = CaseReportsWindow(self)
    @property
    def showWarningWhenWrongColumns(self):
        return self.__showWarningWhenIncompleteColumns__

    def setup(self):
        self.saveValuesButton = ctk.ctkPushButton()
        self.saveValuesButton.text = "Save"
        self.saveValuesButton.setIcon(qt.QIcon("{0}/Save.png".format(SlicerUtil.CIP_ICON_DIR)))
        self.saveValuesButton.setIconSize(qt.QSize(24,24))
        self.layout.addWidget(self.saveValuesButton)

        self.openButton = ctk.ctkPushButton()
        self.openButton.text = "Open"
        self.openButton.setIcon(qt.QIcon("{0}/open_file.png".format(SlicerUtil.CIP_ICON_DIR)))
        self.openButton.setIconSize(qt.QSize(24,24))

        self.layout.addWidget(self.openButton)

        self.exportButton = ctk.ctkPushButton()
        self.exportButton.text = "Export"
        self.exportButton.setIcon(qt.QIcon("{0}/export-csv.png".format(SlicerUtil.CIP_ICON_DIR)))
        self.exportButton.setIconSize(qt.QSize(24,24))
        self.layout.addWidget(self.exportButton)

        self.removeButton = ctk.ctkPushButton()
        self.removeButton.setIcon(qt.QIcon("{0}/delete.png".format(SlicerUtil.CIP_ICON_DIR)))
        self.removeButton.setIconSize(qt.QSize(24,24))
        self.removeButton.text = "Clean cache"
        self.layout.addWidget(self.removeButton)

        self.saveValuesButton.connect('clicked()', self.onSave)
        self.exportButton.connect('clicked()', self.onExport)
        self.openButton.connect('clicked()', self.onShowStoredData)
        self.removeButton.connect('clicked()', self.onRemoveStoredData)

    def __initEvents__(self):
        """Init all the structures required for events mechanism"""
        self.setEvents([self.EVENT_SAVE_BUTTON_CLICKED, self.EVENT_SHOW_REPORT, self.EVENT_CLEAN_CACHE])

    def setColumnNames(self, columnNames):
        """ Set the column names that will saved every time the user clicks "Save" button
        :param columnNames:
        """
        self.logic.columnNames = columnNames

    def saveCurrentValues(self, **kwargs):
        """ Save a record.
        The function will expect to be invoked with key-value parameters with the name of the columns.
        Ex: self.reportsWidget.saveCurrentValues(
                caseId = caseName,
                regionType = stat.LabelCode,
                label = stat.LabelDescription)
        :param kwargs:
        :return:
        """
        self.logic.saveValues(**kwargs)

    def enableSaveButton(self, enabled):
        """ Enable/Disable the "Save" button
        :param enabled: True/False
        """
        self.saveValuesButton.setEnabled(enabled)

    def showSaveButton(self, show):
        """ Show/hide the save button (it can be hidden when the data are saved obligatory)
        :param show: show == True
        """
        self.saveValuesButton.setVisible(show)

    def showWarnigMessages(self, showMessages):
        """ Show/Hide warning messages when the columns passed when saving some values are not exactly the ones expected
        :param showMessages: True/False
        """
        self.__showWarningWhenIncompleteColumns__ = showMessages
        self.logic.showWarningWhenIncompleteColumns = showMessages

    ###############
    # EVENTS
    def onSave(self):
        """ Trigger the event of saving some stored data.
        The widget just triggers the signal, it is the responsibility of the parent to save the desired data
        :return:
        """
        self.triggerEvent(self.EVENT_SAVE_BUTTON_CLICKED)


    def onExport(self):
        """ Export the current csv file to a customized and formatted file
        :return:
        """
        fileName = qt.QFileDialog.getSaveFileName(self.parent, "Export to CSV file")
        if fileName:
            self.logic.exportCSV(fileName)
            qt.QMessageBox.information(slicer.util.mainWindow(), 'Data exported', 'The data were exported successfully')


    def onShowStoredData(self):
        """ Show the dialog window with all the information stored so far
        :return:
        """
        self.reportWindow.load(self.logic.columnNamesExtended, self.logic.loadValues())
        self.reportWindow.show()
        self.triggerEvent(self.EVENT_SHOW_REPORT)

    def onRemoveStoredData(self):
        """ Remove the current csv file
        :return:
        """
        if (qt.QMessageBox.question(slicer.util.mainWindow(), 'Remove stored data',
                'Are you sure you want to remove the saved csv data?',
                qt.QMessageBox.Yes|qt.QMessageBox.No)) == qt.QMessageBox.Yes:
            self.logic.remove()
            qt.QMessageBox.information(slicer.util.mainWindow(), 'Data removed', 'The data were removed successfully')
            self.triggerEvent(self.EVENT_CLEAN_CACHE)


#############################
##
class CaseReportsLogic(object):
    DBTYPE_SQLITE = 0


    def __init__(self, moduleName, columnNames, filePreffix):
        self.__moduleName__ = moduleName
        p = SlicerUtil.getSettingsDataFolder(moduleName)
        if filePreffix != "":
            self.__csvFilePath__ = os.path.join(p, "{0}.{1}.storage.csv".format(filePreffix, moduleName))
        else:
            self.__csvFilePath__ = os.path.join(p, moduleName + ".storage.csv")
        self.__columnNames__ = columnNames
        self.showWarningWhenIncompleteColumns = True

        self.db = None

    def createDB(self, dbType):
        if dbType == self.DBTYPE_SQLITE:
            self.db = vtk.vtkSQLiteDatabase()

    @property
    def TIMESTAMP_COLUMN_NAME(self):
        return "Timestamp"

    @property
    def columnNames(self):
        return self.__columnNames__
    @columnNames.setter
    def columnNames(self, value):
        self.__columnNames__ = value

    @property
    def columnNamesExtended(self):
        """ Column names with the date (timestamp) added as the first column
        :return:
        """
        columns = [self.TIMESTAMP_COLUMN_NAME]
        columns.extend(self.columnNames)
        return columns

    @property
    def csvFilePath(self):
        """ Path of the file that contains all the data
        :return: Path of the file that contains all the data
        """
        return self.__csvFilePath__


    def saveValues(self, **kwargs):
        """ Save a new row of information in the current csv file that stores the data  (from a dictionary of items)
        :param kwargs: dictionary of values
        """
        # Check that we have all the "columns"
        if len(kwargs) != len(self.columnNames) and self.showWarningWhenIncompleteColumns:
            print("WARNING. There is a wrong number of arguments in ReportsWidget. ")
            print("Current columns: ")
            pprint.pprint(self.columnNames)
            print("Total: {0}".format(len(self.columnNames)))
            print("Args passed: ")
            pprint.pprint(kwargs)
            print("Total: {0}".format(len(kwargs)))

        for key in kwargs:
            if key not in self.columnNames:
                print("WARNING: Column {0} is not included in the list of columns".format(key))
        # Add the values in the right order (there are not obligatory fields)
        orderedColumns = []
        # Always add a timestamp as the first value
        orderedColumns.append(time.strftime("%Y/%m/%d %H:%M:%S"))
        for column in self.columnNames:
            if kwargs.has_key(column):
                orderedColumns.append(kwargs[column])
            else:
                orderedColumns.append('')

        fileExists = os.path.isfile(self.csvFilePath)
        with open(self.csvFilePath, 'a+b') as csvfile:
            writer = csv.writer(csvfile)
            # If file is empty, save also the column names
            # if not fileExists:
            #     writer.writerow(self.columnNames)
            writer.writerow(orderedColumns)


    def exportCSV(self, filePath):
        """ Export the information stored in the current csv file that is storing the data to a better
        formatted csv file in a location chosen by the user
        :param filePath: destination of the file (full path)
        :return:
        """
        if os.path.exists(self.csvFilePath):
            with open(self.csvFilePath, 'r+b') as csvfileReader:
                reader = csv.reader(csvfileReader)
                with open(filePath, 'a+b') as csvfileWriter:
                    writer = csv.writer(csvfileWriter)
                    writer.writerow(self.columnNamesExtended)
                    for row in reader:
                        writer.writerow(row)
            return True
        else:
            return False

    def loadValues(self):
        """ Load all the information stored in the csv file
        :return: list of lists (rows/colums)
        """
        data = []
        if os.path.exists(self.csvFilePath):
            with open(self.csvFilePath, 'r+b') as csvfileReader:
                reader = csv.reader(csvfileReader)
                for row in reader:
                    data.append(row)
        return data

    def getLastRow(self):
        """ Return the last row of data that was stored in the csv file
        :return: list with the information of a single row
        """
        if os.path.exists(self.csvFilePath):
            with open(self.csvFilePath, 'r+b') as csvfileReader:
                reader = csv.reader(csvfileReader)
                #return reader.next()
                # Read all the information of the file to iterate in reverse order
                rows = [row for row in reader]
                return rows.pop()
        # Error case
        return None

    def findLastMatchRow(self, columnIndex, value):
        """ Go over all the rows in the CSV until it finds the value "value" in the column "columnName"
        :param columnIndex: index of the column that we are comparing. This index will NOT include the obligatory timestamp field
        :param value:
        :return: row with the first match or None if it' not found
        """
        if os.path.exists(self.csvFilePath):
            with open(self.csvFilePath, 'r+b') as csvfileReader:
                reader = csv.reader(csvfileReader)
                rows = [row for row in reader if row[columnIndex + 1] == value]
                # print("DEBUG. Rows:")
                # import pprint
                # pprint.pprint(rows)
                if len(rows) > 0:
                    # Get the last element
                    return rows.pop()
        # Not found
        return None

    def remove(self):
        """ Remove the whole results file """
        if os.path.exists(self.csvFilePath):
            os.remove(self.csvFilePath)




class CaseReportsWindow(qt.QWidget):
    """ Class that show a window dialog with a table that will display all the information loaded
    for the state of this module
    """
    def __init__(self, parent):
        super(CaseReportsWindow, self).__init__()

        self.mainLayout = qt.QVBoxLayout(self)
        self.setLayout(self.mainLayout)
        self.resize(400, 300)

        self.label = qt.QLabel("Data stored in the module: ")
        self.label.setStyleSheet("margin: 10px 0 15px 0")
        self.mainLayout.addWidget(self.label)

        self.tableView = qt.QTableView()
        self.tableView.setColumnWidth(0,125)

        self.tableView.setSizePolicy(qt.QSizePolicy.Expanding, qt.QSizePolicy.Expanding)
        self.mainLayout.addWidget(self.tableView)

        self.exportButton = ctk.ctkPushButton()
        self.exportButton.text = "Export"
        self.exportButton.setFixedWidth(150)
        self.exportButton.setIcon(qt.QIcon("{0}/export-csv.png".format(SlicerUtil.CIP_ICON_DIR)))
        self.exportButton.setIconSize(qt.QSize(24,24))
        self.mainLayout.addWidget(self.exportButton)

        self.removeButton = ctk.ctkPushButton()
        self.removeButton.text = "Clean cache"
        self.removeButton.setIcon(qt.QIcon("{0}/delete.png".format(SlicerUtil.CIP_ICON_DIR)))
        self.removeButton.setIconSize(qt.QSize(24,24))
        self.removeButton.setFixedWidth(150)
        self.mainLayout.addWidget(self.removeButton)

        self.exportButton.connect('clicked()', parent.onExport)
        self.removeButton.connect('clicked()', parent.onRemoveStoredData)


    def load(self, columnNames, data):
        """ Load all the information displayed in the table
        :param columnNames: list of column names
        :param data: list of rows, each of them with one value per column
        """
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

        self.tableView.sortByColumn(0, 1)   # Sort by Date Descending

