#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
import pip

# Merci Sam & Max : http://sametmax.com/creer-un-setup-py-et-mettre-sa-bibliotheque-python-en-ligne-sur-pypi/

setup(
    name='memimto',
    version="0.0.1",
    packages=find_packages(),
    install_requires=[
        "Flask",
        "flask-cors",
        "Flask-SQLAlchemy",
        "celery",
        "redis",
        "face_recognition",
        "scikit-learn",
        "python-dotenv",
        "gunicorn",
        "pymysql",
        "PyJWT"
    ],
    entry_points={
        'console_scripts': [
            'memimto-server = memimto.__main__:main'
        ],
    },
    license="GPL3"
)