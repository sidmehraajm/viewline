"""
AYON connectivity + shape self-test for Viewline.

Run this BEFORE launching the GUI to confirm the AYON integration works against
your server and to see the real data shapes. It prints, for the first project it
finds: projects, folders/tasks/products counts, a sample version, its
representations (raw file paths + resolved local paths), and a sample of
activities (review comments).

Usage (from the repo folder, using the venv python):

    set AYON_SERVER_URL=http://ayon:5000
    set AYON_API_KEY=c8e65fba4bfc4de1a5021656680776d0
    .venv\\Scripts\\python.exe scripts\\ayon_selftest.py

Or simply run run-viewline.bat's env first. Nothing here writes to AYON.
"""

from __future__ import absolute_import

import os
import json
import pprint

# Allow running as a loose script: make "viewline" importable.
_HERE = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.dirname(os.path.dirname(_HERE))
if _PARENT not in os.sys.path:
    os.sys.path.insert(0, _PARENT)

from viewline.scripts import ayon_provider as ap  # noqa: E402


def _line(title):
    print("\n" + "=" * 8 + " " + title + " " + "=" * 8)


def main():
    _line("CONNECT")
    ayon = ap._connect()
    print("Server:", os.getenv("AYON_SERVER_URL"))

    _line("PROJECTS")
    projects = ap.Projects.get()
    print("count:", len(projects))
    for p in projects[:10]:
        print("  -", p["id"], "|", p["name"], "| code:", p["code"])
    if not projects:
        print("No projects returned. Check API key permissions.")
        return

    project = projects[0]
    project_name = project["ayon_name"]

    _line("ROOTS for %s" % project_name)
    roots = ap._resolve_roots(project_name)
    print(json.dumps(roots, indent=2))

    _line("RAW COUNTS")
    folders = list(ayon.get_folders(project_name))
    tasks = list(ayon.get_tasks(project_name))
    products = list(ayon.get_products(project_name))
    print("folders:", len(folders), "tasks:", len(tasks), "products:", len(products))

    _line("SHOTS (folders) ")
    shots = ap.Shots.get(project)
    print("count:", len(shots))
    for s in shots[:10]:
        print("  -", s.get("path") or s.get("name"))

    _line("TASKS (all) ")
    tasks_list = ap.Tasks.get(project)
    print("count:", len(tasks_list))
    for t in tasks_list[:10]:
        print("  -", t.get("name"))

    _line("SAMPLE VERSION (reviewable) ")
    versions = ap.Versions.get(project)
    print("reviewable versions:", len(versions))
    if versions:
        v = versions[0]
        pprint.pprint(v)

        _line("RAW REPRESENTATIONS for that version")
        for rep in ayon.get_representations(project_name, version_ids=[v["ayon_id"]]):
            files = rep.get("files") or []
            print("  rep name:", rep.get("name"), "| files:", len(files))
            for f in files[:3]:
                raw = f.get("path", "")
                print("      raw :", raw)
                print("      real:", ap._apply_roots(raw, roots))

        _line("ACTIVITIES (review comments) for that version")
        ok, notes = ap.Review.get(v, reverse=True)
        print("has notes:", ok, "| count:", len(notes or []))
        if notes:
            pprint.pprint(notes[0])
    else:
        print("No reviewable versions found. If you expected some, the media")
        print("filter may be too strict, or representations have no playable ext.")

    _line("DONE")
    print("If media 'real' paths above exist on disk, the GUI will play them.")


if __name__ == "__main__":
    main()
