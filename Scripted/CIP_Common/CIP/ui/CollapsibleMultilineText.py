import qt

class CollapsibleMultilineText(qt.QTextEdit):
    """Text field that expands when it gets the focus and remain collapsed otherwise"""
    def __init__(self):
        super(CollapsibleMultilineText, self).__init__()
        self.minHeight = 20
        self.maxHeight = 50
        self.setFixedHeight(self.minHeight)

    def focusInEvent(self, event):
        # super(MyLineEdit, self).focusInEvent(event)
        self.setFixedHeight(self.maxHeight)

    def focusOutEvent(self, event):
        # super(MyLineEdit, self).focusOutEvent(event)
        self.setFixedHeight(self.minHeight)