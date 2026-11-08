"""Exercise credential staging using a synthetic key and no provider calls."""
from pathlib import Path
import os
import stat
import subprocess
import yaml


def test_workflow_stages_literal_key_and_removes_it_on_exit(tmp_path):
    workflow = yaml.safe_load((Path(__file__).parents[1] / '.github/workflows/data_pipeline.yml').read_text())
    step = next(s for s in workflow['jobs']['run-pipeline']['steps'] if s['name'] == 'Run Data Pipeline')
    assert step['env']['EE_KEY_JSON'] == '${{ secrets.EE_KEY_JSON }}'
    assert '${{ secrets.' not in step['run']
    key = '{"fake_key": "a\'b\\nc$(touch should-not-exist)"}'
    target = tmp_path / 'synthetic-key.json'
    env = {**os.environ, 'EE_KEY_JSON': key, 'GOOGLE_APPLICATION_CREDENTIALS': str(target)}
    # Replace only the provider invocation with local filesystem/env checks.
    check = '''test -z "${EE_KEY_JSON+x}"
test -f "$GOOGLE_APPLICATION_CREDENTIALS"
cp "$GOOGLE_APPLICATION_CREDENTIALS" "$GOOGLE_APPLICATION_CREDENTIALS.observed"
stat -c '%a' "$GOOGLE_APPLICATION_CREDENTIALS" > "$GOOGLE_APPLICATION_CREDENTIALS.mode"'''
    script = step['run'].replace('python scripts/generate_dashboard_data.py', check)
    assert script != step['run']
    result = subprocess.run(['bash', '-c', script], cwd=tmp_path, env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert not target.exists()
    assert (tmp_path / 'synthetic-key.json.observed').read_text() == key
    assert (tmp_path / 'synthetic-key.json.mode').read_text().strip() == '600'
    assert not (tmp_path / 'should-not-exist').exists()
