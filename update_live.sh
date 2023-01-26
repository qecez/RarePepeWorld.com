#!/bin/bash
source_path="/home/rpw/src/RarePepeWorld/"
target_path="/var/www/rpw/run/RarePepeWorld/"

cp -iv "$source_path/rpw/DataConnectors.py" "$target_path/rpw/"
cp -iv "$source_path/rpw/QueryTools.py" "$target_path/rpw/"
cp -iv "$source_path/rpw/Utils.py" "$target_path/rpw/"
cp -iv "$source_path/rpw/ViewsData.py" "$target_path/rpw/"
cp -iv "$source_path/rpw/app.py" "$target_path/rpw/"
cp -iv "$source_path/Settings.py_live"  "$target_path/Settings.py"
cp -iv "$source_path/run.sh_live"  "$target_path/run.sh"
cp -iv "$source_path/rpw/Logging.py" "$target_path"

rsync -av --progress --delete "$source_path/templates/" "$target_path/templates/"

