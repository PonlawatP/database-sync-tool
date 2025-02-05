import aiomysql
from config import MYSQL_CONFIG, MARIADB_CONFIG
import logging
from datetime import datetime
import asyncio

import time
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global sync status dictionary
sync_status = {
    "is_running": False,
    "last_sync": None,
    "last_status": None,
    "current_operation": None,
    "progress": 0
}

def update_sync_status(is_running=None, last_sync=None, last_status=None, current_operation=None):
    """Update the sync status dictionary with new values"""
    if is_running is not None:
        sync_status["is_running"] = is_running
    if last_sync is not None:
        sync_status["last_sync"] = last_sync
    if last_status is not None:
        sync_status["last_status"] = last_status
    if current_operation is not None:
        sync_status["current_operation"] = current_operation

async def fake_sync():
    global sync_status
    sync_status["current_operation"] = "Fake sync"
    await asyncio.sleep(5)
    sync_status["current_operation"] = "Syncing tables"
    await asyncio.sleep(5)
    sync_status["current_operation"] = "Syncing data"
    await asyncio.sleep(5)
    sync_status["current_operation"] = "Re-enabling foreign key checks"
    await asyncio.sleep(5)
    sync_status["current_operation"] = "Sync completed"
    await asyncio.sleep(1)
    sync_status.update({
        "is_running": False,
        "last_sync": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "last_status": "success",
        "current_operation": None
    })


async def sync_databases():
    global sync_status
    try:
        sync_status["is_running"] = True
        sync_status["current_operation"] = "Syncing main database"
        
        # Connect to MySQL using aiomysql
        mysql_conn = await aiomysql.connect(**MYSQL_CONFIG)
        mysql_cursor = await mysql_conn.cursor()
        sync_status["progress"] = 10

        sync_status["current_operation"] = "Syncing secondary database"
        # Connect to MariaDB using aiomysql
        mariadb_conn = await aiomysql.connect(**MARIADB_CONFIG)
        mariadb_cursor = await mariadb_conn.cursor()
        sync_status["progress"] = 20

        # Disable foreign key checks
        sync_status["current_operation"] = "Disabling foreign key checks"
        await mariadb_cursor.execute("SET FOREIGN_KEY_CHECKS=0")
        sync_status["progress"] = 22

        # Initialize sync tracking
        sync_status["current_operation"] = "Initializing sync tracking..."
        sync_stats = {
            'tables_created': 0,
            'tables_deleted': 0,
            'tables_synced': 0,
            'rows_synced': 0,
            'failed_tables': []
        }

        # delete all tables from mariadb
        sync_status["current_operation"] = "Deleting all tables from MariaDB"
        await mariadb_cursor.execute("SHOW TABLES")
        tables = await mariadb_cursor.fetchall()
        for table in tables:
            await mariadb_cursor.execute(f"DROP TABLE {table[0]}")
            sync_stats['tables_deleted'] += 1
            sync_status["progress"] = 20 + (8 * sync_stats['tables_deleted'] / len(tables))

        # Get tables from MySQL
        sync_status["current_operation"] = "Getting tables from MySQL"
        await mysql_cursor.execute("SHOW TABLES")
        tables = [table[0] for table in await mysql_cursor.fetchall()]
        sync_status["progress"] = 28

        # First pass: create all tables without data
        sync_status["current_operation"] = "Creating tables..."
        for table in tables:
            sync_status["current_operation"] = f"[{sync_stats['tables_created']}/{len(tables)}] Creating table {table}..."
            sync_status["progress"] = 30 + (20 * sync_stats['tables_created'] / len(tables))
            try:
                await mysql_cursor.execute(f"SHOW CREATE TABLE {table}")
                create_table_sql = (await mysql_cursor.fetchone())[1]
                await mariadb_cursor.execute(create_table_sql)
                logger.info(f"Created table {table} in MariaDB")
                sync_stats['tables_created'] += 1
            except Exception as e:
                logger.error(f"Error creating table {table}: {str(e)}")
                sync_stats['failed_tables'].append(table)

        # Second pass: sync data
        sync_status["current_operation"] = "Syncing data..."
        sync_status["progress"] = 50
        for table in tables:
            if table in sync_stats['failed_tables']:
                continue  # Skip tables that failed to create
            try:
                # Get data from MySQL
                await mysql_cursor.execute(f"SELECT * FROM {table}")
                rows = await mysql_cursor.fetchall()

                sync_status["current_operation"] = f"[{sync_stats['tables_synced']}/{len(tables)}] Syncing {len(rows)} rows from {table}..."
                # Clear MariaDB table
                await mariadb_cursor.execute(f"TRUNCATE TABLE {table}")
                
                # Get column names
                await mysql_cursor.execute(f"SHOW COLUMNS FROM {table}")
                columns = await mysql_cursor.fetchall()
                columns = [f"`{column[0]}`" for column in columns]
                
                # Prepare insert statement
                placeholders = ','.join(['%s' for _ in columns])
                insert_query = f"INSERT INTO {table} ({','.join(columns)}) VALUES ({placeholders})"
                
                # Insert data into MariaDB
                await mariadb_cursor.executemany(insert_query, rows)
                sync_stats['tables_synced'] += 1
                sync_stats['rows_synced'] += len(rows)
                logger.info(f"Synced {len(rows)} rows to table {table}")
                
            except Exception as e:
                logger.error(f"Error syncing table {table}: {str(e)}")
                sync_stats['failed_tables'].append(table)
                sync_status["current_operation"] = f"Error syncing table {table}: {str(e)}"

            sync_status["progress"] = 50 + (45 * sync_stats['tables_synced'] / len(tables))

        # Re-enable foreign key checks
        sync_status["current_operation"] = "Re-enabling foreign key checks..."
        sync_status["progress"] = 100
        await mariadb_cursor.execute("SET FOREIGN_KEY_CHECKS=1")
        await mariadb_conn.commit()
        
        # Log final sync statistics
        logger.info(f"Sync completed. Statistics: {sync_stats}")
        logger.info(f"Tables created: {sync_stats['tables_created']}")
        logger.info(f"Tables synced: {sync_stats['tables_synced']}")
        logger.info(f"Rows synced: {sync_stats['rows_synced']}")
        if sync_stats['failed_tables']:
            logger.warning(f"Failed to sync these tables: {sync_stats['failed_tables']}")
        
    except Exception as e:
        logger.error(f"Error during sync: {str(e)}")
        raise
        
    finally:
        if 'mysql_conn' in locals():
            mysql_conn.close()
        if 'mariadb_conn' in locals():
            mariadb_conn.close() 
        sync_status.update({
            "is_running": False,
            "last_sync": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "last_status": "success",
            "current_operation": None,
            "progress": 0
        })
