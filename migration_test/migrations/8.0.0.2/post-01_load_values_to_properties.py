# -*- coding: utf-8 -*-

from openerp import api, SUPERUSER_ID

from openerp.addons.migration_test.migrations.tools import restore_field_to_property, drop_legacy_tables

# patch needed because of the name with dots of the directory: 8.0.0.3
import sys, os
sys.path.append(os.path.dirname(__file__))

from common import fields_to_property, column_backups

import logging
_logger = logging.getLogger('upgrade')


def migrate(cr, version):
    """
    Restore the property values saved before the update.

    When the variable ODOO_VERIFY_MULTICOMPANY is enabled then check that one
    user of every company can see the same values that before the upgrade.
    """
    if not version:
        return
    VERIFY_MULTICOMPANY_FIELDS = True
    use_extra_table = True  # all values are taken from the legacy (backup) table
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        for model, fields in fields_to_property.items():
            for field in fields:
                restore_field_to_property( env, model, field, use_extra_table,
                verify=VERIFY_MULTICOMPANY_FIELDS)
    drop_legacy_tables(cr, column_backups)
