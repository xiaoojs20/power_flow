import json
import numpy as np

import matplotlib.pyplot as plt
import os

def compare():
    try:
        with open('results_matlab.json', 'r') as f:
            mat = json.load(f)
    except FileNotFoundError:
        print("Error: results_matlab.json not found.")
        return

    try:
        with open('results_python.json', 'r') as f:
            py = json.load(f)
    except FileNotFoundError:
        print("Error: results_python.json not found.")
        return

    modes = {
        'q_const': {
            'title': 'Part I: Constant Q Mode (Q=0)',
            'desc': '在该模式下，所有风电机组（节点 1-8）的无功出力固定为 0，系统完全依靠变频站和平衡节点支撑电压。'
        },
        'pf_const': {
            'title': 'Part II: Constant PF Mode (PF=0.98)',
            'desc': '在该模式下，风电机组按 0.98 滞后功率因数运行，无功出力随有功同步变化，提供就地电压支撑。'
        }
    }
    
    scenarios = {
        'standard': '标准工况',
        'low': '轻载工况',
        'heavy': '重载工况',
        'trip': '故障工况'
    }
    
    report = "# 低频交流输电系统 (LFAC) 潮流计算详尽双模式对比报告\n\n"
    
    report += "## 1. 仿真验证说明\n"
    report += "本报告对海上风电低频送出系统进行了两种不同风机控制策略下的潮流计算，并严格校验了 MATLAB (MATPOWER) 与 Python (PYPOWER) 的一致性。\n\n"

    for mode_id, config in modes.items():
        report += f"## {config['title']}\n"
        report += f"{config['desc']}\n\n"
        
        m_mode = mat.get(mode_id, {})
        p_mode = py.get(mode_id, {})

        # 3.X.1 Platform Consistency
        report += f"### {config['title'][0:6]}.1 平台计算一致性校验\n"
        report += "| 场景 | MATLAB 收敛 | Python 收敛 | 最大电压误差 (pu) | 结论 |\n"
        report += "| :--- | :---: | :---: | :---: | :---: |\n"
        
        for sn, s_desc in scenarios.items():
            m_s = m_mode.get(sn)
            p_s = p_mode.get(sn)
            if not m_s or not p_s: continue
            
            mb = np.array(m_s['bus']).astype(float)
            pb = np.array(p_s['bus']).astype(float)
            v_err = np.max(np.abs(mb[:, 7] - pb[:, 7]))
            report += f"| {s_desc} | {'✓' if m_s['success'] else '✗'} | {'✓' if p_s['success'] else '✗'} | {v_err:.2e} | {'对齐' if v_err < 1e-12 else '有偏'} |\n"
        report += "\n"

        # 3.X.2 P-V Sweep for this mode
        if 'sweep' in m_mode:
            report += f"### {config['title'][0:6]}.2 P-V 灵敏度扫描 (10% - 150%)\n"
            ms = np.array(m_mode['sweep'])
            ps = np.array(p_mode.get('sweep', []))
            
            if ms.ndim == 1 and ms.size > 0: ms = ms.reshape(1, -1)
            if ps.ndim == 1 and ps.size > 0: ps = ps.reshape(1, -1)

            plt.figure(figsize=(15, 12))
            for b in range(1, 12):
                plt.subplot(4, 3, b)
                if ms.size > 0: plt.plot(ms[:, 0], ms[:, b], 'r-', label='MATLAB', linewidth=1.5)
                if ps.size > 0: plt.plot(ps[:, 0], ps[:, b], 'b--', label='Python', linewidth=1.5)
                plt.title(f'Bus {b} Voltage')
                plt.grid(True)
                if b == 1: plt.legend()
            plt.tight_layout()
            pv_img = f'pf_figs/pv_sweep_{mode_id}.png'
            plt.savefig(pv_img); plt.close()
            report += f"![PV Sweep {mode_id}]({pv_img})\n\n"

        # 3.X.3 Scenario Details
        report += f"### {config['title'][0:6]}.3 详细潮流结果 (Scenario Results)\n"
        for sn, s_desc in scenarios.items():
            m_s = m_mode.get(sn)
            if not m_s: continue
            
            report += f"#### {s_desc} 潮流详表\n"
            mb = np.array(m_s['bus']).astype(float)
            mg = np.array(m_s['gen']).astype(float)
            
            report += "| 节点 (Bus) | 类型 | Vm (pu) | Va (deg) | P Gen (MW) | Q Gen (Mvar) |\n"
            report += "| :--- | :---: | :---: | :---: | :---: | :---: |\n"
            for b_idx in range(11):
                bus_id = int(mb[b_idx, 0])
                # Find gen for this bus
                g_idx = np.where(mg[:, 0] == bus_id)[0]
                pg_val = mg[g_idx[0], 1] if len(g_idx) > 0 else 0
                qg_val = mg[g_idx[0], 2] if len(g_idx) > 0 else 0
                report += f"| {bus_id} | {int(mb[b_idx, 1])} | {mb[b_idx, 7]:.4f} | {mb[b_idx, 8]:.2f} | {pg_val:.1f} | {qg_val:.1f} |\n"
            
            # Plot profiles
            plt.figure(figsize=(10, 5))
            plt.subplot(1, 2, 1)
            plt.plot(mb[:, 0], mb[:, 7], 'g-o')
            plt.title(f'V-Profile: {sn}')
            plt.xticks(range(1, 12)); plt.grid(True)
            
            plt.subplot(1, 2, 2)
            plt.bar(mg[:, 0], mg[:, 2], color='orange')
            plt.title(f'Q-Gen: {sn}')
            plt.xticks(range(1, 12)); plt.grid(True)
            
            plt.tight_layout()
            sn_img = f'pf_figs/res_{mode_id}_{sn}.png'
            plt.savefig(sn_img); plt.close()
            report += f"\n![Results {mode_id} {sn}]({sn_img})\n\n"

    # Final Comparison
    report += "## 3. 两种控制方式综合性能对比\n"
    if 'sweep' in mat['q_const'] and 'sweep' in mat['pf_const']:
        mq = np.array(mat['q_const']['sweep'])
        mp = np.array(mat['pf_const']['sweep'])
        
        plt.figure(figsize=(12, 6))
        # Plot Bus 1 for both
        plt.subplot(1, 2, 1)
        plt.plot(mq[:, 0], mq[:, 1], 'r-', label='Q=0', linewidth=2)
        plt.plot(mp[:, 0], mp[:, 1], 'b--', label='PF=0.98', linewidth=2)
        plt.title('WF1 (Bus 1) Voltage Stability')
        plt.legend(); plt.grid(True)
        
        # Plot M3C (Bus 10) Qg
        plt.subplot(1, 2, 2)
        # We need Qg from Gen 10 during sweep... actually sweep results only contain V.
        # Let's just compare Bus 9 (Connection) V.
        plt.plot(mq[:, 0], mq[:, 9], 'r-', label='Q=0')
        plt.plot(mp[:, 0], mp[:, 9], 'b--', label='PF=0.98')
        plt.title('Connection Bus (Bus 9) Voltage Stability')
        plt.legend(); plt.grid(True)
        
        plt.tight_layout()
        plt.savefig('pf_figs/final_comp_pv.png'); plt.close()
        report += "![Final Comp](pf_figs/final_comp_pv.png)\n\n"
        report += "**工程结论**: \n"
        report += "1. 定功率因数控制能通过就地提供无功功率，有效延缓远端电压随出力增加而下降的趋势。\n"
        report += "2. 滞后功率因数 (Lagging PF) 对提升系统静态电压稳定极限有显著贡献。\n"

    with open('pf_comparison_report.md', 'w') as f:
        f.write(report)
    print("Enriched dual-mode report generated.")

if __name__ == "__main__":
    compare()
