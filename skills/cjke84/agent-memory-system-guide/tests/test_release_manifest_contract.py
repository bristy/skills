from pathlib import Path


def test_skill_uses_canonical_openclaw_name():
    repo_root = Path(__file__).resolve().parents[1]
    skill_text = (repo_root / 'SKILL.md').read_text(encoding='utf-8')

    assert 'name: memory-system' in skill_text
    assert 'Use when' in skill_text


def test_manifest_exists_for_publish_workflows():
    repo_root = Path(__file__).resolve().parents[1]
    manifest_text = (repo_root / 'manifest.toml').read_text(encoding='utf-8')

    for token in [
        'name = "Agent Memory System Guide"',
        'slug = "agent-memory-system-guide"',
        'version = "1.0.10"',
        'skill_id = "14ff5aad-4df3-4b33-ba0b-6cc217cdb939"',
        '[openclaw]',
        '[clawhub]',
    ]:
        assert token in manifest_text
