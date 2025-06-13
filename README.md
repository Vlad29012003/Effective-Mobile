# django-template-blog


# Run project in server
### Gunicorn use next flags:
```
max_requests = 1000 // Max requests per worker, after which worker will be restarted
max_requests_jitter = 100 // Random jitter to avoid all workers restarting at the same time
preload_app = True // Preload the application code before forking workers
```
  
# Run project local
### Dependencies
- **Make sure you have the latest version of Python 3.12+ installed.**
- **Make sure you have [uv](https://docs.astral.sh/uv/getting-started/installation/) installed.**
- **Install requirements:**
  ```bash
  uv sync
  ```
- **Create `.env` file by copying `infra/env.example`:**

### Docker
- **Run local docker:**
  ```bash
  make docker-local
  ```
#### MinIO (S3 Object Storage)
- **Create bucket for static files and media:**
    - By terminal
      ```bash
       > docker compose -f docker-compose.locale.yml exec -it minio bash
       > mc config host add myminio http://minio:9000 ${MINIO_ROOT_USER} ${MINIO_ROOT_PASSWORD};
       > mc mb --quiet myminio/default;
       > mc anonymous set public myminio/default;
      ```
    - By browser
        - Go to `http://localhost:9001`
        - Login
        - Open `Buckets`
        - Click `Create bucket`
        - Create bucket with name `default`
        - Update `Access Policy` to `Public`

## Django
- **Run migrations:**
  ```bash
  make migrate
  ```
- **Create superuser:**
  ```bash
    make createsuperuser
  ```
- **Collect static files:**
  ```bash
  make collectstatic
  ```

## Django Project Structure

- apps (Django apps)
    - common (Common functionality)
- config (Django project settings)
    - db_routers (Database routers)
    - di (Dependency Injection)
    - middlewares (Middlewares)
    - settings
        - base.py (Base settings)
        - dev.py (Development settings)
        - local.py (Local settings)
        - prod.py (Production settings)
    - asgi.py (ASGI configuration)
    - celery.py (Celery configuration)
    - urls.py (URL configuration)
    - wsgi.py (WSGI configuration)
- static (Static files)
- manage.py

## Adding application to project

- **Hints: If your app start with prefix ov, it will use `ov_database`, be careful with migrations!**

1. Create a new folder in apps directory (e.g. **apps/myapp**)
2. Create a new Django app inside the folder:
   ```python manage.py startapp myapp apps/myapp```
3. Update in **myapp/apps.py** `name` variable from `myapp` to `apps.myapp`
4. Add the new app to the `INSTALLED_APPS` list in **config/settings/base.py**

## Adding group and permissions

- Open `constants.py` in your application
- Create new group and permissions
- Create `GroupConfig` in your application
    - When you write action, please use prefix!
- Open `signals.py` in common application
- Update `create_groups` function

## Adding action permission to view (DRF)

- Open your application views.py
- Add `ActionPermissionBase` permission class to your view
- Add `required_action` attribute to your view (Or make `get_required_action` method, which return `string`)
- Action permission doesn't work for superuser! Superuser can do everything, without action permission

## Admin Panel

- We use [Unfold](https://unfoldadmin.com/docs/integrations/django-guardian/) for admin Panel
- Please use mixins from common, for common functionality
- If u need to add new tools for admin panel like import-export, modeltranslation, etc, please check integration in
  Unfold, before whiting your own
