"""
Skills configuration for the sequel2sql agent.

Separated from sqlagent.py so it can be imported independently
(e.g., in tests) without pulling in the full agent dependency chain.
"""

from pathlib import Path

from pydantic_ai_skills import SkillsToolset

SKILLS_DIR = Path(__file__).parent.parent / "skills"

skills_toolset = SkillsToolset(directories=[str(SKILLS_DIR)])

# Normalize resource names to use forward slashes (Windows path separator fix).
# pydantic_ai_skills uses str(Path) which produces backslashes on Windows,
# but SKILL.md documents resources with forward slashes.
for _skill in skills_toolset._skills.values():
	if _skill.resources:
		for _resource in _skill.resources:
			_resource.name = _resource.name.replace("\\", "/")


def get_db_skill_instructions(db_identifier: str) -> str:
	"""
	Return skill instructions filtered to only what's relevant for this database.

	Replaces the previous pattern of calling skills_toolset.get_instructions()
	(which listed ALL 11 skills) and then appending get_db_skill_hint().
	This version emits only the error-taxonomy skill and the DB-specific
	semantic model, saving ~350-400 tokens of irrelevant context per run.
	"""
	normalized = db_identifier.replace("_", "-").lower()
	db_skill_name = f"{normalized}-semantic-model"
	relevant_names = {db_skill_name}

	relevant_skills = {
		name: skill
		for name, skill in skills_toolset._skills.items()
		if name in relevant_names
	}

	if not relevant_skills:
		return ""

	# Build XML skill list — same format as pydantic_ai_skills._INSTRUCTION_SKILLS_HEADER
	skills_list_lines: list[str] = []
	for skill in sorted(relevant_skills.values(), key=lambda s: s.name):
		skills_list_lines.append("<skill>")
		skills_list_lines.append(f"<name>{skill.name}</name>")
		skills_list_lines.append(f"<description>{skill.description}</description>")
		if skill.uri:
			skills_list_lines.append(f"<uri>{skill.uri}</uri>")
		skills_list_lines.append("</skill>")
	skills_list = "\n".join(skills_list_lines)

	instructions = (
		"You have access to skills containing domain-specific knowledge and "
		"capabilities.\n\n"
		f"<available_skills>\n{skills_list}\n</available_skills>\n\n"
		"Use `load_skill(<name>)` to load full skill instructions. "
		"Load only what you need, when you need it."
	)

	if db_skill_name in relevant_skills:
		instructions += (
			f"\n\n**IMPORTANT**: A semantic model skill is available for "
			f"database '{db_identifier}'. Before writing SQL, call "
			f"`load_skill('{db_skill_name}')` to load business definitions, "
			f"metrics, and known patterns. Prefer the semantic model when available."
		)

	return instructions
