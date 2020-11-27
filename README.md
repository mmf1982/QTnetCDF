# QTnetCDF

Can open netCDF4, hdf5 and hdf4 files. For hdf4 files, it tries to remove the vdata that only represents sd variable attributes or dimensions.

Download for example a h5/ hdf/ nc file from here: https://hdfeos.org/zoo/index_openNSIDC_Examples.php  

call as 

    python3.7 -m NetCDF4viewer whatever_is_your_test_filename.nc_or_hdf_or_h5_or_hdf4

  In the file representation that opens, a click on the triangle infront of a group (or main file level), opens the group.
  The following keys are activated on the tree:
  * double click on variable: plot Supported are 1D, 2D and 3D variables.
  * "d" key is pressed on selected line, attribute information of that group or variable is prited.
  * "s" key is pressed on selected variable opens it as a detachable table view (for 0D, 1D, 2D, 3D and 4D variables. Higher dimensions are not supported. 4D variables with large grids might cause problems because a complete variable is read into memory). If the variable is 3D it shows slice 0 along the zeroth dimension, This can be changed by a slicer bar and "+"/ "-" buttons. If the variable is 4D, the slice is as for 3D and additionally slice 0 along the first dimension. Note that the second slicer always needs have a dimension at least one higher than the first. Each slicer also has an entry field where the field number can be entered directly (hit enter key to confirm). 
  * "x" data set as x for line plot
  * "y" data set as y for line plot
  * "e" data set as error on x for line plot
  * "u" data set as error on y for line plot
  * "m" to loaded to misc. Data can then be combined with other data via the "/", "*", "+" and "-" buttons. Note that a+b/c will be calculated as (a+b)/c. The data set here (either as a full 1, 2, 3 or 4 D variable or a 1D or 2D subset) can either be set as x, y or z (as x etc) variable or directly plotted (plot misc) 

  ## Plotting

  The main thing about this tool is the plotting, you can do line/ marker plots, image or pcolormesh or scatter plots.

  ### 1D plotting

  If a variable is 1D, a double click will automatically plot it over its index. However, x, y, xerr and yerr can also be set. Either as a 1D variable as described above, or from the table view (after "s" on a 0, 1, 2, 3 or 4D variable) on which the following keys are activated: 

  * "x" data set as x for line plot
  * "y" data set as y for line plot
  * "e" data set as error on x for line plot
  * "u" data set as error on y for line plot

  In the table, multiple rows or columns can be selected for y or x (and also for both). If for both of them more than one are selected, it
  needs to be the same number. If only one has more than 1 selected, the other one is plotted against this single one for each of the chosen
  rows/ columns. If either has more than one row/ column selected, yerr (or xerr) is ignored. If only x or only y is selected,
  that variable is plotted as a function of its index (index is always on the x-axis).

  To remove any of x, y, xerr, yerr or misc, click on its name below the "hold" and "plot" buttons. However, all but "misc" will be automatically overwritten once a new "x", "y", "z", "e" or "u" is pressed. 
  
  Buttons:

  * "hold" --> "release" to keep plotting in same window or to open a new. If there is no current window (
  the current value can be chosen with the button "make active" in the corresponding window), "plot" has no effect if hold button shows "release".
  * "plot line" to plot current selection of x, y, xerr and yerr with lines.
  * "plot symbol" to plot current selection of x  and y with symbols, no line. If no key is pressed, the symbol is ".". Supported keys: .o+xv^<>123hHdp (they have their usual matplotlib marker interpretation).

 The plots support the usual matplotlib shortcuts (l,k,L,  g,G,...) and the QT backend possibility to change the axes and lines. However, if the line style is changed, there are currently some inconsistences with the legend (if add_interactivity is used in conjunction).

 Line/ marker plots also have some of the functionality from add_interactivity (if it is installed), namely:

 * left click a line/ marker to toggle
 * right click a line/ marker to bring it to front
 * left click a line/ marker while arrow up to make line thicker (marker larger), arrow down to make it thinner (marker smaller).
 * left click legend while arrow left: make legend text smaller, right arrow to make it bigger
 * move legend by drag and drop

* "use idxs?" --> If the plot was performed via "plot symbol", a lasso selector is activated. If used, the indices and the values of x 
and y are written to the terminal and the indices can be used to restrict future plots with this button. Press button "use idxs?" in the main window before
the next plot.)

* "add country lines" --> this only makes sense if the plot is a lon-lat plot. It adds country outlines and coast lines to the plot.

* "broadcast plot"  --> If more than one file was opened at the same time, the first window has this extra button. If a line plot is open and active, press this button to plot into it from other windows.


 ### 2D, 3D and 4D plotting

 Currently, only 2D, 3D or 4D variables can be plotted by directly clicking on them in the TreeView (or usining misc, see above. Hitting the "plot misc" button does the same to the "misc" variable as double clicking a variable).

 2D/ 3D/ 4D plots have the usual QT possibility of changing color map and limits. There is now also a "plot log" which converts the data to log. x, y axis can be converted to log with "k" and "l", as usual.

 For 3D plots, you can slice along x, y or z and use the "+" and "-" buttons to go forward or backward in the variable, or write a slice number in the entry field and hit the enter key to confirm.

 While 4D plots are implemented (there are two slicers now, the upper one always has to be at a "higher" axis than the lower, default is first is 0, second is 1), it's use is discouraged since the whole 4D variable is loaded at once and the program might get really slow or even unresponsive.

 For 2D plotting, instead of simple image plot (via double click), x and y axis can be set (with "x" and "y", see above) and then the z data can be set via "z".
 Here, x and y can be 1 or 2 dimensional (but they have to be consistent, i.e. if x is 1D, y has to be 1D, too). If they are 1 dimensional and do not fit the data, the z data is transposed to
 try if the data fits that way. A warning is displayed. You need to press either of the two "plot" buttons, there is no difference between them for 2D plots.

 The 2D plotting with x, y and z also supports all 3 variables as 1D. In this case, a scatter plot is attempted.

 # Crashes

 Currently, the program might be a bit debil, it crashes:
 * currently no know crashes, please report and send the example file.

 # other functionality

 * In table view, if a row(s) or column(s) is selected and "+" is pressed, the row or column is summed and the value printed in the terminal
 * Two (or more) files can be opened at the same time (passing more than one file path as command line argument, separated by a space). In that case, the window of the first file has an extra button (to the left of the "plot symbol" button), called "broadcast plot". If a 1D plot is performed from that window, and then the "broadcast plot" button is pushed, that same plot window becomes visible by the other windows (from the other open files). If you press the "hold" button in the other open window, the plot will be carried out in that very same plot window. 

 This is useful if you have 2 versions of supposedly the same data, processed slightly differently. This allows you to easily plot both together in one figure.

# Configure
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


 # Nice to have, not implemented yet:
 I collect some ideas here for implementation. Please contact me if you have more suggestions.
 * Assigning a condition on one variable to transform it to a mask to use on other variables: This can now be done indirectly with the "use idxs?" and lasso selector.
 * Having the possibility of scaling variables with a scale factor
 * Make pcolormesh also workable for 3D variables (without the possibility of slicing, mapping decided automatically (?))
 

