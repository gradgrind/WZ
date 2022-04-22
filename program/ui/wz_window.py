"""
ui/wz_window.py

Last updated:  2022-04-22

The main window of the WZ GUI.


=+LICENCE=============================
Copyright 2022 Michael Towers

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.

=-LICENCE========================================
"""

_TITLE = "WZ"

########################################################################

import sys, os, builtins

if __name__ == '__main__':
    # Enable package import if running as module
    #print(sys.path)
    this = sys.path[0]
    appdir = os.path.dirname(this)
    sys.path[0] = appdir
    basedir = os.path.dirname(appdir)
    from core.base import start
    import ui.ui_base
    #    start.setup(os.path.join(basedir, 'TESTDATA'))
    #    start.setup(os.path.join(basedir, 'DATA'))
    start.setup(os.path.join(basedir, "DATA-2023"))

from ui.ui_base import QWidget, QVBoxLayout, QHBoxLayout, \
        QLabel, QStackedWidget, QFrame, QPushButton, HLine, run

### -----

class MainWindow(QWidget):
    def __init__(self):
#?
        """Note that some of the initialization is done after a short
        delay: <init> is called using a single-shot timer.
        """
        super().__init__()
        self.setWindowTitle(_TITLE)
        topbox = QVBoxLayout(self)
        # ---------- Title Box ---------- #
        titlebox = QHBoxLayout()
        topbox.addLayout(titlebox)
        self.year_term = QLabel()
        titlebox.addWidget(self.year_term)
        titlebox.addStretch(1)
        self.title_label = QLabel()
#TODO: Bold, larger?
        titlebox.addWidget(self.title_label)
        titlebox.addStretch(1)
        topbox.addWidget(HLine())
        # ---------- Tab Box ---------- #
        tab_box_layout = QHBoxLayout()
        topbox.addLayout(tab_box_layout)

        self.buttonbox = QVBoxLayout()
        tab_box_layout.addLayout(self.buttonbox)
        self.widgetstack = QStackedWidget()
#        self.widgetstack.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.widgetstack.setFrameStyle(QFrame.Box | QFrame.Raised)
#        self.widgetstack.setLineWidth(3)
#        self.widgetstack.setMidLineWidth(2)
        tab_box_layout.addWidget(self.widgetstack)
        self.tab_buttons = []
        self.index = -1


# Add QStatusBar?


#        for tab in TABS:
#            self.tab_widget.add_page(tab)
#        # Run the <init> method when the event loop has been entered:
#        QTimer.singleShot(10, self.init)
#
#?
    def closeEvent(self, e):
#        DEBUG("CLOSING CONTROL")
        if self.check_unsaved():
#?            backend_instance.terminate()
            e.accept()
        else:
            e.ignore()

    def check_unsaved(self):
        """Called when a "quit program" request is received.
        Check for unsaved data, asking for confirmation if there is
        some. Return <True> if it is ok to continue (quit).
        """
        w = self.widgetstack.currentWidget()
        if w:
            return w.leave_ok()
        return True

    def add_tab(self, tab_widget):
        b = TabButton(tab_widget.name, len(self.tab_buttons))
        self.tab_buttons.append(b)
        self.buttonbox.addWidget(b)
        self.widgetstack.addWidget(tab_widget)

# Adding spacing and stretches might be useful ...
#            if i:
#                self.buttonbox.addSpacing(i)
#            else:
#                self.buttonbox.addStretch(1)
    def add_stretch(self):
        self.buttonbox.addStretch(1)

    def select_tab(self, index):
        """Select the tab (module) with given index.
        """
# initially this will probably be the first widget
        i0 = self.widgetstack.currentIndex()
        print("???", i0)
        if i0 == index:
            # No change of stack widget
            if self.tab_buttons[i0].isChecked():
                print(" ... no change")
                return

            print(f"Current tab ({i0}): button not 'checked'")
        elif i0 >= 0:
            print(f"SELECT TAB {index}")
            # Check that the old tab can be left
            tab0 = self.widgetstack.widget(i0)
            if tab0.leave_ok():
                tab0.leave()
                # Deselect old button
                self.tab_buttons[i0].setChecked(False)
                self.widgetstack.setCurrentIndex(index)
            else:
                # Deselect new button
                self.tab_buttons[index].setChecked(False)
#
                print(" ... deselect new button")
                return
        else:
            raise Bug("??? tab index = %d" % i0)
        # Select new button
        self.tab_buttons[index].setChecked(True)
        # Enter new tab
        tab = self.widgetstack.widget(index)
        tab.enter()
        self.title_label.setText(f'<b>{tab.title}</b>')


class TabButton(QPushButton):
    """A custom class to provide special buttons for the tab switches.
    """
    __stylesheet = "QPushButton:checked {background-color: #ffd36b;}"
#
    def __init__(self, label, index):
        super().__init__(label)
        self.index = index
        self.setStyleSheet(self.__stylesheet)
        self.setCheckable(True)
        self.clicked.connect(self.selected)
#
    def selected(self):
        MAIN_WIDGET.select_tab(self.index)


########################################################################
# I probably won't use this code in this form, but it might be helpful
# somehow ...
class MainWindowUI(QWidget):
    def __init__(self):
        super().__init__()
#        self.setWindowTitle(PROGRAM_NAME)
#        icon = get_icon('datatable')
#        self.setWindowIcon(icon)


        self.setupUi()

    def setupUi(self):
#        self.resize(817, 504)




        font = QFont()
        font.setFamilies([u"Sans Serif"])
        font.setPointSize(12)
        self.setFont(font)
        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setSpacing(1)
        self.verticalLayout_3.setContentsMargins(1, 1, 1, 1)
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSpacing(3)
        self.horizontalLayout.setContentsMargins(-1, 3, -1, 3)

        self.l_year = QLabel()
        font1 = QFont()
        font1.setBold(True)
        self.l_year.setFont(font1)
        self.horizontalLayout.addWidget(self.l_year)

        self.l_title = QLabel()
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.l_title.sizePolicy().hasHeightForWidth())
        self.l_title.setSizePolicy(sizePolicy)
        self.l_title.setFont(font1)
        self.l_title.setAlignment(Qt.AlignCenter)
        self.horizontalLayout.addWidget(self.l_title)

        self.verticalLayout_3.addLayout(self.horizontalLayout)

        self.line = QFrame()
        self.line.setFrameShadow(QFrame.Plain)
        self.line.setLineWidth(1)
        self.line.setFrameShape(QFrame.HLine)

        self.verticalLayout_3.addWidget(self.line)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setSpacing(0)
        self.choose_module = QWidget()
        self.verticalLayout = QVBoxLayout(self.choose_module)
        self.verticalLayout.setSpacing(8)
        self.verticalLayout.setContentsMargins(1, 1, 1, 1)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(3, 3, 3, 3)
        self.pb_intro = QPushButton(self.choose_module)
        self.pb_intro.setObjectName(u"pb_intro")
        self.pb_intro.setText(u"Willkommen")
        self.pb_intro.setCheckable(True)
        self.pb_intro.setChecked(True)
        self.pb_intro.setAutoExclusive(True)

        self.verticalLayout.addWidget(self.pb_intro)

        self.pb_calendar = QPushButton(self.choose_module)
        self.pb_calendar.setObjectName(u"pb_calendar")
        self.pb_calendar.setCheckable(True)
        self.pb_calendar.setChecked(False)
        self.pb_calendar.setAutoExclusive(True)

        self.verticalLayout.addWidget(self.pb_calendar)

        self.pb_pupil = QPushButton(self.choose_module)
        self.pb_pupil.setObjectName(u"pb_pupil")
        self.pb_pupil.setText(u"Sch\u00fclerdaten verwalten")
        self.pb_pupil.setCheckable(True)
        self.pb_pupil.setAutoExclusive(True)

        self.verticalLayout.addWidget(self.pb_pupil)

        self.pb_template_fill = QPushButton(self.choose_module)
        self.pb_template_fill.setObjectName(u"pb_template_fill")
        self.pb_template_fill.setText(u"Vorlage ausf\u00fcllen")
        self.pb_template_fill.setCheckable(True)
        self.pb_template_fill.setAutoExclusive(True)

        self.verticalLayout.addWidget(self.pb_template_fill)

        self.verticalSpacer = QSpacerItem(20, 352, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)


        self.horizontalLayout_2.addWidget(self.choose_module)

        self.main_stack = QStackedWidget()
        self.main_stack.setObjectName(u"main_stack")
        sizePolicy1 = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.main_stack.sizePolicy().hasHeightForWidth())
        self.main_stack.setSizePolicy(sizePolicy1)
        self.main_stack.setMinimumSize(QSize(600, 0))
        self.tab_intro = QWidget()
        self.tab_intro.setObjectName(u"tab_intro")
        self.verticalLayout_2 = QVBoxLayout(self.tab_intro)
        self.verticalLayout_2.setSpacing(1)
        self.verticalLayout_2.setContentsMargins(1, 1, 1, 1)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(1, 1, 1, 1)
        self.intro_text = QTextBrowser(self.tab_intro)
        self.intro_text.setObjectName(u"intro_text")
        self.intro_text.setReadOnly(True)
        self.intro_text.setPlaceholderText(u"Welcome and Introduction ...")

        self.verticalLayout_2.addWidget(self.intro_text)

        self.main_stack.addWidget(self.tab_intro)
        self.tab_calendar = QWidget()
        self.tab_calendar.setObjectName(u"tab_calendar")
        self.horizontalLayout_5 = QHBoxLayout(self.tab_calendar)
        self.horizontalLayout_5.setSpacing(3)
        self.horizontalLayout_5.setContentsMargins(1, 1, 1, 1)
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.verticalLayout_8 = QVBoxLayout()
        self.verticalLayout_8.setSpacing(3)
        self.verticalLayout_8.setObjectName(u"verticalLayout_8")
        self.label = QLabel(self.tab_calendar)
        self.label.setObjectName(u"label")

        self.verticalLayout_8.addWidget(self.label)

        self.line_2 = QFrame(self.tab_calendar)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setFrameShape(QFrame.HLine)
        self.line_2.setFrameShadow(QFrame.Sunken)

        self.verticalLayout_8.addWidget(self.line_2)

        self.edit_calendar = QTextEdit(self.tab_calendar)
        self.edit_calendar.setObjectName(u"edit_calendar")
        self.edit_calendar.setDocumentTitle(u"")
        self.edit_calendar.setLineWrapMode(QTextEdit.NoWrap)
        self.edit_calendar.setAcceptRichText(False)

        self.verticalLayout_8.addWidget(self.edit_calendar)


        self.horizontalLayout_5.addLayout(self.verticalLayout_8)

        self.widget = QWidget(self.tab_calendar)
        self.widget.setObjectName(u"widget")
        self.verticalLayout_7 = QVBoxLayout(self.widget)
        self.verticalLayout_7.setSpacing(3)
        self.verticalLayout_7.setContentsMargins(1, 1, 1, 1)
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.pushButton = QPushButton(self.widget)
        self.pushButton.setObjectName(u"pushButton")

        self.verticalLayout_7.addWidget(self.pushButton)

        self.verticalSpacer_4 = QSpacerItem(20, 379, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_7.addItem(self.verticalSpacer_4)


        self.horizontalLayout_5.addWidget(self.widget)

        self.main_stack.addWidget(self.tab_calendar)
        self.tab_pupil = QWidget()
        self.tab_pupil.setObjectName(u"tab_pupil")
        self.horizontalLayout_3 = QHBoxLayout(self.tab_pupil)
        self.horizontalLayout_3.setSpacing(3)
        self.horizontalLayout_3.setContentsMargins(1, 1, 1, 1)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.pupil_stack = QStackedWidget(self.tab_pupil)
        self.pupil_stack.setObjectName(u"pupil_stack")
        self.pupil_1 = QWidget()
        self.pupil_1.setObjectName(u"pupil_1")
        self.pupil_stack.addWidget(self.pupil_1)
        self.pupil_2 = QWidget()
        self.pupil_2.setObjectName(u"pupil_2")
        self.pupil_stack.addWidget(self.pupil_2)

        self.horizontalLayout_3.addWidget(self.pupil_stack)

        self.pupil_functions = QWidget(self.tab_pupil)
        self.pupil_functions.setObjectName(u"pupil_functions")
        self.verticalLayout_4 = QVBoxLayout(self.pupil_functions)
        self.verticalLayout_4.setSpacing(3)
        self.verticalLayout_4.setContentsMargins(1, 1, 1, 1)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.pupil_class = QComboBox(self.pupil_functions)
        self.pupil_class.setObjectName(u"pupil_class")

        self.verticalLayout_4.addWidget(self.pupil_class)

        self.pupil_pupil = QComboBox(self.pupil_functions)
        self.pupil_pupil.setObjectName(u"pupil_pupil")

        self.verticalLayout_4.addWidget(self.pupil_pupil)

        self.pushButton_4 = QPushButton(self.pupil_functions)
        self.pushButton_4.setObjectName(u"pushButton_4")
        self.pushButton_4.setText(u"???")

        self.verticalLayout_4.addWidget(self.pushButton_4)

        self.verticalSpacer_2 = QSpacerItem(20, 286, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_4.addItem(self.verticalSpacer_2)

        self.pushButton_5 = QPushButton(self.pupil_functions)
        self.pushButton_5.setObjectName(u"pushButton_5")
        self.pushButton_5.setText(u"Speichern")

        self.verticalLayout_4.addWidget(self.pushButton_5)


        self.horizontalLayout_3.addWidget(self.pupil_functions)

        self.main_stack.addWidget(self.tab_pupil)
        self.tab_template_fill = QWidget()
        self.tab_template_fill.setObjectName(u"tab_template_fill")
        self.verticalLayout_6 = QVBoxLayout(self.tab_template_fill)
        self.verticalLayout_6.setSpacing(3)
        self.verticalLayout_6.setContentsMargins(1, 1, 1, 1)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setSpacing(3)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.template_form = QWidget(self.tab_template_fill)
        self.template_form.setObjectName(u"template_form")
        sizePolicy2 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.template_form.sizePolicy().hasHeightForWidth())
        self.template_form.setSizePolicy(sizePolicy2)

        self.horizontalLayout_4.addWidget(self.template_form)

        self.template_functions = QWidget(self.tab_template_fill)
        self.template_functions.setObjectName(u"template_functions")
        self.verticalLayout_5 = QVBoxLayout(self.template_functions)
        self.verticalLayout_5.setSpacing(3)
        self.verticalLayout_5.setContentsMargins(1, 1, 1, 1)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.template_class = QComboBox(self.template_functions)
        self.template_class.setObjectName(u"template_class")

        self.verticalLayout_5.addWidget(self.template_class)

        self.template_pupil = QComboBox(self.template_functions)
        self.template_pupil.setObjectName(u"template_pupil")

        self.verticalLayout_5.addWidget(self.template_pupil)

        self.template_choose = QPushButton(self.template_functions)
        self.template_choose.setObjectName(u"template_choose")

        self.verticalLayout_5.addWidget(self.template_choose)

        self.verticalSpacer_3 = QSpacerItem(20, 287, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_5.addItem(self.verticalSpacer_3)

        self.template_make = QPushButton(self.template_functions)
        self.template_make.setObjectName(u"template_make")

        self.verticalLayout_5.addWidget(self.template_make)


        self.horizontalLayout_4.addWidget(self.template_functions)


        self.verticalLayout_6.addLayout(self.horizontalLayout_4)

        self.main_stack.addWidget(self.tab_template_fill)

        self.horizontalLayout_2.addWidget(self.main_stack)


        self.verticalLayout_3.addLayout(self.horizontalLayout_2)

        QWidget.setTabOrder(self.pb_intro, self.pb_calendar)
        QWidget.setTabOrder(self.pb_calendar, self.pb_pupil)
        QWidget.setTabOrder(self.pb_pupil, self.pb_template_fill)
        QWidget.setTabOrder(self.pb_template_fill, self.intro_text)
        QWidget.setTabOrder(self.intro_text, self.pupil_pupil)
        QWidget.setTabOrder(self.pupil_pupil, self.pupil_class)
        QWidget.setTabOrder(self.pupil_class, self.pushButton_4)
        QWidget.setTabOrder(self.pushButton_4, self.pushButton_5)
        QWidget.setTabOrder(self.pushButton_5, self.template_class)
        QWidget.setTabOrder(self.template_class, self.template_pupil)
        QWidget.setTabOrder(self.template_pupil, self.template_make)
        QWidget.setTabOrder(self.template_make, self.template_choose)

        self.retranslateUi()

        self.main_stack.setCurrentIndex(1)
        self.pupil_stack.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(self)
    # setupUi

    def retranslateUi(self):
        self.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.l_year.setText(QCoreApplication.translate("Form", u"School year + term", None))
        self.l_title.setText(QCoreApplication.translate("Form", u"Page Title", None))
        self.pb_calendar.setText(QCoreApplication.translate("Form", u"Schuljahr", None))
        self.label.setText(QCoreApplication.translate("Form", u"Kalender bearbeiten", None))
        self.edit_calendar.setHtml(QCoreApplication.translate("Form", u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:'Sans Serif'; font-size:12pt; font-weight:400; font-style:normal;\">\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p></body></html>", None))
        self.pushButton.setText(QCoreApplication.translate("Form", u"\u00c4nderungen\n"
"speichern", None))
        self.template_choose.setText(QCoreApplication.translate("Form", u"Vorlage w\u00e4hlen", None))
        self.template_make.setText(QCoreApplication.translate("Form", u"Erstellen", None))
    # retranslateUi

## --------------------------------------------------------------------------------


if __name__ == "__main__":
    from ui.ui_base import StackPage, APP

    MAIN_WIDGET = MainWindow()
    builtins.MAIN_WIDGET = MAIN_WIDGET
    MAIN_WIDGET.add_tab(StackPage())
    import ui.modules   # Initialize the "pages"

    MAIN_WIDGET.add_stretch()
# A bodge to get the tab title set initially ...
#    MAIN_WIDGET.widgetstack.setCurrentIndex(1)
    MAIN_WIDGET.select_tab(0)
    MAIN_WIDGET.year_term.setText("2022.1")
    geometry = APP.primaryScreen().availableGeometry()
    MAIN_WIDGET.resize(int(geometry.width() * 0.7), int(geometry.height() * 0.7))
    run(MAIN_WIDGET)
#    if SHOW_CONFIRM("Shall I do this?"):
#        run(MAIN_WIDGET)
