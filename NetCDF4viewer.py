#!/usr/bin/python3
"""Main module to build data tree for show nc and hdf files"""
import os
import sys
import netCDF4
import yaml
import numpy as np
import pyhdf.error
import pandas
import subprocess
# import copy
import datetime
from PyQt5 import QtCore
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QKeySequence
from PyQt5.QtWidgets import (QApplication, QTreeView, QAbstractItemView, QMainWindow, QDockWidget,
                             QSizePolicy, QWidget, QPushButton, QVBoxLayout, QHBoxLayout,
                             QStatusBar, QLineEdit, QLabel, QScrollArea)
# from cftime import date2num, num2date

import matplotlib
try:
    from .Fastplot import Fast3D, Fast2D, Fast1D, Fast2Dplus, Fast2D_select
except (ImportError, ModuleNotFoundError):
    from Fastplot import Fast3D, Fast2D, Fast1D, Fast2Dplus, Fast2D_select
try:
    from .helper_tools import check_for_time
except (ImportError, ModuleNotFoundError):
    from helper_tools import check_for_time
try:
    from .Menues import FileMenu, HelpWindow
except (ImportError, ModuleNotFoundError):
    from Menues import FileMenu, HelpWindow
try:
    from .Converters import Hdf4Object, Table, Representative, MFC_type, dictgen, read_txt, Data
except (ImportError, ModuleNotFoundError):
    from Converters import Hdf4Object, Table, Representative, MFC_type, dictgen, read_txt, Data
try:
    from .Colorschemes import QDarkPalette, reset_colors
except:
    from Colorschemes import QDarkPalette, reset_colors
try:
    from .MFC_orig import read_all
except:
    from MFC_orig import read_all
try:
    from .Tables import MyTable
except:
    from Tables import MyTable

from numpy import arange, squeeze

CONFIGPATH = ""
C_LINES = None

# __version__ = "0.0.4"
# __author__ = "Martina M. Friedrich"

def dimming():
    '''
    dim screen for .1 second
    
    This was intended to be used to indicate copying, currently not used.
    '''
    get = subprocess.check_output(["xrandr", "--verbose"]).decode("utf-8").split()
    for s in [get[i - 1] for i in range(len(get)) if get[i] == "connected"]:
        br_data = float(get[get.index("Brightness:") + 1])
        brightness = lambda br: ["xrandr", "--output", s, "--brightness", br]
        flash = ["sleep", "0.1"]
        for cmd in [brightness(str(br_data - 0.1)), flash, brightness(str(br_data))]:
            subprocess.call(cmd)


class Pointer(QStandardItem):
    """
    class to add underlying data to an item in treeview
    """

    def __init__(self, mdata, name, path=""):
        """
        :param mdata: group of variable handle, underlying data
        :param name: string to be used in QStandardItem constructor
        """
        super(Pointer, self).__init__(name)
        self.mdata = mdata
        self.name = name
        self.path = path


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
                mydata, unit = check_for_time(current_pointer.mdata)
            except Exception as err:
                mydata = current_pointer.mdata
                unit = ""
                if event.text() not in  ["d", "a"]:
                    raise err
            # print("unit to set is: ", unit)
            try:
                mypath = current_pointer.mdata.group().path
            except:
                mypath = ""
            # try:
            #    unit = current_pointer.mdata.units
            # except Exception as err:
            #    print("no unit? ", err)
            #    unit = ""
            if event.text() == "d":
                print("   ")
                print("     INFO on ", current_pointer.name)
                print("----------------------------")
                if self.master.filetype == "netcdf4":
                    attributes = {key: current_pointer.mdata.getncattr(key) for key in
                                  current_pointer.mdata.ncattrs()}
                else:
                    #print(current_pointer.mdata)
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
                    elif isinstance(attributes[attr], str) and len(attributes[attr]) > 250000:
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
                last_tab = self.tab
                self.tab = self.open_infotab(attributes, current_pointer.name)
                if last_tab is not None and self.master.config["Tableview"]["tabbing"]:
                    self.master.tabifyDockWidget(last_tab, self.tab)
            elif event.text() == "a":
                print("     INFO on ", current_pointer.name)
                try:
                    my_dimensions = {current_pointer.mdata.dimensions[entr].name.ljust(50): 
                                         current_pointer.mdata.dimensions[entr].size for
                                         entr in current_pointer.mdata.dimensions}
                    self.tab = self.open_infotab(my_dimensions, current_pointer.name, which="dimensions ")
                except:
                    dimnames = current_pointer.mdata.dimensions
                    dimsizes = current_pointer.mdata.shape
                    try:
                        my_dimensions = {nm: sz for nm, sz in zip(dimnames, dimsizes)}
                    except Exception as ex:
                        print(ex)
                    self.tab = self.open_infotab(my_dimensions, current_pointer.name, which="dimensions ")
                for nam, val in my_dimensions.items():
                    print(nam, ":", val)
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
                    tocopy = squeeze(mydata)
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
                self.master.mdata.x.set(squeeze(mydata), current_pointer.mdata.name, mypath,
                                        dimension=current_pointer.mdata.dimensions, units=unit)
            elif event.text() == "y":
                print("The unit that is set is: , ", unit)
                self.master.mdata.y.set(squeeze(mydata), current_pointer.mdata.name, mypath,
                                        dimension=current_pointer.mdata.dimensions, units=unit)
                print(self.master.mdata.y.units)
            elif event.text() == "z":
                self.master.mdata.z.set(squeeze(mydata), current_pointer.mdata.name, mypath,
                                        dimension=current_pointer.mdata.dimensions, units=unit)
            elif event.text() == "u":
                self.master.mdata.yerr.set(squeeze(mydata), current_pointer.mdata.name, mypath, units=unit)
            elif event.text() == "e":
                self.master.mdata.xerr.set(squeeze(mydata), current_pointer.mdata.name, mypath, units=unit)
            elif event.text() == "f":
                self.master.mdata.flag.set(squeeze(mydata), current_pointer.mdata.name, mypath, units=unit)
            elif event.text() == "m":  # TODO: what to do for mfc?
                print("here")
                if self.master.filetype == "hdf4":
                    mval = "self.mfile.myrefdict[int("+str(current_pointer.mdata.myref)+")].get_value()"
                else:
                    mypath = current_pointer.mdata.group().path
                    if self.master.filetype == "mfc":
                        if mypath:
                            fullpath = "']['".join(mypath.lstrip("/").split("/"))
                        else:
                            fullpath = current_pointer.mdata.name
                    else:
                        fullpath = mypath+"/"+current_pointer.mdata.name
                    mval = "self.mfile['"+fullpath+"'][:]"
                    
                textshow = current_pointer.mdata.name
                if self.master.mdata.misc.datavalue is None:
                    self.master.mdata.misc.set(mval, textshow)
                else:
                    if not isinstance(self.master.mdata.misc.datavalue, str):
                        textshow = self.master.mdata.misc.name_value+textshow
                        temp = self.master.mdata.misc.datavalue
                        mval = eval("temp"+self.last_operator+"mval")
                        self.last_operator = None
                        
                    else:
                        textshow = self.master.mdata.misc.name_value+textshow
                        mval = self.master.mdata.misc.datavalue+mval
                    self.master.mdata.misc.set(mval, textshow)
                isold=False
                if isold:
                    if self.master.mdata.misc.datavalue is None:
                        thisdims = tuple([mds for mds in current_pointer.mdata.dimensions if mds != 1])
                        self.master.mdata.misc.set(
                            squeeze(mydata.astype("float")), current_pointer.mdata.name, dimension=thisdims, units=unit)
                    else:
                        try:
                            if "+" in self.master.mdata.misc_op:
                                mdata = self.master.mdata.misc.datavalue + squeeze(mydata)
                            elif "-" in self.master.mdata.misc_op:
                                mdata = self.master.mdata.misc.datavalue - squeeze(mydata)
                            elif "/" in self.master.mdata.misc_op:
                                mdata = self.master.mdata.misc.datavalue / squeeze(mydata)
                            elif "*" in self.master.mdata.misc_op:
                                mdata = self.master.mdata.misc.datavalue * squeeze(mydata)
                            mname = self.master.mdata.misc.name_value + self.master.mdata.misc_op + current_pointer.mdata.name
                            self.master.mdata.misc.set(mdata, mname)
                        except ValueError as verr:
                            HelpWindow(self, "likely dimensions that don't fit together: " + str(verr))
                        except Exception as exc:
                            print("Something wen wrong:", exc)
        except TypeError as te:
            HelpWindow(self.master, "likely you clicked a group and pressed x, y, u or e. \n"
                                    "On groups, only d and a works to show details and dimensions, respectively." + str(te))
        except AttributeError as err:
            HelpWindow(self.master, str(err) +
                       "something went wrong. Possibly you did not click in the first column of a variable\n"
                       " when clicking x,y,u,e or d. You have to be in the 'name' column when clicking.")

    def open_infotab(self, mlist, varname, which="attributes "):
        dock_widget = QDockWidget(which + varname)
        if self.master.dark:
            dock_widget.setPalette(QDarkPalette())
        canvas_widget = ScrollLabel()
        dock_widget.setWidget(canvas_widget)
        mtext = "\n".join([" " + key + ":\t " + str(mlist[key]) for key in mlist])
        canvas_widget.setText(mtext)
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

    def open_table(self, current_p):
        """
        open the current variable (located at current_p) as table view
        """
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
        print("------------")
        print(self.complete_name)
        self.view = None
        self.plot_buttons = None
        self.mdata = Data()
        self.holdon = False
        self.only_indices = False
        self.active1D = None
        self.openplots = []
        self.plotaeralayout = None
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
        self.config["this_file"] = CONFIGPATH
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
                            HelpWindow(self,
                                       "You try to add to a plot. This caused an error. Maybe that was not what you intended: " +
                                       str(terr))
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
                                HelpWindow(self, "it seems there are no indices to use" + str(exdf))
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
                    # if self.mdata.z.datavalue.ndim == 1:
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
        except AttributeError as err:
            HelpWindow(self,
                       str(err) + "It seems you have not set anything to plot. You need to mark row(s) or column(s)\n"
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
                HelpWindow(self,
                           "There is currently no active plot with current idx marked. If it was set before, that one is used.")

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
                    temp[:, 0] = temp[:, 0] + 360
                    C_LINES.append(temp)

        ln_coll = matplotlib.collections.LineCollection(C_LINES,
                                                        colors=self.config["Plotsettings"]["country_line_color"],
                                                        linewidths=self.config["Plotsettings"][
                                                            "country_line_thickness"])
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
            #try:
                try:
                    thisdims = list(self.mdata.misc.dimension)
                    if len(thisdims) == 0:
                        raise ValueError()
                except Exception as exs:
                    thisdims = []
                previousvalue = self.mdata.misc.datavalue
                previoustext = self.mdata.misc.name_value
                newtext = self.mentry.text()
                self.mentry.clear()
                try:
                    if not previoustext: previoustext = ""
                except ValueError:
                    pass
                try:
                    if not previousvalue: previousvalue = ""
                except ValueError:
                    pass
                try:
                    self.mdata.misc.set(previousvalue+newtext, previoustext + newtext)
                except:
                    temp = previousvalue
                    try:
                        self.mdata.misc.set(eval("temp"+newtext), previoustext + newtext)
                    except:
                        self.last_operator = newtext
                        self.mdata.misc.set(temp, previoustext + newtext)
                        #from PyQt5.QtCore import pyqtRemoveInputHook
                        #pyqtRemoveInputHook()
                        #import pdb
                        #pdb.set_trace()
                return
                '''
                num = float(self.mentry.text())
                if self.mdata.misc.datavalue is None:
                    self.mdata.misc.set(num, str(num))
                else:
                    # try:
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
                                mdata = mdata[:, self.current_idx, ...]
                            elif num == 2:
                                mdata = mdata[:, :, self.current_idx, ...]
                            elif num == 3:
                                mdata = mdata[:, :, :, self.current_idx, ...]
                            elif num == 4:
                                mdata = mdata[:, :, :, :, self.current_idx, ...]
                            else:
                                HelpWindow(self, "please choose a number that is smaller than the current dimension")
                                return
                            self.only_indices = False
                            mdata = np.nanmean(mdata, axis=num)
                        else:
                            mdata = np.nanmean(self.mdata.misc.datavalue, axis=num)
                        mdata = np.nanmean(self.mdata.misc.datavalue, axis=num)
                        num = " along axis " + str(num)
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
                                mdata = mdata[:, self.current_idx, ...]
                            elif num == 2:
                                mdata = mdata[:, :, self.current_idx, ...]
                            elif num == 3:
                                mdata = mdata[:, :, :, self.current_idx, ...]
                            elif num == 4:
                                mdata = mdata[:, :, :, :, self.current_idx, ...]
                            else:
                                HelpWindow(self, "please choose a number that is smaller than the current dimension")
                                return
                            self.only_indices = False
                            mdata = np.nanmedian(mdata, axis=num)
                        else:
                            mdata = np.nanmedian(self.mdata.misc.datavalue.data, axis=num)
                        num = " along axis " + str(num)
                    mname = self.mdata.misc.name_value + " " + self.mdata.misc_op + str(num)
                    self.mdata.misc.set(mdata, mname, dimension=thisdims)
            except ValueError:
                pass
            '''

        def get_flag_number():
            try:
                num = float(flag_entry.text())
                mname = self.mdata.flag.name_value + " " + self.mdata.flag_op + str(num)
                # I need to check x,y,z, for the moment, assume z:
                if "<" in self.mdata.flag_op:
                    mdata = self.mdata.flag.datavalue < num
                elif "=" in self.mdata.flag_op:
                    mdata = self.mdata.flag.datavalue == num
                else:
                    mdata = self.mdata.flag.datavalue > num
                self.mdata.flag.set(mdata, mname)
                # zdata = np.copy(self.mdata.misc.datavalue)
                # zdata[~mdata] = np.nan
                # self.mdata.misc.set(zdata, self.mdata.misc.name_value + " at " + mname)
            except ValueError:
                print("no value found")
            except TypeError:
                print("maybe no flag chosen?")

        # make flag_layout fields:
        flag_entry = QLineEdit()
        flag_entry.returnPressed.connect(get_flag_number)
        flag_entry.setFixedWidth(40)
        flag_layout.addWidget(flag_entry)
        for el in ["<", ">", "=="]:
            button = QPushButton(el)
            width = button.fontMetrics().boundingRect(el).width() + 8
            button.setMaximumWidth(width)
            flag_layout.addWidget(button)

            def func_flag(el):
                self.mdata.flag_op = el
                self.mdata.flag.setText(self.mdata.flag.name + ": " + self.mdata.flag.name_value + " " + el)

            button.clicked.connect(lambda state, x=el: func_flag(x))
        for el in ["on x", "on y", "on z"]:  #TODO: on misc needs rework, "on misc"
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
                try:
                    myval.mask[~my_flag] = True
                    my_name = self.mdata.__dict__[to_use].name_value + " only " + self.mdata.flag.name_value
                    self.mdata.__dict__[to_use].set(myval, my_name, dimension=self.mdata.__dict__[to_use].dimension)
                except IndexError as exc:
                    HelpWindow(self, "probably flag and x,y have different dimensions: "+str(exc))
                except TypeError:
                    HelpWindow(self, "check your flag condition, something went wrong there")
            button.clicked.connect(lambda state, x=el: apply_flag(x))
        flag_widget.setLayout(flag_layout)
        showall_layout.addWidget(flag_widget)
        self.mentry = QLineEdit()
        self.mentry.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.mentry.returnPressed.connect(get_number)
        self.mentry.editingFinished.connect(get_number)

        ## self.entry.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        misc_layout.addWidget(self.mentry)  # , alignment=QtCore.Qt.AlignHCenter)
        for use_as in ["as x", "as y", "as z"]:
            button = QPushButton(use_as)
            width = button.fontMetrics().boundingRect(use_as).width() + 8
            button.setMaximumWidth(width)
            misc_layout.addWidget(button)
            def funcxyz(which):
                try:
                    val = eval(self.mdata.misc.datavalue)
                except:
                    val = self.mdata.misc.datavalue
                name = self.mdata.misc.name_value
                if "x" in which:
                    self.mdata.x.set(val, name)
                elif "y" in which:
                    self.mdata.y.set(val, name)
                elif "z" in which:
                    self.mdata.z.set(val, name)
            button.clicked.connect(lambda state, w=use_as: funcxyz(w))
        button_plot = QPushButton("plot misc")
        width = button_plot.fontMetrics().boundingRect("plot misc").width() + 8
        button_plot.setMaximumWidth(width)
        misc_layout.addWidget(button_plot)
        button_table = QPushButton("view misc")
        width = button_plot.fontMetrics().boundingRect("view misc").width() + 8
        button_table.setMaximumWidth(width)
        misc_layout.addWidget(button_table)
        def misctable():
            last_tab = self.view.tab
            datavalue = eval(self.mdata.misc.datavalue)
            namevalue = self.mdata.misc.name_value
            mpointer = Pointer(datavalue, namevalue)
            self.view.tab = self.view.open_table(mpointer)
            if last_tab is not None and self.config["Tableview"]["tabbing"]:
                 self.tabifyDockWidget(last_tab, self.view.tab)
        button_table.clicked.connect(misctable)
        def plotmisc():
            try:
                datavalue = eval(self.mdata.misc.datavalue)
            except Exception as exc:
                mtext = ("something went wrong. The expression: " +
                      self.mdata.misc.datavalue + 
                      " could not be evaluated. Please check that it is correct." +
                      "The error reported is: " + str(exc))
                HelpWindow(self, mtext)
                return
            name = self.mdata.misc.name_value
            if datavalue.ndim >=3:
                temp = Fast3D(datavalue, parent=self, **self.config["Startingsize"]["3Dplot"],
                              mname=name, filename=self.name, dark=self.dark,
                              plotscheme=self.plotscheme)
            elif datavalue.ndim == 2:
                if self.only_indices:
                    temp = Fast2D(self, datavalue, parent=self,
                                  **self.config["Startingsize"]["2Dplot"],
                                  **self.config["Plotsettings"], mname=name,
                                  filename=self.name, dark=self.dark,
                                  plotscheme=self.plotscheme, only_indices=self.current_idx)
                else:
                    temp = Fast2D(self, datavalue,
                                  parent=self, **self.config["Startingsize"]["2Dplot"], **self.config["Plotsettings"],
                                  mname=name, filename=self.name, dark=self.dark,
                                  plotscheme=self.plotscheme)
            elif datavalue.ndim ==1:
                mdata = Data()
                mdata.x.set(arange(len(datavalue)), "index")
                mdata.y.set(datavalue, name)
                if self.holdon:
                    self.active1D.update_plot(mdata)
                else:
                    if self.only_indices:
                        temp = Fast1D(
                            self, mdata, **self.config["Startingsize"]["1Dplot"], mname=name,
                            filename=self.name, dark=self.dark, plotscheme=self.plotscheme,
                            only_indices=self.current_idx)
                    else:
                        temp = Fast1D(
                            self, mdata, **self.config["Startingsize"]["1Dplot"], mname=name,
                            filename=self.name, dark=self.dark, plotscheme=self.plotscheme)
                    self.active1D = temp
            else:
                return
            if not self.holdon:
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
            HelpWindow(self, "This seems to be an unknown file format")
        self.setWindowTitle(self.name)

    def get_data(self, signal):
        try:
            if isinstance(self.model.itemFromIndex(signal).mdata, Representative):
                mydata = np.squeeze(self.model.itemFromIndex(signal).mdata.get_value())
            else:
                mydata, unt = check_for_time(self.model.itemFromIndex(signal).mdata)
                mydata = np.squeeze(mydata)
                # mydata = np.squeeze(self.model.itemFromIndex(signal).mdata[:])
                # if "time" in self.model.itemFromIndex(signal).mdata.name.lower():
                #    #print("time is in name")
                #    try:
                #        unit = self.model.itemFromIndex(signal).mdata.units
                #        mydata = num2date(mydata, unit, only_use_cftime_datetimes=False)
                #    except:
                #        pass
            try:
                mydata_dims = self.model.itemFromIndex(signal).mdata.dimensions
            except:
                mydata_dims = None
            thisdata = self.model.itemFromIndex(signal).mdata
            if mydata.ndim > self.config["moreDdata"]["upper_absolute_limit"]:
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
                for dim in self.model.itemFromIndex(signal).mdata.dimensions:
                    temp = Pointer(self.model.itemFromIndex(signal).mdata.dimensions[dim].size, dim)
                    last_tab = self.view.tab
                    self.view.tab = self.view.open_table(temp)
                    if last_tab is not None and self.config["Tableview"]["tabbing"]:
                        self.tabifyDockWidget(last_tab, self.view.tab)
            except Exception as ex:
                HelpWindow(self, str(ex) + "cannot plot data or display information")
            return
        if mydata.ndim >= 3 and mydata.ndim <= self.config["moreDdata"]["limit_for_sliceplot"]:
            temp = Fast3D(
                mydata, parent=self, **self.config["Startingsize"]["3Dplot"],
                mname=thisdata.name, filename=self.name, dark=self.dark, plotscheme=self.plotscheme,
                mydata_dims=mydata_dims)
            self.openplots.append(temp)
        elif mydata.ndim == 2 and self.config["moreDdata"]["limit_for_sliceplot"] > 1:
            if self.only_indices:
                temp = Fast2D(self,
                              mydata, parent=self, **self.config["Startingsize"]["2Dplot"],
                              **self.config["Plotsettings"],
                              mname=thisdata.name, filename=self.name, dark=self.dark, plotscheme=self.plotscheme,
                              only_indices=self.current_idx, mydata_dims=mydata_dims)
            else:
                temp = Fast2D(self,
                              mydata, parent=self, **self.config["Startingsize"]["2Dplot"],
                              **self.config["Plotsettings"],
                              mname=thisdata.name, filename=self.name, dark=self.dark, plotscheme=self.plotscheme,
                              mydata_dims=mydata_dims)
            self.openplots.append(temp)
        elif mydata.ndim == 1:
            mdata = Data()
            try:
                dimhere = self.model.itemFromIndex(signal).mdata.dimensions[0]
                if dimhere == thisdata.name:
                    xdata = arange(len(mydata))
                    dimhere = "index"
                else:
                    try:
                        print("searching in: ", self.model.itemFromIndex(signal).mdata.group()[dimhere])
                        xdata, unt = check_for_time(self.model.itemFromIndex(signal).mdata.group()[dimhere])
                    except:
                        try:
                            xdata, unt = check_for_time(self.model.itemFromIndex(signal).mdata.group().parent[dimhere])
                        except:
                            try:
                                xdata, unt = check_for_time(
                                    self.model.itemFromIndex(signal).mdata.group().parent.parent[dimhere])
                            except:
                                try:
                                    xdata, unt = check_for_time(
                                        self.model.itemFromIndex(signal).mdata.group().parent.parent.parent[dimhere])
                                except:
                                    xdata = arange(len(mydata))
                                    unt = ""
                mdata.x.set(xdata, dimhere, units=unt)
            except Exception as exc:
                mdata.x.set(arange(len(mydata)), "index")
            mpath = ""
            test = thisdata
            while hasattr(test, "group"):
                try:
                    mpath = test.group().name + "/" + mpath
                except KeyError:
                    mpath = mpath
                test = test.group()
            try:
                mdata.y.set(mydata, mpath + thisdata.name, units=thisdata.units)
            except Exception as err:
                print("trying to get unit: ", err)
                mdata.y.set(mydata, mpath + thisdata.name)
            # TODO: The above maybe set via config file if I want the whole path or only the var
            if self.holdon:
                if isinstance(self.active1D, Fast2D):
                    HelpWindow(self, "hold is on, but no suitable plot open. Plotting in 2D plots only with x or y set")
                else:
                    if self.active1D is not None:
                        if isinstance(self.active1D.mydata.x.datavalue[0],
                                      datetime.datetime) and not isinstance(mdata.x.datavalue[0], datetime.datetime):
                            HelpWindow(self, "old axis has datetime x, new x data is not datetime. unselect hold")
                            return
                        elif not isinstance(self.active1D.mydata.x.datavalue[0],
                                            datetime.datetime) and isinstance(mdata.x.datavalue[0], datetime.datetime):
                            HelpWindow(self, "old axis has not datetime x, new x data is datetime. unselect hold")
                            return
                        elif isinstance(self.active1D.mydata.y.datavalue[0],
                                        datetime.datetime) and not isinstance(mdata.y.datavalue[0], datetime.datetime):
                            HelpWindow(self, "old axis has datetime y, new y data is not datetime. unselect hold")
                            return
                        elif not isinstance(self.active1D.mydata.y.datavalue[0],
                                            datetime.datetime) and isinstance(mdata.y.datavalue[0], datetime.datetime):
                            HelpWindow(self, "old axis has not datetime y, new y data is datetime. unselect hold")
                            return
                        else:
                            self.active1D.update_plot(mdata)
                    else:
                        HelpWindow(self, "hold is on, but no suitable plot open")
            else:
                if self.only_indices:
                    temp = Fast1D(self,
                                  mdata, **self.config["Startingsize"]["1Dplot"],
                                  mname=thisdata.name, filename=self.name,
                                  dark=self.dark, plotscheme=self.plotscheme, only_indices=self.current_idx,
                                  mydata_dims=mydata_dims)
                else:
                    temp = Fast1D(self,
                                  mdata, **self.config["Startingsize"]["1Dplot"],
                                  mname=thisdata.name, filename=self.name,
                                  dark=self.dark, plotscheme=self.plotscheme, mydata_dims=mydata_dims)
                self.active1D = temp
                self.openplots.append(temp)
        elif mydata.ndim > self.config["moreDdata"]["limit_for_sliceplot"]:
            # I need to find the variables that correspond to the dimension names
            if isinstance(self.model.itemFromIndex(signal).mdata, Representative):
                mydata = self.model.itemFromIndex(signal).mdata.get_value()
            else:
                mydata = self.model.itemFromIndex(signal).mdata[:]
            mydimdict = {}
            for midx, dimhere in enumerate(mydata_dims):
                if dimhere in mydimdict.keys():
                    dimhere = dimhere + str(midx)
                try:
                    mydimdict[dimhere], _ = check_for_time(self.model.itemFromIndex(signal).mdata.group()[dimhere])
                except:
                    try:
                        mydimdict[dimhere], _ = check_for_time(
                            self.model.itemFromIndex(signal).mdata.group().parent[dimhere])
                    except:
                        try:
                            mydimdict[dimhere], _ = check_for_time(
                                self.model.itemFromIndex(signal).mdata.group().parent.parent[dimhere])
                        except:
                            try:
                                mydimdict[dimhere], _ = check_for_time(
                                    self.model.itemFromIndex(signal).mdata.group().parent.parent.parent[dimhere])
                            except:
                                print("no variable found with dimension name ", dimhere)
                                mydimdict[dimhere] = None
            temp = Fast2D_select(self,
                                 mydata, parent=self, **self.config["Startingsize"]["nDplot"],
                                 **self.config["Plotsettings"],
                                 mname=thisdata.name, filename=self.name, dark=self.dark, plotscheme=self.plotscheme,
                                 mydata_dims=mydimdict)
            self.openplots.append(temp)
        else:
            HelpWindow(self, "nothing to plot, it seems to be a scalar")

    def walk_down_mfc(self, currentlevel, currentitemlevel, combine=""):
        if isinstance(currentitemlevel, str):
            currentitemlevel = Pointer(currentlevel, currentitemlevel, path=combine)
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
                    units = ""  # current_pointer.mdata.attributes
                try:
                    dtype = str(currentlevel[mkey].dtype)
                except (AttributeError, KeyError):
                    dtype = ""
                last = [self.walk_down_mfc(currentlevel[mkey], mkey, combine=combine+"/"+mkey), QStandardItem(ndim),
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
            dims = ", ".join([str(dim) for dim in currentlevel.dimensions])
            currentitemlevel.appendRow([
                self.walk_down_netcdf(currentlevel, self.name), QStandardItem(""), QStandardItem(""),
                QStandardItem(dims), QStandardItem(""), QStandardItem(""), QStandardItem(attrs)])
            return currentitemlevel
        try:
            totallist = list(currentlevel.groups.keys())
            totallist.sort()
        except KeyError:
            totallist = []
        try:
            totallist.extend(list(currentlevel.variables.keys()))
            totallist.sort()
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
            totallist.sort()
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
                    units = str(mkey.data.units) # current_pointer.mdata.attributes
                except (AttributeError, KeyError):
                    try:
                        units = mkey.data.attributes["units"]
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
    with open(CONFIGPATH) as fid:
        config = yaml.load(fid, yaml.Loader)
    new_font = my_graphics.font()
    new_font.setPointSize(config["Startingsize"]["Fontsize"])
    my_graphics.setFont(new_font)
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
                if len(path) > 0:
                    try:
                        mdata, unit = check_for_time(self.windows[idx].mfile[path])
                        # mdata = self.windows[idx].mfile[path][:]
                        thisname = path
                    except TypeError as te:
                        HelpWindow(self, "setting same variables for x, y, z, ... is currently not supported for hdf4")
                        return
                    except KeyError as ke:
                        HelpWindow(self,
                                   "probably it was tried to set a variable as x,y,z, xerror or yerror that does not exist. The error message is: " + str(
                                       ke))
                        return
                    except IndexError:
                        try:
                            thisname, col = path.split(",col=")
                            col = int(col)
                            mdata, unit = check_for_time(self.windows[idx].mfile[thisname])
                            mdata = mdata[:, int(col)]
                            # mdata = self.windows[idx].mfile[thisname][:, int(col)]
                        except (ValueError, IndexError):
                            try:
                                thisname, row = path.split(",row=")
                                row = int(row)
                                mdata, unit = check_for_time(self.windows[idx].mfile[thisname])
                                mdata = mdata[thisname][int(row), :]
                                # mdata = self.windows[idx].mfile[thisname][int(row), :]
                            except (IndexError, ValueError) as err:
                                print(err)
                                if "slice" in path:
                                    thisname, rest = path.split(" slice ")
                                    mslice, rest = rest.split(" in dim ")
                                    mdata = self.windows[idx].mfile[thisname]
                                    try:
                                        dim, row = rest.split(",row=")
                                        row = int(row)
                                        if dim == "0":
                                            mdata = mdata[mslice, row, :]
                                        elif dim == "1":
                                            mdata = mdata[row, mslice, :]
                                        elif dim == "2":
                                            mdata = mdata[row, :, mslice]
                                        else:
                                            HelpWindow(self,
                                                       "currently, set same data only supports base data up to 3 dimensions")
                                            print("not supported right now")
                                            return
                                    except ValueError:
                                        dim, col = rest.split(",col=")
                                        col = int(col)
                                        if dim == "0":
                                            mdata = mdata[mslice, :, col]
                                        elif dim == "1":
                                            mdata = mdata[:, mslice, col]
                                        elif dim == "2":
                                            mdata = mdata[:, col, mslice]
                                        else:
                                            HelpWindow(self,
                                                       "currently, set same data only supports base data up to 3 dimensions")
                                            print("not supported right now")
                                            return
                    self.windows[idx].mdata.__dict__[which.split("(")[0]].set(mdata, name, thisname)


class ScrollLabel(QScrollArea):
    def __init__(self, *args, **kwargs):
        QScrollArea.__init__(self, *args, **kwargs)
        self.setWidgetResizable(True)
        content = QWidget(self)
        self.setWidget(content)
        lay = QVBoxLayout(content)
        self.label = QLabel(content)
        self.label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
        self.label.setWordWrap(True)
        lay.addWidget(self.label)

    def setText(self, text):
        # setting text to the label
        self.label.setText(text)


if __name__ == '__main__':
    mfile = sys.argv[1:]
    if len(mfile) > 0:
        main(mfile)
    else:
        main()
