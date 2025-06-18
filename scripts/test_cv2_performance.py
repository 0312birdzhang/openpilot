import subprocess
import os
import time

class Camera:
  def __init__(self):
    self.W, self.H = 1920, 1080
    self.frame_size = self.W * self.H * 3 // 2  # NV12 格式每帧大小
    self.proc = self._start_gst_pipeline()

  def _start_gst_pipeline(self):
    env = os.environ.copy()
    env["GST_PLUGIN_PATH"] = "/usr/lib/gstreamer-1.0:" + env.get("GST_PLUGIN_PATH", "")
    env["LD_LIBRARY_PATH"] = "/usr/lib:" + env.get("LD_LIBRARY_PATH", "")
    cmd = [
        "gst-launch-1.0", "-q", "qtiqmmfsrc", "camera=0", "name=camsrc",
        "!", f"video/x-raw,format=NV12,width={self.W},height={self.H},framerate=30/1",
        "!", "fdsink", "fd=1"
    ]
    return subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=10**8, env=env)

  def read_frame(self):
    return self.proc.stdout.read(self.frame_size)

  def close(self):
    self.proc.terminate()

# 测试函数
def test_camera_fps(duration_sec=1):
  cam = Camera()
  start = time.time()
  count = 0
  try:
    while time.time() - start < duration_sec:
      frame = cam.read_frame()
      if not frame or len(frame) != cam.frame_size:
        print("❌ 错误：没有读到完整一帧")
        break
      count += 1
  finally:
    cam.close()

  elapsed = time.time() - start
  fps = count / elapsed
  print(f"✅ {elapsed:.2f} 秒内读取了 {count} 帧，FPS ≈ {fps:.2f}")

# 运行测试
if __name__ == "__main__":
  test_camera_fps(duration_sec=20)

