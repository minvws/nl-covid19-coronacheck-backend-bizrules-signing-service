# Docs: https://docs.djangoproject.com/en/3.1/topics/db/multi-db/#using-routers
class VCBEDatabaseRouter(object):
    def db_for_read(self, model, **hints):
        return 'vcbe_db' if model.__name__.lower().startswith('vcbe') else None

    def db_for_write(self, model, **hints):
        return 'vcbe_db' if model.__name__.lower().startswith('vcbe') else None

    def allow_relation(self, obj1, obj2, **hints):
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        return False
