#####################################################
# Frame
frame = qt.QFrame(self.statisticsCollapsibleButton)	# Widget parent of the frame (it can be empty)
frameLayout = qt.QHBoxLayout()
frame.setLayout(frameLayout)
frameLayout.addWidget(myInnerFrameButton)
self.mainLayout.addWidget(frame)

#####################################################
# Simple textbox
txtServer = qt.QLineEdit()
txtServer.setText("Initial text")
txtServer.setFixedWidth(100)
# Force 0-100 range
txtServer.setValidator(qt.QIntValidator(0, 100))

#####################################################
# Button (complete example)
self.exampleButton = ctk.ctkPushButton()
self.exampleButton.text = "Push me!"
self.exampleButton.toolTip = "This is the button tooltip"
self.exampleButton.setIcon(qt.QIcon("{0}/Reload.png".format(SlicerUtil.ICON_DIR)))
self.exampleButton.setIconSize(qt.QSize(20,20))
self.exampleButton.setStyleSheet("font-weight:bold; font-size:12px; background-color: green;" )
self.exampleButton.setFixedWidth(200)


self.btnGoToPreviousStructure = ctk.ctkPushButton()
self.btnGoToPreviousStructure.text = " Previous slice"
self.btnGoToPreviousStructure.toolTip = "Go to the previous slice that contains the selected label" 
#self.goToPreviousStructureButton.setIcon(qt.QIcon(os.path.join(SlicerUtil.CIP_ICON_DIR, "previous.png")))
self.btnGoToPreviousStructure.setIcon(SlicerUtil.getIcon("previous.png"))
# To Reuse one of the system icons: self.singleSlideViewButton.setIcon(SlicerUtil.getIcon("LayoutOneUpRedSliceView.png", isSystemIcon=True))
self.btnGoToPreviousStructure.setIconSize(qt.QSize(24,24))
self.btnGoToPreviousStructure.setFixedWidth(150)        
self.btnGoToPreviousStructure.iconAlignment = 0x0001    # Align the icon to the right. See http://qt-project.org/doc/qt-4.8/qt.html#AlignmentFlag-enum for a complete list
self.btnGoToPreviousStructure.buttonTextAlignment = (0x0081) # Aling the text to the left and vertical center
self.btnGoToPreviousStructure.enabled = False

# To get the button that provoked the event in the connect signal:
self.btnGoToPreviousStructure.clicked.connect(lambda: self.onButtonClicked(self.btnGoToPreviousStructure))

#####################################################
# Checkbox
self.evaluateSegmentationCheckbox = qt.QCheckBox()
self.evaluateSegmentationCheckbox.setText("Allow saving seeds for batch mode processing")
self.evaluateSegmentationCheckbox.connect("stateChanged(int)", self.onCheckboxEvaluateSegmentationClicked)
self.evaluateSegmentationCheckbox.connect("clicked()", self.onCheckboxEvaluateSegmentationClicked)
def __onSaveTimeCostCheckboxClicked__(self, checked):
    selected = (checked == 2)		#(0 for False)


#####################################################
# Show dialog message
qt.QMessageBox.information(slicer.util.mainWindow(), 'OK!', 'The test was ok. Review the console for details')
# It can be warning, critical...

# Show a dialog with Yes/No question:
if qt.QMessageBox.question(slicer.util.mainWindow(), "Reset volume?",
                    "All the elements for the current volume ({0}) will be removed. Are you sure?".format(currentVolumeName),
                    qt.QMessageBox.Yes|qt.QMessageBox.No) == qt.QMessageBox.Yes:

#####################################################
# Radio Button Group with key-value
self.typesRadioButtonGroup = qt.QButtonGroup()
self.typesList = []
for key, description in self.logic.mainTypes.iteritems():
    rbitem = qt.QRadioButton(description)
    self.typesRadioButtonGroup.addButton(rbitem, key)  # Important: key is a number
    self.typesLayout.addWidget(rbitem)
    
self.typesRadioButtonGroup.buttons()[0].setChecked(True)
....
self.typesRadioButtonGroup.connect("buttonClicked (QAbstractButton*)", self.ontypestRadioButtonClicked)
...
selectedId = self.typesRadioButtonGroup.checkedId()

# To find later the id of a button:
id = self.typesRadioButtonGroup.id(self.typesRadioButtonGroup.buttons()[0])

#####################################################
# Combo box with key-values
self.cbRegion = qt.QComboBox(self.structuresCollapsibleButton)        
index=0
for key, item in self.logic.getRegionTypes().iteritems():
    self.cbRegion.addItem(item[1])    # Add label description
    self.cbRegion.setItemData(index, key)     # Add string code
    index += 1
...
region = self.cbRegion.itemData(self.cbRegion.currentIndex) 
...
self.cbRegion.connect("currentIndexChanged (int)", self.onCbRegionCurrentIndexChanged)
....

#####################################################
# Open a filedialog
f = qt.QFileDialog.getOpenFileName()
if f:
    self.caseListTxt.text = f

# Just with folders: Idem but with qt.QFileDialog.getExistingDirectory()

######
# Controls to select files/directories
# Files:
caseListPathEdit = ctk.ctkPathLineEdit()
path = caseListPathEdit.currentPath     # (Read/Write)
# Directories:
button = ctk.ctkDirectoryButton()
dir = button.directory                  # (Read/Write)



#####################################################
# Set vertical alignment to the top in the layout (example in a grid layout) 
self.mainLayout.addWidget(mywidget, 2, 1, 0x0020)    
# Top vertical and right edge:
self.mainLayout.addWidget(mywidget, 2, 1, 0x0020|0x0002)    
# You can see all the flag combinations for vertical and horizontal aligments here: http://doc.qt.io/qt-4.8/qt.html#AlignmentFlag-enum   

#####################################################
# Iterate over several subcategories ("flat")
self.__storedColumnNames__.extend(itertools.chain.from_iterable(self.featureClasses.itervalues()))

#####################################################
# Timer
self.timer = qt.QTimer()
self.timer.setInterval(150)
self.timer.timeout.connect(self.myFunction)		# Function without params
self.timer.start()
self.timer.stop()

######################################################
# Frames with borders
frame.setFrameStyle(0x0002 | 0x0010)   # See all the combinations here: http://doc.qt.io/qt-4.8/qframe.html#setFrameStyle
frame.lineWidth = 2
frame.setStyleSheet("background-color:#EEEEEE; margin-bottom: 10px")     
