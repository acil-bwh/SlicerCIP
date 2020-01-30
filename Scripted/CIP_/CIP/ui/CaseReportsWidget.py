import os, time, pprint, logging
from collections import OrderedDict

import qt, ctk, slicer

from CIP.logic import EventsTrigger
from CIP.logic.SlicerUtil import SlicerUtil
from CIP.ui.CollapsibleMultilineText import CollapsibleMultilineText

class CaseReportsWidget(EventsTrigger):
    # Events triggered by the widget
    EVENT_SAVE_BUTTON_CLICKED = 1
    EVENT_SHOW_REPORT = 2
    EVENT_HIDE_REPORT = 3
    EVENT_CLEAN_CACHE = 4
    EVENT_PRINT_BUTTON_CLICKED = 5

    @property
    def TIMESTAMP_COLUMN_NAME(self):
        return self.logic.TIMESTAMP_COLUMN_KEY

    def __init__(self, dbTableName, columnsDict, parentWidget = None, dbFilePath=None):
        """
        Widget constructor
        :param dbTableName: name of the table that will store the information of the module
        :param columnsDict: dictionary of colummKey-ColumnDescription (note that column keys cannot contain special
        characters, white spaces, etc.)
        :param parentWidget: widget where this ReportsWidget will be inserted
        :param dbFilePath: full path of the file that will store the database that is using the widget.
                           by default, it will be in the settings folder
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
        self.logic = CaseReportsLogic(dbTableName, columnsDict, dbFilePath=dbFilePath)
        self.__initEvents__()
        self.reportWindow = CaseReportsWindow(self)
        self.reportWindow.objectName = "caseReportsWindow"

    @property
    def showWarningWhenWrongColumns(self):
        return self._showWarningWhenIncompleteColumns_

    def setup(self):
        self.mainFrame = qt.QFrame()
        frameLayout = qt.QGridLayout()
        self.mainFrame.setLayout(frameLayout)
        self.layout.addWidget(self.mainFrame)

        self.saveButton = ctk.ctkPushButton()
        self.saveButton.text = "Save"
        self.saveButton.toolTip = "Save the current table"
        self.saveButton.objectName = "reportSaveButton"
        self.saveButton.setIcon(qt.QIcon("{0}/Save.png".format(SlicerUtil.CIP_ICON_DIR)))
        self.saveButton.setIconSize(qt.QSize(24, 24))
        frameLayout.addWidget(self.saveButton, 0, 0)

        self.openButton = ctk.ctkPushButton()
        self.openButton.text = "Open"
        self.openButton.toolTip = "Open all the results saved"
        self.openButton.objectName = "reportOpenButton"
        self.openButton.setIcon(qt.QIcon("{0}/open_file.png".format(SlicerUtil.CIP_ICON_DIR)))
        self.openButton.setIconSize(qt.QSize(24,24))
        frameLayout.addWidget(self.openButton, 0, 1)

        self.exportButton = ctk.ctkPushButton()
        self.exportButton.text = "Export"
        self.exportButton.toolTip = "Export all the saved results to a CSV file"
        self.exportButton.objectName = "reportExportButton"
        self.exportButton.setIcon(qt.QIcon("{0}/export-csv.png".format(SlicerUtil.CIP_ICON_DIR)))
        self.exportButton.setIconSize(qt.QSize(24,24))
        frameLayout.addWidget(self.exportButton, 0, 2)

        self.removeButton = ctk.ctkPushButton()
        self.removeButton.setIcon(qt.QIcon("{0}/delete.png".format(SlicerUtil.CIP_ICON_DIR)))
        self.removeButton.setIconSize(qt.QSize(24,24))
        self.removeButton.text = "Clean cache"
        frameLayout.addWidget(self.removeButton, 0, 3)

        self.printButton = ctk.ctkPushButton()
        self.printButton.text = "Print"
        self.printButton.toolTip = "Print report"
        self.printButton.objectName = "reportPrintButton"
        self.printButton.setIcon(qt.QIcon("{0}/print.png".format(SlicerUtil.CIP_ICON_DIR)))
        self.printButton.setIconSize(qt.QSize(24,24))
        self.printButton.setVisible(False)  # By default, this button will be hidden
        frameLayout.addWidget(self.printButton, 0, 4)

        self.additionalComentsLabel = qt.QLabel("Additional comments:")
        self.additionalComentsLabel.setStyleSheet("margin-top: 3px")
        frameLayout.addWidget(self.additionalComentsLabel, 1, 0, 1, 2)
        self.additionalComentsTextEdit = CollapsibleMultilineText()
        frameLayout.addWidget(self.additionalComentsTextEdit, 1, 1, 1, 3)

        self.openButton.connect('clicked()', self.onShowStoredData)
        self.saveButton.connect('clicked()', self.onSave)
        self.exportButton.connect('clicked()', self.onExport)
        self.printButton.connect('clicked()', self.onPrintReport)
        self.removeButton.connect('clicked()', self.onRemoveStoredData)

    def cleanup(self):
        self.reportWindow.cleanup()

    def __initEvents__(self):
        """Init all the structures required for events mechanism"""
        events = [attr for attr in dir(self) if not callable(getattr(self, attr)) and attr.startswith("EVENT_")]
        for i in range(len(events)):
            events[i] = eval('self.{}'.format(events[i]))
        self.setEvents(events)

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
        s = self.additionalComentsTextEdit.toPlainText()
        s = s.replace("\r\n", "  ").replace("\n", "  ")
        kwargs[self.logic.ADDITIONAL_COMMENTS_COLUMN_KEY] = s
        return self.logic.insertRow(**kwargs)

    def enableSaveButton(self, enabled):
        """ Enable/Disable the "Save" button
        :param enabled: True/False
        """
        self.saveButton.setEnabled(enabled)

    def showPrintButton(self, visible):
        """ Show/Hide the Print Button
        :param enabled: True/False
        """
        self.printButton.setVisible(visible)

    # def showSaveButton(self, show):
    #     """ Show/hide the save button (it can be hidden when the data are saved obligatory)
    #     :param show: show == True
    #     """
    #     self.saveButton.setVisible(show)

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

    @staticmethod
    def getColumnKeysNormalizedDictionary(columnList):
        """
        From a list of column descriptive names, build a dictionary ColumnKey-ColumnDescription, where ColumnDescription
        will contain the provided columnList and ColumnKey will be the normalized (removing non-alphanumeric symbols)
        :param columnList: list of column descriptions
        :return: OrderedDictionary of columnKey-ColumnDescription
        """
        return CaseReportsLogic.getColumnKeysNormalized(columnList)

    ###############
    # EVENTS
    def onSave(self):
        """ Trigger the event of saving some stored data.
        The widget just triggers the signal, it is the responsibility of the parent to save the desired data
        :return:
        """
        self.triggerEvent(self.EVENT_SAVE_BUTTON_CLICKED)

    def onExpandRows(self):
        self.reportWindow.tableView.resizeRowsToContents()

    def onShowStoredData(self):
        """ Show the dialog window with all the information stored so far
        :return:
        """
        # self.reportWindow.load(self.logic.columnNamesExtended, self.logic.loadValues())

        self.reportWindow.show()
        self.triggerEvent(self.EVENT_SHOW_REPORT)

    def onExport(self):
        """ Export the current csv file to a customized and formatted file
        :return:
        """
        fileName = qt.QFileDialog.getSaveFileName(slicer.util.mainWindow(), "Export to CSV file")
        if fileName:
            self.logic.exportCSV(fileName)
            qt.QMessageBox.information(slicer.util.mainWindow(), 'Data exported', 'The data were exported successfully')

    def onPrintReport(self):
        self.triggerEvent(self.EVENT_PRINT_BUTTON_CLICKED)

    def onRemoveStoredData(self):
        """ Remove the current csv file
        :return:
        """
        if (qt.QMessageBox.question(slicer.util.mainWindow(), 'Remove stored data',
                'Are you sure you want to clear the stored data? (This operation cannot be undone)',
                qt.QMessageBox.Yes|qt.QMessageBox.No)) == qt.QMessageBox.Yes:
            self.logic.clear()
            qt.QMessageBox.information(slicer.util.mainWindow(), 'Data removed', 'The data were removed successfully')
            self.triggerEvent(self.EVENT_CLEAN_CACHE)


#############################
##
class CaseReportsLogic(object):
    def __init__(self, dbTableName, columnsDict, dbFilePath=None):
        """
        Constructor
        :param dbTableName: name of the table in the database
        :param columnsDict: dictionary of column key-column value
        :param dbFilePath: path to the file that will store the data. By default it will be
                            in the CIP settings folder
        """
        self._dbFilePath_ = SlicerUtil.modulesDbPath() if dbFilePath is None else dbFilePath
        self._dbTableName_ = dbTableName
        logging.debug("Module storage in {}-{}".format(dbFilePath, dbTableName))
        # We need the dictionary to be ordered for the table node
        self._initTableNode_()
        if isinstance(columnsDict, OrderedDict):
            self.columnsDict = columnsDict
        else:
            self.columnsDict = OrderedDict(columnsDict)
        self._initColumns_()

        # self.__columnNames__ = columnNames
        self.showWarningWhenIncompleteColumns = True

    @property
    def TIMESTAMP_COLUMN_KEY(self):
        return "Timestamp"

    @property
    def ADDITIONAL_COMMENTS_COLUMN_KEY(self):
        return "AdditionalComments"

    @property
    def _columnKeys_(self):
        return list(self.columnsDict.keys())

    @property
    def _columnDescriptions_(self):
        return list(self.columnsDict.values())

    @property
    def reservedColumnKeys(self):
        return (self.TIMESTAMP_COLUMN_KEY, self.ADDITIONAL_COMMENTS_COLUMN_KEY)

    def _initTableNode_(self):
        """
        Initialize the vtkMRMLTableSQLiteStorageNode and add it to the scene
        """
        self.tableStorageNode = slicer.vtkMRMLTableSQLiteStorageNode()
        slicer.mrmlScene.AddNode(self.tableStorageNode)
        self.tableStorageNode.SetFileName(self._dbFilePath_)
        self.tableStorageNode.SetTableName(self._dbTableName_)
        self.tableNode = slicer.vtkMRMLTableNode()
        slicer.mrmlScene.AddNode(self.tableNode)
        self.tableNode.SetName("{}_table".format(self._dbTableName_))
        self.tableNode.SetAndObserveStorageNodeID(self.tableStorageNode.GetID())
        if os.path.isfile(self._dbFilePath_):
            # Read the previous data
            self.tableStorageNode.ReadData(self.tableNode)
        else:
            logging.info("The storage database has not been created yet")

    def _initColumns_(self):
        """
        Create the list of columns in the tableNode based on the existing columns dictionary.
        If the database already existed, create new columns if necessary
        :param columnsDict:
        """
        for colKey, colDesc in list(self.columnsDict.items()):
            if not colKey.isalnum():
                raise Exception("Column {} is not alphanumeric. The column keys can contain only letters and numbers."
                                .format(colKey))
            if colKey in self.reservedColumnKeys:
                raise Exception("One of the columns is named as one of the reserved fields: {}".format(
                    self.reservedColumnKeys))

        table = self.tableNode.GetTable()
        if self.tableNode.GetNumberOfColumns() == 0:
            # Empty table
            # Add columns
            for value in self.columnsDict.values():
                col = self.tableNode.AddColumn()
                # We will keep the "friendly" name of the column until the moment we are saving in db
                col.SetName(value)
            SlicerUtil.logDevelop("Table {} initialized from scratch with the following columns: {}".format(
                self._dbTableName_, self.columnsDict), includePythonConsole=True)
            tableColumnKeys = list(self.columnsDict.keys())
        else:
            # The table already has previously existing columns. Check if new columns were introduced
            tableColumnKeys = []
            for i in range(self.tableNode.GetNumberOfColumns()):
                tableColumnKeys.append(table.GetColumnName(i))

            for key in self.columnsDict.keys():
                if key not in tableColumnKeys:
                    # Add a new column to the table
                    col = self.tableNode.AddColumn()
                    col.SetName(key)
                    SlicerUtil.logDevelop("New column added to the table {} in the database: {}".
                                          format(self._dbTableName_, key), includePythonConsole=True)

        # Add obligatory columns
        for key in self.reservedColumnKeys:
            if key not in self.columnsDict:
                self.columnsDict[key] = key
            if key not in tableColumnKeys:
                col = self.tableNode.AddColumn()
                col.SetName(key)


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

    def hasColumn(self, columnKeyOrDescription):
        """
        Return True if the column specified is in the list of columnn keys or column descriptions
        :param columnKeyOrDescription:
        :return: Boolean
        """
        return columnKeyOrDescription in self._columnKeys_ or columnKeyOrDescription in self._columnDescriptions_

    def getColumnKey(self, columnKeyOrDescription):
        """
        Get a column key. If columnKeyOrDescription is a column key, just return that value. If it matches to any of
        the column descriptions, return the corresponding column key
        :param columnKeyOrDescription:
        :return: String or None if the column was not found
        """
        for key, value in self.columnsDict.items():
            if columnKeyOrDescription in (key, value):
                return key
        return None

    def insertRow(self, **kwargs):
        """ Save a new row of information in the current db file that stores the data.
        Each entry can contain ColumnKey-Value or ColumnDescription-Value
        :param kwargs: dictionary of values
        :return: 0 = OK; 1=Warning (when there are columns not expected)
        """
        result = 0
        # Check that we have all the "columns"
        for key in kwargs:
            if not self.hasColumn(key):
                logging.warning("WARNING: Column {} is not included in the list of columns and therefore it will NOT be saved".
                      format(key))
                result = 1

        rowIndex = self.tableNode.AddEmptyRow()
        table = self.tableNode.GetTable()

        # Temporarily rename the columns so that the db saves the normalized names columns
        keys = list(self.columnsDict.keys())
        for i in range(table.GetNumberOfColumns()):
            # # Sanity check
            # assert table.GetColumn(i).GetName() == self.columnsDict[keys[i]], "Column mismatch (table=={}; Dict=={})".format(
            #     table.GetColumn(i).GetName(), self.columnsDict[keys[i]])
            # Change the name
            table.GetColumn(i).SetName(keys[i])
        table.Modified()

        try:
            for key, value in kwargs.items():
                if value is not None:
                    for i in range(0, len(self.columnsDict)):
                        colName = table.GetColumnName(i)
                        if colName == self.TIMESTAMP_COLUMN_KEY:
                            self.tableNode.SetCellText(rowIndex, i, time.strftime("%Y/%m/%d %H:%M:%S"))
                        elif colName == self.getColumnKey(key):
                            value = str(value)  # The table node only allows text
                            self.tableNode.SetCellText(rowIndex, i, value)
                            break
        except Exception as ex:
            # Remove the row
            self.tableNode.RemoveRow(rowIndex)
            raise ex

        # Persist the info
        self.tableStorageNode.WriteData(self.tableNode)
        # Return to the original column names
        for i in range(table.GetNumberOfColumns()):
            # Change the name
            table.GetColumn(i).SetName(self.columnsDict[keys[i]])
        table.Modified()
        # Notify GUI
        self.tableNode.Modified()
        if result == 1:
            logging.warning("Current list of columns keys: {}".format(self._columnKeys_))
            logging.warning("Current list of columns descriptions: {}".format(self._columnDescriptions_))
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

    @staticmethod
    def getColumnKeysNormalized(columnList):
        """
        From a list of column descriptive names, build a dictionary ColumnKey-ColumnDescription, where ColumnDescription
        will contain the provided columnList and ColumnKey will be the normalized (removing non-alphanumeric symbols)
        :param columnList: list of column descriptions
        :return: OrderedDictionary of columnKey-ColumnDescription
        """
        d = OrderedDict()
        for column in columnList:
            key = ""
            for c in column:
                if c.isalnum():
                    key += c
            d[key] = column
        return d
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
        :return: dictionary with the information of a single row
        """
        rows = self.tableNode.GetNumberOfRows()
        if rows == 0:
            # Only header. No data
            return None
        columns = self.tableNode.GetNumberOfColumns()
        values = {}
        table = self.tableNode.GetTable()
        for i in range(columns):
            col = table.GetColumn(i)
            key = self.getColumnKey(col.GetName())
            values[key] = self.tableNode.GetCellText(rows-1, i)
        return values

    def findLastMatchRow(self, columnName, value):
        """ Go over all the rows in the CSV until it finds the value "value" in the column "columnName"
        :param columnIndex: index of the column that we are comparing. This index will NOT include the obligatory timestamp field
        :param value:
        :return: row with the first match or None if it' not found
        """
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
        for i in range(rows-1, -1, -1):
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

        self.expandRowsButton = ctk.ctkPushButton()
        self.expandRowsButton.text = "Expand rows"
        self.expandRowsButton.toolTip = "Change the height of the rows to show/hide all the multiline data"
        self.expandRowsButton.setFixedWidth(150)
        self.expandRowsButton.setIcon(qt.QIcon("{0}/reload.png".format(SlicerUtil.CIP_ICON_DIR)))
        self.expandRowsButton.setIconSize(qt.QSize(24, 24))
        self.mainLayout.addWidget(self.expandRowsButton)

        self.exportButton = ctk.ctkPushButton()
        self.exportButton.text = "Export"
        self.exportButton.toolTip = "Export to a CVS file"
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

        self.expandRowsButton.connect('clicked()', parent.onExpandRows)
        self.exportButton.connect('clicked()', parent.onExport)
        self.removeButton.connect('clicked()', parent.onRemoveStoredData)

    def cleanup(self):
        self.tableView.setMRMLTableNode(None)
        self.expandRowsButton.disconnect('clicked()')
        self.exportButton.disconnect('clicked()')
        self.removeButton.disconnect('clicked()')


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

    # def load(self, columnNames, data):
    #     """ Load all the information displayed in the table
    #     :param columnNames: list of column names
    #     :param data: list of rows, each of them with one value per column
    #     """
    #     columns = []
    #     for colName in columnNames:
    #         column = self.tableNode.AddColumn()
    #         column.SetName(colName)
    #         column.InsertNextValue("my value {}".format(colName))
    #
    #     self.tableView.setMRMLTableNode(self.tableNode)
    #     self.tableNode.Modified()
    #     return
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

