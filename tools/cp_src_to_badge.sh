#!/bin/bash

# Usage: ./copy_files.sh /path/to/base_dir /path/to/dest_dir

BASE_DIR="$1"

if [[ -z "$BASE_DIR" ]]; then
    echo "Usage: $0 <base_dir>"
    exit 1
fi

export CP_BASE_DIR="/Volumes/CIRCUITPY/"

echo "status: Creating app directories..."
mkdir -p "${CP_BASE_DIR}apps/register"
mkdir -p "${CP_BASE_DIR}apps/hello"
mkdir -p "${CP_BASE_DIR}apps/appStore"
mkdir -p "${CP_BASE_DIR}apps/schedule"

echo "status: Creating base asset directories..."
mkdir -p "${CP_BASE_DIR}lib"
mkdir -p "${CP_BASE_DIR}badge"
mkdir -p "${CP_BASE_DIR}font"
mkdir -p "${CP_BASE_DIR}img"

echo "status: Copying boot.py"
cp -r "${BASE_DIR}/boot.py" "${CP_BASE_DIR}boot.py"

echo "status: Copying secrets.py"
cp -r "${BASE_DIR}/secrets.py" "${CP_BASE_DIR}secrets.py"

echo "status: Copying code.py"
cp -r "${BASE_DIR}/code.py" "${CP_BASE_DIR}code.py"

echo "status: Copying hello.json"
cp -r "${BASE_DIR}/hello.json" "${CP_BASE_DIR}hello.json"

echo "status: Copying register app"
cp -r "${BASE_DIR}/apps/register/"* "${CP_BASE_DIR}apps/register/."

echo "status: Copying hello app"
cp -r "${BASE_DIR}/apps/hello/"* "${CP_BASE_DIR}apps/hello/."

echo "status: Copying appStore app"
cp -r "${BASE_DIR}/apps/appStore/"* "${CP_BASE_DIR}apps/appStore/."

echo "status: Copying schedule app"
cp -r "${BASE_DIR}/apps/schedule/"* "${CP_BASE_DIR}apps/schedule/."

echo "status: Copying badge directory"
cp -r "${BASE_DIR}/badge/"* "${CP_BASE_DIR}badge/."

echo "status: Copying lib directory"
cp -r "${BASE_DIR}/lib/"* "${CP_BASE_DIR}lib/."

echo "status: Copying img directory"
cp -r "${BASE_DIR}/img/"* "${CP_BASE_DIR}img/."

echo "status: Copying font directory"
cp -r "${BASE_DIR}/font/"* "${CP_BASE_DIR}font/."
