# QTnetCDF

Can open netCDF4, hdf5 and hdf4 files. For hdf4 files, it tries to remove the vdata that only represents sd variable attributes or dimensions.

call as 
  python3.7 -m NetCDF4viewer test.nc
  
  In the file representation that opens, a click on the triangle infront of a group (or main file level), open the group.
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
  
  If a variable is 1D, a double click will automatically plot it over its index. However, x, y, xerr and yerr can also be set. Either as a 1D variable as described above, or in from the table view (after "s" on a 0, 1, 2 or 3D variable) on which the following keys are activated: 
  
  * "x" data set as x for line plot
  * "y" data set as y for line plot
  * "e" data set as error on x for line plot
  * "u" data set as error on y for line plot
  
  In the table, multiple rows or columns can be selected for y. If so, yerr is ignored. If only x or only y is selected, that variable is plotted as a function of its index. 
  
  To remove any of x, y, xerr or yerr, click on it below the "hold" and "plot" buttons.
  Buttons:
  
  "plot" to plot current selection of x, y, xerr and yerr
  "hold" --> "release" to keep plotting in same window or to open a new. If there is no current window, "plot" has no effect if hold button shows "release". 
 
 The plots support the usual matplotlib shortcuts (l,k,L,  g,G,...) and the QT backend possibility to change the axes
 
 Line plots also have some of the functionality from add_interactivity, namely:
 
 * left click a line to toggle
 * right click a line to bring it to front
 * left click while arrow up to make line thicker, arrow down to make it thinner
 * left click while button left make legend text smaller, right click to make it bigger
 
 ### 2D and 3D plotting
 
 Currently, only 2D or 3D variables can be plotted by directly clicking on them in the TreeView.
 
 2D/ 3D plots have the usual QT possibility of changing color map and limits. There is now also a "plot log" which converts the data to log. x, y axis can be converted to log with "k" and "l", as usual. 
 
 For 3D plots, you can slice along x, y or z and use the "+" and "-" buttons to go forward or backward in the file.
 
 ## Crashes
 
 Currently, the program is a bit debil, it crashes:
 * when a group is double clicked
 * when a group is marked and "s" is clicked
 * when anything else than the first column in a tree is selected and any of the active keys is pressed (or double clicked)

 
 
 
  
  
