import tkinter as tk
from tkinter import ttk
import sys
from matplotlib.pyplot import text
import orhelper

from lib.FreePlotPane import FreePlotPane

from .ORKSelector import ORKSelector
from .SimPane import SimPane
from .PlotPane import PlotPane
from .FreePlotPane import FreePlotPane
from .PrintRedirector import PrintRedirector

class ORKPlusApp(tk.Tk):
    def __init__(self):
        super().__init__() # self is now typical "root" object in tk
        self.iconify()
        self.title('ORKPlus')
        self.ork_file = None

        # set style
        self.tk.call('source', 'lib/black.tcl')
        self.style = ttk.Style(self)
        self.style.theme_use('black')
        self.style.configure('lefttab.TNotebook',tabposition='ne')
        self.iconbitmap('lib/ssi_logo.ico')

        # create constituent components
        self.ORKselect = ORKSelector(self)
        self.plotnotebook = ttk.Notebook(self,style='lefttab.TNotebook')
        self.plotpane = PlotPane(self.plotnotebook)
        self.freeplotpane = FreePlotPane(self.plotnotebook)
        self.plotnotebook.add(self.plotpane,text='Results')
        self.plotnotebook.add(self.freeplotpane,text='Free Plot')
        self.simpane = SimPane(self,self.plotpane,self.freeplotpane)
        self.printredirector = PrintRedirector(self)

        # grid place components
        self.ORKselect.grid(row=0,column=0,columnspan=2,sticky='nsew')
        self.simpane.grid(row=1,column=0,sticky='nsew')
        self.plotnotebook.grid(row=1,column=1,sticky='nsew')
        self.printredirector.grid(row=2,column=0,columnspan=2,sticky='nsew')
        self.columnconfigure(1,weight=1)
        self.rowconfigure(1,weight=1)
        

        # bind events
        self.bind('<<NewORKSelected>>',self.updateORK)


    def updateORK(self,event=None):
        self.ork_file = self.ORKselect.currentORK()
        self.simpane.updateFromORK(self.ork_file)

    def run(self):
        ''' Starts the application loop, including the error logger and print redirector. '''
        old_stdout = sys.stdout
        with self.printredirector as sys.stdout:
            with orhelper.OpenRocketInstance() as instance:
                self.simpane.giveORinstance(instance)
                self.deiconify()
                self.state('zoomed')
                print("Welcome to ORKPlus - select an ORK file to get started.")
                self.mainloop() # start GUI application running, on close will call kill() function above
        sys.stdout = old_stdout