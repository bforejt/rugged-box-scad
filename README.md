# rugged-box-scad

Parametric, customizable rugged storage box for OpenSCAD, with a
Gridfinity-compatible variant. Forked from
[smkent/monoscad](https://github.com/smkent/monoscad) to add
non-standard Gridfinity cell sizes and stand-on-back feet.

## Project status

This is a **shared personal project** and is **work in progress**. It
is not exhaustively tested — only a small number of parameter
combinations have been exported to STL and test-printed (those that
have, have printed successfully). Many permutations of the parametric
options have never been generated, sliced, or printed.

**Caution before printing.** This fork modifies the original
`smkent/monoscad` source (see [CHANGES.md](CHANGES.md)) and bumps the
[`kennetek/gridfinity-rebuilt-openscad`](https://github.com/kennetek/gridfinity-rebuilt-openscad)
library to a newer API than upstream monoscad targets. If you customize
the box for your own use case, render it carefully and inspect the
geometry before committing filament to it.

**Testing environment.** Rendering and validation is done on Apple
silicon (macOS) with OpenSCAD **2026.06.06 (git 49366181)**. Going
forward, the latest OpenSCAD on macOS will be the primary testing
environment used by the author. Other operating systems, processor
architectures, or older OpenSCAD versions may work fine — or may not
— but they aren't actively tested.

**Reporting issues — please include repeatability details.** Issue
reports are very welcome! To help investigate effectively, please
include enough detail to reproduce what you saw. At a minimum:

- **Customizer settings used** — a screenshot of the customizer
  panel, the saved parameter-set JSON, or just a list of which values
  you changed from the file defaults
- **OpenSCAD version** — Help → About inside the app (include the
  build / git hash if shown)
- **Operating system and architecture** — e.g. "Ubuntu 24.04 on
  x86_64" or "Windows 11 on ARM"
- **What you observed** — short summary of the problem (preview
  rendered differently than expected? slicer rejected the STL? a
  printed part didn't fit?)
- **Helpful extras** — the rendered STL, a screenshot of the
  OpenSCAD preview, or the slicer's error pane all speed things up

The more reproducible the report, the faster it can be looked into.
PRs are also welcome.

## Examples

Tested, printed parameter combinations live in [`examples/`](examples/),
one subdirectory per configuration with the exported STLs alongside.
Today this is one configuration —
[`examples/43mm_gridfinity_4x3`](examples/43mm_gridfinity_4x3/) — and
the list will grow as more variants are validated. Use these as
starting points if you want a known-good configuration rather than
generating from the SCAD yourself.

Two top-level designs in [`src/`](src/):

- [`rugged-box.scad`](src/rugged-box.scad) — standalone parametric box
- [`rugged-box-gridfinity.scad`](src/rugged-box-gridfinity.scad) —
  Gridfinity-compatible variant; bottom is a Gridfinity baseplate, top
  optionally exposes Gridfinity stacking lips
- [`rugged-box-library.scad`](src/rugged-box-library.scad) — shared
  library implementing both

### Compatible Gridfinity bins

The author's primary use case for the Gridfinity variant is filling
the box with bins generated from
[ostat/gridfinity_extended_openscad](https://github.com/ostat/gridfinity_extended_openscad).
In test prints those bins have mated correctly with the box's bottom
baseplate and (when enabled) the lid's stacking-lip surface — so if
you want a known-good source for bins to drop in, that's the
companion project that's been tried here.

## Setup

```sh
git clone --recurse-submodules https://github.com/<you>/rugged-box-scad.git
# or, if already cloned without --recurse-submodules:
git submodule update --init --recursive
```

Use a recent OpenSCAD — the latest release or development snapshot is
what the author tests against (see *Testing environment* above for the
exact build). Open any `.scad` file in [`src/`](src/) directly —
relative `use`/`include` paths resolve to the submodule under
[`lib/`](lib/), so no `OPENSCADPATH` setup is needed.

## License & attribution

This project is a derivative work of two upstream projects with
different licenses. The combined work is distributed under
**CC BY-SA 4.0** ([LICENSE](LICENSE)), as required by the upstream
rugged-box code.

| Source | License | Pinned commit |
| --- | --- | --- |
| [smkent/monoscad](https://github.com/smkent/monoscad) (rugged-box and gridfinity/rugged-box subdirs) | CC BY-SA 4.0 | [`a980c0e`](https://github.com/smkent/monoscad/commit/a980c0e4a83d43316286d994b0bda67a6889529a) |
| [kennetek/gridfinity-rebuilt-openscad](https://github.com/kennetek/gridfinity-rebuilt-openscad) (submodule at [`lib/gridfinity-rebuilt-openscad`](lib/gridfinity-rebuilt-openscad)) | MIT — see [LICENSES/MIT-gridfinity-rebuilt.txt](LICENSES/MIT-gridfinity-rebuilt.txt) | [`910e22d`](https://github.com/kennetek/gridfinity-rebuilt-openscad/commit/910e22d8607fd7f5f51ad5e5cbc5287a76810bfd) |

The MIT submodule is one-way compatible into CC BY-SA 4.0; the same
arrangement is used by the upstream monoscad repo.

Original rugged-box design by Stephen Kent (smkent / bulbasaur0 on
Printables). Gridfinity-rebuilt library by Kenneth Hodson (kennetek),
based on the original Gridfinity system by Zack Freedman.

## A note on slicer warnings (cosmetic)

Slicers (PrusaSlicer, OrcaSlicer, etc.) will report **hundreds of
"errors" or "facets fixed"** when loading the exported STLs. These are
**cosmetic** and do not affect the printed result.

Two patterns produce the count:

1. **Boolean tessellation noise** — OpenSCAD's CGAL/Manifold engines
   emit a small number of zero-area (degenerate) triangles wherever
   boolean operations create coincident vertices. Every part exported
   from this project shows roughly 400 of these as a baseline; the
   exact count varies with geometry.
2. **Coplanar surface duplicates** — when two unioned solids have
   faces sitting exactly on the same plane (rather than overlapping by
   a small epsilon), the surface gets tessellated twice. This shows up
   as a handful of duplicate facets, usually on lid-mating or
   seal-groove regions.

The exported meshes are **manifold and closed** (no open edges, no
non-manifold edges) — only the degenerate/duplicate facets show up,
which every slicer auto-removes silently before slicing. The error
count is the slicer telling you what it cleaned up, not a problem with
the model.

If the count bothers you, use the slicer's built-in repair (PrusaSlicer:
right-click → *Fix through Netfabb*) to write a clean STL.

## Modifications

This is a derivative work. All modifications relative to the upstream
sources are recorded in [CHANGES.md](CHANGES.md). Entries that may be
worth contributing back to upstream are tagged `[upstream-candidate]`.

Copyright © 2026 Brian Forejt, in addition to the original copyrights
of the upstream authors.
