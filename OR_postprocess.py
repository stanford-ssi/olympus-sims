import orhelper
import orhelperhelper as orhh
import numpy as np
import matplotlib.pyplot as plt
from random import gauss
from tkinter import filedialog
from orhelper import FlightDataType, FlightEvent, JIterator
from orhelperhelper import ExtendedDataType
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
            tk.Label(top, text='Select which motor to use:').pack()
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
                orsimlistener = ORSimListener(sim, rocket)
                orh.run_simulation(sim,listeners=[orsimlistener])
                data = orh.get_timeseries(sim, [e for e in FlightDataType]) # get all data available
                extended_data = orsimlistener.get_results()
                data.update(extended_data)
                events = orh.get_events(sim)
                
                # Add data to simulation list
                self.append(data)           

        return True 
    
    def plot_sims(self):
        for i in range(len(self)):
            xtime = self[i][FlightDataType.TYPE_TIME]
            # Plot Extended Data
            plt.figure(0)
            plt.plot(xtime, self[i][ExtendedDataType.TYPE_DAMPING_RATIO])
            plt.title("Damping Ratio")
            plt.xlabel('time (s)')
            plt.ylabel('\zeta')

            plt.figure(1)
            plt.plot(xtime, self[i][ExtendedDataType.TYPE_NATURAL_FREQUENCY])
            plt.title("Natural Frequency")
            plt.xlabel('time (s)')
            plt.ylabel('Natural Freq (Hz)')

            plt.figure(2)
            plt.plot(xtime, np.abs(np.divide(self[i][FlightDataType.TYPE_VELOCITY_TOTAL],np.multiply(np.sqrt(10E9),self[i][ExtendedDataType.TYPE_FLUTTER_VELOCITY]))))
            plt.title("Velocity to Fin Flutter Speed Ratio")
            plt.xlabel('time (s)')
            plt.ylabel('Speed Ratio')

        plt.show()



class ORSimListener(orhelper.AbstractSimulationListener):
    ''' ORSimListener < AbstractSimulationListener
    A simulation listener for runs of an OpenRocket simulation. 

    Calculates desirable values during runtime after each timestep.

    TODO: Make this also adjust the wind model to match local launchsite data.
    '''
    def __init__(self, sim, rocket):
        self.results = {ExtendedDataType.TYPE_DAMPING_COEFF:[],
                        ExtendedDataType.TYPE_DAMPING_RATIO:[],
                        ExtendedDataType.TYPE_CORRECTIVE_COEFF:[],
                        ExtendedDataType.TYPE_NATURAL_FREQUENCY:[],
                        ExtendedDataType.TYPE_DYNAMIC_PRESSURE:[],
                        ExtendedDataType.TYPE_FLUTTER_VELOCITY:[],
                        }
        self.rocket = rocket
        self.x_ne = rocket.getLength()
        self.timestep = sim.getOptions().getTimeStep()
        self.vf_coeff = orhh.calculate_fin_flutter_coeff(rocket)
        self.sim_conds = None
        self.sim_config = None
        self.motor_config = None
        self.motor_instance = None
        self.mass_calc = None
        self.aero_calc = None
        self.flight_conds = None
        self.last_motor_mass = 0
        self.last_time = 0

    def postFlightConditions(self, status, flight_conds):
        self.flight_conds = flight_conds
        return super().postFlightConditions(status,flight_conds)

    def postStep(self, status):
        if self.sim_conds is None:
            self.sim_conds = status.getSimulationConditions()
            self.sim_config = status.getConfiguration()
            self.motor_config = status.getMotorConfiguration()
            # TODO: figure out if this is ever the wrong motor id to choose
            motor_id = self.motor_config.getMotorIDs().get(0)
            self.motor_instance = self.motor_config.getMotorInstance(motor_id)
            self.mass_calc = self.sim_conds.getMassCalculator()
            self.aero_calc = self.sim_conds.getAerodynamicCalculator()
        
        sim_wngs = status.getWarnings()        
        force_analysis = dict(self.aero_calc.getForceAnalysis(self.sim_config, self.flight_conds, sim_wngs))
        reached_apogee = status.isApogeeReached()
        launchrod_cleared = status.isLaunchRodCleared()

        # TODO - check for launchrod clear and apogee, store values as Nan
        if launchrod_cleared and not(reached_apogee):
            # Atmospheric conditions
            atm_conds = self.flight_conds.getAtmosphericConditions()
            pres = float(atm_conds.getPressure())
            soundspeed = float(atm_conds.getMachSpeed())
            dens = float(atm_conds.getDensity())

            # Rocket conditions
            area_ref = float(self.flight_conds.getRefArea())
            cps = [] # list of CPs for each aerodynamic component
            cnas = [] # list of CNas for eacha aerodynamic component
            for comp in force_analysis.keys():
                if force_analysis[comp].getCP() is not None:
                    cps.append(float(force_analysis[comp].getCP().length()))
                    cnas.append(float(force_analysis[comp].getCNa()))
            motor_mass = float(self.mass_calc.getPropellantMass(self.sim_config, self.motor_config))
            prop_mdot = (self.last_motor_mass - motor_mass)/self.timestep # backwards Euler derivative
            cp = sum(cps) # total rocket Cp
            cna = sum(cnas) # total rocket CNa
            vel = float(self.flight_conds.getVelocity()) # velocity of rocket
            I_long = float(self.mass_calc.getLongitudinalInertia(self.sim_config, self.motor_config)) # longitudinal inertia of rocket
            cg = float(self.rocket.getCG().length()) # center of gravity of rocket

            ''' Update stored values'''
            self.last_motor_mass = motor_mass

            ''' Calculate new data values. '''
            C1 = 0.5*dens*(vel**2)*area_ref*cna*(cp-cg) # Corrective moment coefficient
            C2R = prop_mdot*(self.x_ne-cg)**2 # Propulsive damping coefficient
            C2A = 0.5*dens*vel*area_ref*sum([(cna_x-cg)**2 for cna_x in cnas]) # Aerodynamic damping coefficient
            C2 = np.add(C2R,C2A) # Damping coefficient
            DR = C2/(2*np.sqrt(C1*I_long)) # Damping Ratio
            NF = np.sqrt(C1/I_long)/(2*np.pi) #Natural frequency 
            Q = 0.5*dens*(vel**2) # Dynamic pressure
            VF = soundspeed*self.vf_coeff/np.sqrt(pres) # fin flutter velocity with unity shear modulus
        
        else:
            ''' If not in air-stabilized ascent phase, append NaN. '''
            self.last_motor_mass = float(self.mass_calc.getPropellantMass(self.sim_config, self.motor_config))
            C1 = np.nan # Corrective moment coefficient
            C2R = np.nan # Propulsive damping coefficient
            C2A = np.nan # Aerodynamic damping coefficient
            C2 = np.nan # Damping coefficient
            DR = np.nan # Damping Ratio
            NF = np.nan #Natural frequency 
            Q = np.nan # Dynamic pressure
            VF = np.nan # fin flutter velocity with unity shear modulus

        self.results[ExtendedDataType.TYPE_DAMPING_COEFF].append(C2)
        self.results[ExtendedDataType.TYPE_DAMPING_RATIO].append(DR)
        self.results[ExtendedDataType.TYPE_CORRECTIVE_COEFF].append(C1)
        self.results[ExtendedDataType.TYPE_NATURAL_FREQUENCY].append(NF)
        self.results[ExtendedDataType.TYPE_DYNAMIC_PRESSURE].append(Q)
        self.results[ExtendedDataType.TYPE_FLUTTER_VELOCITY].append(VF)

        return super().postStep(status)
    
    def get_results(self): 
        # return dict of results in order of type enumeration
        return self.results

if __name__ == '__main__':
    sims = ORSims()
    if sims.add_sims(1): # run passed number of OR sims
        sims.plot_sims() # display output in graphic
