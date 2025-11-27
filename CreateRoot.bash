#!/bin/bash

DB_USER="okeou"
DB_HOST="localhost"
TARGET_PASS="okeou"

if command -v mariadb &> /dev/null; then
    DB_CMD="mariadb"
    echo "Using command: mariadb"
else
    DB_CMD="mysql"
    echo "Using command: mysql"
fi

function remove_root() {
  echo "Removing user '${DB_USER}'@'${DB_HOST}'..."
  $DB_CMD -e "DROP USER IF EXISTS '${DB_USER}'@'${DB_HOST}';"
  echo "User '${DB_USER}' removed (if it existed)."
  exit 0
}

function add_root() {
  $DB_CMD -e "CREATE USER IF NOT EXISTS '${DB_USER}'@'${DB_HOST}' IDENTIFIED BY '${TARGET_PASS}';"
  $DB_CMD -e "ALTER USER '${DB_USER}'@'${DB_HOST}' IDENTIFIED BY '${TARGET_PASS}';"
  $DB_CMD -e "GRANT ALL PRIVILEGES ON *.* TO '${DB_USER}'@'${DB_HOST}' WITH GRANT OPTION;"
  $DB_CMD -e "FLUSH PRIVILEGES;"
  echo "Success: User '${DB_USER}' is present with full privileges."
  exit 0
}

function show_user() {
  $DB_CMD -e "SELECT User, Host FROM mysql.user;"
  exit 0
}

case $1 in
"-r"|"--remove")
  remove_root
  ;;
"-a"|"--add")
  add_root
  ;;
"-s"|"--show")
  show_user
  ;;
*)
  echo "Usage: $0 [option]"
  echo -e "  -a, --add\tCreate or update the ${DB_USER} user with full privileges"
  echo -e "  -r, --remove\tRemove the ${DB_USER} user from MySQL"
  exit 1
  ;;
esac

