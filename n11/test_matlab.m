function test_matlab()
    fprintf('MATLAB is running successfully.\n');
    fprintf('Current Version: %s\n', version);
    fprintf('Current Path: %s\n', pwd);
    x = randn(2,2);
    disp('Matrix calculation test:');
    disp(x);
    exit;
end
