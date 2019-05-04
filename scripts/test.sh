#! /bin/bash

set -ex # fail on first error, print commands

SRC_DIR=${SRC_DIR:-`pwd`}

echo "Checking documentation..."
python -m pydocstyle --convention=numpy ${SRC_DIR}/ridge_map/
echo "Success!"

echo "Checking code style with black..."
python -m black --check ridge_map/
echo "Success!"

echo "Checking code style with pylint..."
python -m pylint ridge_map/
echo "Success!"

echo "Running unit tests..."
python -m pytest -v --cov=ridge_map test/
