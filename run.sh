#!/bin/bash
gunicorn -w 3 run:app
