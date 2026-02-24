try {
    const { execSync } = require('child_process');
    const output = execSync('npx next build', { encoding: 'utf-8', stdio: 'pipe' });
    require('fs').writeFileSync('build_output.txt', output);
} catch (e) {
    require('fs').writeFileSync('build_output.txt', e.stdout + e.stderr);
}
