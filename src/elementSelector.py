# Copyright (c) 2004 Nanorex, Inc.  All rights reserved.
'''
elementSelector.py

$Id$
'''

from ElementSelectorDialog import *
from elementpixmaps import *
from fileIO import readElementColors, saveElementColors
import elements 
from constants import globalParms
from ThumbView import *
import drawer

########################################################
# Declaring tuples

elementAMU = { 1 : "1.008", 2 : "4.003", 
                        5 : "10.811", 6 : "12.011" , 7 : "14.007", 8 : "15.999", 9 : "18.998", 10: "20.178",
                        13 : "26.982", 14 : "28.086", 15 : "30.974", 16 : "32.066", 17 : "35.453", 18 : "39.948",
                        32 : "72.610", 33 : "74.922", 34 : "78.960", 35 : "79.904", 36 : "83.800",
                        51 : "121.760", 52 : "127.600", 53 : "126.904", 54 : "131.290" }

########################################################

class elementSelector(ElementSelectorDialog):
    def __init__(self, win):
        ElementSelectorDialog.__init__(self, win)
        self.w = win
        self.fileName = None
        self.isElementModified = False
        self.isFileSaved = False
        self.elemTable = elements.elemprefs().deepCopy(elements.elemtables[3])
        
        self.elementGroupBox.setColumnLayout(5, Qt.Vertical)
        
        buttons = [(self.pushButton1, 1), (self.pushButton2, 2), (self.pushButton5, 5), (self.pushButton6, 6), (self.pushButton7,7), (self.pushButton8, 8), (self.pushButton9, 9), (self.pushButton10, 10), (self.pushButton13, 13), (self.pushButton14, 14), (self.pushButton15, 15), (self.pushButton16, 16), (self.pushButton17, 17), (self.pushButton18, 18), (self.pushButton32,32), (self.pushButton33, 33), (self.pushButton34, 34), (self.pushButton35, 35), (self.pushButton36, 36), (self.pushButton51, 51), (self.pushButton52, 52), (self.pushButton53, 53), (self.pushButton54, 54)]
        
        self.buttonGroup = QButtonGroup(self)
        self.buttonGroup.setExclusive(True)
        self.buttonGroup.hide()
        for button in buttons: self.buttonGroup.insert(button[0], button[1])
        self.connect(self.buttonGroup, SIGNAL("clicked(int)"), self.setElementInfo)
         
        self.elemGLPane = ElementView(self.elementFrame, "element glPane", self.w.glpane)
        # Put the GL widget inside the frame
        flayout = QVBoxLayout(self.elementFrame,1,1,'flayout')
        flayout.addWidget(self.elemGLPane,1)

    def disConnectChangingControls(self):
        self.disconnect(self.redSlider,SIGNAL("valueChanged(int)"),self.changeSpinRed)
        self.disconnect(self.redSpinBox,SIGNAL("valueChanged(int)"),self.changeSliderRed)
        self.disconnect(self.blueSlider,SIGNAL("valueChanged(int)"),self.changeSpinBlue)
        self.disconnect(self.blueSpinBox,SIGNAL("valueChanged(int)"),self.changeSliderBlue)
        self.disconnect(self.greenSlider,SIGNAL("valueChanged(int)"),self.changeSpinGreen)
        self.disconnect(self.greenSpinBox,SIGNAL("valueChanged(int)"),self.changeSliderGreen)
   
    def reconnectChangingControls(self):
        self.connect(self.redSlider,SIGNAL("valueChanged(int)"),self.changeSpinRed)
        self.connect(self.redSpinBox,SIGNAL("valueChanged(int)"),self.changeSliderRed)
        self.connect(self.blueSlider,SIGNAL("valueChanged(int)"),self.changeSpinBlue)
        self.connect(self.blueSpinBox,SIGNAL("valueChanged(int)"),self.changeSliderBlue)
        self.connect(self.greenSlider,SIGNAL("valueChanged(int)"),self.changeSpinGreen)
        self.connect(self.greenSpinBox,SIGNAL("valueChanged(int)"),self.changeSliderGreen)    
        
    # called as a slot from button push
    def setElementInfo(self,value):
        self.w.setElement(value)
        
    def setDisplay(self, value):
        eInfoText = "<p>" + str(value) + "</p> "
        elemSymbol = self.elemTable.getElemSymbol(value)
        if not elemSymbol: return
        eInfoText += "<p> " + "<font size=26> <b>" + elemSymbol + "</b> </font> </p>"
        eInfoText += "<p>" + elementAMU[ value ] + "</p>"
        self.elemInfoLabel.setText(eInfoText)
        
        self.buttonGroup.setButton(value)
        self.updateElemGraphDisplay()
        
        r =  int(self.color[0]*255 + 0.5)
        g = int(self.color[1]*255 + 0.5)
        b = int(self.color[2]*255 + 0.5)
        
        self.disConnectChangingControls()
        self.redSlider.setValue(r)
        self.greenSlider.setValue(g)
        self.blueSlider.setValue(b)
        self.redSpinBox.setValue(r)
        self.greenSpinBox.setValue(g)
        self.blueSpinBox.setValue(b)
        self.reconnectChangingControls()
        
    def updateElemGraphDisplay(self):
        """Update non user interactive controls display for current selected element: element label info and element graphics info """
        elemNum =  self.buttonGroup.selectedId()
        self.color = self.elemTable.getElemColor(elemNum)
        self.rad = self.elemTable.getElemRvdw(elemNum)
        
        self.elemGLPane.refreshDisplay(self.color, self.rad)
         
        r =  int(self.color[0]*255 + 0.5)
        g = int(self.color[1]*255 + 0.5)
        b = int(self.color[2]*255 + 0.5)
        self.elemColorLabel.setPaletteBackgroundColor(QColor(r, g, b)) 
        
 
    def transmutePressed(self):
        force = self.transmuteCheckBox.isChecked()
        self.w.glpane.mode.modifyTransmute(self.w.Element, force = force)
        # bruce 041216: renamed elemSet to modifyTransmute, added force option

    def read_element_rgb_table(self):
        """Open file browser to select a file to read from, read the data, update elements color in the selector dialog and also the display models """
        # Determine what directory to open.
        if self.w.assy.filename: odir, fil, ext = fileparse(self.assy.filename)
        else: odir = globalParms['WorkingDirectory']
        self.fileName = QFileDialog.getOpenFileName(odir,
                "All Files (*.*);;Elements color file (*.txt);;",
                self )
        if self.fileName:
            colorTable = readElementColors(str(self.fileName))
            if colorTable:
                for row in colorTable:
                    self.elemTable.change(row[0], color = [row[1]/255.0, row[2]/255.0, row[3]/255.0])
                
                elemNum =  self.buttonGroup.selectedId()
                self.setDisplay(elemNum)
        #After loading a file, reset the flag        
        self.isElementModified = False        
        
    def write_element_rgb_table(self):
        """Save the current set of element preferences into an external file---currently only r,g,b color of each element will be saved."""
        if not self.fileName:
           sdir = globalParms['WorkingDirectory']
        else:
           sdir = self.fileName
           
        fn = QFileDialog.getSaveFileName(sdir,
                    "Element Color File (*.txt);;",
                    self, "colorSaveDialog", "Save Element Colors As ...")
        
        if fn:
            fn = str(fn)
            if fn[-4] != '.':
                fn += '.txt'
            
            import os    
            if os.path.exists(fn): # ...and if the "Save As" file exists...
                    # ... confirm overwrite of the existing file.
                    ret = QMessageBox.warning( self, "Save Element Colors...", "The file \"" + fn + "\" already exists.\n"\
                        "Do you want to overwrite the existing file or cancel?",
                        "&Overwrite", "&Cancel", None,
                        0,      # Enter == button 0
                        1 )     # Escape == button 1

                    if ret==1: # The user cancelled
                        return 
                    
            # write the current set of element colors into a file    
            saveElementColors(fn, self.elemTable)
            #After saving a file, reset the flag        
            self.isFileSaved = True        
                
                        
                        
    def changeSliderBlue(self,a0):
        self.disconnect(self.blueSlider,SIGNAL("valueChanged(int)"),self.changeSpinBlue)
        self.blueSlider.setValue(a0)
        elemNum =  self.buttonGroup.selectedId()
        self.elemTable.change(elemNum, color = [self.color[0], self.color[1], a0/255.0])
        self.connect(self.blueSlider,SIGNAL("valueChanged(int)"),self.changeSpinBlue)
        self.updateElemGraphDisplay()
        self.isElementModified = True
        
    def changeSpinRed(self,a0):
        self.disconnect(self.redSpinBox,SIGNAL("valueChanged(int)"),self.changeSliderRed)
        self.redSpinBox.setValue(a0)
        elemNum =  self.buttonGroup.selectedId()
        self.elemTable.change(elemNum, color = [a0/255.0, self.color[1], self.color[2]])
        self.connect(self.redSpinBox,SIGNAL("valueChanged(int)"),self.changeSliderRed)
        self.updateElemGraphDisplay()
        self.isElementModified = True
        
    def changeSliderRed(self,a0):
        self.disconnect( self.redSlider,SIGNAL("valueChanged(int)"),self.changeSpinRed)
        self.redSlider.setValue(a0)
        elemNum =  self.buttonGroup.selectedId()
        self.elemTable.change(elemNum, color = [a0/255.0, self.color[1], self.color[2]])
        self.connect(self.redSlider,SIGNAL("valueChanged(int)"),self.changeSpinRed)
        self.updateElemGraphDisplay()
        self.isElementModified = True
      
    def changeSpinBlue(self,a0):
        self.disconnect(self.blueSpinBox,SIGNAL("valueChanged(int)"),self.changeSliderBlue)
        self.blueSpinBox.setValue(a0)
        elemNum =  self.buttonGroup.selectedId()
        self.elemTable.change(elemNum, color = [self.color[0], self.color[1], a0/255.0])
        self.connect(self.blueSpinBox,SIGNAL("valueChanged(int)"),self.changeSliderBlue)
        self.updateElemGraphDisplay()
        self.isElementModified = True
        
    def changeSpinGreen(self,a0):
        self.disconnect(self.greenSpinBox,SIGNAL("valueChanged(int)"),self.changeSliderGreen)
        self.greenSpinBox.setValue(a0)
        elemNum =  self.buttonGroup.selectedId()
        self.elemTable.change(elemNum, color = [self.color[0], a0/255.0, self.color[2]])
        self.connect(self.greenSpinBox,SIGNAL("valueChanged(int)"),self.changeSliderGreen)
        self.updateElemGraphDisplay()
        self.isElementModified = True
                
    def changeSliderGreen(self,a0): 
        self.disconnect(self.greenSlider,SIGNAL("valueChanged(int)"),self.changeSpinGreen)
        self.greenSlider.setValue(a0)
        elemNum =  self.buttonGroup.selectedId()
        self.elemTable.change(elemNum, color = [self.color[0], a0/255.0, self.color[2]])
        self.connect(self.greenSlider,SIGNAL("valueChanged(int)"),self.changeSpinGreen)
        self.updateElemGraphDisplay()
        self.isElementModified = True
        
    def ok(self):
        if self.isElementModified and not self.isFileSaved:
            ret = QMessageBox.question(self, "Warnings", "Do you want to save the modifications?", QMessageBox.Yes, QMessageBox.No)
            if ret == QMessageBox.Yes:
                self.write_element_rgb_table()
        
        # If element modified or external file loaded, use it 
        if self.isElementModified or self.fileName:  
            elements.elemtables[3].deepCopy(self.elemTable)
            elements.set_element_table(3, self.w.assy)    
        
        self.fileName = None
        self.isElementModified = False
        self.isFileSaved = False    
        self.accept()
        
        
    def cancel(self):
        # If elements modified or external file loaded, restore
        # current pref to originial since our dialog is reused 
        if self.isElementModified or self.fileName:  
            self.elemTable.deepCopy(elements.elemtables[3])
        
        self.fileName = None
        self.isElementModified = False
        self.isFileSaved = False    
        self.reject()
    

class ElementView(ThumbView):
    """Element graphical display """    
    def __init__(self, parent, name, shareWidget = None):
        ThumbView.__init__(self, parent, name, shareWidget)
        self.scale = 5.0 ## the possible largest rvdw of all elements
        self.color = [0.5, 0.5, 0.0]
        self.pos = [0.0, 0.0, 0.0]
        self.rad = -1.0 ##Initial value when no element selected
        self.level = 2
        self.glPane = shareWidget
        
    def drawModel(self):
        """The method for element drawing """
        if self.rad >= 0.0 :
           drawer.drawsphere(self.color, self.pos, self.rad, self.level)
           
           glDisable(GL_LIGHTING) 
           self.qglColor(QColor(0, 0, 0))
           w = self.width/2 - 10*4
           h = self.height - 24 
           self.renderText(w, h, QString('Rvdw = ' + str(self.rad)))
           glEnable(GL_LIGHTING)
            
    def refreshDisplay(self, newColor, newRad):
        """Display the new element """    
        self.color = newColor
        self.rad = newRad
        self.updateGL()
        
        
### Test code #########
import sys        
if __name__=='__main__':
  QApplication.setColorSpec(QApplication.CustomColor)
  app=QApplication(sys.argv)

  if not QGLFormat.hasOpenGL():
    raise 'No Qt OpenGL support.'

  w = elementSelector(None)
  app.setMainWidget(w)
  w.resize(400,350)
  w.show()
  w.setCaption('box')
  app.exec_loop()        