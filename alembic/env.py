from logging.config import fileConfig

import yaml
from sqlalchemy import engine_from_config
from sqlalchemy import pool

from app.database.gino import db
from app.web.config import DatabaseConfig
from alembic import context

with open('config.yml') as cfg:
    raw_cfg = yaml.safe_load(cfg)
    db_config = DatabaseConfig(**raw_cfg['database'])
    print(db_config)

config = context.config


def set_sqlalchemy_url(
        username: str,
        password: str,
        host: str,
        db_name: str):

    config.set_main_option('sqlalchemy.url',
                           f'postgres://{username}:{password}@{host}/{db_name}')


# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
from app.admin.models import AdminModel
target_metadata = db


# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """

    set_sqlalchemy_url(
        username=db_config.user,
        password=db_config.password,
        host=db_config.host,
        db_name=db_config.database,
    )

    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """

    set_sqlalchemy_url(
        username=db_config.user,
        password=db_config.password,
        host=db_config.host,
        db_name=db_config.database,
    )

    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
