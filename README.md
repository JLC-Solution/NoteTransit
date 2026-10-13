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
5. **First sign-in to Microsoft** — see [Signing in to Microsoft](#signing-in-to-microsoft-first-run) below.
6. Your notebooks are listed. Type the name of one notebook, or press **Enter** for all of them.
7. Optionally run a **3-page test** first (answer `y`), then check the result in Notes.
8. NoteTransit takes inventory and downloads every page — nothing appears in Notes yet, that's expected. Microsoft limits requests per hour, so you will see pauses: let it run.
9. Then **Notes asks "Import?" — click Import** (the window may be hidden behind the Terminal). You click once per batch of 500 notes.
10. NoteTransit then files every note into the right folder automatically.

Large notebooks can take hours: keep the Mac plugged in and the lid open. The Mac is kept awake automatically while the migration runs.

## Signing in to Microsoft (first run)

1. The Terminal shows a message like:
   `To sign in, use a web browser to open the page https://microsoft.com/devicelogin and enter the code ABCD1234`
2. Open that page in any browser (on the Mac or even on your phone), type the code, and sign in with the **Microsoft account that holds your OneNote notebooks**.
3. Microsoft asks whether **"Microsoft Graph Command Line Tools"** may **read your OneNote notebooks**. This is Microsoft's own public app ID that NoteTransit uses; it only gets read access (`Notes.Read`). Click **Accept / Yes**.
4. Close the browser tab and go back to the Terminal: your notebooks are listed.

Good to know:
- The code expires after about 15 minutes. If it expired, close the Terminal and start again.
- The sign-in is remembered in the hidden file `.token_cache.json` inside the folder, so the next runs don't ask again.
- **Work or school account** and you see "Need admin approval"? Your organization blocks this app ID: ask your IT department, or use your own app ID (see [below](#using-your-own-azure-app-id-optional)).
- To **sign out** of NoteTransit: delete `.token_cache.json`. To also remove the permission from your Microsoft account: personal account → [account.live.com/consent/Manage](https://account.live.com/consent/Manage), remove "Microsoft Graph Command Line Tools"; work/school account → [myapps.microsoft.com](https://myapps.microsoft.com) or your IT department.

## Stopping, resuming, starting over

### How to stop
Click in the Terminal window and press **Control + C** (or simply close the Terminal window). OneNote is never touched, so stopping can't damage anything there.

### When is it safe to stop?

| What the Terminal shows | Safe to stop? | What happens next time |
|---|---|---|
| Sign-in, notebook list, `Reading OneNote structure…`, section lines | ✅ Yes | Starts again normally |
| `Downloading N pages…` and the `[12/340] …` lines | ✅ Yes — **best moment** | Already downloaded pages are kept in `cache/` and not downloaded again |
| `In Notes, click "Import"` / `Waiting for N notes to be imported…` | ⚠️ Only **before** you click Import: click **Cancel** in the Notes window, then stop | The batch is simply prepared again |
| After clicking Import, and during `Filing notes into folders…` | ❌ No — wait for the next `=== Batch …` line or for `Done` | See "Stopped at the wrong moment?" below |
| `Done: N notes migrated in total.` | ✅ Finished | Running again only adds **new** OneNote pages |

To resume, simply run `Start migration.command` again (same folder, same notebook choice). Pages already in Apple Notes are skipped — this works as long as you keep `migration_state.json` **and** don't delete or rename the folders created in Notes.

### Some pages ended with errors?
At the end, NoteTransit lists the pages it couldn't migrate. Just run `Start migration.command` again: it sees the errors and asks **"Retry ONLY these pages?"** — answer `y`. It then reads only the sections containing those pages instead of scanning all of OneNote again, which is much faster.
If some pages were imported but not filed, it reminds you to delete the **Imported Notes** folder in Notes first, to avoid duplicates.

On a normal (full) run, only the sections that still have pages to migrate are shown, plus a one-line summary.

### Stopped at the wrong moment?
If you stopped after clicking **Import** (during the import or *"Filing notes into folders…"*), some notes are sitting in a folder called **Imported Notes** in Notes and NoteTransit doesn't know about them.

- **Quick fix:** in Notes, delete the **Imported Notes** folder, then run NoteTransit again. Notes already filed are kept; the rest is imported again. Check for any duplicate notes in the last folder that was being filed.
- **Clean restart** (guaranteed, no duplicates):
  1. In Notes, delete the **Import OneNote** folder and the **Imported Notes** folder (then empty *Recently Deleted* in Notes if you want).
  2. In the NoteTransit folder, delete `migration_state.json` and the `exports` folder.
  3. Keep `cache/` (no need to download again) and `.token_cache.json` (no need to sign in again).
  4. Run NoteTransit again.

### Files in the NoteTransit folder

| File / folder | What it is | Can I delete it? |
|---|---|---|
| `.token_cache.json` *(hidden)* | Your Microsoft sign-in | Yes → you'll have to sign in again |
| `migration_state.json` | Which pages are already in Notes, and the Notes folders created | ⚠️ Only for a clean restart (see above) — otherwise the next run imports everything again (duplicates) |
| `cache/` | Downloaded and converted pages — **a copy of your notes** | Yes → they'll be downloaded again if needed |
| `exports/` | Temporary import files sent to Notes | Yes, anytime it isn't running |
| `migration.log` | Log of everything shown in the Terminal | Yes |
| `.venv/` *(hidden)* | Python tools installed on first run (~50 MB) | Yes → reinstalled automatically next time |

Hidden files: in Finder press **⌘ Shift .** (Command + Shift + period) to show/hide them.

### Cleaning up when everything is done
Once you've checked your notes in Apple Notes (and on your iPhone):
- **Simplest:** move the whole NoteTransit folder to the Trash. Nothing else was installed on your Mac.
- **Keep it for later** (to bring over new OneNote pages someday): delete only `cache/`, `exports/` and `migration.log` — and `.token_cache.json` if you don't want the Microsoft sign-in kept on this Mac. Keep `migration_state.json`.

`cache/` and `migration.log` contain copies of your notes' content: delete them if other people use this Mac.

## Command-line options

From the `English` or `Français` folder, after a first run (which creates `.venv`). Set `NOTETRANSIT_LANG=en` for English messages.

```bash
.venv/bin/python onenote_to_applenotes.py --list                     # list notebooks, writes nothing
.venv/bin/python onenote_to_applenotes.py --list --details           # with section groups and sections
.venv/bin/python onenote_to_applenotes.py --notebook "Travel" --max-pages 3   # test on 3 pages
.venv/bin/python onenote_to_applenotes.py --notebook "Travel"        # one notebook
.venv/bin/python onenote_to_applenotes.py                            # everything
.venv/bin/python onenote_to_applenotes.py --root "From OneNote"      # other root folder name
.venv/bin/python onenote_to_applenotes.py --retry-errors             # retry only the pages that had errors
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
5. **Première connexion à Microsoft** : voir [Connexion à Microsoft](#connexion-à-microsoft-premier-lancement) plus bas.
6. Vos blocs-notes s'affichent. Tapez le nom de l'un d'eux, ou **Entrée** pour tous.
7. Vous pouvez d'abord faire un **essai sur 3 pages** (répondez `o`) et vérifier le résultat dans Notes.
8. NoteTransit fait l'inventaire puis télécharge toutes les pages : rien n'arrive dans Notes pendant ce temps, c'est normal. Microsoft limite le nombre de requêtes par heure, d'où des pauses : laissez faire.
9. Puis **Notes demande « Importer ? » : cliquez sur Importer** (la fenêtre peut être derrière le Terminal). Un clic par lot de 500 notes.
10. NoteTransit range ensuite chaque note dans le bon dossier, tout seul.

Les gros blocs-notes peuvent prendre des heures : laissez le Mac branché, capot ouvert. Il est automatiquement empêché de se mettre en veille pendant la migration.

### Connexion à Microsoft (premier lancement)

1. Le Terminal affiche un message du type :
   `To sign in, use a web browser to open the page https://microsoft.com/devicelogin and enter the code ABCD1234`
2. Ouvrez cette page dans n'importe quel navigateur (sur le Mac ou même sur votre téléphone), tapez le code, et connectez-vous avec le **compte Microsoft qui contient vos blocs-notes OneNote**.
3. Microsoft demande si **« Microsoft Graph Command Line Tools »** peut **lire vos blocs-notes OneNote**. C'est l'identifiant d'application public de Microsoft qu'utilise NoteTransit ; il n'a qu'un accès en lecture (`Notes.Read`). Cliquez sur **Accepter / Oui**.
4. Fermez l'onglet et revenez au Terminal : vos blocs-notes s'affichent.

Bon à savoir :
- Le code expire au bout d'environ 15 minutes. S'il a expiré, fermez le Terminal et relancez.
- La connexion est mémorisée dans le fichier caché `.token_cache.json` du dossier : les lancements suivants ne redemandent rien.
- **Compte professionnel ou scolaire** et message « Approbation de l'administrateur requise » ? Votre organisation bloque cette application : demandez à votre service informatique, ou utilisez votre propre identifiant d'app (voir la section *Using your own Azure app ID* plus haut, en anglais).
- Pour **déconnecter** NoteTransit : supprimez `.token_cache.json`. Pour retirer aussi l'autorisation de votre compte Microsoft : compte personnel → [account.live.com/consent/Manage](https://account.live.com/consent/Manage), retirez « Microsoft Graph Command Line Tools » ; compte pro/école → [myapps.microsoft.com](https://myapps.microsoft.com) ou votre service informatique.

### Arrêter, reprendre, recommencer

**Pour arrêter :** cliquez dans la fenêtre du Terminal et appuyez sur **Contrôle + C** (ou fermez simplement la fenêtre du Terminal). OneNote n'est jamais modifié : arrêter ne peut rien y abîmer.

**Quand peut-on arrêter sans souci ?**

| Ce qu'affiche le Terminal | Arrêt possible ? | Au prochain lancement |
|---|---|---|
| Connexion, liste des blocs-notes, `Lecture de l'arborescence OneNote…`, lignes de sections | ✅ Oui | Tout repart normalement |
| `Téléchargement de N pages…` et les lignes `[12/340] …` | ✅ Oui — **le meilleur moment** | Les pages déjà téléchargées restent dans `cache/` et ne sont pas retéléchargées |
| `Dans Notes, cliquez sur « Importer »` / `Attente de l'import de N notes…` | ⚠️ Seulement **avant** d'avoir cliqué sur Importer : cliquez sur **Annuler** dans la fenêtre de Notes, puis arrêtez | Le lot est simplement préparé à nouveau |
| Après avoir cliqué sur Importer, et pendant `Rangement des notes dans les dossiers…` | ❌ Non — attendez la ligne `=== Lot …` suivante ou `Terminé` | Voir « Arrêté au mauvais moment ? » ci-dessous |
| `Terminé : N notes migrées au total.` | ✅ Fini | Une relance n'ajoute que les **nouvelles** pages OneNote |

Pour reprendre, relancez simplement `Lancer la migration.command` (même dossier, même choix de bloc-notes). Les pages déjà dans Notes sont sautées, à condition de garder `migration_state.json` **et** de ne pas supprimer ni renommer les dossiers créés dans Notes.

**Des pages en erreur à la fin ?**
À la fin, NoteTransit liste les pages qu'il n'a pas pu migrer. Relancez simplement `Lancer la migration.command` : il voit les erreurs et demande **« Réessayer UNIQUEMENT ces pages ? »** — répondez `o`. Il ne relit alors que les sections qui contiennent ces pages, au lieu de parcourir tout OneNote : c'est beaucoup plus rapide.
Si des notes avaient été importées sans être rangées, il vous rappelle de supprimer d'abord le dossier **Notes importées** dans Notes, pour éviter les doublons.

Lors d'un lancement normal (complet), seules les sections qui ont encore des pages à migrer sont affichées, avec un résumé sur une ligne.

**Arrêté au mauvais moment ?**
Si vous avez arrêté après avoir cliqué sur **Importer** (pendant l'import ou le « Rangement des notes dans les dossiers… »), des notes sont restées dans un dossier **Notes importées** et NoteTransit ne le sait pas.

- **Solution rapide :** dans Notes, supprimez le dossier **Notes importées**, puis relancez NoteTransit. Les notes déjà rangées sont gardées, le reste est réimporté. Vérifiez s'il y a des doublons dans le dernier dossier en cours de rangement.
- **Recommencer proprement** (sûr, sans doublons) :
  1. Dans Notes, supprimez le dossier **Import OneNote** et le dossier **Notes importées** (puis videz *Suppressions récentes* dans Notes si vous voulez).
  2. Dans le dossier NoteTransit, supprimez `migration_state.json` et le dossier `exports`.
  3. Gardez `cache/` (pas besoin de retélécharger) et `.token_cache.json` (pas besoin de se reconnecter).
  4. Relancez NoteTransit.

**Les fichiers du dossier NoteTransit**

| Fichier / dossier | Ce que c'est | Je peux le supprimer ? |
|---|---|---|
| `.token_cache.json` *(caché)* | Votre connexion Microsoft | Oui → il faudra se reconnecter |
| `migration_state.json` | Les pages déjà dans Notes et les dossiers créés | ⚠️ Seulement pour recommencer proprement (voir plus haut) — sinon tout est réimporté (doublons) |
| `cache/` | Pages téléchargées et converties — **une copie de vos notes** | Oui → elles seront retéléchargées si besoin |
| `exports/` | Fichiers d'import temporaires envoyés à Notes | Oui, quand l'outil ne tourne pas |
| `migration.log` | Journal de tout ce qui s'est affiché | Oui |
| `.venv/` *(caché)* | Outils Python installés au premier lancement (~50 Mo) | Oui → réinstallé automatiquement |

Fichiers cachés : dans le Finder, appuyez sur **⌘ Maj .** (Commande + Maj + point) pour les afficher ou les masquer.

**Nettoyer quand tout est fini**
Une fois vos notes vérifiées dans Notes (et sur l'iPhone) :
- **Le plus simple :** mettez tout le dossier NoteTransit à la Corbeille. Rien d'autre n'a été installé sur le Mac.
- **Le garder pour plus tard** (pour transférer un jour les nouvelles pages OneNote) : supprimez seulement `cache/`, `exports/` et `migration.log` — et `.token_cache.json` si vous ne voulez pas garder la connexion Microsoft sur ce Mac. Gardez `migration_state.json`.

`cache/` et `migration.log` contiennent une copie du contenu de vos notes : supprimez-les si d'autres personnes utilisent ce Mac.

### Licence et auteur

MIT : libre d'utilisation, de modification et de partage.
Créé par **JLC Solution**. Suggestions et contributions bienvenues.
