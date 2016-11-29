# -*- coding: utf-8 -*-
# some utilities adapted from openupgrade: http://bit.ly/1VsS33p

from openerp.addons.migration_test.migrations.tools import backup_columns_in_tables


# patch needed because of the name with dots of the directory: 8.0.0.3
import sys, os
sys.path.append(os.path.dirname(__file__))

from common import column_backups


import logging
_logger = logging.getLogger('upgrade')


def migrate(cr, version):
    """
    Save the property values before the update.

    Two methods are available for that in `migration.tools`: `rename_columns`
    and `backup_columns_in_tables`. The first one keeps the values in renamed
    columns from the same table. The second one uses a temporary table.
    """
    if not version:
        return
    backup_columns_in_tables(cr, column_backups, version )
