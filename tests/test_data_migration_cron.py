# -*- coding: utf-8 -*-

from datetime import datetime

from dateutil.relativedelta import relativedelta
from odoo.tests.common import tagged
from odoo.tools.config import config

from ...base.models.ir_actions import IrActionsServer
from ...base.models.ir_cron import ir_cron
from ..models.reschedule_wizard import RescheduleMigrationWizard
from ..utils.enum import eMigrationStatus, eRunningMethod
from .test_common import TestOdooDataMigrationCommon


@tagged('test_odoo_data_migration',
        'test_odoo_data_migration_cron',
        'post_install',
        '-at_install')
class TestOdooDataMigrationCron(TestOdooDataMigrationCommon):
    def setUp(cls):
        super(TestOdooDataMigrationCron, cls).setUp()
        cls.RESCHEDULE_WIZARD_MODEL: RescheduleMigrationWizard = cls.env[
            'reschedule.migration.wizard']

    def test_1_create_and_run_migration_cron_ok(self):
        # Create a migration record
        migration_name = 'Test Migration 1 Cron'
        scheduled_running_time = datetime.now() + relativedelta(minutes=1)
        migration_record = self._create_migration_with_cron(
            migration_name=migration_name,
            model_name=self.TEST_MODEL_NAME,
            function_name='test_unittest_ok',
            scheduled_running_time=scheduled_running_time)

        # Check the created record, should have ir_cron_record
        self.assertIsNotNone(migration_record)
        self.assertIsNotNone(migration_record.ir_cron_reference)
        ir_cron_ref: ir_cron = migration_record.ir_cron_reference
        self.assertEqual(ir_cron_ref.active, True)
        self.assertEqual(ir_cron_ref.numbercall, 1)
        self.assertEqual(ir_cron_ref.cron_name,
                         'Scheduled Migration - {}'.format(migration_name))
        self.assertEqual(ir_cron_ref.nextcall, scheduled_running_time)

        ir_cron_action_ref: IrActionsServer = ir_cron_ref.ir_actions_server_id
        self.assertEqual(
            ir_cron_ref.model_id.model,
            self.DATA_MIGRATION_MODEL._name)
        self.assertEqual(
            ir_cron_action_ref.code,
            "rec = env['odoo.data.migration'].browse({}).run_migration()".format(
                migration_record.id))

        # Try to run the cron by immediately trigger run cron, due to we can't
        # wait cron to run
        ir_cron_ref.method_direct_trigger()

        # Validate migration result
        # This sample migration should create a new record in test model
        self.assertEqual(
            migration_record.migration_status,
            eMigrationStatus.done.name)
        test_record = self.TEST_MODEL_OBJ.search([])
        self.assertEqual(len(test_record), 1)
        self.assertEqual(test_record.name, 'Test')

        # Cleanup
        self.TEST_MODEL_OBJ.cleanup_data()

    def test_2_change_at_upgrade_to_cron_migration(self):
        # First, create a migration using running_method at_upgrade, then change it to cron_job.
        # Initially, it won't have ir_cron_record, so we need to add
        # ir_cron_record first.
        migration_name = 'Test Migration 2 At Upgrade to Cron'
        initial_migration_record = self._create_migration_at_upgrade(
            migration_name=migration_name,
            model_name=self.TEST_MODEL_NAME,
            function_name='test_unittest_ok')
        self.assertIsNotNone(initial_migration_record)
        self.assertFalse(initial_migration_record.ir_cron_reference)
        self.assertFalse(initial_migration_record.scheduled_running_time)

        # Then, change it to cron job. It should be now have ir_cron reference
        scheduled_running_time = datetime.now() + relativedelta(minutes=10)
        # Pass the timezone context so that it won't be reconverted again since
        # datetime.now() output in utc
        initial_migration_record.with_context(tz=config.get('timezone') or 'UTC').write({
            'running_method': eRunningMethod.cron_job.name,
            'scheduled_running_time': scheduled_running_time
        })

        # Check result
        self.assertIsNotNone(initial_migration_record.ir_cron_reference)
        ir_cron_ref: ir_cron = initial_migration_record.ir_cron_reference
        self.assertEqual(ir_cron_ref.active, True)
        self.assertEqual(ir_cron_ref.numbercall, 1)
        self.assertEqual(ir_cron_ref.cron_name,
                         'Scheduled Migration - {}'.format(migration_name))
        self.assertEqual(ir_cron_ref.nextcall, scheduled_running_time)

        ir_cron_action_ref: IrActionsServer = ir_cron_ref.ir_actions_server_id
        self.assertEqual(
            ir_cron_ref.model_id.model,
            self.DATA_MIGRATION_MODEL._name)
        self.assertEqual(
            ir_cron_action_ref.code,
            "rec = env['odoo.data.migration'].browse({}).run_migration()".format(
                initial_migration_record.id))

        # Cleanup
        self.TEST_MODEL_OBJ.cleanup_data()

    def test_3_reschedule_cron_migration(self):
        # First create a migration using running_method cron_job. Then reschedule it, the nextcall
        # should be follow the rescheduled time
        # Create a migration record
        migration_name = 'Test Migration 3 Reschedule Cron'
        scheduled_running_time = datetime.now() + relativedelta(minutes=1)
        migration_record = self._create_migration_with_cron(
            migration_name=migration_name,
            model_name=self.TEST_MODEL_NAME,
            function_name='test_unittest_ok',
            scheduled_running_time=scheduled_running_time)

        # Check the created record, should have ir_cron_record
        self.assertIsNotNone(migration_record)
        self.assertIsNotNone(migration_record.ir_cron_reference)
        ir_cron_ref: ir_cron = migration_record.ir_cron_reference
        self.assertEqual(ir_cron_ref.active, True)
        self.assertEqual(ir_cron_ref.numbercall, 1)
        self.assertEqual(ir_cron_ref.cron_name,
                         'Scheduled Migration - {}'.format(migration_name))
        self.assertEqual(ir_cron_ref.nextcall, scheduled_running_time)

        # Now, try to reschedule it
        new_scheduled_running_time = datetime.now() + relativedelta(minutes=10)
        reschedule_wizard = self.RESCHEDULE_WIZARD_MODEL.create({
            'data_migration_record': migration_record.id,
            'rescheduled_time': new_scheduled_running_time
        }).reschedule_cron()

        # Validate rescheduling result
        ir_cron_ref: ir_cron = migration_record.ir_cron_reference
        self.assertEqual(ir_cron_ref.active, True)
        self.assertEqual(ir_cron_ref.numbercall, 1)
        self.assertEqual(ir_cron_ref.nextcall, new_scheduled_running_time)

        # Cleanup
        self.TEST_MODEL_OBJ.cleanup_data()
