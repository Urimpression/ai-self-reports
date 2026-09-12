"""Write out the coding rules exactly as they were sent to the coders.

A reader who wants to judge a coding rule should not have to read Python to
find it. This script pulls the rule text out of the settings file that each
coding pass wrote at the time it ran, so the page cannot drift from what was
actually sent.

Run it with:  python3 scripts/build_coding_rules_doc.py
"""

import json
from collections import OrderedDict

from paths import PROJECT_ROOT, ANALYSIS, require_project

OUTPUT = PROJECT_ROOT / "public" / "coding-rules.md"

# One coding folder is named for each rule, so that the page shows each rule
# once rather than once per run. Any folder using the same rule text is listed
# beside it.
NOT_THE_PILOT = {"factorial-01", "gemini-02", "gemini-budget-test"}


def main():
    require_project("analysis", "scripts")

    rules = OrderedDict()
    for folder in sorted((ANALYSIS / "coding").iterdir()):
        if not folder.is_dir() or folder.name in NOT_THE_PILOT:
            continue
        settings_path = folder / "settings.json"
        if not settings_path.exists():
            continue
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
        rule_text = settings.get("rule")
        if not rule_text:
            continue
        name = settings.get("rule_name", "registered")
        coder = settings.get("coder", {})
        # Two folders can carry the same rule text under the same name, coded
        # by different model families. Group by the text itself so that a
        # difference in wording can never hide behind a shared name.
        key = (name, rule_text)
        entry = rules.setdefault(key, {"folders": [], "coders": set(),
                                       "features": settings.get("features", [])})
        entry["folders"].append(folder.name)
        entry["coders"].add(f"{coder.get('provider', '?')} / {coder.get('model', '?')} "
                            f"at temperature {coder.get('temperature', '?')}")

    lines = [
        "# The coding rules, as they were sent",
        "",
        "Every rule below is the text a coder actually received, taken from the "
        "settings file each coding pass wrote when it ran. Nothing here is a "
        "description of a rule; it is the rule.",
        "",
        f"There are {len(rules)} distinct rule texts across the pilot's coding passes.",
        "",
    ]

    for index, ((name, text), entry) in enumerate(rules.items(), start=1):
        lines += [
            f"## Rule {index}: {name}",
            "",
            f"Answers recorded: {', '.join(entry['features']) if entry['features'] else 'not recorded'}.",
            "",
            "Coders that ran it:",
            "",
        ]
        lines += [f"- {coder}" for coder in sorted(entry["coders"])]
        lines += ["", "Coding folders that used it:", ""]
        lines += [f"- `analysis/coding/{folder}`" for folder in sorted(entry["folders"])]
        lines += ["", "The text sent to the coder:", "", "```", text.rstrip(), "```", ""]

    OUTPUT.parent.mkdir(exist_ok=True)
    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUTPUT.relative_to(PROJECT_ROOT)} with {len(rules)} rules")


if __name__ == "__main__":
    main()
