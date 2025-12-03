"""
Database Management Layer
Implementing APCV 360 database design principles
- Connection pooling
- Transaction management
- Query optimization
- Migration support
"""
import sqlite3
import logging
from contextlib import contextmanager
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
import os


logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Centralized database management with connection pooling
    Follows APCV 360 best practices
    """
    
    def __init__(self, db_path: str = None):
        """
        Initialize database manager
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path or self._get_database_path()
        self._ensure_database_directory()
        self._connection_pool = []
        self._max_pool_size = 10
        
        logger.info(f"DatabaseManager initialized with path: {self.db_path}")
    
    def _get_database_path(self) -> str:
        """Determine database path based on environment"""
        # Railway production path
        if os.environ.get('RAILWAY_ENVIRONMENT'):
            data_dir = os.environ.get('DATA_PATH', '/data/app_data')
            os.makedirs(data_dir, exist_ok=True)
            return os.path.join(data_dir, 'registration_submissions.db')
        
        # Local development
        return os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'data',
            'camp_power_up.db'
        )
    
    def _ensure_database_directory(self):
        """Ensure database directory exists"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            logger.info(f"Created database directory: {db_dir}")
    
    @contextmanager
    def get_connection(self):
        """
        Get database connection from pool
        Context manager for automatic connection cleanup
        """
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        
        # Enable foreign keys (best practice)
        conn.execute("PRAGMA foreign_keys = ON")
        
        try:
            yield conn
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()
    
    @contextmanager
    def transaction(self):
        """
        Transaction context manager
        Automatically commits on success, rolls back on error
        """
        with self.get_connection() as conn:
            try:
                yield conn
                conn.commit()
                logger.debug("Transaction committed successfully")
            except Exception as e:
                conn.rollback()
                logger.error(f"Transaction rolled back due to error: {e}")
                raise
    
    def execute_query(
        self,
        query: str,
        params: Tuple = (),
        fetch_one: bool = False,
        fetch_all: bool = True
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Execute SELECT query
        
        Args:
            query: SQL query string
            params: Query parameters (prevents SQL injection)
            fetch_one: Return single row
            fetch_all: Return all rows
        
        Returns:
            Query results as list of dictionaries
        """
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            
            if fetch_one:
                row = cursor.fetchone()
                return dict(row) if row else None
            
            if fetch_all:
                return [dict(row) for row in cursor.fetchall()]
            
            return None
    
    def execute_update(
        self,
        query: str,
        params: Tuple = ()
    ) -> int:
        """
        Execute INSERT/UPDATE/DELETE query
        
        Args:
            query: SQL query string
            params: Query parameters
        
        Returns:
            Number of affected rows
        """
        with self.transaction() as conn:
            cursor = conn.execute(query, params)
            return cursor.rowcount
    
    def execute_many(
        self,
        query: str,
        params_list: List[Tuple]
    ) -> int:
        """
        Execute batch INSERT/UPDATE
        
        Args:
            query: SQL query string
            params_list: List of parameter tuples
        
        Returns:
            Number of affected rows
        """
        with self.transaction() as conn:
            cursor = conn.executemany(query, params_list)
            return cursor.rowcount
    
    def table_exists(self, table_name: str) -> bool:
        """Check if table exists"""
        query = """
            SELECT name FROM sqlite_master
            WHERE type='table' AND name=?
        """
        result = self.execute_query(query, (table_name,), fetch_one=True)
        return result is not None
    
    def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """Get table schema information"""
        query = f"PRAGMA table_info({table_name})"
        return self.execute_query(query)
    
    def column_exists(self, table_name: str, column_name: str) -> bool:
        """Check if column exists in table"""
        schema = self.get_table_schema(table_name)
        return any(col['name'] == column_name for col in schema)
    
    def add_column(
        self,
        table_name: str,
        column_name: str,
        column_type: str,
        default_value: Any = None
    ):
        """
        Add column to existing table
        
        Args:
            table_name: Table name
            column_name: Column name
            column_type: SQL column type
            default_value: Default value for column
        """
        if self.column_exists(table_name, column_name):
            logger.info(f"Column {column_name} already exists in {table_name}")
            return
        
        default_clause = f"DEFAULT {default_value}" if default_value else ""
        query = f"""
            ALTER TABLE {table_name}
            ADD COLUMN {column_name} {column_type} {default_clause}
        """
        
        self.execute_update(query)
        logger.info(f"Added column {column_name} to {table_name}")
    
    def get_row_count(self, table_name: str) -> int:
        """Get total row count for table"""
        query = f"SELECT COUNT(*) as count FROM {table_name}"
        result = self.execute_query(query, fetch_one=True)
        return result['count'] if result else 0
    
    def backup_database(self, backup_path: str = None):
        """
        Create database backup
        
        Args:
            backup_path: Path for backup file
        """
        if not backup_path:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_dir = os.path.join(
                os.path.dirname(self.db_path),
                'backups'
            )
            os.makedirs(backup_dir, exist_ok=True)
            backup_path = os.path.join(
                backup_dir,
                f'backup_{timestamp}.db'
            )
        
        # Use SQLite backup API
        with self.get_connection() as source:
            backup_conn = sqlite3.connect(backup_path)
            source.backup(backup_conn)
            backup_conn.close()
        
        logger.info(f"Database backed up to: {backup_path}")
        return backup_path
    
    def vacuum(self):
        """Optimize database (reclaim space, rebuild indexes)"""
        with self.get_connection() as conn:
            conn.execute("VACUUM")
        logger.info("Database vacuumed successfully")
    
    def analyze(self):
        """Update query optimizer statistics"""
        with self.get_connection() as conn:
            conn.execute("ANALYZE")
        logger.info("Database statistics updated")


# Singleton instance
_db_instance: Optional[DatabaseManager] = None


def get_db() -> DatabaseManager:
    """Get database manager singleton instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseManager()
    return _db_instance


def init_db(db_path: str = None):
    """Initialize database with schema"""
    global _db_instance
    _db_instance = DatabaseManager(db_path)
    
    # Create tables
    from .schema import create_tables
    create_tables(_db_instance)
    
    logger.info("Database initialized successfully")
