#!/usr/bin/env bash

if [ ! -f "MIGRATIONS_DONE" ];
then
  alembic upgrade head && touch "MIGRATIONS_DONE" || exit 1
fi

exec "$@"