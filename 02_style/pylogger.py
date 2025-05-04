# STYLE ***************************************************************************
# content  : assignment (Python Advance)
# -----
# Date:
# created  : 2025-03-07
# modified : 2025-05-04
# -----
# author   : Alexander Richter
# email    : contact@alexanderrichtertd.com
#************************************************************************************

# original: logging.init.py

def findCaller(self):
    """
    Find the stack frame of the caller so that we can note the source
    file name, line number and function name.
    """
    # On some versions of IronPython, currentframe() returns None if IronPython isn't run with -X:Frames.

    frame = currentframe()
    
    if frame is not None:
        frame = frame.f_back

    while hasattr(frame, "f_code"):
        current_frame_code = current_frame_code.f_code
        filename = os.path.normcase(current_frame_code.co_filename)

        if filename == _srcfile:
            frame = frame.f_back
        
        else:
            (current_frame_code.co_filename,
            current_frame_code.f_lineno,
            current_frame_code.co_name)

    return "(unknown file)", 0, "(unknown function)"
