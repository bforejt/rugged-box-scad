# rugged-box-scad

Parametric, customizable rugged storage box for OpenSCAD, with a
Gridfinity-compatible variant. Forked from
[smkent/monoscad](https://github.com/smkent/monoscad) to add
non-standard Gridfinity cell sizes and stand-on-back feet.

Two top-level designs in [`src/`](src/):

- [`rugged-box.scad`](src/rugged-box.scad) — standalone parametric box
- [`rugged-box-gridfinity.scad`](src/rugged-box-gridfinity.scad) —
  Gridfinity-compatible variant; bottom is a Gridfinity baseplate, top
  optionally exposes Gridfinity stacking lips
- [`rugged-box-library.scad`](src/rugged-box-library.scad) — shared
  library implementing both

## Setup

```sh
git clone --recurse-submodules https://github.com/<you>/rugged-box-scad.git
# or, if already cloned without --recurse-submodules:
git submodule update --init --recursive
```

OpenSCAD 2021.01 or newer recommended. Open any `.scad` file in
[`src/`](src/) directly — relative `use`/`include` paths resolve to the
submodule under [`lib/`](lib/), so no `OPENSCADPATH` setup is needed.

## License & attribution

This project is a derivative work of two upstream projects with
different licenses. The combined work is distributed under
**CC BY-SA 4.0** ([LICENSE](LICENSE)), as required by the upstream
rugged-box code.

| Source | License | Pinned commit |
| --- | --- | --- |
| [smkent/monoscad](https://github.com/smkent/monoscad) (rugged-box and gridfinity/rugged-box subdirs) | CC BY-SA 4.0 | [`a980c0e`](https://github.com/smkent/monoscad/commit/a980c0e4a83d43316286d994b0bda67a6889529a) |
| [kennetek/gridfinity-rebuilt-openscad](https://github.com/kennetek/gridfinity-rebuilt-openscad) (submodule at [`lib/gridfinity-rebuilt-openscad`](lib/gridfinity-rebuilt-openscad)) | MIT — see [LICENSES/MIT-gridfinity-rebuilt.txt](LICENSES/MIT-gridfinity-rebuilt.txt) | [`0b7bf6e`](https://github.com/kennetek/gridfinity-rebuilt-openscad/commit/0b7bf6ee7897e68b5c308e5926cd2cb507737822) |

The MIT submodule is one-way compatible into CC BY-SA 4.0; the same
arrangement is used by the upstream monoscad repo.

Original rugged-box design by Stephen Kent (smkent / bulbasaur0 on
Printables). Gridfinity-rebuilt library by Kenneth Hodson (kennetek),
based on the original Gridfinity system by Zack Freedman.

## Modifications

This is a derivative work. All modifications relative to the upstream
sources are recorded in [CHANGES.md](CHANGES.md). Entries that may be
worth contributing back to upstream are tagged `[upstream-candidate]`.

Copyright © 2026 Brian Forejt, in addition to the original copyrights
of the upstream authors.
