import numpy as np
from math import erfc, sqrt, log10
Q = lambda x: 0.5*erfc(x/sqrt(2))
rng = np.random.default_rng(1)
N = 2_000_000
bits = rng.integers(0, 2, N)
sym = 2*bits - 1.0
print("noise_v  sigma/comp  EbN0_dB  theory   sim_aligned  sim_shift1")
for v in (0.1, 0.3, 0.5, 0.7, 1.0, 1.5, 2.0):
    s = v/np.sqrt(2)
    rx = sym + s*rng.standard_normal(N)
    dec = (rx >= 0).astype(int)
    ber = np.mean(dec != bits)
    ber_shift = np.mean(dec[1:] != bits[:-1])
    th = Q(1/s)
    print(f"{v:6.1f}  {s:9.3f}  {-20*log10(v):7.2f}  {th:.5f}  {ber:.5f}      {ber_shift:.5f}")
