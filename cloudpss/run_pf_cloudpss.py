import json
import numpy as np
import sys
import os

# Add parent directory to path for pypower access
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pypower.runpf import runpf
from pypower.ppoption import ppoption
from pypower.idx_bus import VM
from case_lf_n10_cloudpss import build_case_cloudpss

class NumPyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, (np.bool_, bool)):
            return bool(obj)
        return json.JSONEncoder.default(self, obj)

def run_pf_cloudpss():
    """Run power flow calculations using CloudPSS line parameters."""
    ppopt = ppoption(VERBOSE=0, OUT_ALL=0, PF_TOL=1e-8)

    scenarios = {
        'standard': np.array([200, 100, 200, 100, 100, 100, 100, 100]),
        'low': np.array([200, 100, 200, 100, 100, 100, 100, 100]) * 0.3,
        'heavy': np.array([200, 100, 200, 100, 100, 100, 100, 100]) * 1.1,
        'trip': np.array([0, 100, 200, 100, 100, 100, 100, 100])
    }
    
    all_results = {}
    modes = {
        'q_const': {'mode': 0, 'pf': 1.0},
        'pf_const': {'mode': 1, 'pf': 0.98},
        'pf_099': {'mode': 1, 'pf': 0.99}
    }

    for mode_name, config in modes.items():
        all_results[mode_name] = {}
        mode_val = config['mode']
        pf_val = config['pf']
        print(f"Processing Mode: {mode_name} (PF={pf_val})")
        
        for name, Ps in scenarios.items():
            try:
                ppc = build_case_cloudpss(Ps, control_mode=mode_val, pf=pf_val)
                res = runpf(ppc, ppopt)
                
                output = {
                    'success': bool(res[0]['success']),
                    'bus': res[0]['bus'].tolist(),
                    'gen': res[0]['gen'].tolist(),
                    'branch': res[0]['branch'].tolist()
                }
                all_results[mode_name][name] = output
                status = "✓" if output['success'] else "✗"
                print(f"  Scenario {name}: {status}")
            except Exception as e:
                print(f"  Error in scenario {name}: {e}")
                
        # P-V Sweep for each mode
        sweep_results = []
        base_ps = scenarios['standard']
        for scale in np.arange(0.1, 1.6, 0.1):
            Ps_sweep = base_ps * scale
            try:
                ppc_s = build_case_cloudpss(Ps_sweep, control_mode=mode_val, pf=pf_val)
                res_s = runpf(ppc_s, ppopt)
                if res_s[0]['success']:
                    row = [float(scale)] + res_s[0]['bus'][:, VM].tolist()
                    sweep_results.append(row)
            except:
                pass
        all_results[mode_name]['sweep'] = sweep_results
        print(f"  P-V sweep: {len(sweep_results)} converged points")

    with open('results_python.json', 'w') as f:
        json.dump(all_results, f, cls=NumPyEncoder, indent=4)
    print("\nCloudPSS power flow completed. Results saved to results_python.json")

if __name__ == "__main__":
    run_pf_cloudpss()
