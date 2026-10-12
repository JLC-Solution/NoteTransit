#!/bin/bash
# NoteTransit: OneNote -> Apple Notes. Run with:  bash "Start migration.command"
cd "$(dirname "$0")" || exit 1
export NOTETRANSIT_LANG=en
clear
echo "=== NoteTransit: OneNote -> Apple Notes ==="
echo

if ! python3 -c "import sys" >/dev/null 2>&1; then
  echo "Python is not installed on this Mac yet."
  echo "A window will offer to install the \"command line developer tools\": accept,"
  echo "wait for the installation to finish, then run this file again."
  xcode-select --install 2>/dev/null
  read -r -p "Press Enter to close."
  exit 1
fi

if [ ! -x .venv/bin/python ]; then
  echo "Setting up (first time only, about 1 minute)…"
  python3 -m venv .venv && .venv/bin/pip install -q --disable-pip-version-check -r requirements.txt || {
    echo "Setup failed (internet connection?)."; read -r -p "Press Enter to close."; exit 1; }
fi

echo
echo "Step 1: sign in to your Microsoft account and list your notebooks."
echo "Nothing is written to Notes yet."
.venv/bin/python -u onenote_to_applenotes.py --list || { read -r -p "Press Enter to close."; exit 1; }

echo
echo "Step 2: choose the notebook."
read -r -p "Notebook to migrate (copy its name from the list; Enter = ALL): " nb
args=()
[ -n "$nb" ] && args=(--notebook "$nb")

echo
echo "During the migration, Notes will ask \"Import?\": click Import."
echo "If macOS asks to let \"Terminal\" control \"Notes\", click OK."
read -r -p "Run a TEST with only 3 pages first? (y/n) " test
if [ "$test" = "y" ] || [ "$test" = "Y" ]; then
  caffeinate -i .venv/bin/python -u onenote_to_applenotes.py "${args[@]}" --max-pages 3 2>&1 | tee -a migration.log
  echo
  echo "Check the result in Notes, folder \"Import OneNote\"."
  read -r -p "Continue with the rest? (y/n) " more
  [ "$more" = "y" ] || [ "$more" = "Y" ] || { read -r -p "Press Enter to close."; exit 0; }
fi

caffeinate -i .venv/bin/python -u onenote_to_applenotes.py "${args[@]}" 2>&1 | tee -a migration.log
echo
read -r -p "Done. Press Enter to close."
