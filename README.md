Create a new folder called `RiggingTools` in your maya scripts folder for your current version e.g.:
`C:\Users\USER\Documents\maya\2020\scripts\RiggingTools`

Put the `Script` folder you downloaded in there so you end up with this
`C:\Users\USER\Documents\maya\2020\scripts\RiggingTools\Scripts`

Then put the `__init__.py` file in the same folder. You can also just create it yourself, 
it's empty but needed for python

The script *should* be compatible with maya 2017+

To run the script run this from the script editor or shelf
```python
from RiggingTools.Source import RiggingToolsUI
reload(RiggingToolsUI)
ui = RiggingToolsUI.show_ui()
```

Current State:

    Importing and Exporting nurbs curves;  
    Create a Nurbs Curve and click Save.  
    To load, simply click on the curve in the list and hit Create.  
    Names for the created control should work as well. Should also be self explanatory
    You can set the mode via the dropdown menu, to automatically have the created curved be grouped
    To delete a stored curve right click and hit delete.  
    To rename, right click and hit rename, a name has to be provided.
    Commands and Options tab are doing absolutely nothing as of right now.  
    Docking should work, also try closing, reopening and scaling the window.
    You can zoom by pressing +/- while the list of Controls is in focus, don't ask why, I was just bored
