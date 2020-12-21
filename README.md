# QTnetCDF

QTnetCDF is a hdf/ netCDF4 viewer with emphasis on plotting. It is implemented in python and uses QT. 
It can open netCDF4, hdf5 and hdf4 files. For hdf4 files, it tries to remove the vdata that only represents sd variable attributes or dimensions. The functionality for hdf4 files is somewhat reduced. 

It is tested with python3.7 (on linux) and python3.8 on windows. Under windows, it works with installing the needed packages via anaconda and python3.8. Under linux, it is recommended to use the setup scripts in conjuction with pip and python3.7, see Quick start below. 


## Quick start for linux

Create and activate a virtual environment:

    python3.7 -m venv newenv_test
    source newenv_test/bin/activate

download both QTnetCDF and add_interactivity:

    git clone  https://github.com/mmf1982/QTnetCDF
    git clone  https://github.com/mmf1982/add_interactivity

inside the respecitve directories, run:

    python3.7 setup.py install

It might be that the package pyhdf needed for QTnetCDF throws an error. If so, try manually to do:

    python3.7 -m pip install pyhdf
and then redo the installation of QTnetCDF (phython3.7 setup.py install in the QTnetCDF4 directory).

Download for example a h5/ hdf/ nc file from here: https://hdfeos.org/zoo/index_openNSIDC_Examples.php  

and then call as 

    python3.7 -m NetCDF4viewer whatever_is_your_test_filename.nc_or_hdf_or_h5_or_hdf4

with

    deactivate
    
you can leave the virtual environment again. OF course you do not need to work within a virual environment in the frist place, but it might be the saver option if you just want to give it a try. 

## Basic functionality

  The file representation that opens after opening a file looks like this:
  
  ![File when opened](/images/collapsed_file.png)
    
  A click on the triangle infront of a group (or main file level), opens the group.
  
  ![Expanend group](/images/open_file.png)
  
  The following keys are activated on the tree (always on the entry in the first column, marked with the red oval above!):
  * double click on variable: plot Supported are 1D, 2D, 3D and 4D variables.
  * "d" key is pressed on selected line, attribute information of that group or variable is prited.
  * "s" key is pressed on selected variable opens it as a detachable table view ![Table view](/images/open_table.png) (for 0D, 1D, 2D, 3D and 4D variables. Higher dimensions are not supported. 4D variables with large grids might cause problems because a complete variable is read into memory). If the variable is 3D it shows slice 0 along the zeroth dimension, This can be changed by a slicer bar and "+"/ "-" buttons and an entry field. If the variable is 4D, the slice is as for 3D and additionally slice 0 along the first dimension. Note that the second slicer always needs have a dimension at least one higher than the first. Each slicer also has an entry field where the field number can be entered directly (hit enter key to confirm). 
  * "x" data set as x for line plot
  * "y" data set as y for line plot
  * "e" data set as error on x for line plot
  * "u" data set as error on y for line plot
  * "m" to loaded to misc. Data can then be combined with other data via the "/", "*", "+" and "-" buttons. Note that a+b/c will be calculated as (a+b)/c. The data set here (either as a full 1, 2, 3 or 4 D variable or a 1D or 2D subset) can either be set as x, y or z (as x etc) variable or directly plotted (plot misc) ![Misc](/images/misc.png)
 

## New features:
  * More than one file can be opened and plots can be made in a common window, this adds two extra buttons to the window of the first file: ![Extra buttons](/images/extra_button.png), one to make the plot window available (*broadcast plot*), the other, *set same data*, see following point.
  
  * If the same variables (same path to the variables) should be plotted from different files, they only need to be set in the first file (not supported for hdf4) and can then be set for all other windows with the *set same data* button.
  * A simple country and coast line plot can be overlayed on longitude-latitude plots, button *add country lines* above. This is possible to pcolormesh plots (so if x, y and z are all 2D or if x and y are 1D but z is 2D) and also to scatter plots (so if x, y and z are all 1D):
  
   scatter                   |  pcolormesh
  ---------------------------|-------------------------
  ![Scatter](/images/scatter_countries.png) | ![Pcolormesh](/images/pcolormesh_country.png)
  
  (note the slider for the pixel size in the scatter plot)
  * variables can be multiplied, divided, added and subtracted before plotting, see "m" above. 
  * the scrolling wheel can be used to scroll in and out.
  * If a plot was made with button *plot symbol*, the lasso selector can be used:
  ![Lasso Selector](/images/choose.png) 
  
  Together with button *use idxs?* which turns into *using idxs only*, this can be used to restrict the indices in following plots, like here were values for x, y and z has been chosen:
  
  ![Choise](/images/choice.png)
  
  The result is a scatter plot only containing indices that were chosen with the lasso selector, in the displayed case, for which the validity is 100:  
  ![Scatter Plot](/images/chosen.png). 
  
  Also note the slider with which the size of the scatter plots can be adjusted. 

## Plotting

  The main thing about this tool is the plotting, you can do line/ marker plots, image, pcolormesh or scatter plots. Data is supported up to 4 dimensions.

  ### 1D plotting

  If a variable is 1D, a double click will automatically plot it over its index. However, x, y, xerr and yerr can also be set. Either as a 1D variable as described above, or from the table view (after "s" on a 1, 2, 3 or 4D variable) on which the following keys are activated: 

  * "x" data set as x for line plot
  * "y" data set as y for line plot
  * "e" data set as error on x for line plot
  * "u" data set as error on y for line plot
  * "m" to load to misc and combine it with other data

  In the table, multiple rows or columns can be selected for y or x (and also for both). How the data is interpreted and plot depends on whether there are  
  multiple rows/ columns are selected for both variables or not: 
  
  * If for both of them more than one are selected, it needs to be the same number and they are each plotted against each other as x[i] : y[i]
  * If only one has more than 1 selected, the single one is plotted against each of the chosen rows/ columns.
  * If either has more than one row/ column selected, yerr (or xerr) is ignored.
  * If only x or only y is selected that variable is plotted as a function of its index (index is always on the x-axis).

  To remove any of x, y, xerr, yerr or misc, click on its name below the "hold" and "plot" buttons. However, all but "misc" will be automatically overwritten once 
  a new "x", "y", "z", "e" or "u" is pressed. 
  
  Buttons:

  * *hold* --> "release": to keep plotting in the same window (button has to read "release") or to open a new plot window (if button reads "hold"). If there is no current window (the current window can be chosen with the button "make active" in the corresponding window), "plot" has no effect if hold button shows "release".
  * *plot line*: to plot current selection of x, y, xerr and yerr with lines. If "z" variable is selected, "plot line" and "plot symbol" are identical, see below.
  * *plot symbol*: to plot current selection of x  and y with symbols, no line. If no key is pressed, the symbol is ".". Supported keys: .o+xv^<>123hHdp (they have their usual matplotlib marker interpretation).

 The plots support the usual matplotlib shortcuts (l, k, L,  g, G, ..., see https://matplotlib.org/3.1.1/users/navigation_toolbar.html) and the QT backend possibility to change the axes and lines. However, if the line style is changed, there are currently some inconsistences with the legend (if add_interactivity is used in conjunction).

 Line/ marker plots also have some of the functionality from add_interactivity (if it is installed), namely:

 * left click a line/ marker to toggle
 * right click a line/ marker to bring it to front
 * left click a line/ marker while arrow up to make line thicker (marker larger), arrow down to make it thinner (marker smaller).
 * left click legend while arrow left: make legend text smaller, right arrow to make it bigger
 * move legend by drag and drop

* *use idxs?* --> If the plot was performed via "plot symbol", a lasso selector is activated (only for x-y plots, not x-y-z scatter plots). If used, the indices and the values of x and y are written to the terminal and the indices can be used to restrict future plots with this button. Press button "use idxs?" in the main window before the next plot.)

* *add country lines* --> this only makes sense if the plot is a lon-lat plot. It adds country outlines and coast lines to the plot.

* *broadcast plot* & *set same data*  --> If more than one file was opened at the same time, the first window has these extra buttons. If a line or scatter plot is open (x-y or x-y-z, but not image or pcolormesh) and active, press this button to plot into it from other windows (in the other windows, one still needs to press the *hold* button to enable plotting in the same plot window. *set same data* sets the same data (same variable and same slice/ row/ column, but not same indices if chosen) to the other open windows. Of course, this only works for files that have the same type of structure. This feature is currently not supported for hdf4 files.


 ### 2D, 3D and 4D plotting

 Currently, only 2D, 3D or 4D variables can be plotted by directly clicking on them in the TreeView (or usining misc, see above. Hitting the "plot misc" button does the same to the "misc" variable as double clicking a variable).

 2D/ 3D/ 4D plots have the usual QT possibility of changing color map and limits. There is now also a *plot log* button in the plot window which converts the data to log, however the z-limits cannot be 0 or negative and might need adjusting before. x, y axis can be converted to log with "k" and "l", as usual, see matplotlib shortcuts.

 For 3D plots, you can slice along x, y or z and use the "+" and "-" buttons to go forward or backward in the variable, or write a slice number in the entry field and hit the enter key to confirm. This is in analogy to the table view of 3D variables.

 While plots of 4D variables are implemented (there are two slicers then, the upper one always has to be at a "higher" axis than the lower, default is first is 0, second is 1), it's use is discouraged since the whole 4D variable is loaded at once and the program might get really slow or even unresponsive. This is in analogy to the table view of 4D variables.

 For 2D plotting, instead of simple image plot (via double click), x and y axis can be set (with "x" and "y", see above) and then the z data can be set via "z".
 The type of plot performed depends on the dimensionalit of the variabels:
 
 * no x and y set, plot via double click on 2D variable: image plot of variable
 * x, y and z set, all 1D: A scatter plot is performed where the z value sets the colour of each scatter point
 * x, y 1D and z 2D: pcolormesh performed, if z data only fits x and y if it is transposed, it will be transposed
 * x, y and z 2D: pcolormesh, the shape has to be identical
 * x, y and z 2D, with x and y having nan values: pcolor is performed: this is considerably slower and might lead to speed issues.

 ## other functionality

 * In table view, if a row(s) or column(s) is selected and "+" is pressed, the row or column is summed and the value printed in the terminal, however there is an issue with fill values at the moment which might not be interpreted correctly.
 * Two (or more) files can be opened at the same time (passing more than one file path as command line argument, separated by a space). In that case, the window of the first file has 2 extra buttons (to the left of the "plot symbol" button), called *broadcast plot* and *set same data*: If a line or scatter plot is performed from that window, and then the "broadcast plot" button is pushed, that same plot window becomes visible by the other windows (from the other open files). If you press the "hold" button in the other open window, the plot will be carried out in that very same plot window. The *set same data* button broadcasts the path of variabels to be used. This does currently not support hdf4 files. 

 This is useful if you have 2 versions of supposedly the same data, processed slightly differently. This allows you to easily plot both together in one figure.

## Configure
The tool comes with a config.yml file which is located in the same folder as the python programs. Here, default settings for
the window sizes (main window and plot windows) can be set. 

The width of the table headers (name, dimension, etc.) can also
be specified there. By default, no color scheme is used, default settings are used. One can change Colorscheme:
  App: dark (from light) to use a dark colour scheme. The actual settings of the colors used ("white", "black", etc) can also
be changed in the configuration file. For the plotting, any of the standard matplotlib styles (see 
also https://matplotlib.org/3.2.1/gallery/style_sheets/style_sheets_reference.html) can be set, or a combination. However, it
is also possible to set your own stylesheet.mplstyle. The tools comes with an example. A complete file path to your standard
setup file can be provided here, too: Colorscheme: Plots:

See here: https://matplotlib.org/3.1.3/tutorials/introductory/customizing.html for options to put in your stylesheet.

It is possible to supply a different config.yml at start-up via the command line.
If this is desired, the path (including file name) needs to be passed as first argument (so before the first file to open)
preceded by a "-" without a space:

    python3.7 -m NetCDF4viewer -/home/your_home/path_to/config.yml path/to_your/ncfile.nc

 ## Nice to have, not implemented yet:
 I collect some ideas here for implementation. Please contact me if you have more suggestions.
 * Assigning a condition on one variable to transform it to a mask to use on other variables: This can now be done indirectly with the "use idxs?" and lasso selector.
 * Having the possibility of scaling variables with a scale factor
 * Make pcolormesh also workable for 3D variables (without the possibility of slicing, mapping decided automatically (?))
 

