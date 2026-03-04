import numpy as np
from pypower.idx_bus import BUS_I, BUS_TYPE, PD, QD, GS, BS, BUS_AREA, VM, \
    VA, BASE_KV, ZONE, VMAX, VMIN
from pypower.idx_gen import GEN_BUS, PG, QG, QMAX, QMIN, VG, MBASE, \
    GEN_STATUS, PMAX, PMIN
from pypower.idx_brch import F_BUS, T_BUS, BR_R, BR_X, BR_B, RATE_A, \
    RATE_B, RATE_C, TAP, SHIFT, BR_STATUS, ANGMIN, ANGMAX

def build_case_lfreq_py(Ps=None, control_mode=1):
    if Ps is None:
        Ps = np.array([200, 100, 200, 100, 100, 100, 100, 100])
    
    # control_mode: 0 - Constant Q (Q=0), 1 - Constant PF (0.98 lagging)
    
    # Base values
    Ub = 230e3
    Sb = 1000e6
    Zb = Ub**2 / Sb
    fb = 20
    
    Ps_max = np.array([200, 100, 200, 100, 100, 100, 100, 100])
    SVGs = np.array([46, 23, 47, 23, 22, 23, 23, 26])
    
    # Collection to M3C line (Line 9-10)
    len_h2b = 265
    b_h2b = 2 * np.pi * fb * 1.20E-08
    r_h2b_norm = 3.737314 / Zb
    x_h2b_norm = 2 * np.pi * fb * 0.1177 / Zb
    b_h2b_norm = len_h2b * b_h2b / (1/Zb) # b = 1/Z
    
    # WF to Collection lines (Lines 1-8)
    lens = np.array([9, 24, 24, 10, 24, 10, 10, 16])
    rs_unit = np.array([0.08, 0.108, 0.08, 0.108, 0.108, 0.108, 0.108, 0.108])
    xs_unit = 2 * np.pi * fb * np.array([1.30E-03, 1.34E-03, 1.30E-03, 1.34E-03, 
                                        1.34E-03, 1.34E-03, 1.34E-03, 1.34E-03])
    bs_unit = 10e-6 * 2 * np.pi * fb * np.array([0.00887075, 0.0086673, 0.00887075, 0.0086673, 
                                                0.0086673, 0.0086673, 0.0086673, 0.0086673])
    
    r_norm = lens * rs_unit / Zb
    
    Zb_trm_main = Ub**2 / (Ps_max * 1e6)
    Zb_trm_turb = (37e3)**2 / (6e6)
    
    x_norm = (lens * xs_unit / Zb + 
              0.14 * Zb_trm_main / Zb + 
              0.075 * Zb_trm_turb / Zb * (230**2 / 37**2) / (np.maximum(Ps, 1e-6) / 6.0))
    
    b_norm = lens * bs_unit / (1/Zb)
    
    # M3C Converter Station (Line 10-11)
    Sm3c = 550
    Um3c = 165e3
    Zb_m3c = Um3c**2 / (Sm3c * 1e6)
    
    S_tmp = 330e6
    U_tmp = 65e3
    Zb_tmp = U_tmp**2 / S_tmp
    L_tmp = 21.5e-3
    Lm3c = L_tmp / Zb_tmp * Zb_m3c / 2
    Xm3c = 2 * np.pi * fb * Lm3c
    Xm3c_norm = Xm3c / Zb
    
    # Rest of branches...
    ppc = {'version': '2', 'baseMVA': 1000.0}
    
    # Bus Data
    bus = np.array([
        [1, 1, 0, 0, 0, 0, 1, 1, 0, 37, 1, 1.1, 0.9],
        [2, 1, 0, 0, 0, 0, 1, 1, 0, 37, 1, 1.1, 0.9],
        [3, 1, 0, 0, 0, 0, 1, 1, 0, 37, 1, 1.1, 0.9],
        [4, 1, 0, 0, 0, 0, 1, 1, 0, 37, 1, 1.1, 0.9],
        [5, 1, 0, 0, 0, 0, 1, 1, 0, 37, 1, 1.1, 0.9],
        [6, 1, 0, 0, 0, 0, 1, 1, 0, 37, 1, 1.1, 0.9],
        [7, 1, 0, 0, 0, 0, 1, 1, 0, 37, 1, 1.1, 0.9],
        [8, 1, 0, 0, 0, 0, 1, 1, 0, 37, 1, 1.1, 0.9],
        [9, 1, 0, 0, 0, 0, 1, 1, 0, 230, 1, 1.1, 0.9],
        [10, 2, 0, 0, 0, 0, 1, 1, 0, 230, 1, 1.1, 0.9],
        [11, 3, 0, 0, 0, 0, 1, 1, 0, 165, 1, 1.1, 0.9]
    ])
    
    # Set Isolated buses
    for i in range(8):
        if Ps[i] <= 1e-3:
            bus[i, BUS_TYPE] = 4
            
    ppc['bus'] = bus
    
    # Gen Data
    # bus Pg Qg Qmax Qmin Vg mBase status Pmax Pmin
    gen = np.zeros((11, 21))
    gen[:, GEN_BUS] = np.arange(1, 12)
    gen[:, VG] = 1.0
    gen[:, MBASE] = 1000.0
    gen[:, GEN_STATUS] = 1.0
    
    gen[0:8, PG] = Ps
    
    if control_mode == 1:
        # 定功率因数控制 (Constant PF = 0.98 Lagging)
        pf_target = 0.98
        tan_phi = np.sqrt(1/pf_target**2 - 1)
        gen[0:8, QG] = gen[0:8, PG] * tan_phi
    else:
        # 定无功控制 (Constant Q = 0)
        gen[0:8, QG] = 0.0
    
    gen[0:8, PMAX] = Ps_max
    gen[0:8, QMAX] = Ps_max * 0.65
    gen[0:8, QMIN] = -Ps_max * 0.65
    
    gen[8, PG] = 0
    gen[8, PMAX] = np.sum(Ps_max)
    
    gen[9, PG] = 0
    gen[9, PMAX] = Sm3c * 2
    
    gen[10, PG] = 0
    gen[10, PMAX] = 0
    
    # Update status for trip
    for i in range(8):
        if Ps[i] <= 1e-3:
            gen[i, GEN_STATUS] = 0

    ppc['gen'] = gen
    
    # Branch Data
    branch = np.zeros((10, 13))
    branch[:, TAP] = 1.0 # Set all to 1.0 by default
    for i in range(8):
        branch[i, F_BUS] = i + 1
        branch[i, T_BUS] = 9
        branch[i, BR_R] = r_norm[i]
        branch[i, BR_X] = x_norm[i]
        branch[i, BR_B] = b_norm[i]
        branch[i, RATE_A] = 250
        branch[i, BR_STATUS] = 1 if Ps[i] > 1e-3 else 0
        branch[i, ANGMIN] = -360
        branch[i, ANGMAX] = 360
        
        if Ps[i] <= 1e-3:
            gen[i, GEN_STATUS] = 0
            
    # Rest of branches...
    # Line 9-10
    branch[8, F_BUS] = 9
    branch[8, T_BUS] = 10
    branch[8, BR_R] = r_h2b_norm
    branch[8, BR_X] = x_h2b_norm
    branch[8, BR_B] = b_h2b_norm
    branch[8, RATE_A] = 250
    branch[8, BR_STATUS] = 1
    branch[8, ANGMIN] = -360
    branch[8, ANGMAX] = 360
    
    # Line 10-11
    branch[9, F_BUS] = 10
    branch[9, T_BUS] = 11
    branch[9, BR_R] = 0
    branch[9, BR_X] = Xm3c_norm
    branch[9, BR_B] = 0
    branch[9, RATE_A] = 250
    branch[9, BR_STATUS] = 1
    branch[9, ANGMIN] = -360
    branch[9, ANGMAX] = 360
    
    ppc['branch'] = branch
    
    # Gencost Data
    # 2 startup shutdown n c(n-1) ... c0
    ppc['gencost'] = np.array([
        [2, 0, 0, 3, 0.11, 5, 150]
    ] * 11)
    
    return ppc

if __name__ == "__main__":
    ppc = build_case_lfreq_py()
    print("PYPOWER Case generated successfully.")
    print("Bus count:", len(ppc['bus']))
    print("Gen count:", len(ppc['gen']))
    print("Branch count:", len(ppc['branch']))
