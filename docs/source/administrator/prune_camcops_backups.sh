#!/bin/bash
# prune_camcops_backups.sh
#
# Removes backups except those from the first of the month or within the most
# recent month.

CAMCOPS_BACKUP_DIR=/var/backups/mysql  # edit this
DATABASE_NAME=camcops  # edit this

find "${CAMCOPS_BACKUP_DIR}" \
    -depth \
    -maxdepth 1 \
    -mtime +31 \
    -type f \
    -name "${DATABASE_NAME}_*.sql" \
    -not -name "${DATABASE_NAME}_??????01T??????*.sql" \
    -print

# Explanation:
#
#   find "${CAMCOPS_BACKUP_DIR}"
#       ... find files starting at this directory
#   -depth
#       ... use depth-first processing (implied by "-delete", so use "-depth"
#           explicitly if you might ever use "-delete" with the same command,
#           so results are consistent)
#   -maxdepth 1
#       ... go at most 1 level deep into the starting directory (i.e. look only
#           at the contents of the starting directory)
#   -type f
#       ... find only regular files (not e.g. directories)
#   -mtime +31
#       ... restrict to files whose modification time (mtime) is at least 31
#           days ago (in fact at least 32; see "man find" under "-atime"); we
#           want to ignore younger files
#   -name "${DATABASE_NAME}_*.sql"
#       ... find only files with this base filename spec (case-sensitive; use
#           -iname for insensitive)
#   -not -name "${DATABASE_NAME}_??????01T??????*.sql"
#       ... ignore files dated the first of the month (which we want to keep);
#           the date/time format is YYYYmmddTHHMMSS
#   -print
#       ... for each file found, print the filename; an equivalent is
#           "-exec ls {} \;", which executes "ls <FILENAME>" for each file
#           found
#       ... replace this with "-delete" or "-exec rm {} \;" to delete the files
#
# If you use "-print", piping the output to sort with "| sort" may help.
