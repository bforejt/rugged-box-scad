#!/usr/bin/env python3
"""Regenerate example STLs from per-config manifests.

Each `examples/<config>/` directory carries:
  - build.json   : a manifest describing the source .scad, the Customizer
                   parameter set, and the list of parts to render.
  - params.json  : an OpenSCAD Customizer parameter file (one named set),
                   snapshotted from the scad-adjacent `src/rugged-box*.json`.

The renderer drives the OpenSCAD CLI once per part, overriding `Part` (and any
extra per-part variables) via `-D` on top of the loaded parameter set. Builds
are incremental: a part is skipped when its STL is newer than every input
(entrypoint .scad, shared library, included submodule files, params, manifest),
using OpenSCAD's `-d` dependency output to discover the true include set.

Stdlib only. Subcommands: build, snapshot (alias add), list, clean.

Notes on determinism: renders pass `--enable predictible-output`, which makes
simple parts byte-stable but does NOT fully stabilize boolean-heavy parts (e.g.
the Gridfinity `top`, which drifts a few degenerate triangles per render). That
noise is cosmetic (see the slicer-warnings note in the README). Incremental
rebuilds therefore key off mtimes, never content hashes.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLES_DIR = REPO_ROOT / "examples"
MANIFEST_NAME = "build.json"
SCHEMA_VERSION = 1

# Fallback OpenSCAD location on macOS when not on PATH and $OPENSCAD unset.
MAC_OPENSCAD = Path("/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD")

# Maps a manifest's entrypoint .scad to the scad-adjacent Customizer JSON that
# `snapshot` pulls named parameter sets from.
VARIANT_SOURCES = {
    "gridfinity": REPO_ROOT / "src" / "rugged-box-gridfinity.json",
    "standalone": REPO_ROOT / "src" / "rugged-box.json",
}


class BuildError(Exception):
    """Raised for user-facing configuration/render errors."""


# --------------------------------------------------------------------------- #
# OpenSCAD discovery
# --------------------------------------------------------------------------- #

def find_openscad():
    """Locate the OpenSCAD binary: $OPENSCAD, then PATH, then the macOS app."""
    env = os.environ.get("OPENSCAD")
    if env:
        p = Path(env)
        if p.is_file() and os.access(p, os.X_OK):
            return str(p)
        raise BuildError(
            "$OPENSCAD is set to {!r} but that is not an executable file.".format(env)
        )
    which = shutil.which("openscad")
    if which:
        return which
    if MAC_OPENSCAD.is_file() and os.access(MAC_OPENSCAD, os.X_OK):
        return str(MAC_OPENSCAD)
    raise BuildError(
        "Could not find OpenSCAD. Set $OPENSCAD to the binary, put `openscad` "
        "on PATH, or install OpenSCAD.app (macOS)."
    )


# --------------------------------------------------------------------------- #
# Manifest loading / validation
# --------------------------------------------------------------------------- #

def manifest_paths(configs=None):
    """Return manifest paths, optionally filtered to the named config dirs."""
    if not EXAMPLES_DIR.is_dir():
        return []
    found = sorted(EXAMPLES_DIR.glob("*/" + MANIFEST_NAME))
    if configs:
        wanted = set(configs)
        found = [m for m in found if m.parent.name in wanted]
        missing = wanted - {m.parent.name for m in found}
        if missing:
            raise BuildError(
                "No manifest for config(s): {}. Looked for examples/<name>/{}.".format(
                    ", ".join(sorted(missing)), MANIFEST_NAME
                )
            )
    return found


def load_manifest(path):
    """Read and validate a build.json, resolving its paths to absolutes."""
    try:
        data = json.loads(path.read_text())
    except (OSError, ValueError) as exc:
        raise BuildError("Cannot read manifest {}: {}".format(path, exc))

    schema = data.get("schema")
    if schema != SCHEMA_VERSION:
        raise BuildError(
            "{}: unsupported schema {!r} (this tool understands {}).".format(
                path, schema, SCHEMA_VERSION
            )
        )

    scad_rel = data.get("scad")
    if not scad_rel:
        raise BuildError("{}: missing required 'scad' field.".format(path))
    scad = (REPO_ROOT / scad_rel).resolve()
    if not scad.is_file():
        raise BuildError("{}: scad entrypoint not found: {}".format(path, scad))

    manifest_dir = path.parent
    params = data.get("params")
    params_path = (manifest_dir / params).resolve() if params else None
    if params_path and not params_path.is_file():
        raise BuildError("{}: params file not found: {}".format(path, params_path))

    parts = data.get("parts") or []
    if not parts:
        raise BuildError("{}: no 'parts' to render.".format(path))
    for i, part in enumerate(parts):
        if not part.get("output"):
            raise BuildError("{}: parts[{}] missing 'output'.".format(path, i))
        if not part.get("part"):
            raise BuildError("{}: parts[{}] missing 'part'.".format(path, i))

    return {
        "manifest_path": path,
        "config": manifest_dir.name,
        "dir": manifest_dir,
        "scad": scad,
        "params": params_path,
        "param_set": data.get("param_set"),
        "export_format": data.get("export_format", "binstl"),
        "parts": parts,
    }


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #

def serialize_define(name, value):
    """Build a `-D` value token from a JSON value, by type.

    bool -> Name=true/false ; number -> Name=3 ; str -> Name="text"
    (bool is checked first because it is a subclass of int).
    """
    if isinstance(value, bool):
        expr = "true" if value else "false"
    elif isinstance(value, (int, float)):
        expr = repr(value)
    else:
        expr = '"{}"'.format(value)
    return "{}={}".format(name, expr)


def build_cmd(oscad, m, part, output_path, depfile):
    """Assemble the OpenSCAD argument list for one part render."""
    cmd = [
        oscad,
        "--enable", "predictible-output",
        "-o", str(output_path),
        "--export-format", m["export_format"],
    ]
    if m["params"] and m["param_set"]:
        cmd += ["-p", str(m["params"]), "-P", m["param_set"]]
    # -D overrides come AFTER -p/-P so they win (verified behavior).
    cmd += ["-D", serialize_define("Part", part["part"])]
    for k, v in (part.get("overrides") or {}).items():
        cmd += ["-D", serialize_define(k, v)]
    cmd += ["-d", str(depfile), "-q", str(m["scad"])]
    return cmd


def parse_depfile(depfile):
    """Parse a Makefile-style depfile into a set of absolute prereq paths."""
    prereqs = set()
    try:
        text = depfile.read_text()
    except OSError:
        return prereqs
    # Strip line continuations, drop the "target:" prefix, collect the rest.
    text = text.replace("\\\n", " ")
    if ":" in text:
        text = text.split(":", 1)[1]
    for tok in text.split():
        tok = tok.strip()
        if tok:
            prereqs.add(Path(tok).resolve())
    return prereqs


def cached_depfile(output_path):
    return output_path.with_name(output_path.name + ".d")


def part_inputs(m, output_path):
    """Inputs whose mtime should trigger a rebuild of this part."""
    inputs = {m["scad"], m["manifest_path"]}
    if m["params"]:
        inputs.add(m["params"])
    # Union the cached dependency set (library + submodule includes) if present.
    dep = cached_depfile(output_path)
    if dep.is_file():
        inputs |= parse_depfile(dep)
    return {p for p in inputs if p.is_file()}


def needs_rebuild(output_path, inputs):
    if not output_path.is_file():
        return True
    out_mtime = output_path.stat().st_mtime
    return any(p.stat().st_mtime > out_mtime for p in inputs)


def render_part(oscad, m, part, force, dry_run):
    """Render one part. Returns one of: 'built', 'skipped', 'failed'."""
    output_path = (m["dir"] / part["output"]).resolve()
    inputs = part_inputs(m, output_path)

    if not force and not needs_rebuild(output_path, inputs):
        print("  skip   {}".format(part["output"]))
        return "skipped"

    if dry_run:
        print("  would  {}".format(part["output"]))
        return "skipped"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix=".d", delete=False) as tf:
        tmp_dep = Path(tf.name)
    try:
        cmd = build_cmd(oscad, m, part, output_path, tmp_dep)
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0 or not output_path.is_file():
            print("  FAIL   {}".format(part["output"]))
            err = (proc.stderr or "").strip()
            if err:
                for line in err.splitlines():
                    print("           {}".format(line))
            return "failed"
        # Cache the resolved dependency list beside the output for next time.
        prereqs = parse_depfile(tmp_dep)
        if prereqs:
            cached_depfile(output_path).write_text(
                "\n".join(sorted(str(p) for p in prereqs)) + "\n"
            )
        copies = part.get("copies", 1)
        suffix = "  (x{})".format(copies) if copies and copies != 1 else ""
        print("  built  {}{}".format(part["output"], suffix))
        return "built"
    finally:
        tmp_dep.unlink(missing_ok=True)


# --------------------------------------------------------------------------- #
# Subcommands
# --------------------------------------------------------------------------- #

def cmd_build(args):
    oscad = find_openscad()
    manifests = manifest_paths(args.configs)
    if not manifests:
        raise BuildError("No manifests found under examples/*/{}.".format(MANIFEST_NAME))

    totals = {"built": 0, "skipped": 0, "failed": 0}
    for mp in manifests:
        m = load_manifest(mp)
        parts = m["parts"]
        if args.part:
            parts = [p for p in parts if p["output"] == args.part or p["part"] == args.part]
            if not parts:
                continue
        print("{} ({})".format(m["config"], m["scad"].name))
        for part in parts:
            result = render_part(oscad, m, part, args.force, args.dry_run)
            totals[result] += 1

    print("\n{} built, {} skipped, {} failed".format(
        totals["built"], totals["skipped"], totals["failed"]))
    return 1 if totals["failed"] else 0


def cmd_snapshot(args):
    config_dir = EXAMPLES_DIR / args.config
    config_dir.mkdir(parents=True, exist_ok=True)

    variant = args.variant
    if not variant:
        # Infer from an existing manifest's scad, else default to gridfinity.
        mp = config_dir / MANIFEST_NAME
        variant = "gridfinity"
        if mp.is_file():
            try:
                scad = json.loads(mp.read_text()).get("scad", "")
                variant = "gridfinity" if "gridfinity" in scad else "standalone"
            except ValueError:
                pass

    source = VARIANT_SOURCES.get(variant)
    if source is None:
        raise BuildError("Unknown variant {!r} (expected gridfinity|standalone).".format(variant))
    if not source.is_file():
        raise BuildError("Source parameter file not found: {}".format(source))

    try:
        data = json.loads(source.read_text())
    except ValueError as exc:
        raise BuildError("Cannot parse {}: {}".format(source, exc))
    sets = data.get("parameterSets", {})
    if args.set not in sets:
        raise BuildError(
            "Set {!r} not in {}. Available: {}".format(
                args.set, source.name, ", ".join(sorted(sets)) or "(none)"
            )
        )

    out = config_dir / args.output
    if out.is_file() and not args.force:
        raise BuildError("{} exists; pass --force to overwrite.".format(out))
    payload = {"fileFormatVersion": "1", "parameterSets": {args.set: sets[args.set]}}
    out.write_text(json.dumps(payload, indent=4) + "\n")
    print("Wrote {} (set {!r} from {}).".format(out, args.set, source.name))
    if not (config_dir / MANIFEST_NAME).is_file():
        print("Note: no {} yet in {} — create one to define the parts to render.".format(
            MANIFEST_NAME, config_dir))
    return 0


def cmd_list(args):
    manifests = manifest_paths(args.configs)
    if not manifests:
        print("No manifests found under examples/*/{}.".format(MANIFEST_NAME))
        return 0
    for mp in manifests:
        m = load_manifest(mp)
        setdesc = " [{}]".format(m["param_set"]) if m["param_set"] else ""
        print("{} -> {}{}".format(m["config"], m["scad"].name, setdesc))
        for part in m["parts"]:
            copies = part.get("copies", 1)
            cps = "  x{}".format(copies) if copies and copies != 1 else ""
            ov = part.get("overrides") or {}
            ovs = "  {}".format(ov) if ov else ""
            note = "  - {}".format(part["note"]) if part.get("note") else ""
            print("    {:40s} Part={}{}{}{}".format(
                part["output"], part["part"], cps, ovs, note))
    return 0


def cmd_clean(args):
    manifests = manifest_paths(args.configs)
    targets = []
    for mp in manifests:
        m = load_manifest(mp)
        for part in m["parts"]:
            out = m["dir"] / part["output"]
            if out.is_file():
                targets.append(out)
            dep = cached_depfile(out.resolve())
            if dep.is_file():
                targets.append(dep)
    if not targets:
        print("Nothing to clean.")
        return 0
    for t in targets:
        if args.delete:
            t.unlink()
            print("removed {}".format(t.relative_to(REPO_ROOT)))
        else:
            print("would remove {}".format(t.relative_to(REPO_ROOT)))
    if not args.delete:
        print("\n(dry run; pass --delete to actually remove)")
    return 0


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    p_build = sub.add_parser("build", help="regenerate STLs (incremental)")
    p_build.add_argument("configs", nargs="*", help="config dir name(s); default: all")
    p_build.add_argument("--part", help="only this output filename or Part value")
    p_build.add_argument("--force", action="store_true", help="ignore mtimes; always render")
    p_build.add_argument("--dry-run", action="store_true", help="show what would build")
    p_build.set_defaults(func=cmd_build)

    p_snap = sub.add_parser("snapshot", aliases=["add"],
                            help="copy a Customizer set into an example folder")
    p_snap.add_argument("--config", required=True, help="examples/<config> dir name")
    p_snap.add_argument("--set", required=True, help="parameter set name to extract")
    p_snap.add_argument("--variant", choices=["gridfinity", "standalone"],
                        help="source scad variant (inferred if omitted)")
    p_snap.add_argument("--output", default="params.json", help="output filename")
    p_snap.add_argument("--force", action="store_true", help="overwrite existing output")
    p_snap.set_defaults(func=cmd_snapshot)

    p_list = sub.add_parser("list", help="show configs and the parts they render")
    p_list.add_argument("configs", nargs="*", help="config dir name(s); default: all")
    p_list.set_defaults(func=cmd_list)

    p_clean = sub.add_parser("clean", help="remove generated STLs and dep caches")
    p_clean.add_argument("configs", nargs="*", help="config dir name(s); default: all")
    p_clean.add_argument("--delete", action="store_true", help="actually delete (default dry run)")
    p_clean.set_defaults(func=cmd_clean)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except BuildError as exc:
        print("error: {}".format(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
