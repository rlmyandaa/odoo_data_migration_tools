# -*- coding: utf-8 -*-

from datetime import datetime
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from enum import Enum, auto
import traceback
import logging

_logger = logging.getLogger(__name__)

class eMigrationStatus(str, Enum):
    queued = auto()
    running = auto()
    done = auto()
    failed = auto()

class OdooDataMigration(models.Model):
    _name = 'odoo.data.migration'
    _description = 'Odoo Data Migration'
    _order = 'id desc'

    name = fields.Char('Migration Name', required=True)
    description = fields.Text('Migration Description')
    model_name_relation = fields.Many2one('ir.model', string='Model Name')
    model_name = fields.Char('Source Model', required=True)
    migration_function = fields.Char('Migration Function', required=True,
                                     help='Migration Function Name in Source Model')
    is_run_at_upgrade = fields.Boolean('Run Migration at Upgrade?', default=False, required=True)
    migration_status = fields.Selection(
        selection=[(eMigrationStatus.queued.name, 'Queued'), (eMigrationStatus.running.name, 'Running'),
                   (eMigrationStatus.done.name, 'Done'), (eMigrationStatus.failed.name, 'Failed')],
        default=eMigrationStatus.queued.name,
        required=True)
    last_run = fields.Datetime('Last Migration Run')
    error_traceback = fields.Text('Error Debug Traceback')
    
    migration_created_date = fields.Datetime('Migration Creation Date')
    
    @api.model
    def create(self, vals):
        result = super().create(vals)
        result.write({
            'migration_created_date': datetime.now()
        })
        return result
    
    @api.constrains('model_name')
    def _validate_model_name(self):
        ir_model_obj : models.Model = self.env['ir.model']
        for record in self:
            domain = [('model', '=', record.model_name)]
            relation = ir_model_obj.search(domain, limit=1)
            if not relation:
                raise ValidationError('Model {} is not found.'.format(self.model_name))
            
            record.write({
                'model_name_relation': relation.id
            })
    
    @api.onchange('model_name_relation')
    def _auto_fill_model_name(self):    
        for record in self:
            record.write({
                'model_name': record.model_name_relation.model
            })
    
    def _auto_init(self):
        # Check if odoo data migration is init
        init = super()._auto_init()
        
        # Run auto upgrade
        auto_upgrade_data : OdooDataMigration = self.search([
            '&',
            ('is_run_at_upgrade', '=', True),
            ('migration_status', '!=', 'done')
        ])
        
        migration_count = len(auto_upgrade_data)
        failed_migration_count = 0
        _logger.info('\nRunning auto migration for {} migration.'.format(migration_count))
        
        
        for index, migration in enumerate(auto_upgrade_data):
            _logger.info('\nRUNNING MIGRATION #{} \nMIGRATION : {} \nDESCRIPTION : {}'.format(
                index + 1, migration.name, migration.description))
            migration.run_migration()
            if migration.migration_status == eMigrationStatus.failed.name:
                failed_migration_count += 1
        
        _logger.info('\nMigration done running\nTOTAL: {}\nSUCCESS: {}\nFAILED: {}'.format(
            migration_count, migration_count - failed_migration_count, failed_migration_count
        ))
        
        return init
    
    def batch_migration(self):
        for record in self:
            record.run_migration()
    
    def run_migration(self):
        self.ensure_one()
        self.mark_running()
        is_exception_raised = False
        migrate = False
        try:
            migrate = api.call_kw(self.env[self.model_name],
                             self.migration_function, args=[[]], kwargs={})
        except Exception as e:
            is_exception_raised = True
            traceback_message = traceback.format_exc()
            self.mark_failed(traceback_message)
        
        if not is_exception_raised:
            self.mark_success()
        
        _logger.info('\nMIGRATION RESULT : {}'.format('FAILED' if is_exception_raised else 'SUCCESS'))
        
        return migrate
    
    def mark_running(self):
        self.write({
            'last_run': datetime.now()
        })
    
    def mark_success(self):
        self.write({
            'migration_status': eMigrationStatus.done.name,
            'error_traceback': ''
        })
    
    def mark_failed(self, error_traceback):
        self.write({
            'migration_status': eMigrationStatus.failed.name,
            'error_traceback': error_traceback
        })
