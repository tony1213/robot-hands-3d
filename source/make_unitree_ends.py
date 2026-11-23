#!/usr/bin/env python3
"""Build unitree_ends_mesh/<id>.mjs, Unitree's grippers and hands for unitree_ends_3d.html, from the maker's URDFs and
meshes: Dex1-1 from unitree_dex1_1/, Dex2/5, Dex3-1, Dex5-1, Dex5-S and the Z1 arm's gripper from unitree_ends/.

    python3 make_unitree_ends.py          write the modules
    python3 make_unitree_ends.py --check  only check that they are what the meshes give (exit 1 if not)

The meshes are SolidWorks exports, tessellated far finer than a page needs (Dex2/5 alone is some 790,000 triangles).
Each mesh is simplified by vertex clustering on a grid of CELL metres: every cell's vertices become one, placed where
the planes of the triangles around them meet best (the sum of their area-weighted plane quadrics, solved with small
eigenvalues dropped, as in Lindstrom's out-of-core simplification), so flat faces stay flat and edges stay sharp; the
triangles left with two corners in one cell go. Then normals are smoothed across facets less than CREASE degrees apart
and kept sharp at edges, and the mesh is packed: positions as int16 in UNIT steps, normals as int8, base64.

Each module keeps the URDF's links, joints (origin, axis, limits) and visuals in the URDF's own frames, with the mass
of each link; the page builds the kinematic tree from them. The Z1 gripper is not a URDF of its own: it is the block
of the Z1 arm's xacro that adds it (robot.xacro, values from const.xacro), read here. Which way each hand closes, how
it stands and its colours are the page's. Standard library only.
"""
import ast
import base64
import hashlib
import json
import math
import struct
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

here = Path(__file__).resolve().parent
OUT = here / "unitree_ends_mesh"
UNIT = 1e-5          # m per int16 step
CREASE = 40.0        # degrees: facets closer than this share a normal
OFF = 1 << 20        # added to cell indices so int() floors them
REPO = "unitreerobotics/unitree_ros"
COMMIT = "157ff950351e5f535e03c5d85a16b7d594b3dbcc"   # master on 2026-11-21; unitree_ends/README.md


def dex1_classes(link, flip):
    """Dex1-1: the base is one part; the finger's triangles (finger 1's frame; finger 2 is finger 1 turned half a turn
    about x, so flip y and z back) go to the bar of the guide rail and rack behind the joint's plane (steel where it
    stands out of the housing, up to the black stop at its far end), the jaw's inner face beyond the housing (pad),
    and the rest (black), as make_dex1_mesh.py sorts them for the 3D page."""
    if not link.startswith("Dex1_finger"):
        return lambda t, n: 0
    s = -1 if flip(link) else 1

    def cls(t, n):
        cx = sum(p[0] for p in t) / 3
        cy = s * sum(p[1] for p in t) / 3
        if cx < -0.0003 and cy < 0.032:
            return 1
        if cx > 0.012 and s * n[1] > 0.95:
            return 2
        return 0
    return cls


# id, model, source folder (unitree_ends/<id> unless given), URDF in it, commit, path in the repo, cell (m), classes,
# links left out, class of each link's triangles.
HANDS = [
    {"id": "dex1_1", "model": "Dex1-1", "dir": here / "unitree_dex1_1", "urdf": "dex1_1.urdf",
     "commit": "8927c58e133b5e234e78b8581016f9a4867e9e1c", "path": "robots/dexterous_hand_description/dex1_1",
     "cell": 0.0003, "classes": ["body", "metal", "pad"], "skip": {"Camera"},
     "classify": lambda link: dex1_classes(link, lambda l: l.endswith("_2"))},
    # Dex2/5: the proximal segment of each finger (right_<finger>1_link) is the bare metal frame in the maker's photos.
    {"id": "dex2_5", "model": "Dex2/5", "urdf": "Right_Hand.urdf", "path": "robots/dexterous_hand_description/dex2_5",
     "cell": 0.0007, "classes": ["body", "metal"],
     "classify": lambda link: (lambda t, n: 1 if link[-6:-5] == "1" and link != "right_0_link" else 0)},
    {"id": "dex3_1", "model": "Dex3-1", "urdf": "dex3_1_r.urdf", "path": "robots/dexterous_hand_description/dex3_1",
     "cell": 0.0006, "classes": ["body"]},
    {"id": "dex5_1", "model": "Dex5-1", "urdf": "Dex5-URDF-R/Dex5-URDF-R.urdf",
     "path": "robots/dexterous_hand_description/dex5_1", "cell": 0.00055, "classes": ["body", "finger"],
     "classify": lambda link: (lambda t, n: 0 if link.startswith("base") else 1)},
    {"id": "dex5_s", "model": "Dex5-S", "urdf": "dex5s.urdf", "path": "robots/dexterous_hand_description/dex5_s",
     "cell": 0.0006, "classes": ["body", "silicone"],
     "classify": lambda link: (lambda t, n: 1 if "silicone" in link else 0)},
    {"id": "z1", "model": "Z1 夹爪", "xacro": True, "path": "robots/z1_description", "cell": 0.0006,
     "classes": ["body"]},
]


def stl(path):
    """Triangles of a binary STL as [((x, y, z) × 3), …] in metres."""
    b = path.read_bytes()
    n = struct.unpack_from("<I", b, 80)[0]
    if len(b) != 84 + 50 * n:
        sys.exit(f"{path}: not a binary STL of {n} triangles")
    return [(v[3:6], v[6:9], v[9:12]) for v in struct.iter_unpack("<12fH", b[84:])]


def nums(s, default="0 0 0"):
    return [float(v) for v in (s or default).split()]


def urdf(hand, src):
    """Links (name, mass, visuals) and joints of a URDF, the visuals' mesh files resolved in the source folder."""
    path = src / hand["urdf"]
    root = ET.parse(path).getroot()
    links, joints = [], []
    for l in root.findall("link"):
        if l.get("name") in hand.get("skip", ()):
            continue
        m = l.find("inertial/mass")
        vis = []
        for v in l.findall("visual"):
            g = v.find("geometry/mesh")
            if g is None:
                sys.exit(f"{path.name}: {l.get('name')} has a visual that is not a mesh")
            fn = g.get("filename")
            rel = fn.split("://", 1)[1].split("/", 1)[1] if "://" in fn else fn
            f = next((c for c in (path.parent / rel, src / rel) if c.is_file()), None)
            if f is None:
                sys.exit(f"{path.name}: {fn} is not in {src.relative_to(here)}")
            o = v.find("origin")
            vis.append({"file": f, "xyz": nums(o.get("xyz") if o is not None else None),
                        "rpy": nums(o.get("rpy") if o is not None else None), "scale": nums(g.get("scale"), "1 1 1")})
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
            jt["limit"] = [float(lim.get("lower")), float(lim.get("upper"))]
        if mim is not None:
            jt["mimic"] = {"joint": mim.get("joint"), "multiplier": float(mim.get("multiplier", "1")),
                           "offset": float(mim.get("offset", "0"))}
        joints.append(jt)
    return links, joints, [path]


def evaluate(expr, props):
    """A xacro value: a number, or ${…} arithmetic over numbers, PI and the properties."""
    expr = expr.strip()
    if not expr.startswith("${"):
        return float(expr)

    def ev(node):
        if isinstance(node, ast.Expression):
            return ev(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)
        if isinstance(node, ast.Name):
            if node.id == "PI":
                return math.pi
            return evaluate(props[node.id], props)
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
            v = ev(node.operand)
            return -v if isinstance(node.op, ast.USub) else v
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)):
            a, b = ev(node.left), ev(node.right)
            return {ast.Add: a + b, ast.Sub: a - b, ast.Mult: a * b, ast.Div: a / b if b else math.nan}[type(node.op)]
        sys.exit(f"xacro expression {expr!r}: cannot evaluate {ast.dump(node)}")
    return ev(ast.parse(expr[2:-1], mode="eval"))


def z1(src):
    """The Z1 gripper from the arm's xacro: the block under <xacro:if value="$(arg UnitreeGripper)">, its links' meshes
    the collision STLs (the visual .dae files are the same mesh without materials)."""
    X = "{http://www.ros.org/wiki/xacro}"
    props = {p.get("name"): p.get("value") for p in ET.parse(src / "xacro" / "const.xacro").getroot().iter(X + "property")}
    root = ET.parse(src / "xacro" / "robot.xacro").getroot()
    block = next(e for e in root.iter(X + "if") if "UnitreeGripper" in e.get("value", ""))
    links, joints = [], []
    for l in block.findall("link"):
        fn = l.find("collision/geometry/mesh").get("filename")
        f = src / fn.split("://", 1)[1].split("/", 1)[1]
        links.append({"name": l.get("name"), "mass": evaluate(l.find("inertial/mass").get("value"), props),
                      "visuals": [{"file": f, "xyz": [0, 0, 0], "rpy": [0, 0, 0], "scale": [1, 1, 1]}]})
    names = {l["name"] for l in links}
    for j in block.findall("joint"):
        if j.find("child").get("link") not in names or j.find("parent").get("link") not in names:
            continue      # the stator's joint to the arm's link06: the gripper stands alone here
        o, a, lim = j.find("origin"), j.find("axis"), j.find("limit")
        joints.append({"name": j.get("name"), "type": j.get("type"), "parent": j.find("parent").get("link"),
                       "child": j.find("child").get("link"), "xyz": nums(o.get("xyz")), "rpy": nums(o.get("rpy")),
                       "axis": nums(a.get("xyz")),
                       "limit": [evaluate(lim.get("lower"), props), evaluate(lim.get("upper"), props)]})
    return links, joints, [src / "xacro" / "robot.xacro", src / "xacro" / "const.xacro"]


def eig3(a):
    """Eigenvalues and eigenvectors (columns of v) of a symmetric 3×3 matrix, by Jacobi rotations."""
    a = [row[:] for row in a]
    v = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
    for _ in range(30):
        off = a[0][1] ** 2 + a[0][2] ** 2 + a[1][2] ** 2
        if off <= 1e-24 * (a[0][0] ** 2 + a[1][1] ** 2 + a[2][2] ** 2) + 1e-300:
            break
        for p, q in ((0, 1), (0, 2), (1, 2)):
            if abs(a[p][q]) < 1e-300:
                continue
            theta = (a[q][q] - a[p][p]) / (2 * a[p][q])
            t = (1.0 if theta >= 0 else -1.0) / (abs(theta) + math.sqrt(theta * theta + 1))
            c = 1 / math.sqrt(t * t + 1)
            s = t * c
            for k in range(3):
                akp, akq = a[k][p], a[k][q]
                a[k][p], a[k][q] = c * akp - s * akq, s * akp + c * akq
            for k in range(3):
                apk, aqk = a[p][k], a[q][k]
                a[p][k], a[q][k] = c * apk - s * aqk, s * apk + c * aqk
            for k in range(3):
                vkp, vkq = v[k][p], v[k][q]
                v[k][p], v[k][q] = c * vkp - s * vkq, s * vkp + c * vkq
    return [a[0][0], a[1][1], a[2][2]], v


def simplify(tris, cell, classify):
    """Vertex clustering with quadric placement. tris in the link's frame; classify(tri, unit normal) → class index.
    Returns the cells' points and the triangles left, as (a, b, c, class)."""
    inv = 1.0 / cell
    index, acc, corners = {}, [], []
    for t in tris:
        (x0, y0, z0), (x1, y1, z1), (x2, y2, z2) = t
        ux, uy, uz = x1 - x0, y1 - y0, z1 - z0
        vx, vy, vz = x2 - x0, y2 - y0, z2 - z0
        nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
        ln = math.sqrt(nx * nx + ny * ny + nz * nz)
        if ln > 0:
            a, b, c = nx / ln, ny / ln, nz / ln
            d = -(a * x0 + b * y0 + c * z0)
            w = ln / 2
            q = (w * a * a, w * a * b, w * a * c, w * a * d, w * b * b, w * b * c, w * b * d, w * c * c, w * c * d, w * d * d)
        else:
            a = b = c = 0.0
            q = None
        f = []
        for x, y, z in t:
            k = (int(x * inv + OFF), int(y * inv + OFF), int(z * inv + OFF))
            i = index.get(k)
            if i is None:
                i = index[k] = len(acc)
                acc.append([0.0] * 13 + [0, k])
            s = acc[i]
            if q is not None:
                for j in range(10):
                    s[j] += q[j]
            s[10] += x
            s[11] += y
            s[12] += z
            s[13] += 1
            f.append(i)
        corners.append((f, classify(t, (a, b, c))))
    points = []
    for s in acc:
        n = s[13]
        m = (s[10] / n, s[11] / n, s[12] / n)
        A = [[s[0], s[1], s[2]], [s[1], s[4], s[5]], [s[2], s[5], s[7]]]
        r = [-(A[i][0] * m[0] + A[i][1] * m[1] + A[i][2] * m[2] + (s[3], s[6], s[8])[i]) for i in range(3)]
        lam, v = eig3(A)
        top = max(lam)
        p = list(m)
        for i in range(3):
            if top > 0 and lam[i] > 1e-2 * top:
                k = (v[0][i] * r[0] + v[1][i] * r[1] + v[2][i] * r[2]) / lam[i]
                for j in range(3):
                    p[j] += k * v[j][i]
        k = s[14]
        for j in range(3):   # stay within half a cell of the cell
            lo = (k[j] - OFF - 0.5) * cell
            p[j] = min(max(p[j], lo), lo + 2 * cell)
        points.append(tuple(p))
    faces, seen = [], set()
    for (a, b, c), cls in corners:
        if a == b or b == c or a == c:
            continue
        m = min(a, b, c)
        key = (a, b, c) if m == a else (b, c, a) if m == b else (c, a, b)
        if key in seen:
            continue
        seen.add(key)
        faces.append((a, b, c, cls))
    return points, faces


def pack(points, faces, classes):
    """Crease normals, sort by class, pack. Points in the link's frame."""
    used = sorted({v for f in faces for v in f[:3]})
    normals, units = [], []
    for a, b, c, _ in faces:
        u = [points[b][i] - points[a][i] for i in range(3)]
        v = [points[c][i] - points[a][i] for i in range(3)]
        n = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
        l = math.sqrt(sum(x * x for x in n)) or 1.0
        normals.append(n)
        units.append(tuple(x / l for x in n))
    around = {v: [] for v in used}
    for i, f in enumerate(faces):
        for v in f[:3]:
            around[v].append(i)
    cos = math.cos(math.radians(CREASE))
    out_pos, out_nor, out_idx, seen, spans = [], [], [], {}, []
    for ci, name in enumerate(classes):
        start = len(out_idx)
        for i, f in enumerate(faces):
            if f[3] != ci:
                continue
            for v in f[:3]:
                s = [0.0, 0.0, 0.0]
                for j in around[v]:
                    if sum(units[i][k] * units[j][k] for k in range(3)) >= cos:
                        for k in range(3):
                            s[k] += normals[j][k]
                l = math.sqrt(sum(x * x for x in s)) or 1.0
                q = tuple(max(-127, min(127, round(x / l * 127))) for x in s)
                k = (v, q)
                if k not in seen:
                    seen[k] = len(out_pos)
                    p = tuple(round(c / UNIT) for c in points[v])
                    if max(abs(c) for c in p) > 32767:
                        sys.exit(f"a point {points[v]} is beyond int16 × {UNIT} m")
                    out_pos.append(p)
                    out_nor.append(q)
                out_idx.append(seen[k])
        if len(out_idx) > start:
            spans.append([name, start, len(out_idx) - start])
    big = len(out_pos) > 65535
    b64 = lambda b: base64.b64encode(b).decode("ascii")
    return {"vertices": len(out_pos), "triangles": len(out_idx) // 3, "groups": spans, "index32": big,
            "position": b64(struct.pack(f"<{3 * len(out_pos)}h", *[c for p in out_pos for c in p])),
            "normal": b64(struct.pack(f"<{3 * len(out_nor)}b", *[c for p in out_nor for c in p])),
            "index": b64(struct.pack(f"<{len(out_idx)}{'I' if big else 'H'}", *out_idx))}


def build(hand):
    src = hand.get("dir", here / "unitree_ends" / hand["id"])
    links, joints, docs = z1(src) if hand.get("xacro") else urdf(hand, src)
    classify = hand.get("classify", lambda link: (lambda t, n: 0))
    meshes, visuals, cache, files = [], [], {}, list(docs)
    source = after = 0
    for l in links:
        for v in l["visuals"]:
            key = (v["file"], tuple(v["scale"]), l["name"])
            if key not in cache:
                tris = stl(v["file"])
                sx, sy, sz = v["scale"]
                if (sx, sy, sz) != (1, 1, 1):
                    tris = [tuple((p[0] * sx, p[1] * sy, p[2] * sz) for p in t) for t in tris]
                pts, faces = simplify(tris, hand["cell"], classify(l["name"]))
                cache[key] = len(meshes)
                meshes.append(pack(pts, faces, hand["classes"]))
                source += len(tris)
                after += meshes[-1]["triangles"]
                if v["file"] not in files:
                    files.append(v["file"])
            visuals.append({"link": l["name"], "mesh": cache[key], "xyz": v["xyz"], "rpy": v["rpy"]})
    lic = src / "LICENSE" if (src / "LICENSE").is_file() else here / "unitree_ends" / "LICENSE"
    out = {
        "id": hand["id"], "model": hand["model"],
        "source": {"repo": REPO, "commit": hand.get("commit", COMMIT), "path": hand["path"],
                   "license": "BSD-3-Clause",
                   "sha256": {f.relative_to(src).as_posix(): hashlib.sha256(f.read_bytes()).hexdigest() for f in files}},
        "unit": UNIT, "cell": hand["cell"], "trianglesSource": source, "triangles": after,
        "mass": round(sum(l["mass"] for l in links), 6),
        "links": [{"name": l["name"], "mass": l["mass"]} for l in links],
        "joints": joints, "visuals": visuals, "meshes": meshes,
    }
    licence = "".join(f"//   {x}".rstrip() + "\n" for x in lic.read_text(encoding="utf-8").strip().splitlines())
    head = (f"// Generated by make_unitree_ends.py from {src.relative_to(here).as_posix()}/: Unitree {hand['model']} as Unitree\n"
            f"// publishes it in unitree_ros ({out['source']['commit'][:7]}), each link in its URDF frame, metres. Meshes simplified\n"
            f"// on a {hand['cell'] * 1000:g} mm grid; positions int16 × unit, normals int8, base64. Do not edit: rerun the script.\n"
            "// The meshes are Unitree's, under this licence:\n//\n" + licence + "\n")
    return head + "export const END=" + json.dumps(out, ensure_ascii=False, separators=(",", ":")) + ";\n", out


def main():
    check = "--check" in sys.argv
    only = [a for a in sys.argv[1:] if not a.startswith("--")]
    bad = []
    for hand in HANDS:
        if only and hand["id"] not in only:
            continue
        text, out = build(hand)
        path = OUT / f"{hand['id']}.mjs"
        if check:
            if not path.is_file() or path.read_text(encoding="utf-8") != text:
                bad.append(path.name)
            continue
        OUT.mkdir(exist_ok=True)
        path.write_text(text, encoding="utf-8")
        print(f"{path.relative_to(here)}: {path.stat().st_size // 1024} KB; {out['trianglesSource']} → {out['triangles']} triangles "
              f"on a {hand['cell'] * 1000:g} mm grid, {len(out['links'])} links, "
              f"{sum(j['type'] != 'fixed' for j in out['joints'])} moving joints, {out['mass']:.3f} kg", flush=True)
    if check:
        print("unitree_ends_mesh/ is current" if not bad else f"differ from what the meshes give: {', '.join(bad)}: rerun make_unitree_ends.py")
        sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
