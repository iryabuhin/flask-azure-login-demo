#!/bin/bash
gunicorn -w 3 _app:app
