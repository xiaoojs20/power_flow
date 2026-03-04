import json
import numpy as np
from pypower.runpf import runpf
from case_lf_n10_py import build_case_lfreq_n10_py

def run_pf_python_n10():
    from pypower.ppoption import ppoption
    from pypower.runpf import runpf
    from case_lf_n10_py import build_case_lfreq_n10_py
    
    ppopt = ppoption(VERBOSE=0, OUT_ALL=0, PF_TOL=1e-8)

    scenarios = {
        'standard': np.array([200, 100, 200, 100, 100, 100, 100, 100]),
        'low': np.array([200, 100, 200, 100, 100, 100, 100, 100]) * 0.3,
        'heavy': np.array([200, 100, 200, 100, 100, 100, 100, 100]) * 1.1,
        'trip': np.array([0, 100, 200, 100, 100, 100, 100, 100])
    }
    
    # helper for JSON serialization of numpy arrays
    class NumPyEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            if isinstance(obj, (np.bool_, bool)):
                return bool(obj)
            return json.JSONEncoder.default(self, obj)
            
    all_results = {}
    modes = {'q_const': 0, 'pf_const': 1}
    
    from pypower.idx_bus import VM

    for mode_name, mode_val in modes.items():
        all_results[mode_name] = {}
        print(f"Processing Mode: {mode_name}")
        
        for name, Ps in scenarios.items():
            try:
                ppc = build_case_lfreq_n10_py(Ps, control_mode=mode_val)
                res = runpf(ppc, ppopt)
                
                output = {
                    'success': bool(res[0]['success']),
                    'bus': res[0]['bus'].tolist(),
                    'gen': res[0]['gen'].tolist(),
                    'branch': res[0]['branch'].tolist()
                }
                all_results[mode_name][name] = output
                print(f"  Scenario {name} processed.")
            except Exception as e:
                print(f"  Error in scenario {name}: {e}")
                
        # P-V Sweep for each mode
        sweep_results = []
        base_ps = scenarios['standard']
        for scale in np.arange(0.1, 1.6, 0.1):
            Ps_sweep = base_ps * scale
            try:
                ppc_s = build_case_lfreq_n10_py(Ps_sweep, control_mode=mode_val)
                res_s = runpf(ppc_s, ppopt)
                if res_s[0]['success']:
                    row = [float(scale)] + res_s[0]['bus'][:, VM].tolist()
                    sweep_results.append(row)
            except:
                pass
        all_results[mode_name]['sweep'] = sweep_results

    with open('results_python.json', 'w') as f:
        json.dump(all_results, f, cls=NumPyEncoder, indent=4)
    print("PYPOWER 10-node scenarios and sweeps completed for all modes.")

if __name__ == "__main__":
    run_pf_python_n10()
