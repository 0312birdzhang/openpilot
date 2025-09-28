#!/usr/bin/env bash

export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export VECLIB_MAXIMUM_THREADS=1
if [ -s /data/params/d/dp_device_model_selected ]; then
  export FINGERPRINT="$(cat /data/params/d/dp_device_model_selected)"
fi

if [ -z "$AGNOS_VERSION" ]; then
  export AGNOS_VERSION="12.8"
fi

export STAGING_ROOT="/data/safe_staging"
export DISABLE_DRIVER=1
export USE_WEBCAM=1
export LITE=1
export ROAD_CAM=$(ls -l /dev/v4l/by-id/ |grep index0|grep Camera|awk -F'video' '{print $NF}')
