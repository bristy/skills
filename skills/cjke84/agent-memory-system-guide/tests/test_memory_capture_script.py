from pathlib import Path
import subprocess
import sys


def run_script(tmp_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / 'scripts' / 'memory_capture.py'
    return subprocess.run(
        [sys.executable, str(script_path), '--workspace', str(tmp_path), *args],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )


def test_bootstrap_creates_missing_memory_files(tmp_path: Path):
    result = run_script(tmp_path, '--generated-at', '2026-03-24T09:30:00+08:00')

    assert result.returncode == 0
    assert (tmp_path / 'SESSION-STATE.md').exists()
    assert (tmp_path / 'working-buffer.md').exists()
    capture_path = tmp_path / 'memory-capture.md'
    assert capture_path.exists()
    capture_text = capture_path.read_text(encoding='utf-8')
    assert 'Generated at: 2026-03-24T09:30:00+08:00' in capture_text
    assert '候选决策' in capture_text


def test_bootstrap_preserves_existing_state_files(tmp_path: Path):
    session_state = tmp_path / 'SESSION-STATE.md'
    working_buffer = tmp_path / 'working-buffer.md'
    session_state.write_text('# SESSION-STATE.md\n\ncustom session\n', encoding='utf-8')
    working_buffer.write_text('# working-buffer.md\n\ncustom buffer\n', encoding='utf-8')

    result = run_script(tmp_path, '--generated-at', '2026-03-24T10:00:00+08:00')

    assert result.returncode == 0
    assert session_state.read_text(encoding='utf-8') == '# SESSION-STATE.md\n\ncustom session\n'
    assert working_buffer.read_text(encoding='utf-8') == '# working-buffer.md\n\ncustom buffer\n'
