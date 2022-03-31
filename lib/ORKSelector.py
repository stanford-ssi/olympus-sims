import tkinter as tk
from tkinter import ttk
from tkinter import filedialog

from matplotlib.pyplot import text
from lib import orhelperhelper as orhh

class ORKSelector(tk.Frame):
    def __init__(self, root):
        self.root = root
        super().__init__(root)
        self.ork_file = tk.StringVar(self,'OlympusTestRocket-Current.ork')
        
        # create constituent widgets
        self.ork_entry = ttk.Entry(self,textvariable=self.ork_file,state=tk.DISABLED)
        self.ork_select = ttk.Button(self,text="Select ORK File",command=self.selectORK)
        self.ork_refresh = ttk.Button(self,text="Refresh ORK File",command=self.refreshORK)

        # pack constituent widgets
        self.ork_entry.grid(row=0,column=0,columnspan=5,sticky='nsew')
        self.ork_select.grid(row=0,column=5,sticky='nsew')
        self.ork_refresh.grid(row=0,column=6,sticky='nsew')
        self.columnconfigure(0,weight=1)
        self.rowconfigure(0,weight=1)

    def selectORK(self,event=None):
        hold = filedialog.askopenfilename(title='Select an OpenRocket Document',filetypes=(('OpenRocket Documents','*.ork'),))
        if hold is not None and hold != "":
            self.ork_file.set(hold)
            self.refreshORK()
    
    def refreshORK(self, event=None):
        self.root.event_generate("<<NewORKSelected>>", when="tail") # just pretend we loaded a new ORK file without changin
    
    def currentORK(self):
        return self.ork_file.get()