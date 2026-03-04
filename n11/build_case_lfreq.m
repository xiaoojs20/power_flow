function mpc = build_case_lfreq(Ps, control_mode)
    % 构建自定义低频潮流系统 mpc 数据结构
    % Ps: 风电场有功出力 (MW)
    % control_mode: 0 - Constant Q (Q=0), 1 - Constant PF (0.98 lagging)
    % 返回：mpc 结构体，可直接用于 runpf
        if nargin < 1 || isempty(Ps)
            Ps = [200, 100, 200, 100, 100, 100, 100, 100]; 
        end
        if nargin < 2 || isempty(control_mode)
            control_mode = 1; % Default to Constant PF
        end
        %% ========== 基准容量等数据 ==========
        Ub = 230e3;         % 220kV
        Sb = 1000e6;        % 1000MVA
        Zb = Ub^2 / Sb;
        fb = 20;            % Hz
    
        %% 风电场有功容量 & SVG 无功容量
        Ps_max = [200, 100, 200, 100, 100, 100, 100, 100];             % MW
        SVGs = [46, 23, 47, 23, 22, 23, 23, 26];                   % Mvar
        Ps_norm = Ps_max * 1e6 / Sb;
        Qs_norm = SVGs * 1e6 / Sb;
    

        %% 汇集到变频站线路参数（双回线）
        len_h2b = 265;
        % r_h2b = 0.02317;
        % x_h2b = 2 * pi * fb * 9.52E-04;
        b_h2b = 2 * pi * fb * 1.20E-08;
        % 
        % r_h2b_norm = len_h2b * r_h2b / Zb;
        % x_h2b_norm = len_h2b * x_h2b / Zb;
        % b_h2b_norm = len_h2b * b_h2b / Zb;
        
        r_h2b_norm = 3.737314 / Zb;
        x_h2b_norm = 2 * pi * fb * 0.1177 / Zb;
        b_h2b_norm = len_h2b * b_h2b / Zb;

        z_h2b_norm = r_h2b_norm + 1j * x_h2b_norm


        %% 场站到汇集站线路参数（单位：km, Ω/km, H/km, µF/km）
        lens = [9, 24, 24, 10, 24, 10, 10, 16];
        rs = [0.08, 0.108, 0.08, 0.108, 0.108, 0.108, 0.108, 0.108];
   
        xs = 2 * pi * fb * [1.30E-03, 1.34E-03, 1.30E-03, 1.34E-03, ...
                            1.34E-03, 1.34E-03, 1.34E-03, 1.34E-03];
        bs = 10e-6 * 2 * pi * fb * [0.00887075, 0.0086673, 0.00887075, 0.0086673, ...
                                    0.0086673, 0.0086673, 0.0086673, 0.0086673];
    
        % 主变/箱变 Zb
        Zb;
        Zb_trm_main = Ub^2 ./ (Ps_max*1e6);
        Zb_trm_turb = (37*1e3)^2 / (6*1e6);
        
        % 0.14 * Zb_trm_main / Zb
        % 0.075 * Zb_trm_turb / Zb * (230^2 / 37^2) / (100/6) % 0.75
        
        % rs_norm = lens .* rs / Zb
        rs_norm = lens .* rs / Zb;

        xs_norm = lens .* xs / Zb + ...
            0.14 * Zb_trm_main / Zb + ...
            0.075 * Zb_trm_turb / Zb * (230^2 / 37^2) ./ (max(Ps, 1e-6)/6);

        bs_norm = lens .* bs * Zb;
    
   
        %% 变频站参数
        Sm3c = 550;         % MVA
        Qm3c = 460;         % Mvar
        Um3c = 165e3;       % V
        Zb_m3c = Um3c^2 / (Sm3c * 1e6);
    
        % M3C 阻抗等效换算
        S_tmp = 330e6;
        U_tmp = 65e3;
        Zb_tmp = U_tmp^2 / S_tmp;
        L_tmp = 21.5e-3;            % H
        Lm3c = L_tmp / Zb_tmp * Zb_m3c / 2;
        Xm3c = 2 * pi * fb * Lm3c;
        Xm3c_norm = Xm3c / Zb;
    
        %% === 加载基础 mpc 框架 ===
        mpc = loadcase('case_lf_new');
    
        %% === 获取索引 ===
        define_constants;
        
        %% === 修改 branch 参数 ===
        mpc.branch(:, BR_R) = [rs_norm'; r_h2b_norm; 0];
        mpc.branch(:, BR_X) = [xs_norm'; x_h2b_norm; Xm3c_norm];
        mpc.branch(:, BR_B) = [bs_norm'; (len_h2b * b_h2b * Zb); 0];
        mpc.branch(:, TAP) = 0; % ratio = 0 is 1.0 in MATPOWER
        mpc.branch(1:8, TAP) = 1.0; 
        
        % 根据 Ps 设置支路状态 (处理断开工况)
        for i = 1:8
            if Ps(i) <= 1e-3
                mpc.branch(i, BR_STATUS) = 0;
                mpc.gen(i, GEN_STATUS) = 0;
                mpc.bus(i, BUS_TYPE) = 4;  % Isolated
            end
        end
    
        %% === 修改 gen 参数 ===
        ng = size(mpc.gen, 1);
        mpc.gen(1:8, PG) = Ps';
        
        % 控制方式选择
        if control_mode == 1
            % 定功率因数控制 (Constant PF = 0.98 Lagging)
            pf_target = 0.98;
            tan_phi = sqrt(1/pf_target^2 - 1);
            mpc.gen(1:8, QG) = mpc.gen(1:8, PG) * tan_phi;
        else
            % 定无功控制 (Constant Q = 0)
            mpc.gen(1:8, QG) = 0;
        end
        
        mpc.gen(9, PG) = 0; 
        mpc.gen(9, PMAX) = sum(Ps_max);
        mpc.gen(10, PMAX) = Sm3c*2;
        
        mpc.gen(:, PMIN) = zeros(ng, 1);
        mpc.gen(1:8, QMAX) = Ps_max' * 0.65;
        mpc.gen(1:8, QMIN) = -Ps_max' * 0.65;
        
        %% === 修改 gencost 参数 ===
        mpc.gencost = repmat([2, 0, 0, 3, 0.11, 5, 150], ng, 1);
        
    end