FULL_PATH_TO_SCRIPT="$(realpath "${BASH_SOURCE[0]}")"
SCRIPT_DIRECTORY="$(dirname "$FULL_PATH_TO_SCRIPT")"
cd $SCRIPT_DIRECTORY

source env/bin/activate
kasa --host 192.168.1.44 on
rm -f ./fail
