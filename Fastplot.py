"""Module to make 2D plots with sliders to view 3D and 4D data faster. Also includes bases for line plots"""
import os
import sys
import matplotlib.pyplot as plt
import numpy
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (QApplication, QLabel, QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QMessageBox,
                             QMainWindow, qApp, QSlider, QStatusBar, QLineEdit, QInputDialog)
from matplotlib.path import Path
from matplotlib.widgets import LassoSelector
from numpy import ma
import numpy as np
import copy


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

SIZEVALS = numpy.array([0.1, 0.2, 0.5, 1, 2, 3, 4, 5, 8, 15, 20, 30, 50, 80, 150])


class Easyerrorbar(axs.Axes):
    """ Circumvent problem with normal matplotlib errorbar():

    error-bars not accessible, label assigned to error-bars. When getting lines on the axis, the error-bars
    are not accessible. To make things worse, the label, set on error-bar creation, is not assigned to the
    line object of the plot, but to the not accessible error-bars. This projection overwrites the normal
    error-bar and plots a single line, converting each point into 7 points, walking up-down the y error and then
    left-right the x-error before going to the next point."""
    name = 'easyerrorbar'

    def errorbar(self, x, y, yerr=None, xerr=None, **kwargs):
        """

        :param x: 1D array like  X coordinates for plot
        :param y: 1D array like Y coordinates for plot
        :param yerr: 1D array like X error for plot
        :param xerr: 1D array like Y error for plot
        :param kwargs: arguments passed on to axs.Axes.plot
        """
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
        super().plot(x2, y2, **kwargs)


class MplCanvas(FigureCanvasQTAgg):
    """
    Main class for the canvas to view 1, 2, 3 or 4D variables, either as line, scatter, image, pcolor or pcolormesh

    A mouse scroll zoom is activated
    """
    def __init__(self, parent=None, width=4, height=4, dpi=150, plotscheme="default", scatter_dot_size=5, **kwargs):
        """
        Canvas to view 1, 2, 3 or 4 D plots, here 3 and 4 D refer to 2 D with slicers

        :param parent: parent QT app
        :param width: float width of figure
        :param height: float height of figure
        :param dpi: int Resolution
        :param plotscheme: string or list of strings, see also plt.style.available for available style sheets
        :param scatter_dot_size: integer Size for markers in plot
        :param **kwargs contains all other passed parameters. Although not used here, it is important to include
        """
        try:
            plt.style.use(plotscheme)
        except:
            try:
                here = os.path.dirname(os.path.abspath(__file__))
                if (not isinstance(plotscheme, numpy.ndarray)) and (not isinstance(plotscheme, list)):
                    plotscheme = [plotscheme]
                plotschemenew = plotscheme[:-1]
                plotschemenew.append(os.path.join(here, plotscheme[-1]))
                plt.style.use(plotschemenew)
            except:
                pass
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        proj.register_projection(Easyerrorbar)  # this is needed for 1D errorbars.
        self.axes = self.fig.add_subplot(111, projection='easyerrorbar')
        super(MplCanvas, self).__init__(self.fig)
        self.scatter_dot_size = scatter_dot_size
        self.change_size = QSlider(Qt.Horizontal)
        self.change_size.setRange(0, len(SIZEVALS) - 1)
        self.change_size.setValue(numpy.argmin(numpy.abs(self.scatter_dot_size - SIZEVALS)))
        self.change_size.valueChanged.connect(self.change_scatter_size)
        self.toolbar = NavigationToolbar(self, parent)
        self.im = None
        self.cb = None
        self.sc_size_slider = None
        self.mpl_connect('key_press_event', self.on_key_press)
        self.setFocusPolicy(Qt.StrongFocus)
        self.mparent = parent
        self.scroll_zoom()

    def scroll_zoom(self, base_scale=2.):
        """
        using mouse scroll wheel to zoom in and out

        :param base_scale: factor by which to enlarge, inverse of this to shrink
        :return: Function zooming
        """
        def zooming(event):
            xlim = self.axes.get_xlim()
            ylim = self.axes.get_ylim()
            xdat = event.xdata
            ydat = event.ydata
            x_ext_r = (xlim[1] - xdat)
            x_ext_l = (xdat - xlim[0])
            y_ext_o = (ylim[1] - ydat)
            y_ext_u = (ydat - ylim[0])
            if event.button == 'up':
                # zoom in
                scale_factor = 1 / base_scale
            elif event.button == 'down':
                # zoom out
                scale_factor = base_scale
            else:
                scale_factor = 1
                print(event.button)
            self.axes.set_xlim([xdat - x_ext_l * scale_factor, xdat + x_ext_r * scale_factor])
            self.axes.set_ylim([ydat - y_ext_u * scale_factor, ydat + y_ext_o * scale_factor])
            self.axes.figure.canvas.draw_idle()

        self.mpl_connect('scroll_event', zooming)
        return zooming

    def on_key_press(self, event):
        """
        See key_press_handler help: implements default key bindings for canvas and toolbar.
        :param event: key press/ release event
        """
        try:
            key_press_handler(event, self, self.toolbar)
        except TypeError:
            pass

    def image(self, mdata, limits=None):
        """
        Plot the current 2D data as an image. Use either default limits or provided limits

        :param mdata: 2D array to display
        :param limits: dictionary with keys xlim, ylim, clim and cmap
        :return: None
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
        self.cb = self.fig.colorbar(self.im, ax=self.axes, shrink=0.8)
        return

    def change_scatter_size(self, value):
        """
        To change the scatter plot dot size with the slider
        :param value: float Size to change the scatter dots to
        """
        self.scatter_dot_size = SIZEVALS[value]
        self.im.set_sizes([SIZEVALS[value]])
        self.draw()

    def pcolormesh(self, x, y, z, only_indices=None):
        """
        Make a 2D plotting, either with pcolormesh or as scatter plot, depending on x, y and z dimensionality

        :param x: 1D or 2D array used for x-coordinate of pcolormesh or scatter
        :param y: 1D or 2D array used for y-coordinate of pcolormesh or scatter
        :param z: 1D or 2D array used for z-coordinate of pcolormesh or color mapping in scatter
        :param only_indices: array of integers, only used if x, y and z are 1D, limit scatter plot to those indices
        :return: bool, True if plot worked, False if plot failed
        """
        def adjustgrid(xin, yin):
            '''
            if the x and y grid have the same dimensions as the z data, make
            some approximation to get a grid that is (dimx+1, dimy+1) so it works
            with pcolormesh. The outer grid is adjusted by half the difference

            Parameters:
            -----------
            xin: 2D array (M, N)
                x coordinate array
            yin: 2D array  (M, N)
                y coordinate array

            Returns:
            --------
            newlon: 2D array (M+1, N+1)
                new x array
            newlat: 2D array (M+1, N+1)
                new y array
            '''
            lon = ma.copy(xin)
            lat = ma.copy(yin)
            dlony = ma.diff(lon)/2
            newlony = dlony + lon[:, :-1]
            newlony = ma.concatenate(
                ((lon[:, 0] - dlony[:, 0]).reshape(-1, 1),
                 newlony,
                 (lon[:, -1] + dlony[:,-1]).reshape(-1, 1)), axis=1)
            dlonx = ma.diff(newlony,axis=0)/2
            newlonx = dlonx + newlony[:-1, :]
            newlon = ma.concatenate(
                ((newlony[0, :] - dlonx[0, :]).reshape(1, -1),
                 newlonx,
                 (newlony[-1, :] + dlonx[-1, :]).reshape(1, -1)))
            dlaty = ma.diff(lat)/2
            newlaty = dlaty + lat[:, :-1]
            newlaty = ma.concatenate(
                ((lat[:, 0] - dlaty[:, 0]).reshape(-1, 1),
                 newlaty,
                 (lat[:, -1] + dlaty[:, -1]).reshape(-1, 1)), axis=1)
            dlatx = ma.diff(newlaty,axis=0)/2
            newlatx = dlatx + newlaty[:-1, :]
            newlat = ma.concatenate(
                ((newlaty[0, :] - dlatx[0, :]).reshape(1, -1),
                 newlatx,
                 (newlaty[-1, :] + dlatx[-1,:]).reshape(1, -1)))
            return newlon, newlat
        def remove_mask(xin, yin, zin):
            '''
            If there are masked values in the x or y coordinates, it is not
            possible to use pcolormesh and pcolor would need to be used. That is
            very slow. Instead, make sure that those values are also masked in
            the z-data and replace the masked values in the grid with the
            smallest unmasked ones in the grid.

            Parameters:
            -----------
            xin: 2D array (M, N)
                x coordinate array
            yin: 2D array  (M, N)
                y coordinate array
            zin: 2D array (M, N)
                z-data array

            Returns:
            --------
            lon: 2D array (M, N)
                new x array without masked values
            lat: 2D array (M, N)
                new y array without masked values
            zdata: 2D array (M, N)
                additionally masks all values that were masked in the grid
            '''
            lon = np.copy(xin)
            lon[xin.mask] = xin.min()
            lat = np.copy(yin)
            lat[yin.mask] = yin.min()
            mymask = zin.mask  | xin.mask[:-1, 1:]
            zdata = ma.array(np.copy(zin[:].data), mask=mymask)
            return lon, lat, zdata
        try:
            self.cb.remove()
        except AttributeError:
            pass
        except KeyError:
            pass
        try:
            xx = x.datavalue
            yy = y.datavalue
            cc = z.datavalue
            if cc.ndim == 1:  # this means it will be a scatter plot
                if only_indices is not None:
                    xx = xx[only_indices]
                    yy = yy[only_indices]
                    cc = cc[only_indices]
                self.im = self.axes.scatter(xx, yy, c=cc, s=self.scatter_dot_size)
                if self.sc_size_slider is None:
                    self.sc_size_slider = self.toolbar.addWidget(self.change_size)
            elif (xx.shape == yy.shape) and (xx.ndim != 1):
                if tuple([zentry+1 for zentry in cc.shape]) == xx.shape:
                    try:
                        self.im = self.axes.pcolormesh(xx, yy, cc)
                    except ValueError:
                        print("The data is one less than the grid, no fix but\n"
                               "there are masked values in the grid coordinats.\n "
                               "Make a crude fix, pcolor is too slow!")
                        newx,newy,newz = remove_mask(xx,yy,cc)
                        self.im = self.axes.pcolormesh(newx, newy, newz)
                else:  # assume grid has the same size as zarray
                    xnew, ynew = adjustgrid(xx, yy)
                    try:
                        self.im = self.axes.pcolormesh(xnew, ynew, cc)
                    except ValueError:
                        print(
                               "The data is same saize as the grid, a fix applied\n"
                               "and there are masked values in the grid coordinats.\n "
                               "Make a crude fix, pcolor is too slow!")
                        lon, lat, zdata = remove_mask(xnew, ynew, cc)
                        self.im = self.axes.pcolormesh(lon, lat, zdata)
            elif (xx.ndim == 1) & (yy.ndim == 1):
                # this sould mean that both xx and yy are 1D and together form the shape of cc
                if xx.size in cc.shape:
                    # make xx one longer. Shift outer boundaries by the nearest diff
                    xdiff = ma.diff(xx)/2
                    xxnew = xdiff + xx[:-1]
                    xxnew = ma.concatenate((xx[:1]-xdiff[0], xxnew, xx[-1:]+xdiff[-1]))
                else:
                    xxnew = xx
                if yy.size in cc.shape:
                    ydiff = ma.diff(yy)/2
                    yynew = ydiff + yy[:-1]
                    yynew = ma.concatenate((yy[:1]-ydiff[0], yynew, yy[-1:]+ydiff[-1]))
                else:
                    yynew = yy
                # handle masks in the x-y axis
                if xxnew.mask.any() or yynew.mask.any():
                    xxnew = ma.copy(xxnew)
                    yynew = ma.copy(yynew)
                    # find indices that are masked in the grid coordinates
                    indxs_maskx = np.arange(len(xxnew))[xxnew.mask]
                    indxs_masky = np.arange(len(yynew))[yynew.mask]
                    # since the grid gives borders, the data point before also
                    # needs to be masked out, but not if the first grid is masked
                    indxs_maskx2 = indxs_maskx - 1
                    indxs_masky2 = indxs_masky - 1
                    indxs_maskx2 = indxs_maskx2[indxs_maskx2>0]
                    indxs_masky2 = indxs_masky2[indxs_masky2>0]
                    indxs_maskx = indxs_maskx[indxs_maskx<len(xxnew)-1]
                    indxs_masky = indxs_masky[indxs_masky<len(yynew)-1]
                    # also, if the masked grid boundary is the last (n), then only
                    # the data position at (n-1) has to be masked out, (n) does
                    # not exist.
                    ccnew = np.ma.copy(cc)
                    # mask those coordinates out in the data grid
                    ccnew.mask = ma.getmaskarray(ccnew)
                    ccnew.mask[indxs_masky,:] = True
                    ccnew.mask[:, indxs_maskx] = True
                    ccnew.mask[indxs_masky2,:] = True
                    ccnew.mask[:, indxs_maskx2] = True
                    xxnew[xxnew.mask] = xxnew.min()
                    yynew[yynew.mask] = yynew.min()
                else:
                    ccnew = cc
                try:
                    self.im = self.axes.pcolormesh(xxnew, yynew, ccnew)
                except TypeError as exc1:
                    HelpWindow(self, "careful: z data is transposed to fit x and y")
                    self.im = self.axes.pcolormesh(xxnew, yynew, ccnew.T)
            else:
                HelpWindow(self.mparent, "the dimensions seem wrong\n"
                           "xdim: " + str(xx.shape) + " ydim: " +
                           str(yy.shape) + " zdim: " + str(xx.shape))
                return False
        except Exception as exc1:
            HelpWindow(self.mparent, "something went really wrong " + str(exc1))
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

    def set_axis_values(self, mdict):
        self.im.set_clim(mdict["clim"])
        self.im.axes.set_xlim(mdict["xlim"])
        self.im.axes.set_ylim(mdict["ylim"])
        self.im.set_cmap(mdict["cmap"])


class DataChooser(QWidget):
    """Class to handle data with 3 or 4 dimensions: includes sliders for the choice of 2D slides"""
    def __init__(self, parent, is3d=True, is4d=False, is3dspecial=False, dimnames=None, **kwargs):
        print("in DataChooser", is3dspecial)
        super().__init__(**kwargs)
        layout4 = QHBoxLayout()
        layout5 = QVBoxLayout()
        self.is3d = is3d
        self.is4d = is4d
        self.is3dspecial = is3dspecial
        self.dimnames = dimnames
        slicings = QWidget()
        layout2 = QVBoxLayout()
        slider = None
        layout3 = None
        dimensions = None
        if is3d or is3dspecial:
            if is3dspecial:
                print("here:", str(is3dspecial[0] - 1))
                print("dd:", parent.mydata.dimension)
                print("here2:", parent.mydata.dimension[is3dspecial[1]])
                self.slice_label = QLabel("slice = 0" + "/ 0-" + str(is3dspecial[0] - 1)  + " of " + parent.mydata.dimension[is3dspecial[1]] )
            else:
                if self.dimnames:
                    self.slice_label = QLabel("slice = 0" + "/ 0-" + str(parent.shape[0] - 1) + " of " + self.dimnames[0])
                else:
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
            if self.dimnames:
                self.slice_label2 = QLabel("slice = 0" + "/ 0-" + str(parent.shape[1] - 1) + " of " + self.dimnames[1])
            else:
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
            slider2.setRange(1, len(parent.shape) - 1)
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
        if is3dspecial:
            slicings.setLayout(layout2)
            self.freeze_button = QPushButton('keep settings')
            self.freeze_button.clicked.connect(self.on_freeze)
            layout5.addWidget(self.freeze_button)
            layout4.addWidget(slicings)
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
        if self.is3d or self.is3dspecial:
            if self.is4d:
                worked = self.mparent.update_plot(self.active_index, self.active_dimension, self.frozen, self.is_log,
                                                  idx2=self.active_index2, dim2=self.active_dimension2)
                if not worked:
                    self.is_log = False
                    self.log_button.setText("put log")
                    _ = self.mparent.update_plot(self.active_index, self.active_dimension, self.frozen,
                                                 self.is_log,
                                                 idx2=self.active_index2, dim2=self.active_dimension2)
            else:
                worked = self.mparent.update_plot(self.active_index, self.active_dimension, self.frozen, self.is_log)
                if not worked:
                    self.is_log = False
                    self.log_button.setText("put log")
                    _ = self.mparent.update_plot(
                        self.active_index, self.active_dimension, self.frozen, self.is_log)
        else:
            worked = self.mparent.update_plot(self.is_log)
            if not worked:
                self.is_log = False
                self.log_button.setText("put log")
                _ = self.mparent.update_plot(self.is_log)
        return

    def on_freeze(self):
        if self.is3d or self.is3dspecial:
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
                    _ = self.mparent.update_plot(
                        self.active_index, self.active_dimension, self.frozen, self.is_log,
                        idx2=self.active_index2, dim2=self.active_dimension2)
            else:
                worked = self.mparent.update_plot(self.active_index, self.active_dimension, self.frozen, self.is_log)
                if not worked:
                    self.is_log = False
                    self.log_button.setText("put log")
                    _ = self.mparent.update_plot(
                        self.active_index, self.active_dimension, self.frozen, self.is_log)

    def update_dim_label(self, value):
        if self.is3d:
            self.active_dimension = value
            self.update_slice()
            self.dim_label.setText("dim = " + str(value))
            if self.dimnames:
                self.slice_label.setText(
                    "slice = " + (str(self.active_index)) + "/ 0-" + str(self.mparent.shape[value] - 1) + " of " +
                                      self.dimnames[value])
            else:
                self.slice_label.setText(
                    "slice = " + (str(self.active_index)) + "/ 0-" + str(self.mparent.shape[value] - 1))

    def update_dim_label2(self, value):
        self.active_dimension2 = value
        self.update_slice()
        self.dim_label2.setText("dim = " + str(value))
        if self.dimnames:
            self.slice_label2.setText("slice = " + (str(self.active_index2)) + "/ 0-" + str(self.mparent.shape[value] - 1) + " of " +
                                      self.dimnames[value])
        else:
            self.slice_label2.setText("slice = " + (str(self.active_index2)) + "/ 0-" + str(self.mparent.shape[value] - 1))

    def on_minus(self):
        if self.is3d or self.is3dspecial:
            if self.is3dspecial:
                mymax = self.is3dspecial[0]
            else:
                mymax = self.mparent.shape[self.active_dimension]
            if self.active_index > -(mymax-1):
                self.active_index -= 1
            else:
                self.active_index = 0
            self.update_slice()

    def on_minus2(self):
        mymax = self.mparent.shape[self.active_dimension2]
        if self.active_index2 > -(mymax-1):
            self.active_index2 -= 1
        else:
            self.active_index2 = 0
        self.update_slice()

    def on_plus(self):
        if self.is3d or self.is3dspecial:
            if self.is3dspecial:
                mymax = self.is3dspecial[0]
            else:
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
        if self.is3d or self.is3dspecial:
            if not self.is4d:
                worked = self.mparent.update_plot(self.active_index, self.active_dimension, self.frozen, self.is_log)
                if not worked:
                    self.is_log = False
                    self.log_button.setText("put log")
                    _ = self.mparent.update_plot(self.active_index, self.active_dimension, self.frozen,
                                                 self.is_log)
                if self.is3dspecial:
                    self.slice_label.setText("slice = " + str(self.active_index) + "/ 0-" + str(
                       self.is3dspecial[0] - 1) + " of " + str(self.mparent.mydata.dimension[self.is3dspecial[1]]))
                else:
                    if self.dimnames:
                        self.slice_label.setText("slice = " + str(self.active_index) + "/ 0-" + str(
                            self.mparent.shape[self.active_dimension] - 1) + " of " +
                                      self.dimnames[self.active_dimension])
                    else:
                        self.slice_label.setText("slice = " + str(self.active_index) + "/ 0-" + str(
                            self.mparent.shape[self.active_dimension] - 1))
            else:
                worked = self.mparent.update_plot(self.active_index, self.active_dimension,
                                                  self.frozen, self.is_log, idx2=self.active_index2,
                                                  dim2=self.active_dimension2)
                if not worked:
                    self.is_log = False
                    self.log_button.setText("put log")
                    _ = self.mparent.update_plot(self.active_index, self.active_dimension,
                                                 self.frozen, self.is_log, idx2=self.active_index2,
                                                 dim2=self.active_dimension2)
                if self.dimnames:
                    self.slice_label.setText("slice = " + str(self.active_index) + "/ 0-" + str(
                        self.mparent.shape[self.active_dimension] - 1) + " of " +
                                      self.dimnames[self.active_dimension])
                    self.slice_label2.setText("slice = " + str(self.active_index2) + "/ 0-" + str(
                        self.mparent.shape[self.active_dimension2] - 1) + " of " +
                                      self.dimnames[self.active_dimension2])
                else:
                    self.slice_label.setText("slice = " + str(self.active_index) + "/ 0-" + str(
                        self.mparent.shape[self.active_dimension] - 1))
                    self.slice_label2.setText("slice = " + str(self.active_index2) + "/ 0-" + str(
                        self.mparent.shape[self.active_dimension2] - 1))


class Fast2D(QMainWindow):
    def __init__(self, master, mydata, parent=None, mname=None, filename=None, dark=False, only_indices=None, is3dsp=False, mydata_dims=None, **kwargs):
        if master is None:
            master = QApplication([])
        super(Fast2D, self).__init__(parent)
        self.isimage = True
        self.master = master
        if mydata.__class__.__name__ == "Data":
            self.isimage = False
            self.x = mydata.x.copy()
            self.y = mydata.y.copy()
            mydata = mydata.z.copy()
            if only_indices is not None:
                self.x.datavalue = self.x.datavalue[only_indices]
                self.y.datavalue = self.y.datavalue[only_indices]
                mydata.datavalue = mydata.datavalue[only_indices]
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
        my_slider = DataChooser(self, is3d=False, is3dspecial=is3dsp)
        self.active_button = QPushButton("make active")
        self.active_button.clicked.connect(self.make_active)
        mainwindow = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.myfigure.toolbar)
        layout.addWidget(self.active_button)
        layout.addWidget(self.myfigure, stretch=1)
        layout.addWidget(my_slider)
        mainwindow.setLayout(layout)
        if self.isimage:
            self.myfigure.image(mydata)
            if mydata_dims and len(mydata_dims) == 2:
                self.myfigure.axes.set_ylabel(mydata_dims[0])
                self.myfigure.axes.set_xlabel(mydata_dims[1])
            self.myfigure.axes.set_title(mname)
        else:
            worked = self.myfigure.pcolormesh(self.x, self.y, mydata)  # , only_indices)
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
        self.myfigure.fig.set_tight_layout(True)
        self.show()
        return

    def add_to_plot(self, mydata, only_indices=None, symbol=None):
        if only_indices is not None:
            newx = mydata.x.copy()
            newy = mydata.y.copy()
            newz = mydata.z.copy()
            newx.datavalue = newx.datavalue[only_indices]
            newy.datavalue = newy.datavalue[only_indices]
            newz.datavalue = newz.datavalue[only_indices]
        else:
            newx = mydata.x
            newy = mydata.y
            newz = mydata.z
        #if self.mydata.datavalue.ndim > 1:
        #    HelpWindow(self, "cannot update image plot")
        #    return
        #else:
        if newz.datavalue is None:
            label = newx.name_value + " vs " + newy.name_value
            try:
                if symbol:
                    self.myfigure.axes.plot(newx.datavalue, newy.datavalue, marker=symbol, lw=0, label=label)
                else:
                    self.myfigure.axes.plot(newx.datavalue, newy.datavalue, lw=1, label=label)
            except ValueError as exvalerr:
                HelpWindow(self, "The following error occured trying to add a plot: " + str(exvalerr))
                return
            self.myfigure.draw()
            try:
                ai.add_interactivity(fig=self.myfigure.fig, ax=self.myfigure.axes, nodrag=False, legsize=7)
            except:
                print("it seems that add_interactivity is not loaded. Check if the file is in pythonpath")
        elif newz.datavalue.ndim > 1:
            HelpWindow(self, "cannot update plot with z value of ndim > 1, only scatter plot type")
            return
        else:
            if self.mydata.datavalue.ndim == 1:
                self.x.datavalue = numpy.r_[self.x.datavalue, newx.datavalue]
                self.y.datavalue = numpy.r_[self.y.datavalue, newy.datavalue]
                self.mydata.datavalue = numpy.r_[self.mydata.datavalue, newz.datavalue]
                self.myfigure.cb.remove()
                self.myfigure.im.remove()
                worked = self.myfigure.pcolormesh(self.x, self.y, self.mydata)
            else:
                self.myfigure.pcolormesh(newx, newy, newz)
        self.myfigure.draw()
        #if not worked:
        self.show()
        return

    def make_active(self):
        self.master.active1D = self

    def update_plot(self, is_log=False):
        if is_log:
            if min(*self.myfigure.im.get_clim()) <= 0:
                _ = HelpWindow(
                    self, "it seems there are 0 or negative values.\n "
                    "Before putting log, adjust limits \nand keep the values. Change back to lin for now.")
                return False
            self.myfigure.im.set_norm(LogNorm(*self.myfigure.im.get_clim()))
        else:
            self.myfigure.im.set_norm(Normalize(*self.myfigure.im.get_clim()))
        try:
            self.myfigure.draw()
        except (ValueError, ZeroDivisionError):
            _ = HelpWindow(
                self, "it seems there are 0 or negative values.\n "
                "Before putting log, adjust limits \nand keep the values. Change back to lin for now.")
            return False
        return True


class Fast2Dplus(Fast2D):
    '''
    This is really a 3D plot, however it does not allow for slicing, because
    x and y axis are specified. It does however allow to change the "level" of
    the third dimension.
    '''
    def __init__(self, master, mydat, parent=None, mname=None, filename=None, dark=False, only_indices=None, **kwargs):
        print (kwargs)
        mydata = mydat.copy()
        self.odata = mydat
        if master is None:
            master = QApplication([])
        # Try to figure out which dimension is the extra dimension
        one, two, three = mydata.z.datavalue.shape
        different_ones = set([one, two, three])
        # if there are duplicated dimensions, let the user choose
        if len(different_ones)< 3:
            extraid, _ = QInputDialog.getText(master, 'Set z-dimension', 'There are duplicated dimensions.\n'
                                              'Current dimensions of z are: '+ str(mydat.z.dimension) + '\n'
                                              'Type (0,1,2) for the dimension along which to slice, i.e.\n'
                                              'that are not x- and y-. \n'
                                              'x-dimension is:' + str(mydat.x.dimension) +
                                              '\ny-dimension is:' + str(mydat.y.dimension))
            extraid = int(extraid)
        else:
            in_z = []
            for midx in different_ones:
                if (midx in mydata.x.datavalue.shape) or (midx in mydata.y.datavalue.shape):
                    in_z.append(midx)
                elif (midx+1 in mydata.x.datavalue.shape) or (midx in mydata.y.datavalue.shape):
                    in_z.append(midx)
            if len(in_z) == 2:
                extraid = np.arange(3)[[x not in in_z for x in mydata.z.datavalue.shape]][0]
            else:  # unclear, let the user choose
                extraid, _ = QInputDialog.getText(self, 'Set z-dimension', 'There are duplicated dimensions. Which (0,1,2) is z?')
        if extraid == 0:
            mydata.z.datavalue = mydata.z.datavalue[0]
            ext_in_dir = mydat.z.datavalue.shape[0]
        elif extraid == 1:
            mydata.z.datavalue = mydata.z.datavalue[:,0]
            ext_in_dir = mydat.z.datavalue.shape[1]
        elif extraid == 2:
            mydata.z.datavalue = mydata.z.datavalue[:,:,0]
            ext_in_dir = mydat.z.datavalue.shape[2]
        super(Fast2Dplus, self).__init__(master, mydata, parent, mname, filename, dark, only_indices, is3dsp=(ext_in_dir, extraid), **kwargs)
        self.master = master
        self.my_ext_dim = extraid
        #
        #extraid = int(extraid)
        #print("shape of z was: ", mydata.z.datavalue.shape)
        #temp = Fast2D(master, mydata, parent, mname, filename, dark, only_indices, is3dsp=True, **kwargs)

    def update_plot(self, active_index, active_dimension, frozen, is_log, idx2=None, dim2=None):
        if frozen:
            axesvalues = self.myfigure.get_axis_values
        self.myfigure.cb.remove()
        self.myfigure.im.remove() #set_visible(False)
        if self.my_ext_dim == 0:
            self.mydata.datavalue = self.odata.z.datavalue[active_index]
        elif self.my_ext_dim == 1:
            self.mydata.datavalue = self.odata.z.datavalue[:, active_index]
        elif self.my_ext_dim == 2:
            self.mydata.datavalue = self.odata.z.datavalue[:, :, active_index]
        if frozen:
            worked = self.myfigure.pcolormesh(self.x, self.y, self.mydata)
            self.myfigure.set_axis_values(axesvalues)
        else:
            worked = self.myfigure.pcolormesh(self.x, self.y, self.mydata)
        self.myfigure.draw()

        # maybe the below only is done if not frozen.
        if is_log:
            if min(*self.myfigure.im.get_clim()) <= 0:
                _ = HelpWindow(
                    self, "it seems there are 0 or negative values.\n "
                    "Before putting log, adjust limits \nand keep the values. Change back to lin for now.")
                return False
            self.myfigure.im.set_norm(LogNorm(*self.myfigure.im.get_clim()))
        else:
            self.myfigure.im.set_norm(Normalize(*self.myfigure.im.get_clim()))
        try:
            self.myfigure.draw()
        except (ValueError, ZeroDivisionError):
            _ = HelpWindow(
                self, "it seems there are 0 or negative values.\n "
                "Before putting log, adjust limits \nand keep the values. Change back to lin for now.")
            return False
        return True


class Fast1D(QMainWindow):
    def __init__(self, master, mydata, symbol=False, mname=None, filename=None, dark=False, only_indices=None, mydata_dims=None,
                 **kwargs):
        super().__init__()
        if mname is None:
            mname = '1D Viewer'
        self.master = master
        self.setWindowTitle(mname)
        self.only_indices = only_indices
        self.setWindowIcon(QIcon("web.png"))
        self.myfigure = MplCanvas(self, **kwargs)
        try:
            self.myfigure.toolbar.actions()[7].triggered.connect(self.add_interactivity)
        except:
            pass
        self.lassos = []
        self.current_idx = []
        self.active_button = QPushButton("make active")
        self.active_button.clicked.connect(self.make_active)
        mainwindow = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.myfigure.toolbar)
        layout.addWidget(self.active_button)
        layout.addWidget(self.myfigure, stretch=1)
        mainwindow.setLayout(layout)
        self.setCentralWidget(mainwindow)
        try:
            self.update_plot(mydata, symbol, only_indices)
        except ValueError as valerr:
            _ = HelpWindow(
                self, "Probably you chose to plot x-y with different dimensions? Errormessage: " + str(valerr))
        self.myfigure.axes.set_xlabel(mydata.x.text().split(":")[1])
        self.myfigure.axes.set_ylabel(mydata.y.text().split(":")[1])
        center(self)
        if filename is not None:
            statusbar = QStatusBar()
            statusbar.showMessage(filename)
            self.setStatusBar(statusbar)
        if dark:
            palette = QDarkPalette()
            self.setPalette(palette)
        self.myfigure.fig.set_tight_layout(True)
        self.show()

    def make_active(self):
        self.master.active1D = self

    def onselect(self, hh, xdata, ydata):
        def onsel(verts, my_hh=hh, my_xdata=xdata, my_ydata=ydata):
            pts = [(xi, yi) for xi, yi in zip(my_xdata, my_ydata)]
            path = Path(verts)
            idxs = numpy.nonzero(path.contains_points(pts))[0]
            mask = numpy.full([len(pts), ], fill_value=False)
            mask[idxs] = True
            labelx, labely = [entr.strip() for entr in my_hh.split("vs")]
            self.current_idx = idxs

        return onsel

    def update_plot(self, mydata, symbol=False, oi=None):
        if mydata.y.datavalue.ndim > 1:
            alllabel = mydata.y.text().split(":")[1].split("s.")[-1].split(" - ")
            labs = numpy.arange(int(alllabel[0]), int(alllabel[1]) + 1)
            if mydata.x.datavalue.ndim > 1:
                if not mydata.x.datavalue.shape == mydata.y.datavalue.shape:
                    raise ValueError(
                        "x and y have different shapes, make sure to choose either same number of rows/cols"
                        " or either for x or y only 1 column/ row and that the length of the x and y data is equal.")
                alllabel2 = mydata.x.text().split(":")[1].split("s.")[-1].split(" - ")
                labcols = numpy.arange(int(alllabel2[0]), int(alllabel2[1]) + 1)
                for row, col, lab, labcol in zip(mydata.y.datavalue, mydata.x.datavalue, labs, labcols):
                    if oi is not None:
                        row = row[oi]
                        col = col[oi]
                    label = (mydata.x.text().split(":")[1].split("s.")[0] + " " + str(labcol) +
                             " vs " + mydata.y.text().split(":")[1].split("s.")[0] +
                             " " + str(lab))
                    if symbol:
                        self.myfigure.axes.plot(col, row, marker=symbol, lw=0, label=label)
                        self.lassos.append(make_lasso(col, row, self.onselect, label, self.myfigure.axes))
                    else:
                        self.myfigure.axes.plot(col, row, label=label)
            else:
                xdata = numpy.copy(mydata.x.datavalue)
                if oi is not None:
                    xdata = xdata[oi]
                for row, lab in zip(mydata.y.datavalue, labs):
                    if oi is not None:
                        row = row[oi]
                    label = (mydata.x.text().split(":")[1] + " vs " + mydata.y.text().split(":")[1].split("s.")[0] +
                             " " + str(lab))
                    if symbol:
                        self.myfigure.axes.plot(xdata, row, marker=symbol, lw=0, label=label)
                        self.lassos.append(make_lasso(xdata, row, self.onselect, label,
                                                      self.myfigure.axes))
                    else:
                        self.myfigure.axes.plot(xdata, row, label=label)
        elif mydata.x.datavalue.ndim > 1:
            ydata = numpy.copy(mydata.y.datavalue)
            if oi is not None:
                ydata = ydata[oi]
            alllabel = mydata.x.text().split(":")[1].split("s.")[-1].split(" - ")
            labs = numpy.arange(int(alllabel[0]), int(alllabel[1]) + 1)
            for row, lab in zip(mydata.x.datavalue, labs):
                if oi is not None:
                    row = row[oi]
                label = (mydata.x.text().split(":")[1].split("s.")[0] + " " + str(lab) + " vs " +
                         mydata.y.text().split(":")[1])
                if symbol:
                    self.myfigure.axes.plot(row, ydata, marker=symbol, lw=0, label=label)
                    self.lassos.append(make_lasso(row, ydata, self.onselect, label, self.myfigure.axes))
                else:
                    self.myfigure.axes.plot(row, ydata, label=label)
        else:
            label = mydata.x.text().split(":")[1] + " vs " + mydata.y.text().split(":")[1]
            xdata = numpy.copy(mydata.x.datavalue)
            ydata = numpy.copy(mydata.y.datavalue)
            if oi is not None:
                xdata = xdata[oi]
                ydata = ydata[oi]
            if symbol:
                self.myfigure.axes.plot(xdata, ydata, marker=symbol, lw=0, label=label)
                self.lassos.append(make_lasso(xdata, ydata, self.onselect, label, self.myfigure.axes))
            else:
                self.myfigure.axes.errorbar(xdata, ydata, yerr=mydata.yerr.datavalue,
                                            xerr=mydata.xerr.datavalue, label=label)
        try:
            ai.add_interactivity(fig=self.myfigure.fig, ax=self.myfigure.axes, nodrag=False, legsize=7)
        except:
            print("it seems that add_interactivity is not loaded. Check if the file is in pythonpath")
        self.myfigure.draw()

    def add_interactivity(self):
        self.myfigure.axes.get_legend().remove()
        ai.add_interactivity(fig=self.myfigure.fig, ax=self.myfigure.axes, nodrag=False, legsize=7)
        self.myfigure.draw()


def make_lasso(xdata, ydata, mfunc, label, axis):
    """
    Activate a lasso selector on axis

    :param xdata: x-indeces
    :param ydata: y-indices
    :param mfunc: Function to execute with the LassoSelector
    :param label: str
    :param axis: axis handle Axis to activate LassoSelector on
    :return: Function LassoSelector activated on axis calling function myfunc
    """
    myfunc = mfunc(label, xdata, ydata)
    return LassoSelector(axis, myfunc)


class Fast3D(QMainWindow):
    def __init__(self, mydata, parent=None, mname=None, filename=None, dark=False, mydata_dims=None, **kwargs):
        """

        :param mydata: 3D or 4D array of data to display
        :param parent: Qt app handle
        :param mname: string, Name to put as title in the window
        :param filename: string, Name to put in the status bar
        :param dark: bool, if True use the color palette defined as QDarkPalette
        :param kwargs: other parameters passed trough to MplCanvas (e.g.
        """
        self.dimnames =mydata_dims
        if mydata.ndim == 4:
            self.is4d = True
        else:
            self.is4d = False
        super(Fast3D, self).__init__(parent)
        if mname is None:
            mname = '3D Viewer'
        self.setWindowTitle(mname)
        if mydata.ndim <= 4:
            self.mydata = mydata
            try:
                self.shape = mydata.shape
            except Exception as exc:
                print(exc)
            self.myfigure = MplCanvas(parent=self, **kwargs)
            self.my_slider = DataChooser(self, is4d=self.is4d, dimnames=mydata_dims)
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
        :param idx2: integer Index in the second dimension
        :param dim2: integer Number of the second dimension
        :param index: integer Index in the first dimension
        :param dimension: integer Number of the first dimension
        :param hold_it: bool True if plotting in the existing active axis
        :param is_log: bool True makes color scale log
        :return: bool, True if all worked, False otherwise
        """
        try:
            if dimension == 0:
                newdata = self.mydata[index]
            elif dimension == 1:
                newdata = self.mydata[:, index, :]
            elif dimension == 2:
                newdata = self.mydata[:, :, index]
            else:
                HelpWindow(
                    self,
                    "dimension 1 cannot be larger than 3, because the second slider has to have a higher dimension")
                return False
            if self.dimnames:
                dimnames = list(self.dimnames)
                _ = dimnames.pop(dimension)
        except IndexError:
            HelpWindow(self, "It seems you chose an index that does not exist. Maybe you changed slicing at high index")
            return False
        if dim2 is not None:
            if dim2 <= dimension:
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
                if self.dimnames:
                    _ = dimnames.pop(dim2-1)
            except IndexError:
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
                        _ = HelpWindow(
                            self, "it seems there are 0 or negative values.\n "
                            "Before putting log, adjust limits \nand keep the values. Change back to lin for now.")
                        return False
                    self.myfigure.im.set_norm(LogNorm(*old_lims))
                else:
                    self.myfigure.image(newdata)
                    if min(*self.myfigure.im.get_clim()) <= 0:
                        _ = HelpWindow(
                            self, "it seems there are 0 or negative values.\n "
                            "Before putting log, adjust limits \nand keep the values. Change back to lin for now.")
                        return False
                    self.myfigure.im.set_norm(LogNorm(*self.myfigure.im.get_clim()))
            else:
                self.myfigure.image(newdata)
        try:
            if self.dimnames:
                self.myfigure.axes.set_ylabel(dimnames[0])
                self.myfigure.axes.set_xlabel(dimnames[1])
            self.myfigure.draw()
        except (ValueError, ZeroDivisionError):
            HelpWindow(self, "it seems there are 0 or negative values.\n "
                             "Before putting log, adjust limits \nand "
                             "keep the values. Change back to lin for now.")
            return False
        except RuntimeError:
            HelpWindow(self, "sorry, something bad happened")
        self.myfigure.fig.set_tight_layout(True)
        return True


def main():
    """
    For demonstation purpose only: pltos a 4D array as image with two sliders for the dimension slicing
    :return: None
    """
    app = QApplication([])
    mdata = numpy.random.random((10, 10, 10, 20))
    mdata[0, :, :, :] = 0
    mdata[-1, :, :, :] = 10
    mdata[:, 0, :, :] = 5
    mdata[:, :, 3, :] = 3
    mdata[:, :, :, 4] = 2
    Fast3D(mdata)
    if __name__ == "__main__":
        sys.exit(app.exec_())


if __name__ == "__main__":
    main()
