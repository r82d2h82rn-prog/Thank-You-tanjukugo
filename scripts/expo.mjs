import { spawn } from 'node:child_process';
// This project needs no Expo account or remote API to run locally.
const child = spawn(process.execPath, ['node_modules/expo/bin/cli', ...process.argv.slice(2)], {
  stdio: 'inherit', env: { ...process.env, EXPO_NO_TELEMETRY: '1', EXPO_OFFLINE: '1' },
});
child.on('exit', code => process.exit(code ?? 1));
