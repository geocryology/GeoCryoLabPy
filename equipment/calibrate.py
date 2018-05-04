
"""
bath calibration

bath temp           probe temp
    -10.00              -10.216
    +25.00              +24.795
"""


r0 = 99.978
a  = 0.0038563
sL = -10.0
sH = 25.0

tL = -10.216
tH = 24.795

eL = tL - sL
eH = tH - sH

r0_new = r0 * (1 + a * (eH * sL - eL * sH) / (sH - sL))
a_new  = a  * (1 + ((1 + a * sH) * eL - (1 + a * sL) * eH) / (sH - sL))

print r0_new
print a_new