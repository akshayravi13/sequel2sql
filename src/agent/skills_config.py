"""
Skills configuration for the sequel2sql agent.

Separated from sqlagent.py so it can be imported independently
(e.g., in tests) without pulling in the full agent dependency chain.
"""

from pathlib import Path

from pydantic_ai_skills import SkillsToolset

SKILLS_DIR = Path(__file__).parent.parent / "skills"

skills_toolset = SkillsToolset(directories=[str(SKILLS_DIR)])


def get_db_skill_hint(db_identifier: str) -> str:
	"""Return an instruction to load the DB skill if one exists, else empty string."""
	normalized = db_identifier.replace("_", "-").lower()
	skill_dir = SKILLS_DIR / f"{normalized}-semantic-model"
	if (skill_dir / "SKILL.md").exists():
		return (
			f"\n\n**IMPORTANT**: A semantic model skill is available for "
			f"database '{db_identifier}'. Before writing SQL, call "
			f"`load_skill('{normalized}-semantic-model')` to load business "
			f"definitions, metrics, and known patterns. Prefer the semantic "
			f"model when available.\n"
		)
	return ""
