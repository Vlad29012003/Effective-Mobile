class ExternalDatabaseRouter:
    """
    A router to control all database operations on models in the external applications.
    """

    route_app_prefix = "external"

    def db_for_read(self, model, **hints):
        """
        Attempts to read external models go to external_database.
        """
        if model._meta.app_label.startswith(self.route_app_prefix):
            return "external_database"

        return None

    def db_for_write(self, model, **hints):
        """
        Attempts to write external models go to external_database.
        """
        if model._meta.app_label.startswith(self.route_app_prefix):
            return "external_database"

        return None

    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations if a model in the external apps is involved.
        """
        if obj1._meta.app_label.startswith(
            self.route_app_prefix
        ) or obj2._meta.app_label.startswith(self.route_app_prefix):
            return True

        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Make sure the external apps only appear in the 'external_database' database.
        """
        if app_label.startswith(self.route_app_prefix):
            return db == "external_database"

        return None
