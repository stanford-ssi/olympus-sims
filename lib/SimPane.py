import tkinter as tk
from tkinter import ttk
import numpy as np
from lib import orhelperhelper as orhh
import orhelper
from .units import units
from .Sim import Sim

class SimPane(ttk.Frame):
    def __init__(self, root, plotpane, freeplotpane):
        self.root = root
        self.plotpane = plotpane
        self.freeplotpane = freeplotpane
        self.ork_file = None
        super().__init__(root)
        ttk.Label(self,text='Sim. Select').grid(row=0,column=0,sticky='nsew')
        self.sim_select_var = tk.StringVar(self,value='')
        self.sim_select = ttk.OptionMenu(self,self.sim_select_var,'','')
        self.sim_select_var.trace_add(mode='write',callback=self.change_sim)
        self.sim_select.grid(row=0,column=1,columnspan=4,sticky='nsew')
        ttk.Separator(self,orient='horizontal').grid(row=1,columnspan=5,sticky='nsew')

        self.outmeans = []
        self.outstds = []
        self.outunits = []

        i = 2
        for j in range(len(Sim.outputs)):
            output = Sim.outputs[j]
            outmean = tk.DoubleVar(self,value=0) 
            outunit = tk.StringVar(self,value=units.get_preferred_unit(output.unit))
            outstd = tk.DoubleVar(self,value=0)
            self.outmeans.append(outmean)
            self.outstds.append(outstd)
            self.outunits.append(outunit)
            ind = i
            ttk.Label(self,text=output.name+': ').grid(row=i,column=0,sticky='nsew')
            ttk.Label(self,textvariable=self.outmeans[j]).grid(row=i,column=1,sticky='nsew')
            ttk.Label(self,text=' +/- ').grid(row=i,column=2,sticky='nsew')
            ttk.Label(self,textvariable=self.outstds[j]).grid(row=i,column=3,sticky='nsew')
            ttk.OptionMenu(self,outunit,outunit.get(),*tuple(units.get_compatible_units(outunit.get()))).grid(row=i,column=4,sticky='nsew')
            self.outunits[j].trace_add(mode='write',callback=lambda v,m,i,ind=j : self.update_output(ind))
            i += 1

        ttk.Label(self,text='Num. iterations').grid(row = i+3, column=0,sticky='nsew')
        self.iter_var = tk.IntVar(self,value=1)
        ttk.Entry(self,textvariable=self.iter_var).grid(row=i+3, column=1,columnspan=3, sticky='nsew')
        ttk.Button(self,text='Run Sim',command=self.run_sim).grid(row=i+3, column=4, sticky='nsew')

        self.columnconfigure(1,weight=1)
        self.columnconfigure(3,weight=1)
        self.rowconfigure(i+2,weight=1)

        self.sim_names = []
        self.sims = []
        self.curr_sim = None
    
    def clear_sims(self):
        self.sims = []
        self.sim_names = []

    def get_sim(self):
        return self.curr_sim

    def add_sim(self, sim_name, sim_motor):
        sim_idx = len(self.sims)
        self.sims.append(Sim(self.instance, self.orh, self.ork_file, sim_idx, sim_name,sim_motor))
        self.sim_names.append(sim_name + ' - ' + sim_motor)

    def change_sim(self, *args):
        # check which sim name is selected
        sim_selected = self.sim_names.index(self.sim_select_var.get())
        if sim_selected == -1:
            return
        self.curr_sim = self.sims[sim_selected] # get Sim object
        # update output variables, binding change of Sim vars to updating label vars
        self.curr_sim.clear_outputs()
        # clear plots, update plotting if data exists
        if len(self.curr_sim.data) > 0:
            self.plot()
            self.update_outputs()
        #update free plot pane with sim
        self.plotpane.update_sim(self.curr_sim)
        self.freeplotpane.update_sim(self.curr_sim)
    
    def update_outputs(self,*args):
        for i in range(len(Sim.outputs)):
            self.update_output(i)
        
    def update_output(self,idx):
        newunit = self.outunits[idx].get()
        baseunit = Sim.outputs[idx].unit
        precision = 2 # rounding precision
        self.outmeans[idx].set(round(units.convert(Sim.outputs[idx].mean, baseunit, newunit),precision))
        self.outstds[idx].set(round(units.convert(Sim.outputs[idx].stddev, baseunit, newunit),precision))

    def giveORinstance(self,instance):
        self.instance = instance
        self.orh = orhelper.Helper(instance)

    def updateFromORK(self, ORKfile):
        self.clear_sims()
        # Get new simulation names
        self.ork_file = ORKfile

        doc = self.orh.load_doc(ORKfile)
        sims = orhh.get_simulations(doc)
        for key in sims:
            self.add_sim(key, sims[key])
        # Update Sim Select drop down
        holdval = self.sim_select_var.get()
        menu = self.sim_select["menu"]
        menu.delete(0, "end")
        for string in self.sim_names:
            menu.add_command(label=string, 
                             command=lambda value=string: self.sim_select_var.set(value))
        if holdval not in self.sim_names:
            self.sim_select_var.set(self.sim_names[0])
    
    def run_sim(self,event=None):
        if self.curr_sim is None:
            return
        self.curr_sim.run(int(self.iter_var.get()))
        self.update_outputs()
        self.plot()
    
    def plot(self):
        self.freeplotpane.update_all()
        self.plotpane.update_all()