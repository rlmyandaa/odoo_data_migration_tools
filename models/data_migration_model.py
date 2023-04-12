# -*- coding: utf-8 -*-

import logging
import traceback
from datetime import datetime

import pytz
from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.config import config

from ..utils.enum import eMigrationStatus, eRunningMethod
from ..utils.timezone_convert import convert_datetime_data

_logger = logging.getLogger(__name__)


class OdooDataMigration(models.Model):
    _name = 'odoo.data.migration'
    _description = 'Odoo Data Migration'
    _order = 'id desc'

    name = fields.Char('Migration Name', required=True)
    description = fields.Text('Migration Description')
    model_name_relation = fields.Many2one('ir.model', string='Model Name')
    model_name = fields.Char('Source Model', required=True)
    migration_function = fields.Char(
        'Migration Function',
        required=True,
        help='Migration Function Name in Source Model')
    migration_status = fields.Selection(
        selection=[
            (eMigrationStatus.cancelled.name,
             'Cancelled'),
            (eMigrationStatus.queued.name,
             'Queued'),
            (eMigrationStatus.running.name,
             'Running'),
            (eMigrationStatus.done.name,
             'Done'),
            (eMigrationStatus.failed.name,
             'Failed')],
        default=eMigrationStatus.queued.name,
        required=True)
    last_run = fields.Datetime('Last Migration Run')
    error_traceback = fields.Text('Error Debug Traceback')
    migration_created_date = fields.Datetime('Migration Creation Date')
    scheduled_running_time = fields.Datetime(
        'Scheduled Running Time',
        help='You need to use reschedule menu to change scheduled\
                                                 running time for migration that using cron job.')
    ir_cron_reference = fields.Many2one('ir.cron', string='Ir Cron Record')
    running_method = fields.Selection(
        string='Migration Running Method',
        selection=[
            (eRunningMethod.at_upgrade.name,
             'at Upgrade'),
            (eRunningMethod.cron_job.name,
             'Cron Job')],
        required=True,
        default=eRunningMethod.at_upgrade.name)

    ####################################
    # Compute function
    ####################################
    @api.constrains('running_method', 'scheduled_running_time')
    def _validate_running_method(self):
        """ Validate running_method for the migration records. """
        for record in self:
            # If using cron, make sure time is exist
            if record.running_method == eRunningMethod.cron_job.name and not record.scheduled_running_time:
                raise ValidationError(
                    'Running using cron needs to specify time of execution.')

    @api.constrains('model_name')
    def _validate_model_name(self):
        """ Validate model name, and also fill out the model relation data to ir.model. """
        ir_model_obj: models.Model = self.env['ir.model']
        for record in self:
            domain = [('model', '=', record.model_name)]
            relation = ir_model_obj.search(domain, limit=1)
            if not relation:
                raise ValidationError(
                    'Model {} is not found.'.format(
                        self.model_name))

            record.write({
                'model_name_relation': relation.id
            })

    @api.onchange('model_name_relation')
    def _auto_fill_model_name(self):
        """ Autofill model_name field after selection model. Used in view to add
        better UX.
        """
        for record in self:
            record.write({
                'model_name': record.model_name_relation.model
            })

    ####################################
    # Main Migration Function
    ####################################

    @api.model
    def create(self, vals):
        # In case if we add the record from xml data, we need to parse
        # the datetime field since every datetime that will be saved in
        # db should be in UTC.
        # First, determine if there are any timezone context first, if the records
        # are created from xml data, there should be no timezone context.
        # But if the record is created from the view, there should be timezone
        # context.

        # First, convert the datetime from payload
        if not self.env.context.get('tz', False):
            convert_datetime_data(vals)
        result = super().create(vals)

        # Add migration date data
        result.write({
            'migration_created_date': datetime.now()
        })

        # Look for record that is using cron as the running method,
        # then create ir_cron record data so it will be executed
        # through odoo cron job.
        cron_result: OdooDataMigration = result.filtered_domain([
            '&',
            ('running_method', '=', eRunningMethod.cron_job.name),
            ('scheduled_running_time', '!=', False)
        ])
        for migration in cron_result:
            # Create cron job record
            ir_cron_record = migration._create_cron_data()
            # Add cron job record reference
            migration.write({
                'ir_cron_reference': ir_cron_record
            })

        return result

    def write(self, vals_list):
        # In case when changing migration from at_upgrade to using cron_job,
        # auto add new ir_cron record.
        result = super().write(vals_list)
        cron_migration: OdooDataMigration = self.filtered_domain([
            '&',
            '&',
            ('running_method', '=', eRunningMethod.cron_job.name),
            ('scheduled_running_time', '!=', False),
            ('ir_cron_reference', '=', False)
        ])
        for record in cron_migration:
            cron_record = record._create_cron_data()
            record.ir_cron_reference = cron_record

        return result

    @api.model
    def trigger_migration_upgrade(self):
        """
        Main trigger function to run migration when upgrading the module.
        All migration records that in queue and using running_method at_upgrade
        will be migrated during module upgrading process.
        """
        # Run auto upgrade
        auto_upgrade_data: OdooDataMigration = self.search([
            '&',
            ('running_method', '=', eRunningMethod.at_upgrade.name),
            ('migration_status', '=', eMigrationStatus.queued.name)
        ])

        migration_count = len(auto_upgrade_data)
        failed_migration_count = 0
        _logger.info(
            '\nRunning auto migration for {} migration.'.format(migration_count))

        for index, migration in enumerate(auto_upgrade_data):
            _logger.info(
                '\nRUNNING MIGRATION #{} \nMIGRATION : {} \nDESCRIPTION : {}'.format(
                    index + 1, migration.name, migration.description))
            migration.run_migration()
            if migration.migration_status == eMigrationStatus.failed.name:
                failed_migration_count += 1

        _logger.info(
            '\nMigration done running\nTOTAL: {}\nSUCCESS: {}\nFAILED: {}'.format(
                migration_count,
                migration_count -
                failed_migration_count,
                failed_migration_count))

        return True

    def batch_migration(self):
        """
        Function to run migration as batch. Used for contextual action button
        in list view.
        """
        for record in self:
            record.run_migration()
            # Deactivate cron record so migration won't run twice
            record._deactivate_cron()

    def run_migration(self):
        """ Main migration running function. """

        self.ensure_one()
        # Mark migration as running
        self.mark_running()

        is_exception_raised = False
        migrate = False
        _logger.info('\\STARTING MIGRATION : {} \nDESCRIPTION : {}'.format(
            self.name, self.description))

        # Try to run migration
        try:
            migrate = api.call_kw(self.env[self.model_name],
                                  self.migration_function, args=[[]], kwargs={})
        except Exception as e:
            is_exception_raised = True
            traceback_message = traceback.format_exc()
            # If failed, mark failed and log the traceback message
            self.mark_failed(traceback_message)

        # Check if exception raised
        if not is_exception_raised:
            self.mark_success()

        _logger.info('\nMIGRATION RESULT : {}'.format(
            'FAILED' if is_exception_raised else 'SUCCESS'))

        return migrate

    ####################################
    # Utils
    ####################################

    def _create_cron_data(self):
        self.ensure_one()
        payload = {
            'name': 'Scheduled Migration - ' + self.name,
            'model_id': self.env.ref('odoo_data_migration.model_odoo_data_migration').id,
            # 'user_id': self.env.ref('base.user_root').id,
            'state': 'code',
            'code': "rec = env['odoo.data.migration'].browse({}).run_migration()".format(self.id),
            'interval_number': 0,
            'active': True,
            'numbercall': 1,
            'nextcall': self.scheduled_running_time
        }
        ir_cron_data = self.env['ir.cron'].create(payload)
        return ir_cron_data

    def mark_running(self):
        """ Mark migration records as running. """
        self.write({
            'migration_status': eMigrationStatus.running.name,
            'last_run': datetime.now()
        })
        # Commit to avoid running error when using cron
        self.env.cr.commit()

    def mark_success(self):
        """ Mark migration records as success. """
        self.write({
            'migration_status': eMigrationStatus.done.name,
            'error_traceback': ''
        })
        # Commit to avoid running error when using cron
        self.env.cr.commit()

    def mark_failed(self, error_traceback):
        """ Mark migration records as failed, also log the error traceback. """
        self.write({
            'migration_status': eMigrationStatus.failed.name,
            'error_traceback': error_traceback
        })
        # Commit to avoid running error when using cron
        self.env.cr.commit()

    def requeue_migration(self):
        """ Requeue migration. With this, every migration that use running_method
        at upgrade will be run in the next upgrade.
        """
        self.write({
            'migration_status': eMigrationStatus.queued.name
        })

    def _deactivate_cron(self):
        """ Deactivate cron record. """
        self.ensure_one()
        if self.ir_cron_reference:
            self.ir_cron_reference.write({
                'active': False,
                'numbercall': 0
            })

    def batch_cancel_migration(self):
        """
        Function to cancel migration as batch. Used for contextual action button
        in list view.
        """
        for record in self:
            if record.migration_status not in [
                    eMigrationStatus.done.name,
                    eMigrationStatus.running.name,
                    eMigrationStatus.cancelled.name]:
                record.cancel_migration()

    def cancel_migration(self):
        """ Cancel migration. """
        self.ensure_one()
        if self.running_method == eRunningMethod.cron_job.name:
            try:
                self._deactivate_cron()
                self.write({
                    'migration_status': eMigrationStatus.cancelled.name
                })
            except Exception:
                raise ValidationError(
                    "Cron failed to cancel. The cron job might currently still running.")
        else:
            self.write({
                'migration_status': eMigrationStatus.cancelled.name
            })
