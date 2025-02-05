import configparser
import os

# Determine the config file path. Adjust if needed.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(BASE_DIR, 'config', 'config.ini')

# Disable interpolation to handle special characters (like %)
config = configparser.ConfigParser(interpolation=None)
config.read(config_path)

# MySQL Configuration
MYSQL_CONFIG = {
    'host': config.get('mysql', 'host', fallback='localhost'),
    'user': config.get('mysql', 'user', fallback='root'),
    'password': config.get('mysql', 'password', fallback=''),
    'db': config.get('mysql', 'database', fallback='db_name'),
    'autocommit': True
}

# MariaDB Configuration
MARIADB_CONFIG = {
    'host': config.get('mariadb', 'host', fallback='localhost'),
    'user': config.get('mariadb', 'user', fallback='root'),
    'password': config.get('mariadb', 'password', fallback=''),
    'db': config.get('mariadb', 'database', fallback='db_name'),
    'autocommit': True
} 