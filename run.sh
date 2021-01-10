#!/bin/bash
source venv/bin/activate
exec gunicorn -b :5000 -w 3 --access-logfile - --error-logfile - _app:app
