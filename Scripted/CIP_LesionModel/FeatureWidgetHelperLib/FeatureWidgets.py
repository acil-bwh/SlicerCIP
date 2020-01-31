from __main__ import vtk, qt, ctk, slicer
import string
import collections
import FeatureWidgetHelperLib


class CheckableTabsWidget(qt.QTabWidget):
    """ Class that contains all the tabs correspondign to the main categories
    """
    def __init__(self, parent=None):
        super(CheckableTabsWidget, self).__init__(parent)
        self.featureClassFeatureWidgets = collections.OrderedDict()

        # hack ( QTabWidget.setTabBar() and tabBar() are protected )
        self.tab_bar = self.findChildren(qt.QTabBar)[0]

        # Bold font style
        self.boldFont = qt.QFont()
        self.boldFont.setBold(True)

        self.tab_bar.setFont(self.boldFont)
        self.tab_bar.setContextMenuPolicy(3)
        self.tab_bar.installEventFilter(self)

    def addTab(self, widget, featureClass, featureWidgets, checkStatus=True):
        qt.QTabWidget.addTab(self, widget, featureClass)

        checkBox = FeatureWidgetHelperLib.FeatureWidget()
        checkBox.Setup(featureName=featureClass, featureClassFlag=True, checkStatus=checkStatus)
        self.featureClassFeatureWidgets[featureClass] = checkBox

        self.tab_bar.setTabButton(self.tab_bar.count - 1, qt.QTabBar.LeftSide, checkBox)
        self.connect(checkBox, qt.SIGNAL('stateChanged(int)'),
                     lambda checkState: self.stateChanged(checkBox, checkState, featureWidgets))

    def isChecked(self, index):
        return self.tab_bar.tabButton(index, qt.QTabBar.LeftSide).checkState() != 0

    def setCheckState(self, index, checkState):
        self.tab_bar.tabButton(index, qt.QTabBar.LeftSide).setCheckState(checkState)

    def stateChanged(self, checkBox, checkState, featureWidgets):
        # uncheck all checkboxes in QObject # may not need to pass list?
        index = list(self.featureClassFeatureWidgets.values()).index(checkBox)
        if checkState == 0:
            for widget in featureWidgets:
                widget.checked = False
        elif checkState == 2:
            for widget in featureWidgets:
                widget.checked = True

    def eventFilter(self, object, event):
        # context menu request (right-click) on QTabBar is forwarded to the QCheckBox (FeatureWidget)
        if object == self.tab_bar and event.type() == qt.QEvent.ContextMenu:
            tabIndex = object.tabAt(event.pos())
            pos = list(self.featureClassFeatureWidgets.values())[tabIndex].mapFrom(self.tab_bar, event.pos())

            if tabIndex > -1:
                qt.QCoreApplication.sendEvent(list(self.featureClassFeatureWidgets.values())[tabIndex],
                                              qt.QContextMenuEvent(0, pos))

            return True
        return False

    def getFeatureClassWidgets(self):
        return (list(self.featureClassFeatureWidgets.values()))

    def addParameter(self, featureClass, parameter):
        self.featureClassFeatureWidgets[featureClass].addParameter(parameter)


class FeatureWidget(qt.QCheckBox):
    def __init__(self, parent=None):
        super(FeatureWidget, self).__init__(parent)

    def Setup(self, featureName="", featureClassFlag=False, checkStatus=True):
        self.featureName = featureName
        self.checked = checkStatus

        if featureClassFlag:
            self.descriptionLabel = FeatureWidgetHelperLib.FeatureClassDescriptionLabel()
            self.descriptionLabel.setDescription(self.featureName)
        else:
            self.descriptionLabel = FeatureWidgetHelperLib.FeatureDescriptionLabel()
            self.descriptionLabel.setDescription(self.featureName)
            self.setText(self.featureName)

        self.setContextMenuPolicy(3)
        self.widgetMenu = FeatureWidgetHelperLib.ContextMenu(self)
        self.widgetMenu.Setup(self.featureName, self.descriptionLabel)
        self.customContextMenuRequested.connect(lambda point: self.connectMenu(point))

    def connectMenu(self, pos):
        self.widgetMenu.popup(self.mapToGlobal(pos))

    def addParameter(self, parameterName):
        self.widgetMenu.addParameter(parameterName)

    def getParameterDict(self):
        parameterDict = collections.OrderedDict()
        for k, v in list(self.widgetMenu.parameters.items()):
            value = v['Edit Window'].getValue()
            parameterDict[k] = value
        return (parameterDict)

    def getParameterEditWindow(self, parameterName):
        return (self.widgetMenu.parameters[parameterName]['Edit Window'])

    def getName(self):
        return (self.featureName)


class ContextMenu(qt.QMenu):
    def __init__(self, parent=None):
        super(ContextMenu, self).__init__(parent)

    def Setup(self, featureName, descriptionLabel="Description:"):
        self.featureName = featureName
        self.descriptionLabel = descriptionLabel
        self.parameters = collections.OrderedDict()

        self.descriptionAction = qt.QWidgetAction(self)
        self.descriptionAction.setDefaultWidget(self.descriptionLabel)
        self.closeAction = qt.QAction("Close", self)
        self.reloadActions()

    def reloadActions(self):
        self.addAction(self.descriptionAction)
        for parameter in self.parameters:
            self.addAction(self.parameters[parameter]['Action'])
        self.addAction(self.closeAction)

    def addParameter(self, parameterName):
        self.parameters[parameterName] = {}
        self.parameters[parameterName]['Action'] = qt.QAction(('Edit %s' % parameterName), self)
        self.parameters[parameterName]['Edit Window'] = FeatureWidgetHelperLib.ParameterEditWindow(self,
                                                                                                   self.featureName,
                                                                                                   parameterName)

        self.parameters[parameterName]['Action'].connect('triggered()', lambda parameterName=parameterName:
        self.parameters[parameterName]['Edit Window'].showWindow())
        self.reloadActions()

    def getParameters(self):
        return (self.parameters)


class ParameterEditWindow(qt.QInputDialog):
    def __init__(self, parent=None, featureName="", parameterName=""):
        super(ParameterEditWindow, self).__init__(parent)

        self.featureName = featureName
        self.parameterName = parameterName
        self.helpString = "Edit " + parameterName + " (" + self.featureName + ")"

        self.setLabelText(self.helpString + "\nCurrent Value = " + str(self.getValue()) + ": ")
        self.setInputMode(1)  # integer input only #make this modifiable

    def showWindow(self):
        self.resetLabel()
        self.open()

    def resetLabel(self):
        self.setLabelText(self.helpString + " (Current Value = " + str(self.getValue()) + "): ")

    def getValue(self):
        return (self.intValue())
