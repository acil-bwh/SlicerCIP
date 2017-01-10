import csv, os, time, pprint, logging
import qt, ctk, slicer

from CIP.logic import EventsTrigger
from CIP.logic.SlicerUtil import SlicerUtil

class CaseReportsWidget(EventsTrigger):
    # Events triggered by the widget
    EVENT_SAVE_BUTTON_CLICKED = 1
    EVENT_SHOW_REPORT = 2
    EVENT_HIDE_REPORT = 3
    EVENT_CLEAN_CACHE = 4

    @property
    def TIMESTAMP_COLUMN_NAME(self):
        return self.logic.TIMESTAMP_COLUMN_NAME

    def __init__(self, moduleName, columnNames, parentWidget = None, filePreffix=""):
        """
        Widget constructor
        :param moduleName:
        :param columnNames: list of column names
        :param parentWidget:
        :param filePreffix:
        """
        EventsTrigger.__init__(self)
        
        if not parentWidget:
            self.parent = slicer.qMRMLWidget()
            self.parent.setLayout(qt.QVBoxLayout())
            self.parent.setMRMLScene(slicer.mrmlScene)
        else:
            self.parent = parentWidget
        self.layout = self.parent.layout()

        self._showWarningWhenIncompleteColumns_ = True
        self.logic = CaseReportsLogic(moduleName, columnNames, filePreffix)
        self.__initEvents__()
        self.reportWindow = CaseReportsWindow(self)
        self.reportWindow.objectName = "caseReportsWindow"

    @property
    def showWarningWhenWrongColumns(self):
        return self._showWarningWhenIncompleteColumns_

    def setup(self):
        self.saveButton = ctk.ctkPushButton()
        self.saveButton.text = "Save"
        self.saveButton.objectName = "reportSaveButton"
        self.saveButton.setIcon(qt.QIcon("{0}/Save.png".format(SlicerUtil.CIP_ICON_DIR)))
        self.saveButton.setIconSize(qt.QSize(24, 24))
        self.layout.addWidget(self.saveButton)

        self.openButton = ctk.ctkPushButton()
        self.openButton.text = "Open"
        self.openButton.objectName = "reportOpenButton"
        self.openButton.setIcon(qt.QIcon("{0}/open_file.png".format(SlicerUtil.CIP_ICON_DIR)))
        self.openButton.setIconSize(qt.QSize(24,24))

        self.layout.addWidget(self.openButton)

        self.exportButton = ctk.ctkPushButton()
        self.exportButton.text = "Export"
        self.exportButton.objectName = "reportExportButton"
        self.exportButton.setIcon(qt.QIcon("{0}/export-csv.png".format(SlicerUtil.CIP_ICON_DIR)))
        self.exportButton.setIconSize(qt.QSize(24,24))
        self.layout.addWidget(self.exportButton)

        self.removeButton = ctk.ctkPushButton()
        self.removeButton.setIcon(qt.QIcon("{0}/delete.png".format(SlicerUtil.CIP_ICON_DIR)))
        self.removeButton.setIconSize(qt.QSize(24,24))
        self.removeButton.text = "Clean cache"
        self.layout.addWidget(self.removeButton)

        self.saveButton.connect('clicked()', self.onSave)
        self.exportButton.connect('clicked()', self.onExport)
        self.openButton.connect('clicked()', self.onShowStoredData)
        self.removeButton.connect('clicked()', self.onRemoveStoredData)

    def __initEvents__(self):
        """Init all the structures required for events mechanism"""
        self.setEvents([self.EVENT_SAVE_BUTTON_CLICKED, self.EVENT_SHOW_REPORT, self.EVENT_CLEAN_CACHE])

    # def setColumnNames(self, columnNames):
    #     """ Set the column names that will saved every time the user clicks "Save" button
    #     :param columnNames:
    #     """
    #     self.logic.columnNames = columnNames

    def insertRow(self, **kwargs):
        """ Save a record.
        The function will expect to be invoked with key-value parameters with the name of the columns.
        Ex: self.reportsWidget.insertRow(
                caseId = caseName,
                regionType = stat.LabelCode,
                label = stat.LabelDescription)
        :param kwargs:
        :return: 0 = OK; 1 = Warning
        """
        # Add the values in the right order (there are not obligatory fields)
        # Insert the default timestamp
        return self.logic.insertRow(**kwargs)

    def enableSaveButton(self, enabled):
        """ Enable/Disable the "Save" button
        :param enabled: True/False
        """
        self.saveButton.setEnabled(enabled)

    def showSaveButton(self, show):
        """ Show/hide the save button (it can be hidden when the data are saved obligatory)
        :param show: show == True
        """
        self.saveButton.setVisible(show)

    def showWarnigMessages(self, showMessages):
        """ Show/Hide warning messages when the columns passed when saving some values are not exactly the ones expected
        :param showMessages: True/False
        """
        self._showWarningWhenIncompleteColumns_ = showMessages
        self.logic.showWarningWhenIncompleteColumns = showMessages

    def hideReportsWindow(self):
        """ Hide the reports window
        """
        self.reportWindow.hide()
        self.triggerEvent(self.EVENT_HIDE_REPORT)

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
        fileName = qt.QFileDialog.getSaveFileName(slicer.util.mainWindow(), "Export to CSV file")
        if fileName:
            self.logic.exportCSV(fileName)
            qt.QMessageBox.information(slicer.util.mainWindow(), 'Data exported', 'The data were exported successfully')

    def onShowStoredData(self):
        """ Show the dialog window with all the information stored so far
        :return:
        """
        # self.reportWindow.load(self.logic.columnNamesExtended, self.logic.loadValues())
        self.reportWindow.show()
        self.triggerEvent(self.EVENT_SHOW_REPORT)

    def onRemoveStoredData(self):
        """ Remove the current csv file
        :return:
        """
        if (qt.QMessageBox.question(slicer.util.mainWindow(), 'Remove stored data',
                'Are you sure you want to clear the saved csv data?',
                qt.QMessageBox.Yes|qt.QMessageBox.No)) == qt.QMessageBox.Yes:
            self.logic.clear()
            qt.QMessageBox.information(slicer.util.mainWindow(), 'Data removed', 'The data were removed successfully')
            self.triggerEvent(self.EVENT_CLEAN_CACHE)


#############################
##
class CaseReportsLogic(object):
    def __init__(self, moduleName, columnNames, filePreffix):
        self.__moduleName__ = moduleName
        p = SlicerUtil.getSettingsDataFolder(moduleName)
        if filePreffix != "":
            self._dbFilePath_ = os.path.join(p, "{0}.{1}.sqlitestorage.db".format(filePreffix, moduleName))
        else:
            self._dbFilePath_ = os.path.join(p, moduleName + ".sqlitestorage.db")
        logging.debug("Module {} storage in {}".format(moduleName, self._dbFilePath_))
        self._initTableNode_()

        if os.path.isfile(self._dbFilePath_):
            # Read the previous data
            self.tableStorageNode.ReadData(self.tableNode)

        self._checkColumns_(columnNames)
        # self.__columnNames__ = columnNames
        self.showWarningWhenIncompleteColumns = True



    @property
    def TIMESTAMP_COLUMN_NAME(self):
        return "Timestamp"

    def _initTableNode_(self):
        self.tableStorageNode = slicer.vtkMRMLTableSQLiteStorageNode()
        slicer.mrmlScene.AddNode(self.tableStorageNode)
        self.tableStorageNode.SetFileName(self._dbFilePath_)
        self.tableStorageNode.SetTableName(self.__moduleName__)
        self.tableNode = slicer.vtkMRMLTableNode()
        self.tableNode.SetName("{}_table".format(self.__moduleName__))
        self.tableNode.SetAndObserveStorageNodeID(self.tableStorageNode.GetID())

    def _checkColumns_(self, newColumnNames):
        """
        Create the list of columns.
        If the database already existed, create new columns if necessary
        :param newColumnNames:
        """
        self._columns_ = []
        table = self.tableNode.GetTable()
        if self.tableNode.GetNumberOfColumns() == 0:
            # Empty table. Add the timestamp column and the rest of the columns
            self._columns_.append(self.TIMESTAMP_COLUMN_NAME)
            col = self.tableNode.AddColumn()
            col.SetName(self.TIMESTAMP_COLUMN_NAME)
            for columnName in newColumnNames:
                col = self.tableNode.AddColumn()
                col.SetName(columnName)
                self._columns_.append(columnName)
            logging.info("New table created with the following column names: {}".format(self._columns_))
        else:
            for i in range(self.tableNode.GetNumberOfColumns()):
                self._columns_.append(table.GetColumnName(i))
            for columnName in newColumnNames:
                if columnName not in self._columns_:
                    # Add a new column
                    col = self.tableNode.AddColumn()
                    col.SetName(columnName)
                    self._columns_.append(columnName)
                    logging.info("New column added to the database: {}".format(columnName))


    @property
    def columnNames(self):
        return self._columns_
    # @columnNames.setter
    # def columnNames(self, value):
    #     self.__columnNames__ = value

    # @property
    # def columnNamesExtended(self):
    #     """ Column names with the date (timestamp) added as the first column
    #     :return:
    #     """
    #     columns = [self.TIMESTAMP_COLUMN_NAME]
    #     columns.extend(self.columnNames)
    #     return columns

    @property
    def dbFilePath(self):
        """ Path of the file that contains all the data
        :return: Path of the file that contains all the data
        """
        return self._dbFilePath_


    def insertRow(self, **kwargs):
        """ Save a new row of information in the current csv file that stores the data  (from a dictionary of items)
        :param kwargs: dictionary of values
        :return: 0 = OK; 1=Warning
        """
        result = 0
        # Check that we have all the "columns"
        # if len(kwargs) != len(self.columnNames) and self.showWarningWhenIncompleteColumns:
        #     print("WARNING. There is a wrong number of arguments in ReportsWidget. ")
        #     print("Current columns: ")
        #     pprint.pprint(self.columnNames)
        #     print("Total: {0}".format(len(self.columnNames)))
        #     print("Args passed: ")
        #     pprint.pprint(kwargs)
        #     print("Total: {0}".format(len(kwargs)))
        #     result = 1

        for key in kwargs:
            if key not in self.columnNames:
                print("WARNING: Column {0} is not included in the list of columns and therefore it will NOT be saved".
                      format(key))
                result = 1

        rowIndex = self.tableNode.AddEmptyRow()
        table = self.tableNode.GetTable()

        try:
            # Insert the timestamp
            self.tableNode.SetCellText(rowIndex, 0, time.strftime("%Y/%m/%d %H:%M:%S"))
            # Rest of the values
            for i in range(1, len(self.columnNames)):
                colName = table.GetColumnName(i)
                if colName in kwargs:
                    elem = kwargs[colName]
                    if elem is not None:
                        elem = str(elem)    # The table node only allows text
                    self.tableNode.SetCellText(rowIndex, i, elem)
        except Exception as ex:
            # Remove the row
            self.tableNode.RemoveRow(rowIndex)
            raise ex
        # Persist the info
        self.tableStorageNode.WriteData(self.tableNode)

        # Notify GUI
        self.tableNode.Modified()
        return result

    def exportCSV(self, filePath):
        """ Export the information stored in the current csv file that is storing the data to a better
        formatted csv file in a location chosen by the user
        :param filePath: destination of the file (full path)
        :return:
        """
        # Use a regular TableStorageNode to export to CSV
        storageNode = slicer.vtkMRMLTableStorageNode()
        storageNode.SetFileName(filePath)
        storageNode.WriteData(self.tableNode)
        return True
        # if os.path.exists(self.dbFilePath):
        #     with open(self.dbFilePath, 'r+b') as csvfileReader:
        #         reader = csv.reader(csvfileReader)
        #         with open(filePath, 'a+b') as csvfileWriter:
        #             writer = csv.writer(csvfileWriter)
        #             writer.writerow(self.columnNamesExtended)
        #             for row in reader:
        #                 writer.writerow(row)
        #     return True
        # else:
        #     return False

    # def loadValues(self):
    #     """ Load all the information stored in the csv file
    #     :return: list of lists (rows/colums)
    #     """
    #     data = []
    #     if os.path.exists(self.dbFilePath):
    #         with open(self.dbFilePath, 'r+b') as csvfileReader:
    #             reader = csv.reader(csvfileReader)
    #             for row in reader:
    #                 data.append(row)
    #     return data

    def getLastRow(self):
        """ Return the last row of data that was stored in the file
        :return: list with the information of a single row
        """
        # if os.path.exists(self.dbFilePath):
        #     with open(self.dbFilePath, 'r+b') as csvfileReader:
        #         reader = csv.reader(csvfileReader)
        #         #return reader.next()
        #         # Read all the information of the file to iterate in reverse order
        #         rows = [row for row in reader]
        #         return rows.pop()
        # # Error case
        # return None
        rows = self.tableNode.GetNumberOfRows()
        if rows == 0:
            # Only header. No data
            return None
        columns = self.tableNode.GetNumberOfColumns()
        values = []
        for i in range(columns):
            values.append(self.tableNode.GetCellText(rows-1, i))
        return values

    def findLastMatchRow(self, columnName, value):
        """ Go over all the rows in the CSV until it finds the value "value" in the column "columnName"
        :param columnIndex: index of the column that we are comparing. This index will NOT include the obligatory timestamp field
        :param value:
        :return: row with the first match or None if it' not found
        """
        # TODO: REPLACE THIS
        # if os.path.exists(self.dbFilePath):
        #     with open(self.dbFilePath, 'r+b') as csvfileReader:
        #         reader = csv.reader(csvfileReader)
        #         rows = [row for row in reader if row[columnIndex + 1] == value]
        #         # print("DEBUG. Rows:")
        #         # import pprint
        #         # pprint.pprint(rows)
        #         if len(rows) > 0:
        #             # Get the last element
        #             return rows.pop()
        # # Not found
        # return None
        columns = self.tableNode.GetNumberOfColumns()
        colIndex = -1
        table = self.tableNode.GetTable()
        for i in range(columns):
            if table.GetColumnName(i) == columnName:
                colIndex = i
                break
        if colIndex == -1:
            raise Exception("Column not found: {}".format(columnName))
        rows = self.tableNode.GetNumberOfRows()
        for i in range(rows-1, stop=-1, step=-1):
            if self.tableNode.GetCellText(i, colIndex) == str(value):
                # Return the whole row
                values = []
                for c in range(columns):
                    values.append(self.tableNode.GetCellText(i, c))
                return values
        return None     # Not found


    def clear(self):
        """ Remove all the data content """
        while self.tableNode.GetNumberOfRows() > 0:
            self.tableNode.RemoveRow(0)







class CaseReportsWindow(qt.QWidget):
    """ Class that show a window dialog with a table that will display all the information loaded
    for the state of this module
    """
    def __init__(self, parent):
        """
        Window that display the data
        :param parent: CaseReportsWidget object
        """
        super(CaseReportsWindow, self).__init__()

        self.mainLayout = qt.QVBoxLayout(self)
        self.setLayout(self.mainLayout)
        self.resize(400, 300)

        self.label = qt.QLabel("Data stored in the module: ")
        self.label.setStyleSheet("margin: 10px 0 15px 0")
        self.mainLayout.addWidget(self.label)

        self.tableView = slicer.qMRMLTableView()
        self.tableView.setColumnWidth(0,125)
        self.tableView.setMRMLTableNode(parent.logic.tableNode)
        self.tableView.setFirstRowLocked(True)  # First row will be headers
        self.tableView.setSortingEnabled(True)

        self.tableView.setSizePolicy(qt.QSizePolicy.Expanding, qt.QSizePolicy.Expanding)
        self.mainLayout.addWidget(self.tableView)

        self.exportButton = ctk.ctkPushButton()
        self.exportButton.text = "Export"
        self.exportButton.setFixedWidth(150)
        self.exportButton.setIcon(qt.QIcon("{0}/export-csv.png".format(SlicerUtil.CIP_ICON_DIR)))
        self.exportButton.setIconSize(qt.QSize(24,24))
        self.mainLayout.addWidget(self.exportButton)

        self.removeButton = ctk.ctkPushButton()
        self.removeButton.text = "Clean"
        self.removeButton.setIcon(qt.QIcon("{0}/delete.png".format(SlicerUtil.CIP_ICON_DIR)))
        self.removeButton.setIconSize(qt.QSize(24,24))
        self.removeButton.setFixedWidth(150)
        self.mainLayout.addWidget(self.removeButton)

        self.exportButton.connect('clicked()', parent.onExport)
        self.removeButton.connect('clicked()', parent.onRemoveStoredData)


    # def load(self, columnNames, data):
    #     """ Load all the information displayed in the table
    #     :param columnNames: list of column names
    #     :param data: list of rows, each of them with one value per column
    #     """
    #     self.items = []
    #
    #     self.statisticsTableModel = qt.QStandardItemModel()
    #     self.tableView.setModel(self.statisticsTableModel)
    #     self.tableView.verticalHeader().visible = False
    #     self.tableView.sortingEnabled = True
    #
    #     policy = self.tableView.sizePolicy
    #     policy.setVerticalPolicy(qt.QSizePolicy.Expanding)
    #     policy.setHorizontalPolicy(qt.QSizePolicy.Expanding)
    #     policy.setVerticalStretch(0)
    #     self.tableView.setSizePolicy(policy)
    #
    #     # Header
    #     self.statisticsTableModel.setHorizontalHeaderLabels(columnNames)
    #
    #     for row in range(len(data)):
    #         rowData = data[row]
    #         for col in range(len(rowData)):
    #             item = qt.QStandardItem()
    #             item.setData(data[row][col], qt.Qt.DisplayRole)
    #             item.setEditable(False)
    #             self.statisticsTableModel.setItem(row, col,item)
    #             self.items.append(item)
    #
    #     self.tableView.sortByColumn(0, 1)   # Sort by Date Descending

    def load(self, columnNames, data):
        """ Load all the information displayed in the table
        :param columnNames: list of column names
        :param data: list of rows, each of them with one value per column
        """
        columns = []
        for colName in columnNames:
            column = self.tableNode.AddColumn()
            column.SetName(colName)
            column.InsertNextValue("my value {}".format(colName))

        self.tableView.setMRMLTableNode(self.tableNode)
        self.tableNode.Modified()
        return
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
