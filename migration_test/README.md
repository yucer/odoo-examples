# migration_test module

It contains two [migration script folders](https://github.com/yucer/odoo-examples/tree/8.0_company_dependent_mig/migration_test/migrations). It was developed for version 8.0 but it should work also in higher versions.

Two migrations scripts are used:

1. A **pre-update** script: [pre-01_save_values_for_company_fields.py](https://github.com/yucer/odoo-examples/blob/8.0_company_dependent_mig/migration_test/migrations/8.0.0.2/pre-01_save_values_for_company_fields.py) that saves a backup of the affected fields in a _temporary table_, before the update.

2. A **post-update** script: [post-01_load_values_to_properties.py](https://github.com/yucer/odoo-examples/blob/8.0_company_dependent_mig/migration_test/migrations/8.0.0.2/post-01_load_values_to_properties.py) that assign back the values to the corresponding **ir.property** records.

Some notes:

- The list of fields that change simultaneously to **company_dependent=True** are specified in  [common.py](https://github.com/yucer/odoo-examples/blob/8.0_company_dependent_mig/migration_test/migrations/8.0.0.2/common.py), a python module accessible to both pre- and post-update scripts.  Only the fields whose name stay on the [fields_to_property](https://github.com/yucer/odoo-examples/blob/8.0_company_dependent_mig/migration_test/migrations/8.0.0.2/common.py#L5) list will be saved. There is a [common.py](https://github.com/yucer/odoo-examples/blob/8.0_company_dependent_mig/migration_test/migrations/8.0.0.2/common.py) module for each of such migration folders.

- The list of functions used to make such operations are shared between the migration scripts of different folders. They are located inside the [tools.py](https://github.com/yucer/odoo-examples/blob/8.0_company_dependent_mig/migration_test/migrations/tools.py) python module.

- The restore process is optimized for a fast write. It uses the [set_multi](https://github.com/yucer/odoo-examples/blob/8.0_company_dependent_mig/migration_test/migrations/tools.py#L140) method, avoiding to make a big loop for writing.

- The values are written for [all the companies](https://github.com/yucer/odoo-examples/blob/8.0_company_dependent_mig/migration_test/migrations/tools.py#L135), we decide that way in order to maintain the same state for the database . All the new values were supposed to be the same for all the companies before the update because it was previously just one value accessible (although not visible) for all of them. Any company can change its copy of the value independently after the update.

- A possible improvement of the script will be _not to write those values that are not visible for a company_, that would require an evaluation against the access rules and would involve a complexity that many people might not need. Normally, people realize the need of convert a field to company dependent the first time they are going to introduce a record that should not be visible to others, so getting copies of the previous value for all the companies might be OK.

- A temporary table will be created and dropped by the script of a migration folder.The naming convention for it includes the target version number of the update scripts (the folder name with underscores). An example of a temporary table's name should be something like `res_partner_8_0_0_2`
