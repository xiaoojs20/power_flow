---
description: How to run MATLAB from the terminal on macOS within Antigravity
---

# Running MATLAB from Terminal (macOS)

This workflow provides instructions on how to execute MATLAB scripts and functions from the terminal, which is the standard way to integrate MATLAB with Antigravity.

## Prerequisite
MATLAB must be installed in the `/Applications` folder. The standard path for R2024a is:
`/Applications/MATLAB_R2024a.app/bin/matlab`

## Usage Modes

### 1. Batch Mode (Recommended)
Use the `-batch` flag for non-interactive execution of scripts or statements. This mode is the most stable and automatically handles headless execution.

**// turbo**
```bash
/Applications/MATLAB_R2024a.app/bin/matlab -batch "your_script_name"
```
*Note: Do not include the `.m` extension.*

### 2. Statement Execution
Run a series of MATLAB commands directly from the command line.

**// turbo**
```bash
/Applications/MATLAB_R2024a.app/bin/matlab -batch "x = rand(5); disp(x); exit;"
```

### 3. Command Redirection
If you encounter hangs or need to capture debug information, redirect output and use `-nodisplay`.

**// turbo**
```bash
/Applications/MATLAB_R2024a.app/bin/matlab -nodisplay -nosplash -batch "my_script" > stdout.log 2> stderr.log
```

## Troubleshooting

### "Unable to load ApplicationService" Warning
- **Occurrence**: Common on macOS when running in a headless shell.
- **Handling**: This is usually a non-fatal warning. The process may take 15-30 seconds to initialize. Do not terminate the command immediately; wait for the output.

### Version Differences
If you have a different version of MATLAB, locate the binary using:
```bash
mdfind "kind:app MATLAB" | grep MATLAB
```
And replace the path in the commands above.

## External Documentation
For more details, refer to the [official MathWorks documentation](https://ww2.mathworks.cn/help/matlab/ref/matlabmacos.html).
