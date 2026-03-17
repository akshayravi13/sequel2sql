"""
Tests for the pydantic-ai-skills SkillsToolset integration.

Verifies skill discovery, loading, and the get_db_skill_hint() helper
without requiring a live database connection.
"""

from pathlib import Path

from pydantic_ai_skills import SkillsToolset

SKILLS_DIR = Path(__file__).parent.parent / "src" / "skills"


def test_skill_discovery():
    """SkillsToolset discovers all expected skills in the skills directory."""
    toolset = SkillsToolset(directories=[str(SKILLS_DIR)])
    skill_names = list(toolset.skills.keys())
    assert "db-query" in skill_names, f"db-query skill not found. Found: {skill_names}"
    assert "california-schools-template-semantic-model" in skill_names, (
        f"california-schools-template-semantic-model not found. Found: {skill_names}"
    )


def test_skill_loading():
    """Loading the california schools skill returns its full content."""
    toolset = SkillsToolset(directories=[str(SKILLS_DIR)])
    skill = toolset.get_skill("california-schools-template-semantic-model")
    content = skill.content
    assert "Key Concepts" in content
    assert "Gotchas" in content
    assert "Core Join Paths" in content


def test_base_skill_loading():
    """Loading the db-query base skill returns its content."""
    toolset = SkillsToolset(directories=[str(SKILLS_DIR)])
    skill = toolset.get_skill("db-query")
    content = skill.content
    assert "Safety Rules" in content
    assert "Query Quality" in content


def test_db_skill_hint_present():
    """get_db_skill_hint returns a load_skill hint when a skill exists for the DB."""
    from src.agent.skills_config import get_db_skill_hint

    hint = get_db_skill_hint("california_schools_template")
    assert hint != ""
    assert "load_skill" in hint
    assert "california-schools-template-semantic-model" in hint


def test_db_skill_hint_absent():
    """get_db_skill_hint returns empty string when no skill exists for the DB."""
    from src.agent.skills_config import get_db_skill_hint

    hint = get_db_skill_hint("nonexistent_db")
    assert hint == ""


def test_agent_no_regression():
    """skills_config module imports cleanly and exposes expected names."""
    from src.agent.skills_config import get_db_skill_hint, skills_toolset

    assert skills_toolset is not None
    assert callable(get_db_skill_hint)
