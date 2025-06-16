# How not to save up a lot of migration?

### TIPS:
- Before migrate with dev, please clean your migrations.

### How clean migrations, if you work locally?
- How to roll back migrations in database?
  - Full clean migrations:
    - `make migrate <app_name> zero`
    - `make migrations blog zero`
  - Rollback to specific migration:
    - `make migrate <app_name> <migration_name>`
    - `make migrate blog 0001`
    - `make migrate blog 0002`
- After rollback, you can delete migration files in `apps/<app_name>/migrations/` folder.
  - Rollback zero example:
    - `make migrate blog zero`
    - `rm apps/blog/migrations/0001_initial.py`
    - `rm apps/blog/migrations/0002_auto_20231001_1234.py`
    - `rm apps/blog/migrations/0003_auto_20231002_1234.py`
  - Rollback to specific migration example:
    - `make migrate blog 0001`
    - `rm apps/blog/migrations/0002_auto_20231001_1234.py`
    - `rm apps/blog/migrations/0003_auto_20231002_1234.py`
- After deleting migration files, you can create new migrations:
  - `make migrations <app_name>`
  - Example: `make migrations blog`
- After creating new migrations, you can apply them:
  - `make migrate <app_name>`
  - Example: `make migrate blog`
