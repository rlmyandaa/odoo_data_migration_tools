# -*- coding: utf-8 -*-

from odoo import models, fields, api


class OdooDataMigrationTest(models.Model):
    _name = 'odoo.data.migration.test'
    _description = 'Odoo Data Migration Test'

    name = fields.Char('Migration Name', required=True)

    def test_unittest_ok(self):
        rec = self.create({
            'name': 'Test'
        })
        return rec

    def test_unittest_nok(self):
        num = 'a'
        int(num)

    @api.model
    def cleanup_data(self):
        data = self.search([])
        data.unlink()
