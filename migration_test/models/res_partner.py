#-*- coding: utf-8 -*-
from openerp import models, fields, api, exceptions, _

import logging
_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    credit_limit = fields.Float(string='Credit Limit', company_dependet=True),
