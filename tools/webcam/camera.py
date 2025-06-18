import subprocess
import os

class Camera:
  def __init__(self, cam_type_state, stream_type, camera_id):
    self.cam_type_state = cam_type_state
    self.stream_type = stream_type
    self.cur_frame_id = 0
    self.W, self.H = 1920, 1080
    self.frame_size = self.W * self.H * 3 // 2  # NV12 格式大小
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

  def read_frames(self):
    try:
      while True:
        raw = self.proc.stdout.read(self.frame_size)
        if len(raw) != self.frame_size:
          print("❌ 未获取完整帧")
          break
        yield raw  # 直接返回原始 NV12 数据
    except Exception as e:
      print(f"读取帧出错: {e}")
    self.proc.terminate()

