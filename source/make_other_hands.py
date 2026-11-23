#!/usr/bin/env python3
"""Build other_hands_mesh/<id>.mjs, other makers' dexterous hands for unitree_ends_3d.html, from the models the makers
publish (other_hands/<id>/; where each comes from, its commit and licence: other_hands/README.md).

    python3 make_other_hands.py              write the modules
    python3 make_other_hands.py --check      only check that they are what the models give (exit 1 if not)
    python3 make_other_hands.py wuji_hand    only these hands

The simplification, normals and packing are make_unitree_ends.py's (imported from it), so both sets of modules have
the same form and the page draws them the same way. This script adds the readers the other models need: URDF with
binary or ASCII STL, OBJ, GLB or Collada (DAE) meshes, and MuJoCo MJCF (Shadow's hand, as MuJoCo Menagerie
publishes it). Colours: a visual's URDF or MJCF material, or the material of each triangle in a GLB or DAE file, picks
the class of its triangles (each hand's `classify`); the page gives each class its look. Mimic joints are kept, and
OYMotion's ROHand, whose fingers are linkages a URDF cannot close, gets a table per joint from OYMotion's own linkage
formula (FingerMathURDF.py in oymotion/rohand_urdf_ros2, MIT), sampled along the slider that drives it.
Standard library only.
"""
import base64
import hashlib
import json
import math
import re
import struct
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

here = Path(__file__).resolve().parent
sys.path.insert(0, str(here))
import make_unitree_ends as mu   # noqa: E402  (simplify, pack, UNIT)

SRC = here / "other_hands"
CELL = 0.00002       # m: the grid that first welds the corners each STL triangle repeats (make_unitree_ends.py's clustering)
ERR = 0.0002         # m: then edge collapse while the surface moves less than this (root mean square)
OUT = here / "other_hands_mesh"
MANIFEST = json.loads((SRC / "manifest.json").read_text(encoding="utf-8"))


def lum(rgba):
    return 0.2126 * rgba[0] + 0.7152 * rgba[1] + 0.0722 * rgba[2]


def by_tone(dark=0.3, light=0.6):
    """Classes from the material's lightness: dark, mid, light (0, 1, 2); no colour counts as light."""
    def visual(link, rgba):
        def cls(t, n):
            c = getattr(t, "c", None) or rgba
            if c is None:
                return 2
            v = lum(c)
            return 0 if v < dark else 1 if v < light else 2
        return cls
    visual.key = lambda link, rgba: tuple(rgba or ())
    return visual


def by_link(rule):
    """Classes from the link's name: rule(link) → class index."""
    visual = lambda link, rgba: (lambda t, n, k=rule(link): k)
    visual.key = lambda link, rgba: rule(link)
    return visual


def by_rgba(rule):
    """Classes from the visual's URDF colour: rule(rgba) → class index."""
    visual = lambda link, rgba: (lambda t, n, k=rule(rgba): k)
    visual.key = lambda link, rgba: rule(rgba)
    return visual


def one(link, rgba):
    return lambda t, n: 0


one.key = lambda link, rgba: None


# id, the model file in other_hands/<id>/, cell (m), classes (the page's looks are keyed by these), classify,
# links left out. `brand` and `model` name it in the module's header.
HANDS = [
    # Inspire's photos: a white palm and wrist, the fingers black (the URDF has every part white).
    {"id": "inspire_rh56dfx", "brand": "因时 Inspire Robots", "model": "RH56DFX",
     "classes": ["palm", "finger"], "classify": by_link(lambda l: 0 if l == "R_hand_base_link" else 1)},
    {"id": "linker_l20", "brand": "灵心巧手 LinkerBot", "model": "LinkerHand L20",
     "classes": ["dark", "mid", "light"], "classify": by_tone()},
    {"id": "linker_o6", "brand": "灵心巧手 LinkerBot", "model": "LinkerHand O6",
     "classes": ["dark", "mid", "light"], "classify": by_tone()},
    {"id": "brainco_revo2", "brand": "强脑科技 BrainCo", "model": "Revo2", "classes": ["body"]},
    {"id": "oymotion_rohand", "brand": "傲意科技 OYMotion", "model": "ROHand", "classes": ["body"],
     "linkage": "rohand"},
    {"id": "dexrobot_dexhand021", "brand": "灵巧智能 DexRobot", "model": "DexHand021",
     "classes": ["dark", "mid", "light"], "classify": by_tone()},
    {"id": "wuji_hand", "brand": "舞肌科技 Wuji", "model": "Wuji Hand 2.1", "classes": ["dark", "mid", "light"],
     "classify": by_tone()},
    {"id": "agibot_omnihand", "brand": "智元 AgiBot", "model": "OmniHand 2025 (O10)",
     "classes": ["dark", "mid", "light"], "classify": by_tone(0.3, 0.9)},
    {"id": "robotera_xhand1", "brand": "星动纪元 RobotEra", "model": "XHAND1 Pro-U",
     "classes": ["body", "cover"], "classify": by_rgba(lambda rgba: 1 if rgba and rgba[1] > 0.3 else 0)},
    {"id": "fourier_fdh6", "brand": "傅利叶 Fourier", "model": "FDH-6（6 自由度灵巧手）",
     "classes": ["body"]},
    {"id": "sharpa_wave", "brand": "Sharpa", "model": "SharpaWave", "classes": ["body", "pad"],
     "classify": by_link(lambda l: 1 if "elastomer" in l else 0)},
    {"id": "shadow_hand", "brand": "Shadow Robot", "model": "Shadow Dexterous Hand E3M5",
     "classes": ["dark", "mid", "light"], "classify": by_tone()},
    {"id": "allegro_v5", "brand": "Wonik Robotics", "model": "Allegro Hand V5（四指）",
     "classes": ["dark", "mid", "light"], "classify": by_tone()},
    {"id": "leap_hand", "brand": "卡内基梅隆大学 CMU", "model": "LEAP Hand",
     "classes": ["motor", "printed"], "classify": by_link(lambda l: 1 if l in ("palm_lower",) or "fingertip" in l or l.startswith("pip") else 0)},
    {"id": "ability_hand", "brand": "PSYONIC", "model": "Ability Hand（大号）", "classes": ["body"]},
    {"id": "tesollo_dg5f", "brand": "Tesollo", "model": "DG-5F",
     "classes": ["dark", "mid", "light"], "classify": by_tone()},
]


# ---------------- meshes ----------------
class Tri(tuple):
    """A triangle ((x, y, z) × 3) that may carry its own colour (t.c, rgba) from a GLB or DAE material."""


def tri(a, b, c, col=None):
    t = Tri((a, b, c))
    if col is not None:
        t.c = col
    return t


def stl(path):
    b = path.read_bytes()
    if len(b) >= 84:
        n = struct.unpack_from("<I", b, 80)[0]
        if len(b) == 84 + 50 * n:
            return [tri(v[3:6], v[6:9], v[9:12]) for v in struct.iter_unpack("<12fH", b[84:])]
    pts = [tuple(map(float, m)) for m in re.findall(rb"vertex\s+(\S+)\s+(\S+)\s+(\S+)", b)]
    if not pts or len(pts) % 3:
        sys.exit(f"{path}: neither a binary nor an ASCII STL")
    return [tri(*pts[i:i + 3]) for i in range(0, len(pts), 3)]


def obj(path):
    vs, out = [], []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        p = line.split()
        if not p:
            continue
        if p[0] == "v":
            vs.append(tuple(map(float, p[1:4])))
        elif p[0] == "f":
            ix = [int(q.split("/")[0]) for q in p[1:]]
            ix = [i - 1 if i > 0 else len(vs) + i for i in ix]
            for k in range(1, len(ix) - 1):
                out.append(tri(vs[ix[0]], vs[ix[k]], vs[ix[k + 1]]))
    return out


def matmul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]


def apply(m, p):
    return tuple(m[i][0] * p[0] + m[i][1] * p[1] + m[i][2] * p[2] + m[i][3] for i in range(3))


IDENT = [[1.0, 0, 0, 0], [0, 1.0, 0, 0], [0, 0, 1.0, 0], [0, 0, 0, 1.0]]


def glb(path):
    """Triangles of a binary glTF (no compression extensions), through its scene's node transforms."""
    b = path.read_bytes()
    if b[:4] != b"glTF":
        sys.exit(f"{path}: not a GLB")
    jl = struct.unpack_from("<I", b, 12)[0]
    j = json.loads(b[20:20 + jl])
    if j.get("extensionsRequired"):
        sys.exit(f"{path}: needs {j['extensionsRequired']}")
    bl = struct.unpack_from("<I", b, 20 + jl)[0]
    blob = b[28 + jl:28 + jl + bl]

    def acc(i):
        a = j["accessors"][i]
        bv = j["bufferViews"][a["bufferView"]]
        fmt = {5126: "f", 5125: "I", 5123: "H", 5121: "B"}[a["componentType"]]
        n = {"SCALAR": 1, "VEC3": 3}[a["type"]]
        size = struct.calcsize(fmt)
        stride = bv.get("byteStride") or n * size
        start = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
        return [struct.unpack_from(f"<{n}{fmt}", blob, start + k * stride) for k in range(a["count"])]

    def local(node):
        if "matrix" in node:
            m = node["matrix"]
            return [[m[c * 4 + r] for c in range(4)] for r in range(4)]
        t = node.get("translation", [0, 0, 0])
        x, y, z, w = node.get("rotation", [0, 0, 0, 1])
        s = node.get("scale", [1, 1, 1])
        r = [[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
             [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
             [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]
        return [[r[i][0] * s[0], r[i][1] * s[1], r[i][2] * s[2], t[i]] for i in range(3)] + [[0, 0, 0, 1.0]]

    out = []

    def walk(ni, m):
        node = j["nodes"][ni]
        m = matmul(m, local(node))
        if "mesh" in node:
            for prim in j["meshes"][node["mesh"]]["primitives"]:
                if prim.get("mode", 4) != 4:
                    continue
                pos = [apply(m, p) for p in acc(prim["attributes"]["POSITION"])]
                idx = [i[0] for i in acc(prim["indices"])] if "indices" in prim else list(range(len(pos)))
                col = None
                if "material" in prim:
                    col = j["materials"][prim["material"]].get("pbrMetallicRoughness", {}).get("baseColorFactor")
                for k in range(0, len(idx) - 2, 3):
                    out.append(tri(pos[idx[k]], pos[idx[k + 1]], pos[idx[k + 2]], col))
        for c in node.get("children", []):
            walk(c, m)

    for ni in j["scenes"][j.get("scene", 0)]["nodes"]:
        walk(ni, IDENT)
    return out


def dae(path):
    """Triangles of a Collada file, through its visual scene's node matrices, each with its material's diffuse colour."""
    root = ET.parse(path).getroot()
    ns = root.tag.split("}")[0] + "}" if root.tag.startswith("{") else ""
    q = lambda s: s.replace("c:", ns)
    unit = root.find(q("c:asset/c:unit"))
    scale = float(unit.get("meter", "1")) if unit is not None else 1.0
    up = root.find(q("c:asset/c:up_axis"))
    if up is not None and up.text.strip() != "Z_UP":
        sys.exit(f"{path}: up axis {up.text}; only Z_UP is read")
    effects = {}
    for e in root.iter(q("c:effect")):
        c = e.find(q(".//c:diffuse/c:color"))
        effects[e.get("id")] = tuple(map(float, c.text.split())) if c is not None else None
    materials = {m.get("id"): effects.get(m.find(q("c:instance_effect")).get("url").lstrip("#")) for m in root.iter(q("c:material"))}
    geoms = {}
    for g in root.iter(q("c:geometry")):
        mesh = g.find(q("c:mesh"))
        srcs = {s.get("id"): list(map(float, s.find(q("c:float_array")).text.split())) for s in mesh.findall(q("c:source"))}
        verts = {v.get("id"): srcs[v.find(q("c:input[@semantic='POSITION']")).get("source").lstrip("#")] for v in mesh.findall(q("c:vertices"))}
        parts = []
        for t in mesh.findall(q("c:triangles")):
            inputs = t.findall(q("c:input"))
            stride = max(int(i.get("offset")) for i in inputs) + 1
            vin = next(i for i in inputs if i.get("semantic") == "VERTEX")
            pos = verts[vin.get("source").lstrip("#")]
            p = list(map(int, t.find(q("c:p")).text.split()))
            ix = p[int(vin.get("offset"))::stride]
            parts.append((t.get("material"), [tuple(pos[3 * i:3 * i + 3]) for i in ix]))
        if mesh.findall(q("c:polylist")) or mesh.findall(q("c:polygons")):
            sys.exit(f"{path}: polylist/polygons not read")
        geoms[g.get("id")] = parts
    out = []

    def walk(node, m):
        mt = node.find(q("c:matrix"))
        if mt is not None:
            v = list(map(float, mt.text.split()))
            m = matmul(m, [v[0:4], v[4:8], v[8:12], v[12:16]])
        elif node.find(q("c:translate")) is not None or node.find(q("c:rotate")) is not None:
            sys.exit(f"{path}: node transforms other than <matrix> not read")
        for ig in node.findall(q("c:instance_geometry")):
            bind = {im.get("symbol"): im.get("target").lstrip("#") for im in ig.iter(q("c:instance_material"))}
            for mat, pts in geoms[ig.get("url").lstrip("#")]:
                col = materials.get(bind.get(mat, mat))
                pts = [tuple(c * scale for c in apply(m, p)) for p in pts]
                for k in range(0, len(pts) - 2, 3):
                    out.append(tri(pts[k], pts[k + 1], pts[k + 2], col))
        for c in node.findall(q("c:node")):
            walk(c, m)

    for vs in root.iter(q("c:visual_scene")):
        for n in vs.findall(q("c:node")):
            walk(n, IDENT)
    return out


READERS = {".stl": stl, ".obj": obj, ".glb": glb, ".dae": dae}


def triangles(f, scale):
    tris = READERS[f.suffix.lower()](f)
    sx, sy, sz = scale
    if (sx, sy, sz) != (1, 1, 1):
        tris = [tri(*((p[0] * sx, p[1] * sy, p[2] * sz) for p in t), getattr(t, "c", None)) for t in tris]
    return tris


# ---------------- robot descriptions ----------------
def nums(s, default="0 0 0"):
    return [float(v) for v in (s or default).split()]


def resolve(fn, urdf_dir, src):
    """A mesh path as URDFs write it (package://pkg/rel, a relative path) in the hand's folder."""
    rel = fn.split("://", 1)[1] if "://" in fn else fn
    cands = [urdf_dir / rel, src / rel]
    if "://" in fn and "/" in rel:
        tail = rel.split("/", 1)[1]
        cands += [urdf_dir / tail, src / tail, urdf_dir.parent / tail]
    for c in cands:
        if c.is_file():
            return c.resolve()
    hits = [p for p in src.rglob(Path(rel).name) if p.is_file()]
    if len(hits) == 1:
        return hits[0].resolve()
    sys.exit(f"{fn}: not found in {src.relative_to(here)}")


def urdf(hand, path):
    src = SRC / hand["id"]
    root = ET.parse(path).getroot()
    named = {m.get("name"): nums(m.find("color").get("rgba")) for m in root.findall("material") if m.find("color") is not None}
    links, joints = [], []
    for l in root.findall("link"):
        if l.get("name") in hand.get("skip", ()):
            continue
        m = l.find("inertial/mass")
        vis = []
        for v in l.findall("visual"):
            g = v.find("geometry/mesh")
            if g is None:
                continue    # spheres and boxes marking tips or sensors
            mat = v.find("material")
            rgba = None
            if mat is not None:
                rgba = nums(mat.find("color").get("rgba")) if mat.find("color") is not None else named.get(mat.get("name"))
            o = v.find("origin")
            vis.append({"file": resolve(g.get("filename"), path.parent, src), "xyz": nums(o.get("xyz") if o is not None else None),
                        "rpy": nums(o.get("rpy") if o is not None else None), "scale": nums(g.get("scale"), "1 1 1"), "rgba": rgba})
        links.append({"name": l.get("name"), "mass": float(m.get("value")) if m is not None else 0.0, "visuals": vis})
    names = {l["name"] for l in links}
    for j in root.findall("joint"):
        child = j.find("child").get("link")
        if child not in names:
            continue
        o, a, lim, mim = j.find("origin"), j.find("axis"), j.find("limit"), j.find("mimic")
        jt = {"name": j.get("name"), "type": j.get("type"), "parent": j.find("parent").get("link"), "child": child,
              "xyz": nums(o.get("xyz") if o is not None else None), "rpy": nums(o.get("rpy") if o is not None else None)}
        if jt["type"] != "fixed":
            jt["axis"] = nums(a.get("xyz") if a is not None else None, "1 0 0")
            jt["limit"] = None if jt["type"] == "continuous" or lim is None or lim.get("lower") is None else \
                [float(lim.get("lower")), float(lim.get("upper"))]
        if mim is not None:
            jt["mimic"] = {"joint": mim.get("joint"), "multiplier": float(mim.get("multiplier", "1")),
                           "offset": float(mim.get("offset", "0"))}
        joints.append(jt)
    return links, joints


def rot(rpy):
    """R = Rz(yaw) Ry(pitch) Rx(roll), as URDF and the page (Euler order 'ZYX') read rpy."""
    cr, sr, cp, sp, cy, sy = math.cos(rpy[0]), math.sin(rpy[0]), math.cos(rpy[1]), math.sin(rpy[1]), math.cos(rpy[2]), math.sin(rpy[2])
    return [[cy * cp, cy * sp * sr - sy * cr, cy * sp * cr + sy * sr],
            [sy * cp, sy * sp * sr + cy * cr, sy * sp * cr - cy * sr],
            [-sp, cp * sr, cp * cr]]


def quat_rpy(w, x, y, z):
    """URDF roll, pitch, yaw (R = Rz(yaw) Ry(pitch) Rx(roll)) of a unit quaternion."""
    n = math.sqrt(w * w + x * x + y * y + z * z)
    w, x, y, z = w / n, x / n, y / n, z / n
    r20 = 2 * (x * z - w * y)
    pitch = -math.asin(max(-1.0, min(1.0, r20)))
    if abs(r20) < 1 - 1e-9:
        roll = math.atan2(2 * (y * z + w * x), 1 - 2 * (x * x + y * y))
        yaw = math.atan2(2 * (x * y + w * z), 1 - 2 * (y * y + z * z))
    else:   # gimbal lock: put it all in yaw
        roll = 0.0
        yaw = math.atan2(-2 * (x * y - w * z), 1 - 2 * (x * x + z * z))
    return [roll, pitch, yaw]


def mjcf(hand, path):
    """Bodies, hinge joints and visual mesh geoms of a MuJoCo model (defaults and childclass resolved; angles in
    radians, orientations given as quat)."""
    src = SRC / hand["id"]
    root = ET.parse(path).getroot()
    comp = root.find("compiler")
    if comp is None or comp.get("angle") != "radian":
        sys.exit(f"{path}: only angle=\"radian\" is read")
    meshdir = path.parent / (comp.get("meshdir") or "")
    classes = {}

    def defaults(el, parent):
        name = el.get("class", "main")
        d = {k: dict(v) for k, v in parent.items()}
        for c in el:
            if c.tag != "default":
                d.setdefault(c.tag, {}).update(c.attrib)
        classes[name] = d
        for c in el.findall("default"):
            defaults(c, d)

    for top in root.findall("default"):
        defaults(top, {})

    def attrs(el, cls):
        a = dict(classes.get(el.get("class") or cls or "main", {}).get(el.tag, {}))
        a.update(el.attrib)
        return a

    mats = {m.get("name"): nums(m.get("rgba"), "1 1 1 1") for m in root.iter("material")}
    meshes = {}
    for m in root.find("asset").findall("mesh"):
        a = attrs(m, None)
        meshes[a.get("name") or Path(a["file"]).stem] = (meshdir / a["file"], nums(a.get("scale"), "1 1 1"))
    links, joints = [], []

    def walk(body, parent, cls):
        cls = body.get("childclass") or cls
        name = body.get("name")
        inertial = body.find("inertial")
        vis = []
        for g in body.findall("geom"):
            a = attrs(g, cls)
            if a.get("type") != "mesh" or a.get("group") == "3" or "mesh" not in a:
                continue
            f, scale = meshes[a["mesh"]]
            if not f.is_file():
                sys.exit(f"{f}: missing")
            q = nums(a.get("quat"), "1 0 0 0")
            vis.append({"file": f.resolve(), "xyz": nums(a.get("pos")), "rpy": quat_rpy(*q), "scale": scale,
                        "rgba": mats.get(a.get("material"))})
        links.append({"name": name, "mass": float(inertial.get("mass")) if inertial is not None else 0.0, "visuals": vis})
        if parent is not None:
            q = nums(body.get("quat"), "1 0 0 0")
            js = [attrs(j, cls) for j in body.findall("joint")]
            if len(js) > 1:
                sys.exit(f"{name}: more than one joint in a body")
            jt = {"name": js[0]["name"] if js else f"{name}_fixed", "type": "fixed", "parent": parent, "child": name,
                  "xyz": nums(body.get("pos")), "rpy": quat_rpy(*q)}
            if js:
                j = js[0]
                if j.get("type", "hinge") != "hinge" or any(abs(v) > 1e-12 for v in nums(j.get("pos"))):
                    sys.exit(f"{name}: only hinge joints at the body's origin are read")
                jt.update(type="revolute", axis=nums(j.get("axis"), "0 0 1"), limit=nums(j.get("range"), "0 0"))
            joints.append(jt)
        for c in body.findall("body"):
            walk(c, name, cls)

    for b in root.find("worldbody").findall("body"):
        walk(b, None, None)
    return links, joints


# ---------------- OYMotion ROHand: the linkage ----------------
def rohand_tables(joints):
    """OYMotion's FingerMathURDF.py (oymotion/rohand_urdf_ros2, MIT), as its node publishes the joints: each
    finger's slider position (m) gives the angles of its linkage's continuous joints. Sampled along each slider's
    range; the page interpolates. Lengths in mm, angles in radians, constants as OYMotion calibrated them."""
    HALF_PI, ONE_HALF_PI, PI = 1.570796326794896, 4.71238898038469, 3.141592653589793
    acos_ = lambda La, Lb, Lc: math.acos((Lb * Lb + Lc * Lc - La * La) / (2 * Lb * Lc))
    length = lambda ang, Lb, Lc: math.sqrt(Lb * Lb + Lc * Lc - 2 * Lb * Lc * math.cos(ang))
    TH = [11.48, 0.48, 10.98, 10.00, 0.5983, 43.78, 2.08, 0.2155, 52.52, 9.90, 11.30, 1.2976, 27.54, 51.30, 26.8, 0.4184, 13.31]
    FI = [[12.70, 8.60, 19.63, 14.25, 0.5353, 0.7624, 0.8496, 35.92, 27.44, 8.63, 7.69, 34.14, 50.23],
          [13.17, 8.60, 19.63, 14.31, 0.5353, 0.7763, 0.8496, 41.01, 32.39, 8.63, 7.69, 39.48, 50.23],
          [13.00, 8.60, 19.63, 14.25, 0.5353, 0.7624, 0.8496, 35.92, 27.44, 8.63, 7.69, 34.14, 50.23],
          [13.15, 8.60, 19.63, 14.27, 0.5353, 0.7502, 0.8141, 31.93, 23.59, 8.63, 7.53, 30.85, 35.53]]
    OFF_TH = [0.6074383248631001, 2.8197538544904397, 1.2557970445133417]
    OFF = [[3.055350818197261, 3.097067763726074, 2.87820648914036, 2.3908318621005367],
           [3.0346826701825362, 3.073820699422426, 2.944724914084966, 2.391084783991995],
           [3.0397366575345286, 3.065587927708385, 2.837397232568017, 2.3530467141470157],
           [3.0307258069795937, 3.0363511158112364, 2.865085492814143, 2.2973462058501406]]

    def thumb(pos):
        pos = (pos - 0.003) * 1000
        L_BP0, L_OP, L_AB, L_OA, A_OAR, L_CT0, L_OT, A_EOQ, L_OE, L_CD, L_ED, A_DEF, L_EF, XE = TH[:14]
        L_BP = L_BP0 + pos
        L_OB = math.sqrt(L_OP * L_OP + L_BP * L_BP)
        A_OBP = math.atan(L_OP / L_BP)
        A_QOS = acos_(L_AB, L_OA, L_OB) - A_OBP - A_OAR
        L_CT = L_CT0 + pos
        L_OC = math.sqrt(L_CT * L_CT + L_OT * L_OT)
        A_OCT = math.atan(L_OT / L_CT)
        L_CE = length(A_EOQ + A_OCT, L_OE, L_OC)
        A_CEF = acos_(L_CD, L_CE, L_ED) + A_DEF
        L_CF = length(A_CEF, L_CE, L_EF)
        A_ECF = acos_(L_EF, L_CE, L_CF)
        A_QCF = HALF_PI - (HALF_PI - math.atan((XE - L_CT) / L_CE) - A_ECF)
        A_DCT = acos_(L_ED, L_CD, L_CE) + (A_QCF - A_ECF) + HALF_PI
        L_OD = length(A_DCT - A_OCT, L_OC, L_CD)
        A_OED = acos_(L_OD, L_OE, L_ED)
        return [A_QOS - OFF_TH[0], A_DCT - OFF_TH[1], OFF_TH[2] - A_OED]

    def finger(k, pos):
        pos = (pos - 0.003) * 1000
        X_A0, L_AP, L_AC, L_OC, A_BOQ, A_COD, A_EDF, L_OD, _, L_OB, L_DE, L_BE, _ = FI[k]
        L_OP = X_A0 + pos
        L_OA = math.sqrt(L_OP * L_OP + L_AP * L_AP)
        A_AOP = acos_(L_AP, L_OA, L_OP)
        A_CAR = ONE_HALF_PI - (HALF_PI - A_AOP) - acos_(L_OC, L_AC, L_OA)
        A_DOP = A_COD + A_AOP + acos_(L_AC, L_OC, L_OA)
        A_DOB = A_BOQ + PI - A_DOP
        L_BD = length(A_DOB, L_OB, L_OD)
        A_BDE = acos_(L_BE, L_DE, L_BD)
        A_EDO = A_BDE - acos_(L_OB, L_BD, L_OD)
        A_EBO = acos_(length(A_BDE, L_DE, L_OD), L_BE, L_OB)
        return [A_CAR - OFF[k][0], A_DOP - OFF[k][1], A_EDF + A_EDO - OFF[k][2], A_EBO - OFF[k][3]]

    lim = {j["name"]: j["limit"] for j in joints if j["type"] == "prismatic"}
    tables = {}
    drive = {"th_slider_link": (thumb, ["th_proximal_link", "th_connecting_link", "th_distal_link"])}
    for k, f in enumerate(["if", "mf", "rf", "lf"]):
        drive[f"{f}_slider_link"] = (lambda p, k=k: finger(k, p),
                                     [f"{f}_slider_abpart_link", f"{f}_proximal_link", f"{f}_distal_link", f"{f}_connecting_link"])
    for slider, (fn, names) in drive.items():
        lo, hi = lim[slider]
        xs = [lo + (hi - lo) * i / 16 for i in range(17)]
        ys = [fn(x) for x in xs]
        for i, n in enumerate(names):
            tables[n] = {"joint": slider, "x": [round(x, 6) for x in xs], "y": [round(y[i], 5) for y in ys]}
    return tables


# ---------------- edge collapse ----------------
def decimate(points, faces, err, target=0):
    """Garland and Heckbert's edge collapse on a welded mesh (points; faces as (a, b, c, class)). Each vertex sums the
    area-weighted planes of its triangles; open edges and edges between classes add steep planes across them, so
    outlines and colour borders stay. The cheapest collapse goes first, its cost the mean squared distance (over the
    area of the planes) of the merged vertex from them; a collapse that would flip a triangle, or break the surface
    (the link condition), is skipped. Stops when the next costs more than err² or `target` triangles are left."""
    import heapq
    n = len(points)
    P = [list(p) for p in points]
    F = [list(f[:3]) for f in faces]
    cls = [f[3] for f in faces]
    alive = [True] * len(F)
    Q = [[0.0] * 11 for _ in range(n)]
    vf = [set() for _ in range(n)]
    edges = {}
    normal = []
    for i, (a, b, c) in enumerate(F):
        pa, pb, pc = P[a], P[b], P[c]
        ux, uy, uz = pb[0] - pa[0], pb[1] - pa[1], pb[2] - pa[2]
        vx, vy, vz = pc[0] - pa[0], pc[1] - pa[1], pc[2] - pa[2]
        nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
        ln = math.sqrt(nx * nx + ny * ny + nz * nz)
        normal.append((nx / ln, ny / ln, nz / ln) if ln else (0.0, 0.0, 0.0))
        for v in (a, b, c):
            vf[v].add(i)
        for e in ((a, b), (b, c), (c, a)):
            edges.setdefault((min(e), max(e)), []).append(i)
        if not ln:
            continue
        nx, ny, nz = normal[-1]
        d = -(nx * pa[0] + ny * pa[1] + nz * pa[2])
        w = ln / 2
        q = (w * nx * nx, w * nx * ny, w * nx * nz, w * nx * d, w * ny * ny, w * ny * nz, w * ny * d, w * nz * nz, w * nz * d, w * d * d, w)
        for v in (a, b, c):
            s = Q[v]
            for k in range(11):
                s[k] += q[k]
    locked = set()
    for (a, b), fs in edges.items():
        if len(fs) == 2 and cls[fs[0]] == cls[fs[1]]:
            continue
        # an open edge, a colour border or an edge of more than two triangles (CAD parts that touch): a plane
        # through the edge, across each triangle, weighted heavily
        pa, pb = P[a], P[b]
        ex, ey, ez = pb[0] - pa[0], pb[1] - pa[1], pb[2] - pa[2]
        el2 = ex * ex + ey * ey + ez * ez
        for f in fs:
            fx, fy, fz = normal[f]
            mx, my, mz = ey * fz - ez * fy, ez * fx - ex * fz, ex * fy - ey * fx
            lm = math.sqrt(mx * mx + my * my + mz * mz)
            if not lm:
                continue
            mx, my, mz = mx / lm, my / lm, mz / lm
            d = -(mx * pa[0] + my * pa[1] + mz * pa[2])
            w = 100.0 * el2
            q = (w * mx * mx, w * mx * my, w * mx * mz, w * mx * d, w * my * my, w * my * mz, w * my * d, w * mz * mz, w * mz * d, w * d * d, 0.0)
            for v in (a, b):
                s = Q[v]
                for k in range(11):
                    s[k] += q[k]
    stamp = [0] * n

    def cost(u, v):
        qu, qv = Q[u], Q[v]
        q = [qu[k] + qv[k] for k in range(11)]
        area = q[10] or 1e-30
        pu, pv = P[u], P[v]
        cands = [pu, pv, [(pu[k] + pv[k]) / 2 for k in range(3)]]
        a00, a01, a02, a11, a12, a22 = q[0], q[1], q[2], q[4], q[5], q[7]
        det = a00 * (a11 * a22 - a12 * a12) - a01 * (a01 * a22 - a12 * a02) + a02 * (a01 * a12 - a11 * a02)
        if abs(det) > 1e-12 * (a00 + a11 + a22 + 1e-30) ** 3:
            b0, b1, b2 = -q[3], -q[6], -q[8]
            x = ((b0 * (a11 * a22 - a12 * a12) - a01 * (b1 * a22 - a12 * b2) + a02 * (b1 * a12 - a11 * b2)) / det,
                 (a00 * (b1 * a22 - a12 * b2) - b0 * (a01 * a22 - a12 * a02) + a02 * (a01 * b2 - b1 * a02)) / det,
                 (a00 * (a11 * b2 - b1 * a12) - a01 * (a01 * b2 - b1 * a02) + b0 * (a01 * a12 - a11 * a02)) / det)
            m = cands[2]
            el = math.dist(pu, pv)
            if math.dist(x, m) <= el:
                cands.append(list(x))
        best, bx = None, None
        for x in cands:
            e = (q[0] * x[0] * x[0] + 2 * q[1] * x[0] * x[1] + 2 * q[2] * x[0] * x[2] + 2 * q[3] * x[0] + q[4] * x[1] * x[1]
                 + 2 * q[5] * x[1] * x[2] + 2 * q[6] * x[1] + q[7] * x[2] * x[2] + 2 * q[8] * x[2] + q[9])
            if best is None or e < best:
                best, bx = e, x
        return max(best, 0.0) / area, bx

    heap = []
    for (a, b) in edges:
        if a in locked or b in locked:
            continue
        c, x = cost(a, b)
        heap.append((c, a, b, 0, 0))
    heapq.heapify(heap)
    live = len(F)
    lim = err * err

    def ring(v):
        s = set()
        for f in vf[v]:
            s.update(F[f])
        s.discard(v)
        return s

    while heap and live > target:
        c, u, v, su, sv = heapq.heappop(heap)
        if c > lim:
            break
        if stamp[u] != su or stamp[v] != sv or u in locked or v in locked:
            continue
        shared = vf[u] & vf[v]
        if not shared:
            continue
        c, x = cost(u, v)     # Q may have grown since the push
        if c > lim:
            continue
        # link condition: the vertices next to both are exactly the third corners of the shared triangles
        third = set()
        for f in shared:
            third.update(F[f])
        third -= {u, v}
        if (ring(u) & ring(v)) != third:
            continue
        ok = True
        for f in (vf[u] | vf[v]) - shared:
            a, b, cc = (x if k in (u, v) else P[k] for k in F[f])
            ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
            vx, vy, vz = cc[0] - a[0], cc[1] - a[1], cc[2] - a[2]
            nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
            ln = math.sqrt(nx * nx + ny * ny + nz * nz)
            o = normal[f]
            if ln == 0 or (nx * o[0] + ny * o[1] + nz * o[2]) / ln < 0.2:
                ok = False
                break
        if not ok:
            continue
        for f in shared:
            alive[f] = False
            live -= 1
            for k in F[f]:
                vf[k].discard(f)
        for f in vf[v]:
            F[f] = [u if k == v else k for k in F[f]]
        vf[u] |= vf[v]
        vf[v] = set()
        for f in vf[u]:
            a, b, cc = (P[k] if k != u else x for k in F[f])
            ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
            vx, vy, vz = cc[0] - a[0], cc[1] - a[1], cc[2] - a[2]
            nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
            ln = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
            normal[f] = (nx / ln, ny / ln, nz / ln)
        qu, qv = Q[u], Q[v]
        for k in range(11):
            qu[k] += qv[k]
        P[u] = list(x)
        stamp[u] += 1
        stamp[v] = -1
        for w in ring(u):
            if w in locked:
                continue
            c2, _ = cost(u, w)
            a, b = (u, w) if u < w else (w, u)
            heapq.heappush(heap, (c2, a, b, stamp[a], stamp[b]))
    remap, pts, out = {}, [], []
    for i, f in enumerate(F):
        if not alive[i]:
            continue
        g = []
        for k in f:
            if k not in remap:
                remap[k] = len(pts)
                pts.append(tuple(P[k]))
            g.append(remap[k])
        out.append((g[0], g[1], g[2], cls[i]))
    return pts, out


# ---------------- build ----------------
def build(hand):
    m = MANIFEST[hand["id"]]
    src = SRC / hand["id"]
    path = src / m["model"]
    links, joints = mjcf(hand, path) if path.suffix == ".xml" else urdf(hand, path)
    if hand.get("linkage") == "rohand":
        tables = rohand_tables(joints)
        for j in joints:
            if j["name"] in tables:
                j["table"] = tables[j["name"]]
    classify = hand.get("classify", one)
    meshes, visuals, cache, shift, files = [], [], {}, [], [path]
    source = after = 0
    for l in links:
        for v in l["visuals"]:
            # one mesh for every link that shows the same file the same way (fingers alike)
            key = (v["file"], tuple(v["scale"]), classify.key(l["name"], v["rgba"]))
            if key not in cache:
                tris = triangles(v["file"], v["scale"])
                pts, faces = mu.simplify(tris, hand.get("cell", CELL), classify(l["name"], v["rgba"]))
                pts, faces = decimate(pts, faces, hand.get("err", ERR))
                # Some makers export each part in the assembly's frame, beyond what int16 × UNIT reaches (±0.327 m)
                # from the link's origin: such a mesh is moved to its box's centre and the visual's origin with it.
                used = [pts[i] for f in faces for i in f[:3]]
                c = (0.0, 0.0, 0.0)
                if used and max(abs(x) for p in used for x in p) > 0.3:
                    c = tuple(round((min(p[i] for p in used) + max(p[i] for p in used)) / 2, 5) for i in range(3))
                    pts = [(p[0] - c[0], p[1] - c[1], p[2] - c[2]) for p in pts]
                cache[key] = len(meshes)
                shift.append(c)
                meshes.append(mu.pack(pts, faces, hand["classes"]))
                source += len(tris)
                after += meshes[-1]["triangles"]
                if v["file"] not in files:
                    files.append(v["file"])
            c, xyz = shift[cache[key]], v["xyz"]
            if any(c):
                r = rot(v["rpy"])
                xyz = [round(xyz[i] + sum(r[i][k] * c[k] for k in range(3)), 9) for i in range(3)]
            visuals.append({"link": l["name"], "mesh": cache[key], "xyz": xyz, "rpy": v["rpy"]})
    lic = [src / n for n in m["licences"]]
    out = {
        "id": hand["id"], "brand": hand["brand"], "model": hand["model"],
        "source": {"repo": m["repo"], "commit": m["commit"], "path": m["root"], "license": m["spdx"],
                   "sha256": {f.relative_to(src.resolve()).as_posix(): hashlib.sha256(f.read_bytes()).hexdigest() for f in files}},
        "unit": mu.UNIT, "cell": hand.get("cell", CELL), "err": hand.get("err", ERR), "trianglesSource": source, "triangles": after,
        "mass": round(sum(l["mass"] for l in links), 6),
        "links": [{"name": l["name"], "mass": l["mass"]} for l in links],
        "joints": joints, "visuals": visuals, "meshes": meshes,
    }
    if lic:
        text = "\n\n".join(f.read_text(encoding="utf-8", errors="replace").strip() for f in lic)
        licence = "// The model is the maker's, under this licence:\n//\n" + \
            "".join(f"//   {x}".rstrip() + "\n" for x in text.splitlines())
    else:
        licence = f"// The maker's repository ({m['repo']}) states no licence: all rights stay with the maker.\n"
    head = (f"// Generated by make_other_hands.py from other_hands/{hand['id']}/: {hand['brand']} {hand['model']} as the maker\n"
            f"// publishes it ({m['repo']} at {m['commit'][:7]}), each link in its own frame, metres. Meshes welded on a\n"
            f"// {hand.get('cell', CELL) * 1000:g} mm grid, then simplified by edge collapse to {hand.get('err', ERR) * 1000:g} mm; positions int16 × unit,\n"
            "// normals int8, base64. Do not edit: rerun the script.\n"
            + licence + "\n")
    return head + "export const END=" + json.dumps(out, ensure_ascii=False, separators=(",", ":")) + ";\n", out


def work(hid):
    return build(next(h for h in HANDS if h["id"] == hid))


def main():
    check = "--check" in sys.argv
    only = [a for a in sys.argv[1:] if not a.startswith("--")]
    ids = [h["id"] for h in HANDS if not only or h["id"] in only]
    bad = []
    # Four hands at a time (each holds its source triangles, up to some 300 MB for the largest).
    import concurrent.futures as cf
    import multiprocessing as mp
    with cf.ProcessPoolExecutor(max_workers=min(4, len(ids)), mp_context=mp.get_context("fork")) as ex:
        for hid, (text, out) in zip(ids, ex.map(work, ids)):
            path = OUT / f"{hid}.mjs"
            if check:
                if not path.is_file() or path.read_text(encoding="utf-8") != text:
                    bad.append(path.name)
                continue
            OUT.mkdir(exist_ok=True)
            path.write_text(text, encoding="utf-8")
            hand = next(h for h in HANDS if h["id"] == hid)
            print(f"{path.relative_to(here)}: {path.stat().st_size // 1024} KB; {out['trianglesSource']} → {out['triangles']} triangles "
                  f"({hand.get('cell', CELL) * 1000:g} mm grid, {hand.get('err', ERR) * 1000:g} mm), {len(out['links'])} links, "
                  f"{sum(j['type'] != 'fixed' for j in out['joints'])} moving joints, {out['mass']:.3f} kg", flush=True)
    if check:
        print("other_hands_mesh/ is current" if not bad else f"differ from what the models give: {', '.join(bad)}: rerun make_other_hands.py")
        sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
