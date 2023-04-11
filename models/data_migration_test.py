# -*- coding: utf-8 -*-

from odoo import models, fields, api


class OdooDataMigrationTest(models.Model):
    _name = 'odoo.data.migration.test'
    _description = 'Odoo Data Migration Test'

    name = fields.Char('Migration Name', required=True)

    def test_run(self):
        print("YOLO")
