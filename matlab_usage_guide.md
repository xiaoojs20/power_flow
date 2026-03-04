# MATLAB in Antigravity 使用指南

本文档解释了如何在 Antigravity 环境中成功运行 MATLAB 脚本及 Case 文件。

## 1. MATLAB 路径配置

在本地 macOS 环境中，MATLAB 的执行路径通常为：
```bash
/Applications/MATLAB_R2024a.app/bin/matlab
```
> [!TIP]
> 如果你的版本不同（如 R2023b），请相应修改路径。

## 2. 推荐的运行命令

为了在终端（Headless 模式）下稳定运行，建议使用 `-batch` 参数。该参数会自动禁用 GUI 并简化输出。

### 运行脚本示例
```bash
/Applications/MATLAB_R2024a.app/bin/matlab -batch "your_script_name"
```
*注意：脚本名称不需要 `.m` 后缀，且脚本必须在当前工作目录下。*

### 运行单条命令示例
```bash
/Applications/MATLAB_R2024a.app/bin/matlab -batch "x = 1+1; disp(x);"
```

---

## 3. 常见问题排查

### 3.1 `Unable to load ApplicationService for command client-v1`
**现象**: 运行开始时终端输出多行此类警告。
**原因**: 这是 macOS 版 MATLAB 在 Headless 模式下尝试初始化某些系统服务（如 WindowServer）时产生的警告。
**解决方法**: 
- 通常这是**良性警告**，不影响计算。在输出这些警告后，MATLAB 可能需要 15-30 秒进行初始化，请耐心等待。
- **验证成功案例**: 用户在本地成功通过 `-batch` 模式运行。即使看到 `WARNING: package sun.awt.X11 not in java.desktop`，只要出现结果输出即代表运行成功。

### 3.2 潮流计算 (MATPOWER) 运行
由于本地环境权限差异，建议你在本地手动执行我为你准备好的潮流计算脚本：
```bash
/Applications/MATLAB_R2024a.app/bin/matlab -batch "run_pf_matlab"
```
运行后会生成 `results_matlab.json`，之后你可以使用 Python 脚本进行指标比对。

---

## 4. 与 Python (PYPOWER) 的切换

如果你发现 MATLAB 在某些复杂环境下初始化过慢，可以无缝切换到 PYPOWER：
1. **环境**: 使用 `python3 -m venv power_venv`。
2. **安装**: `pip install pypower`。
3. **运行**: 直接使用 Python 调用你的 Case 转换脚本。

详细对比请参考 [low_freq_system_py.md](file:///Users/xiaojs20/Course/新能源工作室/vibe_grid/low_freq_system_py.md)。
