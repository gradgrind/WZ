# Various widgets, etc., which I tried out but in the end didn't use
# (at least, not in this form). Perhaps there are some useful code
# snippets here ...

class DelegatableList(QListWidget):
    """Changes must be registered with mouse-click or return-key.
    """
    def __init__(self, parent):
        super().__init__(parent=parent)
        self.result = False     # Flag: no registered result
        self.itemClicked.connect(self.__done)

    @Property(str, user=True)
    def text(self):
        text = self.currentItem().text()
        #print("§GET:", text)
        return text

    @text.setter
    def text(self, text):
        if self.result:
            # This method gets called during saving of the result data,
            # which is not necessary.
            return
        #print("$SET", text)
        self.clear()
        row = -1
        items = []
        for i in range(len(SHARED_DATA["PERIODS"])):
            item = str(i + 1)
            if item == text:
                row = i
            items.append(item)
        self.addItems(items)
        self.setCurrentRow(row)

    def keyPressEvent(self, e):
        e.accept()
        key = e.key()
        if key == Qt.Key_Return:
            self.__done()
        else:
            super().keyPressEvent(e)

    def __done(self):
        #print("§§§DONE", self.currentItem().text())
        self.result = True  # Register result as valid
        #self.hide()
        self.clearFocus()


class DurationDelegate(QStyledItemDelegate):
    def __init__(self, table, modified=None):
        super().__init__(parent=table)
        self.__table = table
        self.__modified = modified

    def createEditor(self, parent, option, index):
        w = DelegatableList(parent=parent)
        w.setMinimumHeight(80)
# There is a problem here: any part of this list which extends past the
# master table area will be hidden.
        return w

    def setModelData(self, editor, model, index):
        text = editor.text
        if  text:
            print("?-------", text)
            if (not self.__modified) or self.__modified(index.row(), text):
                model.setData(index, text)
        self.__table.setFocus()


class EditableComboBox(QComboBox):
    def __init__(self, parent=None, changed_callback=None, sort=True):
        """<changed_callback> takes a single parameter, the new text.
        <sort> selects alphabetical sorting (ascending) of manually
        added entries (not those added in the program).
        """
        self.__changed = changed_callback
        super().__init__(parent=parent, editable=True)
        self.__item = None
        if sort:
            self.setInsertPolicy(QComboBox.InsertPolicy.InsertAlphabetically)
        self.currentIndexChanged.connect(self.index_changed)

    def focusOutEvent(self, e):
        """Close the editor when focus leaves it. This reverts any
        partially entered text.
        """
        self.clearEditText()
        self.setCurrentIndex(self.currentIndex())

    def index_changed(self, i):
        # This can be called twice on a change because of sorting
        t = self.currentText()
        if t != self.__item:
            self.__item = t
            if self.__changed:
                self.__changed(t)


class RoomListValidator(QValidator):
    def init(self, roommap):
        self.roommap = roommap

    def validate(self, text, pos):
        #print("VALIDATE:", pos, text)
        if text.endswith("+"):
            textv = text[:-1]
        else:
            textv = text
        for rid in textv.split("/"):
            if not rid:
                continue
            if rid in self.roommap or rid == "$":
                print(f" ... {rid}: ok")
            else:
                print(f" ... {rid}: NOT ok")
                return (QValidator.State.Intermediate, text, pos)
                #return (QValidator.State.Invalid, text, pos)
        return (QValidator.State.Acceptable, text, pos)
