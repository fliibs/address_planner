# Release Notes

## Unreleased — intranet RALF compatibility

- Standard `0x` and `0b` address prefixes are parsed before legacy `h`/`b`
  radix markers, preventing values such as `@0xfb4` and `@0xb10` from being
  misclassified as binary.
- RALF numeric and Tcl failures now report the input file. Numeric failures also
  include the raw value, Tcl hierarchy and candidate source line numbers.
- Undefined field instances named `reserved` are ignored case-insensitively;
  defined `reserved` fields and other undefined field names retain the normal
  parser behavior.
- `AddressSpace.add_ralf()` accepts both the current `ralf_file=` keyword and the
  intranet-v3p0 `sub_space=` keyword. Positional calls remain supported.
- An intranet modulefile template and csh direct-run instructions document the
  required Address Planner and independent U-HDL project roots.

## v1.2.2 — APV integration

- `apv_html` is now integrated as a pinned build-time submodule. Calling
  `top.generate("build/example")` generates one self-contained offline report at
  `build/example/<model>/html/<model>_address_map.html`; normal generation does
  not require Node.js or an initialized submodule.
- The new APV embeds a compressed SQLite schema v2, reuses repeated Node, Field
  and text definitions, and queries children or Fields only when they are
  opened. It also adds loading progress, resizable tables, Description wrapping
  and persistent light/dark themes.

APB/APB4 RTL behavior is unchanged in this release.
