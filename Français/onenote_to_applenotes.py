#!/usr/bin/env python3
"""
NoteTransit — OneNote -> Apple Notes (macOS).
https://github.com/JLC-Solution/NoteTransit

  Notebook / Bloc-notes            -> folder / dossier
  Section group / Groupe de sections -> subfolder / sous-dossier
  Section                          -> subfolder / sous-dossier
  Page                             -> note ("Parent › Sub-page" for sub-pages)

Reads OneNote through Microsoft Graph, writes ENEX batches that Apple Notes imports
(one "Import" click per 500 notes), then files each note into its folder.
Lit OneNote via Microsoft Graph, crée des lots ENEX importés par Notes (un clic
« Importer » par lot de 500 notes), puis range chaque note dans son dossier.

  python onenote_to_applenotes.py --list
  python onenote_to_applenotes.py --notebook "Travel" --max-pages 3
  python onenote_to_applenotes.py --notebook "Travel"
  python onenote_to_applenotes.py

Messages: NOTETRANSIT_LANG=en for English (French by default).
Running again resumes where it stopped (migration_state.json).
"""
import argparse
import base64
import hashlib
import json
import mimetypes
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

import msal
import requests
from bs4 import BeautifulSoup

HERE = Path(__file__).resolve().parent
STATE_FILE = HERE / "migration_state.json"
TOKEN_CACHE = HERE / ".token_cache.json"
CACHE_DIR = HERE / "cache"
EXPORT_DIR = HERE / "exports"

GRAPH = "https://graph.microsoft.com/v1.0/me/onenote"

# Langue des messages : "fr" (défaut) ou "en", choisie par le lanceur via NOTETRANSIT_LANG
LANG = "en" if os.environ.get("NOTETRANSIT_LANG", "").lower().startswith("en") else "fr"
MESSAGES = {
    "login_failed": ("Échec de la connexion : {e}", "Sign-in failed: {e}"),
    "network_retry": ("    (réseau : {e}, nouvel essai dans {wait}s)", "    (network: {e}, retrying in {wait}s)"),
    "throttled": ("    (limite de l'API Microsoft, pause {wait}s ; rythme : 1 requête / {rate}s)",
                  "    (Microsoft API limit, pausing {wait}s; pace: 1 request / {rate}s)"),
    "gave_up": ("Microsoft refuse encore après 15 essais : {url}", "Microsoft still refusing after 15 attempts: {url}"),
    "untitled": ("Sans titre", "Untitled"),
    "image_failed": ("[image non récupérée : {e}]", "[image not retrieved: {e}]"),
    "attachment_failed": ("[pièce jointe « {name} » non récupérée : {e}]", "[attachment \"{name}\" not retrieved: {e}]"),
    "click_import": ("\n👉 Dans Notes, cliquez sur « Importer » (la fenêtre peut être derrière le Terminal).",
                     "\n👉 In Notes, click \"Import\" (the window may be behind the Terminal)."),
    "waiting_import": ("   Attente de l'import de {n} notes…", "   Waiting for {n} notes to be imported…"),
    "imported_count": ("\r   Notes importées : {count}/{n}      ", "\r   Notes imported: {count}/{n}      "),
    "section_unreadable": ("{path} (section illisible) : {e}", "{path} (unreadable section): {e}"),
    "section_line": ("📂 {path} — {total} pages, {todo} à migrer", "📂 {path} — {total} pages, {todo} to migrate"),
    "downloading": ("\nTéléchargement de {n} pages…", "\nDownloading {n} pages…"),
    "batch_title": ("\n=== Lot {n} sur {total} : {count} notes ===", "\n=== Batch {n} of {total}: {count} notes ==="),
    "filing": ("Rangement des notes dans les dossiers…", "Filing notes into folders…"),
    "not_found": ("{path} / {title} : non retrouvée après import", "{path} / {title}: not found after import"),
    "filed": ("   ✓ {path} : {n} notes", "   ✓ {path}: {n} notes"),
    "not_filed": ("⚠ {n} notes n'ont pas pu être rangées : elles sont restées dans le dossier "
                  "« Notes importées » de Notes.",
                  "⚠ {n} notes could not be filed: they are still in the \"Imported Notes\" folder in Notes."),
    "notebook_count": ("{n} blocs-notes :", "{n} notebooks:"),
    "reading_tree": ("Lecture de l'arborescence OneNote…", "Reading OneNote structure…"),
    "no_notebook": ("Aucun bloc-notes trouvé{named}.", "No notebook found{named}."),
    "named": (" nommé « {name} »", " named \"{name}\""),
    "nothing_new": ("Rien de nouveau à migrer.", "Nothing new to migrate."),
    "ready": ("\n{n} notes prêtes, en {lots} lot(s) : Notes demandera « Importer » {lots} fois.",
              "\n{n} notes ready, in {lots} batch(es): Notes will ask \"Import\" {lots} time(s)."),
    "done": ("\nTerminé : {n} notes migrées au total.", "\nDone: {n} notes migrated in total."),
    "errors_title": ("Pages en erreur (relancez : seules ces pages seront réessayées) :",
                     "Pages with errors (run it again: only these pages will be retried):"),
    "sections_summary": ("{n} sections lues, dont {done} déjà entièrement migrées (non affichées).",
                         "{n} sections read, {done} of them already fully migrated (not shown)."),
    "retry_title": ("Nouvel essai des pages en erreur uniquement ({n}), sans relire tout OneNote…",
                    "Retrying only the pages with errors ({n}), without scanning all of OneNote…"),
    "retry_none": ("Aucune page en erreur à réessayer.", "No pages with errors to retry."),
    "retry_locate": ("   Recherche de la section de {n} élément(s) en erreur…",
                     "   Locating the section of {n} failed item(s)…"),
    "retry_lost": ("   ✗ introuvable dans OneNote (supprimé ?) : {msg}",
                   "   ✗ not found in OneNote (deleted?): {msg}"),
    "unfiled_warn": ("\n⚠ Certaines notes avaient été importées mais pas rangées. Si un dossier "
                     "« Notes importées » existe dans Notes, supprimez-le maintenant pour éviter les doublons.",
                     "\n⚠ Some notes were imported but not filed. If there is an \"Imported Notes\" folder "
                     "in Notes, delete it now to avoid duplicates."),
    "press_enter": ("Appuyez sur Entrée pour continuer…", "Press Enter to continue…"),
    "h_list": ("affiche les noms des blocs-notes sans rien écrire", "list notebook names, writes nothing"),
    "h_details": ("avec --list : affiche aussi groupes et sections", "with --list: also show section groups and sections"),
    "h_max": ("essai : ne migre que N pages", "test: migrate only N pages"),
    "h_notebook": ("ne migrer que ce bloc-notes", "migrate only this notebook"),
    "h_root": ("dossier racine dans Notes (défaut : %(default)s)", "root folder in Notes (default: %(default)s)"),
    "h_client": ("ID d'application Azure (optionnel)", "Azure app ID (optional)"),
    "h_retry": ("ne réessayer que les pages en erreur (sans relire tout OneNote)",
                "retry only the pages with errors (no full OneNote scan)"),
}


def t(key, **kw):
    fr, en = MESSAGES[key]
    return (en if LANG == "en" else fr).format(**kw)
# Client public "Microsoft Graph Command Line Tools". Remplaçable par l'ID de votre
# propre inscription d'app Azure via --client-id.
DEFAULT_CLIENT_ID = "14d82eec-204b-4c2f-b7e8-296a70dab67e"
SCOPES = ["Notes.Read"]


# ---------------------------------------------------------------- Microsoft Graph

class Graph:
    def __init__(self, client_id):
        cache = msal.SerializableTokenCache()
        if TOKEN_CACHE.exists():
            cache.deserialize(TOKEN_CACHE.read_text())
        self.cache = cache
        self.app = msal.PublicClientApplication(
            client_id, authority="https://login.microsoftonline.com/common", token_cache=cache
        )
        self.session = requests.Session()

    def token(self):
        accounts = self.app.get_accounts()
        result = self.app.acquire_token_silent(SCOPES, account=accounts[0]) if accounts else None
        if not result:
            flow = self.app.initiate_device_flow(scopes=SCOPES)
            if "user_code" not in flow:
                sys.exit(t("login_failed", e=flow.get('error_description', flow)))
            print("\n" + flow["message"] + "\n")
            result = self.app.acquire_token_by_device_flow(flow)
        if "access_token" not in result:
            sys.exit(t("login_failed", e=result.get('error_description', result)))
        if self.cache.has_state_changed:
            TOKEN_CACHE.write_text(self.cache.serialize())
        return result["access_token"]

    # Microsoft limite le nombre de requêtes par heure (chaque page et chaque image comptent).
    # On espace les requêtes, et on ralentit le rythme dès que Microsoft refuse.
    interval = 0.5

    def get(self, url, raw=False):
        for attempt in range(15):
            time.sleep(self.interval)
            try:
                r = self.session.get(url, headers={"Authorization": f"Bearer {self.token()}"}, timeout=120)
            except requests.exceptions.RequestException as e:
                wait = min(2 ** attempt * 5, 300)
                print(t("network_retry", e=type(e).__name__, wait=wait))
                time.sleep(wait)
                continue
            if r.status_code in (429, 500, 502, 503, 504):
                if r.status_code == 429:
                    Graph.interval = min(Graph.interval * 2, 15)
                retry_after = r.headers.get("Retry-After", "")
                wait = int(retry_after) if retry_after.isdigit() else min(60 * (attempt + 1), 300)
                print(t("throttled", wait=wait, rate=f"{Graph.interval:.1f}"))
                time.sleep(wait)
                continue
            r.raise_for_status()
            Graph.interval = max(Graph.interval * 0.98, 0.5)
            return r if raw else r.json()
        raise RuntimeError(t("gave_up", url=url))

    def get_all(self, url):
        items = []
        while url:
            data = self.get(url)
            items += data.get("value", [])
            url = data.get("@odata.nextLink")
        return items


def same_name(a, b):
    return " ".join(a.split()).casefold() == " ".join(b.split()).casefold()


def load_tree(g, notebook_filter=None):
    """Retourne [{name, kind, id, children:[...]}] : bloc-notes > groupes > sections."""
    def group_children(kind, gid):
        base = f"{GRAPH}/{kind}/{gid}"
        children = [
            {"name": sg["displayName"], "kind": "group", "id": sg["id"],
             "children": group_children("sectionGroups", sg["id"])}
            for sg in g.get_all(f"{base}/sectionGroups")
        ]
        children += [
            {"name": s["displayName"], "kind": "section", "id": s["id"], "children": []}
            for s in g.get_all(f"{base}/sections")
        ]
        return children

    tree = []
    for nb in g.get_all(f"{GRAPH}/notebooks"):
        if notebook_filter and not same_name(nb["displayName"], notebook_filter):
            continue
        tree.append({"name": nb["displayName"], "kind": "notebook", "id": nb["id"],
                     "children": group_children("notebooks", nb["id"])})
    return tree


def section_pages(g, section_id):
    pages = g.get_all(f"{GRAPH}/sections/{section_id}/pages?pagelevel=true&$top=100")
    pages.sort(key=lambda p: p.get("order", 0))
    # Titre des sous-pages : "Parent › Enfant"
    parents = {}
    for p in pages:
        level = p.get("level", 0)
        title = (p.get("title") or "").strip() or t("untitled")
        parents[level] = title
        p["display_title"] = " › ".join(parents[l] for l in range(level + 1) if l in parents) if level else title
    return pages


# ---------------------------------------------------------------- Conversion OneNote -> ENEX
#
# Les notes passent par un fichier ENEX (format Evernote) que Notes importe lui-même :
# c'est la seule voie où les images s'affichent à leur place et où les dates
# d'origine sont conservées. Le script range ensuite les notes dans les dossiers.

KEEP_ATTRS = {"href", "colspan", "rowspan", "type", "hash", "checked"}
INVALID_XML = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def image_type(data):
    if data.startswith(b"\x89PNG"):
        return "image/png"
    if data.startswith(b"\xff\xd8"):
        return "image/jpeg"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    if data.startswith(b"BM"):
        return "image/bmp"
    if data[:4] in (b"II*\x00", b"MM\x00*"):
        return "image/tiff"
    if data[4:12] in (b"ftypheic", b"ftypheix", b"ftypmif1"):
        return "image/heic"
    return None


def enex_date(iso):
    """'2023-05-02T10:00:00.123Z' -> '20230502T100000Z'"""
    return re.sub(r"[-:]", "", (iso or "1970-01-01T00:00:00")[:19]) + "Z"


def iso_epoch(iso):
    return datetime.fromisoformat((iso or "1970-01-01T00:00:00")[:19]).replace(tzinfo=timezone.utc).timestamp()


def convert_page(g, page):
    """Page OneNote -> élément <note> ENEX (texte XML)."""
    raw = g.get(f"{GRAPH}/pages/{page['id']}/content", raw=True).text
    soup = BeautifulSoup(raw, "html.parser")
    body = soup.body or soup
    resources = []

    def media(data, mime, name):
        digest = hashlib.md5(data).hexdigest()
        resources.append(
            f'<resource><data encoding="base64">{base64.b64encode(data).decode()}</data>'
            f"<mime>{xml_escape(mime)}</mime><resource-attributes>"
            f"<file-name>{xml_escape(name)}</file-name></resource-attributes></resource>")
        return soup.new_tag("en-media", attrs={"type": mime, "hash": digest})

    for i, img in enumerate(body.find_all("img")):
        src = img.get("data-fullres-src") or img.get("src")
        try:
            data = g.get(src, raw=True).content
            # Microsoft renvoie "application/octet-stream" : on lit le vrai type dans les octets
            mime = image_type(data) or img.get("data-fullres-src-type") or img.get("data-src-type") or "image/png"
            img.replace_with(media(data, mime, f"image{i + 1}.{mime.split('/')[-1]}"))
        except Exception as e:
            img.replace_with(t("image_failed", e=e))

    for obj in body.find_all("object"):
        name = obj.get("data-attachment") or "piece_jointe"
        try:
            data = g.get(obj["data"], raw=True).content
            mime = obj.get("type") or mimetypes.guess_type(name)[0] or "application/octet-stream"
            obj.replace_with(media(data, mime, name))
        except Exception as e:
            obj.replace_with(t("attachment_failed", name=name, e=e))

    for frame in body.find_all("iframe"):
        url = frame.get("data-original-src") or frame.get("src", "")
        a = soup.new_tag("a", href=url)
        a.string = f"🎬 {url}"
        frame.replace_with(a)

    for el in body.find_all(attrs={"data-tag": True}):
        tags = el["data-tag"]
        if "to-do" in tags:
            el.insert(0, soup.new_tag("en-todo", attrs={"checked": "true" if "completed" in tags else "false"}))

    # OneNote code le gras/italique/souligné en CSS : on les convertit en balises
    for el in body.find_all(style=True):
        style = el["style"].replace(" ", "").lower()
        for css, tag in (("font-weight:bold", "b"), ("font-style:italic", "i"),
                         ("text-decoration:underline", "u"), ("text-decoration:line-through", "s")):
            if css in style:
                wrapper = soup.new_tag(tag)
                for child in list(el.contents):
                    wrapper.append(child.extract())
                el.append(wrapper)

    for el in body.find_all(["script", "style", "meta", "link", "title"]):
        el.decompose()
    for el in body.find_all(True):
        el.attrs = {k: v for k, v in el.attrs.items() if k in KEEP_ATTRS}

    content = INVALID_XML.sub("", "".join(c.decode(formatter="minimal") if hasattr(c, "decode") else xml_escape(str(c))
                                          for c in body.contents))
    enml = ('<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE en-note SYSTEM '
            f'"http://xml.evernote.com/pub/enml2.dtd"><en-note>{content}</en-note>').replace("]]>", "]]]]><![CDATA[>")
    title = INVALID_XML.sub("", page["display_title"])
    return (f"<note><title>{xml_escape(title)}</title>"
            f"<created>{enex_date(page.get('createdDateTime'))}</created>"
            f"<updated>{enex_date(page.get('lastModifiedDateTime') or page.get('createdDateTime'))}</updated>"
            f"<content><![CDATA[{enml}]]></content>{''.join(resources)}</note>\n")


# ---------------------------------------------------------------- Apple Notes

AS_FOLDER = """
on run argv
  set parentId to item 1 of argv
  set fname to item 2 of argv
  tell application "Notes"
    if parentId is "" then
      -- "folders of account" inclut aussi les sous-dossiers : on garde ceux de premier niveau
      repeat with f in (folders of default account whose name is fname)
        if class of (container of f) is account then return id of f
      end repeat
      return id of (make new folder at default account with properties {name:fname})
    end if
    set p to folder id parentId
    if exists folder fname of p then return id of folder fname of p
    return id of (make new folder at p with properties {name:fname})
  end tell
end run
"""

# Dossiers de premier niveau : "id<TAB>nombre de notes" par ligne
AS_TOP_FOLDERS = """
tell application "Notes"
  set out to ""
  repeat with f in folders of default account
    if class of (container of f) is account then
      set out to out & (id of f) & tab & (count of notes of f) & linefeed
    end if
  end repeat
  return out
end tell
"""

# Notes d'un dossier : "id<US>nom<US>secondes depuis maintenant" par ligne
AS_LIST_NOTES = """
on run argv
  tell application "Notes"
    set now to current date
    set out to ""
    repeat with n in notes of folder id (item 1 of argv)
      set out to out & (id of n) & (ASCII character 31) & (name of n) & (ASCII character 31) & ((creation date of n) - now) & linefeed
    end repeat
    return out
  end tell
end run
"""

AS_MOVE = """
on run argv
  tell application "Notes"
    set dest to folder id (item 1 of argv)
    repeat with i from 2 to count of argv
      move note id (item i of argv) to dest
    end repeat
  end tell
end run
"""

AS_DELETE_IF_EMPTY = """
on run argv
  tell application "Notes"
    set f to folder id (item 1 of argv)
    if (count of notes of f) is 0 and (count of folders of f) is 0 then delete f
  end tell
end run
"""


def osascript(script, *args):
    r = subprocess.run(["osascript", "-", *args], input=script, capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(r.stderr.strip())
    return r.stdout.strip()


def top_folders():
    out = {}
    for line in osascript(AS_TOP_FOLDERS).splitlines():
        fid, _, count = line.partition("\t")
        out[fid] = int(count or 0)
    return out


def import_enex(path, expected):
    """Ouvre le fichier ENEX dans Notes et attend que l'utilisateur clique sur Importer.
    Retourne l'id du dossier « Notes importées » créé par Notes."""
    before = set(top_folders())
    subprocess.run(["open", "-a", "Notes", str(path)], check=True)
    print(t("click_import"))
    print(t("waiting_import", n=expected), end="", flush=True)
    last, stable = None, 0
    while True:
        time.sleep(5)
        new = {fid: c for fid, c in top_folders().items() if fid not in before}
        if new:
            fid, count = max(new.items(), key=lambda kv: kv[1])
            stable = stable + 1 if count == last else 0
            last = count
            print(t("imported_count", count=count, n=expected), end="", flush=True)
            # fini quand tout est là, ou quand le nombre ne bouge plus depuis 30 s
            if count >= expected and stable >= 1 or count and stable >= 6:
                print()
                return fid
        else:
            print(".", end="", flush=True)


# ---------------------------------------------------------------- Migration

def load_state():
    state = json.loads(STATE_FILE.read_text()) if STATE_FILE.exists() else {}
    for key in ("folders", "pages", "errors", "retry_sections"):
        state.setdefault(key, {})
    return state


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=1))


def ensure_folder(state, path):
    """path = tuple de noms depuis la racine ; crée chaque niveau si besoin."""
    parent_id = ""
    for i in range(len(path)):
        key = " / ".join(path[: i + 1])
        if key not in state["folders"]:
            state["folders"][key] = osascript(AS_FOLDER, parent_id, path[i])
            save_state(state)
        parent_id = state["folders"][key]
    return parent_id


def print_tree(nodes, indent=0):
    for n in nodes:
        icon = {"notebook": "📓", "group": "📁", "section": "📂"}[n["kind"]]
        print("  " * indent + f"{icon} {n['name']}")
        print_tree(n["children"], indent + 1)


def collect_pages(g, nodes, path, state, out, limit, stats):
    """Liste (chemin, page) des pages pas encore migrées.
    Seules les sections qui ont encore des pages à migrer sont affichées."""
    for n in nodes:
        if len(out) >= limit:
            return
        here = path + (n["name"],)
        if n["kind"] != "section":
            collect_pages(g, n["children"], here, state, out, limit, stats)
            continue
        if not collect_section(g, n["id"], here, state, out, limit):
            stats["done"] += 1
        stats["sections"] += 1


def collect_section(g, section_id, here, state, out, limit=float("inf")):
    """Ajoute à out les pages pas encore migrées d'une section ; retourne leur nombre."""
    try:
        pages = section_pages(g, section_id)
    except Exception as e:
        state["errors"][section_id] = t("section_unreadable", path=' / '.join(here), e=e)
        state["retry_sections"][section_id] = list(here)
        print(f"✗ {' / '.join(here)} : {e}")
        return 1
    state["errors"].pop(section_id, None)
    todo = [p for p in pages if p["id"] not in state["pages"]]
    if todo:
        print(t("section_line", path=' / '.join(here), total=len(pages), todo=len(todo)))
    for p in todo[: int(limit - len(out)) if limit != float("inf") else None]:
        p["_section"] = section_id
        out.append((here, p))
    return len(todo)


def section_path(g, section_id, root):
    """Chemin (racine, bloc-notes, groupes…, section) d'une section, en remontant ses parents."""
    s = g.get(f"{GRAPH}/sections/{section_id}?$expand=parentNotebook($select=displayName),"
              "parentSectionGroup($select=id,displayName)")
    names = [s["displayName"]]
    sg = s.get("parentSectionGroup")
    while sg:
        names.insert(0, sg["displayName"])
        sg = g.get(f"{GRAPH}/sectionGroups/{sg['id']}?$expand=parentSectionGroup($select=id,displayName)"
                   ).get("parentSectionGroup")
    return [root, s["parentNotebook"]["displayName"]] + names


def retry_todo(g, state, root):
    """Pages à réessayer : on ne relit que les sections qui contiennent des erreurs."""
    sections = dict(state["retry_sections"])
    # États créés par une version précédente : retrouver la section de chaque erreur
    unknown = [eid for eid in state["errors"] if eid not in sections] if not sections else []
    if unknown:
        print(t("retry_locate", n=len(unknown)))
    for eid in unknown:
        try:
            try:
                sid = g.get(f"{GRAPH}/pages/{eid}?$select=id&$expand=parentSection($select=id)")["parentSection"]["id"]
            except requests.HTTPError:
                sid = eid  # l'erreur concernait une section entière
            if sid not in sections:
                sections[sid] = section_path(g, sid, root)
        except Exception:
            print(t("retry_lost", msg=state["errors"][eid]))
    print(t("retry_title", n=len(state["errors"])))
    state["retry_sections"] = {}
    todo = []
    for sid, path in sections.items():
        collect_section(g, sid, tuple(path), state, todo)
    save_state(state)
    return todo


def norm(s):
    return " ".join((s or "").split()).casefold()


BATCH_NOTES = 500                 # notes par fichier d'import (= un clic sur « Importer »)
BATCH_BYTES = 400 * 1024 * 1024   # et au plus ~400 Mo par fichier


def download(g, todo, state):
    """Télécharge et convertit chaque page (mise en cache : une relance ne retélécharge rien)."""
    print(t("downloading", n=len(todo)))
    CACHE_DIR.mkdir(exist_ok=True)
    ready = []
    for i, (path, p) in enumerate(todo, 1):
        cached = CACHE_DIR / (re.sub(r"\W", "_", p["id"]) + ".xml")
        try:
            if not cached.exists():
                cached.write_text(convert_page(g, p), encoding="utf-8")
            ready.append((path, p, cached))
            state["errors"].pop(p["id"], None)
            print(f"   [{i}/{len(todo)}] {' / '.join(path[1:])} / {p['display_title']}")
        except Exception as e:
            state["errors"][p["id"]] = f"{' / '.join(path)} / {p['display_title']} : {e}"
            state["retry_sections"][p["_section"]] = list(path)
            print(f"   [{i}/{len(todo)}] ✗ {p['display_title']} : {e}")
        if i % 20 == 0:
            save_state(state)
    save_state(state)
    return ready


def batches(ready):
    batch, size = [], 0
    for item in ready:
        item_size = item[2].stat().st_size
        if batch and (len(batch) >= BATCH_NOTES or size + item_size > BATCH_BYTES):
            yield batch
            batch, size = [], 0
        batch.append(item)
        size += item_size
    if batch:
        yield batch


def import_batch(batch, state, n, total):
    EXPORT_DIR.mkdir(exist_ok=True)
    enex = EXPORT_DIR / f"batch {n} of {total} {time.strftime('%Y-%m-%d %Hh%M')}.enex"
    with open(enex, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE en-export SYSTEM '
                '"http://xml.evernote.com/pub/evernote-export4.dtd">\n'
                f'<en-export export-date="{time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())}" '
                'application="Evernote" version="10">\n')
        for _, _, cached in batch:
            f.write(cached.read_text(encoding="utf-8"))
        f.write("</en-export>\n")

    print(t("batch_title", n=n, total=total, count=len(batch)))
    import_folder = import_enex(enex, len(batch))

    # Rangement : chaque note importée est reconnue par son titre et sa date de création
    print(t("filing"))
    now = time.time()
    imported = []
    for line in osascript(AS_LIST_NOTES, import_folder).splitlines():
        nid, name, offset = line.split("\x1f")
        imported.append({"id": nid, "name": norm(name), "epoch": now + float(offset.replace(",", "."))})
    moves = {}
    for path, p, _ in batch:
        created = iso_epoch(p.get("createdDateTime"))
        candidates = [x for x in imported if abs(x["epoch"] - created) <= 5]
        match = next((x for x in candidates if x["name"] == norm(p["display_title"])), None)
        if not match and len(candidates) == 1:
            match = candidates[0]
        if not match:
            # date différente (fuseau, arrondi…) : titre unique parmi les notes importées
            same_title = [x for x in imported if x["name"] == norm(p["display_title"])]
            if len(same_title) == 1:
                match = same_title[0]
        if not match:
            state["errors"][p["id"]] = t("not_found", path=' / '.join(path), title=p['display_title'])
            state["retry_sections"][p["_section"]] = list(path)
            continue
        imported.remove(match)
        moves.setdefault(path, []).append((p["id"], match["id"]))
    for path, items in moves.items():
        folder_id = ensure_folder(state, path)
        osascript(AS_MOVE, folder_id, *[nid for _, nid in items])
        for pid, nid in items:
            state["pages"][pid] = nid
            state["errors"].pop(pid, None)
        save_state(state)
        print(t("filed", path=' / '.join(path), n=len(items)))
    osascript(AS_DELETE_IF_EMPTY, import_folder)
    enex.unlink(missing_ok=True)
    if imported:
        print(t("not_filed", n=len(imported)))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--list", action="store_true", help=t("h_list"))
    ap.add_argument("--details", action="store_true", help=t("h_details"))
    ap.add_argument("--max-pages", type=int, default=0, help=t("h_max"))
    ap.add_argument("--notebook", help=t("h_notebook"))
    ap.add_argument("--root", default="Import OneNote", help=t("h_root"))
    ap.add_argument("--client-id", default=DEFAULT_CLIENT_ID, help=t("h_client"))
    ap.add_argument("--retry-errors", action="store_true", help=t("h_retry"))
    args = ap.parse_args()

    g = Graph(args.client_id)
    if args.list and not args.details:
        notebooks = g.get_all(f"{GRAPH}/notebooks")
        print(t("notebook_count", n=len(notebooks)))
        for nb in sorted(notebooks, key=lambda nb: nb["displayName"].casefold()):
            print(f"  📓 {nb['displayName']}")
        return

    state = load_state()
    if args.retry_errors and not args.list:
        if not state["errors"]:
            print(t("retry_none"))
            return
        # « non retrouvée après import » : la note est peut-être restée dans « Notes importées »
        unfiled = any(m.endswith(("non retrouvée après import", "not found after import"))
                      for m in state["errors"].values())
        todo = retry_todo(g, state, args.root)
        if unfiled and todo:
            print(t("unfiled_warn"))
            input(t("press_enter"))
    else:
        print(t("reading_tree"))
        tree = load_tree(g, args.notebook)
        if not tree:
            sys.exit(t("no_notebook", named=t("named", name=args.notebook) if args.notebook else ""))

        if args.list:
            print_tree(tree)
            return

        limit = args.max_pages or float("inf")
        todo = []
        stats = {"sections": 0, "done": 0}
        collect_pages(g, tree, (args.root,), state, todo, limit, stats)
        print(t("sections_summary", n=stats["sections"], done=stats["done"]))
    if not todo:
        print(t("nothing_new"))
    else:
        ready = download(g, todo, state)
        lots = list(batches(ready))
        if lots:
            print(t("ready", n=len(ready), lots=len(lots)))
        for n, batch in enumerate(lots, 1):
            import_batch(batch, state, n, len(lots))

    print(t("done", n=len(state['pages'])))
    if state["errors"]:
        print(t("errors_title"))
        for msg in state["errors"].values():
            print("  -", msg)


if __name__ == "__main__":
    main()
