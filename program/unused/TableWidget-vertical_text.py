# Vertical text in QTableWidget
# Note that headers have no delegate. It is possible to get vertical
# text in headers by subclassing QHeaderView, but it is tricky. See the
# code in test-itemdelegates for an attempt.

class VerticalTextDelegate(QtGui.QStyledItemDelegate):
    def paint(self, painter, option, index):
        optionCopy = QtGui.QStyleOptionViewItem(option)
        rectCenter = QtCore.QPointF(QtCore.QRectF(option.rect).center())
        painter.save()
        painter.translate(rectCenter.x(), rectCenter.y())
        painter.rotate(-90.0)
        painter.translate(-rectCenter.x(), -rectCenter.y())
        optionCopy.rect = painter.worldTransform().mapRect(option.rect)

        # Call the base class implementation
        super().paint(painter, optionCopy, index)

        painter.restore()

    def sizeHint(self, option, index):
        val = QtGui.QSize(self.sizeHint(option, index))
        return QtGui.QSize(val.height(), val.width())


# To use the delegate:

item = QtGui.QTableWidgetItem("test")
self.table_widget.setItem(2, 0, item)
self.table_widget.setItemDelegateForColumn(0,VerticalTextDelegate(self))
