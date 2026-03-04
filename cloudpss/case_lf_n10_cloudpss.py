import numpy as np
from pypower.idx_bus import BUS_I, BUS_TYPE, PD, QD, GS, BS, BUS_AREA, VM, \
    VA, BASE_KV, ZONE, VMAX, VMIN
from pypower.idx_gen import GEN_BUS, PG, QG, QMAX, QMIN, VG, MBASE, \
    GEN_STATUS, PMAX, PMIN
from pypower.idx_brch import F_BUS, T_BUS, BR_R, BR_X, BR_B, RATE_A, \
    RATE_B, RATE_C, TAP, SHIFT, BR_STATUS, ANGMIN, ANGMAX

def build_case_cloudpss(Ps=None, control_mode=1, pf=0.98):
    """Build 10-node LFAC system using CloudPSS simulation platform line parameters.
    
    Key differences from original case:
    - Collection lines (1-8→9): uniform 10km (original varying 9-24km)
    - Line R/X/B per km: CloudPSS uniform values (original varying per line type)
    - Transformer impedances (main + box) are RETAINED (CloudPSS models them separately)
    - Sending line (9→10): 265km with CloudPSS R/X/B per km
    
    Args:
        Ps: Wind farm active power output array (MW), default = [200,100,200,100,100,100,100,100]
        control_mode: 0 - Constant Q (Q=0), 1 - Constant PF
        pf: Power factor target for Constant PF mode (e.g., 0.98 or 0.99)
    """
    if Ps is None:
        Ps = np.array([200, 100, 200, 100, 100, 100, 100, 100])
    
    # Base values
    Ub = 230e3       # 230 kV
    Sb = 1000e6      # 1000 MVA
    Zb = Ub**2 / Sb  # 52.9 Ohm
    fb = 20           # Hz
    
    Ps_max = np.array([200, 100, 200, 100, 100, 100, 100, 100])
    
    # ==========================================
    # CloudPSS Line Parameters (uniform for all lines)
    # ==========================================
    r_per_km = 0.01158    # Ω/km  (正序电阻)
    x_per_km = 0.02991    # Ω/km  (正序感抗)
    xc_MOhm_km = 0.3316   # MΩ·km (正序容抗, 按中国电力工程惯例)
    
    # ==========================================
    # Collection lines (1-8 → 9): all 10 km (CloudPSS uniform length)
    # Line impedance + Transformer impedance
    # ==========================================
    len_coll = 10  # km (CloudPSS uniform)
    
    # Line R (pure line resistance)
    r_line_coll = len_coll * r_per_km / Zb  # pu
    
    # Line X (pure line reactance)
    x_line_coll = len_coll * x_per_km / Zb  # pu
    
    # Line B (charging susceptance)
    xc_coll_total = xc_MOhm_km * 1e6 / len_coll          # Ω
    bc_coll_total = 1.0 / xc_coll_total                   # S
    b_coll_pu = bc_coll_total * Zb                         # pu
    
    # Transformer impedances (same as original case)
    # Main transformer: Uk% = 14%, Zbase_main = Ub^2 / Ps_max
    Zb_trm_main = Ub**2 / (Ps_max * 1e6)
    x_main_pu = 0.14 * Zb_trm_main / Zb  # per generator
    
    # Box (turbine) transformer: Uk% = 7.5%, Zbase_turb = (37kV)^2 / 6MVA
    Zb_trm_turb = (37e3)**2 / (6e6)
    x_box_pu = 0.075 * Zb_trm_turb / Zb * (230**2 / 37**2) / (np.maximum(Ps, 1e-6) / 6.0)
    
    # Total branch X for collection lines = line + main transformer + box transformer
    x_coll_total_pu = x_line_coll + x_main_pu + x_box_pu
    
    # Total branch R for collection lines (transformer R negligible, only line R)
    r_coll_total_pu = np.full(8, r_line_coll)
    
    # ==========================================
    # Sending line (9 → 10): 265 km
    # ==========================================
    len_send = 265  # km
    
    r_send_pu = len_send * r_per_km / Zb
    x_send_pu = len_send * x_per_km / Zb
    xc_send_total = xc_MOhm_km * 1e6 / len_send
    bc_send_total = 1.0 / xc_send_total
    b_send_pu = bc_send_total * Zb
    
    # M3C capacity (for gen limits only)
    Sm3c = 550  # MVA
    
    # ==========================================
    # Build ppc
    # ==========================================
    ppc = {'version': '2', 'baseMVA': 1000.0}
    
    # Bus Data (10 buses)
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
        [10, 3, 0, 0, 0, 0, 1, 1, 0, 230, 1, 1.1, 0.9]
    ])
    
    # Set isolated buses for tripped wind farms
    for i in range(8):
        if Ps[i] <= 1e-3:
            bus[i, BUS_TYPE] = 4
            
    ppc['bus'] = bus
    
    # Gen Data (10 generators)
    gen = np.zeros((10, 21))
    gen[:, GEN_BUS] = np.arange(1, 11)
    gen[:, VG] = 1.0
    gen[:, MBASE] = 1000.0
    gen[:, GEN_STATUS] = 1.0
    
    gen[0:8, PG] = Ps
    
    if control_mode == 1:
        # Constant PF
        pf_target = pf
        tan_phi = np.sqrt(1/pf_target**2 - 1)
        gen[0:8, QG] = gen[0:8, PG] * tan_phi
    else:
        # Constant Q = 0
        gen[0:8, QG] = 0.0
    
    gen[0:8, PMAX] = Ps_max
    gen[0:8, QMAX] = Ps_max * 0.65
    gen[0:8, QMIN] = -Ps_max * 0.65
    
    gen[8, PG] = 0
    gen[8, PMAX] = np.sum(Ps_max)
    
    gen[9, PG] = 0
    gen[9, PMAX] = Sm3c * 2
    
    # Update status for tripped WFs
    for i in range(8):
        if Ps[i] <= 1e-3:
            gen[i, GEN_STATUS] = 0

    ppc['gen'] = gen
    
    # Branch Data (9 branches)
    branch = np.zeros((9, 13))
    branch[:, TAP] = 1.0  # Default to 1.0
    
    # Collection lines (1-8 → 9): CloudPSS line params + transformer impedances
    for i in range(8):
        branch[i, F_BUS] = i + 1
        branch[i, T_BUS] = 9
        branch[i, BR_R] = r_coll_total_pu[i]
        branch[i, BR_X] = x_coll_total_pu[i]
        branch[i, BR_B] = b_coll_pu
        branch[i, RATE_A] = 250
        branch[i, BR_STATUS] = 1 if Ps[i] > 1e-3 else 0
        branch[i, ANGMIN] = -360
        branch[i, ANGMAX] = 360
        
    # Sending line (9 → 10)
    branch[8, F_BUS] = 9
    branch[8, T_BUS] = 10
    branch[8, BR_R] = r_send_pu
    branch[8, BR_X] = x_send_pu
    branch[8, BR_B] = b_send_pu
    branch[8, RATE_A] = 250
    branch[8, TAP] = 0  # ratio=0 means 1.0 in MATPOWER/PYPOWER
    branch[8, BR_STATUS] = 1
    branch[8, ANGMIN] = -360
    branch[8, ANGMAX] = 360
    
    ppc['branch'] = branch
    
    # Gencost Data
    ppc['gencost'] = np.array([
        [2, 0, 0, 3, 0.11, 5, 150]
    ] * 10)
    
    return ppc

if __name__ == "__main__":
    ppc = build_case_cloudpss()
    print("CloudPSS 10-node Case generated successfully.")
    print("Bus count:", len(ppc['bus']))
    print("Gen count:", len(ppc['gen']))
    print("Branch count:", len(ppc['branch']))
    print("\nBranch parameters (pu):")
    print(f"  {'Branch':<10} {'R':>12} {'X':>12} {'B':>12}")
    for i in range(9):
        f = int(ppc['branch'][i, 0])
        t = int(ppc['branch'][i, 1])
        r = ppc['branch'][i, 2]
        x = ppc['branch'][i, 3]
        b = ppc['branch'][i, 4]
        print(f"  {f}->{t:<6} {r:>12.8f} {x:>12.8f} {b:>12.8f}")
