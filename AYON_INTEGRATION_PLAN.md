# Viewline → AYON Integration Plan

**Goal:** View all AYON publishes (reviewables) inside Viewline's Review Player, and read/write review notes against AYON — with media read directly from local/mounted studio storage.

**Decisions locked in:**
- Media access: **local / mounted studio storage** (Viewline opens the exr/mov straight from disk; AYON gives us the resolved path).
- Scope: **only reviewables** (product versions that have a reviewable/preview representation).
- Delivery: this document first (no code changes yet).

---

## 1. How Viewline is architected (the seam we use)

Viewline is deliberately built so a studio never touches the player itself — all production data flows through **one file**: `scripts/__init__.py`. It exposes three providers with fixed signatures:

| Class / method | Returns | Feeds |
| --- | --- | --- |
| `Projects.get()` | list of project dicts | Project browser |
| `Versions.get(project)` | list of version/media dicts | Version list + Media player |
| `Review.get(version)` | `(bool, notes)` | Review-notes panel |
| `Review.set(context)` | `(bool, message)` | Submitting a new note |

Today these read/write JSON in `resources/presets/` (and a per-user copy under `VIEW_LINE_PROFILE_ROOT/viewline/schemas/`). **AYON integration = replacing the bodies of these four methods.** Nothing in `widgets/`, `playback/`, or the UI needs to change, as long as we return the same dict shapes.

The rest of this plan is: what data shapes to return, how AYON maps onto them, and how to wire it in cleanly.

---

## 2. The exact data contracts to preserve

These come straight from the sample presets and the player code — the AYON layer must reproduce them.

### 2.1 Project dict (from `Projects.get()`)
```json
{
  "type": "Project",
  "id": 358,
  "code": "SCE",
  "name": "My Super Hero",
  "created_at": "2026-04-26 10:41:45:PM",
  "image": "media/my-super-hero.png",
  "sg_description": null
}
```
- `id` is used to filter versions (`version["project"]["id"] == project["id"]`).
- `created_at` is used for sorting (string in `YYYY-MM-DD hh:mm:ss:AM/PM`, produced by `utils.getDateTimes`).
- `image` is a thumbnail path (resolved relative to the schemas folder today).

### 2.2 Version dict (from `Versions.get()`) — the important one
```json
{
  "type": "Version",
  "id": 2996,
  "code": "Version-0001",
  "project": { "id": 358, "name": "My Super Hero", "type": "Project" },
  "entity": { "id": 1999, "name": "shot-101", "type": "Shot" },
  "sg_task": { "id": 2999, "name": "compositing", "type": "Task" },
  "sg_status_list": "rev",
  "description": "pipeline test",
  "created_at": "2026-03-16 05:29:13:PM",
  "created_by": { "id": 34, "name": "workspace 0.0.1", "type": "ApiUser" },
  "image": "media/shot-101.png",
  "media": "media/shot-101/render.####.exr"
}
```
- `media` is what the player opens. Sequences use the `####` frame token; movies are a single file. **This must be an absolute local path once AYON resolves roots.**
- Optional `usd` key (same shape as `media`) for USD scene review.
- `image` is the thumbnail.
- `sg_status_list`, `sg_task`, `entity` are echoed back when writing notes, so keep them populated.

### 2.3 Review note dicts (from `Review.get()` / `Review.set()`)
Notes carry `note_links` (linking a note to a Version id), `replies`, `attachments`, `sg_status_list`, `sg_review_type`. `Review.set()` also flips the version's status. AYON's equivalent is **activities/comments** on the version entity plus a **status change**.

---

## 3. AYON → Viewline field mapping

AYON's publish chain is `project → folder (shot/asset) → task` and `product → version → representation`, with **reviewables** attached to a version. Mapping:

| Viewline field | AYON source |
| --- | --- |
| Project `id` | project `name` is AYON's key; keep AYON `name` as `code`, use a stable hash or the name itself as `id` |
| Project `name` | project `attrib.fullname` (fallback: `name`) |
| Project `code` | project `code` |
| Project `image` | project thumbnail (or none) |
| Version `id` | version entity `id` (AYON uses string UUIDs — see §5 note) |
| Version `code` | `{product_name} v{version:0>3}` (e.g. `renderCompositingMain v005`) |
| Version `project` | `{id, name, type:"Project"}` |
| Version `entity` | folder → `{id: folder.id, name: folder.name, type: folder.folderType}` |
| Version `sg_task` | task → `{id: task.id, name: task.name, type:"Task"}` |
| Version `sg_status_list` | version `status` |
| Version `description` | version `attrib.comment` / `data` |
| Version `created_at` | version `createdAt` → reformat to Viewline's datetime string |
| Version `created_by` | version `author` |
| Version `image` | version thumbnail (`get_thumbnail`), cached to a local temp file |
| Version `media` | **resolved local path** of the reviewable/preview representation (see §4) |
| Note (`Review.get`) | version **activities** of type `comment` |
| New note (`Review.set`) | `create_activity(... activity_type="comment")` + `update_version(status=...)` |

**"Only reviewables" filter:** query versions, then keep those that have a reviewable. Two ways:
1. `get_reviewables_for_version(project_name, version_id)` returns the reviewable list — keep versions where this is non-empty.
2. Or filter representations by name/tag (e.g. `review`, `mov`, `mp4`, `exr`) and keep versions that have one.

Recommended: use reviewables as the primary signal, fall back to a representation whitelist.

---

## 4. Resolving media to a local path (the "mounted storage" case)

A representation's `files` each carry a `path` that is **root-templated**, e.g. `{root[work]}/SCE/shot-101/publish/render/renderMain/v005/SCE_shot-101_renderMain_v005.####.exr`.

To turn that into a real disk path:
1. Get the project's roots for this site: `ayon_api.get_project_roots_for_site(project_name, site_id)` (or `get_project_roots_by_site`). This returns `{"work": "P:/projects", ...}` per the studio's storage mounts.
2. Substitute the `{root[...]}` token into each file `path`.
3. For **sequences**, collapse the per-frame files back into Viewline's `####` token (AYON stores one file entry per frame, or a single templated entry — handle both: if multiple frames, replace the frame number with `####`).
4. For **movies/single-file reviewables**, use the path directly.

For the **thumbnail** (`image`): AYON serves thumbnails via the API, not disk. `ayon_api.get_thumbnail(...)` → write bytes to a local cache file under `VIEW_LINE_PROFILE_ROOT/viewline/cache/` → return that path. (This is the one place we still pull from the server, since thumbnails aren't on the studio mount.)

**Edge cases to handle:** representation with no local file present (offline media) → skip or mark; mixed slashes on Windows (normalize with `utils.pathResolver`); reviewable that is a transcoded mp4 living in the AYON storage root vs. the raw published exr — decide which one Viewline should open (recommend: prefer the mp4/mov reviewable for smooth playback, offer the exr as an AOV/high-res toggle later).

---

## 5. Implementation approach (recommended structure)

Even though delivery is "plan first," here is the concrete shape the code should take so you can green-light it.

**Add a new module `scripts/providers/ayon.py`** with a small client wrapper, and make `scripts/__init__.py` delegate to either the JSON demo provider or the AYON provider based on an env var. This keeps the sample mode working (useful for demos/tests) and isolates all AYON specifics.

```
scripts/
  __init__.py          # thin dispatcher: picks backend, same 4 methods
  providers/
    json_demo.py       # today's JSON logic, moved verbatim
    ayon.py            # new: ayon_api-backed implementation
```

Dispatch rule: if `VIEWLINE_BACKEND == "ayon"` (or `AYON_SERVER_URL` is set), use `ayon.py`; else JSON. This means **zero behavior change** for anyone running the demo.

### 5.1 Auth / connection
AYON auth uses two env vars, already the AYON standard:
- `AYON_SERVER_URL`
- `AYON_API_KEY` (a service/API key) — or an interactive login token.

The provider calls `ayon_api.init_service()` / `ayon_api.get_server_api_connection()` once and reuses it. Add these to a copy of `call-win.bat` alongside the existing OCIO/USD vars.

### 5.2 Method-by-method

**`Projects.get()`** → `ayon_api.get_projects(active=True)`; map each to the project dict; sort by `createdAt` desc.

**`Versions.get(project)`** →
1. `get_folders(project_name)` and `get_tasks(project_name)` (build id→name/type lookup maps).
2. `get_products(project_name)` for product name + type (+ optional product-type filter).
3. `get_versions(project_name, ...)` (latest or all — recommend latest per product, plus hero).
4. For each version, check reviewables; keep only those with one.
5. Resolve the reviewable representation to a local `media` path (§4); fetch thumbnail to `image`.
6. Assemble the version dict; sort by `createdAt` desc.

**`Review.get(version)`** → `get_activities(project_name, entity_ids=[version_id], activity_types=["comment"])`; shape into Viewline's note/reply/attachment structure. Map AYON comment author/body/createdAt onto `created_by` / `content` / `created_at`.

**`Review.set(context)`** →
1. `create_activity(project_name, version_id, activity_type="comment", body=context["message"])`.
2. If status changed: `update_version(project_name, version_id, status=context["status"]["value"])` (map Viewline status codes → AYON status names — see §6).
3. Handle attachments: `upload_reviewable()` or attach files to the activity (AYON supports file attachments on activities).
4. Return `(True, message)` in the same format.

### 5.3 The `id` type mismatch (important)
Viewline assumes **integer** ids (used in filtering and note-linking). AYON uses **string UUIDs**. Two clean options:
- **A (recommended):** keep AYON's real UUID in a parallel key (e.g. `ayon_id`) and generate a stable integer `id` via a deterministic hash of the UUID for Viewline's internal use. All AYON calls use `ayon_id`; all Viewline internals use `id`.
- **B:** loosen Viewline's comparisons to treat ids as strings (small change, but touches more than just `scripts/`).

Option A keeps the "don't modify the player" guarantee.

---

## 6. Status mapping

Viewline uses ShotGrid-style short codes (`rev`, `apr`, `ip`, etc.) in `sg_status_list`. AYON projects define their own statuses (`In Progress`, `Pending Review`, `Approved`, ...). Build a small bidirectional map in the provider, sourced from `get_project_status(...)` / project anatomy statuses, so:
- reading: AYON status → nearest Viewline code (for display/colour).
- writing: Viewline status choice → AYON status name.

This map is the one studio-specific bit worth confirming against your actual AYON status list.

---

## 7. Open questions to confirm before coding

1. **AYON server details** — server URL + how you want to authenticate (service API key vs per-user login).
2. **Site / roots** — which AYON *site id* this workstation maps to, so root resolution picks the right mounted drive letters/paths.
3. **Which reviewable to play** — transcoded mp4/mov (smooth) vs. raw published EXR sequence (accurate). Recommend mp4/mov as default `media`.
4. **Version scope** — latest version per product only, or every version? (Affects list length.)
5. **Status list** — your project's AYON status names, to build the §6 map.
6. **AYON version** — confirm your AYON server + `ayon-python-api` version so I target the right method names (a couple were renamed across releases).

---

## 8. Running Viewline (prerequisite, independent of AYON)

Viewline runs via a batch launcher, not `pip install`. To run it on this machine you need:

- **Python 3.10**
- Packages: `PySide6==6.9.0`, `PyOpenGL`, `numpy==1.26.4`, `av`, `OpenImageIO`, `opencolorio`, `requests`, `pyqtdarktheme` (OpenImageIO/OCIO are the tricky wheels on Windows).
- **OpenUSD 26.05** (built from source per README) for USD review; optional if you only review images/movies.
- **`ayon-python-api`** (`pip install ayon-python-api`) — new requirement for this integration.
- Environment (set by a launcher like `call-win.bat`):
  - `PYTHONPATH` must include the **parent** of this repo folder (`C:\pipeline`, because the code imports `from viewline import ...`) plus USD's `lib/python`.
  - `OCIO` → path to an ACES OCIO config.
  - `VIEW_LINE_PROFILE_ROOT` → working/profile dir (defaults to `%USERPROFILE%/Documents`).
  - `PATH` += USD `bin` and `lib`.
  - **New:** `AYON_SERVER_URL`, `AYON_API_KEY`, `VIEWLINE_BACKEND=ayon`.
- Launch: `python viewline/main.py`.

The existing `call-win.bat` hardcodes `D:/works/developments` paths — copy it to `call-viewline-ayon.bat`, repoint to this machine's paths, and add the three AYON vars.

---

## 9. Suggested build order

1. Confirm §7 answers + get Viewline running with the JSON demo backend (proves the environment).
2. Add the backend dispatcher + move JSON logic into `providers/json_demo.py` (no behavior change).
3. Implement `Projects.get` against AYON — verify the project browser populates.
4. Implement `Versions.get` (reviewables-only, local path resolution) — verify publishes appear and play.
5. Implement `Review.get` then `Review.set` — verify notes round-trip and status updates land in AYON.
6. Status map + thumbnail caching polish.
7. Ship the AYON launcher `.bat`.
```
```
