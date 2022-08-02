# QTnetCDF

QTnetCDF is a hdf/ netCDF4 viewer with emphasis on plotting. It is implemented in python and uses QT. 
It can open netCDF4, hdf5 and hdf4 files, MFC files and some plain text ascii files (some lucky guesses involved though). For hdf4 files, it tries to remove the vdata that only represents sd variable attributes or dimensions. The functionality for hdf4 files is somewhat limited. hdf5 compount data types are not supported (hdf5 files are read in as netCDF4).

It is tested with python3.7, python3.8 and python3.9 (on linux) and python3.8 on windows. Under windows, it works with installing the needed packages via anaconda and python3.8. Under linux, it is recommended to use the setup scripts in conjuction with pip and python3.7, python3.8 or python3.9, see Quick start below. 

For full functionality, also install https://github.com/mmf1982/add_interactivity

## Quick start for linux

You can, but you do not have to, use a virtual invironment:

Create and activate a virtual environment (only needed if you actually want to run it in the virtual environment, skip otherwise):

    python3.8 -m venv newenv_test
    source newenv_test/bin/activate

download both QTnetCDF and add_interactivity:

    git clone  https://github.com/mmf1982/QTnetCDF
    git clone  https://github.com/mmf1982/add_interactivity

inside the respecitve directories, run:

    python3.8 setup.py install

It might be that the package pyhdf needed for QTnetCDF throws an error. If so, try manually to do:

    python3.8 -m pip install pyhdf

It might also be that you have some issues with the qt5 packages, it might help to force a reinstall of the libraries via:

    sudo apt install --reinstall libqt5widgets5 libqt5gui5 libqt5dbus5 libqt5network5 libqt5core5a

You can also try to install a specific version of PyQt5. E.g. by:
    
    python3.8 -m pip install PyQt5==5.15.1    
and then redo the installation of QTnetCDF (phython3.8 setup.py install in the QTnetCDF4 directory).
    
To test your installation, download for example a h5/ hdf/ nc file from here: https://hdfeos.org/zoo/index_openNSIDC_Examples.php  

and then call as 

    python3.8 -m NetCDF4viewer whatever_is_your_test_filename.nc_or_hdf_or_h5_or_hdf4

In case you used the virtual environment, with

    deactivate
    
you can leave the virtual environment again. Of course you do not need to work within a virual environment in the frist place, but it might be the saver option if you just want to give it a try.

If, during testing, you received a warning that add_interactivity could not be found, the easiest is maybe to include a softlink inside the QTnetCDF folder to the appropriate file inside add_interactivity. However, if both packages are inside your python path, this should not be necessary.

## Basic functionality

  The file representation that opens after opening a file looks like this:
  
  ![File when opened](/images/collapsed_file.png)
    
  A click on the triangle infront of a group (or main file level), opens the group.
  
  ![Expanend group](/images/open_file.png)
  
  The following keys are activated on the tree (always on the entry in the first column, marked with the red oval above!):
  * double click on variable: plots supported data, supported are 1D, 2D, 3D and 4D variables. 2D, 3D and 4D are plotted as image, 3D with a slider and 4D with two sliders. NEW: Also 5D+ is supported. The double click opens a new type of plot/ table window, see below under 5D+ plotting. This type of plotting can also be achived for 2D, 3D and 4D, if the configuration files is changed accordingly configured (set *moreDdata/limit_for_sliceplot* to 2, 3 or 4 to allow slice plots for 2, 3 or 4 dimensions, set it to 2 to directly change to the new plot layout for data of more than 2D). If the data is 1D, the x-axis is the dimension. If, in the same or a parent group, a variable of the dimension name exists, the double-clicked variable is plotted over the dimension variable (time with units as "microseconds/ seconds/ minutes/ hours/ days since .." is supported (read via cftime)), otherwise it is plotted over the index.
  * "d" key is pressed on selected line, attribute information of that group or variable is prited in the terminal.
  * "s" key is pressed on selected variable opens it as a detachable table view ![Table view](/images/open_table.png) (for 0D, 1D, 2D, 3D and 4D variables. Higher dimensions are not supported, see however *double click* above. 4D variables with large grids might cause problems because a complete variable is read into memory). If the variable is 3D it shows slice 0 along the zeroth dimension, This can be changed by a slicer bar and "+"/ "-" buttons and an entry field. If the variable is 4D, the slice is as for 3D and additionally slice 0 along the first dimension. Note that the second slicer always needs to have a dimension at least one higher than the first. Each slicer also has an entry field where the field number can be entered directly (hit enter key to confirm). 
  * "x" data set as x for line/ scatter/ 2D- or 3D pcolormesh plot
  * "y" data set as y for line/scatter/ 2D- or 3D pcolormesh plot
  * "z" data set as z for scatter plot/ 2D- or 3D pcolormesh
  * "e" data set as error on x for line plot
  * "u" data set as error on y for line plot
  * "m" to load to misc. Data can then be combined with other data via the "/", "*", "+" and "-" buttons. Note that a+b/c will be calculated as (a+b)/c. The data set here (either as a full 1, 2, 3 or 4 D variable or a 1D or 2D subset) can either be set as x, y or z (*as x* etc) variable or directly plotted (*plot misc*) ![Misc](/images/misc.png)
  * "f" to load to flag. This variable together with "<" or ">" or "==" and a value typed in the corresponding field can be used to select only data (for x, y, z or m) for which the flag condition is fullfilled. To use this, first load a specific variable as flag (by pressing flag on a variable), then press either "<" or ">" or "==" and then type a value in the field and then press enter. Use this flag on either x,y,z or m. Note: The dimensions must agree. Only those data points for which the flag condition is fulfilled are plotted. Other values of the chosen variable (for x, y, z or m) are set to Nan. Note: This means also that the variable is converted to float for the purpose of plotting.
  
## New features in 0.0.4: 
5D+ data is now supported; activate by double click on the variable creates both a table and plot:
  ![qtnetcdf4](https://user-images.githubusercontent.com/38353016/177121672-7977ea18-2379-4960-b954-2811476cd479.png)

if the file is a netCDF4 file and has variables with the names of the dimensions of the data in question, the axis and the tables are labeled with that variable instead of with the indices. However, the plot is an image plot, not a colormesh plot. This means that independently of the spacing of the axis, each entry in the 2D matrix is a square. Labelled are the square centers, not the box edges, since edges are not provided (if the variable has the same dimension as the data, by definition the positions are the centers, not the edges). First, choose the two axis that you want to keep as variable for the selected data (indicated by red rectangle). For all but these 2 axes, values have to be chosen (values or indices in case no variables with matching dimension names are found in the same or parent groups), see blue ellipse in the image above. Note that you can either use the drop down menu or the +/- buttons to change the value. In order to display this new data selection. If you have not changed the configuration file (see below), no need to press the button "done and plot", since the update is done immediately. This behaviour can be changed in the configuration file (*moreData: update_plot_immediately: False*)
  * If data is plotted in this manner (to achieve this also for 2D, 3D and 4D, change *moreDdata/limit_for_sliceplot*  to 1, 2 or 3), data can be saved (2D data), press the "save last selection" button. Note: even if other plots/ tables are shown, only the last selection can be saved.
  * The table that is opened can be used, as other tables, to select x-, y-, z- data. (see yellow ellipses)
  
For marker (not line, so produced with button "plot symbol" from the main window) plots, there is one additional feature:
 
  * After selecting indices on marker plots, a save menu can be opened when clicking on "save selection". If a file name is entered (the original filename is suggested as starting input) and *return* is pressed, the selection (x, y, possibly z) is saved as nc file.
 
## New features in 0.0.3:
  * The just described feature to flag out data with pressing "f" on a variable and setting its limits:
    "f" to load to flag. This variable together with "<" or ">" or "==" and a value typed in the corresponding field can be used to select only data (for x, y, z or m) for which the flag condition is fullfilled. To use this, first load a specific variable as flag (by pressing flag on a variable), then press either "<" or ">" and then type a value in the field and then press enter. Use this flag on either x,y,z or m. Note: The dimensions must agree. Only those data points for which the flag condition is fulfilled are plotted. Other values of the chosen variable (for x, y, z or m) are set to Nan. Note: This means also that the variable is converted to float for the purpose of plotting. This cannot currently be combined with the lasso selector. Note that "f" is currently not activated on the table view; this means that only "full variables" can be used for flags.
  * Support for matplotlib > 3.4
  * for x-y-z plots, z now also supports 4D data (as before x and y need either to be both 1D or 2D).
  * support for MFC files and plain text ascii files.
  * if the time unit of a time variable is convertable to datetime using cftime, it is converted to datetime and displayed as such.
  * line plots can switch axes via button "swap axes" (disabled if one of the variables is "time").
## New features in 0.0.2:
  * for x-y-z plots, z now also supports 3D data (as before x and y need either to be both 1D or 2D), but no slicing in other directions is possible. If there are different axis having the same dimensions, a pop-up window requires information on which axis to slice along.
  * for x-y-z plots, nans in the x- and y- variables do not use pcolor any longer and hence there is a speed gain. However, these masked values are "transferred to the z values.
  * for x-y-z plots, if x and y have the same dimensions (instead of M+1 and N+1) than z (M,N), the grid is extended as (x[0]- diff_x[0]/2, x+diff_x/2, x[-1]+diff_x[-1]/2)
  * for double click plots, the information about dimension is shown on the axis and on the sliders.
  * pcolormesh plots can now be overlayed with scatter plots or 1D line plots

## New features added prior to 0.0.2:
  * More than one file can be opened and plots can be made in a common window, this adds two extra buttons to the window of the first file: ![Extra buttons](/images/extra_button.png), one to make the plot window available (*broadcast plot*), the other, *set same data*, see following point.
  * If the same variables (same path to the variables) should be plotted from different files, they only need to be set in the first file (not supported for hdf4) and can then be set for all other windows with the *set same data* button. This is for example usefull if one wants to plot several satellite overpass files in a single plot.
  * A simple country and coast line plot can be overlayed on longitude-latitude plots, button *add country lines* above. This is possible to pcolormesh plots (so if x, y and z are all 2D or if x and y are 1D but z is 2D) and also to scatter plots (so if x, y and z are all 1D):
  
   scatter                   |  pcolormesh
  ---------------------------|-------------------------
  ![Scatter](/images/scatter_countries.png) | ![Pcolormesh](/images/pcolormesh_country.png)
  
  (note the slider for the pixel size in the scatter plot)
  * variables can be multiplied, divided, added and subtracted before plotting, see "m" above. 
  * the scrolling wheel can be used to zoom in and out of a plot.
  * If a plot was made with button *plot symbol*, the lasso selector is active:
  ![Lasso Selector](/images/choose.png) 
  
  Together with button *use idxs?* which turns into *using idxs only*, this can be used to restrict the indices in following plots, like here were values for x, y and z has been chosen:
  
  ![Choice](/images/choice.png)
  
  The result is a scatter plot only containing indices that were chosen with the lasso selector, in the displayed case, for which the validity is 100:  
  ![Scatter Plot](/images/chosen.png). 
  
  Also note the slider which sets the size of the dots in scatter plots. 
  * using misc, it is now possible to add/ subtract/ divide/ multiply a constant factor of a variable: enter a float in the entry field marked red below, choose an operator and then mark a variable and press *m*, as described above under basic functionality. It is also possible to first choose the variable and the operator. In either case, press enter after entering the float in the input field. ![Constant factor](/images/input_field.png) 
  
## bug fixes (prior to 0.0.3):
* undocked table takes color scheme specified for main window
* if more than two files are opened at the same time, the title of each window is the name of the respective file
* windows with x-y-z plots get the name of the z value as title
* behaviour of x-y plot if only x variable specified changed: Now x-variable is plotted on x and index on y. In order to get variable plotted as y, set variable as y and leave x empty.
* add updated interactive legend after chaning line/ marker style/ color/ size with matplotlib gui.
* after marking a variable (<=2D), "c" copies the data
* a variable loaded into misc, can be averaged (mean or median, use respective button) along a dimension which needs to be specified in the input field. First, load the data into misc, then press "median" or "mean" button, then type the dimension and press enter. 
* double click on the group opens the dimensions as variables in the table and dumps the content (dimension names, variable names, etc.) to the console.
* In a line or symbol plot, right click on a line copies the line and middle click (in a different plotting window) pasts that plot. This also works for windows from different files as long as the files were opened at the same time via the command line.

## Plotting

  The main thing about this tool is the plotting, you can do line/ marker plots, image, pcolormesh or scatter plots. Data is supported up to 4 dimensions.

  ### 1D plotting

  If a variable is 1D, a double click will automatically plot it over its index. However, x, y, xerr and yerr can also be set. Either as a 1D variable as described above, or from the table view (after "s" on a 1, 2, 3 or 4D variable) on which the following keys are activated, note: "f" is currently not activated: 

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

  To remove any of x, y, xerr, yerr or misc, click on its name (below the *hold* and *plot* buttons). However, all but *misc* will be automatically overwritten once 
  a new *x*, *y*, *z*, *e* or *u* is pressed. 
  
  Buttons:

  * *hold* --> *release*: to keep plotting in the same window (button has to read "release") or to open a new plot window (if button reads *hold*). If there is no current window (the current window can be chosen with the button *make active* in the corresponding window), *plot* has no effect if hold button shows *release*.
  * *plot line*: to plot current selection of x, y, xerr and yerr with lines. If a *z* variable is selected, *plot line* and *plot symbol* are identical, see below.
  * *plot symbol*: to plot current selection of x  and y with symbols, no line. If no key is pressed, the symbol is ".". Supported keys: .o+xv^<>123hHdp (they have their usual matplotlib marker interpretation).

 The plots support the usual matplotlib shortcuts (l, k, L,  g, G, ..., see https://matplotlib.org/3.1.1/users/navigation_toolbar.html) and the QT backend possibility to change the axes and lines. If the line/ marker style is changed via the normal QT backend GUI, a new interactive legend is created automatically (if add_interactivity package is installed, too).

 Line/ marker plots also have some of the functionality from add_interactivity (if it is installed https://github.com/mmf1982/add_interactivity), namely:

 * left click a line/ marker in the legend to toggle
 * right click a line/ marker in the legend to bring it to front
 * left click a line/ marker in the legend while arrow up key pressed: make line thicker (marker larger), arrow down key pressed: make it thinner (marker smaller).
 * left click legend while arrow left key pressed: make legend text smaller, right arrow key pressed: to make it bigger
 * move legend by drag and drop
 * right click on a line/ marker (not in legend): copy
 * middle click in a plot: paste the copied line

* *use idxs?* --> If the plot was performed via "plot symbol", a lasso selector is activated (only for x-y plots, not x-y-z scatter plots). If used, the indices and the values of x and y are written to the terminal and the indices can be used to restrict future plots with this button. Press button "use idxs?" in the main window before the next plot.)

* *add country lines* --> this only makes sense if the plot is a lon-lat plot. It adds country outlines and coast lines to the plot.

* *broadcast plot* & *set same data*  --> If more than one file was opened at the same time, the first window has these extra buttons. If a line or scatter plot is open (x-y or x-y-z, but not image or pcolormesh) and active, press this button to plot into it from other windows (in the other windows, one still needs to press the *hold* button to enable plotting in the same plot window. *set same data* sets the same data (same variable and same slice/ row/ column, but not same indices if chosen) to the other open windows. Of course, this only works for files that have the same type of structure. This feature is currently not supported for hdf4 files.


 ### 2D, 3D and 4D plotting

 Currently, only 2D, 3D or 4D variables can be plotted by directly clicking on them in the TreeView (or usining misc, see above. Hitting the "plot misc" button does the same to the "misc" variable as double clicking a variable).

 2D/ 3D/ 4D plots have the usual QT possibility of changing color map and limits. There is now also a *plot log* button in the plot window which converts the data to log, however the z-limits cannot be 0 or negative and might need adjusting before. x, y axis can be converted to log with "k" and "l", as usual, see matplotlib shortcuts.

 For 3D plots, you can slice along x, y or z and use the "+" and "-" buttons to go forward or backward in the variable, or write a slice number in the entry field and hit the enter key to confirm. This is in analogy to the table view of 3D variables.

 While plots of 4D variables are implemented (there are two slicers then, the upper one always has to be at a "higher" axis than the lower, default is first is 0, second is 1), it's use is discouraged since the whole 4D variable is loaded at once and the program might get really slow or even unresponsive. This is in analogy to the table view of 4D variables.

 For 2D and 3D plotting, instead of simple image plot (via double click), x and y axis can be set (with "x" and "y", see above) and then the z data can be set via "z".
 The type of plot performed depends on the dimensionalit of the variabels:
 
 * no x and y set, plot via double click on 2D variable: image plot of variable
 * x, y and z set, all 1D: A scatter plot is performed where the z value sets the colour of each scatter point.
 * x, y 1D and z 2D: pcolormesh performed, if z data only fits x and y if it is transposed, it will be transposed, a warning is displayed.
 * x, y and z 2D: pcolormesh, the shape has to be identical (or x- y- grid each one longer, as to represent really the boundaries)
 * x, y and z 2D, with x and y having nan values: a crude fix is applied that "moves" the nans to the z-data instead. However, since each x-y center coordinate is translated into four boundaries (above, below, left, right), and one missing x-y point means 4 missing boundaries, more nans are introduced in the field. However, x- and y- coordinates should not contain nans in the first place.
 * x, y 1D or both 2D and z 3D: pcolormesh with slicing along the 3rd dimension, plus/ minus buttons and an entry field to change the slice are present.

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

    python3.8 -m NetCDF4viewer -/home/your_home/path_to/config.yml path/to_your/ncfile.nc

 ## Nice to have, not implemented yet:
 I collect some ideas here for implementation. Please contact me if you have more suggestions.
  * incldue a "search" field to find variables in all groups matching a partial name
  * having the option to use "long names" instead of variable names for e.g. plots.
  * having a button to change several things from the configuration file "on the fly": --> For testing, this is implemented in the "Menu" bar now:
![image](https://user-images.githubusercontent.com/38353016/177938729-833f6394-76f1-4e83-a677-c8ba2def0de2.png)


    - country outline color and line thickness      --> can be changed, need to plot country lines again in order to take effect
    - whether or not to open new plot/ table when settings change in the new 5D+ support  --> can be changed, takes effect with next plot
    - whether or not to plot immediately or only on "done and plot" in the new 5D+ support  --> can be changed, takes effect with newxt plot
    - whether to use the new table/ plot window or the original for 2D -- 4D variables 
    - turn off "save as" pop-up after selecting indices
 
## Implementations done on request:
 * Add possibility to add country outlines.
 * Assigning a condition on one variable to transform it to a mask to use on other variables: This can now be done indirectly with the "use idxs?" and lasso selector. This is now explicitly implemented in version 0.0.3 (with "f")
 * Make pcolormesh also workable for 4D variables (without the possibility of slicing in the two set axis, mapping decided automatically for those as already done for 3D. This might be useful for map data with height and time dimension.) this is now implemented in version 0.0.3
 * Add support for 5D+. This is currently only done for netCDF and, with the additional requirement to have each a variable for each dimension name of the 5D + variable. Instead of slicing with a slicer, x-axis and y-axis are set via a drop-down menu. The other 5D+x -2 variables have to be set via a drop-down menu for each variable. 
