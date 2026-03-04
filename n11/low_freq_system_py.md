# 低频交流输电系统 (PYPOWER 版本) 技术文档

本文档详细说明了将 MATPOWER `case_lf_new.m` 系统无缝切换至 PYPOWER 的过程、数据结构对比及参数一致性说明。

## 1. 数据结构对比 (MATPOWER vs PYPOWER)

PYPOWER 是 MATPOWER 的 Python 端移植，其核心数据结构（基于 NumPy 数组）与 MATPOWER 矩阵保持高度一致。

| 项 (Item) | MATPOWER (MATLAB) | PYPOWER (Python/NumPy) | 说明 |
| :--- | :--- | :--- | :--- |
| 对象类型 | `struct` | `dict` | PYPOWER case 是一个字典 |
| 矩阵索引 | 1-based (1, 2, 3...) | 0-based (0, 1, 2...) | **注意: Python 索引从 0 开始** |
| 节点数据 | `mpc.bus` (矩阵) | `ppc['bus']` (ndarray) | 字段定义完全相同 |
| 发电机数据 | `mpc.gen` (矩阵) | `ppc['gen']` (ndarray) | 字段定义完全相同 |
| 支路数据 | `mpc.branch` (矩阵) | `ppc['branch']` (ndarray) | 字段定义完全相同 |

### 1.1 索引定义
在 PYPOWER 中，我们通过以下模块获取标准索引：
```python
from pypower.idx_bus import BUS_I, BUS_TYPE, PD, QD, ...
from pypower.idx_gen import GEN_BUS, PG, QG, PMAX, ...
from pypower.idx_brch import F_BUS, T_BUS, BR_R, BR_X, ...
```

---

## 2. PYPOWER Case 生成逻辑 (`case_lf_py.py`)

Python 版本的参数计算逻辑与 MATLAB 版本完全同步：

### 2.1 阻抗计算 (Impedance)
利用 NumPy 的向量化执行线路阻抗计算：
```python
r_norm = r_h2b_norm * lens / 265
x_norm = (lens * xs_unit / Zb + 
          0.14 * Zb_trm_main / Zb + 
          0.075 * Zb_trm_turb / Zb * (230**2 / 37**2) / (Ps / 6.0))
```
- **关键差异**: 在 Python 中，数组切片 `gen[0:8]` 对应 MATLAB 的 `gen(1:8, :)`。

### 2.2 变压器建模
变压器变比 $Tap$ 在 PYPOWER 的支路矩阵第 9 列（索引为 8, `TAP`）进行配置。
- 默认为 1.0 (表示额定变比)。
- 在潮流计算前后，会根据电压标幺值进行动态调整以模拟分接头。

---

## 3. 运行环境说明

- **虚拟环境**: `power_venv`
- **主要依赖**: `pypower`, `numpy`, `scipy`
- **运行方式**:
  ```bash
  source ./power_venv/bin/activate
  python case_lf_py.py
  ```

---

## 4. 转换风险提示

1.  **节点索引一致性**: 虽然 Python 是 0-based，但 `ppc['bus']` 的第一列（`BUS_I`）通常仍保留原始的节点编号（1, 2, 3...）。在定义支路 `F_BUS` 和 `T_BUS` 时，必须确保引用的是正确的节点 ID 而非数组索引。
2.  **精度差异**: NumPy (Float64) 与 MATLAB (Double) 在极少数边缘情况下可能存在极其微小的舍入误差，需在 `pf_report.md` 中进行比对验证。

---
> **后续计划**: 下一步将运行 `run_pf_matlab.m` 和 `run_pf_pypower.py` 并生成详细结果对比报告。
