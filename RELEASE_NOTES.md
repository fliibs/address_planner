# Release Notes

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
