#SPDX-License-Identifier: MIT
from augur.application import Application
from augur.augurplugin import AugurPlugin
from augur import logger

class BOSSDIPlugin(AugurPlugin):
    """
    This plugin serves as an example as to how to load plugins into Augur
    """
    def __init__(self, augur):
        self.__bossdi = None
        # _augur will be set by the super init
        super().__init__(augur)

    def __call__(self):
        from .bossdi_db import Bossdi
        if self.__bossdi is None:
            logger.debug('Initializing Bossdi')
            self.__bossdi = Bossdi(
                user=self._augur.read_config('Bossdi', 'user', 'AUGUR_BOSSDI_DB_USER', 'bossdi_user'),
                password=self._augur.read_config('Bossdi', 'pass', 'AUGUR_BOSSDI_DB_PASS', '122334'),
                host=self._augur.read_config('Bossdi', 'host', 'AUGUR_BOSSDI_DB_HOST', '0.0.0.0'),
                port=self._augur.read_config('Bossdi', 'port', 'AUGUR_BOSSDI_DB_PORT', '3333'),
                dbname=self._augur.read_config('Bossdi', 'name', 'AUGUR_BOSSDI_DB_NAME', 'bossdi_db'),
                projects=self._augur.read_config('Bossdi', 'projects', None, [])
            )
        return self.__bossdi

BOSSDIPlugin.augur_plugin_meta = {
    'name': 'bossdi',
    'datasource': True
}
Application.register_plugin(BOSSDIPlugin)

__all__ = ['BOSSDIPlugin']