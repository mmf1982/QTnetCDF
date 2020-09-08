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
 
 Currently, only 2D or 3D variables can be plotted by directly clicking on them in the TreeView.
 
 2D/ 3D plots have the usual QT possibility of changing color map and limits. There is now also a "plot log" which converts the data to log. x, y axis can be converted to log with "k" and "l", as usual. 
 
 For 3D plots, you can slice along x, y or z and use the "+" and "-" buttons to go forward or backward in the file.
 
 ## Crashes
 
 Currently, the program is a bit debil, it crashes:
 * currently no know crashes, please report and send the example file.

 ## other functionality

 * In table view, if a row(s) or column(s) is selected and "+" is pressed, the row or column is summed and the value printed in the terminal


 
 
 
  
  
