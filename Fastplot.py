import sys
import numpy
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (QApplication, QLabel, QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QMessageBox,
                             QDesktopWidget, QMainWindow, qApp, QSlider)
try:
    from . import add_interactivity as ai
except (ModuleNotFoundError, ImportError):
    try:
        from add_interactivity import add_interactivity as ai
    except (ModuleNotFoundError, ImportError):
        print("add_interactivity is not loaded. This reduces the interactivity"
              "for 1D plots. Check if add_interactivity.py is in the current python path")
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
    def __init__(self, parent=None, width=4, height=4, dpi=150):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        proj.register_projection(Easyerrorbar)  # this is needed for 1D errorbars.
        self.axes = self.fig.add_subplot(111, projection='easyerrorbar')
        super(MplCanvas, self).__init__(self.fig)
        self.toolbar = NavigationToolbar(self, parent)
        self.im = None
        self.cb = None
        self.mpl_connect('key_press_event', self.on_key_press)
        self.setFocusPolicy(Qt.StrongFocus)
        self.parent = parent

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

        self.im = self.axes.imshow(mdata, cmap="jet")
        if limits is not None:
            self.im.axes.set_xlim(limits["xlim"])
            self.im.axes.set_ylim(limits["ylim"])
            self.im.set_clim(limits["clim"])
            self.im.set_cmap(limits["cmap"])
        self.cb = self.fig.colorbar(self.im, ax=self.axes)
        return

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
    def __init__(self, parent, is3d=True, **kwargs):
        super().__init__(**kwargs)
        layout4 = QHBoxLayout()
        layout5 = QVBoxLayout()
        self.is3d = is3d
        if is3d:
            self.active_index = 0
            self.active_dimension = 0
            self.frozen = False
            layout = QHBoxLayout()
            plus = QPushButton('+')
            minus = QPushButton('-')
            plus.clicked.connect(self.on_plus)
            minus.clicked.connect(self.on_minus)
            self.slice_label = QLabel("slice = 0"+ "/ 0-" + str(parent.shape[0]-1))
            layout.addWidget(minus)
            layout.addWidget(plus)
            buttons = QWidget()
            buttons.setLayout(layout)
            slicings = QWidget()
            layout2 = QVBoxLayout()
            layout2.addWidget(buttons, alignment=Qt.AlignVCenter)
            layout2.addWidget(self.slice_label, alignment=Qt.AlignHCenter)
            slicings.setLayout(layout2)
            layout3 = QVBoxLayout()
            slider = QSlider(Qt.Horizontal)
            self.dim_label = QLabel("dim = 0")
            slider.setRange(0, len(parent.shape) - 1)
            slider.valueChanged.connect(self.update_dim_label)
            dimensions = QWidget()
            layout3.addWidget(slider, alignment=Qt.AlignVCenter)
            layout3.addWidget(self.dim_label, alignment=Qt.AlignHCenter)
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
        self.parent = parent

    def on_log(self):
        if self.is_log:
            self.is_log = False
            self.log_button.setText("put log")
        else:
            self.is_log = True
            self.log_button.setText("put lin")
        if self.is3d:
            worked = self.parent.update_plot(self.active_index, self.active_dimension, self.frozen, self.is_log)
            if not worked:
                self.is_log = False
                self.log_button.setText("put log")
                worked = self.parent.update_plot(self.active_index, self.active_dimension, self.frozen, self.is_log)
        else:
            worked = self.parent.update_plot(self.is_log)
            if not worked:
                self.is_log = False
                self.log_button.setText("put log")
                worked = self.parent.update_plot(self.is_log)

    def on_freeze(self):
        if self.frozen:
            self.frozen = False
            self.freeze_button.setText("keep settings")
        else:
            self.frozen = True
            self.freeze_button.setText("      release      ")
        worked = self.parent.update_plot(self.active_index, self.active_dimension, self.frozen, self.is_log)
        if not worked:
            self.is_log = False
            self.log_button.setText("put log")
            worked = self.parent.update_plot(self.active_index, self.active_dimension, self.frozen, self.is_log)

    def update_dim_label(self, value):
        self.active_dimension = value
        self.update_slice()
        self.dim_label.setText("dim = " + str(value))
        self.slice_label.setText("slice = "+(str(self.active_index)) + "/ 0-" + str(self.parent.shape[value] - 1))

    def on_minus(self):
        mymax = self.parent.shape[self.active_dimension]
        if self.active_index > -mymax:
            self.active_index -= 1
        else:
            self.active_index = -1
        self.update_slice()

    def on_plus(self):
        mymax = self.parent.shape[self.active_dimension]
        if self.active_index < mymax - 1:
            self.active_index += 1
        else:
            self.active_index = 0
        self.update_slice()

    def update_slice(self):
        worked = self.parent.update_plot(self.active_index, self.active_dimension, self.frozen, self.is_log)
        if not worked:
            self.is_log = False
            self.log_button.setText("put log")
            worked = self.parent.update_plot(self.active_index, self.active_dimension, self.frozen, self.is_log)
        self.slice_label.setText("slice = " + str(self.active_index) + "/ 0-" + str(self.parent.shape[self.active_dimension]-1))


class Fast2D(QMainWindow):
    def __init__(self, mydata, mname=None, **kwargs):
        super().__init__()
        if mname is None:
            mname = '2D Viewer'
        self.setWindowTitle(mname)
        self.setWindowIcon(QIcon("web.png"))
        self.myfigure = MplCanvas(self, **kwargs)
        my_slider = DataChooser(self, False)
        mainwindow = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.myfigure.toolbar)
        layout.addWidget(self.myfigure, stretch=1)
        layout.addWidget(my_slider)
        mainwindow.setLayout(layout)
        self.myfigure.image(mydata)
        self.setCentralWidget(mainwindow)
        center(self)
        self.show()

    def update_plot(self, is_log=False):
        if is_log:
            self.myfigure.im.set_norm(LogNorm(*self.myfigure.im.get_clim()))
        else:
            self.myfigure.im.set_norm(Normalize(*self.myfigure.im.get_clim()))
        try:
            self.myfigure.draw()
        except ValueError:
            help = HelpWindow(self, "it seems there are 0 or negative values.\n "
                                    "Before putting log, adjust limits \nand "
                                    "keep the values. Change back to lin for now.")
            return False
        return True


class Fast1D(QMainWindow):
    def __init__(self, mydata, mname=None, **kwargs):
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
            self.update_plot(mydata)
        except ValueError as valerr:
            help = HelpWindow(self, "Probably you chose to plot x-y with different dimensions? Errormessage:"+
                              str(valerr))
        self.myfigure.axes.set_xlabel(mydata.x.text().split(":")[1])
        center(self)
        self.show()

    def update_plot(self, mydata):
        if mydata.y.datavalue.ndim > 1:
            alllabel = mydata.y.text().split(":")[1].split("s.")[-1].split(" - ")
            labs = numpy.arange(int(alllabel[0]), int(alllabel[1])+1)
            for row, lab in zip(mydata.y.datavalue, labs):
                label = (mydata.x.text().split(":")[1] + " vs " + mydata.y.text().split(":")[1].split("s.")[0] +
                         " " + str(lab))
                self.myfigure.axes.plot(mydata.x.datavalue, row, label=label)
        elif mydata.x.datavalue.ndim > 1:
            alllabel = mydata.x.text().split(":")[1].split("s.")[-1].split(" - ")
            labs = numpy.arange(int(alllabel[0]), int(alllabel[1])+1)
            for row, lab in zip(mydata.x.datavalue, labs):
                label = (mydata.x.text().split(":")[1].split("s.")[0] + " " + str(lab) + " vs " +
                         mydata.y.text().split(":")[1])
                self.myfigure.axes.plot(row, mydata.y.datavalue, label=label)
        else:
            label = mydata.x.text().split(":")[1] + " vs " + mydata.y.text().split(":")[1]
            self.myfigure.axes.errorbar(mydata.x.datavalue, mydata.y.datavalue, yerr=mydata.yerr.datavalue,
                                        xerr=mydata.xerr.datavalue, label=label)
        try:
            ai.add_interactivity(fig=self.myfigure.fig, ax=self.myfigure.axes, nodrag=False, legsize=7)
        except:
            print("it seems that add_interactivity is not loaded. Check if the file is in pythonpath")
        self.myfigure.draw()


class Fast3D(QMainWindow):
    def __init__(self, mydata, parent=None, mname=None, **kwargs):
        super(Fast3D, self).__init__(parent)
        if mname is None:
            mname = '3D Viewer'
        self.setWindowTitle(mname)
        self.setWindowIcon(QIcon("web.png"))
        if mydata.ndim == 3:
            self.mydata = mydata
            try:
                self.shape = mydata.shape
            except Exception as exc:
                print(exc)
            self.myfigure = MplCanvas(parent=self, **kwargs)
            my_slider = DataChooser(self)
            self.update_plot(0, 0)
            mainwindow = QWidget()
            layout = QVBoxLayout()
            layout.addWidget(self.myfigure.toolbar)
            layout.addWidget(self.myfigure, stretch=1)
            layout.addWidget(my_slider)
            mainwindow.setLayout(layout)
            self.setCentralWidget(mainwindow)
            center(self)
            self.show()
        elif mydata.ndim > 3:
            messagebox = QMessageBox()
            messagebox.addButton(QMessageBox.Yes)
            reply = messagebox.exec_()
            if __name__ == "__main__" and reply == QMessageBox.Yes:
                sys.exit()
            elif reply == QMessageBox.Yes:
                qApp.quit()

    def update_plot(self, index, dimension, hold_it=False, is_log=False):
        """
        :param index: integer
        :param dimension:
        :param hold_it: logical
        :param is_log: logical
        """
        if dimension == 0:
            newdata = self.mydata[index]
        elif dimension == 1:
            newdata = self.mydata[:, index, :]
        elif dimension == 2:
            newdata = self.mydata[:, :, index]
        else:
            raise ValueError("dimensionality is too high")
        if hold_it:
            self.myfigure.image(newdata, self.myfigure.get_axis_values)
            if is_log:
                self.myfigure.im.set_norm(LogNorm(*self.myfigure.im.get_clim()))
        else:
            if is_log:
                old_lims = self.myfigure.im.get_clim()
                if (self.myfigure.im.get_array() == newdata).all():
                    self.myfigure.im.set_norm(LogNorm(*old_lims))
                else:
                    self.myfigure.image(newdata)
                    self.myfigure.im.set_norm(LogNorm(*self.myfigure.im.get_clim()))
            else:
                self.myfigure.image(newdata)
        #if is_log:
        #    print(newdata.min(), newdata.max())
        #    print(*self.myfigure.im.get_clim())

        try:
            self.myfigure.draw()
        except ValueError:
            help = HelpWindow(self, "it seems there are 0 or negative values.\n "
                                    "Before putting log, adjust limits \nand "
                                    "keep the values. Change back to lin for now.")
            return False
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
