"""
CloudPSS EMT Electromagnetic Transient Simulation Script

This script uses the CloudPSS SDK to:
1. Fetch the model (model/xiaojs20/low_freq_copy)
2. Run power flow calculation
3. Write power flow results back to model
4. Run EMT (electromagnetic transient) simulation
5. Retrieve and save waveform data
6. Generate plot images
"""

import sys
import os
import json
import time

import cloudpss

# ─── Configuration ──────────────────────────────────────────────────────────
TOKEN = 'eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6NTQxMywidXNlcm5hbWUiOiJ4aWFvanMyMCIsInNjb3BlcyI6WyJtb2RlbDo5ODM2NyIsImZ1bmN0aW9uOjk4MzY3IiwiYXBwbGljYXRpb246MzI4MzEiXSwicm9sZXMiOlsieGlhb2pzMjAiXSwidHlwZSI6ImFwcGx5IiwiZXhwIjoxODAzNzE2NTMwLCJub3RlIjoic2RrX3hpYW9vIiwiaWF0IjoxNzcyNjEyNTMwfQ.Pds8At5AEb0EFeLyEo8wYN8xBuugbywZLIvoGklJBSDxCcAdmBJK5mZ-cQ7jhzyNF33sSQzv_1JO68aV9zUOew'
MODEL_RID = 'model/xiaojs20/low_freq_copy'
API_URL = 'https://cloudpss.net/'

# Output paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
EMT_RESULTS_FILE = os.path.join(SCRIPT_DIR, 'emt_results.json')
EMT_FIGS_DIR = os.path.join(SCRIPT_DIR, 'emt_figs')


def setup_cloudpss():
    """Set up CloudPSS connection."""
    cloudpss.setToken(TOKEN)
    os.environ['CLOUDPSS_API_URL'] = API_URL
    print(f"CloudPSS API URL: {API_URL}")
    print(f"Model RID: {MODEL_RID}")


def fetch_model():
    """Fetch the model from CloudPSS."""
    print("\n" + "=" * 60)
    print("Fetching model...")
    model = cloudpss.Model.fetch(MODEL_RID)
    print(f"Model fetched successfully.")

    # Print available configs and jobs for diagnostics
    print(f"\nAvailable configs ({len(model.configs)}):")
    for i, cfg in enumerate(model.configs):
        print(f"  [{i}] {cfg}")

    print(f"\nAvailable jobs ({len(model.jobs)}):")
    for i, job in enumerate(model.jobs):
        print(f"  [{i}] {job}")

    return model


def run_power_flow(model):
    """Run power flow calculation and return runner."""
    print("\n" + "=" * 60)
    print("Step 1: Running Power Flow Calculation...")
    print("=" * 60)

    config = model.configs[0]
    job = model.jobs[0]  # First job = power flow

    print(f"Config: {config}")
    print(f"Job: {job}")

    runner = model.run(job, config)

    # Wait for completion
    while not runner.status():
        logs = runner.result.getLogs()
        for log in logs:
            print(f"  [PF LOG] {log}")
        time.sleep(1)

    print("Power flow calculation completed.")

    # Print power flow results
    try:
        buses = runner.result.getBuses()
        branches = runner.result.getBranches()
        print(f"\n--- Power Flow Results ---")
        print(f"Buses: {json.dumps(buses, indent=2, ensure_ascii=False, default=str)[:2000]}")
        print(f"Branches: {json.dumps(branches, indent=2, ensure_ascii=False, default=str)[:2000]}")
    except Exception as e:
        print(f"Warning: Could not retrieve power flow results: {e}")

    return runner


def run_emt_simulation(model, pf_runner):
    """Run EMT simulation using power flow results as initial condition."""
    print("\n" + "=" * 60)
    print("Step 2: Writing Power Flow Results Back to Model...")
    print("=" * 60)

    # Write power flow results back to model
    try:
        pf_runner.result.powerFlowModify(model)
        print("Power flow results written back to model successfully.")
    except Exception as e:
        print(f"Warning: powerFlowModify failed: {e}")
        print("Proceeding with EMT simulation without power flow write-back...")

    print("\n" + "=" * 60)
    print("Step 3: Running EMT Simulation...")
    print("=" * 60)

    config = model.configs[0]
    # EMT job is typically the second job (index 1)
    if len(model.jobs) > 1:
        job = model.jobs[1]
    else:
        print("Warning: Only one job available, using jobs[0] for EMT.")
        job = model.jobs[0]

    print(f"Config: {config}")
    print(f"EMT Job: {job}")

    runner = model.run(job, config)

    # Wait for completion with log output
    while not runner.status():
        logs = runner.result.getLogs()
        for log in logs:
            print(f"  [EMT LOG] {log}")
        time.sleep(1)

    print("EMT simulation completed.")
    return runner


def retrieve_and_save_results(runner):
    """Retrieve EMT waveform data and save to JSON."""
    print("\n" + "=" * 60)
    print("Step 4: Retrieving EMT Results...")
    print("=" * 60)

    plots = runner.result.getPlots()
    print(f"Number of plot groups: {len(plots)}")

    all_channel_data = {}

    for i in range(len(plots)):
        channel_names = runner.result.getPlotChannelNames(i)
        print(f"\n  Plot group [{i}]: {len(channel_names)} channels")
        print(f"    Channel names: {channel_names}")

        group_data = {}
        for name in channel_names:
            channel_data = runner.result.getPlotChannelData(i, name)
            group_data[name] = channel_data
            # Print a brief summary
            if isinstance(channel_data, dict):
                x_data = channel_data.get('x', [])
                y_data = channel_data.get('y', [])
                print(f"    - {name}: {len(x_data)} points, "
                      f"x=[{x_data[0]:.4f}..{x_data[-1]:.4f}]" if len(x_data) > 0 else f"    - {name}: empty")

        all_channel_data[f'plot_group_{i}'] = group_data

    # Save to JSON
    with open(EMT_RESULTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_channel_data, f, indent=2, ensure_ascii=False, default=str)
    print(f"\nEMT results saved to: {EMT_RESULTS_FILE}")

    return all_channel_data


def generate_plots(all_channel_data):
    """Generate waveform plots and save as PNG."""
    print("\n" + "=" * 60)
    print("Step 5: Generating Plots...")
    print("=" * 60)

    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not available. Skipping plot generation.")
        print("Install with: pip install matplotlib")
        return

    os.makedirs(EMT_FIGS_DIR, exist_ok=True)

    for group_name, group_data in all_channel_data.items():
        if not group_data:
            continue

        fig, ax = plt.subplots(figsize=(12, 6))

        for ch_name, ch_data in group_data.items():
            if isinstance(ch_data, dict) and 'x' in ch_data and 'y' in ch_data:
                x = ch_data['x']
                y = ch_data['y']
                label = ch_data.get('name', ch_name)
                ax.plot(x, y, label=label, linewidth=0.8)

        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Value')
        ax.set_title(f'EMT Simulation - {group_name}')
        ax.legend(fontsize=8, loc='best')
        ax.grid(True, alpha=0.3)
        plt.tight_layout()

        fig_path = os.path.join(EMT_FIGS_DIR, f'{group_name}.png')
        fig.savefig(fig_path, dpi=150)
        plt.close(fig)
        print(f"  Saved: {fig_path}")

    print(f"\nAll plots saved to: {EMT_FIGS_DIR}")


def main():
    print("=" * 60)
    print("  CloudPSS EMT Electromagnetic Transient Simulation")
    print("=" * 60)

    # 1. Setup
    setup_cloudpss()

    # 2. Fetch model
    model = fetch_model()

    # 3. Run power flow
    pf_runner = run_power_flow(model)

    # 4. Run EMT simulation (with power flow write-back)
    emt_runner = run_emt_simulation(model, pf_runner)

    # 5. Retrieve and save results
    all_channel_data = retrieve_and_save_results(emt_runner)

    # 6. Generate plots
    generate_plots(all_channel_data)

    print("\n" + "=" * 60)
    print("  ALL DONE!")
    print("=" * 60)


if __name__ == '__main__':
    main()
