from logging import root
import orhelper
from orhelper import FlightDataType, FlightEvent
from orhelper import JIterator
from enum import Enum
from typing import Union, List, Iterable, Dict
import numpy as np

''' Extend FlightDataType to include our added data types. '''
flightdatalen = max([x.value for x in FlightDataType])
class ExtendedDataType(Enum):
    TYPE_DAMPING_COEFF = flightdatalen + 1
    TYPE_DAMPING_RATIO = flightdatalen + 2
    TYPE_CORRECTIVE_COEFF = flightdatalen + 3
    TYPE_NATURAL_FREQUENCY = flightdatalen + 4
    TYPE_DYNAMIC_PRESSURE = flightdatalen + 5
    TYPE_FLUTTER_VELOCITY = flightdatalen + 6
    TYPE_CHAR_OSCILLATION_DISTANCE = flightdatalen + 7
    TYPE_FLUTTER_VELOCITY_CF = flightdatalen + 8
    TYPE_FLUTTER_VELOCITY_FG = flightdatalen + 9

''' Create dict that provides mapping from FlightDataType/ExtendedDataType to string desc and unit. '''
class DataType:
    def __init__(self, name, unit):
        self.name = name
        self.unit = unit

DataTypeMap = {    
    FlightDataType.TYPE_TIME : DataType('time','s'),
    FlightDataType.TYPE_ALTITUDE : DataType('Altitude','m'),
    FlightDataType.TYPE_VELOCITY_Z : DataType('Vertical Velocity','m*s^-1'),
    FlightDataType.TYPE_ACCELERATION_Z : DataType('Vertical Acceleration','m*s^-2'),
    FlightDataType.TYPE_VELOCITY_TOTAL : DataType('Velocity','m*s^-1'),
    FlightDataType.TYPE_ACCELERATION_TOTAL : DataType('Acceleration','m*s^-2'),
    FlightDataType.TYPE_POSITION_X : DataType('Position E','m'),
    FlightDataType.TYPE_POSITION_Y : DataType('Position N','m'),
    FlightDataType.TYPE_POSITION_XY : DataType('Lateral Distance','m'),
    FlightDataType.TYPE_VELOCITY_XY : DataType('Horizontal Velocity','m*s^-1'),
    FlightDataType.TYPE_ACCELERATION_XY : DataType('Horizontal Acceleration','m*s^-2'),
    FlightDataType.TYPE_AOA  : DataType('Angle of Attack','rad'),
    FlightDataType.TYPE_ROLL_RATE : DataType('Roll Rate','rad*s^-1'),
    FlightDataType.TYPE_PITCH_RATE : DataType('Pitch Rate','rad*s^-1'),
    FlightDataType.TYPE_YAW_RATE : DataType('Yaw Rate','rad*s^-1'),
    FlightDataType.TYPE_MASS : DataType('Mass','kg'),
    FlightDataType.TYPE_PROPELLANT_MASS : DataType('Propellant Mass','kg'),
    FlightDataType.TYPE_LONGITUDINAL_INERTIA : DataType('Longitudinal Inertia','kg*m^-2'),
    FlightDataType.TYPE_ROTATIONAL_INERTIA : DataType('Rotational Inertia','kg*m^-2'),
    FlightDataType.TYPE_CP_LOCATION : DataType('CP','m'),
    FlightDataType.TYPE_CG_LOCATION : DataType('CG','m'),
    FlightDataType.TYPE_STABILITY : DataType('Static Margin Calibers','unitless'),
    FlightDataType.TYPE_MACH_NUMBER : DataType('Mach Number','unitless'),
    FlightDataType.TYPE_REYNOLDS_NUMBER : DataType('Reynolds Number','unitless'),
    FlightDataType.TYPE_THRUST_FORCE : DataType('Thrust','N'),
    FlightDataType.TYPE_DRAG_FORCE : DataType('Drag Force','N'),
    FlightDataType.TYPE_DRAG_COEFF : DataType('Drag Coefficient','unitless'),
    FlightDataType.TYPE_AXIAL_DRAG_COEFF : DataType('Axial Drag Coefficient','unitless'),
    FlightDataType.TYPE_FRICTION_DRAG_COEFF : DataType('Friction Drag Coefficient','unitless'),
    FlightDataType.TYPE_PRESSURE_DRAG_COEFF : DataType('Pressure Drag Coefficient','unitless'),
    FlightDataType.TYPE_BASE_DRAG_COEFF : DataType('Base Drag Coefficient','unitless'),
    FlightDataType.TYPE_NORMAL_FORCE_COEFF : DataType('Normal Force Coefficient','unitless'),
    FlightDataType.TYPE_PITCH_MOMENT_COEFF : DataType('Pitch Moment Coefficient','unitless'),
    FlightDataType.TYPE_YAW_MOMENT_COEFF : DataType('Yaw Moment Coefficient','unitless'),
    FlightDataType.TYPE_SIDE_FORCE_COEFF : DataType('Lateral Force Coefficient','unitless'),
    FlightDataType.TYPE_ROLL_MOMENT_COEFF : DataType('Roll Moment Coefficient','unitless'),
    FlightDataType.TYPE_ROLL_FORCING_COEFF : DataType('Roll Forcing Coefficient','unitless'),
    FlightDataType.TYPE_ROLL_DAMPING_COEFF : DataType('Roll Damping Coefficient','unitless'),
    FlightDataType.TYPE_PITCH_DAMPING_MOMENT_COEFF : DataType('Pitch Damping Moment Coefficient','unitless'),
    FlightDataType.TYPE_YAW_DAMPING_MOMENT_COEFF : DataType('Yaw Damping Moment Coefficient','unitless'),
    FlightDataType.TYPE_CORIOLIS_ACCELERATION : DataType('Coriolis Acceleration','m*s^-2'),
    FlightDataType.TYPE_REFERENCE_LENGTH : DataType('Reference Length','m'),
    FlightDataType.TYPE_REFERENCE_AREA : DataType('Reference Area','m^2'),
    FlightDataType.TYPE_ORIENTATION_THETA : DataType('Vertical Orientation (zenith)','rad'),
    FlightDataType.TYPE_ORIENTATION_PHI : DataType('Lateral Orientation (azimuth)','rad'),
    FlightDataType.TYPE_WIND_VELOCITY : DataType('Wind Velocity','m*s^-1'),
    FlightDataType.TYPE_AIR_TEMPERATURE : DataType('Air Temperature','K'),
    FlightDataType.TYPE_AIR_PRESSURE : DataType('Air Pressure','Pa'),
    FlightDataType.TYPE_SPEED_OF_SOUND : DataType('Speed of Sound','m*s^-1'),
    FlightDataType.TYPE_TIME_STEP : DataType('Time Step','s'),
    FlightDataType.TYPE_COMPUTATION_TIME : DataType('Computation Time','s'),
    ExtendedDataType.TYPE_DAMPING_COEFF : DataType('Damping Coefficient','unitless'),
    ExtendedDataType.TYPE_DAMPING_RATIO : DataType('Damping Ratio','unitless'),
    ExtendedDataType.TYPE_CORRECTIVE_COEFF : DataType('Corrective Moment Coefficient','unitless'),
    ExtendedDataType.TYPE_NATURAL_FREQUENCY : DataType('Natural Frequency','rad*s^-1'),
    ExtendedDataType.TYPE_DYNAMIC_PRESSURE : DataType('Dynamic Pressure','Pa'),
    ExtendedDataType.TYPE_FLUTTER_VELOCITY : DataType('Fin Flutter Velocity (Unity Shear Modulus)','m*s^-1'),
    ExtendedDataType.TYPE_CHAR_OSCILLATION_DISTANCE : DataType('Charateristic Oscillation Length','m'),
    ExtendedDataType.TYPE_FLUTTER_VELOCITY_CF : DataType('Carbon Fiber Fin Flutter Velocity','m*s^-1'),
    ExtendedDataType.TYPE_FLUTTER_VELOCITY_FG : DataType('Fiberglass Fin Flutter Velocity','m*s^-1'),
}

EventTypeMap = {
    FlightEvent.LAUNCH : "Launch",
    FlightEvent.IGNITION : "Ignition",
    FlightEvent.LIFTOFF : "Liftoff",
    FlightEvent.LAUNCHROD : "Launch Rod Clearance",
    FlightEvent.BURNOUT : "Burnout",
    FlightEvent.EJECTION_CHARGE : "Ejection Charge",
    FlightEvent.STAGE_SEPARATION : "Stage Separation",
    FlightEvent.APOGEE : "Apogee",
    FlightEvent.RECOVERY_DEVICE_DEPLOYMENT : "Recovery Deployment",
    FlightEvent.GROUND_HIT : "Ground Hit",
    FlightEvent.SIMULATION_END : "Simulation End",
    FlightEvent.ALTITUDE : "Altitude",
    FlightEvent.TUMBLE : "Tumble",
    FlightEvent.EXCEPTION : "Exception"
}

''' orhelper add-on functions. '''
def get_all_components(rocket,debug=False):
    ''' Get all components objects and return them as a list. '''
    ret = []
    for component in JIterator(rocket):
         ret.append(component)
         if debug:
             print(component.getName())
    return ret

def calculate_fin_flutter_coeff(rocket):
    ''' Get fin components and calculate flutter coeff - the resulting fin flutter critical speed is:
            v_finflutter = flutter_coeff * a * sqrt(G/P)

            where  a = speed of sound at current altitude
                   G = shear modulus of fin material (assumed isotropic)
                   P = static pressure at current altitude
     '''
    fins = None
    for component in JIterator(rocket):
        try:
            component.getRootChord() # check to see if component is a TrapezoidalFinSet
            fins = component
            break
        except:
            pass
    if fins is None:
        raise AttributeError("Rocket does not have a trapezoidal fin set.")
    rootchord = float(fins.getRootChord())
    tipchord = float(fins.getTipChord())
    thickness = float(fins.getThickness())
    semispan = float(fins.getSpan())
    fin_area = 0.5*(rootchord+tipchord)*semispan
    aspect_ratio = (semispan**2)/fin_area
    l = tipchord/rootchord
    vf_coeff = np.sqrt(2*(aspect_ratio+2)*((thickness/rootchord)**3)/(1.337*(aspect_ratio**3)*(l+1)))

    return vf_coeff

def get_simulations(doc):
    ''' Get all simulations in a doc and return them as a dict mapping sim name to motor employed.'''
    ret = {}
    for sim in doc.getSimulations():
        this_sim_name = str(sim.getName()) 
        sim_opts = sim.getOptions()
        motorconfig_id = sim_opts.getMotorConfigurationID()
        config = sim.getConfiguration() # create new config
        found_motor = False
        for comp in JIterator(sim.getRocket()):
            try:
                motor_name = comp.getMotor(motorconfig_id).getDesignation()
                this_motor = str(motor_name)
                found_motor = True
                break
            except Exception as e:
                pass
        if not(found_motor):
            this_motor = 'No Motor' 
        ret[this_sim_name] = this_motor
    return ret

def get_status_flight_data(status, variables : Iterable[Union[FlightDataType, str]]):
    ''' Get most recent flight data values from a simulation status. '''
    def translate_flight_data_type(flight_data_type:Union[FlightDataType, str]):
        if isinstance(flight_data_type, FlightDataType):
            name = flight_data_type.name
        elif isinstance(flight_data_type, str):
            name = flight_data_type
        else:
            raise TypeError("Invalid type for flight_data_type")
        return getattr(FlightDataType, name)

    branch = status.getFlightData()
    output = dict()
    for v in variables:
        output[v] = np.array(branch.get(translate_flight_data_type(v)))
    return output
