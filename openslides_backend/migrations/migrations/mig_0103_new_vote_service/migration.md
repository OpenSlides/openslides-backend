# Short overview

Current split between automatic and manual actions:

* Simple changes like adding, editing and removing collection, field or most of
  the field attributes are being handled by the diff generator (usually) almost
  fully automatically. Developer needs to run the script, check the output and
  adjust the diff only in rare cases.

* Renames are being handled semi-automatically: developer needs to define the
  renames dictionary in the Migration class.

* Special almost automatic handling of (currently) 3 specific cases:
  * A new required field in existing collection:
    * creating a required field
    * adding `required: true` to an existing field
  * Field rename that results in writing side switch (table field becomes view
    field or other way around)
  * Field getting a new/more strict enum type:
    * change from string/string[] to enum/enum[]
    * Removing option from an existing enum

  Diff generator collects such cases, generates the maps that should be used
  to finish handling such cases in the cleanup method of te migration class and
  writes them to the `DiffMixin` class and/or `cleanup_statements.sql` defined
  in the new files next to the `migration.py`.
  Developer has to import and extend it `DiffMixin` in the migration class.
  `BaseMigration` class will handle the fields from `DiffMixin`.

  **Note:** side switch is not relevant for the vote
  service, therefore will be implemented later.

* Complex logic like moving data between columns and tables, creating or
  updating entries, modifying data in renamed columns etc. should be defined
  by the developer, mainly in `data_manipulation` method of the migration class.
  Some actions are getting partially automated:
    * Saving the data for `data_manipulation` into the temporary tables. Developer has
      to define the collections and fields to save in `migration_tables`.
    * Helper methods will patially automate some common actions.

# Not relevant for vote service migration but let's keep it somewhere for now

* Relation side switch:
  * Technically can happen on rename of 1-1 relational fields.
  * At some point we may also want to manually switch the writing side of some
    relations to make it more logical.
  * For now Hannes will implement a simple assertion that will raise error in such cases.
  * The intended way to handle side switch detected by diff generator:
    * Diff generator collects these cases and adds `switched_writing_side` to
      the `DiffMixin`.
    * In the migration class the previous writing side must be automativally
      saved in migration table in `data_preparation`
    * In `data_manipulation` data from the migration table gets automatically
      transfered into the new table field
