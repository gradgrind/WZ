# -*- coding: utf-8 -*-
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGraphicsView

class GViewResizing(QGraphicsView):
    """An automatcally-resizing QGraphicsView ...
    """
    def __init__(self, parent):
        super().__init__(parent)
        # Apparently it is a good idea to disable scrollbars when using
        # this resizing scheme. With this resizing scheme they would not
        # appear anyway, so this doesn't lose any features!
        self.setHorizontalScrollBarPolicy (Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy (Qt.ScrollBarAlwaysOff)

    def resizeEvent(self, event):
        self.resize()
        return super().resizeEvent(event)

    def resize(self, qrect=None):
        if qrect == None:
            qrect = self.sceneRect()
        self.fitInView(qrect, Qt.KeepAspectRatio)

