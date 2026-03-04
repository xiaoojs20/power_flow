"""
CloudPSS EMT Simulation Demo - IEEE 3-Machine 9-Bus System

Following the CloudPSS SDK quick-start documentation:
1. Fetch IEEE3 model
2. Run power flow (jobs[0])
3. Run EMT simulation (jobs[1])
4. Retrieve waveform data and generate plots
"""

import sys
import os
import json
import time

import cloudpss

# ─── Configuration ──────────────────────────────────────────────────────────
TOKEN = 'eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6NTQxMywidXNlcm5hbWUiOiJ4aWFvanMyMCIsInNjb3BlcyI6WyJtb2RlbDo5ODM2NyIsImZ1bmN0aW9uOjk4MzY3IiwiYXBwbGljYXRpb246MzI4MzEiXSwicm9sZXMiOlsieGlhb2pzMjAiXSwidHlwZSI6ImFwcGx5IiwiZXhwIjoxODAzNzE2NTMwLCJub3RlIjoic2RrX3hpYW9vIiwiaWF0IjoxNzcyNjEyNTMwfQ.Pds8At5AEb0EFeLyEo8wYN8xBuugbywZLIvoGklJBSDxCcAdmBJK5mZ-cQ7jhzyNF33sSQzv_1JO68aV9zUOew'
MODEL_RID = 'model/CloudPSS/IEEE3'
API_URL = 'https://cloudpss.net/'

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
EMT_RESULTS_FILE = os.path.join(SCRIPT_DIR, 'emt_results.json')
PF_RESULTS_FILE = os.path.join(SCRIPT_DIR, 'pf_results.json')
EMT_FIGS_DIR = os.path.join(SCRIPT_DIR, 'emt_figs')


def main():
    print("=" * 60)
    print("  CloudPSS EMT Demo - IEEE 3-Machine 9-Bus")
    print("=" * 60)

    # ── 1. Setup ─────────────────────────────────────────────────
    cloudpss.setToken(TOKEN)
    os.environ['CLOUDPSS_API_URL'] = API_URL
    print(f"API: {API_URL}")
    print(f"RID: {MODEL_RID}")

    # ── 2. Fetch model ───────────────────────────────────────────
    print("\n[1/5] Fetching model...")
    model = cloudpss.Model.fetch(MODEL_RID)
    print(f"  configs: {len(model.configs)}, jobs: {len(model.jobs)}")
    for i, j in enumerate(model.jobs):
        name = j.get('name', j.get('rid', 'unknown'))
        rid = j.get('rid', '')
        print(f"  job[{i}]: {name} (rid={rid})")

    config = model.configs[0]

    # ── 3. Power Flow ────────────────────────────────────────────
    print("\n[2/5] Running Power Flow (jobs[0])...")
    pf_job = model.jobs[0]
    runner = model.run(pf_job, config)

    t0 = time.time()
    while not runner.status():
        logs = runner.result.getLogs()
        for log in logs:
            print(f"  [PF] {log}")
        time.sleep(1)
    elapsed = time.time() - t0
    print(f"  Power flow done in {elapsed:.1f}s")

    # Save PF results
    pf_data = {}
    try:
        buses = runner.result.getBuses()
        branches = runner.result.getBranches()
        pf_data = {'buses': buses, 'branches': branches}
        print(f"  Buses: {len(buses)} tables, Branches: {len(branches)} tables")
        with open(PF_RESULTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(pf_data, f, indent=2, ensure_ascii=False, default=str)
        print(f"  Saved: {PF_RESULTS_FILE}")
    except Exception as e:
        print(f"  Warning getting PF results: {e}")

    # ── 4. Write back PF & Run EMT ───────────────────────────────
    print("\n[3/5] Writing PF back to model...")
    try:
        runner.result.powerFlowModify(model)
        print("  Done.")
    except Exception as e:
        print(f"  Warning: {e}")

    print("\n[4/5] Running EMT Simulation (jobs[1])...")
    emt_job = model.jobs[1]
    print(f"  Job: {emt_job.get('name', 'EMT')}")

    runner = model.run(emt_job, config)

    t0 = time.time()
    while not runner.status():
        logs = runner.result.getLogs()
        for log in logs:
            print(f"  [EMT] {log}")
        elapsed_now = time.time() - t0
        if int(elapsed_now) % 15 == 0:
            print(f"  ... {elapsed_now:.0f}s elapsed")
        time.sleep(2)
    elapsed = time.time() - t0
    print(f"  EMT done in {elapsed:.1f}s")

    # ── 5. Retrieve EMT results ──────────────────────────────────
    print(f"\n[5/5] Retrieving EMT results...")
    plots = runner.result.getPlots()
    print(f"  Plot groups: {len(plots)}")

    all_data = {}
    for i in range(len(plots)):
        channels = runner.result.getPlotChannelNames(i)
        print(f"  Group [{i}]: {len(channels)} channels")
        for ch in channels:
            print(f"    - {ch}")
        group = {}
        for name in channels:
            ch = runner.result.getPlotChannelData(i, name)
            group[name] = ch
        all_data[f'group_{i}'] = group

    # Save JSON
    with open(EMT_RESULTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False, default=str)
    print(f"  Saved: {EMT_RESULTS_FILE}")

    # ── 6. Generate plots ────────────────────────────────────────
    print("\nGenerating plots...")
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        matplotlib.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
        matplotlib.rcParams['axes.unicode_minus'] = False
    except ImportError:
        print("  matplotlib not installed, skipping.")
        return

    os.makedirs(EMT_FIGS_DIR, exist_ok=True)

    # Per-group overview plots
    for gname, gdata in all_data.items():
        if not gdata:
            continue
        fig, ax = plt.subplots(figsize=(14, 5))
        for ch_name, ch_val in gdata.items():
            if isinstance(ch_val, dict) and 'x' in ch_val and 'y' in ch_val:
                label = ch_val.get('name', ch_name)
                ax.plot(ch_val['x'], ch_val['y'], label=label, linewidth=0.6)
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Value')
        ax.set_title(f'EMT Results - {gname}')
        ax.legend(fontsize=7, loc='best', ncol=2)
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        fpath = os.path.join(EMT_FIGS_DIR, f'{gname}.png')
        fig.savefig(fpath, dpi=150)
        plt.close(fig)
        print(f"  Saved: {fpath}")

    # Individual channel plots (first 8)
    all_channels = []
    for gname, gdata in all_data.items():
        for ch_name, ch_val in gdata.items():
            if isinstance(ch_val, dict) and 'x' in ch_val and 'y' in ch_val:
                all_channels.append((gname, ch_name, ch_val))

    for idx, (gname, ch_name, ch_val) in enumerate(all_channels[:8]):
        fig, ax = plt.subplots(figsize=(12, 4))
        label = ch_val.get('name', ch_name)
        ax.plot(ch_val['x'], ch_val['y'], 'b-', linewidth=0.5)
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Value')
        ax.set_title(label)
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        safe = ch_name.replace('/', '_').replace('#', '').replace(':', '_')
        fpath = os.path.join(EMT_FIGS_DIR, f'ch_{idx}_{safe}.png')
        fig.savefig(fpath, dpi=150)
        plt.close(fig)
        print(f"  Saved: {fpath}")

    print("\n" + "=" * 60)
    print("  ALL DONE!")
    print("=" * 60)


if __name__ == '__main__':
    main()
