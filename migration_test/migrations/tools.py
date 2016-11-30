# -*- coding: utf-8 -*-
# some utilities adapted from OCA/management-system: http://bit.ly/1VsS33p
# those utilites are the same used in openupgrade

import os.path
import inspect

from openerp.osv import orm
from openerp.tools.misc import ustr

import logging
_logger = logging.getLogger('upgrade')


def _get_target_version():
    frm = inspect.stack()[3]
    _, dirname = os.path.split(os.path.dirname(frm[1]))
    target_version = dirname.replace('.', '_')
    return target_version


def get_legacy_name(original_name):
    """Give a temporary name for an object using an odoo module version"""
    _version = _get_target_version()
    return '%s_%s' % (original_name, _version.replace('.', '_'))


def normalize_value(value):
    """Normalize the property value to an id when an object is used"""
    res = value.id if isinstance(value, orm.BaseModel) else value
    return res


def rename_columns(cr, column_spec):
    """
    Renames columns according to the column_spec.

    The column spec is a dictionary whose key is the table name and the values
    are mapping tupples (old_name, new_name). When new_name is None, the name is
    calculated using the odoo version of the update.
    """
    for table in column_spec.keys():
        for (old, new) in column_spec[table]:
            if new is None:
                new = get_legacy_name(old)
            _logger.info("table %s, column %s: renaming to %s", table, old, new)
            cr.execute(
                'ALTER TABLE "%s" RENAME "%s" TO "%s"' %
                (table, old, new,)
            )
            cr.execute(
                'DROP INDEX IF EXISTS "%s_%s_index"' %
                (table, old)
            )


def backup_columns_in_tables(cr, column_spec):
    """
    Drop legacy (backup) tables created to hold temporary the property data
    during the update.

    See the `rename_columns` function for a description of `column_spec`
    """
    sql_fmt = 'CREATE TABLE %(new_table)s AS SELECT %(fields)s FROM %(table)s'
    log_fmt = 'copying from table "%(table)s" to table "%(new_table)s" the columns: %(fields)s'
    for table in column_spec.keys():
        new_table = get_legacy_name(table)
        fields = [field for (field, _) in column_spec[table]]
        fields.append('id')
        params = { 'table': table, 'new_table': new_table,
                   'fields': ', '.join(fields) }
        _logger.info(log_fmt % params )
        sql = sql_fmt % params
        cr.execute(sql)


def drop_legacy_tables(cr, column_spec):
    """
    Drop legacy (backup) tables created to hold temporary the property data
    during the update.

    See the `rename_columns` function for a description of `column_spec`
    """
    for table in column_spec.keys():
        legacy_table = get_legacy_name(table)
        _logger.info("dropping table %s", legacy_table)
        cr.execute('DROP TABLE IF EXISTS "%s"' % legacy_table)


def drop_legacy_columns(cr, column_spec):
    """
    Drop legacy (backup) columns. See the `rename_columns` function for a
    description of `column_spec`
    """
    for table in column_spec.keys():
        for (old, new) in column_spec[table]:
            if new is None:
                new = get_legacy_name(old)
            _logger.info("table %s, dropping column %s", table, new)
            cr.execute(
                'ALTER TABLE "%s" DROP COLUMN "%s" TO "%s"' % (table, new,)
            )
            cr.execute(
                'DROP INDEX IF EXISTS "%s_%s_index"' % (table, new)
            )


def restore_field_to_property(env, model_name, field_name, use_extra_table, verify=True):
    """Restore property values previously saved in a renamed column"""
    # support the use of extra table or renamed columns
    model_obj = env[model_name]
    table_name = model_obj._table
    if use_extra_table:
        table_name = get_legacy_name(table_name)
        legacy_field_name = field_name
    else:
        legacy_field_name = get_legacy_name(field_name)
    # query saved values
    sql_fmt = 'SELECT id as res_id, %(column)s as value FROM %(table)s'
    sql_query = sql_fmt % {'table': table_name, 'column': legacy_field_name}
    env.cr.execute(sql_query)
    values = dict(env.cr.fetchall())
    # set the default value for every company
    if field_name in model_obj._defaults:
        env.cr.execute("SELECT id FROM ir_model_fields WHERE name=%s AND model=%s", (field_name, model_name))
        field_id = env.cr.fetchone()[0]
        field = model_obj._fields[field_name]
        default_value = model_obj._defaults[field_name]
        info_default_fmt = 'setting default value from %(table)s.%(field)s to %(value)s in company with id: %(company_id)s'
        for company in env['res.company'].search([]):
            _logger.info(info_default_fmt % {'table': table_name,
                                             'field': field_name,
                                             'value': default_value,
                                             'company_id': company.id})
            property = env['ir.property'].with_context(force_company=company.id)
            property.create({
                'fields_id': field_id,
                'company_id': company.id,
                'name': field_name,
                'value': default_value,
                'type': field.type,
            })
    # insert the property values for every company
    info_fmt = 'loading values from %(table)s.%(field)s to company with id: %(company_id)s '
    for company in env['res.company'].search([]):
        _logger.info(info_fmt % {'table': table_name,
                                 'field': field_name,
                                 'company_id': company.id})
        property = env['ir.property'].with_context(force_company=company.id)
        property.set_multi(field_name, model_name, values)
    # optional verification of the values' visibility for one user of every company
    if verify:
        user_status_fmt = 'verifying %(count)s values from %(model)s using user: %(login)s'
        user_skip_fmt = 'company_id %(cid)d already tested. Skipping verification for user: %(login)s'
        missmatch_fmt = 'Value missmatch for %(model_name)s in record %(id)d: %(old_value)s != %(new_value)s'
        tested_company_ids = set([])
        for user in env['res.users'].search([]):
            objs =  model_obj.sudo(user.id).search([])
            if user.company_id.id in tested_company_ids:
                _logger.info(user_skip_fmt % {'login': user.login, 'cid': user.company_id.id})
            else:
                _logger.info(user_status_fmt % {'model': model_name, 'count': len(objs), 'login': user.login})
                for obj in objs:
                    old_value = values[obj.id]
                    new_value = getattr(obj, field_name)
                    # normalize the values to compare acording to the field type
                    _field = obj._fields[field_name]
                    old_value = _field.convert_to_cache(old_value, obj, False)
                    old_value = _field.convert_to_read(old_value, True) or False
                    new_value = _field.convert_to_read(new_value, True) or False
                    cmp = {'model_name': model_name,
                           'id': obj.id,
                           'old_value': old_value,
                           'new_value': new_value }
                    assert ustr(cmp['old_value']) == ustr(cmp['new_value']), missmatch_fmt % cmp
                tested_company_ids.add(user.company_id.id)
    _logger.info('all values of %(table)s.%(field)s restored !' % {'table': table_name, 'field': field_name})
