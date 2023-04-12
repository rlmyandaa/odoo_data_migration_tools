# -*- coding: utf-8 -*-

from datetime import datetime

from odoo.tests.common import TransactionCase
from odoo.tools.config import config

from ..models.data_migration_model import OdooDataMigration
from ..models.data_migration_test import OdooDataMigrationTest
from ..utils.enum import eRunningMethod


class TestOdooDataMigrationCommon(TransactionCase):
    def setUp(cls):
        super(TestOdooDataMigrationCommon, cls).setUp()
        cls.DATA_MIGRATION_MODEL: OdooDataMigration = cls.env['odoo.data.migration']
        cls.TEST_MODEL_NAME: str = 'odoo.data.migration.test'
        cls.TEST_MODEL_OBJ: OdooDataMigrationTest = cls.env['odoo.data.migration.test']
        # Cleanup data
        cls.TEST_MODEL_OBJ.cleanup_data()

    def _create_migration_at_upgrade(
            cls,
            migration_name: str,
            model_name: str,
            function_name: str):
        payload = {
            'name': migration_name,
            'description': migration_name,
            'model_name': model_name,
            'migration_function': function_name,
            'running_method': eRunningMethod.at_upgrade.name
        }
        migration_record = cls.DATA_MIGRATION_MODEL.create(payload)
        return migration_record

    def _create_migration_with_cron(
            cls,
            migration_name: str,
            model_name: str,
            function_name: str,
            scheduled_running_time: datetime = False):
        payload = {
            'name': migration_name,
            'description': migration_name,
            'model_name': model_name,
            'migration_function': function_name,
            'running_method': eRunningMethod.cron_job.name,
            'scheduled_running_time': scheduled_running_time
        }
        migration_record = cls.DATA_MIGRATION_MODEL.with_context(
            tz=config.get('timezone') or 'UTC').create(payload)
        return migration_record
