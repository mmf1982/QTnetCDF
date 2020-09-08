from PyQt5.QtGui import QIcon, QKeySequence, QFont
from PyQt5.QtWidgets import QAction, QMenuBar, qApp, QTreeView, QFileSystemModel, QMainWindow, QLabel, QDesktopWidget
import pathlib
import netCDF4
import os
def center(window):
    """
    simple function put the window in the center of the screen

    :param window: window on which to act
    :return: None
    """
    qr = window.frameGeometry()  # where it currently is in upper left corner
    cp = QDesktopWidget().availableGeometry().center()  # center of my screen
    qr.moveCenter(cp)  # move the center of the geometry (not the object itself) to center of screen
    window.move(qr.topLeft())  # move the object itself to the top-left corner of that geometry

class HelpWindow(QMainWindow):
    def __init__(self, master, mytext):
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
        self.model = QFileSystemModel()
        newp = pathlib.Path().absolute()
        allps = [str(newp)]
        while str(newp.parent) != "/":
            allps.append(str(newp.parent))
            newp = newp.parent
        allps.append(str(newp.parent))
        self.model.setRootPath(".")
        self.treeview.setModel(self.model)
        for idx in allps:
            self.treeview.expand(self.model.index(idx))
        self.treeview.setCurrentIndex(self.model.index(allps[0]))
        self.treeview.doubleClicked.connect(self.open_file)
        self.setCentralWidget(self.treeview)
        self.show()

    def open_file(self, signal):
        file_path = self.model.filePath(signal)
        self.master.load_file(file_path)
        self.close()
        print(file_path)


class FileMenu(QMenuBar):
    def __init__(self, my_master):
        super().__init__(my_master)
        self.master = my_master
        file_menu = self.addMenu('&File')
        file_menu.addAction(self.make_exit)
        file_menu.addAction(self.open_file)
        next_menu = self.addMenu('&previous/ next')
        next_menu.addAction(self.next)
        next_menu.addAction(self.previous)

    def open_menu(self):
        w = Files(self.master)
        print("showing anything?")

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
        nextact = QAction(QIcon('next.png'), '&next', self.master)
        nextact.setShortcut(QKeySequence.FindNext)
        nextact.setStatusTip('next file')
        nextact.triggered.connect(self.next_file)
        return nextact

    @property
    def previous(self):
        nextact = QAction(QIcon('previous.png'), '&previous', self.master)
        nextact.setShortcut(QKeySequence.FindPrevious)
        nextact.setStatusTip('previous file')
        nextact.triggered.connect(self.previous_file)
        return nextact

    def next_file(self):
        newp = pathlib.Path().absolute()
        allfiles = os.listdir()
        allfiles.sort()
        old_idx = allfiles.index(self.master.name)
        if old_idx < len(allfiles) - 1:
            new_idx = old_idx + 1
        else:
            new_idx = 0
        newfile = allfiles[new_idx]
        print(newfile)
        print(newp)
        self.master.load_file(os.path.join(newp, newfile))

    def previous_file(self):
        newp = pathlib.Path().absolute()
        allfiles = os.listdir()
        allfiles.sort()
        old_idx = allfiles.index(self.master.name)
        if old_idx > 0:
            new_idx = old_idx - 1
        else:
            new_idx = len(allfiles)
        newfile = allfiles[new_idx]
        print(newfile)
        print(newp)
        self.master.load_file(os.path.join(newp, newfile))
