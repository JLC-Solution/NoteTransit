#!/bin/bash
# Migration OneNote -> Apple Notes : double-cliquez sur ce fichier.
cd "$(dirname "$0")" || exit 1
export NOTETRANSIT_LANG=fr
clear
echo "=== NoteTransit : OneNote -> Apple Notes ==="
echo

if ! python3 -c "import sys" >/dev/null 2>&1; then
  echo "Python n'est pas encore installé sur ce Mac."
  echo "Une fenêtre va proposer d'installer les « outils de ligne de commande » : acceptez,"
  echo "attendez la fin de l'installation, puis relancez ce fichier."
  xcode-select --install 2>/dev/null
  read -r -p "Appuyez sur Entrée pour fermer."
  exit 1
fi

if [ ! -x .venv/bin/python ]; then
  echo "Préparation (une seule fois, environ 1 minute)…"
  python3 -m venv .venv && .venv/bin/pip install -q --disable-pip-version-check -r requirements.txt || {
    echo "La préparation a échoué (connexion internet ?)."; read -r -p "Entrée pour fermer."; exit 1; }
fi

echo
echo "Étape 1 : connexion à votre compte Microsoft et liste de vos blocs-notes."
echo "Rien n'est encore écrit dans Notes."
.venv/bin/python -u onenote_to_applenotes.py --list || { read -r -p "Entrée pour fermer."; exit 1; }

echo
echo "Étape 2 : choix du bloc-notes."
read -r -p "Nom du bloc-notes à migrer (copiez-le depuis la liste ; Entrée = TOUS) : " nb
args=()
[ -n "$nb" ] && args=(--notebook "$nb")

echo
echo "Pendant la migration, Notes demandera « Importer ? » : cliquez sur Importer."
echo "Si macOS demande que « Terminal » contrôle « Notes », cliquez sur OK."
read -r -p "Faire d'abord un ESSAI avec 3 pages seulement ? (o/n) " essai
if [ "$essai" = "o" ] || [ "$essai" = "O" ]; then
  caffeinate -i .venv/bin/python -u onenote_to_applenotes.py "${args[@]}" --max-pages 3 2>&1 | tee -a migration.log
  echo
  echo "Regardez le résultat dans Notes, dossier « Import OneNote »."
  read -r -p "Continuer avec le reste ? (o/n) " suite
  [ "$suite" = "o" ] || [ "$suite" = "O" ] || { read -r -p "Entrée pour fermer."; exit 0; }
fi

caffeinate -i .venv/bin/python -u onenote_to_applenotes.py "${args[@]}" 2>&1 | tee -a migration.log
echo
read -r -p "Terminé. Appuyez sur Entrée pour fermer."
