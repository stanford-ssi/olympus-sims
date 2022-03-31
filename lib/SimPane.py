from email import iterators
import tkinter as tk
from tkinter import ttk
from tkinter.tix import COLUMN
import numpy as np

from matplotlib.pyplot import plot
from lib import orhelperhelper as orhh
import orhelper
from orhelper import FlightDataType, FlightEvent
from .ORSimListener import ORSimListener
from .units import units

class Sim:
    def __init__(self, ORinstance, orh, ork_file, idx, name, motor):
        self.idx = idx
        self.name = name
        self.motor = motor
        self.ork_file = ork_file
        self.or_instance = ORinstance
        self.orh = orh
        self.data = []
        self.num_iters = 1
        self.events = []

        # sim outputs
        self.rail_depart_speed = tk.DoubleVar(value=0)
        self.max_altitude = tk.DoubleVar(value=0)
        self.time_to_apogee = tk.DoubleVar(value=0)
        self.max_ascent_speed = tk.DoubleVar(value=0)
        self.max_q = tk.DoubleVar(value=0)
        self.max_mach = tk.DoubleVar(value=0)
    
    def run(self, iterations = 1):
        iterations = min(max(1,iterations),10)
        self.num_iters = iterations
        self.data = []
        self.events = []
        self.doc = self.orh.load_doc(self.ork_file)

        sim = self.doc.getSimulation(self.idx) 

        for i in range(iterations):
            print("Running simulation iteration " + str(i+1)+ " of " + str(iterations))
            opts = sim.getOptions()
            rocket = opts.getRocket()

            # Run simulation
            orsimlistener = ORSimListener(sim, rocket)
            self.orh.run_simulation(sim,listeners=[orsimlistener])
            data = self.orh.get_timeseries(sim, [e for e in FlightDataType]) # get all data available
            extended_data = orsimlistener.get_results()
            data.update(extended_data)
            events = self.orh.get_events(sim)
            
            # Add data to simulation list
            self.data.append(data)           
            self.events.append(events)
        self.update_outputs()
    
    def update_outputs(self):
        new_alt = 0
        new_rail_depart_speed = 0
        new_time_to_ap = 0
        new_max_ascent_speed = 0
        new_max_q = 0
        new_max_mach = 0
        num_iters = len(self.data)
        for i in range(num_iters):
            new_alt += max(self.data[i][FlightDataType.TYPE_ALTITUDE])/num_iters
            rail_depart_time = self.events[i][FlightEvent.LAUNCHROD][0]
            rail_depart_ind = np.where((self.data[i][FlightDataType.TYPE_TIME]-rail_depart_time)==min(abs(self.data[i][FlightDataType.TYPE_TIME]-rail_depart_time)))
            new_rail_depart_speed += self.data[i][FlightDataType.TYPE_VELOCITY_Z][rail_depart_ind[0][0]]/num_iters
            pre_ap_time_idx = self.data[i][FlightDataType.TYPE_TIME] < self.events[i][FlightEvent.APOGEE][0]
            new_max_ascent_speed += max(self.data[i][FlightDataType.TYPE_VELOCITY_Z][pre_ap_time_idx])
            new_max_q += max(self.data[i][FlightDataType.TYPE_ACCELERATION_Z][pre_ap_time_idx])
            new_max_mach += max(self.data[i][FlightDataType.TYPE_MACH_NUMBER][pre_ap_time_idx])
            new_time_to_ap += self.events[i][FlightEvent.APOGEE][0]/num_iters
        self.max_altitude.set(new_alt)
        self.rail_depart_speed.set(new_rail_depart_speed)
        self.time_to_apogee.set(new_time_to_ap)
        self.max_ascent_speed.set(new_max_ascent_speed)
        self.max_q.set(new_max_q)
        self.max_mach.set(new_max_mach)

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
        self.sim_select.grid(row=0,column=1,columnspan=2,sticky='nsew')
        ttk.Separator(self,orient='horizontal').grid(row=1,columnspan=2,sticky='nsew')
        self.alt_var = tk.DoubleVar(self,value=0) # stores unit-correct value of avg max altitude from last sim
        self.alt_unit = tk.StringVar(self,value='m')
        ttk.Label(self,text='Altitude: ').grid(row=3,column=0,sticky='nsew')
        ttk.Label(self,textvariable=self.alt_var).grid(row=3,column=1,sticky='nsew')
        ttk.OptionMenu(self,self.alt_unit,'m',*('m','ft','mi'),command=self.update_outputs).grid(row=3,column=2,sticky='nsew')

        self.time_to_ap_var = tk.DoubleVar(self, value=0)
        self.time_to_ap_unit = tk.StringVar(self,value='s')
        ttk.Label(self,text='Time to Apogee: ').grid(row=4,column=0,sticky='nsew')
        ttk.Label(self,textvariable=self.time_to_ap_var).grid(row=4,column=1,sticky='nsew')
        ttk.OptionMenu(self,self.time_to_ap_unit,'s',*('s','min','hr'),command=self.update_outputs).grid(row=4,column=2,sticky='nsew')
       
        self.rail_speed_var = tk.DoubleVar(self, value=0)
        self.rail_speed_unit = tk.StringVar(self,value='m*s^-1')
        ttk.Label(self,text='Rail Speed: ').grid(row=5,column=0,sticky='nsew')
        ttk.Label(self,textvariable=self.rail_speed_var).grid(row=5,column=1,sticky='nsew')
        ttk.OptionMenu(self,self.rail_speed_unit,'m*s^-1',*('m*s^-1','mi*hr^-1','ft*s^-1')).grid(row=5,column=2,sticky='nsew')

        self.max_speed_var = tk.DoubleVar(self, value=0)
        self.max_speed_unit = tk.StringVar(self,value='m*s^-1')
        ttk.Label(self,text='Max. Speed: ').grid(row=6,column=0,sticky='nsew')
        ttk.Label(self,textvariable=self.max_speed_var).grid(row=6,column=1,sticky='nsew')
        ttk.OptionMenu(self,self.max_speed_unit,'m*s^-1',*('m*s^-1','mi*hr^-1','ft*s^-1')).grid(row=6,column=2,sticky='nsew')

        self.max_mach_var = tk.DoubleVar(self, value=0)
        self.max_mach_unit = tk.StringVar(self,value='unitless')
        ttk.Label(self,text='Max. Mach: ').grid(row=7,column=0,sticky='nsew')
        ttk.Label(self,textvariable=self.max_mach_var).grid(row=7,column=1,sticky='nsew')
        ttk.OptionMenu(self,self.max_mach_unit,'unitless',*('unitless')).grid(row=7,column=2,sticky='nsew')

        self.max_q_var = tk.DoubleVar(self, value=0)
        self.max_q_unit = tk.StringVar(self,value='m*s^-2')
        ttk.Label(self,text='Max. Acceleration: ').grid(row=8,column=0,sticky='nsew')
        ttk.Label(self,textvariable=self.max_q_var).grid(row=8,column=1,sticky='nsew')
        ttk.OptionMenu(self,self.max_q_unit,'m*s^-2',*('m*s^-2','ft*s^-2')).grid(row=8,column=2,sticky='nsew')
        
        precision = 2
        self.alt_unit.trace_add(mode='write',callback=lambda *args : self.alt_var.set(round(units.convert(self.get_sim().max_altitude.get(),'m',self.alt_unit.get()),precision)))
        self.time_to_ap_unit.trace_add(mode='write',callback=lambda *args : self.time_to_ap_var.set(round(units.convert(self.get_sim().time_to_apogee.get(),'s',self.time_to_ap_unit.get()),precision)))
        self.rail_speed_unit.trace_add(mode='write',callback=lambda *args : self.rail_speed_var.set(round(units.convert(self.get_sim().rail_depart_speed.get(),'m*s^-1',self.rail_speed_unit.get()),precision)))
        self.max_speed_unit.trace_add(mode='write',callback=lambda *args : self.max_speed_var.set(round(units.convert(self.get_sim().max_ascent_speed.get(),'m*s^-1',self.max_speed_unit.get()),precision)))
        self.max_mach_unit.trace_add(mode='write',callback=lambda *args : self.max_mach_var.set(round(units.convert(self.get_sim().max_mach.get(),'unitless',self.max_mach_unit.get()),precision)))
        self.max_q_unit.trace_add(mode='write',callback=lambda *args : self.max_q_var.set(round(units.convert(self.get_sim().max_q.get(),'m*s^-2',self.max_q_unit.get()),precision)))


        ttk.Label(self,text='Num. iterations').grid(row = 10, column=0,sticky='nsew')
        self.iter_var = tk.IntVar(self,value=1)
        ttk.Entry(self,textvariable=self.iter_var).grid(row=10, column=1, sticky='nsew')
        ttk.Button(self,text='Run Sim',command=self.run_sim).grid(row=10, column=2, sticky='nsew')

        self.columnconfigure(1,weight=1)
        self.rowconfigure(9,weight=1)

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
        self.update_outputs()
        # clear plots, update plotting if data exists
        if len(self.curr_sim.data) > 0:
            self.plot()
        #update free plot pane with sim
        self.plotpane.update_sim(self.curr_sim)
        self.freeplotpane.update_sim(self.curr_sim)
    
    def update_outputs(self,*args):
        # Force updated calc by writing to unit var
        self.alt_unit.set(self.alt_unit.get())
        self.time_to_ap_unit.set(self.time_to_ap_unit.get())
        self.rail_speed_unit.set(self.rail_speed_unit.get())
        self.max_speed_unit.set(self.max_speed_unit.get())
        self.max_mach_unit.set(self.max_mach_unit.get())
        self.max_q_unit.set(self.max_q_unit.get())

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
        self.curr_sim.run()
        self.update_outputs()
        self.plot()
    
    def plot(self):
        self.freeplotpane.update_all()
        self.plotpane.update_all()