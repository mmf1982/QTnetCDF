from PyQt5 import QtCore
from PyQt5.QtGui import QIcon, QKeySequence, QFont
from PyQt5.QtWidgets import (QAction, QMenuBar, qApp, QTreeView,
                             QFileSystemModel, QMainWindow, QLabel,
                             QDesktopWidget, QWidget, QVBoxLayout,
                             QHBoxLayout, QLineEdit)
import pathlib
import os

def center(window):
    """
    simple function put the window in the center of the screen

    :param window: window handle to window on which to act
    :return: None
    """
    qr = window.frameGeometry()  # where it currently is in upper left corner
    cp = QDesktopWidget().availableGeometry().center()  # center of my screen
    qr.moveCenter(cp)  # move the center of the geometry (not the object itself) to center of screen
    window.move(qr.topLeft())  # move the object itself to the top-left corner of that geometry


class MyQFileSystemModel(QFileSystemModel):
    def __init__(self):
        super(MyQFileSystemModel, self).__init__()

    def data(self, qmodelindex, role=None):  # real signature unknown; restored from __doc__
        if role == QtCore.Qt.TextAlignmentRole:
            return QFileSystemModel.data(self, qmodelindex, role=QtCore.Qt.AlignLeft)
        else:
            return QFileSystemModel.data(self, qmodelindex, role=role)


class HelpWindow(QMainWindow):
    def __init__(self, master, mytext):
        """
        Open a window to show an error that occurred

        :param master:  Qt master application which calls this help window
        :param mytext: str Message to write in the winodw
        """
        super().__init__(master)
        self.setStyleSheet("background-color: red")
        mylabel = QLabel(mytext)
        mylabel.setStyleSheet("color: black")
        newfont = QFont("Mono", 14, QFont.Bold)
        mylabel.setFont(newfont)
        self.setCentralWidget(mylabel)
        self.show()


class Files(QMainWindow):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.treeview = QTreeView()
        self.model = MyQFileSystemModel()
        newp = pathlib.Path(self.master.complete_name).absolute()
        allps = [str(newp)]
        while str(newp.parent) != os.path.sep:
            allps.append(str(newp.parent))
            newp = newp.parent
            if newp.parent == newp:
                break

        allps.append(str(newp.parent))
        self.model.setRootPath(os.path.curdir)
        self.treeview.setModel(self.model)
        for idx in allps:
            self.treeview.expand(self.model.index(idx))
        self.treeview.setCurrentIndex(self.model.index(allps[0]))
        self.treeview.setAlternatingRowColors(True)
        self.treeview.setAutoScroll(True)
        self.treeview.doubleClicked.connect(self.open_file)
        self.setCentralWidget(self.treeview)
        self.resize(self.master.config["Startingsize"]["Filemenu"]["width"],
                    self.master.config["Startingsize"]["Filemenu"]["height"])
        self.treeview.setUniformRowHeights(True)
        for idx, key in enumerate(self.master.config["Headers"]["Filemenu"]):
            width = self.master.config["Headers"]["Filemenu"][key]
            self.treeview.setColumnWidth(idx, width)
        self.treeview.setAlternatingRowColors(True)
        self.treeview.scrollTo(self.model.index(allps[0]))
        self.show()

    def open_file(self, signal):
        file_path = self.model.filePath(signal)
        self.master.load_file(file_path)
        self.close()


class FileMenu(QMenuBar):
    def __init__(self, my_master, forspec=False):
        super().__init__(my_master)
        self.master = my_master
        file_menu = self.addMenu('&File')
        file_menu.addAction(self.make_exit)
        file_menu.addAction(self.open_file)
        previous = self.addAction(self.previous)
        mnext = self.addAction(self.next)
        open_config = self.addAction(self.openconfig)
        self.forspec = forspec
        # next_menu = self.addMenu('&previous')
        # next_menu.addAction(self.previous)
        # next_menu = self.addMenu('&next')
        # next_menu.addAction(self.next)

    @property
    def openconfig(self):
        nextact = QAction(QIcon.fromTheme('document-properties'), '&config', self.master)
        nextact.setStatusTip('open config file')
        nextact.triggered.connect(self.config_open)
        return nextact

    def config_open(self):
        # file_name = self.master.config["this_file"]
        # if hasattr(os, "startfile"):
        #    x = os.startfile(file_name)
        # elif shutil.which("xdg-open"):
        #    x = subprocess.call(["xdg-open", file_name])
        #    print("xdk")
        # elif "EDITOR" in os.environ:
        #    x = subprocess.call([os.environ["EDITOR"], file_name])
        # print(x)
        new = Configchange(self)

    def open_menu(self):
        _ = Files(self.master)

    @property
    def open_file(self):
        openact = QAction(QIcon('open.png'), '&Open...', self.master)
        openact.setShortcut(QKeySequence.Open)
        openact.setStatusTip('Open File')
        openact.triggered.connect(self.open_menu)
        return openact

    @property
    def make_exit(self):
        exitact = QAction(QIcon('exit.png'), '&Exit', self.master)
        exitact.setShortcut(QKeySequence.Close)
        exitact.setStatusTip('Exit application')
        exitact.triggered.connect(qApp.quit)
        return exitact

    @property
    def next(self):
        nextact = QAction(QIcon.fromTheme('go-next'), '&next', self.master)
        nextact.setShortcut(QKeySequence.FindNext)
        nextact.setStatusTip('next file')
        nextact.triggered.connect(self.next_file)
        return nextact

    @property
    def previous(self):
        nextact = QAction(QIcon.fromTheme('go-previous'), '&previous', self.master)
        nextact.setShortcut(QKeySequence.FindPrevious)
        nextact.setStatusTip('previous file')
        nextact.triggered.connect(self.previous_file)
        return nextact

    def next_file(self):
        newp = os.path.split(self.master.complete_name)[0]
        if len(newp) == 0:
            newp = "."
        allfiles = os.listdir(newp)
        allfiles.sort()
        old_idx = allfiles.index(os.path.split(self.master.complete_name)[-1])
        if old_idx < len(allfiles) - 1:
            new_idx = old_idx + 1
        else:
            new_idx = 0
        newfile = allfiles[new_idx]
        self.master.load_file(os.path.join(newp, newfile))

    def previous_file(self):
        newp = os.path.split(self.master.complete_name)[0]
        if len(newp) == 0:
            newp = "."
        allfiles = os.listdir(newp)
        allfiles.sort()
        old_idx = allfiles.index(os.path.split(self.master.complete_name)[-1])
        if old_idx > 0:
            new_idx = old_idx - 1
        else:
            new_idx = len(allfiles) - 1
        newfile = allfiles[new_idx]
        self.master.load_file(os.path.join(newp, newfile))

class Configchange(QMainWindow):
    def __init__(self, master):
        """
        Open a window to change some settings from teh config

        :param master:  Qt master application which calls this help window
        """
        super().__init__(master)
        self.setStyleSheet("background-color: white")
        self.master = master
        mlayout = QVBoxLayout()
        mwidget = QWidget()
        newfont = QFont("Mono", 12, QFont.Bold)
        keylist = ["country_line_color", "country_line_thickness",
                    "limit_for_sliceplot",
                   "update_plot_immediately", "newplotwindow"]
        if self.master.forspec:
            keylist = ["manual"]
        for key in keylist:
            mlayoutsub = QHBoxLayout()
            mlabel = QLabel(key)
            mlabel.setStyleSheet("color: black")
            mlabel.setFont(newfont)
            try:
                mfield = QLineEdit(str(self.master.master.config["Plotsettings"][key]))
            except KeyError:
                try:
                    mfield = QLineEdit(str(self.master.master.config["moreDdata"][key]))
                except KeyError:
                    key="manual"
                    mfield = QLineEdit(str(self.master.master.config["settings"]["offset"][key]))
            slotLambda = lambda k=key, v=mfield: self.mchange(k, v)
            mfield.editingFinished.connect(slotLambda)
            
            mfield.setFixedWidth(100)
            mlayoutsub.addWidget(mlabel)
            mlayoutsub.addWidget(mfield)
            thiswidget = QWidget()
            thiswidget.setLayout(mlayoutsub)
            mlayout.addWidget(thiswidget)
        mwidget.setLayout(mlayout)
        self.setCentralWidget(mwidget)
        self.show()
        #self.connect(self, Qt.SIGNAL('triggered()'), self.closeEvent)
    def mchange(self, key, mentry):
        newvalue = mentry.text()
        try:
            newvalue = float(newvalue)
        except:
            if newvalue.lower() == "true":
                newvalue = True
            elif newvalue.lower() == "false":
                newvalue = False
            else:
                pass
        if self.master.forspec:
            self.master.master.config["settings"]["offset"][key] = int(newvalue)
        else:
            if key in self.master.master.config["Plotsettings"]:
                self.master.master.config["Plotsettings"][key] = newvalue
            else:
                self.master.master.config["moreDdata"][key] = newvalue
            return

    def closeEvent(self, event):
        self.destroy()
        event.accept()
