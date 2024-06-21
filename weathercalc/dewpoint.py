import math

###
# Define constants
###

b = 18.678
c = 257.14
d = 234.5

def gamma_m(T: float, RH: int):
    return math.log((RH/100)*math.exp((b-T/d)*(T/(c+T))))

def dew_point(T: float, RH: int):
    gm = gamma_m(T, RH)
    return (c * gm)/(b - gm)
