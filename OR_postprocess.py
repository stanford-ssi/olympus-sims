import orhelper
import orhelperhelper as orhh
import numpy as np
import matplotlib.pyplot as plt
from random import gauss
from tkinter import filedialog
from orhelper import FlightEvent
from orhelperhelper import FlightDataType
import tkinter as tk
from tkinter import ttk


''' Simulation class definitions. '''
class ORSims(list):
    def __init__(self):
        self.ORjar_file = None # path to OpenRocket JAR file
        self.ork_file= None # name of ork file to be loaded
        self.doc = None

    def ask_ORdoc(self):
        hold = filedialog.askopenfilename(title='Select an OpenRocket Document',filetypes=(('OpenRocket Documents','*.ork'),))
        if hold is not None and hold != "":
            self.ork_file = hold

    def ask_sim(self):
        def askComboValue(*values):
            top = tk.Toplevel() # use Toplevel() instead of Tk()
            tk.Label(top, text='Select your value').pack()
            box_value = tk.StringVar()
            combo = ttk.Combobox(top, textvariable=box_value, values=values)
            combo.pack()
            combo.bind('<<ComboboxSelected>>', lambda _: top.destroy())
            top.grab_set()
            top.wait_window(top)  # wait for itself destroyed, so like a modal dialog
            return box_value.get()
        sim_names = orhh.get_simulation_names(self.doc)
        if len(sim_names) < 2:
            return 0
        else:
            hold = askComboValue(*tuple(sim_names))
            try:
                return sim_names.index(hold)
            except ValueError:
                return -1

    
    def add_sims(self, num_sims = 1):
        with orhelper.OpenRocketInstance() as instance:

            # Load the document and get simulation
            orh = orhelper.Helper(instance)
            if self.ork_file == None:
                self.ask_ORdoc()
            if self.ork_file == None:
                return False
            self.doc = orh.load_doc(self.ork_file)
            # TO-DO: ask user which simulation they want loaded
            sim_ind = self.ask_sim()
            if sim_ind < 0:
                return False
            sim = self.doc.getSimulation(sim_ind) 

            for i in range(num_sims):
                # Randomize various parameters
                opts = sim.getOptions()
                rocket = opts.getRocket()

                # Run simulation
                orsimlistener = ORSimListener()
                orh.run_simulation(sim,listeners=[orsimlistener])
                data = orh.get_timeseries(sim, [FlightDataType.TYPE_TIME, FlightDataType.TYPE_ALTITUDE, FlightDataType.TYPE_VELOCITY_Z])
                events = orh.get_events(sim)

                # Add data to simulation list
                self.append(data)
            print(self)
            


class ORSimListener(orhelper.AbstractSimulationListener):
    ''' ORSimListener < AbstractSimulationListener
    A simulation listener for runs of an OpenRocket simulation. 

    Calculates desirable values during runtime after each timestep.

    TODO: Make this also adjust the wind model to match local launchsite data.
    '''
    def __init__(self):
        self.results = {FlightDataType.TYPE_DAMPING_COEFF:[],
                        FlightDataType.TYPE_DAMPING_RATIO:[],
                        FlightDataType.TYPE_CORRECTIVE_COEFF:[],
                        FlightDataType.TYPE_NATURAL_FREQUENCY:[],
                        FlightDataType.TYPE_DYNAMIC_PRESSURE:[],
                        FlightDataType.TYPE_FLUTTER_VELOCITY:[],
                        }

    def postFlightConditions(self, status, flight_conds) -> None:
        print('POST-FLIGHT_COND')
        sim_conds = status.getSimulationConditions()
        sim_config = status.getConfiguration()
        aero_calc = sim_conds.getAerodynamicCalculator()
        sim_wngs = status.getWarnings()
        force_analysis = dict(aero_calc.getForceAnalysis(sim_config, flight_conds, sim_wngs))
        for comp in force_analysis.keys():
            if force_analysis[comp].getCP() is not None:
                print(str(comp.getName()) + ' : CP = ' + str(force_analysis[comp].getCP()))

        return super().postFlightConditions(status,flight_conds)
    
    def get_results(self): 
        # return dict of calculated values
        return self.results

if __name__ == '__main__':
    sims = ORSims()
    if sims.add_sims(1): # run passed number of OR sims
        sims.plot_sims() # display output in graphic
