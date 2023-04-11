# -*- coding: utf-8 -*-
{
    'name': "Odoo Data Migration Tools",

    'summary': """
        Tools for managing data migration.""",

    'description': """
        Tools for managing data migration.
    """,

    'author': "Hersyanda Putra Adi",
    'website': "http://www.hrsynd.site",
    'category': 'Uncategorized',
    'version': '1.0',
    'installable': True,
    'application': True,

    # Add depends to existing module that needs to be migrated
    'depends': ['base', 'mail'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'migration_list/migration_list.xml',
        'views/reschedule_wizard_view.xml',
        'views/data_migration_view.xml',

        # IMPORTANT : ALWAYS PUT THIS XML AT THE END OF THE DATA LIST
        'migration_list/migration_trigger.xml'
    ],
    # only loaded in demonstration mode
    'demo': [],
    'license': 'AGPL-3',
}
