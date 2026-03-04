function run_pf_matlab()
    % Run power flow for multiple scenarios in MATPOWER
    addpath(pwd);
    
    scenarios = struct();
    % 1. Standard (100%)
    scenarios.standard = [200, 100, 200, 100, 100, 100, 100, 100];
    % 2. Low Load (30%)
    scenarios.low = scenarios.standard * 0.3;
    % 3. Heavy Load (110%)
    scenarios.heavy = scenarios.standard * 1.1;
    % 4. Contingency (WF1 Out)
    scenarios.trip = scenarios.standard;
    scenarios.trip(1) = 0;
    
    names = fieldnames(scenarios);
    all_results = struct();
    
    modes = struct('q_const', 0, 'pf_const', 1);
    mode_names = fieldnames(modes);
    
    for m = 1:length(mode_names)
        mode_name = mode_names{m};
        mode_val = modes.(mode_name);
        all_results.(mode_name) = struct();
        
        fprintf('Processing Mode: %s\n', mode_name);
        
        for i = 1:length(names)
            name = names{i};
            Ps = scenarios.(name);
            try
                mpc = build_case_lfreq(Ps, mode_val);
                res = runpf(mpc, mpoption('verbose', 0, 'out.all', 0));
                
                output = struct();
                output.success = res.success;
                output.bus = res.bus;
                output.gen = res.gen;
                output.branch = res.branch;
                
                all_results.(mode_name).(name) = output;
                fprintf('  Scenario %s processed.\n', name);
            catch ME
                fprintf('  Error in scenario %s: %s\n', name, ME.message);
            end
        end
        
        % P-V Sweep for each mode
        sweep_results = [];
        for scale = 0.1:0.1:1.5
            Ps_sweep = scenarios.standard * scale;
            try
                mpc_s = build_case_lfreq(Ps_sweep, mode_val);
                res_s = runpf(mpc_s, mpoption('verbose', 0, 'out.all', 0));
                if res_s.success
                   sweep_results = [sweep_results; scale, res_s.bus(:, 8)'];
                end
            catch
            end
        end
        all_results.(mode_name).sweep = sweep_results;
    end
    
    % Save to results_matlab.json
    fid = fopen('results_matlab.json', 'w');
    fprintf(fid, '%s', jsonencode(all_results));
    fclose(fid);
end
