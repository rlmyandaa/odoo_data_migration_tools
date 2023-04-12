# -*- coding: utf-8 -*-

from odoo.exceptions import ValidationError
from odoo.tests.common import tagged

from ..utils.enum import eMigrationStatus
from .test_common import TestOdooDataMigrationCommon


@tagged('test_odoo_data_migration', 'post_install', '-at_install')
class TestOdooDataMigration(TestOdooDataMigrationCommon):
    def setUp(cls):
        super(TestOdooDataMigration, cls).setUp()

    def test_1_create_and_run_migration_ok(self):
        # Create a migration record
        migration_record = self._create_migration_at_upgrade(
            migration_name='Test Migration 1 At Upgrade',
            model_name=self.TEST_MODEL_NAME,
            function_name='test_unittest_ok')

        # Run the migration
        migration_record.run_migration()

        # Check migration result
        # This sample migration should create a new record in test model
        self.assertEqual(
            migration_record.migration_status,
            eMigrationStatus.done.name)
        test_record = self.TEST_MODEL_OBJ.search([])
        self.assertEqual(len(test_record), 1)
        self.assertEqual(test_record.name, 'Test')

        # Cleanup
        self.TEST_MODEL_OBJ.cleanup_data()

    def test_2_create_and_run_migration_nok_1(self):
        # Create a migration record
        # Trigger the error using not ok function
        migration_record = self._create_migration_at_upgrade(
            migration_name='Test Migration 2 At Upgrade NOK Function',
            model_name=self.TEST_MODEL_NAME,
            function_name='test_unittest_nok')

        # Run the migration
        migration_record.run_migration()

        # Check migration result
        # This sample migration should output error due to it's trying to
        # convert 'a' to integer value
        self.assertEqual(
            migration_record.migration_status,
            eMigrationStatus.failed.name)
        self.assertTrue(len(migration_record.error_traceback) > 0)

        # Cleanup
        self.TEST_MODEL_OBJ.cleanup_data()

    def test_3_create_and_run_migration_nok_2(self):
        # Create a migration record
        # Trigger the error using undefined function in target model
        migration_record = self._create_migration_at_upgrade(
            migration_name='Test Migration 3 At Upgrade NOK Undefined Function',
            model_name=self.TEST_MODEL_NAME,
            function_name='test_unittest_nok_undefined')

        # Run the migration
        migration_record.run_migration()

        # Check migration result
        # This sample migration should output error due to the function is
        # undefined
        self.assertEqual(
            migration_record.migration_status,
            eMigrationStatus.failed.name)
        self.assertTrue(len(migration_record.error_traceback) > 0)

        # Cleanup
        self.TEST_MODEL_OBJ.cleanup_data()

    def test_4_test_migration_constrain(self):
        # Create a migration record
        # Trigger the error using undefined model name
        with self.assertRaises(ValidationError):
            migration_record = self._create_migration_at_upgrade(
                migration_name='Test Migration 3 At Upgrade NOK Undefined Model',
                model_name='undefined.model.name',
                function_name='test_unittest_nok_undefined')

        # Create a migration record
        # Trigger the error using runing method cron_job without scheduled time
        with self.assertRaises(ValidationError):
            migration_record = self._create_migration_with_cron(
                migration_name='Test Migration 3 At Upgrade NOK Cron to Scheduled Time',
                model_name=self.TEST_MODEL_NAME,
                function_name='test_unittest_nok')

        # Cleanup
        self.TEST_MODEL_OBJ.cleanup_data()

    def test_5_test_migration_model_autofill(self):
        # Create a migration record
        # Check model relation autofill, if we create by defining model_name,
        # the model relation to ir_model_data should be automatically filled.
        migration_record = self._create_migration_at_upgrade(
            migration_name='Test Migration 3 At Upgrade Autofill',
            model_name=self.TEST_MODEL_NAME,
            function_name='test_unittest_ok')

        self.assertIsNotNone(migration_record.model_name_relation)

        # Cleanup
        self.TEST_MODEL_OBJ.cleanup_data()
