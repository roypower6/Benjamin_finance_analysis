@echo off
mkdir finance_django
cd finance_django
pip install django yfinance pandas plotly
django-admin startproject finance_project .
python manage.py startapp analysis
echo SETUP_COMPLETE
