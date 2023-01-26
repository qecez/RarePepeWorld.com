#!/usr/bin/env python
import sys, os
import os
import time
from pathlib import Path

os.environ['RPW_SCRIPT_BASE'] = str(Path(os.getcwd()).parent)
os.environ['RPW_LOG_PATH'] = str(Path(os.getcwd()).parent / 'logs/')
os.environ['RPW_LOG_LEVEL'] = 'DEBUG'

sys.path.insert(0, os.environ['HOME'] + '/RarePepeWorld/')  # Run path
# from rpw import Settings
import Settings

def combine_files(self, file1, file2):
    with open('file1', 'w') as outfile:
        with open(file2) as infile:
            for line in infile:
                outfile.write(line)


def get_dbcopy():
    file_stamp = time.strftime('%Y-%m-%d-%I:%M')

    script_dir = os.path.dirname(os.path.realpath(__file__))
    db_user = Settings.Sources['mysql']['user']
    db_password = Settings.Sources['mysql']['password']
    db_host = Settings.Sources['mysql']['host']
    db_database = Settings.Sources['mysql']['database_name']
    dump_file = script_dir + "/" + db_database + "_" + file_stamp + ".sql"
    os.popen(
        f"mysqldump -u {db_user} "
        f"-p{db_password}"
        f"-h {db_host} "
        f"--default-character-set=utf8 "
        f"--ignore-table={db_database}.log {db_database} "
        f"--result-file {dump_file}")
    print("\n-- The dump file has been created @ " + dump_file + " --")


if __name__ == "__main__":
    get_dbcopy()
