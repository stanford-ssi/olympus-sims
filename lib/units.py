''' 
Units:

The units module handles basic unit conversion by defining a set of unit conversion anonymous 
functions. The functions use numpy array-friendly operations to allow users to pass a value array in place
of a single value, should they wish.
'''

import numpy as np

''' The unit lib stores conversion functions that take a value, x, from a given unit to the base unit. Metric modifiers on base units are 
    handled separately (made easy by the fact that all base units are the metric base units). 
    Ex:  unit_lib['m']['in'] is the equivalent of  0.0254 (m / in) 

    NOTE: The unit lib doesn't handle unit systems with different zero-reference points, e.g. temperature. The unit_offset structure holds
    offset values; if a unit is not found in the unit_offset library, it is assumed that reference points are the same.
'''
unit_lib = {
    "m" : { "m": 1, "in": 0.0254, "ft": 0.0254 * 12.0, "mi": 1609.344 } , # LINEAR DISTANCE (base: meter), area and volume also handled with ^ operator (e.g in^2)
    "L" : { "L": 1, "m^3": 1E3, "mm^3":1E-6, "in^3": (0.0254**3)/1E-3, "ft^3": (0.0254**3.0)*(1728)/1E-3, "gal":3.785411784}, # VOLUME (base: Liter | Liter is special, so we include this despite power handling)
    "N" : { "N": 1, "lbf": 4.4482216 }, # FORCE (base: Newton)
    "s" : { "s": 1, "min":60, "hr": 3600 }, # TIME (base: seconds)
    "g" : { "g": 1, "kg":1000, "lb": 453.59237 , "slug": 14593.90}, # MASS (base: gram | lb is included for imperial-minded folk)
    "Pa" :{ "Pa": 1, "psi": 6894.7572931783, "atm": 101325, "bar": 1e5 }, # PRESSURE (base: Pascal)
    "K" : { "K": 1, "R": 5.0/9.0, "C": 1, "F": 5.0/9.0 }, #TEMPERATURE (base: Kelvin)
    "J" : { "J": 1}, # ENERGY (base: Joule)
    "rad": {"rad":1,"deg": np.pi/180, "rot": 2*np.pi }, # ANGLE (base: rad)
    "unitless" : { "unitless": 1, "none": 1 } # UNITLESS
}
''' The unit_offset stores the offsets of a unit from the base unit's zero reference, in the base unit. If a unit is not found in the unit_offset
    structure, it is assumed that no reference-shift is necessary.
    Ex: to convert a temperature, T, in degC to degK
    degK = unit_lib['K']['C'] * T degC + unit_offset['K']['C'] degK 
'''
unit_offset = {
    "K" : {"C": 273.15 , "F": 273.15 - 32*5.0/9.0 }, #TEMPERATURE OFFSETS 
}

''' The metric mult stores the metric multipliers based on the shorthand prefixes. '''
metric_mult = {
    "k": 1000,
    "h": 100,
    "da": 10,
    "d": 0.1,
    "c": 0.01,
    "m": 1E-3,
    "n": 1E-9
}

''' The preferred unit for a given type of base unit. If a base unit doesn't have a preferred definition here, uses base unit as preferred.'''
unit_preferred = {
    "m" : "ft",
    "L" : "L",
    "N" : "lbf",
    "s" : "s",
    "g" : "lb",
    "Pa": "psi",
    "K" : "K",
    "rad" : "deg",
}

class Units():
    def __init__(self):
        pass

    def get_available_units(self):
        ''' Returns a list of all available units defined in the units lib '''
        unit_list = []
        for key in unit_lib:
            unit_list += list(unit_lib[key].keys())
        return unit_list
    
    def get_preferred_unit(self, unit):
        ''' Returns the preferred unit compatible with unit. '''
        # Check for composite unit
        split_units = [x.strip(' ()') for x in unit.split('*')] 
        if len(split_units) > 1:
            return '*'.join(self.get_preferred_unit(x) for x in split_units)

        comp_units = self.get_compatible_units(unit)
        for my_unit in comp_units:
            splitstr = my_unit.split('^')
            my_unit_no_power = splitstr[0]
            power = 1
            if len(splitstr) >1:
                power = splitstr[1]
            if my_unit_no_power in unit_lib.keys():
                return_unit = my_unit
                try:
                    return_unit =  unit_preferred[my_unit]
                except KeyError:
                    try:
                        return_unit =  unit_preferred[my_unit_no_power]+'^'+power 
                    except:
                        pass
                return return_unit

    def get_compatible_units(self, unit, power = 1):
        ''' Returns a list of units compatible with the given unit. 
            The returned list will contain the given unit, unless no other compatible units are found.
        '''  
        # Check for composite unit
        split_units = [x.strip(' ()') for x in unit.split('*')] 
        if len(split_units) > 1:
            comp_units = []
            for x in self.get_compatible_units(split_units[0]):
                for y in self.get_compatible_units(split_units[1]):
                    comp_units = comp_units + [x+'*'+y]
            return comp_units

        my_base_unit = None 
        # Search for the unit in the unit lib
        for base_unit in unit_lib:
            for each_unit in unit_lib[base_unit]:
                if unit.casefold() == each_unit.casefold() :
                    my_base_unit = base_unit
                    break
        
        if my_base_unit == None: # if didn't find it in the lib, try removing a power
            powercheck = unit.split('^') # check to see if unit is taken to a power
            unit = powercheck[0]
            if len(powercheck) > 1:
                try:
                    return self.get_compatible_units(unit, int(powercheck[1])) # pass w power arg
                except:
                    return [] # if power is invalid, return empty string

        
        if my_base_unit is None: # check for metrix prefix
            for prefix in metric_mult:
                if unit[:len(prefix)].casefold() == prefix.casefold():
                    return self.get_compatible_units(unit[len(prefix):], power) 

        if my_base_unit is None: # If you still don't find a base unit, return empty list
            return []
        else:
            if power == 1:
                return list(unit_lib[my_base_unit].keys()) # return list of keys for that base unit
            else:
                return list([key + '^' + str(power) for key in unit_lib[my_base_unit].keys() ]) # return list of key with power modifier

    def validate_units(self, from_unit, to_unit): 
        ''' Returns true if from_unit can be converted to to_unit by this module. Otherwise returns false. '''
        try:
            self.convert(1.0, to_unit, from_unit)
            return True
        except KeyError:
            return False

    def convert(self, value, from_unit, to_unit, power = 1.0):
        ''' Returns the conversion of a value in one unit to a compatible unit.
            value: the value to be converted (can also be a np array of values)
            from_unit: the units of value
            to_unit: the units to which value is converted 

            Raises a KeyError if the units passed are incompatible or invalid.

            For composite units, the units must have the same structure, i.e.
            CORRECT:
                from_unit = 'kg * m^-2 * s' and to_unit = 'lb * in^-2 * s' are compatible, but
            INCORRECT
                to_unit = 'kg * m^-2 * s' and to_unit = 's * lb * in^-2 ' are NOT compatible
        '''
        # Check for composite unit
        split_fromunits = [x.strip(' ()') for x in from_unit.split('*')] 
        split_tounits = [x.strip(' ()') for x in to_unit.split('*')]
        if len(split_fromunits) != len(split_tounits):
            raise KeyError # if have different number of composite units
        elif len(split_fromunits) > 1:
            new_val = value
            for i in range(0,len(split_fromunits)):
                new_val = self.convert(new_val,split_fromunits[i], split_tounits[i])
            return new_val


        my_base_unit = None
        # Search for the from_unit in the unit lib
        for base_unit in unit_lib:
            for unit in unit_lib[base_unit]:
                if unit.casefold() == from_unit.casefold() :
                    my_base_unit = base_unit
                    from_unit = unit
                    break
            if my_base_unit is not None:
                break
        
        # if didn't find it, check to see if the units are to powers
        if my_base_unit is None:
            powercheck_from = from_unit.split('^') # check to see if unit is taken to a power
            from_unit = powercheck_from[0]
            powercheck_to = to_unit.split('^')
            to_unit = powercheck_to[0]

            if len(powercheck_from) == len(powercheck_to) and len(powercheck_from) > 1 :
                try:
                    if float(powercheck_from[1]) != float(powercheck_to[1]):
                        raise KeyError # if powers arent equal, return Key Error
                    else:
                        return self.convert(value, from_unit, to_unit, float(powercheck_from[1])) # collect the power of the unit
                except:
                    raise KeyError
            elif len(powercheck_from) != len(powercheck_to):
                from_unit = '^'.join(powercheck_from) # if they arent both to a power, return the values to their initial state, and check them raw against the unit_lib (checking for L and m^3. for example)
                to_unit = '^'.join(powercheck_to)

        # If didn't find it, from_unit is a metric multiplier of the base unit. 
        # If so, adjust the value to get it in its base unit equivalent (e.g. take the km value to m)
        if my_base_unit is None:
            for prefix in metric_mult:
                if from_unit[:len(prefix)].casefold() == prefix.casefold():
                    value = np.multiply(value, np.power( metric_mult[prefix] , power) )
                    return self.convert(value, from_unit[len(prefix):]+'^'+str(power), to_unit+'^'+str(power)) # having converted to a base unit and multiplied valued, recurse
        # Do the same as above for the to_unit, defining a multiplier thats applied on the value at end if to_unit is 
            # a metric multiplier of a base unit
        mult = 1 # by default, multiplier is 1
        flag = False
        for unit in unit_lib[my_base_unit]:
            if unit.casefold() == to_unit.casefold():
                to_unit = unit
                flag = True
        if flag is False: # If didn't find it, must be a metric multiplier of a base unit
                for prefix in metric_mult:
                    if to_unit[:len(prefix)].casefold() == prefix.casefold():
                        mult = 1 / np.power( metric_mult[prefix] , power)
                        to_unit = to_unit[len(prefix):]
                        for unit in unit_lib[my_base_unit]: # if found the metric multiplier, find the key that is the case-insensitive match
                            if unit.casefold() == to_unit.casefold():
                                to_unit = unit
                                break
                        break
        # Convert to base unit, checking to see if an offset exists 
        value = np.multiply(value, np.power(unit_lib[my_base_unit][from_unit], float(power)) ) # value (from_unit) * # (base_unit/from_unit) = new value (base_unit)
        try:
            value = np.add(value, unit_offset[my_base_unit][from_unit])
        except KeyError:
            pass # KeyError indicates no offset exists for this unit pair
        # Convert to to_unit, checking to see if an offset exists
        try:
            value = np.subtract(value, unit_offset[my_base_unit][to_unit])
        except KeyError:
            pass # KeyError indicates no offset exists for this unit pair
        value = np.divide(value, np.power(unit_lib[my_base_unit][to_unit], float(power)))
        
        return np.multiply(value, mult) # apply the multiplier and return


units = Units()


### FUNCTIONALITY TESTING ###
# print( 0 == units.convert(-273.15, 'C', 'K'))
# print( 2.54 == units.convert(1.0, 'in', 'cm'))
# print(1000/0.0254 == units.convert(1.0, 'km', 'in'))
# print(2.54e-5 == units.convert(1.0, 'in', 'km'))
# print(abs(1/2.21 - units.convert(1.0,'lb','kg')) <= 1E-2)
# print(abs(0.00155 - units.convert(1.0,'mm^2','in^2')) <=1E-3)
# print(units.validate_units('L', 'ft^3'))
# print(units.convert(1.0,'L','ft^3'))
# print( [[1.0], [2.0], [3.0]] ==  np.divide(units.convert([[1],[2],[3]], 'km', 'in'), 1000/0.0254 ) )
# print(units.get_compatible_units('m*s^-2'))
