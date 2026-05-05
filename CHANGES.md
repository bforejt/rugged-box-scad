# Changes

Modifications to the upstream sources in this repo. Entries tagged
`[upstream-candidate]` describe changes that could plausibly be
contributed back to monoscad as a PR.

## Baselines

- **monoscad**: [smkent/monoscad@a980c0e](https://github.com/smkent/monoscad/commit/a980c0e4a83d43316286d994b0bda67a6889529a)
  (main as of 2026-05-03), specifically:
  - `rugged-box/rugged-box.scad`
  - `rugged-box/rugged-box-library.scad` (identical to
    `gridfinity/rugged-box/rugged-box-library.scad`; one copy retained)
  - `gridfinity/rugged-box/rugged-box-gridfinity.scad`
- **gridfinity-rebuilt-openscad**: [kennetek/gridfinity-rebuilt-openscad@910e22d](https://github.com/kennetek/gridfinity-rebuilt-openscad/commit/910e22d8607fd7f5f51ad5e5cbc5287a76810bfd)
  (2025-08-31). Initial import was pinned at `0b7bf6e` (2024-01-29)
  to match Stephen's original tested API; bumped to `910e22d` on
  2026-05-03 — see migration entry below.

## 2026-05-03 — Initial import

- Imported the three rugged-box sources listed above into `src/`.
- Submoduled `lib/gridfinity-rebuilt-openscad` at the pin above.
- Adjusted `include`/`use` paths in `src/rugged-box-gridfinity.scad`
  to reference `../lib/gridfinity-rebuilt-openscad/` (Stephen's
  originals assumed the library was at `OPENSCADPATH` or in a sibling
  `gridfinity-rebuilt-openscad/` directory).

### `[upstream-candidate]` Add `Stand_On_Back` parameter and stand-feet module

Adds an optional pair of feet at the bottom-back of the box bottom,
matching the hinge protrusion, so the closed box can stand upright on
its back edge.

- `src/rugged-box-library.scad` — new `stand_on_back` arg on the `rbox`
  module, plumbed through to a new `_box_stand_feet` module which uses
  a new `_box_stand_foot_body` helper. Wired into both `assembled_open`
  and `assembled_closed` previews.
- `src/rugged-box.scad` — `Stand_On_Back` customizer parameter passed
  to `rbox`.
- `src/rugged-box-gridfinity.scad` — same wiring on the Gridfinity
  variant.

### `[upstream-candidate]` Parameterize Gridfinity cell size

Adds a `Cell_Size` customizer parameter to the Gridfinity rugged-box
(default 42 mm, range 30–50 mm in 0.5 mm steps), replacing the
hardcoded `l_grid` constant from gridfinity-rebuilt-openscad. Allows
non-standard Gridfinity grids (e.g., metric-imperial hybrids,
shrunk/expanded layouts).

- `src/rugged-box-gridfinity.scad` — `Cell_Size` parameter; all
  `l_grid` references in dimension calculations, rib positioning,
  baseplate generation, and stacking-lip generation rebound to
  `Cell_Size`.

## 2026-05-05 — `[upstream-candidate]` End-stop bar follows stand-foot contour

When `Stand_On_Back=true` and `Hinge_End_Stops=true` are both enabled,
the end-stop bar between the hinges grows a foot-shaped protrusion at
its bottom so its contour matches the corner stand feet on either
side. The corner feet themselves are unchanged (still aligned with the
hinge ribs above). The result reads as one continuous arch across the
back wall: feet at the corners, end-stop in the middle, all merging
into a single wide protrusion at low Z, while the end-stop bar stays
narrow at higher Z. When `Stand_On_Back=false`, the end-stop bar is
exactly the existing geometry.

- `src/rugged-box-library.scad` — `_box_hinge_rib_bottom_end_stop`
  conditionally emits an additional `_box_stand_foot_body(width=width)`
  inside its rotated frame when `$b_stand_on_back` is true. Net diff
  from main: 7 lines added.

## 2026-05-03 — `[upstream-candidate]` Migrate to current kennetek API

Bumped the `lib/gridfinity-rebuilt-openscad` submodule from `0b7bf6e`
(Jan 2024) to `910e22d` (Aug 2025), and updated
`src/rugged-box-gridfinity.scad` to match the refactored kennetek API.

**Imports** — added direct imports for the relocated symbols:
- `include` of `standard.scad` now from `src/core/`
- new `use` of `src/core/base.scad` (was in `gridfinity-rebuilt-utility.scad`)
- new `use` of `src/core/gridfinity-rebuilt-holes.scad` for `bundle_hole_options`
- new `use` of `src/helpers/shapes.scad` for `rounded_square`

**Renamed constants:**
- `h_lip` → `STACKING_LIP_HEIGHT` (3.548 → 4.4 mm)
- `h_base` → `BASE_HEIGHT` (5 → 7 mm)
- `h_hole` → `MAGNET_HOLE_DEPTH` (2.4 mm, unchanged value)
- `r_base` → `BASE_TOP_RADIUS` (4 → 3.75 mm)

The base/lip dimension drift means the rendered Z-geometry of the
Gridfinity bottom and the lid's mating top base differ slightly from
the previous version. Both halves consistently use the new constants,
so they remain self-compatible.

**Function signatures:**
- `gridfinityBaseplate(W, L, l, dx, dy, sp, magnets, sh, fitx, fity)`
  → `gridfinityBaseplate([W, L], l, [dx, dy], sp, hole_options, sh, [fitx, fity])`
  with `magnets` boolean replaced by a `bundle_hole_options(...)` bundle.
- `gridfinityBase(gx, gy, l, dx, dy, style_hole, off=, …)`
  → `gridfinityBase([gx, gy], [l, l], hole_options, …)`. The `off`
  parameter is gone; replaced with a uniform XY `scale()` wrapper that
  reproduces the inset (`-0.2mm` at the one callsite that needs it).

**Module replacement:**
- `rounded_rectangle(w, l, h, r)` → `linear_extrude(h) rounded_square([w, l], r, center=true)`.

**New helper:**
- `gridfinity_hole_options()` — local function that produces the
  `bundle_hole_options(...)` bundle, factoring out shared options
  (`crush_ribs=true`, `chamfer=true`) so both call sites stay in sync.

**Verification:** every `Part` value (12 total) renders cleanly with no
OpenSCAD errors or warnings, across all four `Gridfinity_Base_Style`
options, with `Gridfinity_Stackable` on/off, with `Stand_On_Back`
on/off, and at non-standard `Cell_Size` values (30, 38, 50). Print fit
of the new stacking-lip / top-base interface has not yet been
physically verified.

## Future work

- **Print-fit verification of the migrated lid/base interface.**
  The lid's top base uses a `scale()` workaround in place of the old
  `gridfinityBase(off=-0.2)` 0.2 mm fit-tolerance inset. Behaviorally
  equivalent in CSG, but worth a printed test before declaring final.
- **Optionally expose `bundle_hole_options(...)` flags as customizer
  parameters** (refined holes, screw holes, supportless magnet pockets,
  thumbscrew bases). Currently `gridfinity_hole_options()` hardcodes
  `crush_ribs=true, chamfer=true` and disables the rest.
