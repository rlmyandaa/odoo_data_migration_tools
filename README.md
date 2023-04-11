![enter image description here](https://raw.githubusercontent.com/rlmyandaa/odoo_data_migration_tools/master/static/description/icon.png?token=GHSAT0AAAAAACATC3QC67IF3HQYXPGMQTAOZBVCJ6A)
# Odoo Data Migration Tools and Management

Odoo Data Migration Tools and Management. Simple tools for those who do a lot of data migration. With this tools, every data migration is tracked and can be run whether automatically, manually, or even by schedule.

## Features

 - Views to manage migration. Whether you want to create a new migration, rerun old migration, requeue, and reschedule migration.
 - Run migration automatically when upgrading module.
 - Run migration at a certain time by utilising odoo cron job.
 - Error logging in case there are error during migration.

## Configuration

 1. Make sure timezone is set in config file. This will avoid timing error when running migration using schedule. 
	```
	[options]
	...
	timezone = Asia/Tokyo, etc
	```
2. Edit `depends` in this module manifest file, so that this module will depends to all related module where your target migration model is stored.
	```
	'depends': ['base',  'mail', 'module_1', etc],
	```


## Usage
### Quickstart
To create and run migration using this tools, basically you need to do just 3 step.
 1. Create the migration function inside a model
 2. Create the migration record, and point the migration function and model that you already created

### Creating Migration Record
You can create migration either manually in odoo view, or you can define your migration in `migration_list.xml` file in migration_list folder. Sample migration template are provided in `migration_list.xml` file. You can also create a new `.xml` file to store your own migration, just don't forget to declare it on manifest and put it above `migration_trigger.xml` file in manifest.

### Sample Case
Let's say, in res.partner we want to add a new field named `partner_rank` where it will define a partner rank according to how many invoice stored in `invoice_ids` field. To populate partner_rank data for all old res.partner data, we can create a migration by doing these 3 step.

 1. Create this function inside res.partner model
.. code-block:: python
	def migrate_partner_rank(self):
		partners = self.search([])
		for partner in partners:
			if len(partner.invoice_ids) > 5:
				partner.partner_rank = 'regular'
			else:
				partner.partner_rank = 'non regular'

2. Define the migration record, for this example we will define it inside the migration_list.xml data. For this example if we want to execute it when upgrading the module.
	```
	<record id="test_migrate_data_2" model="odoo.data.migration">
		<field name="name">Migrate Partner Rank</field>
		<field name="description">Migrate Partner Rank</field>
		<field name="model_name">res.partner</field>
		<field name="migration_function">migrate_partner_rank</field>
		<field name="running_method">at_upgrade</field>
	</record>
	```
	or if we want to execute it at midnight, we can do this
	```
	<record id="test_migrate_data_2" model="odoo.data.migration">
		<field name="name">Migrate Partner Rank</field>
		<field name="description">Migrate Partner Rank</field>
		<field name="model_name">res.partner</field>
		<field name="migration_function">migrate_partner_rank</field>
		<field name="running_method">cron_job</field>
		<field name="scheduled_running_time">2023-04-11 00:00:00</field>
	</record>
	```
3. Upgrade the module so the migration record will be stored and be executed.

## Changelog
-

## Bug Tracking
Bugs are tracked on  [GitHub Issues](https://github.com/rlmyandaa/odoo_data_migration_tools/issues). In case of trouble, please check there if your issue has already been reported. Any feedback or feature suggestion are welcomed.
