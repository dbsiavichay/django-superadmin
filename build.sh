#!/bin/sh
rm -r ./dist
mkdir dist
pipenv run python setup.py sdist
pipenv run python setup.py bdist_wheel --universal
pipenv run twine upload dist/*
rm -r ./build
rm -r ./gmcm_django_superadmin.egg-info