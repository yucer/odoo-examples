# -*- coding: utf-8 -*-

# fields correspond to: https://redmine.kjellberg-erp.de/issues/4151

fields_to_property = {
    'res.partner': [
        'comment',
    ]
}

table_name = lambda model: model.replace('.','_')

column_backups = dict([( table_name(model), [(f, None) for f in fields])
                       for (model, fields) in fields_to_property.items()])
