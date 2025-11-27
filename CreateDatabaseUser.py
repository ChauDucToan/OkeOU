import subprocess
import sys
import shutil
import argparse

DB_USER = "okeou"
DB_HOST = "localhost"
TARGET_PASS = "okeou"


def get_db_command():
    if shutil.which("mariadb"):
        return "mariadb"
    elif shutil.which("mysql"):
        return "mysql"
    else:
        print("Error: Neither 'mariadb' nor 'mysql' command found in PATH.")
        sys.exit(1)


DB_CMD = get_db_command()


def run_query(query):
    try:
        subprocess.run([DB_CMD, "-e", query], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error executing query: {e}")
        sys.exit(1)


def remove_root():
    print(f"Removing user '{DB_USER}'@'{DB_HOST}'...")
    run_query(f"DROP USER IF EXISTS '{DB_USER}'@'{DB_HOST}';")
    print(f"User '{DB_USER}' removed (if it existed).")


def add_root():
    print(f"Creating/Updating user '{DB_USER}'@'{DB_HOST}'...")
    run_query(f"CREATE USER IF NOT EXISTS '{DB_USER}'@'{DB_HOST}' IDENTIFIED BY '{TARGET_PASS}';")
    run_query(f"ALTER USER '{DB_USER}'@'{DB_HOST}' IDENTIFIED BY '{TARGET_PASS}';")
    run_query(f"GRANT ALL PRIVILEGES ON *.* TO '{DB_USER}'@'{DB_HOST}' WITH GRANT OPTION;")
    run_query("FLUSH PRIVILEGES;")
    print(f"Success: User '{DB_USER}' is present with full privileges.")


def show_user():
    run_query("SELECT User, Host FROM mysql.user;")


def main():
    parser = argparse.ArgumentParser(description="Manage Database User Script")
    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument("-a", "--add", action="store_true", help=f"Create or update {DB_USER}")
    group.add_argument("-r", "--remove", action="store_true", help=f"Remove {DB_USER}")
    group.add_argument("-s", "--show", action="store_true", help="Show all users")

    args = parser.parse_args()

    if args.add:
        add_root()
    elif args.remove:
        remove_root()
    elif args.show:
        show_user()


if __name__ == "__main__":
    main()