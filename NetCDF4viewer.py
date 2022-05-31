import os
import sys
import netCDF4
import yaml
import numpy as np
import pyhdf.error
import pandas
import subprocess
import copy
from PyQt5 import QtCore
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QFont, QKeySequence
from PyQt5.QtWidgets import (QApplication, QTreeView, QAbstractItemView, QMainWindow, QDockWidget,
                             QTableView, QSizePolicy, QWidget, QPushButton, QVBoxLayout, QHBoxLayout,
                             QSlider, QLabel, QStatusBar, QLineEdit)

import matplotlib
try:
    from .Fastplot import Fast3D, Fast2D, Fast1D, Fast2Dplus
except (ImportError, ModuleNotFoundError):
    from Fastplot import Fast3D, Fast2D, Fast1D, Fast2Dplus
try:
    from .Menues import FileMenu, HelpWindow
except (ImportError, ModuleNotFoundError):
    from Menues import FileMenu, HelpWindow
try:
    from .Converters import Hdf4Object, Table, Representative, MFC_type, dictgen, read_txt
except (ImportError, ModuleNotFoundError):
    from Converters import Hdf4Object, Table, Representative, MFC_type, dictgen, read_txt
try:
    from .Colorschemes import QDarkPalette, reset_colors
except:
    from Colorschemes import QDarkPalette, reset_colors
try:
    from .MFC_orig import read_all
except:
    from MFC_orig import read_all

from numpy import array, arange, squeeze, nansum

CONFIGPATH = ""
C_LINES = None
#__version__ = "0.0.3"
#__author__ = "Martina M. Friedrich"


def dimming():
    '''
    dim screen for .1 second
    '''
    get = subprocess.check_output(["xrandr", "--verbose"]).decode("utf-8").split()
    for s in [get[i-1] for i in range(len(get)) if get[i] == "connected"]:
        br_data = float(get[get.index("Brightness:")+1])
        brightness = lambda br: ["xrandr", "--output", s, "--brightness", br]
        flash = ["sleep", "0.1"]
        for cmd in [brightness(str(br_data-0.1)), flash, brightness(str(br_data))]:
            subprocess.call(cmd)

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
        self.name_value = ""
        self.path = ""
        self.dimension = None

    def set(self, value, name, path="", dimension=None):
        self.setText(self.name + ": " + name)
        self.datavalue = value
        self.name_value = name
        self.dimension = dimension
        self.path = "/".join([path, self.name_value])

    def mousePressEvent(self, event):
        self.setText(self.name + ": ")
        self.datavalue = None

    def copy(self):
        class Dummy(object):
            def __init__(self, nme, val, dim):
                self.name_value = copy.deepcopy(nme)
                self.datavalue = copy.deepcopy(val)
                try:
                    self.dimension = copy.deepcopy(list(dim))
                except TypeError:
                    self.dimension = []
            def copy(self):
                newobj = Dummy(self.name_value, self.datavalue, self.dimension)
                return newobj
        newobj = Dummy(self.name_value, self.datavalue, self.dimension)
        return newobj


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
        self.name = name


class MyQTreeView(QTreeView):
    """
    Main class used to display the file structure. Define here the main Key actions (s->table, d->info, double->plot)

    Also, define here the data chooser events x, y, u, e to extract data as x, y yerr and xerr directly from file level
    """

    def __init__(self, master, *args, **kwargs):
        self.master = master
        self.tab = None
        super().__init__(*args, **kwargs)

    def keyPressEvent(self, event):
        idx = self.currentIndex()
        current_pointer = self.model().itemFromIndex(idx)
        try:
            try:
                mypath = current_pointer.mdata.group().path
            except:
                mypath = ""
            if event.text() == "d":
                print("   ")
                print("     INFO on ", current_pointer.name)
                print("----------------------------")
                if self.master.filetype == "netcdf4":
                    attributes = {key: current_pointer.mdata.getncattr(key) for key in
                                  current_pointer.mdata.ncattrs()}
                else:
                    print(current_pointer.mdata)
                    print("\n\n\n")
                    try:
                        attributes = current_pointer.name.data.attributes
                    except AttributeError:
                        attributes = current_pointer.mdata.attributes
                wids = []
                for attr in attributes:
                    if hasattr(attributes[attr], '__len__') and (len(attributes[attr]) > 5) \
                            and not isinstance(attributes[attr], str):
                        mdata = Table(attributes[attr], None, attr)
                        interm_pointer = Pointer(mdata, attr)
                        wids.append(self.open_table(interm_pointer))
                    elif isinstance(attributes[attr], str) and len(attributes[attr]) > 50000:
                        print(attr, ":      is currently not displayed. It is a very long string, "
                                    "likely describing the structure.")
                    elif isinstance(attributes[attr], dict):
                        mdata = attributes[attr]
                        for key in mdata:
                            name = ": ".join([attr, key])
                            mdat = Table(mdata[key], None, name)
                            interm_pointer = Pointer(mdat, name)
                            wids.append(self.open_table(interm_pointer))
                    else:
                        print(attr, ": ", attributes[attr])
                try:
                    one = wids.pop()
                    while len(wids) >= 1:
                        two = wids.pop()
                        if self.master.config["Tableview"]["tabbing"]:
                            self.master.tabifyDockWidget(one, two)
                except Exception as exc:
                    pass
                print(" ")
            elif event.text() == "s":
                # open tableview
                last_tab = self.tab
                self.tab = self.open_table(current_pointer)
                if last_tab is not None and self.master.config["Tableview"]["tabbing"]:
                    self.master.tabifyDockWidget(last_tab, self.tab)
            elif event.text() == "c":
                if isinstance(current_pointer, Representative):
                    tocopy = squeeze(current_pointer.mdata.get_value())
                else:
                    tocopy = squeeze(current_pointer.mdata[:])
                try:
                    (pandas.DataFrame(tocopy)).to_clipboard(index=False, header=False)
                    dimming()
                    print("copied", current_pointer.name)
                except Exception as exs:
                    try:
                        subprocess.run("xclip", universal_newlines=True, input=tocopy)
                        dimming()
                        print("copied", current_pointer.name)
                    except Exception as ecxs:
                        print(ecxs)
                        print("cannot copy")
            elif event.text() == "x":
                self.master.mdata.x.set(squeeze(current_pointer.mdata[:]), current_pointer.mdata.name, mypath,
                                        dimension=current_pointer.mdata.dimensions)
            elif event.text() == "y":
                self.master.mdata.y.set(squeeze(current_pointer.mdata[:]), current_pointer.mdata.name, mypath,
                                        dimension=current_pointer.mdata.dimensions)
            elif event.text() == "z":
                self.master.mdata.z.set(squeeze(current_pointer.mdata[:]), current_pointer.mdata.name, mypath,
                                        dimension=current_pointer.mdata.dimensions)
            elif event.text() == "u":
                self.master.mdata.yerr.set(squeeze(current_pointer.mdata[:]), current_pointer.mdata.name, mypath)
            elif event.text() == "e":
                self.master.mdata.xerr.set(squeeze(current_pointer.mdata[:]), current_pointer.mdata.name, mypath)
            elif event.text() == "f":
                self.master.mdata.flag.set(squeeze(current_pointer.mdata[:]), current_pointer.mdata.name, mypath)
            elif event.text() == "m":
                if self.master.mdata.misc.datavalue is None:
                    thisdims = tuple([mds for mds in current_pointer.mdata.dimensions if mds != 1])
                    self.master.mdata.misc.set(
                        squeeze(current_pointer.mdata[:].astype("float")), current_pointer.mdata.name, dimension=thisdims)
                else:
                    try:
                        if "+" in self.master.mdata.misc_op:
                            mdata = self.master.mdata.misc.datavalue + squeeze(current_pointer.mdata[:])
                        elif "-" in self.master.mdata.misc_op:
                            mdata = self.master.mdata.misc.datavalue - squeeze(current_pointer.mdata[:])
                        elif "/" in self.master.mdata.misc_op:
                            mdata = self.master.mdata.misc.datavalue / squeeze(current_pointer.mdata[:])
                        elif "*" in self.master.mdata.misc_op:
                            mdata = self.master.mdata.misc.datavalue * squeeze(current_pointer.mdata[:])
                        mname = self.master.mdata.misc.name_value+self.master.mdata.misc_op+current_pointer.mdata.name
                        self.master.mdata.misc.set(mdata, mname)
                    except ValueError as verr:
                        HelpWindow(self, "likely dimensions that don't fit together: " + str(verr))
                    except Exception as exc:
                        print("Something wen wrong:", exc)
        except TypeError as te:
            HelpWindow(self.master, "likely you clicked a group and pressed x, y, u or e. \n"
                                    "On groups, only d works to show details." + str(te))
        except AttributeError as err:
            HelpWindow(self.master, str(err)+
                       "something went wrong. Possibly you did not click in the first column of a variable\n"
                       " when clicking x,y,u,e or d. You have to be in the 'name' column when clicking.")

        # elif event.text() == "m":
        #    self.master.mdata.mask.set(current_pointer.mdata[:], current_pointer.mdata.name)

    def open_table(self, current_p):
        dock_widget = QDockWidget(current_p.name)
        if self.master.dark:
            dock_widget.setPalette(QDarkPalette())
        table_widget = MyTable(self.master, current_p)
        dock_widget.setWidget(table_widget)
        if "hor" in self.master.config["Tableview"]["stacking"].lower():
            stacking = QtCore.Qt.Horizontal
        else:
            stacking = QtCore.Qt.Vertical
        if "bottom" in self.master.config["Tableview"]["location"].lower():
            location = QtCore.Qt.BottomDockWidgetArea
        elif "top" in self.master.config["Tableview"]["location"].lower():
            location = QtCore.Qt.TopDockWidgetArea
        elif "right" in self.master.config["Tableview"]["location"].lower():
            location = QtCore.Qt.RightDockWidgetArea
        else:
            location = QtCore.Qt.LeftDockWidgetArea
        self.master.addDockWidget(location, dock_widget, stacking)
        return dock_widget


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
        if master.dark:
            self.setPalette(QDarkPalette())
        self.name = data.name
        fillvalue = np.nan
        try:
            path = data.mdata.group().path
        except:
            path = ""
        try:
            fillvalue = data.mdata._FillValue
        except AttributeError:
            try:
                for key in data.mdata.attributes:
                    if "fillvalue" in key.lower() or "fill_value" in key.lower():
                        fillvalue = data.mdata.attributes[key]
                        break
            except AttributeError:
                pass
        self.table = MyQTableView(self.master, path, fillvalue)
        self.c_idx = 0
        self.c_dim = 0
        self.c_idx2 = 0
        self.c_dim2 = 1
        try:
            self.maxidxs = squeeze(data.mdata[:]).shape
        except (AttributeError, IndexError, TypeError):
            self.maxidxs = [1]
        except Exception as exs:
            print(exs)
            HelpWindow(self, "You tried to open a group in table view or the variable has not data.\n"
                             " This is not possible. Open the group and view variables.")
            return
        self.diminfo = None
        self.sliceinfo = None
        self.diminfo2 = None
        self.slcieinfo2 = None
        if isinstance(data.mdata, Representative):
            self.all_data = squeeze(data.mdata.get_value())
        else:
            try:
                self.all_data = squeeze(data.mdata[:])
            except:
                self.all_data = np.array([data.mdata])
        self.make_design()
        self.update_table()


    def make_design(self):
        """
        Function to setup the layout of the table. If data is 3D, I need data selection options. Otherwise not.
        """
        table_layout = QHBoxLayout()
        table_layout.addWidget(self.table, 2)
        try:
            ndim = self.all_data.ndim
        except AttributeError:
            ndim = 1
        if ndim >= 3:
            choose_area = QWidget()
            choose_area_layout = QVBoxLayout()
            data_selection = self.make_slicer_layout()
            choose_area_layout.addWidget(data_selection)
            choose_area.setLayout(choose_area_layout)
            table_layout.addWidget(choose_area)
        if ndim == 4:
            data_selection = self.make_slicer_layout(1)
            choose_area_layout.addWidget(data_selection)
        elif ndim >=5:
            HelpWindow(self, "dimensionality of the data is too big, data cannot be displayed in a table")
        self.setLayout(table_layout)

    def make_slicer_layout(self, number=0):
        # areas and layouts
        data_selection = QWidget()
        data_selection.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        data_selection_layout = QHBoxLayout()
        slicer_area = QWidget()
        slicer_layout = QHBoxLayout()
        display_area = QWidget()
        display_layout = QVBoxLayout()
        entry_area = QWidget()
        entry_layout = QVBoxLayout()
        # objects
        slicer = QSlider()
        entry_label = QLabel("slice:")
        entry_layout.addWidget(entry_label, alignment=QtCore.Qt.AlignHCenter)
        entry_area.setLayout(entry_layout)
        if number == 0:
            self.entry = QLineEdit()
            self.entry.editingFinished.connect(self.on_click)
            self.entry.setFixedWidth(entry_label.fontMetrics().boundingRect("10000").width())
            #self.entry.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            entry_layout.addWidget(self.entry, alignment=QtCore.Qt.AlignHCenter)
            slicer.setRange(0, 2)
            slicer.valueChanged.connect(self.slicing)
            self.diminfo = QLabel("dim "+str(number))
            self.sliceinfo = QLabel("slice 0 / 0-" + str(self.maxidxs[number] - 1))
            self.sliceinfo.setFixedWidth(entry_label.fontMetrics().boundingRect("slice 10000/0-10000").width())
            display_layout.addWidget(self.diminfo)
            display_layout.addWidget(self.sliceinfo)
        elif number == 1:
            self.entry2 = QLineEdit()
            self.entry2.setFixedWidth(entry_label.fontMetrics().boundingRect("10000").width())
            #self.entry2.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            self.entry2.editingFinished.connect(self.on_click2)
            entry_layout.addWidget(self.entry2, alignment=QtCore.Qt.AlignHCenter)
            slicer.setRange(1, 3)
            slicer.valueChanged.connect(self.slicing2)
            self.diminfo2 = QLabel("dim "+str(number))
            self.sliceinfo2 = QLabel("slice 0 / 0-" + str(self.maxidxs[number] - 1))
            self.sliceinfo2.setFixedWidth(entry_label.fontMetrics().boundingRect("slice 10000/0-10000").width())
            display_layout.addWidget(self.diminfo2)
            display_layout.addWidget(self.sliceinfo2)
        plus = QPushButton("+")
        width = plus.fontMetrics().boundingRect("+").width() + 8
        plus.setMaximumWidth(width)
        minus = QPushButton("-")
        minus.setMaximumWidth(width)
        if number == 0:
            plus.clicked.connect(self.plus)
            minus.clicked.connect(self.minus)
        else:
            plus.clicked.connect(self.plus2)
            minus.clicked.connect(self.minus2)
        for obj in [minus, plus]:
            slicer_layout.addWidget(obj, alignment=QtCore.Qt.AlignHCenter)
        display_area.setLayout(display_layout)
        slicer_area.setLayout(slicer_layout)
        data_selection_layout.addWidget(slicer)
        data_selection_layout.addWidget(display_area)
        entry_layout.addWidget(slicer_area)
        data_selection_layout.addWidget(entry_area)
        data_selection.setLayout(data_selection_layout)
        return data_selection

    def on_click(self):
        try:
            idx = int(self.entry.text())
            if idx > self.maxidxs[self.c_dim] - 1:
                HelpWindow(self, "the index you chose is larger than the current dimension")
                return
            self.c_idx = idx
            self.sliceinfo.setText("slice " + str(self.c_idx) + "/ 0-" + str(self.maxidxs[self.c_dim] - 1))
            self.update_table()
        except ValueError:
            HelpWindow(self, "You need to type integer values")

    def on_click2(self):
        try:
            idx = int(self.entry2.text())
            if idx > self.maxidxs[self.c_dim2] - 1:
                HelpWindow(self, "the index you chose is larger than the current dimension")
                return
            self.c_idx2 = idx
            self.sliceinfo2.setText("slice " + str(self.c_idx2) + "/ 0-" + str(self.maxidxs[self.c_dim] - 1))
            self.update_table()
        except ValueError:
            HelpWindow(self, "You need to type integer values")

    def plus(self):
        """
        If underlying data is 3D, go on slice up.
        """
        if self.c_idx < self.maxidxs[self.c_dim] - 1:
            self.c_idx += 1
        else:
            self.c_idx = 0
        self.sliceinfo.setText("slice " + str(self.c_idx) + "/ 0-" + str(self.maxidxs[self.c_dim] - 1))
        self.update_table()

    def plus2(self):
        """
        If underlying data is 4D, go on slice up on second dim.
        """
        if self.c_idx2 < self.maxidxs[self.c_dim2] - 1:
            self.c_idx2 += 1
        else:
            self.c_idx2 = 0
        self.sliceinfo2.setText("slice " + str(self.c_idx2) + "/ 0-" + str(self.maxidxs[self.c_dim2] - 1))
        self.update_table()

    def minus(self):
        """
        If underlying data is 3D, go on slice down.
        """
        if self.c_idx > -self.maxidxs[self.c_dim]:
            self.c_idx -= 1
        else:
            self.c_idx = 0
        self.sliceinfo.setText("slice " + str(self.c_idx) + "/ 0-" + str(self.maxidxs[self.c_dim] - 1))
        self.update_table()

    def minus2(self):
        """
        If underlying data is 3D, go on slice down.
        """
        if self.c_idx2 > -self.maxidxs[self.c_dim2]:
            self.c_idx2 -= 1
        else:
            self.c_idx2 = 0
        self.sliceinfo2.setText("slice " + str(self.c_idx2) + "/ 0-" + str(self.maxidxs[self.c_dim2] - 1))
        self.update_table()

    def slicing(self, idx):
        """
        If underlying data is 3D, change the slicing dimension
        :param idx: int, which dimension to slice along
        """
        self.c_dim = idx
        self.diminfo.setText("dim " + str(self.c_dim))
        self.sliceinfo.setText("slice = " + (str(self.c_idx)) + "/ 0-" + str(self.maxidxs[self.c_dim] - 1))
        self.update_table()

    def slicing2(self, idx):
        """
        If underlying data is 4D, change the slicing dimension2
        :param idx: int, which dimension to slice along
        """
        self.c_dim2 = idx
        self.diminfo2.setText("dim " + str(self.c_dim2))
        self.sliceinfo2.setText("slice = " + (str(self.c_idx2)) + "/ 0-" + str(self.maxidxs[self.c_dim2] - 1))
        self.update_table()

    def update_table(self):
        """
        If underlying data is 3D, change the displayed data to the new subset of all_data, depending on c_dim and c_idx
        """
        data = None
        try:
            ndim = self.all_data.ndim
        except:
            ndim = 1
        if ndim >= 3:
            if self.c_dim == 0:
                data = self.all_data[self.c_idx, :, :]
            elif self.c_dim == 1:
                data = self.all_data[:, self.c_idx, :]
            elif self.c_dim == 2:
                data = self.all_data[:, :, self.c_idx]
            if ndim == 4:
                if self.c_dim2 <= self.c_dim:
                    HelpWindow(self, "Please have the upper dimension strictly smaller than the lower one." +
                                     " Otherwise the displayed data is incorrect.")
                    return
                if self.c_dim2 == 1:
                    data = data[self.c_idx2, :, :]
                elif self.c_dim2 == 2:
                    data = data[:, self.c_idx2, :]
                elif self.c_dim2 == 3:
                    data = data[:, :, self.c_idx2]
                else:
                    HelpWindow(self, "dimensionality of the data too big")
                    return
        elif ndim == 2:
            data = self.all_data[:]
        elif ndim == 1:
            data = array([self.all_data[:]])
        else:
            try:
                data = array([[self.all_data.getValue()]])
            except:
                data = array([[self.all_data]])
        name = self.name
        if ndim >= 3:
            name += " slice " + str(self.c_idx) + " in dim " + str(self.c_dim)
        if ndim == 4:
            name += " slice " + str(self.c_idx2) + " in dim " + str(self.c_dim2)
        try:
            header = self.all_data.header
        except:
            header = None
        model = TableModel(data[:], name, header)
        self.table.setModel(model)


class MyQTableView(QTableView):
    """
    Display of the 2D or 1D data selected. Header functionality defined here, also for data choosing x,y, u, e.

    TODO: as for main variables, maybe add functionality of double click to plot data directly? Difficult....
    """

    def __init__(self, master, path, fillvalue):
        super(MyQTableView, self).__init__()
        self.fillvalue = fillvalue
        self.path = path
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
        try:
            if event.text() == "x":
                self.master.mdata.x.set(self.currentData, " ".join([self.model().name, self.curridx]), self.path)
            elif event.text() == "y":
                self.master.mdata.y.set(self.currentData, " ".join([self.model().name, self.curridx]), self.path)
            elif event.text() == "z":
                self.master.mdata.z.set(self.currentData, " ".join([self.model().name, self.curridx]), self.path)
            elif event.text() == "u":
                self.master.mdata.yerr.set(self.currentData, " ".join([self.model().name, self.curridx]), self.path)
            elif event.text() == "e":
                self.master.mdata.xerr.set(self.currentData, " ".join([self.model().name, self.curridx]), self.path)
            elif event.text() == "+":
                print("adding up ", " ".join([self.model().name, self.curridx]), nansum(self.currentData[self.currentData != self.fillvalue]))
            elif event.text() == "m":
                mdata = self.currentData
                mname = " ".join([self.model().name, self.curridx])
                if self.master.mdata.misc.datavalue is None:
                    self.master.mdata.misc.set(squeeze(mdata), mname)
                else:
                    try:
                        if "+" in self.master.mdata.misc_op:
                            mdata = self.master.mdata.misc.datavalue + mdata
                        elif "-" in self.master.mdata.misc_op:
                            mdata = self.master.mdata.misc.datavalue - mdata
                        elif "/" in self.master.mdata.misc_op:
                            mdata = self.master.mdata.misc.datavalue / mdata
                        elif "*" in self.master.mdata.misc_op:
                            mdata = self.master.mdata.misc.datavalue * mdata
                        mname = self.master.mdata.misc.name_value + self.master.mdata.misc_op + mname
                        self.master.mdata.misc.set(mdata, mname)
                    except ValueError as verr:
                        HelpWindow(self, "likely dimensions that don't fit together: " + str(verr))
                    except Exception as exc:
                        print("check what s wrong ", exc)
        except TypeError:
            HelpWindow(self, "You need to 'select' a row(s) or column(s) first.\n"
                             "When you 'release' you have to be ontop of the header as well\n"
                             "Whether or not you selected, will be written in the terminal.\n"
                             "It should say: 'selected row(s)/ column(s):    '. If it does not\n"
                             "Nothing was selected. Try again")

        # elif event.text() == "m":
        #    self.master.mdata.mask.set(self.currentData, " ".join([self.model().name, self.curridx]))

    def hheader_selected(self, index):
        """
        these are the columns
        """
        cols = {cols.column() for cols in self.selectedIndexes()}

        if len(cols) > 1:
            self.currentData = array([squeeze(self.model()._data[:, col]) for col in cols])
            self.curridx = "cols. " + str(min(cols)) + " - " + str(max(cols))
            print("selected columns " + str(min(cols)) + " - " + str(max(cols)))
        else:
            self.curridx = "col " + str(index)
            self.currentData = squeeze(self.model()._data[:, index])
        try:
            self.currentData = self.currentData.astype(float)
        except:
            pass

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
        try:
            self.currentData = self.currentData.astype(float)
        except:
            pass


class TableModel(QtCore.QAbstractTableModel):
    """
    Model of the data displayed in MyQTableView.
    """

    def __init__(self, data, name, header):
        super(TableModel, self).__init__()
        self._data = data
        self.name = name
        self.header = header

    def headerData(self, column, orientation, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal and self.header is not None:
                name = self.header[column]
                return QtCore.QVariant(name)
            else:
                return QtCore.QVariant(str(column))

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
    Data for line plots and 3,4 D pcolor with x, y and xerr and yerr
    """

    def __init__(self, **kwargs):
        for key in ["x", "y", "z", "xerr", "yerr", "misc", "flag"]:  # , "mask"]:
            if key == "xerr":
                key2 = "xerr(e)"
            elif key == "yerr":
                key2 = "yerr(u)"
            elif key == "misc":
                key2 = "misc(m)"
            elif key == "flag":
                key2 = "flag(f)"
            else:
                key2 = key
            setattr(self, key, MyQLabel(key2, None))
        self.__dict__.update(kwargs)
        self.misc_op = "+"
        self.flag_op = None
    def copy(self):
        new = Data(x=self.x.copy(), y=self.y.copy(), z=self.z.copy(), xerr=self.xerr.copy(),
                   yerr=self.yerr.copy(), misc=self.misc.copy(), flag=self.flag.copy())
        return new


class MyQButton(QPushButton):
    def __init__(self, *args):
        QPushButton.__init__(self, *args)
        self.symbol = "."

    def keyPressEvent(self, event):
        self.symbol = event.text()


class App(QMainWindow):
    """
    Main Application to hold the file display and detachable the table data
    """

    def __init__(self, this_file):
        super(App, self).__init__()
        if isinstance(this_file, str):
            name = os.path.basename(this_file)
        else:
            name = "test"
        self.setWindowTitle(name)
        self.mfile = None
        self.model = None
        self.name = name
        self.complete_name = name
        self.view = None
        self.plot_buttons = None
        self.mdata = Data()
        self.holdon = False
        self.only_indices = False
        self.active1D = None
        self.openplots = []
        self.plotaeralayout = None
        # here = os.path.dirname(os.path.abspath(__file__))
        with open(CONFIGPATH) as fid:
            self.config = yaml.load(fid, yaml.Loader)
        if "Colors" in self.config.keys():
            reset_colors(self.config["Colors"])
        try:
            self.dark = "dark" in self.config["Colorscheme"]["App"].lower()
            print("dark scheme")
        except:
            self.dark = False
        try:
            self.plotscheme = self.config["Colorscheme"]["plots"]
        except:
            self.plotscheme = "default"
        self.holdbutton = None
        self.filetype = None
        self.load_file(this_file)
        self.setMenuBar(FileMenu(self))
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.resize(self.config["Startingsize"]["Mainwindow"]["width"],
                    self.config["Startingsize"]["Mainwindow"]["height"])

    def fix1d_data(self):
        if self.mdata.y.datavalue is None:
            self.mdata.y.set(arange((self.mdata.x.datavalue.shape[-1])), "index")
            # self.mdata.y.set(self.mdata.x.datavalue, self.mdata.x.text().split(": ")[1])
            # self.mdata.x.set(arange((self.mdata.x.datavalue.shape[-1])), "index")
            # self.mdata.yerr.set(self.mdata.xerr.datavalue, self.mdata.xerr.text().split(": ")[1])
        if self.mdata.x.datavalue is None:
            self.mdata.x.set(arange((self.mdata.y.datavalue.shape[-1])), "index")

    def plotit(self, symbol=False):
        try:
            if self.mdata.z.datavalue is None:
                self.fix1d_data()
            if self.holdon:
                if self.mdata.z.datavalue is None:
                    try:
                        if self.only_indices:
                            self.active1D.update_plot(self.mdata, symbol, oi=self.current_idx)
                        else:
                            self.active1D.update_plot(self.mdata, symbol)
                    except ValueError as valerr:
                        HelpWindow(self, "Probably you chose to plot x-y with different dimensions? Errormessage:" +
                                str(valerr))
                    except TypeError as terr:
                        try:
                            if self.only_indices:
                                self.active1D.add_to_plot(self.mdata, only_indices=self.current_idx, symbol=symbol)
                            else:
                                self.active1D.add_to_plot(self.mdata, symbol=symbol)
                        except TypeError as terr2:
                            HelpWindow(self, "You try to add to a plot. This caused an error. Maybe that was not what you intended: " + str(terr))
                elif self.mdata.z.datavalue.ndim < 1 or self.mdata.z.datavalue.ndim > 3:
                        HelpWindow(self, "dimensionality of z value has to be 1,2,3 for now")
                        self.show()
                        return
                else:
                    if self.only_indices:
                        self.active1D.add_to_plot(self.mdata, only_indices=self.current_idx)
                    else:
                        self.active1D.add_to_plot(self.mdata)
            else:
                if self.mdata.z.datavalue is not None:
                    if self.mdata.z.datavalue.ndim < 1 or self.mdata.z.datavalue.ndim > 4:
                        HelpWindow(self, "dimensionality of z value has to be 1,2,3,4 for now")
                        self.show()
                        return
                    if self.mdata.z.datavalue.ndim <= 2:
                        if self.only_indices:
                            try:
                                temp = Fast2D(self,
                                    self.mdata, **self.config["Startingsize"]["2Dplot"],
                                    **self.config["Plotsettings"], mname=self.mdata.z.name_value,
                                    filename=self.name, dark=self.dark, plotscheme=self.plotscheme,
                                    only_indices=self.current_idx)
                            except AttributeError as exdf:
                                HelpWindow(self, "it seems there are no indices to use"+str(exdf))
                                return
                        else:
                            temp = Fast2D(self,
                                self.mdata, **self.config["Startingsize"]["2Dplot"],
                                **self.config["Plotsettings"], mname=self.mdata.z.name_value,
                                filename=self.name, dark=self.dark, plotscheme=self.plotscheme)
                    elif self.mdata.z.datavalue.ndim > 2:
                        temp = Fast2Dplus(self,
                                self.mdata, **self.config["Startingsize"]["2Dplot"],
                                **self.config["Plotsettings"], mname=self.mdata.z.name_value,
                                filename=self.name, dark=self.dark, plotscheme=self.plotscheme)
                        self.show()
                    self.openplots.append(temp)
                    #if self.mdata.z.datavalue.ndim == 1:
                    self.active1D = temp
                else:
                    if self.only_indices:
                        temp = Fast1D(
                            self, self.mdata, symbol, **self.config["Startingsize"]["1Dplot"], filename=self.name,
                            dark=self.dark, plotscheme=self.plotscheme, only_indices=self.current_idx)
                    else:
                        temp = Fast1D(self, self.mdata, symbol, **self.config["Startingsize"]["1Dplot"],
                              filename=self.name, dark=self.dark, plotscheme=self.plotscheme)
                    self.openplots.append(temp)
                    self.active1D = temp
        except AttributeError as  err:
            HelpWindow(self, str(err)+"It seems you have not set anything to plot. You need to mark row(s) or column(s)\n"
                             "and then hit at least x or y to have some plottable data. Try again")

    def plotitsymbol(self):
        if self.plotsymbol.symbol in ["o", "x", "<", ">", "*", ".", "^", "v", "1", "2", "3", "p", "h", "H", "D", "+"]:
            self.plotit(self.plotsymbol.symbol)
        else:
            HelpWindow(self, "try a different symbol, any of: o x < > * . ^ v 1 2 3 p h H D + ")

    def holdit(self):
        if self.holdon:
            self.holdon = False
            self.holdbutton.setText("hold")
        else:
            self.holdon = True
            self.holdbutton.setText("release")

    def use_indices(self):
        if self.only_indices:
            self.only_indices = False
            self.useidx.setText("use idxs?")
        else:
            self.only_indices = True
            self.useidx.setText("using idxs only")
            try:
                self.current_idx = self.active1D.current_idx
            except AttributeError:
                HelpWindow(self, "There is currently no active plot with current idx marked. If it was set before, that one is used.")

    def plotarea_layout(self):
        plotarea = QWidget()
        self.plotaeralayout = QHBoxLayout()
        self.holdbutton = QPushButton("hold")
        plotbutton = QPushButton("&plot line")
        plotbutton.setShortcut(QKeySequence.Print)
        self.plotsymbol = MyQButton("plot symbol")
        self.useidx = MyQButton("use idxs?")
        self.useidx.clicked.connect(self.use_indices)
        self.plotclines = MyQButton("add country lines")
        self.plotclines.clicked.connect(self.plot_country)
        self.holdbutton.clicked.connect(self.holdit)
        plotbutton.clicked.connect(self.plotit)
        self.plotsymbol.clicked.connect(self.plotitsymbol)
        self.plotaeralayout.addWidget(self.holdbutton)
        self.plotaeralayout.addWidget(plotbutton)
        self.plotaeralayout.addWidget(self.plotsymbol)
        self.plotaeralayout.addWidget(self.useidx)
        self.plotaeralayout.addWidget(self.plotclines)
        plotarea.setLayout(self.plotaeralayout)
        return plotarea

    def plot_country(self):
        global C_LINES
        if C_LINES is None:
            C_LINES = []
            here = os.path.dirname(os.path.abspath(__file__))
            with netCDF4.Dataset(os.path.join(here, "country_lines.h5")) as fid:
                for k in fid.variables:
                    C_LINES.append(fid[k][:])
                    temp = fid[k][:].copy()
                    temp[:,0] = temp[:,0]+360
                    C_LINES.append(temp)
                   
        ln_coll = matplotlib.collections.LineCollection(C_LINES, colors=self.config["Plotsettings"]["country_line_color"], linewidths=self.config["Plotsettings"]["country_line_thickness"])
        if self.active1D is None:
            self.openplots[-1].myfigure.axes.add_collection(ln_coll)
            self.openplots[-1].myfigure.draw()
        else:
            self.active1D.myfigure.axes.add_collection(ln_coll)
            self.active1D.myfigure.draw()

    def make_design(self):
        """setup the layout of the Main window"""
        self.model = QStandardItemModel()
        mainwidget = QWidget()
        layout = QVBoxLayout()
        self.view = MyQTreeView(self)
        layout.addWidget(self.view)
        if self.plot_buttons is None:
            self.plot_buttons = self.plotarea_layout()
        layout.addWidget(self.plot_buttons)
        showtext = QWidget()
        showall = QWidget()
        flag_widget = QWidget()
        flag_layout = QHBoxLayout()
        misc_widget = QWidget()
        misc_layout = QHBoxLayout()
        showall_layout = QVBoxLayout()
        showall_layout.addWidget(showtext)
        showtext_layout = QHBoxLayout()
        layout_xyz = QVBoxLayout()
        layout_errs = QVBoxLayout()
        xyz = QWidget()
        errs = QWidget()
        for entr in self.mdata.__dict__.keys():
            if ("misc_op" not in entr) and ("flag_op" not in entr):
                if "err" in entr:
                    layout_errs.addWidget(self.mdata.__dict__[entr])
                elif len(entr) == 1:
                    layout_xyz.addWidget(self.mdata.__dict__[entr])
                elif "flag" in entr:
                    flag_layout.addWidget(self.mdata.__dict__[entr])
                else:
                    misc_layout.addWidget(self.mdata.__dict__[entr])
        def get_number():
            try:
                try:
                    thisdims = list(self.mdata.misc.dimension)
                except Exception as exs:
                    thisdims = []
                num = float(entry.text())
                if self.mdata.misc.datavalue is None:
                    self.mdata.misc.set(num, str(num))
                else:
                    #try:
                    if "+" in self.mdata.misc_op:
                        mdata = self.mdata.misc.datavalue + num
                    elif "-" in self.mdata.misc_op:
                        mdata = self.mdata.misc.datavalue - num
                    elif "/" in self.mdata.misc_op:
                        mdata = self.mdata.misc.datavalue / num
                    elif "*" in self.mdata.misc_op:
                        mdata = self.mdata.misc.datavalue * num
                    elif "mean" in self.mdata.misc_op:
                        num = int(num)
                        try:
                            _ = thisdims.pop(num)
                        except IndexError:
                            HelpWindow("Please check if you chose a dimension that fits the data chosen in misc")
                            return
                        if (self.only_indices) and self.mdata.misc.datavalue.shape[num] == len(self.current_idx):
                            mdata = self.mdata.misc.datavalue.data
                            if num == 0:
                                mdata = mdata[self.current_idx]
                            elif num == 1:
                                mdata = mdata[:, self.current_idx,...]
                            elif num == 2:
                                mdata = mdata[:, :, self.current_idx,...]
                            elif num == 3:
                                mdata = mdata[:, :, :, self.current_idx,...]
                            elif num == 4:
                                mdata = mdata[:, :, :, :, self.current_idx,...]
                            else:
                                HelpWindow(self, "please choose a number that is smaller than the current dimension")
                                return
                            self.only_indices = False
                            mdata = np.nanmean(mdata, axis=num)
                        else:
                            mdata = np.nanmean(self.mdata.misc.datavalue, axis=num)
                        mdata = np.nanmean(self.mdata.misc.datavalue, axis=num)
                        num = " along axis "+str(num)
                    elif "median" in self.mdata.misc_op:
                        num = int(num)
                        try:
                            _ = thisdims.pop(num)
                        except IndexError:
                            HelpWindow("Please check if you chose a dimension that fits the data chosen in misc")
                            return
                        if (self.only_indices) and self.mdata.misc.datavalue.shape[num] == len(self.current_idx):
                            mdata = self.mdata.misc.datavalue.data
                            if num == 0:
                                mdata = mdata[self.current_idx]
                            elif num == 1:
                                mdata = mdata[:, self.current_idx,...]
                            elif num == 2:
                                mdata = mdata[:, :, self.current_idx,...]
                            elif num == 3:
                                mdata = mdata[:, :, :, self.current_idx,...]
                            elif num == 4:
                                mdata = mdata[:, :, :, :, self.current_idx,...]
                            else:
                                HelpWindow(self, "please choose a number that is smaller than the current dimension")
                                return
                            self.only_indices = False
                            mdata = np.nanmedian(mdata, axis=num)
                        else:
                            mdata = np.nanmedian(self.mdata.misc.datavalue.data, axis=num)
                        num = " along axis "+str(num)
                    mname = self.mdata.misc.name_value+" "+self.mdata.misc_op + str(num)
                    self.mdata.misc.set(mdata, mname, dimension=thisdims)
            except ValueError:
                pass
        def get_flag_number():
            try:
                num = float(flag_entry.text())
                
                mname = self.mdata.flag.name_value+" "+self.mdata.flag_op + str(num)
                # I need to check x,y,z, for the moment, assume z:
                if "<" in self.mdata.flag_op:
                    mdata = self.mdata.flag.datavalue < num
                elif "=" in self.mdata.flag_op:
                    mdata = self.mdata.flag.datavalue == num
                else:
                    mdata = self.mdata.flag.datavalue > num
                self.mdata.flag.set(mdata, mname)
                #zdata = np.copy(self.mdata.misc.datavalue)
                #zdata[~mdata] = np.nan
                #self.mdata.misc.set(zdata, self.mdata.misc.name_value + " at " + mname)
            except ValueError:
                print("no value found")
        # make flag_layout fields:
        flag_entry = QLineEdit()
        flag_entry.returnPressed.connect(get_flag_number)
        flag_entry.setFixedWidth(40)
        flag_layout.addWidget(flag_entry)
        for el in ["<", ">","=="]:
            button = QPushButton(el)
            width = button.fontMetrics().boundingRect(el).width() + 8
            button.setMaximumWidth(width)
            flag_layout.addWidget(button)
            def func_flag(el):
                self.mdata.flag_op = el
                self.mdata.flag.setText(self.mdata.flag.name + ": " + self.mdata.flag.name_value + " " + el)
            button.clicked.connect(lambda state, x=el: func_flag(x))
        for el in ["on x", "on y", "on z", "on misc"]:
            button = QPushButton(el)
            width = button.fontMetrics().boundingRect(el).width() + 8
            button.setMaximumWidth(width)
            flag_layout.addWidget(button)
            def apply_flag(el):
                my_flag = self.mdata.flag.datavalue
                name = self.mdata.flag.name_value
                to_use = el.split()[-1]
                myval = (np.ma.copy(self.mdata.__dict__[to_use].datavalue))
                if not isinstance(myval, np.ma.MaskedArray):
                    myval = np.ma.masked_array(myval, np.full(myval.shape, False))
                if not isinstance(myval.mask, np.ndarray):
                    myval.mask = np.full(myval.shape, False)
                myval.mask[~my_flag] = True
                my_name = self.mdata.__dict__[to_use].name_value + " only " + self.mdata.flag.name_value
                self.mdata.__dict__[to_use].set(myval, my_name, dimension=self.mdata.__dict__[to_use].dimension)
            button.clicked.connect(lambda state, x=el: apply_flag(x))
        flag_widget.setLayout(flag_layout)
        showall_layout.addWidget(flag_widget)
        # make misc_layout fieds:
        entry = QLineEdit()
        entry.returnPressed.connect(get_number)
        entry.setFixedWidth(40)
        ## self.entry.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        misc_layout.addWidget(entry) #, alignment=QtCore.Qt.AlignHCenter)
        for el in ["+", "-", "/", "*", "mean", "median"]:
            button = QPushButton(el)
            width = button.fontMetrics().boundingRect(el).width() + 8
            button.setMaximumWidth(width)
            misc_layout.addWidget(button)
            def func(el):
                #print(el)
                self.mdata.misc_op = el
            button.clicked.connect(lambda state, x=el: func(x))
        for use_as in ["as x", "as y", "as z"]:
            button = QPushButton(use_as)
            width = button.fontMetrics().boundingRect(use_as).width() + 8
            button.setMaximumWidth(width)
            misc_layout.addWidget(button)
            def funcxyz(which):
                val = self.mdata.misc.datavalue
                name = self.mdata.misc.name_value
                dims = self.mdata.misc.dimension
                if "x" in which:
                    self.mdata.x.set(val, name, dimension=dims)
                elif "y" in which:
                    self.mdata.y.set(val, name, dimension=dims)
                elif "z" in which:
                    self.mdata.z.set(val, name, dimension=dims)
            button.clicked.connect(lambda state, w=use_as: funcxyz(w))
        button_plot = QPushButton("plot misc")
        width = button_plot.fontMetrics().boundingRect("plot misc").width() + 8
        button_plot.setMaximumWidth(width)
        misc_layout.addWidget(button_plot)
        def plotmisc():
            if self.mdata.misc.datavalue.ndim >= 3:
                temp = Fast3D(self.mdata.misc.datavalue,
                parent=self, **self.config["Startingsize"]["3Dplot"],
                mname=self.mdata.misc.name_value, filename=self.name, dark=self.dark, plotscheme=self.plotscheme)
                self.openplots.append(temp)
            elif self.mdata.misc.datavalue.ndim == 2:
                if self.only_indices:
                    temp = Fast2D(self, self.mdata.misc.datavalue, parent=self,
                                  **self.config["Startingsize"]["2Dplot"],
                                  **self.config["Plotsettings"], mname=self.mdata.misc.name_value,
                                  filename=self.name, dark=self.dark,
                                  plotscheme=self.plotscheme, only_indices=self.current_idx)
                else:
                    temp = Fast2D(self, self.mdata.misc.datavalue,
                        parent=self, **self.config["Startingsize"]["2Dplot"], **self.config["Plotsettings"],
                        mname=self.mdata.misc.name_value, filename=self.name, dark=self.dark, plotscheme=self.plotscheme)
                self.openplots.append(temp)
            elif self.mdata.misc.datavalue.ndim == 1:
                mdata = Data()
                mdata.x.set(arange(len(self.mdata.misc.datavalue)), "index")
                mdata.y.set(self.mdata.misc.datavalue, self.mdata.misc.name_value)
                if self.holdon:
                    self.active1D.update_plot(mdata)
                else:
                    if self.only_indices:
                        print("my shape: ", mdata.shape)
                        temp = Fast1D(
                            self, mdata, **self.config["Startingsize"]["1Dplot"], mname=self.mdata.misc.name_value,
                            filename=self.name, dark=self.dark, plotscheme=self.plotscheme, only_indices=self.current_idx)
                    else:
                        temp = Fast1D(
                            self, mdata, **self.config["Startingsize"]["1Dplot"], mname=self.mdata.misc.name_value,
                            filename=self.name, dark=self.dark, plotscheme=self.plotscheme)
                    self.active1D = temp
                    self.openplots.append(temp)
        button_plot.clicked.connect(plotmisc)
        ## plus_button.resize(plus_button.sizeHint().width(), plus_button.sizeHint().height())
        misc_widget.setLayout(misc_layout)
        showall_layout.addWidget(misc_widget)
        # make xyz, xerr and yerr fields:
        xyz.setLayout(layout_xyz)
        errs.setLayout(layout_errs)
        showtext_layout.addWidget(xyz)
        showtext_layout.addWidget(errs)
        showtext.setLayout(showtext_layout)
        showall.setLayout(showall_layout)
        layout.addWidget(showall)
        mainwidget.setLayout(layout)
        self.setCentralWidget(mainwidget)
        # self.view.header().setResizeMode(QHeaderView.ResizeToContents)
        self.view.doubleClicked.connect(self.get_data)
        self.view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.model.setHorizontalHeaderLabels(self.config["Headers"]["Table"].keys())
        self.view.setModel(self.model)
        self.view.setUniformRowHeights(True)
        for idx, key in enumerate(self.config["Headers"]["Table"]):
            width = self.config["Headers"]["Table"][key]
            self.view.setColumnWidth(idx, width)

    def load_file(self, m_file):
        if isinstance(m_file, str):
            self.name = os.path.basename(m_file)
            self.complete_name = m_file
            print("loading file: ", m_file)
            if os.path.isdir(m_file):
                self.mfile = dictgen(read_all(m_file))
                self.filetype = "mfc"
            else:
                try:
                    self.mfile.close()
                except AttributeError:
                    pass
                try:
                    self.mfile = netCDF4.Dataset(m_file)
                    self.filetype = "netcdf4"
                except (OSError, UnicodeError):
                    try:
                        self.mfile = Hdf4Object(m_file)
                        self.filetype = "hdf4"
                    except pyhdf.error.HDF4Error:
                        try:
                            self.mfile = MFC_type(m_file)
                            if isinstance(self.mfile, str):
                                HelpWindow(self, self.mfile)
                                return
                            self.filetype = "mfc"
                        except:
                            try:
                                self.name = m_file
                                self.complete_name = m_file
                                self.filetype = "txt"
                                self.mfile = dictgen(read_txt(m_file))
                                if isinstance(self.mfile, str):
                                    HelpWindow(
                                    self, "Failed to open " + str(m_file) + "\n")
                            except:
                                HelpWindow(
                                    self, "This seems not to be a valid nc, hdf4 or hdf5 file: " + str(m_file) + "\n" +
                                    "If you believe it is, please report back")
                                return
        else:
            self.name = "internal"
            self.complete_name = "internal"
            self.mfile = dictgen(m_file)
            self.filetype = "mfc"
        statusbar = QStatusBar()
        statusbar.showMessage(self.name)
        self.setStatusBar(statusbar)
        self.make_design()
        if isinstance(self.mfile, netCDF4._netCDF4.Dataset):
            print("walking down nc/ hdf5")
            self.walk_down_netcdf(self.mfile, self.model)
        elif self.filetype == "hdf4":
            print("walking down hdf4")
            self.walk_down_hdf4(self.mfile.struct, self.model)
        elif self.filetype == "mfc":
            print("walking down mfc")
            self.walk_down_mfc(self.mfile, self.model)
        elif self.filetype == "txt":
            print("walking down txt")
            self.walk_down_mfc(self.mfile, self.model)
        else:
            print("hello???")
            HelpWindow(self, "This seems to be an unknown file format")
        self.setWindowTitle(self.name)

    def get_data(self, signal):
        try:
            if isinstance(self.model.itemFromIndex(signal).mdata, Representative):
                mydata = np.squeeze(self.model.itemFromIndex(signal).mdata.get_value())
            else:
                mydata = np.squeeze(self.model.itemFromIndex(signal).mdata[:])
            try:
                mydata_dims = self.model.itemFromIndex(signal).mdata.dimensions
            except:
                mydata_dims = None
            if mydata.ndim < 5:
                thisdata = self.model.itemFromIndex(signal).mdata
            else:
                print("dimensionality of data is too big. Not yet implemented.")
                return
        except AttributeError:
            HelpWindow(self, "you need to click the first column ('name'), \n" +
                             "not anything else in order to plot a variable or open a group")
            return
        except KeyError:
            HelpWindow(
                self,
                "It seems you tried to plot a group (double click plots). To open the group, click on the triangle")
            return
        except TypeError:
            try:
                #HelpWindow(self, "No data. Info on this element printed to console, dimensions and variables opened as variables")
                for dim in self.model.itemFromIndex(signal).mdata.dimensions:
                    temp = Pointer(self.model.itemFromIndex(signal).mdata.dimensions[dim].size, dim)
                    last_tab = self.view.tab
                    self.view.tab = self.view.open_table(temp)
                    if last_tab is not None and self.config["Tableview"]["tabbing"]:
                        self.tabifyDockWidget(last_tab, self.view.tab)
            except Exception as ex:
                HelpWindow(self, str(ex)+"cannot plot data or display information")
            return
        if mydata.ndim >= 3:
            temp = Fast3D(
                mydata, parent=self, **self.config["Startingsize"]["3Dplot"],
                mname=thisdata.name, filename=self.name, dark=self.dark, plotscheme=self.plotscheme, mydata_dims=mydata_dims)
            self.openplots.append(temp)
        elif mydata.ndim == 2:
            if self.only_indices:
                temp = Fast2D(self,
                    mydata, parent=self, **self.config["Startingsize"]["2Dplot"], **self.config["Plotsettings"],
                    mname=thisdata.name, filename=self.name, dark=self.dark, plotscheme=self.plotscheme, only_indices=self.current_idx, mydata_dims=mydata_dims)
            else:
                temp = Fast2D(self,
                    mydata, parent=self, **self.config["Startingsize"]["2Dplot"], **self.config["Plotsettings"],
                    mname=thisdata.name, filename=self.name, dark=self.dark, plotscheme=self.plotscheme, mydata_dims=mydata_dims)
            self.openplots.append(temp)
        elif mydata.ndim == 1:
            mdata = Data()
            mdata.x.set(arange(len(mydata)), "index")
            mdata.y.set(mydata, thisdata.name)
            if self.holdon:
                if isinstance(self.active1D, Fast2D):
                    HelpWindow(self, "hold is on, but no suitable plot open. Plotting in 2D plots only with x or y set")
                else:
                    if self.active1D is not None:
                        self.active1D.update_plot(mdata)
                    else:
                        HelpWindow(self, "hold is on, but no suitable plot open")
            else:
                if self.only_indices:
                    temp = Fast1D(self,
                        mdata, **self.config["Startingsize"]["1Dplot"],
                        mname=thisdata.name, filename=self.name,
                        dark=self.dark, plotscheme=self.plotscheme, only_indices=self.current_idx, mydata_dims=mydata_dims)
                else:
                    temp = Fast1D(self,
                        mdata, **self.config["Startingsize"]["1Dplot"],
                        mname=thisdata.name, filename=self.name,
                        dark=self.dark, plotscheme=self.plotscheme, mydata_dims=mydata_dims)
                self.active1D = temp
                self.openplots.append(temp)
        else:
            HelpWindow(self, "nothing to plot, it seems to be a scalar")

    def walk_down_mfc(self, currentlevel, currentitemlevel):
        if isinstance(currentitemlevel, str):
            currentitemlevel = Pointer(currentlevel, currentitemlevel)
        else:
            attrs = ""
            currentitemlevel.appendRow([
                self.walk_down_mfc(currentlevel, self.name), QStandardItem(""), QStandardItem(""),
                QStandardItem(""), QStandardItem(""), QStandardItem(""), QStandardItem(attrs)])
            return currentitemlevel
        try:
            totallist = list(currentlevel.keys())
        except (KeyError, AttributeError):
            totallist = []
        for mkey in totallist:
            try:
                attrs = ""
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
                last = [self.walk_down_mfc(currentlevel[mkey], mkey), QStandardItem(ndim),
                        QStandardItem(shape), QStandardItem(dims), QStandardItem(units),
                        QStandardItem(dtype), QStandardItem(attrs)]
                currentitemlevel.appendRow(last)
            except Exception as exs:
                print("walking down mfc failed ", exs)
                print(type(exs))
        return currentitemlevel

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
                print("walking down netcdf failed ", exs)
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

    def closeEvent(self, event):
        print("Close Viewer")


def main(myfile=None):
    global CONFIGPATH
    if myfile is None:
        here = os.path.dirname(os.path.abspath(__file__))
        myfile = [os.path.join(here, "empty.nc")]
    if myfile[0][0] == "-":
        CONFIGPATH = myfile[0][1:]
        try:
            myfile = myfile[1:]
        except:
            myfile = "empty.nc"
    else:
        here = os.path.dirname(os.path.abspath(__file__))
        CONFIGPATH = os.path.join(here, "config.yml")
    name = os.path.basename(myfile[0])
    my_graphics = QApplication([name])
    # my_graphics.setStyle("Fusion")   .setStyleSheet("QWidget{font-size:30px;}");
    # my_graphics.setStyle(QStyleFactory.create('Cleanlooks'))
    with open(CONFIGPATH) as fid:
        config = yaml.load(fid, yaml.Loader)
    new_font = my_graphics.font()
    new_font.setPointSize(config["Startingsize"]["Fontsize"])
    my_graphics.setFont(new_font)
    #my_graphics.setStyleSheet(os.path.join(here, "qt_stylesheet.css"))
    main = App2(myfile)
    sys.exit(my_graphics.exec_())

def showdict(mydict):
    global CONFIGPATH
    here = os.path.dirname(os.path.abspath(__file__))
    CONFIGPATH = os.path.join(here, "config.yml")
    name = "test"
    my_graphics = QApplication([name])
    with open(CONFIGPATH) as fid:
        config = yaml.load(fid, yaml.Loader)
    new_font = my_graphics.font()
    new_font.setPointSize(config["Startingsize"]["Fontsize"])
    my_graphics.setFont(new_font)
    main = App(mydict)
    if "dark" in config["Colorscheme"]["App"]:
        palette = QDarkPalette()
        main.setPalette(palette)
    main.show()
    my_graphics.exec_()

class App2(QWidget):
    def __init__(self, files):
        super(App2, self).__init__()
        self.windows = []
        self.layout = QVBoxLayout()
        self.plus = QPushButton("broadcast plot")
        self.ssd = QPushButton("set same data")
        self.plus.clicked.connect(self.broadcast)
        self.ssd.clicked.connect(self.set_same_data)
        self.layout.addWidget(self.plus)
        self.layout.addWidget(self.ssd)
        for mfile in files:
            self.windows.append(App(mfile))
        if len(files) > 1:
            self.setLayout(self.layout)
            self.windows[0].plotaeralayout.addWidget(self)
        for ii in range(len(files)):
            if self.windows[ii].dark:
                self.palette = QDarkPalette()
                self.windows[ii].setPalette(self.palette)
            self.windows[ii].show()

    def broadcast(self):
        if self.windows[0].active1D is not None:
            for ii in range(1, len(self.windows)):
                self.windows[ii].active1D = self.windows[0].active1D
        else:
            try:
                self.windows[0].active1D = self.windows[0].openplots[-1]
                for ii in range(1, len(self.windows)):
                    self.windows[ii].active1D = self.windows[0].active1D
            except IndexError:
                HelpWindow(self, "it seems there are no open plot windows that are broadcastable")

    def set_same_data(self):
        for which in ["x", "y", "z", "flag(f)", "xerr(e)", "yerr(u)", "misc(m)"]:
            name = self.windows[0].mdata.__dict__[which.split("(")[0]].name_value
            path = self.windows[0].mdata.__dict__[which.split("(")[0]].path
            for idx in range(1, len(self.windows)):
                if len(path)> 0:
                    try:
                        mdata = self.windows[idx].mfile[path][:]
                        thisname = path
                    except TypeError as te:
                        HelpWindow(self, "setting same variables for x, y, z, ... is currently not supported for hdf4")
                        return
                    except KeyError as ke:
                        HelpWindow(self, "probably it was tried to set a variable as x,y,z, xerror or yerror that does not exist. The error message is: "+str(ke))
                        return
                    except IndexError:
                        try:
                            thisname, col = path.split(" col ")
                            mdata = self.windows[idx].mfile[thisname][:, int(col)]
                        except (ValueError, IndexError):
                            try:
                                thisname, row = path.split(" row ")
                                mdata = self.windows[idx].mfile[thisname][int(row), :]
                            except (IndexError, ValueError):
                                if "slice" in path:
                                    thisname, rest = path.split(" slice ")
                                    slice, rest = rest.split(" in dim ")
                                    try:
                                        dim, row = rest.split(" row ")
                                        if dim == "0":
                                            mdata = self.windows[idx].mfile[thisname][slice, row, :]
                                        elif dim == "1":
                                            mdata = self.windows[idx].mfile[thisname][row, slice, :]
                                        elif dim == "2":
                                            mdata = self.windows[idx].mfile[thisname][row, :, slice]
                                        else:
                                            HelpWindow(self, "currently, set same data only supports base data up to 3 dimensions")
                                            print("not supported right now")
                                            return
                                    except ValueError:
                                        dim, col = rest.split(" col ")
                                        if dim == "0":
                                            mdata = self.windows[idx].mfile[thisname][slice, :, col]
                                        elif dim == "1":
                                            mdata = self.windows[idx].mfile[thisname][:, slice, col]
                                        elif dim == "2":
                                            mdata = self.windows[idx].mfile[thisname][:, col, slice]
                                        else:
                                            HelpWindow(self, "currently, set same data only supports base data up to 3 dimensions")
                                            print("not supported right now")
                                            return
                    self.windows[idx].mdata.__dict__[which.split("(")[0]].set(mdata, name, thisname)

if __name__ == '__main__':
    
    mfile = sys.argv[1:]
    if len(mfile) > 0:
        main(mfile)
    else:
        main()
