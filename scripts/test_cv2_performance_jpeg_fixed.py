# -*- coding: utf-8 -*-
import subprocess
import time
import os
import numpy as np
import cv2

class JpegCamera:
  def __init__(self):
    self.proc = self._start_pipeline()

  def _start_pipeline(self):
    env = os.environ.copy()
    env["GST_PLUGIN_PATH"] = "/usr/lib/gstreamer-1.0:" + env.get("GST_PLUGIN_PATH", "")
    env["LD_LIBRARY_PATH"] = "/usr/lib:" + env.get("LD_LIBRARY_PATH", "")
    cmd = [
        "gst-launch-1.0", "-q",
        "qtiqmmfsrc", "camera=0", "name=qmmf",
        "!", "image/jpeg,width=1920,height=1080,framerate=30/1",
        "!", "fdsink", "fd=1"
    ]
    return subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=10**8, env=env)

  def read_jpeg_frame(self):
    # ç®åè¯»åæ¹å¼ï¼åè®¾å¸§ä¹é´ç¨ JPEG SOI+EOI æ¥å¤æ­
    data = b''
    while True:
      chunk = self.proc.stdout.read(4096)
      if not chunk:
        break
      data += chunk
      # JPEGå¸§ç»æç¬¦
      if b'\xff\xd9' in data:
        parts = data.split(b'\xff\xd9', 1)
        return parts[0] + b'\xff\xd9'
    return None

  def close(self):
    self.proc.terminate()

def test_jpeg_fps(duration=2):
  cam = JpegCamera()
  start = time.time()
  count = 0
  try:
    while time.time() - start < duration:
      jpeg = cam.read_jpeg_frame()
      if jpeg:
        # å¯éï¼æµè¯è§£ç æ§è½
        # image = cv2.imdecode(np.frombuffer(jpeg, dtype=np.uint8), cv2.IMREAD_COLOR)
        count += 1
  finally:
    cam.close()
  elapsed = time.time() - start
  print(f"í ½í³¸ JPEGæ¨¡å¼: {count}å¸§ / {elapsed:.2f}ç§ â {count / elapsed:.2f} FPS")

test_jpeg_fps(20)

