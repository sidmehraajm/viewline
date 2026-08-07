"""
AYON data providers for Viewline.

Drop-in replacement for the JSON providers in ``scripts/__init__.py``. Implements
the same public contract the Review Player expects:

    Projects.get()               -> list[dict]
    Versions.get(project)        -> list[dict]   (reviewables only)
    Review.get(version, reverse) -> (bool, list|None)
    Review.set(context)          -> (bool, str)

Connection:
    Uses ``ayon-python-api``. Credentials come from environment variables
    (set by run-viewline.bat):
        AYON_SERVER_URL   e.g. http://ayon:5000
        AYON_API_KEY      service API key

Media access:
    Local / mounted studio storage. Representation file paths that contain
    ``{root[...]}`` tokens are resolved against the project's roots. If auto
    resolution fails you can override with:
        VIEWLINE_AYON_ROOTS   JSON, e.g. {"work": "P:/projects"}

Optional filters:
    VIEWLINE_AYON_PRODUCT_TYPES   comma list, e.g. "render,review,plate"
                                  (default: keep any version that has playable media)

This module is intentionally defensive: any AYON error degrades gracefully
(empty list / no notes) and is logged, so the player never crashes on a
network hiccup.
"""

from __future__ import absolute_import

import os
import re
import json
import logging
import datetime

LOGGER = logging.getLogger("viewline.ayon")
if not LOGGER.handlers:
    logging.basicConfig(level=logging.INFO)

# Playable media extensions, in preference order (best playback first).
_MOVIE_EXTS = ("mp4", "mov", "avi")
_IMAGE_EXTS = ("exr", "png", "jpg", "jpeg")
_PLAYABLE_EXTS = _MOVIE_EXTS + _IMAGE_EXTS

_CONNECTION = None
_ROOTS_CACHE = {}
_FOLDERS_CACHE = {}
_TASKS_CACHE = {}
_VERSIONS_CACHE = {}


def clear_caches(project_name=None):
    """Drop cached folders/tasks/versions so the next query refetches."""
    if project_name is None:
        _ROOTS_CACHE.clear()
        _FOLDERS_CACHE.clear()
        _TASKS_CACHE.clear()
        _VERSIONS_CACHE.clear()
    else:
        for cache in (_ROOTS_CACHE, _FOLDERS_CACHE, _TASKS_CACHE):
            cache.pop(project_name, None)
        # Version cache is keyed by (project, folder, task) tuples.
        for key in [
            k
            for k in _VERSIONS_CACHE
            if k == project_name
            or (isinstance(k, tuple) and k and k[0] == project_name)
        ]:
            _VERSIONS_CACHE.pop(key, None)


# ---------------------------------------------------------------------------
# Connection
# ---------------------------------------------------------------------------
def _connect():
    """Return a cached, initialised ayon_api module (global connection set)."""
    global _CONNECTION
    if _CONNECTION is not None:
        return _CONNECTION

    import ayon_api

    # 1) Reuse an existing logged-in session (e.g. from the login dialog).
    try:
        ayon_api.get_server_api_connection()
        ayon_api.get_user()  # validates the session
        LOGGER.info("Using existing AYON login session.")
        _CONNECTION = ayon_api
        return _CONNECTION
    except Exception:
        pass

    # 2) Fall back to a service API key from the environment.
    server = os.getenv("AYON_SERVER_URL")
    api_key = os.getenv("AYON_API_KEY")
    if not server or not api_key:
        raise RuntimeError(
            "Not logged in and AYON_SERVER_URL / AYON_API_KEY are not set."
        )

    os.environ["AYON_SERVER_URL"] = server
    os.environ["AYON_API_KEY"] = api_key
    ayon_api.init_service()

    LOGGER.info("Connected to AYON server (API key): %s", server)
    _CONNECTION = ayon_api
    return _CONNECTION


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _fmt_datetime(value):
    """Format an AYON timestamp into Viewline's 'YYYY-MM-DD hh:mm:ss:AM/PM'."""
    if not value:
        return ""
    dt = None
    try:
        if isinstance(value, (int, float)):
            dt = datetime.datetime.fromtimestamp(value)
        else:
            text = str(value).replace("Z", "+00:00")
            dt = datetime.datetime.fromisoformat(text)
    except Exception:
        return str(value)
    return dt.strftime("%Y-%m-%d %I:%M:%S:%p")


def _iso(value):
    """Return a lexically-sortable ISO string for sorting."""
    return str(value or "")


def _resolve_roots(project_name):
    """Return {root_name: absolute_path} for local media resolution."""
    if project_name in _ROOTS_CACHE:
        return _ROOTS_CACHE[project_name]

    roots = {}

    # 1) Manual override wins.
    override = os.getenv("VIEWLINE_AYON_ROOTS")
    if override:
        try:
            roots = json.loads(override)
        except Exception:
            LOGGER.warning("VIEWLINE_AYON_ROOTS is not valid JSON; ignoring.")

    # 2) Auto-fetch from the server (try known helper names / signatures).
    if not roots:
        ayon = _connect()
        site_id = os.getenv("AYON_SITE_ID")
        for fn_name in (
            "get_project_roots_for_site",
            "get_project_roots_by_site",
            "get_project_roots_by_site_id",
        ):
            fn = getattr(ayon, fn_name, None)
            if not fn:
                continue
            for args in ((project_name, site_id), (project_name,)):
                try:
                    result = fn(*args)
                    if result:
                        roots = dict(result)
                        raise StopIteration
                except StopIteration:
                    break
                except Exception:
                    continue
            if roots:
                break

    if not roots:
        LOGGER.warning(
            "Could not resolve AYON roots for '%s'. If media paths contain "
            "{root[...]} tokens, set VIEWLINE_AYON_ROOTS.",
            project_name,
        )

    _ROOTS_CACHE[project_name] = roots
    return roots


def _apply_roots(path, roots):
    """Substitute {root[...]} / {root} tokens and normalise slashes."""
    if not path:
        return path
    out = str(path)
    if "{root" in out:
        for key, value in (roots or {}).items():
            out = out.replace("{root[%s]}" % key, str(value))
        if roots and "{root}" in out:
            out = out.replace("{root}", str(list(roots.values())[0]))
    return os.path.normpath(out).replace("\\", "/")


def _ext(path):
    return path.rsplit(".", 1)[-1].lower() if "." in path else ""


def _to_frame_token(path):
    """Convert a per-frame path into Viewline's #### token."""
    p = str(path)
    # Common frame placeholders first.
    p = re.sub(r"%0?\d*d", "####", p)
    p = re.sub(r"\{frame[^}]*\}", "####", p)
    if "####" in p:
        return p
    # Replace the last run of digits before the extension with ####.
    base, dot, ext = p.rpartition(".")
    if dot:
        base = re.sub(r"(?<=[._])\d+$", "####", base)
        return base + dot + ext
    return p


def _pick_media(representations, roots):
    """Pick the best playable representation. Return (media_path, is_sequence)."""
    best = None  # (rank, rep, files)
    for rep in representations:
        files = rep.get("files") or []
        if not files:
            continue
        # Determine extension from the representation name or the first file.
        sample = files[0].get("path") or files[0].get("name") or ""
        ext = _ext(rep.get("name", "")) or _ext(sample)
        if ext not in _PLAYABLE_EXTS:
            continue
        rank = _PLAYABLE_EXTS.index(ext)
        if best is None or rank < best[0]:
            best = (rank, rep, files)

    if best is None:
        return None, False

    _, rep, files = best
    ext = _ext(rep.get("name", "")) or _ext(files[0].get("path", ""))
    first_path = _apply_roots(files[0].get("path", ""), roots)

    is_sequence = len(files) > 1 and ext in _IMAGE_EXTS
    if is_sequence:
        return _to_frame_token(first_path), True
    return first_path, False


def _cache_thumbnail(ayon, project_name, version_id, thumbnail_id):
    """Download a version thumbnail to a local cache file; return path or ''."""
    if not thumbnail_id:
        return ""
    try:
        cache_dir = os.path.join(
            os.getenv("VIEW_LINE_PROFILE_ROOT", os.path.expanduser("~")),
            "viewline",
            "cache",
            "ayon_thumbs",
        )
        os.makedirs(cache_dir, exist_ok=True)
        out = os.path.join(cache_dir, "%s.jpg" % version_id).replace("\\", "/")
        if os.path.exists(out):
            return out
        content = ayon.get_thumbnail(project_name, "version", version_id, thumbnail_id)
        data = getattr(content, "content", content)
        if not data:
            return ""
        with open(out, "wb") as fh:
            fh.write(data)
        return out
    except Exception as exc:
        LOGGER.debug("Thumbnail fetch failed for %s: %s", version_id, exc)
        return ""


def _project_statuses(ayon, project_name):
    """Return list of AYON status dicts for the project (name/shortName/state)."""
    try:
        project = ayon.get_project(project_name)
        return project.get("statuses") or []
    except Exception:
        return []


def _map_status_to_ayon(ayon, project_name, value):
    """Map a Viewline status code/label to an AYON status name."""
    if not value:
        return value
    for st in _project_statuses(ayon, project_name):
        candidates = {
            str(st.get("name", "")).lower(),
            str(st.get("shortName", "")).lower(),
        }
        if str(value).lower() in candidates:
            return st.get("name", value)
    return value


def _map_status_to_viewline(ayon, project_name, name):
    """Map an AYON status name to a short code for display in Viewline."""
    if not name:
        return name
    for st in _project_statuses(ayon, project_name):
        if str(st.get("name", "")).lower() == str(name).lower():
            return st.get("shortName") or st.get("name") or name
    return name


def _author_dict(name):
    return {"id": name or "ayon", "name": name or "ayon", "type": "HumanUser"}


def _parse_frame(name):
    """Extract a frame number from an attachment filename (annotated.0038.png -> 38)."""
    if not name:
        return None
    nums = re.findall(r"\d+", str(name))
    if not nums:
        return None
    try:
        return int(nums[-1])
    except ValueError:
        return None


def _download_activity_files(ayon, project_name, activity):
    """Download a comment activity's attached files; return attachment dicts.

    File records live in the activity's activityData JSON. Files are cached
    locally so the review-notes panel can display the annotation image and so
    each note can report the frame it was drawn on.
    """
    attachments = []
    data = activity.get("activityData") or {}
    files = []
    if isinstance(data, dict):
        files = data.get("files") or data.get("attachments") or []

    if not files:
        return attachments

    cache_dir = os.path.join(
        os.getenv("VIEW_LINE_PROFILE_ROOT", os.path.expanduser("~")),
        "viewline",
        "cache",
        "ayon_notes",
    )
    os.makedirs(cache_dir, exist_ok=True)

    for f in files:
        if not isinstance(f, dict):
            continue
        fid = f.get("id") or f.get("fileId")
        name = f.get("name") or f.get("filename") or ("%s.png" % fid)
        if not fid:
            continue
        out = os.path.join(cache_dir, "%s_%s" % (fid, name)).replace("\\", "/")
        if not os.path.exists(out):
            downloaded = False
            for endpoint in (
                "api/projects/%s/files/%s" % (project_name, fid),
                "projects/%s/files/%s" % (project_name, fid),
            ):
                try:
                    ayon.download_file(endpoint, out)
                    downloaded = True
                    break
                except Exception:
                    continue
            if not downloaded:
                LOGGER.warning("Could not download note attachment %s", fid)
                continue
        attachments.append(
            {
                "id": fid,
                "type": "Attachment",
                "filename": name,
                "image": out,
                "frame": _parse_frame(name),
            }
        )
    return attachments


def _upload_comment_files(ayon, project_name, filepaths):
    """Upload files to the project and return a list of AYON file ids.

    Uses the project files endpoint (POST /api/projects/<name>/files). The
    returned ids are attached to the comment activity via ``file_ids``.
    """
    file_ids = []
    request_type = getattr(getattr(ayon, "RequestTypes", None), "post", None)
    for path in filepaths or []:
        if not path or not os.path.exists(path):
            LOGGER.warning("Attachment missing on disk, skipping: %s", path)
            continue
        try:
            import mimetypes

            content_type = mimetypes.guess_type(path)[0]
            if not content_type:
                ext = _ext(path)
                content_type = {
                    "png": "image/png",
                    "jpg": "image/jpeg",
                    "jpeg": "image/jpeg",
                    "mp4": "video/mp4",
                    "mov": "video/quicktime",
                }.get(ext, "application/octet-stream")

            kwargs = {
                "filename": os.path.basename(path),
                "content_type": content_type,
            }
            if request_type is not None:
                kwargs["request_type"] = request_type
            response = ayon.upload_file(
                "api/projects/%s/files" % project_name, path, **kwargs
            )
            data = response.json() if hasattr(response, "json") else response
            fid = data.get("id") if isinstance(data, dict) else None
            if fid:
                file_ids.append(fid)
                LOGGER.info("Uploaded attachment %s -> %s", os.path.basename(path), fid)
            else:
                LOGGER.warning("No file id returned for %s: %r", path, data)
        except Exception:
            LOGGER.exception("Attachment upload failed: %s", path)
    return file_ids


def _get_folders(project_name):
    """Return {folder_id: folder_dict} for the project (cached)."""
    if project_name not in _FOLDERS_CACHE:
        ayon = _connect()
        _FOLDERS_CACHE[project_name] = {
            f["id"]: f for f in ayon.get_folders(project_name)
        }
    return _FOLDERS_CACHE[project_name]


def _get_tasks(project_name):
    """Return {task_id: task_dict} for the project (cached)."""
    if project_name not in _TASKS_CACHE:
        ayon = _connect()
        _TASKS_CACHE[project_name] = {
            t["id"]: t for t in ayon.get_tasks(project_name)
        }
    return _TASKS_CACHE[project_name]


def _enrich_version(ayon, v, project, project_name, products, folders, tasks, roots):
    """Turn an AYON version into a Viewline version dict, or None if no media."""
    product = products.get(v.get("productId"))
    if product is None:
        return None

    reps = list(ayon.get_representations(project_name, version_ids=[v["id"]]))
    media_path, _is_seq = _pick_media(reps, roots)
    if not media_path:
        return None  # only reviewables (must have playable media)

    folder = folders.get(product.get("folderId")) or {}
    task = tasks.get(v.get("taskId")) or {}
    attrib = v.get("attrib") or {}
    version_number = v.get("version", 0)
    code = "%s v%03d" % (product.get("name", "version"), int(version_number))

    return {
        "type": "Version",
        "id": v["id"],
        "ayon_id": v["id"],
        "code": code,
        "project": {
            "id": project_name,
            "ayon_name": project_name,
            "name": project.get("name", project_name),
            "type": "Project",
        },
        "entity": {
            "id": folder.get("id"),
            "name": folder.get("name"),
            "type": folder.get("folderType") or "Folder",
        },
        "sg_task": {
            "id": task.get("id"),
            "name": task.get("name"),
            "type": "Task",
        },
        "sg_status_list": v.get("status"),
        "description": attrib.get("comment") or "",
        "created_at": _fmt_datetime(v.get("createdAt")),
        "created_by": _author_dict(v.get("author")),
        "image": _cache_thumbnail(ayon, project_name, v["id"], v.get("thumbnailId")),
        "media": media_path,
        "_created": _iso(v.get("createdAt")),
    }


def _build_versions_filtered(project, shot, task, status):
    """Build (and cache) reviewable versions matching the given filters.

    Scope is narrowed as much as possible before fetching representations:
      - a selected Task limits to that task's folder + task id
      - else a selected Shot limits to that folder
      - a selected Status is applied to the version entity BEFORE fetching media

    With no Task/Shot the whole project is scanned (only when the user clicks
    Load), and a Status filter keeps that affordable.
    """
    project_name = project.get("ayon_name") or project.get("id")
    task_id = None if _is_all(task) else (task or {}).get("id")
    folder_id = None
    if task_id:
        folder_id = (task or {}).get("folder_id")
    if not folder_id and not _is_all(shot):
        folder_id = (shot or {}).get("id")

    ayon = _connect()
    status_value = None if _is_all(status) else (
        (status or {}).get("value") or (status or {}).get("code")
    )
    ayon_status = (
        _map_status_to_ayon(ayon, project_name, status_value) if status_value else None
    )

    cache_key = (project_name, folder_id, task_id, ayon_status)
    if cache_key in _VERSIONS_CACHE:
        return _VERSIONS_CACHE[cache_key]

    roots = _resolve_roots(project_name)
    folders = _get_folders(project_name)
    tasks = _get_tasks(project_name)

    type_filter = os.getenv("VIEWLINE_AYON_PRODUCT_TYPES")
    product_types = (
        [t.strip() for t in type_filter.split(",") if t.strip()]
        if type_filter
        else None
    )
    product_kwargs = {"product_types": product_types}
    if folder_id:
        product_kwargs["folder_ids"] = [folder_id]
    products = {
        pr["id"]: pr for pr in ayon.get_products(project_name, **product_kwargs)
    }
    product_ids = list(products.keys())
    if not product_ids:
        _VERSIONS_CACHE[cache_key] = []
        return []

    try:
        versions = list(
            ayon.get_versions(project_name, product_ids=product_ids, hero=False)
        )
    except TypeError:
        versions = [
            v
            for v in ayon.get_versions(project_name, product_ids=product_ids)
            if int(v.get("version", 0)) >= 0
        ]

    result = []
    for v in versions:
        if task_id and v.get("taskId") != task_id:
            continue
        if ayon_status and v.get("status") != ayon_status:
            continue
        enriched = _enrich_version(
            ayon, v, project, project_name, products, folders, tasks, roots
        )
        if enriched:
            result.append(enriched)

    result.sort(key=lambda k: k.get("_created", ""), reverse=True)
    LOGGER.info(
        "AYON reviewable versions (task=%s status=%s): %d",
        (task or {}).get("name"),
        ayon_status,
        len(result),
    )
    _VERSIONS_CACHE[cache_key] = result
    return result


# ---------------------------------------------------------------------------
# Providers
# ---------------------------------------------------------------------------
class Projects(object):
    @classmethod
    def get(cls):
        try:
            ayon = _connect()
            clear_caches()  # refresh folders/tasks/versions when the browser reloads
            projects = []
            for p in ayon.get_projects():
                name = p.get("name")
                if not name:
                    continue
                data = p.get("data") or {}
                projects.append(
                    {
                        "type": "Project",
                        "id": name,               # project name is AYON's stable key
                        "ayon_name": name,
                        "code": p.get("code") or name,
                        "name": name,
                        "created_at": _fmt_datetime(p.get("createdAt")),
                        "image": "",
                        "sg_description": data.get("description"),
                        "_created": _iso(p.get("createdAt")),
                    }
                )
            projects.sort(key=lambda k: k.get("_created", ""), reverse=True)
            LOGGER.info("AYON projects: %d", len(projects))
            return projects
        except Exception:
            LOGGER.exception("Projects.get() failed")
            return []


def _is_all(context):
    """True when a Shot/Task selection means 'no filter' (the All entry)."""
    return not context or context.get("id") in (None, "", "all", "ALL")


class Shots(object):
    """Folder ('shot') provider. Lists ALL folders in the project."""

    @classmethod
    def get(cls, project):
        try:
            project_name = project.get("ayon_name") or project.get("id")
            folders = _get_folders(project_name)
            result = []
            for f in folders.values():
                result.append(
                    {
                        "type": f.get("folderType") or "Folder",
                        "id": f.get("id"),
                        "ayon_id": f.get("id"),
                        "name": f.get("name"),
                        "path": f.get("path") or f.get("name"),
                    }
                )
            result.sort(key=lambda k: (k.get("path") or k.get("name") or ""))
            return result
        except Exception:
            LOGGER.exception("Shots.get() failed")
            return []


class Tasks(object):
    """Task provider. Lists tasks under a shot (folder), or all tasks."""

    @classmethod
    def get(cls, project, shot=None):
        try:
            project_name = project.get("ayon_name") or project.get("id")
            tasks = _get_tasks(project_name)
            shot_id = None if _is_all(shot) else (shot or {}).get("id")
            result = []
            seen = set()
            for t in tasks.values():
                if shot_id and t.get("folderId") != shot_id:
                    continue
                name = t.get("name")
                key = (name, t.get("id"))
                if key in seen:
                    continue
                seen.add(key)
                result.append(
                    {
                        "type": "Task",
                        "id": t.get("id"),
                        "ayon_id": t.get("id"),
                        "name": name,
                        "task_type": t.get("taskType"),
                        "folder_id": t.get("folderId"),
                    }
                )
            result.sort(key=lambda k: (k.get("name") or ""))
            return result
        except Exception:
            LOGGER.exception("Tasks.get() failed")
            return []


class Statuses(object):
    """Status provider. Returns the project's AYON statuses."""

    @classmethod
    def get(cls, project):
        try:
            ayon = _connect()
            project_name = project.get("ayon_name") or project.get("id")
            result = []
            for s in _project_statuses(ayon, project_name):
                name = s.get("name")
                if not name:
                    continue
                result.append(
                    {
                        "code": name,
                        "value": name,
                        "color": s.get("color") or "#8a8a8a",
                    }
                )
            return result
        except Exception:
            LOGGER.exception("Statuses.get() failed")
            return []


class Versions(object):
    @classmethod
    def get(cls, project, shot=None, task=None, status=None):
        try:
            return _build_versions_filtered(project, shot, task, status)
        except Exception:
            LOGGER.exception("Versions.get() failed")
            return []


class Review(object):
    @classmethod
    def get(cls, version, reverse=False):
        try:
            ayon = _connect()
            project_name = (version.get("project") or {}).get("ayon_name") or (
                version.get("project") or {}
            ).get("id")
            version_id = version.get("ayon_id") or version.get("id")
            if not project_name or not version_id:
                return False, None

            fields = {
                "activityId",
                "activityType",
                "activityData",
                "body",
                "createdAt",
                "author.name",
            }
            try:
                activities = list(
                    ayon.get_activities(
                        project_name,
                        entity_ids=[version_id],
                        activity_types=["comment"],
                        fields=fields,
                    )
                )
            except TypeError:
                activities = list(
                    ayon.get_activities(
                        project_name,
                        entity_ids=[version_id],
                        activity_types=["comment"],
                    )
                )
            if not activities:
                return False, None

            activities.sort(key=lambda a: _iso(a.get("createdAt")), reverse=reverse)

            result = []
            for act in activities:
                author = act.get("authorName") or (act.get("author") or {}).get("name")
                attachments = _download_activity_files(ayon, project_name, act)
                frames = [str(a["frame"]) for a in attachments if a.get("frame") is not None]
                subject = "%s's note on %s" % (author or "ayon", version.get("code", ""))
                if frames:
                    subject += "  (frame %s)" % ", ".join(frames)
                note = {
                    "id": act.get("activityId") or act.get("id"),
                    "type": "Note",
                    "subject": subject,
                    "content": act.get("body", ""),
                    "created_at": _fmt_datetime(act.get("createdAt")),
                    "created_by": _author_dict(author),
                    "project": version.get("project"),
                    "publish_status": "published",
                    "sg_review_type": "Comment",
                    "sg_status_list": version.get("sg_status_list", ""),
                    "note_links": [
                        {
                            "id": version_id,
                            "name": version.get("code", ""),
                            "type": "Version",
                        }
                    ],
                }
                result.append([[note, attachments]])

            return True, result
        except Exception:
            LOGGER.exception("Review.get() failed")
            return False, None

    @classmethod
    def set(cls, context):
        try:
            ayon = _connect()
            version = context["version"]
            project_name = (version.get("project") or {}).get("ayon_name") or (
                version.get("project") or {}
            ).get("id")
            version_id = version.get("ayon_id") or version.get("id")
            body = context.get("message", "")

            # Upload annotated-frame snapshots / attachments to the comment.
            attachments = context.get("attachments") or []
            file_ids = _upload_comment_files(ayon, project_name, attachments)
            if attachments:
                names = ", ".join(os.path.basename(a) for a in attachments)
                body = "%s\n\nAnnotated frames: %s" % (body, names)

            # Create the comment activity on the version.
            ayon.create_activity(
                project_name,
                version_id,
                "version",
                "comment",
                body=body,
                file_ids=file_ids or None,
            )

            # Update BOTH the version and the parent task status.
            status_choice = (context.get("status") or {}).get("value")
            task = version.get("sg_task") or {}
            task_id = task.get("id")
            if status_choice:
                valid = {
                    s.get("name") for s in _project_statuses(ayon, project_name)
                }
                ayon_status = _map_status_to_ayon(ayon, project_name, status_choice)
                if ayon_status in valid:
                    try:
                        ayon.update_version(
                            project_name, version_id, status=ayon_status
                        )
                        version["sg_status_list"] = ayon_status
                    except Exception:
                        LOGGER.exception("Failed to update version status")
                    if task_id:
                        try:
                            ayon.update_task(
                                project_name, task_id, status=ayon_status
                            )
                        except Exception:
                            LOGGER.exception("Failed to update task status")
                else:
                    LOGGER.warning(
                        "Status '%s' is not an AYON status for '%s'. "
                        "Available: %s. Skipped status update (comment still posted).",
                        status_choice,
                        project_name,
                        sorted(v for v in valid if v),
                    )

            return True, "created comment on %s" % version.get("code", version_id)
        except Exception:
            LOGGER.exception("Review.set() failed")
            return False, "AYON submission failed (see log)"


if __name__ == "__main__":
    pass
