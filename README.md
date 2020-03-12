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
    To load, simply click on the curve in the list and hit Import.  
    To delete a stored curve right click and hit delete.  
    Test Btn is well, just for testing smth, shouldn't do anything interesting for now  
    Commands tab is doing absolutely nothing as of right now.  
    Docking should work, also try closing, reopening and scaling the window.
