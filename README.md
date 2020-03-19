Create a new folder called `RiggingTools` in your maya scripts folder for your current version e.g.:
`C:\Users\USER\Documents\maya\2020\scripts\RiggingTools`

Put the `Source` folder you downloaded in there so you end up with this
`C:\Users\USER\Documents\maya\2020\scripts\RiggingTools\Source`

Then put the `__init__.py` and `config.ini` in the same folder.

The script *should* be compatible with maya 2017+

To run the script run this from the script editor or shelf
```python
from RiggingTools.Source import main
main.show_ui()
```

Current State:

    Importing and Exporting nurbs curves;  
    Create a Nurbs Curve and click Save.  
    To load, simply click on the curve in the list and hit Create.  
    Names for the created control should work as well. Should also be self explanatory
    You can set the mode via the dropdown menu, to automatically have the created curved be grouped
    To delete a stored curve right click and hit delete.  
    To rename, right click and hit rename, a name has to be provided.
    Commands tab is doing absolutely nothing as of right now.  
    Docking should work, also try closing, reopening and scaling the window.
    You can zoom by pressing +/- while the list of Controls is in focus, don't ask why, I was just bored
    Some suffix options are available in the options tab, but you need to save them before they're applied
    
