# STYLE ***************************************************************************
# content  : assignment (Python Advanced)
# -----
# Date:
# created  : 2025-03-07
# modified : 2025-05-04
# -----
# author   : Alexander Richter
# email    : contact@alexanderrichtertd.com
#**********************************************************************************

def set_color(ctrlList=None, color=None):
    """
    Overrides color if override color value exists in color map dictionary
    """    
    # Dictionary to hold values for color overrides
    color_map = {
        1 : 4,
        2 : 13,
        3 : 25,
        4 : 17,
        5 : 17,
        6 : 15,
        7 : 6,
        8 : 16
    }

    override_color = color_map.get(color)

    for ctrlName in ctrlList:
        try:
            mc.setAttr(ctrlName + 'Shape.overrideEnabled', 1)
        except:
            pass
        
        if override_color:
            mc.setAttr(ctrlName + 'Shape.overrideColor', override_color)

# EXAMPLE
# set_color(['circle','circle1'], 8)
