"""Module to use with Fastplot and NetCDF4viewer to display tables"""
from PyQt5 import QtCore
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QFont, QKeySequence
from PyQt5.QtWidgets import (QApplication, QTreeView, QAbstractItemView, QMainWindow, QDockWidget,
                             QTableView, QSizePolicy, QWidget, QPushButton, QVBoxLayout, QHBoxLayout,
                             QSlider, QLabel, QStatusBar, QLineEdit)
import numpy as np

try:
    from .Colorschemes import QDarkPalette, reset_colors
except:
    from Colorschemes import QDarkPalette, reset_colors
try:
    from .Menues import  HelpWindow
except (ImportError, ModuleNotFoundError):
    from Menues import HelpWindow
try:
    from .Converters import Hdf4Object, Table, Representative, MFC_type, dictgen, read_txt
except (ImportError, ModuleNotFoundError):
    from Converters import Hdf4Object, Table, Representative, MFC_type, dictgen, read_txt

class MyTable(QWidget):
    """
    Class for the table to display a specific variable, hold the data and manage data which is actually displayed

    Variable cannot be higher than 3D
    """

    def __init__(self, master, data, name=None, header=None, headernames=None):
        """
        Initialize table

        :param master:  Main Window
        :param data:  data handle or ndnp.array
        """
        super(MyTable, self).__init__()
        self.master = master
        try:
            if master.dark:
                self.setPalette(QDarkPalette())
        except:
            if master.master.dark:
                self.setPalette(QDarkPalette())
        if name is None:
            self.name = data.name
        else:
            self.name = name
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
        if header is not None:
            hasheader = True
        else:
            hasheader = False
        self.table = MyQTableView(self.master, path, fillvalue, hasheader)
        self.c_idx = 0
        self.c_dim = 0
        self.c_idx2 = 0
        self.c_dim2 = 1
        try:
            self.maxidxs = np.squeeze(data.mdata[:]).shape
        except (AttributeError, IndexError, TypeError):
            try:
                self.maxidxs = np.squeeze(data[:]).shape
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
        if hasattr(data, "mdata"):
            if isinstance(data.mdata, Representative):
                self.all_data = np.squeeze(data.mdata.get_value())
            else:
                try:
                    self.all_data = np.squeeze(data.mdata[:])
                except:
                    self.all_data = np.np.array([data.mdata])
        else:
            self.all_data = np.squeeze(data)
        self.make_design()
        self.update_table(header, headernames)


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

    def make_slicer_layout(self, number=0, header=None):
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

    def on_click(self, header=None):
        try:
            idx = int(self.entry.text())
            if idx > self.maxidxs[self.c_dim] - 1:
                HelpWindow(self, "the index you chose is larger than the current dimension")
                return
            self.c_idx = idx
            self.sliceinfo.setText("slice " + str(self.c_idx) + "/ 0-" + str(self.maxidxs[self.c_dim] - 1))
            self.update_table(header)
        except ValueError:
            HelpWindow(self, "You need to type integer values")

    def on_click2(self, header=None):
        try:
            idx = int(self.entry2.text())
            if idx > self.maxidxs[self.c_dim2] - 1:
                HelpWindow(self, "the index you chose is larger than the current dimension")
                return
            self.c_idx2 = idx
            self.sliceinfo2.setText("slice " + str(self.c_idx2) + "/ 0-" + str(self.maxidxs[self.c_dim] - 1))
            self.update_table(header)
        except ValueError:
            HelpWindow(self, "You need to type integer values")

    def plus(self, header=None):
        """
        If underlying data is 3D, go on slice up.
        """
        if self.c_idx < self.maxidxs[self.c_dim] - 1:
            self.c_idx += 1
        else:
            self.c_idx = 0
        self.sliceinfo.setText("slice " + str(self.c_idx) + "/ 0-" + str(self.maxidxs[self.c_dim] - 1))
        self.update_table(header)

    def plus2(self, header=None):
        """
        If underlying data is 4D, go on slice up on second dim.
        """
        if self.c_idx2 < self.maxidxs[self.c_dim2] - 1:
            self.c_idx2 += 1
        else:
            self.c_idx2 = 0
        self.sliceinfo2.setText("slice " + str(self.c_idx2) + "/ 0-" + str(self.maxidxs[self.c_dim2] - 1))
        self.update_table(header)

    def minus(self, header=None):
        """
        If underlying data is 3D, go on slice down.
        """
        if self.c_idx > -self.maxidxs[self.c_dim]:
            self.c_idx -= 1
        else:
            self.c_idx = 0
        self.sliceinfo.setText("slice " + str(self.c_idx) + "/ 0-" + str(self.maxidxs[self.c_dim] - 1))
        self.update_table(header)

    def minus2(self, header=None):
        """
        If underlying data is 3D, go on slice down.
        """
        if self.c_idx2 > -self.maxidxs[self.c_dim2]:
            self.c_idx2 -= 1
        else:
            self.c_idx2 = 0
        self.sliceinfo2.setText("slice " + str(self.c_idx2) + "/ 0-" + str(self.maxidxs[self.c_dim2] - 1))
        self.update_table(header)

    def slicing(self, idx, header=None):
        """
        If underlying data is 3D, change the slicing dimension
        :param idx: int, which dimension to slice along
        """
        self.c_dim = idx
        self.diminfo.setText("dim " + str(self.c_dim))
        self.sliceinfo.setText("slice = " + (str(self.c_idx)) + "/ 0-" + str(self.maxidxs[self.c_dim] - 1))
        self.update_table(header)

    def slicing2(self, idx, header=None):
        """
        If underlying data is 4D, change the slicing dimension2
        :param idx: int, which dimension to slice along
        """
        self.c_dim2 = idx
        self.diminfo2.setText("dim " + str(self.c_dim2))
        self.sliceinfo2.setText("slice = " + (str(self.c_idx2)) + "/ 0-" + str(self.maxidxs[self.c_dim2] - 1))
        self.update_table(header)

    def update_table(self, header=None, headernames=None):
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
            data = np.array([self.all_data[:]])
        else:
            try:
                data = np.array([[self.all_data.getValue()]])
            except:
                data = np.array([[self.all_data]])
        name = self.name
        if ndim >= 3:
            name += " slice " + str(self.c_idx) + " in dim " + str(self.c_dim)
        if ndim == 4:
            name += " slice " + str(self.c_idx2) + " in dim " + str(self.c_dim2)
        if header is not None:
            pass
        else:
            try:
                header = self.all_data.header
            except:
                header = None
        model = TableModel(data[:], name, header, headernames)
        self.table.setModel(model)


class MyQTableView(QTableView):
    """
    Display of the 2D or 1D data selected. Header functionality defined here, also for data choosing x,y, u, e.

    TODO: as for main variables, maybe add functionality of double click to plot data directly? Difficult....
    """

    def __init__(self, master, path, fillvalue, hasheader=False):
        super(MyQTableView, self).__init__()
        self.hasheader = hasheader
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
                try:
                    self.master.mdata.x.set(self.currentData, ",".join([self.model().name, self.curridx]), self.path)
                except AttributeError:
                    self.master.master.mdata.x.set(self.currentData, ",".join([self.model().name, self.curridx]), self.path)
            elif event.text() == "y":
                try:
                    self.master.mdata.y.set(self.currentData, ",".join([self.model().name, self.curridx]), self.path)
                except AttributeError:
                    self.master.master.mdata.y.set(self.currentData, ",".join([self.model().name, self.curridx]), self.path)
            elif event.text() == "z":
                try:
                    self.master.mdata.z.set(self.currentData, ",".join([self.model().name, self.curridx]), self.path)
                except AttributeError:
                    self.master.master.mdata.z.set(self.currentData, ",".join([self.model().name, self.curridx]), self.path)
            elif event.text() == "u":
                try:
                    self.master.mdata.yerr.set(self.currentData, ",".join([self.model().name, self.curridx]), self.path)
                except:
                    self.master.master.mdata.yerr.set(self.currentData, ",".join([self.model().name, self.curridx]), self.path)
            elif event.text() == "e":
                try:
                    self.master.mdata.xerr.set(self.currentData, ",".join([self.model().name, self.curridx]), self.path)
                except AttributeError:
                    self.master.mdata.xerr.set(self.currentData, ",".join([self.model().name, self.curridx]), self.path)
            elif event.text() == "+":
                print("adding up ", " ".join([self.model().name, self.curridx]), nansum(self.currentData[self.currentData != self.fillvalue]))
            elif event.text() == "m":
                mdata = self.currentData
                mname = " ".join([self.model().name, self.curridx])
                try:
                    if self.master.mdata.misc.datavalue is None:
                        self.master.mdata.misc.set(np.squeeze(mdata), mname)
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
                except AttributeError:
                    if self.master.mdata.misc.datavalue is None:
                        self.master.master.mdata.misc.set(np.squeeze(mdata), mname)
                    else:
                        try:
                            if "+" in self.master.master.mdata.misc_op:
                                mdata = self.master.master.mdata.misc.datavalue + mdata
                            elif "-" in self.master.master.mdata.misc_op:
                                mdata = self.master.master.mdata.misc.datavalue - mdata
                            elif "/" in self.master.master.mdata.misc_op:
                                mdata = self.master.master.mdata.misc.datavalue / mdata
                            elif "*" in self.master.master.mdata.misc_op:
                                mdata = self.master.master.mdata.misc.datavalue * mdata
                            mname = self.master.master.mdata.misc.name_value + self.master.mdata.misc_op + mname
                            self.master.master.mdata.misc.set(mdata, mname)
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
            self.currentData = np.array([np.squeeze(self.model()._data[:, col]) for col in cols])
            self.curridx = "cols. " + str(min(cols)) + " - " + str(max(cols))
            print("selected columns " + str(min(cols)) + " - " + str(max(cols)))
        else:
            if self.hasheader:
                #print(help(self.hd))
                # TODO: somehow I need to give a label to the headers in the table model (x and y)
                self.curridx = self.model().headernames["x"]+"="+self.model().header["x"][index]
            else:
                self.curridx = "col=" + str(index)
            self.currentData = np.squeeze(self.model()._data[:, index])
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
            self.currentData = np.array([self.model()._data[row, :] for row in rows])
            self.curridx = "rows. " + str(min(rows)) + " - " + str(max(rows))
            print("selected rows " + str(min(rows)) + " - " + str(max(rows)))
        else:
            if self.hasheader:
                self.curridx = self.model().headernames["y"]+"="+self.model().header["y"][index]
            else:
                self.curridx = "row=" + str(index)
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

    def __init__(self, data, name, header, headernames={"x": None, "y": None}):
        super(TableModel, self).__init__()
        self._data = data
        self.name = name
        self.header = header
        self.headernames = headernames
        #set.setHorizontalHeaderLabels(['a', 'b', 'c', 'd', "e"])

    def headerData(self, column, orientation, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:
            if self.header is not None:
                if orientation == QtCore.Qt.Horizontal:
                    name = self.header["x"][column]
                    return QtCore.QVariant(name)
                elif orientation == QtCore.Qt.Vertical:
                    name = self.header["y"][column]
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

