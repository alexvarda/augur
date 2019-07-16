
import sqlalchemy as s
from augur import logger

class Bossdi(object):
    """Queries BOSSDI database"""

      def __init__(self, user, password, host, port, dbname, projects=None):
        """
        Connect to the database

        :param dbstr: The [database string](http://docs.sqlalchemy.org/en/latest/core/engines.html) to connect to the GHTorrent database
        """
        self.DB_STR = 'sqlite+pysqlite://{}:{}@{}:{}/{}'.format(
            user, password, port, dbname
        )
        logger.debug('BOSSDI: Connecting to {}:{}/{} as {}'.format(host, port, dbname, user))
        self.db = s.create_engine(self.DB_STR, poolclass=s.pool.NullPool)
        self.projects = projects

        