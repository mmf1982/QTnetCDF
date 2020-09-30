import sys
import os
import numpy
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import (QApplication, QLabel, QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QMessageBox,
                             QMainWindow, qApp, QSlider, QStatusBar, QLineEdit)
try:
    from . import add_interactivity as ai
except (ModuleNotFoundError, ImportError):
    try:
        from add_interactivity import add_interactivity as ai
    except (ModuleNotFoundError, ImportError):
        print("add_interactivity is not loaded. This reduces the interactivity"
              "for 1D plots. Check if add_interactivity.py is in the current python path")
try:
    from .Colorschemes import QDarkPalette
except:
    from Colorschemes import QDarkPalette
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib.colors import LogNorm, Normalize
from matplotlib.backend_bases import key_press_handler
import matplotlib.projections as proj
import matplotlib.axes._subplots as axs
try:
    from .Menues import center, HelpWindow
except (ImportError, ModuleNotFoundError):
    from Menues import center, HelpWindow

class Easyerrorbar(axs.Axes):
    """ Circumvent problem with normal matplotlib errorbar():

    error-bars not accessible, label assigned to error-bars. When getting lines on the axis, the error-bars
    are not accessible. To make things worse, the label, set on error-bar creation, is not assigned to the
    line object of the plot, but to the not accessible error-bars. This projection overwrites the normal
    error-bar and plots a single line, converting each point into 7 points, walking up-down the y error and then
    left-right the x-error before going to the next point."""
    name = 'easyerrorbar'

    def errorbar(self, x, y, yerr=None, xerr=None, **kwargs):
        if not ((xerr is None) and (yerr is None)):
            if xerr is None:
                xerr = numpy.zeros(len(x))
            if yerr is None:
                yerr = numpy.zeros(len(x))
            # not entirely sure why, but if I do not save this as new variables, sometimes (if only x and xerr or only
            # y and yerr are selected, but also not always, the main window crashes. Seems to be some memory issue
            x2 = numpy.array([[xc, xc, xc, xc, xc + eb, xc - eb, xc] for xc, eb in zip(x, xerr)]).flatten()
            y2 = numpy.array([[yc, yc + eb, yc - eb, yc, yc, yc, yc] for yc, eb in zip(y, yerr)]).flatten()
        else:
            x2 = numpy.copy(x)
            y2 = numpy.copy(y)
        super().plot(x2, y2,  **kwargs)


class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=4, height=4, dpi=150, plotscheme=["default"], **kwargs):
        try:
            plt.style.use(plotscheme)
        except:
            try:
                here = os.path.dirname(os.path.abspath(__file__))
                plotschemenew = plotscheme[:-1]
                plotschemenew.append(os.path.join(here, plotscheme[0]))
                plt.style.use(plotschemenew)
            except:
                pass
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        proj.register_projection(Easyerrorbar)  # this is needed for 1D errorbars.
        self.axes = self.fig.add_subplot(111, projection='easyerrorbar')
        super(MplCanvas, self).__init__(self.fig)
        self.toolbar = NavigationToolbar(self, parent)
        self.im = None
        self.cb = None
        self.mpl_connect('key_press_event', self.on_key_press)
        self.setFocusPolicy(Qt.StrongFocus)
        self.mparent = parent

    def on_key_press(self, event):
        try:
            key_press_handler(event, self, self.toolbar)
        except TypeError:
            pass

    def image(self, mdata, limits=None):
        """
        Plot the current 2D data as an image. Use either default limits or provided limits
        :param mdata: 2D array to display
        :param limits: dictionary with keys xlim, ylim, clim and cmap
        :return:
        """
        self.axes.cla()
        try:
            self.cb.remove()
        except AttributeError:
            pass
        try:
            self.im = self.axes.imshow(mdata)
        except TypeError:
            HelpWindow(self, "Likely you tried to make an image of text data. \n"
                       "Maybe this is a table and not a matrix? Check with 's'.")
            return
        if limits is not None:
            self.im.axes.set_xlim(limits["xlim"])
            self.im.axes.set_ylim(limits["ylim"])
            self.im.set_clim(limits["clim"])
            self.im.set_cmap(limits["cmap"])
        self.cb = self.fig.colorbar(self.im, ax=self.axes)
        return

    def pcolormesh(self, x, y, z):
        try:
            self.cb.remove()
        except AttributeError:
            pass
        try:
            if z.datavalue.ndim == 1:
                self.im = self.axes.scatter(x.datavalue, y.datavalue, c=z.datavalue)
            else:
                self.im = self.axes.pcolormesh(x.datavalue, y.datavalue, z.datavalue)
        except Exception as exc1:
            try:
                self.im = self.axes.pcolormesh(x.datavalue, y.datavalue, z.datavalue.T)
                HelpWindow(self, "careful: z data is transposed to fit x and y")
            except Exception as exc2:
                HelpWindow(self.mparent, "one of the following errors occured:"+ str(exc1) + str(exc2))
                return False
        self.cb = self.fig.colorbar(self.im, ax=self.axes)
        self.axes.set_xlabel(x.name_value)
        self.axes.set_ylabel(y.name_value)
        self.axes.set_title(z.name_value)
        return True

    @property
    def get_axis_values(self):
        """
        return the current values for x, y and color axis, as well as colour map
        :return: mdict, dictionary with keys clim, xlim, ylim and cmap
        """
        mdict = {
            "clim": self.im.get_clim(),
            "xlim": self.im.axes.get_xlim(),
            "ylim": self.im.axes.get_ylim(),
            "cmap": self.im.get_cmap()}
        return mdict


class DataChooser(QWidget):
    def __init__(self, parent, is3d=True, is4d=False, **kwargs):
        super().__init__(**kwargs)
        layout4 = QHBoxLayout()
        layout5 = QVBoxLayout()
        self.is3d = is3d
        self.is4d = is4d
        slicings = QWidget()
        layout2 = QVBoxLayout()
        if is3d:
            self.slice_label = QLabel("slice = 0" + "/ 0-" + str(parent.shape[0] - 1))
            self.active_index = 0
            self.active_dimension = 0
            self.frozen = False
            self.entry = QLineEdit()
            self.entry.editingFinished.connect(self.on_click)
            self.entry.setFixedWidth(self.entry.fontMetrics().boundingRect("1000000").width())
            layout = QHBoxLayout()
            plus = QPushButton('+')
            minus = QPushButton('-')
            plus.clicked.connect(self.on_plus)
            minus.clicked.connect(self.on_minus)
            layout.addWidget(minus)
            layout.addWidget(plus)
            layout.addWidget(self.entry, alignment=Qt.AlignVCenter)
            buttons = QWidget()
            buttons.setLayout(layout)
            layout2.addWidget(buttons, alignment=Qt.AlignVCenter)
            layout2.addWidget(self.slice_label, alignment=Qt.AlignHCenter)
        if is4d:
            layoutb = QHBoxLayout()
            self.entry2 = QLineEdit()
            self.entry2.editingFinished.connect(self.on_click2)
            self.entry2.setFixedWidth(self.entry2.fontMetrics().boundingRect("1000000").width())
            self.slice_label2 = QLabel("slice = 0" + "/ 0-" + str(parent.shape[1] - 1))
            self.active_index2 = 0
            self.active_dimension2 = 1
            plus2 = QPushButton('+')
            minus2 = QPushButton('-')
            plus2.clicked.connect(self.on_plus2)
            minus2.clicked.connect(self.on_minus2)
            layoutb.addWidget(minus2)
            layoutb.addWidget(plus2)
            layoutb.addWidget(self.entry2, alignment=Qt.AlignVCenter)
            buttons2 = QWidget()
            buttons2.setLayout(layoutb)
            layout2.addWidget(buttons2, alignment=Qt.AlignVCenter)
            layout2.addWidget(self.slice_label2, alignment=Qt.AlignHCenter)
        if is3d:
            slicings.setLayout(layout2)
            layout3 = QVBoxLayout()
            slider = QSlider(Qt.Horizontal)
            self.dim_label = QLabel("dim = 0")
        if is4d:
            slider.setRange(0, len(parent.shape) - 2)
        if is3d:
            slider.setRange(0, len(parent.shape) - 1)
            slider.valueChanged.connect(self.update_dim_label)
            dimensions = QWidget()
            layout3.addWidget(slider, alignment=Qt.AlignVCenter)
            layout3.addWidget(self.dim_label, alignment=Qt.AlignHCenter)
        if is4d:
            slider2 = QSlider(Qt.Horizontal)
            self.dim_label2 = QLabel("dim = 1")
            slider2.setRange(1,len(parent.shape)-1)
            slider2.valueChanged.connect(self.update_dim_label2)
            layout3.addWidget(slider2, alignment=Qt.AlignVCenter)
            layout3.addWidget(self.dim_label2, alignment=Qt.AlignHCenter)
        if is3d:
            dimensions.setLayout(layout3)
            self.freeze_button = QPushButton('keep settings')
            self.freeze_button.clicked.connect(self.on_freeze)
            layout5.addWidget(self.freeze_button)
            layout4.addWidget(slicings)
            layout4.addWidget(dimensions)
        buttons2 = QWidget()
        self.is_log = False
        self.log_button = QPushButton("plot log")
        self.log_button.clicked.connect(self.on_log)
        layout5.addWidget(self.log_button)
        buttons2.setLayout(layout5)
        layout4.addWidget(buttons2)
        self.setLayout(layout4)
        self.mparent = parent

    def on_click(self):
        try:
            idx = int(self.entry.text())
            if self.mparent.shape[self.active_dimension] <= idx:
                print(self.mparent.shape)
                print(self.active_dimension)
                print(idx)
                print("end")
                HelpWindow(self, "the index you chose is too large for this dimension")
                return
            self.active_index = idx
            self.update_slice()
        except ValueError:
            HelpWindow(self, "You need to type an integer")

    def on_click2(self):
        try:
            idx = int(self.entry2.text())
            if self.mparent.shape[self.active_dimension2] <= idx:
                HelpWindow(self, "the index you chose is too large for this dimension")
                return
            self.active_index2 = idx
            self.update_slice()
        except ValueError:
            HelpWindow(self, "You need to type an integer")


    def on_log(self):
        if self.is_log:
            self.is_log = False
            self.log_button.setText("put log")
        else:
            self.is_log = True
            self.log_button.setText("put lin")
        if self.is3d:
            if self.is4d:
                worked = self.mparent.update_plot(self.active_index, self.active_dimension, self.frozen, self.is_log,
                                                  idx2=self.active_index2, dim2=self.active_dimension2)
                if not worked:
                    self.is_log = False
                    self.log_button.setText("put log")
                    worked = self.mparent.update_plot(self.active_index, self.active_dimension, self.frozen,
                                                      self.is_log,
                                                      idx2=self.active_index2, dim2=self.active_dimension2)
            else:
                worked = self.mparent.update_plot(self.active_index, self.active_dimension, self.frozen, self.is_log)
                if not worked:
                    self.is_log = False
                    self.log_button.setText("put log")
                    worked = self.mparent.update_plot(self.active_index, self.active_dimension, self.frozen, self.is_log)
        else:
            worked = self.mparent.update_plot(self.is_log)
            if not worked:
                self.is_log = False
                self.log_button.setText("put log")
                worked = self.mparent.update_plot(self.is_log)
        return

    def on_freeze(self):
        if self.is3d:
            if self.frozen:
                self.frozen = False
                self.freeze_button.setText("keep settings")
            else:
                self.frozen = True
                self.freeze_button.setText("      release      ")
            if self.is4d:
                worked = self.mparent.update_plot(self.active_index, self.active_dimension, self.frozen, self.is_log,
                                                  idx2=self.active_index2, dim2=self.active_dimension2)
                if not worked:
                    self.is_log = False
                    self.log_button.setText("put log")
                    worked = self.mparent.update_plot(self.active_index, self.active_dimension, self.frozen, self.is_log,
                                                  idx2=self.active_index2, dim2=self.active_dimension2)
            else:
                worked = self.mparent.update_plot(self.active_index, self.active_dimension, self.frozen, self.is_log)
                if not worked:
                    self.is_log = False
                    self.log_button.setText("put log")
                    worked = self.mparent.update_plot(self.active_index, self.active_dimension, self.frozen, self.is_log)

    def update_dim_label(self, value):
        if self.is3d:
            self.active_dimension = value
            self.update_slice()
            self.dim_label.setText("dim = " + str(value))
            self.slice_label.setText("slice = "+(str(self.active_index)) + "/ 0-" + str(self.mparent.shape[value] - 1))

    def update_dim_label2(self, value):
            self.active_dimension2 = value
            self.update_slice()
            self.dim_label2.setText("dim = " + str(value))
            self.slice_label2.setText("slice = "+(str(self.active_index2)) + "/ 0-" + str(self.mparent.shape[value] - 1))

    def on_minus(self):
        if self.is3d:
            mymax = self.mparent.shape[self.active_dimension]
            if self.active_index > -mymax:
                self.active_index -= 1
            else:
                self.active_index = -1
            self.update_slice()

    def on_minus2(self):
        mymax = self.mparent.shape[self.active_dimension2]
        if self.active_index2 > -mymax:
            self.active_index2 -= 1
        else:
            self.active_index2 = -1
        self.update_slice()

    def on_plus(self):
        if self.is3d:
            mymax = self.mparent.shape[self.active_dimension]
            if self.active_index < mymax - 1:
                self.active_index += 1
            else:
                self.active_index = 0
            self.update_slice()

    def on_plus2(self):
        if self.is4d:
            mymax = self.mparent.shape[self.active_dimension2]
            if self.active_index2 < mymax - 1:
                self.active_index2 += 1
            else:
                self.active_index2 = 0
            self.update_slice()

    def update_slice(self):
        if self.is3d:
            if not self.is4d:
                worked = self.mparent.update_plot(self.active_index, self.active_dimension, self.frozen, self.is_log)
                if not worked:
                    self.is_log = False
                    self.log_button.setText("put log")
                    worked = self.mparent.update_plot(self.active_index, self.active_dimension, self.frozen, self.is_log)
                self.slice_label.setText("slice = " + str(self.active_index) + "/ 0-" + str(self.mparent.shape[self.active_dimension]-1))
            else:
                worked = self.mparent.update_plot(self.active_index, self.active_dimension,
                                                      self.frozen, self.is_log, idx2=self.active_index2,
                                                      dim2=self.active_dimension2)
                if not worked:
                    self.is_log = False
                    self.log_button.setText("put log")
                    worked = self.mparent.update_plot(self.active_index, self.active_dimension,
                                                      self.frozen, self.is_log, idx2=self.active_index2,
                                                      dim2=self.active_dimension2)
                self.slice_label.setText("slice = " + str(self.active_index) + "/ 0-" + str(self.mparent.shape[self.active_dimension]-1))
                self.slice_label2.setText("slice = " + str(self.active_index2) + "/ 0-" + str(self.mparent.shape[self.active_dimension2]-1))

class Fast2D(QMainWindow):
    def __init__(self, mydata,  parent=None, mname=None, filename=None, dark=False, **kwargs):
        super(Fast2D, self).__init__(parent)
        self.isimage = True
        if (mydata.__class__.__name__) == ("Data"):
            self.isimage = False
            self.x = mydata.x
            self.y = mydata.y
            mydata = mydata.z
        if mname is None:
            mname = '2D Viewer'
        self.mydata = mydata
        try:
            self.shape = mydata.shape
        except AttributeError:
            self.shape = mydata.datavalue.shape
        self.setWindowTitle(mname)
        # self.setWindowIcon(QIcon("web.png"))
        self.myfigure = MplCanvas(parent=self, **kwargs)
        my_slider = DataChooser(self, is3d=False)
        mainwindow = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.myfigure.toolbar)
        layout.addWidget(self.myfigure, stretch=1)
        layout.addWidget(my_slider)
        mainwindow.setLayout(layout)
        if self.isimage:
            self.myfigure.image(mydata)
        else:
            worked = self.myfigure.pcolormesh(self.x, self.y, mydata)
            if not worked:
                self.show()
                return
        self.setCentralWidget(mainwindow)
        center(self)
        if filename is not None:
            statusbar = QStatusBar()
            statusbar.showMessage(filename)
            self.setStatusBar(statusbar)
        if dark:
            palette = QDarkPalette()
            self.setPalette(palette)
        self.show()

    def update_plot(self, is_log=False):
        if is_log:
            if min(*self.myfigure.im.get_clim()) <= 0:
                help = HelpWindow(self, "it seems there are 0 or negative values.\n "
                                    "Before putting log, adjust limits \nand "
                                    "keep the values. Change back to lin for now.")
                return False
            self.myfigure.im.set_norm(LogNorm(*self.myfigure.im.get_clim()))
        else:
            self.myfigure.im.set_norm(Normalize(*self.myfigure.im.get_clim()))
        try:
            self.myfigure.draw()
        except (ValueError, ZeroDivisionError):
            help = HelpWindow(self, "it seems there are 0 or negative values.\n "
                                    "Before putting log, adjust limits \nand "
                                    "keep the values. Change back to lin for now.")
            return False
        return True


class Fast1D(QMainWindow):
    def __init__(self, mydata, symbol=False, mname=None, filename=None, dark=False, **kwargs):
        super().__init__()
        if mname is None:
            mname = '1D Viewer'
        self.setWindowTitle(mname)
        self.setWindowIcon(QIcon("web.png"))
        self.myfigure = MplCanvas(self, **kwargs)
        mainwindow = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.myfigure.toolbar)
        layout.addWidget(self.myfigure, stretch=1)
        mainwindow.setLayout(layout)
        self.setCentralWidget(mainwindow)
        try:
            self.update_plot(mydata, symbol)
        except ValueError as valerr:
            help = HelpWindow(self, "Probably you chose to plot x-y with different dimensions? Errormessage:"+
                              str(valerr))
        self.myfigure.axes.set_xlabel(mydata.x.text().split(":")[1])
        center(self)
        if filename is not None:
            statusbar = QStatusBar()
            statusbar.showMessage(filename)
            self.setStatusBar(statusbar)
        if dark:
            palette = QDarkPalette()
            self.setPalette(palette)
        self.show()

    def update_plot(self, mydata, symbol=False):
        if mydata.y.datavalue.ndim > 1:
            alllabel = mydata.y.text().split(":")[1].split("s.")[-1].split(" - ")
            labs = numpy.arange(int(alllabel[0]), int(alllabel[1])+1)
            if mydata.x.datavalue.ndim > 1:
                if not mydata.x.datavalue.shape == mydata.y.datavalue.shape:
                    raise ValueError("x and y have different shapes, make sure you choose either same number of rows/cols"
                                     " or either for x or y only 1 column/ row and that the length of the x and y data is equal.")
                    return
                alllabel2 = mydata.x.text().split(":")[1].split("s.")[-1].split(" - ")
                labcols = numpy.arange(int(alllabel2[0]), int(alllabel2[1])+1)
                for row, col, lab, labcol in zip(mydata.y.datavalue, mydata.x.datavalue, labs, labcols):
                    label = (mydata.x.text().split(":")[1].split("s.")[0] + str(labcol) +
                             " vs " + mydata.y.text().split(":")[1].split("s.")[0] +
                             " " + str(lab))
                    if symbol:
                        self.myfigure.axes.plot(col, row, marker=symbol, lw=0, label=label)
                    else:
                        self.myfigure.axes.plot(col, row, label=label)
            else:
                for row, lab in zip(mydata.y.datavalue, labs):
                    label = (mydata.x.text().split(":")[1] + " vs " + mydata.y.text().split(":")[1].split("s.")[0] +
                             " " + str(lab))
                    if symbol:
                        self.myfigure.axes.plot(mydata.x.datavalue, row, marker=symbol, lw=0, label=label)
                    else:
                        self.myfigure.axes.plot(mydata.x.datavalue, row, label=label)
        elif mydata.x.datavalue.ndim > 1:
            alllabel = mydata.x.text().split(":")[1].split("s.")[-1].split(" - ")
            labs = numpy.arange(int(alllabel[0]), int(alllabel[1])+1)
            for row, lab in zip(mydata.x.datavalue, labs):
                label = (mydata.x.text().split(":")[1].split("s.")[0] + " " + str(lab) + " vs " +
                         mydata.y.text().split(":")[1])
                if symbol:
                    self.myfigure.axes.plot(row, mydata.y.datavalue, marker=symbol, lw=0, label=label)
                else:
                    self.myfigure.axes.plot(row, mydata.y.datavalue, label=label)
        else:
            label = mydata.x.text().split(":")[1] + " vs " + mydata.y.text().split(":")[1]
            if symbol:
                self.myfigure.axes.plot(mydata.x.datavalue, mydata.y.datavalue,marker=symbol, lw=0, label=label)
            else:
                self.myfigure.axes.errorbar(mydata.x.datavalue, mydata.y.datavalue, yerr=mydata.yerr.datavalue,
                                        xerr=mydata.xerr.datavalue, label=label)
        try:
            ai.add_interactivity(fig=self.myfigure.fig, ax=self.myfigure.axes, nodrag=False, legsize=7)
        except:
            print("it seems that add_interactivity is not loaded. Check if the file is in pythonpath")
        self.myfigure.draw()


class Fast3D(QMainWindow):
    def __init__(self, mydata, parent=None, mname=None, filename=None, dark=False, **kwargs):
        print("here")
        if mydata.ndim == 4:
            self.is4d = True
            print("is 4D")
        else:
            self.is4d = False
        super(Fast3D, self).__init__(parent)
        if mname is None:
            mname = '3D Viewer'
        self.setWindowTitle(mname)
        # self.setWindowIcon(QIcon("web.png"))
        if mydata.ndim <= 4:
            self.mydata = mydata
            try:
                self.shape = mydata.shape
            except Exception as exc:
                print(exc)
            self.myfigure = MplCanvas(parent=self, **kwargs)
            self.my_slider = DataChooser(self, is4d=self.is4d)
            if self.is4d:
                self.update_plot(0, 0, idx2=0, dim2=1)
            else:
                self.update_plot(0, 0)
            self.mainwindow = QWidget()
            self.layout = QVBoxLayout()
            self.layout.addWidget(self.myfigure.toolbar)
            self.layout.addWidget(self.myfigure, stretch=1)
            self.layout.addWidget(self.my_slider)
            self.mainwindow.setLayout(self.layout)
            self.setCentralWidget(self.mainwindow)
            center(self)
            if filename is not None:
                self.statusbar = QStatusBar()
                self.statusbar.showMessage(filename)
                self.setStatusBar(self.statusbar)
            self.show()
        elif mydata.ndim > 4:
            messagebox = QMessageBox()
            messagebox.addButton(QMessageBox.Yes)
            reply = messagebox.exec_()
            if __name__ == "__main__" and reply == QMessageBox.Yes:
                sys.exit()
            elif reply == QMessageBox.Yes:
                qApp.quit()
        if dark:
            self.palette = QDarkPalette()
            self.setPalette(self.palette)

    def update_plot(self, index, dimension, hold_it=False, is_log=False, idx2=None, dim2=None):
        """
        :param index: integer
        :param dimension:
        :param hold_it: logical
        :param is_log: logical
        """
        try:
            if dimension == 0:
                newdata = self.mydata[index]
            elif dimension == 1:
                newdata = self.mydata[:, index, :]
            elif dimension == 2:
                newdata = self.mydata[:, :, index]
            else:
                raise ValueError("dimensionality is too high")
        except (IndexError):
            HelpWindow(self, "It seems you chose an index that does not exist. Maybe you changed slicing at high index")
            return False
        if dim2 is not None:
            if dim2 <= dimension:
                print(dim2, dimension)
                HelpWindow(self, "you have to choose the second dimension larger than the first.")
                return False
            try:
                print("current choice: dim1", dimension, " slice idx ", index)
                print("              : dim2", dim2, " slice idx2 ", idx2)
                if dim2 == 1:
                    newdata = newdata[idx2]
                elif dim2 == 2:
                    newdata = newdata[:, idx2, :]
                elif dim2 == 3:
                    newdata = newdata[:, :, idx2]
                else:
                    raise ValueError("dimensionality is too high")
            except (IndexError):
                HelpWindow(self,
                           "It seems you chose an index that does not exist. Maybe you changed slicing at high index")
                return False

        if hold_it:
            self.myfigure.image(newdata, self.myfigure.get_axis_values)
            if is_log:
                self.myfigure.im.set_norm(LogNorm(*self.myfigure.im.get_clim()))
        else:
            if is_log:
                old_lims = self.myfigure.im.get_clim()
                if (self.myfigure.im.get_array() == newdata).all():
                    if min(*old_lims) <= 0:
                        help = HelpWindow(self, "it seems there are 0 or negative values.\n "
                                    "Before putting log, adjust limits \nand "
                                    "keep the values. Change back to lin for now.")
                        return False
                    self.myfigure.im.set_norm(LogNorm(*old_lims))
                else:
                    self.myfigure.image(newdata)
                    if min(*self.myfigure.im.get_clim()) <= 0:
                        help = HelpWindow(self, "it seems there are 0 or negative values.\n "
                                    "Before putting log, adjust limits \nand "
                                    "keep the values. Change back to lin for now.")
                        return False
                    self.myfigure.im.set_norm(LogNorm(*self.myfigure.im.get_clim()))
            else:
                self.myfigure.image(newdata)
        try:
            self.myfigure.draw()
        except (ValueError, ZeroDivisionError):
            HelpWindow(self, "it seems there are 0 or negative values.\n "
                                    "Before putting log, adjust limits \nand "
                                    "keep the values. Change back to lin for now.")
            return False
        except RuntimeError:
            HelpWindow(self, "sorry, something bad happened")
        return True


def main():
    app = QApplication([])
    mdata = numpy.random.random((10, 10, 10))
    mdata[0, :, :] = 0
    mdata[-1, :, :] = 10
    mdata[:, 0, :] = 5
    mdata[:, :, 3] = 3
    Fast3D(mdata)
    if __name__ == "__main__":
        sys.exit(app.exec_())


if __name__ == "__main__":
    main()
