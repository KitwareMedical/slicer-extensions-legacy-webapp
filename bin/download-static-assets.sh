#!/bin/bash

set -e

script_dir=$(cd $(dirname $0) || exit 1; pwd)

ROOT_DIR=$(realpath "${script_dir}/..")
ASSETS_DIR=${ROOT_DIR}/server/assets

BRANCH=slicer-kitware-com
FILENAME=${BRANCH}.zip
DOWNLOAD_URL="https://github.com/KitwareMedical/slicer-extensions-webapp/archive/refs/heads/${FILENAME}"

# Display summary
echo
echo "[download_static_assets] Settings"
echo "  DOWNLOAD_URL  : ${DOWNLOAD_URL}"
echo "  ROOT_DIR      : ${ROOT_DIR}"
echo "  ASSETS_DIR    : ${ASSETS_DIR}"

# Temporary directory
TEMP_DIR=`mktemp -d -p "/tmp"`
if [[ ! "${TEMP_DIR}" || ! -d "${TEMP_DIR}" ]]; then
  echo "[download_static_assets] Could not create temporary directory"
  exit 1
fi

# Deletes the temp directory
function cleanup {
  echo
  echo "[download_static_assets] Deleting temporary directory ${TEMP_DIR}"
  rm -rf "${TEMP_DIR}"
}

# Register the cleanup function to be called on the EXIT signal
trap cleanup EXIT

# Download
echo
echo "[download_static_assets] Downloading ${FILENAME}"
rm -f
curl -o ${TEMP_DIR}/${FILENAME} -# -SL ${DOWNLOAD_URL}

# Extracting
echo
echo "[download_static_assets] Extracting ${FILENAME}"
unzip -d ${TEMP_DIR}/ ${TEMP_DIR}/${FILENAME}

# Extracted directory is specific to the downloaded archive
site_dir=${TEMP_DIR}/slicer-extensions-webapp-${BRANCH}

# Clear target directories
echo
echo "[download_static_assets] Cleaning directories"
for directory in ${ASSETS_DIR}; do
  subdir=$(basename ${directory})
  echo "  ${directory}"
  find ${directory} ! -name '.keep' -type f -exec rm -f {} +
  find ${directory} ! -name "${subdir}" -type d -exec rm -rf {} +
done

# Copy file
echo
echo "[download_static_assets] Copying"
echo "  ${site_dir}/* -> ${ASSETS_DIR}/"
cp -r ${site_dir}/* ${ASSETS_DIR}/
