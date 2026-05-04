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
- **gridfinity-rebuilt-openscad**: [kennetek/gridfinity-rebuilt-openscad@0b7bf6e](https://github.com/kennetek/gridfinity-rebuilt-openscad/commit/0b7bf6ee7897e68b5c308e5926cd2cb507737822)
  (2024-01-29). This matches the kennetek commit smkent vendored in
  monoscad's library bundle — Stephen's gridfinity rugged-box was
  written and tested against this exact API.

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

## Future work

- **`[upstream-candidate]` Migrate to current kennetek API.** The
  Gridfinity variant is pinned to the Jan 2024 kennetek commit because
  later commits (post-Jun 2024) renamed `h_lip` and changed the
  `gridfinityBaseplate`/`gridfinityBase` signatures (positional args
  → 2D vectors, `enable_magnet` flag → `bundle_hole_options(...)`
  bundle). Migration would unlock 18+ months of upstream improvements.
  Affects `gridfinity_baseplate`, `gridfinity_base`, and the helper
  functions `gridfinity_base_plate_style` and
  `gridfinity_base_plate_magnets_enabled` in
  `src/rugged-box-gridfinity.scad`.
