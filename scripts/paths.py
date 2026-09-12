"""Project paths. Every other script in this project imports from here.

Finds the project by searching upward for the .project-root marker, the way
git finds a repository, so nothing breaks when the folder is moved, renamed,
synced or copied to another machine.
"""

from pathlib import Path

MARKER_FILENAME = ".project-root"


def _find_project_root(start):
    for folder in [start, *start.parents]:
        if (folder / MARKER_FILENAME).exists():
            return folder
    return None


SCRIPTS_DIR = Path(__file__).resolve().parent
_found = _find_project_root(SCRIPTS_DIR)
PROJECT_ROOT = _found if _found else SCRIPTS_DIR.parent
ROOT_WAS_FOUND_BY_MARKER = _found is not None

DRAFTS = PROJECT_ROOT / "drafts"
DATA = PROJECT_ROOT / "data"
ANALYSIS = PROJECT_ROOT / "analysis"
TOOLS = PROJECT_ROOT / "tools"
PREREG = PROJECT_ROOT / "prereg"
REFERENCE = PROJECT_ROOT / "reference"
SKILLS = PROJECT_ROOT / "skills"


def require_project(*needed):
    """Guard. Call before anything that overwrites, moves or deletes."""
    import sys
    if not ROOT_WAS_FOUND_BY_MARKER:
        sys.exit(f"Refusing to run: no '{MARKER_FILENAME}' found above {PROJECT_ROOT}")
    missing = [n for n in needed if not (PROJECT_ROOT / n).is_dir()]
    if missing:
        sys.exit(f"Refusing to run: {PROJECT_ROOT} is missing: {', '.join(missing)}")


def describe():
    print(f"project root      {PROJECT_ROOT}")
    print(f"found by marker   {'yes' if ROOT_WAS_FOUND_BY_MARKER else 'NO, guessed from script location'}")
    for name, path in [("drafts", DRAFTS), ("data", DATA), ("analysis", ANALYSIS),
                       ("tools", TOOLS), ("prereg", PREREG), ("reference", REFERENCE),
                       ("skills", SKILLS)]:
        print(f"  {name:12s} {'ok     ' if path.is_dir() else 'MISSING'} {path}")


if __name__ == "__main__":
    describe()
