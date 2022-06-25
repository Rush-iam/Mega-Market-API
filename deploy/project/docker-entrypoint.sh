#!/usr/bin/env bash

if [ ! -f "MIGRATION_DONE" ];
then
  alembic upgrade head && touch "MIGRATION_DONE" || exit 1
fi

exec "$@"