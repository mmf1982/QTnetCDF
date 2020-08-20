
import os
print(os.path.dirname(os.path.abspath(__file__)))
import pathlib
import sys
import netCDF4
import yaml
from PyQt5 import QtCore
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QFont
from PyQt5.QtWidgets import (QApplication, QTreeView, QAbstractItemView, QMainWindow, QDockWidget,
                             QTableView, QSizePolicy, QWidget, QPushButton, QVBoxLayout, QHBoxLayout,
                             QSlider, QLabel, QStatusBar, QHeaderView)
try:
    from .Fastplot import Fast3D, Fast2D, Fast1D
except (ImportError, ModuleNotFoundError):
    from Fastplot import Fast3D, Fast2D, Fast1D
try:
    from .Menues import FileMenu
except (ImportError, ModuleNotFoundError):
    from Menues import FileMenu
try:
    from .Converters import hdf4_object
except (ImportError, ModuleNotFoundError):
    from Converters import hdf4_object
from numpy import array, arange


class Pointer(QStandardItem):
    """
    class to add underlying data to an item in treeview
    """

    def __init__(self, mdata, name):
        """
        :param mdata: group of variable handle, underlying data
        :param name: string to be used in QStandardItem constructor
        """
        super(Pointer, self).__init__(name)
        self.mdata = mdata


class MyQTreeView(QTreeView):
    """
    Main class used to display the file structure. Define here the main Key actions (s->table, d->info, double->plot)

    Also, define here the data chooser events x, y, u, e to extract data as x, y yerr and xerr directly from file level
    """
    def __init__(self, master, *args, **kwargs):
        self.master = master
        super().__init__(*args, **kwargs)

    def keyPressEvent(self, event):
        idx = self.currentIndex()
        current_pointer = self.model().itemFromIndex(idx)
        if event.text() == "d":
            # this prints the details of the current selection
            try:
                current_pointer.mdata.print_info()
            except:
                print(current_pointer.mdata)
        elif event.text() == "s":
            # open tableview
            self.open_table(current_pointer)
        elif event.text() == "x":
            self.master.mdata.x.set(current_pointer.mdata[:], current_pointer.mdata.name)
        elif event.text() == "y":
            self.master.mdata.y.set(current_pointer.mdata[:], current_pointer.mdata.name)
        elif event.text() == "u":
            self.master.mdata.yerr.set(current_pointer.mdata[:], current_pointer.mdata.name)
        elif event.text() == "e":
            self.master.mdata.xerr.set(current_pointer.mdata[:], current_pointer.mdata.name)
        #elif event.text() == "m":
        #    self.master.mdata.mask.set(current_pointer.mdata[:], current_pointer.mdata.name)

    def open_table(self, current_p):
        dock_widget = QDockWidget(current_p.mdata.name)
        table_widget = MyTable(self.master, current_p.mdata)
        dock_widget.setWidget(table_widget)
        self.master.addDockWidget(QtCore.Qt.BottomDockWidgetArea, dock_widget)


class MyTable(QWidget):
    """
    Class for the table to display a specific variable, hold the data and manage data which is actually displayed

    Variable cannot be higher than 3D
    """
    def __init__(self, master, data):
        """
        Initialize table

        :param master:  Main Window
        :param data:  data handle or ndarray
        """
        super(MyTable, self).__init__()
        self.master = master
        self.name = data.name
        self.table = MyQTableView(self.master)
        self.c_idx = 0
        self.c_dim = 0
        self.maxidxs = data[:].shape
        self.diminfo = None
        self.sliceinfo = None
        self.all_data = data
        self.make_design()
        self.update_table()

    def make_design(self):
        """
        Function to setup the layout of the table. If data is 3D, I need data selection options. Otherwise not.
        """
        table_layout = QHBoxLayout()
        table_layout.addWidget(self.table)
        if self.all_data.ndim == 3:
            data_selection = QWidget()
            data_selection_layout = QVBoxLayout()
            slicer_area = QWidget()
            slicer_layout = QHBoxLayout()
            slicer = QSlider()
            slicer.setRange(0, 2)
            slicer.valueChanged.connect(self.slicing)
            display_area = QWidget()
            display_layout = QVBoxLayout()
            self.diminfo = QLabel("dim 0")
            self.sliceinfo = QLabel("slice 0 / 0-" + str(self.maxidxs[0]-1))
            display_layout.addWidget(self.diminfo)
            display_layout.addWidget(self.sliceinfo)
            display_area.setLayout(display_layout)
            slicer_layout.addWidget(slicer)
            slicer_layout.addWidget(display_area)
            slicer_area.setLayout(slicer_layout)
            plus = QPushButton("+")
            plus.clicked.connect(self.plus)
            minus = QPushButton("-")
            minus.clicked.connect(self.minus)
            for obj in [slicer_area, plus, minus]:
                data_selection_layout.addWidget(obj)
            data_selection.setLayout(data_selection_layout)
            # slider.valueChanged.connect(self.update_dim_label)
            table_layout.addWidget(data_selection)
        self.setLayout(table_layout)

    def plus(self):
        """
        If underlying data is 3D, go on slice up.
        """
        if self.c_idx < self.maxidxs[self.c_dim] - 1:
            self.c_idx += 1
        else:
            self.c_idx = 0
        self.sliceinfo.setText("slice " + str(self.c_idx) + "/ 0-" + str(self.maxidxs[self.c_dim]-1))
        self.update_table()

    def minus(self):
        """
        If underlying data is 3D, go on slice down.
        """
        if self.c_idx > -self.maxidxs[self.c_dim]:
            self.c_idx -= 1
        else:
            self.c_idx = 0
        self.sliceinfo.setText("slice " + str(self.c_idx)  + "/ 0-" + str(self.maxidxs[self.c_dim]-1))
        self.update_table()

    def slicing(self, idx):
        """
        If underlying data is 3D, change the slicing dimension
        :param idx: int, which dimension to slice along
        """
        self.c_dim = idx
        self.diminfo.setText("dim " + str(self.c_dim))
        self.update_table()

    def update_table(self):
        """
        If underlying data is 3D, change the displayed data to the new subset of all_data, depending on c_dim and c_idx
        """
        data = None
        if self.all_data.ndim == 3:
            if self.c_dim == 0:
                data = self.all_data[self.c_idx,:,:]
            elif self.c_dim == 1:
                data = self.all_data[:, self.c_idx, :]
            elif self.c_dim == 2:
                data = self.all_data[:, :, self.c_idx]
        elif self.all_data.ndim == 2:
            data = self.all_data[:]
        elif self.all_data.ndim == 1:
            data = array([self.all_data[:]])
        else:
            data = array([[self.all_data.getValue()]])
        name = self.name
        if self.all_data.ndim == 3:
            name += " slice " + str(self.c_idx) +  " in dim " + str(self.c_dim)
        model = TableModel(data[:], name)
        self.table.setModel(model)


class MyQTableView(QTableView):
    """
    Display of the 2D or 1D data selected. Header functionality defined here, also for data choosing x,y, u, e.

    TODO: as for main variables, maybe add functionality of double click to plot data directly?
    """
    def __init__(self, master):
        super(MyQTableView, self).__init__()
        self.currentData = None
        self.master = master
        self.curridx = None
        self.hd = self.horizontalHeader()
        self.hd.setSectionsClickable(True)
        self.hd.sectionClicked.connect(self.hheader_selected)
        self.vd = self.verticalHeader()
        self.vd.setSectionsClickable(True)
        self.vd.sectionClicked.connect(self.vheader_selected)

    def keyPressEvent(self, event):
        if event.text() == "x":
            self.master.mdata.x.set(self.currentData, " ".join([self.model().name, self.curridx]))
        elif event.text() == "y":
            self.master.mdata.y.set(self.currentData, " ".join([self.model().name, self.curridx]))
        elif event.text() == "u":
            self.master.mdata.yerr.set(self.currentData, " ".join([self.model().name, self.curridx]))
        elif event.text() == "e":
            self.master.mdata.xerr.set(self.currentData, " ".join([self.model().name, self.curridx]))
        #elif event.text() == "m":
        #    self.master.mdata.mask.set(self.currentData, " ".join([self.model().name, self.curridx]))

    def hheader_selected(self, index):
        """
        these are the columns
        """
        cols = {cols.column() for cols in self.selectedIndexes()}

        if len(cols) > 1:
            self.currentData = array([self.model()._data[:, col] for col in cols])
            self.curridx = "cols. " + str(min(cols)) + " - " + str(max(cols))
            print("selected columns " + str(min(cols)) + " - " + str(max(cols)))
        else:
            self.curridx = "col " + str(index)
            self.currentData = self.model()._data[:, index]
            print("selected column " + str(index))

    def vheader_selected(self, index):
        """
        these are the rows
        """
        rows = {rows.row() for rows in self.selectedIndexes()}

        if len(rows) > 1:
            self.currentData = array([self.model()._data[row, :] for row in rows])
            self.curridx = "rows. " + str(min(rows)) + " - " + str(max(rows))
            print("selected rows " + str(min(rows)) + " - " + str(max(rows)))
        else:
            self.curridx = "row " + str(index)
            self.currentData = self.model()._data[index, :]
            print("selected row " + str(index))


class TableModel(QtCore.QAbstractTableModel):
    """
    Model of the data displayed in MyQTableView.
    """
    def __init__(self, data, name):
        super(TableModel, self).__init__()
        self._data = data
        self.name = name

    def data(self, index, role):
        if role == QtCore.Qt.DisplayRole:
            # See below for the nested-list data structure.
            # .row() indexes into the outer list,
            # .column() indexes into the sub-list
            return str(self._data[index.row(), index.column()])

    def rowCount(self, index):
        return self._data.shape[0]

    def columnCount(self, index):
        if len(self._data.shape) > 1:
            my_col = self._data.shape[1]
        else:
            my_col = 0
        return my_col


class Data(object):
    """
    Data for line plots with x, y and xerr and yerr
    """
    def __init__(self, **kwargs):
        for key in ["x", "y", "xerr", "yerr"]: #, "mask"]:
            setattr(self, key, MyQLabel(key, None))
        self.__dict__.update(kwargs)


class MyQLabel(QLabel):
    """
    implements clickable QLabel that performs action on itself: delete text and associated value.
    """
    def __init__(self, dataname, datavalue, extra=": "):
        super(MyQLabel, self).__init__()
        self.datavalue = datavalue
        self.setText(dataname.ljust(5) + extra)
        self.name = dataname.ljust(5)
        newfont = QFont("Mono", 8, QFont.Normal)
        self.setFont(newfont)

    def set(self, value, name):
        self.setText(self.name + ": " + name)
        self.datavalue = value

    def mousePressEvent(self, event):
        self.setText(self.name + ": ")
        self.datavalue = None


class App(QMainWindow):
    """
    Main Application to hold the file display and detachable the table data
    """
    def __init__(self, this_file, name):
        super(App, self).__init__()
        self.mfile = None
        self.model = None
        self.name = name
        self.view = None
        self.mdata = Data()
        self.holdon = False
        self.active1D = None
        here = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(here,"config.yml")) as fid:
            self.config = yaml.load(fid, yaml.Loader)
        self.holdbutton = None
        self.load_file(this_file)
        self.setMenuBar(FileMenu(self))
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.resize(self.config["Startingsize"]["Mainwindow"]["width"],
                            self.config["Startingsize"]["Mainwindow"]["height"])

    def fix1d_data(self):
        if self.mdata.y.datavalue is None:
            self.mdata.y.set(self.mdata.x.datavalue, self.mdata.x.text().split(": ")[1])
            self.mdata.x.set(arange((self.mdata.x.datavalue.shape[-1])), "index")
            self.mdata.yerr.set(self.mdata.xerr.datavalue, self.mdata.xerr.text().split(": ")[1])
        if self.mdata.x.datavalue is None:
            self.mdata.x.set(arange((self.mdata.y.datavalue.shape[-1])), "index")

    def plotit(self):
        self.fix1d_data()
        if self.holdon:
            self.active1D.update_plot(self.mdata)
        else:
            self.active1D = Fast1D(self.mdata, **self.config["Startingsize"]["1Dplot"])

    def holdit(self):
        if self.holdon:
            self.holdon = False
            self.holdbutton.setText("hold")
        else:
            self.holdon = True
            self.holdbutton.setText("release")

    def plotarea_layout(self):
        plotarea = QWidget()
        plotaeralayout = QHBoxLayout()
        self.holdbutton = QPushButton("hold")
        plotbutton = QPushButton("plot")
        self.holdbutton.clicked.connect(self.holdit)
        plotbutton.clicked.connect(self.plotit)
        plotaeralayout.addWidget(self.holdbutton)
        plotaeralayout.addWidget(plotbutton)
        plotarea.setLayout(plotaeralayout)
        return plotarea

    def make_design(self):
        """setup the layout of the Main window"""
        self.model = QStandardItemModel()
        mainwidget = QWidget()
        layout = QVBoxLayout()
        self.view = MyQTreeView(self)
        layout.addWidget(self.view)
        layout.addWidget(self.plotarea_layout())
        showtext = QWidget()
        showtext_layout = QVBoxLayout()
        for entr in self.mdata.__dict__.keys():
            showtext_layout.addWidget(self.mdata.__dict__[entr])
        showtext.setLayout(showtext_layout)
        layout.addWidget(showtext)
        mainwidget.setLayout(layout)
        self.setCentralWidget(mainwidget)
        # self.view.header().setResizeMode(QHeaderView.ResizeToContents)
        self.view.doubleClicked.connect(self.get_data)
        self.view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.model.setHorizontalHeaderLabels(self.config["Headers"].keys())
        self.view.setModel(self.model)
        self.view.setUniformRowHeights(True)
        for idx, key in enumerate(self.config["Headers"]):
            width = self.config["Headers"][key]
            self.view.setColumnWidth(idx, width)
        #self.view.header().setSectionResizeMode(0, QHeaderView.Stretch)

    def load_file(self, m_file):
        self.name = os.path.basename(m_file)
        try:
            self.mfile.close()
        except AttributeError:
            pass
        try:
            self.mfile = netCDF4.Dataset(m_file)
        except OSError:
            self.mfile = hdf4_object(m_file)
        statusbar = QStatusBar()
        statusbar.showMessage(self.name)
        self.setStatusBar(statusbar)
        self.make_design()
        if isinstance(self.mfile, netCDF4._netCDF4.Dataset):
            self.walk_down_netcdf(self.mfile, self.model)
        else:
            self.walk_down_hdf4(self.mfile.struct, self.model)

    def get_data(self, signal):
        if self.model.itemFromIndex(signal).mdata.ndim < 4:
            thisdata = self.model.itemFromIndex(signal).mdata
        else:
            print("dimensionality of data is too big. Not yet implemented.")
            return
        if thisdata.ndim == 3:
            Fast3D(thisdata[:], parent=self, **self.config["Startingsize"]["3Dplot"])
        elif thisdata.ndim == 2:
            Fast2D(thisdata[:], **self.config["Startingsize"]["2Dplot"])
        elif thisdata.ndim == 1:
            mdata = Data()
            mdata.x.set(arange(len(thisdata[:])), "index")
            mdata.y.set(thisdata[:], thisdata.name)
            if self.holdon:
                self.active1D.update_plot(mdata)
            else:
                self.active1D = Fast1D(mdata, **self.config["Startingsize"]["1Dplot"])
        else:
            print("nothing to plot, it seems to be a scalar")

    def walk_down_netcdf(self, currentlevel, currentitemlevel):
        if isinstance(currentitemlevel, str):
            currentitemlevel = Pointer(currentlevel, currentitemlevel)
        else:
            attrs = ", ".join([str(attr) for attr in currentlevel.ncattrs()])
            currentitemlevel.appendRow([
                self.walk_down_netcdf(currentlevel, self.name), QStandardItem(""), QStandardItem(""),
                QStandardItem(""), QStandardItem(""), QStandardItem(""), QStandardItem(attrs)])
            return currentitemlevel
        try:
            totallist = list(currentlevel.groups.keys())
        except KeyError:
            totallist = []
        try:
            totallist.extend(list(currentlevel.variables.keys()))
        except KeyError:
            pass
        for mkey in totallist:
            try:
                attrs = ", ".join([str(attr) for attr in currentlevel[mkey].ncattrs()])
                try:
                    ndim = str(currentlevel[mkey].ndim)
                except (AttributeError, KeyError):
                    ndim = ""
                try:
                    dims = ", ".join([str(dim) for dim in currentlevel[mkey].dimensions])
                except (AttributeError, KeyError):
                    dims = ""
                try:
                    shape = " x ".join([str(entr) for entr in currentlevel[mkey].shape])
                except (AttributeError, KeyError):
                    shape = ""
                try:
                    units = str(currentlevel[mkey].units)
                except (AttributeError, KeyError):
                    units = ""
                try:
                    dtype = str(currentlevel[mkey].dtype)
                except (AttributeError, KeyError):
                    dtype = ""
                last = [self.walk_down_netcdf(currentlevel[mkey], mkey), QStandardItem(ndim),
                        QStandardItem(shape), QStandardItem(dims), QStandardItem(units),
                        QStandardItem(dtype), QStandardItem(attrs)]
                currentitemlevel.appendRow(last)
            except Exception as exs:
                print(exs)
                print(type(exs))
        return currentitemlevel

    def walk_down_hdf4(self, currentlevel, currentitemlevel):
        if isinstance(currentitemlevel, str):
            currentitemlevel = Pointer(currentlevel, currentitemlevel)
        else:
            attrs = ", ".join([str(attr) for attr in currentlevel.attributes.keys()])
            currentitemlevel.appendRow([
                self.walk_down_hdf4(currentlevel, self.name), QStandardItem(""), QStandardItem(""),
                QStandardItem(""), QStandardItem(""), QStandardItem(""), QStandardItem(attrs)])
            return currentitemlevel
        try:
            totallist = list(currentlevel.keys())
        except (KeyError, AttributeError):
            totallist = []
            pass
        if len(totallist) > 0:
            for mkey in totallist:
                attrs = ", ".join([str(attr) for attr in mkey.data.attributes.keys()])
                try:
                    ndim = str(mkey.data.ndim)
                except (AttributeError, KeyError, TypeError):
                    ndim = ""
                try:
                    dims = ", ".join([str(dim) for dim in mkey.data.dimensions])
                except (AttributeError, KeyError, TypeError):
                    dims = ""
                try:
                    shape = " x ".join([str(entr) for entr in mkey.data.dims])
                except TypeError:
                    shape = str(mkey.data.dims)
                except (AttributeError, KeyError):
                    shape = ""
                try:
                    units = str(mkey.data.units)
                except (AttributeError, KeyError):
                    units = ""
                try:
                    dtype = str(mkey.data.stype)
                except (AttributeError, KeyError):
                    dtype = ""
                last = [self.walk_down_hdf4(currentlevel[mkey], mkey), QStandardItem(ndim),
                        QStandardItem(shape), QStandardItem(dims), QStandardItem(units),
                        QStandardItem(dtype), QStandardItem(attrs)]
                currentitemlevel.appendRow(last)
        return currentitemlevel

    def closeEvent(selfself, event):
        print("Close Viewer")

def main(myfile):
    name = os.path.basename(myfile)
    my_graphics = QApplication([name])
    myapp = App(myfile, name)
    myapp.show()
    sys.exit(my_graphics.exec_())


if __name__ == '__main__':
    mfile = sys.argv[1]
    main(mfile)
