import orhelper
from lib import orhelperhelper as orhh
import numpy as np
import matplotlib.pyplot as plt
from random import gauss
from tkinter import filedialog
from orhelper import FlightDataType, FlightEvent, JIterator
from .orhelperhelper import ExtendedDataType
import tkinter as tk
from tkinter import ttk


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
                        ExtendedDataType.TYPE_CHAR_OSCILLATION_DISTANCE:[],
                        ExtendedDataType.TYPE_FLUTTER_VELOCITY_CF:[],
                        ExtendedDataType.TYPE_FLUTTER_VELOCITY_FG:[],
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
            NF = np.sqrt(C1/I_long)  #Natural frequency, Hz 
            COD = NF/vel # Characteristic oscillation distance, 1/m
            Q = 0.5*dens*(vel**2) # Dynamic pressure
            VF = soundspeed*self.vf_coeff/np.sqrt(pres) # fin flutter velocity with unity shear modulus, m/s
            safety_factor = 10 # safety factor on shear moduli for orthotropic consideration
            VF_CF = VF*np.sqrt(1E10/safety_factor) # fin flutter velocity with shear modulus of carbon fiber, ~10GPa
            VF_FG = VF*np.sqrt(3E10/safety_factor) # fin flutter velocity with shear modulus of fiber glass, ~30GPa
        
        else:
            ''' If not in air-stabilized ascent phase, append NaN. '''
            self.last_motor_mass = float(self.mass_calc.getPropellantMass(self.sim_config, self.motor_config))
            C1 = np.nan # Corrective moment coefficient
            C2R = np.nan # Propulsive damping coefficient
            C2A = np.nan # Aerodynamic damping coefficient
            C2 = np.nan # Damping coefficient
            DR = np.nan # Damping Ratio
            NF = np.nan #Natural frequency 
            COD = np.nan # Characteristic oscillation distance
            Q = np.nan # Dynamic pressure
            VF = np.nan # fin flutter velocity with unity shear modulus
            VF_CF = np.nan
            VF_FG = np.nan

        self.results[ExtendedDataType.TYPE_DAMPING_COEFF].append(C2)
        self.results[ExtendedDataType.TYPE_DAMPING_RATIO].append(DR)
        self.results[ExtendedDataType.TYPE_CORRECTIVE_COEFF].append(C1)
        self.results[ExtendedDataType.TYPE_NATURAL_FREQUENCY].append(NF)
        self.results[ExtendedDataType.TYPE_CHAR_OSCILLATION_DISTANCE].append(COD)
        self.results[ExtendedDataType.TYPE_DYNAMIC_PRESSURE].append(Q)
        self.results[ExtendedDataType.TYPE_FLUTTER_VELOCITY].append(VF)
        self.results[ExtendedDataType.TYPE_FLUTTER_VELOCITY_CF].append(VF_CF)
        self.results[ExtendedDataType.TYPE_FLUTTER_VELOCITY_FG].append(VF_FG)

        return super().postStep(status)
    
    def get_results(self): 
        # return dict of results in order of type enumeration
        return self.results


