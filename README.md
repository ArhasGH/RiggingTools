Create a new folder called `RiggingTools` in your maya scripts folder for your current version e.g.:
`C:\Users\USER\Documents\maya\2020\scripts\RiggingTools`

Put the `Script` folder you downloaded in there so you end up with this
`C:\Users\USER\Documents\maya\2020\scripts\RiggingTools\Scripts`

The script *should* be compatible with maya 2017+

To run the script run this from the script editor or shelf
```python
from RiggingTools.Source import RiggingToolsUI
reload(RiggingToolsUI)
ui = RiggingToolsUI.show_ui()
```
