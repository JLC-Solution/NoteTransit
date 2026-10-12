# NoteTransit — OneNote → Apple Notes

**Move your Microsoft OneNote notebooks into Apple Notes, keeping folders, images, tables, checklists and original dates.**
Free, open source, runs entirely on your Mac. Your notes never go through a third-party server.

🇫🇷 [Version française plus bas](#-version-française)

> ☕ NoteTransit is free. If it saved you hours of copy-pasting, you can [buy me a coffee](https://buymeacoffee.com/jl.carbonel) — thank you!

## ⬇️ Download

| Language | Download | Launcher | Guide |
|---|---|---|---|
| 🇬🇧 English | [NoteTransit-English.zip](https://github.com/JLC-Solution/NoteTransit/releases/latest/download/NoteTransit-English.zip) | `Start migration.command` | `HOW-TO.txt` |
| 🇫🇷 Français | [NoteTransit-Francais.zip](https://github.com/JLC-Solution/NoteTransit/releases/latest/download/NoteTransit-Francais.zip) | `Lancer la migration.command` | `LISEZMOI.txt` |

Both folders contain the same script; only the messages and guide language differ.

---

## What it does

| OneNote | → | Apple Notes |
|---|---|---|
| Notebook | → | Folder |
| Section group | → | Subfolder |
| Section | → | Subfolder |
| Page | → | Note |
| Sub-page | → | Note titled `Parent › Sub-page` |

Everything lands in a folder called **Import OneNote**, then syncs to your iPhone and iPad through iCloud.

### What is kept

- Text, paragraphs and line breaks
- Headings, **bold**, *italic*, underline, strikethrough
- Bulleted and numbered lists
- Checklists (as real Apple Notes checkboxes)
- Tables (as real Apple Notes tables)
- Images, **inline, at their original position**
- File attachments (PDF, documents…)
- Original **creation and modification dates**

### What is not kept

- Ink, drawings and handwriting
- Colors, fonts and highlighting (Apple Notes uses its own style)
- Free-form layout: text boxes placed anywhere on the page become a single column
- The checked state of checkboxes (all arrive unchecked)
- Notebooks shared with you by someone else (only your own notebooks are listed)

OneNote is **never modified**: the tool only reads your notes.

## Requirements

- A Mac with Apple Notes, signed in to the iCloud account that should receive the notes
- Your Microsoft account (personal or work/school) that holds the OneNote notebooks
- An internet connection

> Why a Mac? Apple provides no way for an app — on iPhone or Mac — to write directly into Apple Notes. On a Mac, Notes can import files, which is what NoteTransit relies on.

## How to use

1. **Download** [NoteTransit-English.zip](https://github.com/JLC-Solution/NoteTransit/releases/latest/download/NoteTransit-English.zip) and unzip it.
2. Open the **Terminal** app (⌘ Space, type "Terminal", Enter).
3. Type `bash ` (with a space, don't press Enter), **drag the file `Start migration.command`** into the Terminal window, then press **Enter**.
   *(Double-clicking the file is blocked by macOS because it is not signed — use the Terminal instead.)*
4. First run only: if macOS offers to install the *command line developer tools* (for Python), accept, wait, then start again.
5. The Terminal shows a link (`https://login.microsoft.com/device`) and a code: open the link, type the code and sign in with your Microsoft account.
6. Your notebooks are listed. Type the name of one notebook, or press **Enter** for all of them.
7. Optionally run a **3-page test** first (answer `y`), then check the result in Notes.
8. NoteTransit takes inventory and downloads every page — nothing appears in Notes yet, that's expected. Microsoft limits requests per hour, so you will see pauses: let it run.
9. Then **Notes asks "Import?" — click Import** (the window may be hidden behind the Terminal). You click once per batch of 500 notes.
10. NoteTransit then files every note into the right folder automatically.

Large notebooks can take hours: keep the Mac plugged in and the lid open. The Mac is kept awake automatically while the migration runs.

**Interrupted?** Just run it again: downloaded pages are cached and pages already migrated are skipped.
Don't interrupt it during *"Filing notes into folders…"*. If you did, delete the **Import OneNote** and **Imported Notes** folders in Notes and the `migration_state.json` file, then start again.

## Command-line options

From the `English` or `Français` folder, after a first run (which creates `.venv`). Set `NOTETRANSIT_LANG=en` for English messages.

```bash
.venv/bin/python onenote_to_applenotes.py --list                     # list notebooks, writes nothing
.venv/bin/python onenote_to_applenotes.py --list --details           # with section groups and sections
.venv/bin/python onenote_to_applenotes.py --notebook "Travel" --max-pages 3   # test on 3 pages
.venv/bin/python onenote_to_applenotes.py --notebook "Travel"        # one notebook
.venv/bin/python onenote_to_applenotes.py                            # everything
.venv/bin/python onenote_to_applenotes.py --root "From OneNote"      # other root folder name
```

## How it works

1. **Reading** — Microsoft Graph OneNote API, with device-code sign-in (`Notes.Read`, read-only). Pages are downloaded as HTML with their images and attachments.
2. **Conversion** — each page becomes a note in an **ENEX** file (the Evernote export format), the only import path where Apple Notes keeps images inline and original dates.
3. **Import** — the ENEX file is opened in Notes, which asks for confirmation.
4. **Filing** — an AppleScript moves each imported note into its folder, matching notes by title and creation date.

Local files created next to the script (never published, see `.gitignore`):
`.token_cache.json` (Microsoft sign-in), `migration_state.json` (progress), `cache/` (downloaded pages), `exports/` (ENEX batches).

### Using your own Azure app ID (optional)

By default NoteTransit signs in with Microsoft's public client ID for the Microsoft Graph command-line tools. If your organization blocks it, register your own app in the [Azure portal](https://portal.azure.com) (*App registrations* → *New registration* → account type "any organizational directory and personal Microsoft accounts"; *Authentication* → enable *Allow public client flows*; *API permissions* → Microsoft Graph → delegated `Notes.Read`) and run:

```bash
.venv/bin/python onenote_to_applenotes.py --client-id YOUR-APP-ID
```

## License & author

MIT — free to use, modify and share. See [LICENSE](LICENSE).
Made by **JLC Solution**. Issues and pull requests welcome.

---

## 🇫🇷 Version française

**Transférez vos blocs-notes Microsoft OneNote vers Apple Notes, en gardant les dossiers, les images, les tableaux, les cases à cocher et les dates d'origine.**
Gratuit, open source, tout se passe sur votre Mac : vos notes ne passent par aucun serveur tiers.

> ☕ NoteTransit est gratuit. S'il vous a évité des heures de copier-coller, vous pouvez [m'offrir un café](https://buymeacoffee.com/jl.carbonel). Merci !

### Ce que fait l'outil

| OneNote | → | Apple Notes |
|---|---|---|
| Bloc-notes | → | Dossier |
| Groupe de sections | → | Sous-dossier |
| Section | → | Sous-dossier |
| Page | → | Note |
| Sous-page | → | Note titrée `Parent › Sous-page` |

Tout arrive dans un dossier **Import OneNote**, puis se synchronise sur l'iPhone et l'iPad via iCloud.

**Conservé :** texte et sauts de ligne, titres, gras, italique, souligné, barré, listes, cases à cocher (vraies cases Notes), tableaux (vrais tableaux Notes), images **à leur place**, pièces jointes, dates de création et de modification d'origine.

**Pas repris :** dessins et écriture manuscrite, couleurs et polices, mise en page libre (le contenu devient linéaire), état « coché » des cases, blocs-notes partagés par quelqu'un d'autre.

OneNote n'est **jamais modifié** : l'outil ne fait que lire vos notes.

### Il vous faut

- Un Mac avec Notes, connecté au compte iCloud qui doit recevoir les notes
- Votre compte Microsoft (personnel ou professionnel) qui contient les blocs-notes OneNote
- Une connexion internet

> Pourquoi un Mac ? Apple ne permet à aucune application, ni sur iPhone ni sur Mac, d'écrire directement dans Notes. Sur Mac, Notes sait importer des fichiers : c'est ce que NoteTransit utilise.

### Mode d'emploi

1. **Téléchargez** [NoteTransit-Francais.zip](https://github.com/JLC-Solution/NoteTransit/releases/latest/download/NoteTransit-Francais.zip) et décompressez-le.
2. Ouvrez l'app **Terminal** (⌘ Espace, tapez « Terminal », Entrée).
3. Tapez `bash ` (avec un espace, sans Entrée), **glissez le fichier `Lancer la migration.command`** dans la fenêtre, puis appuyez sur **Entrée**.
   *(Le double-clic est bloqué par macOS car le fichier n'est pas signé : passez par le Terminal.)*
4. Premier lancement : si macOS propose d'installer les « outils de ligne de commande » (pour Python), acceptez, attendez, puis relancez.
5. Le Terminal affiche une adresse (`https://login.microsoft.com/device`) et un code : ouvrez l'adresse, tapez le code et connectez-vous à votre compte Microsoft.
6. Vos blocs-notes s'affichent. Tapez le nom de l'un d'eux, ou **Entrée** pour tous.
7. Vous pouvez d'abord faire un **essai sur 3 pages** (répondez `o`) et vérifier le résultat dans Notes.
8. NoteTransit fait l'inventaire puis télécharge toutes les pages : rien n'arrive dans Notes pendant ce temps, c'est normal. Microsoft limite le nombre de requêtes par heure, d'où des pauses : laissez faire.
9. Puis **Notes demande « Importer ? » : cliquez sur Importer** (la fenêtre peut être derrière le Terminal). Un clic par lot de 500 notes.
10. NoteTransit range ensuite chaque note dans le bon dossier, tout seul.

Les gros blocs-notes peuvent prendre des heures : laissez le Mac branché, capot ouvert. Il est automatiquement empêché de se mettre en veille pendant la migration.

**Interruption ?** Relancez simplement : les pages téléchargées sont en cache et celles déjà migrées sont sautées.
Évitez d'interrompre pendant « Rangement des notes dans les dossiers… ». Si c'est arrivé, supprimez dans Notes les dossiers **Import OneNote** et **Notes importées**, ainsi que le fichier `migration_state.json`, puis relancez.

### Licence et auteur

MIT : libre d'utilisation, de modification et de partage.
Créé par **JLC Solution**. Suggestions et contributions bienvenues.
