FULL_PATH_TO_SCRIPT="$(realpath "${BASH_SOURCE[0]}")"
SCRIPT_DIRECTORY="$(dirname "$FULL_PATH_TO_SCRIPT")"
cd $SCRIPT_DIRECTORY

python3 water.py kill &

source env/bin/activate
kasa --host 192.168.1.44 off
touch ./fail
