# Copyright 2007 Nanorex, Inc.  See LICENSE file for details. 
"""
NE1ToolBar.py
@author: Ninad
@version:$Id$
@copyright: 2007 Nanorex, Inc.  All rights reserved.

History:
File created on 20070507. There could be more than one NE1Toolbar classes 
(subclasses of QToolBar) in future depending upon the need.

"""
__author__  = "Ninad"

from PyQt4.QtGui import *
from PyQt4.Qt import *
import sys


class NE1ToolBar(QToolBar):
    
    def paintEvent(self, evt):
        ''' reimplements the paintEvent of QToolBar'''
        #ninad20070507 : NE1ToolBar is used in Movie Prop mgr. 
        # reimplementing paint event makes sure that the 
        # unwanted toolbar border for the Movie control buttons 
        #is not rendered. No other use at the moment. 
        painter = QPainter(self)
        option = QStyleOptionToolBar()
        option.initFrom(self)
        option.backgroundColor = self.palette().color(QPalette.Background)
        option.positionWithinLine = QStyleOptionToolBar.Middle        
        option.positionOfLine = QStyleOptionToolBar.Middle 
        self.style().drawPrimitive(QStyle.PE_PanelToolBar, option, painter, self)
        
        
        
