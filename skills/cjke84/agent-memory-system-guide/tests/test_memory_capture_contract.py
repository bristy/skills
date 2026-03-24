from pathlib import Path


def test_skill_mentions_memory_capture_flow():
    repo_root = Path(__file__).resolve().parents[1]
    skill_text = (repo_root / 'SKILL.md').read_text(encoding='utf-8')

    assert '任务结束 30 秒记录流程' in skill_text
    assert '候选记忆' in skill_text
    assert 'memory-capture.md' in skill_text


def test_memory_capture_template_exists():
    repo_root = Path(__file__).resolve().parents[1]
    template_text = (repo_root / 'templates' / 'memory-capture.md').read_text(encoding='utf-8')

    assert '候选决策' in template_text
    assert '候选踩坑' in template_text
    assert '候选长期记忆' in template_text
