# -*- coding: utf-8 -*-

from odoo import models, fields, api
from ..utils.enum import eRunningMethod


class RescheduleMigrationWizard(models.TransientModel):
    _name = 'reschedule.migration.wizard'
    _description = 'Reschedule Migration Wizard'

    data_migration_record = fields.Many2one(
        'odoo.data.migration', string='Data Migration Record',
        required=True,
        default=lambda self: self.env.context.get('active_id')
    )
    rescheduled_time = fields.Datetime(string="Rescheduled Time",
                                       required=True)

    @api.onchange('data_migration_record')
    def _autofill_rescheduled_time(self):
        for record in self:
            record.rescheduled_time = record.data_migration_record.scheduled_running_time

    def reschedule_cron(self):
        self.ensure_one()
        self.data_migration_record.requeue_migration()
        self.data_migration_record.write({
            'running_method': eRunningMethod.cron_job.name,
            'scheduled_running_time': self.rescheduled_time
        })
        if not self.data_migration_record.ir_cron_reference:
            ir_cron_reference = self.data_migration_record._create_cron_data()
            self.data_migration_record.write({
                'ir_cron_reference': ir_cron_reference
            })

        self.data_migration_record.ir_cron_reference.write({
            'active': True,
            'numbercall': 1,
            'nextcall': self.rescheduled_time
        })
