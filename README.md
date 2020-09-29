# QTnetCDF

Can open netCDF4, hdf5 and hdf4 files. For hdf4 files, it tries to remove the vdata that only represents sd variable attributes or dimensions.

Download for example a h5/ hdf/ nc file from here: https://hdfeos.org/zoo/index_openNSIDC_Examples.php  

call as 

    python3.7 -m NetCDF4viewer whatever_is_your_test_filename.nc_or_hdf_or_h5_or_hdf4
  
  In the file representation that opens, a click on the triangle infront of a group (or main file level), opens the group.
  The following keys are activated on the tree:
  * double click on variable: plot Supported are 1D, 2D and 3D variables.
  * "d" key is pressed on selected line, attribute information of that group or variable is prited.
  * "s" key is pressed on selected variable opens it as a detachable table view (for 0D, 1D, 2D and 3D variables. Higher dimensions are not supported). Note: if it is a group, the program currently crashes. If the variable is 3D it shows a slice along the first dimension, This can be changed by a slicer bar and "+"/ "-" buttons. 
  * "x" data set as x for line plot
  * "y" data set as y for line plot
  * "e" data set as error on x for line plot
  * "u" data set as error on y for line plot
  
  ## Plotting
  
  The main thing about this tool is the plotting, you can do line plots or image plots.
  
  ### 1D plotting
  
  If a variable is 1D, a double click will automatically plot it over its index. However, x, y, xerr and yerr can also be set. Either as a 1D variable as described above, or from the table view (after "s" on a 0, 1, 2 or 3D variable) on which the following keys are activated: 
  
  * "x" data set as x for line plot
  * "y" data set as y for line plot
  * "e" data set as error on x for line plot
  * "u" data set as error on y for line plot
  
  In the table, multiple rows or columns can be selected for y or x (but not both). If so, yerr (or xerr) is ignored. If only x or only y is selected, that variable is plotted as a function of its index. 
  
  To remove any of x, y, xerr or yerr, click on its name below the "hold" and "plot" buttons.
  Buttons:
  
  * "hold" --> "release" to keep plotting in same window or to open a new. If there is no current window, "plot" has no effect if hold button shows "release". 
  * "plot line" to plot current selection of x, y, xerr and yerr
  * "plot symbol" to plot current selection of x  and y with symbols, no line. If no key is pressed, the symbol is ".". Supported keys: .o+xv^<>123hHdp 
 
 The plots support the usual matplotlib shortcuts (l,k,L,  g,G,...) and the QT backend possibility to change the axes. However, if the line style is changed, there are currently some inconsistences with the legend (if add_interactivity is used in conjunction). 
 
 Line plots also have some of the functionality from add_interactivity (if it is installed), namely:
 
 * left click a line to toggle
 * right click a line to bring it to front
 * left click a line while arrow up to make line thicker, arrow down to make it thinner
 * left click legend while arrow left: make legend text smaller, right arrow to make it bigger
 
 ### 2D and 3D plotting
 
 Currently, only 2D, 3D or 4D variables can be plotted by directly clicking on them in the TreeView.
 
 2D/ 3D/ 4D plots have the usual QT possibility of changing color map and limits. There is now also a "plot log" which converts the data to log. x, y axis can be converted to log with "k" and "l", as usual. 
 
 For 3D plots, you can slice along x, y or z and use the "+" and "-" buttons to go forward or backward in the file.
 
 While 4D plots are implemented (there are two slicers now, the upper one always have to be at a "higher" axis than the upper, default is first is 0, second is 1), it's use is discouraged since the whole 4D variable is loaded at once and the
 program might get really slow or even unresponsive. 
 
 For 2D plotting, instead of simple image plot (via double click), x and y axis can be set (with "x" and "y", see above) and then the z data can be set via "z".
 Here, x and y can be 1 or two dimensional. If they are 1 dimensional and do not fit the data, the z data is transposed to
 try if the fit that way. A warning is displayed. You need to press either of the two "plot" buttons.
 
 The 2D plotting with x, y and z also supports all 3 variables as 1D. In this case, a scatter plot is attempted. 
 
 # Crashes
 
 Currently, the program might be a bit debil, it crashes:
 * currently no know crashes, please report and send the example file.

 # other functionality

 * In table view, if a row(s) or column(s) is selected and "+" is pressed, the row or column is summed and the value printed in the terminal

# Configure
The tool comes with a config.yml file which is located in the same folder as the python programs. Here, default settings for
the window sizes (main window and plot windows) can be set. 

The width of the table headers (name, dimension, etc.) can also
be specified there. By default, no color scheme is used, default settings are used. One can change Colorscheme:
  App: dark (from light) to use a dark colour scheme. The actual settings of the colors used ("white", "black", etc) can also
be changed in the configuration file. For the plotting, any of the standard matplotlib styles (see 
also https://matplotlib.org/3.2.1/gallery/style_sheets/style_sheets_reference.html) can be set, or a combination. However, it
is also possible to set your own stylesheet.mplstyle. The tools comes with an example. A complete file path to your standard
setup file can be provided here. 

It is possible to supply a different config.yml at start-up via the command line:
If this is desired, the path (including file name) needs to be passed as first argument (so before the first file to open)
preceded by a "-" without a space:

    python3.7 -m NetCDF4viewer -/home/your_home/path_to/config.yml path/to_your/ncfile.nc
 
 
 # Nice to have, not implemented yet:
 I collect some ideas here for implementation. Please contact me if you have more suggestions.
 * Doing simple manipulations on the data before plotting, such ass adding/ subtracting...
  
