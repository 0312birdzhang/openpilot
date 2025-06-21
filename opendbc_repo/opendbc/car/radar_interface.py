'''
MIT Non-Commercial License
Copyright (c) 2025 Rick Lan

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, for non-commercial purposes only, subject to the following conditions:

- The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
- Commercial use (e.g., use in a product, service, or activity intended to generate revenue) is prohibited without explicit written permission from Rick Lan. Contact ricklan@gmail.com for inquiries.
- Any project that uses the Software must visibly mention the following acknowledgment: "This project uses software from Rick Lan and is licensed under a custom license requiring permission for use."

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''

from opendbc.car.interfaces import RadarInterfaceBase
from opendbc.can.parser import CANParser
from opendbc.car.structs import RadarData
from typing import List, Tuple

DREL_OFFSET = -1.3 # car head to radar
MAX_OBJECTS = 100
MAX_LAT_DIST = 2.4 # lat distance

CLOSED_OBJ_DREL = 10
CLOSED_OBJ_YREL = 1.85

NOT_SEEN_INIT = 8


def _create_radar_parser():
  messages = [("Status", 0), ("ObjectData", 0)]
  messages += [(f"ObjectData_{i}", 0) for i in range(MAX_OBJECTS)]
  return CANParser('u_radar', messages, 1)

class RadarInterface(RadarInterfaceBase):
  def __init__(self, CP):
    super().__init__(CP)

    self.updated_messages = set()

    self.rcp = _create_radar_parser()

    self._pts_cache = dict()
    self._pts_not_seen = {key: 0 for key in range(255)}
    self._should_clear_cache = False

  def _create_parsable_object_can_strings(self, can_strings: List[Tuple]) -> Tuple[List[Tuple], int]:
    """Optimized object string parsing with minimal allocations."""
    if not can_strings or not isinstance(can_strings[0], tuple) or len(can_strings[0]) < 2:
      return [], 0

    # Pre-allocate list with known maximum size
    new_list = []
    new_list_append = new_list.append  # Local reference for faster access

    records = can_strings[0][1]
    id_num = 1

    for record in records:
      if id_num > MAX_OBJECTS:
        break

      if record[0] == 0x60B:
        new_list_append((id_num + 383, record[1], record[2]))
        id_num += 1

    return [(can_strings[0][0], new_list)], len(new_list)

  # called by card.py, 100hz
  def update(self, can_strings):
    ret = RadarData()
    if not self.rcp.can_valid:
      ret.errors.canError = True

    vls = self.rcp.update_strings(can_strings)
    self.updated_messages.update(vls)

    if 1546 in self.updated_messages:
      # prep for next loop
      cpt = self.rcp.vl['Status']

      # find the keys to decay/remove
      keys_to_remove = [key for key in self.pts if key not in self._pts_cache]
      for key in keys_to_remove:
        self._pts_not_seen[key] -= 1
        if self._pts_not_seen[key] <= 0:
          del self.pts[key]

      self.pts.update(self._pts_cache)
      self._should_clear_cache = True

    if 1547 in self.updated_messages:
      parsable_can_string, size = self._create_parsable_object_can_strings(can_strings)
      self.rcp.update_strings(parsable_can_string)

      # do not clear cache until we see a new 0x60b, in case we don't receive
      if self._should_clear_cache:
        self._pts_cache.clear()
        self._should_clear_cache = False

      for i in range(size):
        cpt = self.rcp.vl[f'ObjectData_{i}']

        track_id = int(cpt['ID'])

        d_rel = float(cpt['DistLong']) + DREL_OFFSET
        y_rel = -float(cpt['DistLat'])

        if d_rel < 0:
          continue

        if float(cpt['RCS']) < 0:
          continue

        if abs(y_rel) > MAX_LAT_DIST:
          continue

        if d_rel < CLOSED_OBJ_DREL and abs(y_rel) > CLOSED_OBJ_YREL:
          continue

        if track_id not in self._pts_cache:
          self._pts_cache[track_id] = RadarData.RadarPoint()
          self._pts_cache[track_id].trackId = track_id

        self._pts_not_seen[track_id] = NOT_SEEN_INIT
        self._pts_cache[track_id].yvRel = float(cpt['VRelLat'])
        self._pts_cache[track_id].dRel = d_rel
        self._pts_cache[track_id].yRel = y_rel
        self._pts_cache[track_id].vRel = float(cpt['VRelLong'])
        self._pts_cache[track_id].aRel = float('nan')
        self._pts_cache[track_id].measured = True

    self.updated_messages.clear()

    ret.points = list(self.pts.values())
    return ret
