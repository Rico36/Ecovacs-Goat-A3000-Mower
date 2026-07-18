import re, sys
from pathlib import Path

VENDOR = Path("/home/admin/homeassistant/custom_components/ecovacs/vendor/deebot_client")
SENTINEL = "# aarch64-rs-patch-applied"

RA = """try:
    from deebot_client.rs.map import RotationAngle
except ImportError:
    class RotationAngle:
        def __init__(self, value=0): self._v = int(value)
        @classmethod
        def from_int(cls, value): return cls(value)
        def __int__(self): return self._v
        def __eq__(self, other):
            if isinstance(other, RotationAngle): return self._v == other._v
            return NotImplemented
"""

PT = """try:
    from deebot_client.rs.map import PositionType
except ImportError:
    import enum
    class PositionType(str, enum.Enum):
        DEEBOT = "deebot_pos"
        CHARGER = "chargebase_pos"
"""

DC = """try:
    from deebot_client.rs.util import decompress_base64_data
except ImportError:
    import base64 as _b64, zlib as _zl
    def decompress_base64_data(data):
        raw = _b64.b64decode(data)
        for wb in (-15, 15, 47):
            try: return _zl.decompress(raw, wb)
            except _zl.error: pass
        return raw
"""

PATCHES = [
    ("messages/json/map/cached_map_info.py", r"^from deebot_client\.rs\.map import RotationAngle\s*$", RA),
    ("messages/xml/pos.py",                  r"^from deebot_client\.rs\.map import PositionType\s*$", PT),
    ("commands/json/map/__init__.py",         r"^from deebot_client\.rs\.util import decompress_base64_data\s*$", DC),
    ("commands/json/pos.py",                  r"^from deebot_client\.rs\.map import PositionType\s*$", PT),
    ("commands/xml/map.py",                   r"^from deebot_client\.rs\.map import RotationAngle\s*$", RA),
    ("commands/xml/pos.py",                   r"^from deebot_client\.rs\.map import PositionType\s*$", PT),
]

if not VENDOR.exists():
    print(f"ERROR: {VENDOR} not found"); sys.exit(1)

print(f"\nPatching {VENDOR}\n")
for rel, pat, repl in PATCHES:
    p = VENDOR / rel
    if not p.exists(): print(f"  MISS  {rel}"); continue
    t = p.read_text()
    if SENTINEL in t: print(f"  SKIP  {rel}"); continue
    nt, n = re.subn(pat, repl, t, flags=re.MULTILINE)
    if not n: print(f"  SKIP  {rel}"); continue
    p.write_text(f"# {SENTINEL}\n" + nt)
    print(f"  PATCH {rel}")

# events/map.py — import is inside TYPE_CHECKING block
p = VENDOR / "events/map.py"
if p.exists():
    t = p.read_text()
    if SENTINEL not in t:
        PAT = r"^(\s+)from deebot_client\.rs\.map import PositionType, RotationAngle\s*$"
        def rep(m):
            i = m.group(1)
            return f"{i}try:\n{i}    from deebot_client.rs.map import PositionType, RotationAngle\n{i}except ImportError:\n{i}    pass\n"
        nt, n = re.subn(PAT, rep, t, flags=re.MULTILINE)
        if n: p.write_text(f"# {SENTINEL}\n" + nt); print("  PATCH events/map.py")
        else: print("  SKIP  events/map.py")
    else: print("  SKIP  events/map.py")

print("\nDone. Restart: docker restart home-assistant\n")
