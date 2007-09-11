# Copyright 2004-2007 Nanorex, Inc.  See LICENSE file for details. 
"""
icon_utilities.py - helper functions for finding icon and pixmap files
in standard places, and caching them, and handling errors when they're
not found.

$Id$

History: developed by several authors; moved out of Utility.py
by bruce 070831.

WARNING: most code still imports these functions from Utility.py.
This should be cleaned up when practical.

TODO: most of the code in these functions could probably be merged.
"""

import os, sys
import platform
from PyQt4 import QtGui
import Initialize

# This is the subdirectory component "ui" at the end of "cad/src/ui".
UI_SUBDIRECTORY_COMPONENT = "ui"

# these private global dictionaries are used to cache
# pixmaps and icons returned by some of the functions herein
_pixmaps = {}
_icons = {}

_iconprefix = "."
    # This will be set by initialize() to the pathname of the directory that
    # contains ui/... icon files, for private use. Note that if the
    # ALTERNATE_CAD_SRC_PATH feature is being used, this will be set to
    # a different value than otherwise (new feature, bruce 070831).

def initialize():
    if (Initialize.startInitialization(__name__)):
        return
    
    # initialization code
    global _iconprefix
    _iconprefix = os.path.dirname(os.path.abspath(sys.argv[0]))
    _iconprefix = os.sep.join(_iconprefix.split(os.sep)[:-1] + ["src"])

    import __main__
    if __main__._USE_ALTERNATE_CAD_SRC_PATH: #bruce 070831
        new_iconprefix = __main__._ALTERNATE_CAD_SRC_PATH
        print "ALTERNATE_CAD_SRC_PATH: setting _iconprefix to %r rather than %r" % \
              ( new_iconprefix, _iconprefix )
        _iconprefix = new_iconprefix

    Initialize.endInitialization(__name__)
    return

#initialize() ### TODO: call this from another file, not from first import of this one

def image_directory(): #bruce 070604
    """Return the full pathname of the directory in which the image files
    (mostly icons) with names like ui/<subdir>/<file> exist.
       Note: As of 070604, for developers this path ends with cad/src
    and is also the main source directory, but in built releases it
    might be something different and might be platform-dependent or even
    build-system-dependent.
    """
    global _iconprefix
    return _iconprefix

def geticon(name):
    """
    Return the QIcon for the given image path name. 
    @param name: The image path name provided by the user. the path should start 
           with 'ui/' directory inside the src directory.
    @type  name: str
    
    @return: QIcon object for the given image path.
    @rtype:  QIcon object. 
    """
  
    root, ext = os.path.splitext(name)
    if not ext:
        name = name + '.png'
    
    iconPath = os.path.join(_iconprefix, name)
    iconPath = os.path.normpath(iconPath)      
    
    if not os.path.exists(iconPath):
        if platform.atom_debug:
            print "icon path %s doesn't exist." % (iconPath,)
    
    # Always set the icon with the 'iconPath'. Don't set it as an empty string 
    # like done in getPixmap. This is done on purpose. Right now there is an 
    # apparent bug in Qt in the text alignment for a push button with style sheet. 
    # @see L{PM_GroupBox._getTitleButton} which sets a non-existant 
    # 'Ghost Icon' for this button using 'geticon method'
    #   By setting such  icon, the button text left-aligns! If you create an icon 
    # with iconPath = empty string (when the user supplied path doesn't exist) 
    # the text in that title button center-aligns. So lets just always use the 
    # 'iconPath' even when the path doesn't exist. -- ninad 2007-08-22
    
    icon = QtGui.QIcon(iconPath)
            
    return icon

def getpixmap(name):
    """
    Return the QPixmap for the given image path name. 
    @param name: The image path name provided by the user. the path should start 
           with 'ui/' directory inside the src directory.
    @type  name: str
    
    @return: QPixmap object for the given image path. (could return a Null icon)
    @rtype:  QPixmap object.
    """
    root, ext = os.path.splitext(name)
    if not ext:
        name = name + '.png'
        
    pixmapPath = os.path.join(_iconprefix, name)
    pixmapPath = os.path.normpath(pixmapPath)
    
    if os.path.exists(pixmapPath):
        pixmap = QtGui.QPixmap(pixmapPath)        
    else:
        # return a null pixmap. Client code should do the necessary check 
        # before setting the icon. 
        # @see: L{PM_GroupBox.addPmWidget} for an example on how this is done
        pixmap = QtGui.QPixmap('')
        if platform.atom_debug:
            # This could be a common case. As the client uses getpixmap function 
            # to see if a pixmap exists. So if its obscuring other debug messages,
            # the following print statement can be removed
            print "pixmap path %s doesn't exist." %(pixmapPath)
        
    return pixmap

def imagename_to_pixmap(imagename): #bruce 050108
    """
    Given the basename of a file in our cad/src/ui directory,
    return a QPixmap created from that file. Cache these
    (in our own Python directory, not Qt's QPixmapCache)
    so that at most one QPixmap is made from each file.
    If the imagename does not exist, a Null pixmap is returned.
    """
    try:
        return _pixmaps[imagename]
    except KeyError:
        pixmappath = os.path.join( _iconprefix, UI_SUBDIRECTORY_COMPONENT,
                                   imagename)
        if not os.path.exists(pixmappath):
            print 'pixmap does not exist: ' + pixmappath
            import traceback
            traceback.print_stack(file = sys.stdout)
        pixmap = QtGui.QPixmap(pixmappath)
            # missing file prints a warning but doesn't cause an exception,
            # just makes a null pixmap [confirmed by mark 060202]
        _pixmaps[imagename] = pixmap
        return pixmap
    pass

def imagename_to_icon(imagename):
    """
    Given the basename of a file in our cad/src/ui directory,
    return a QIcon created from that file. Cache these
    (in our own Python directory)
    so that at most one QIcon is made from each file.
    If the imagename does not exist, a Null QIcon is returned.
    """
    try:
        return _icons[imagename]
    except KeyError:
        iconpath = os.path.join( _iconprefix, UI_SUBDIRECTORY_COMPONENT,
                                 imagename)
        if not os.path.exists(iconpath):
            print 'icon does not exist: ' + iconpath
        icon = QtGui.QIcon(iconpath)
        _icons[imagename] = icon
        return icon
    pass

# end
