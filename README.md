# address_planner

[![codecov](https://codecov.io/gh/fliibs/address_planner/branch/main/graph/badge.svg?token=PKHFK2PDPL)](https://codecov.io/gh/fliibs/address_planner) [![test](https://github.com/fliibs/address_planner/workflows/Coverage/badge.svg)](https://github.com/fliibs/address_planner/actions/workflows/coverage.yml)



Address planner is a tool used to plan the allocation of all register and memory addresses in a chip.


[Userguide](https://github.com/fliibs/address_planner/wiki/User-Guide-1)
 Here

## New feature

### Add Write1Pulse and Write0Pulse field

change these two fields from external field to interanl field

```python
# WriteOnePulse
sw_access=Write1Pulse, hw_access=ReadOnly

# WriteZeroPulse
sw_access=Write0Pulse, hw_access=ReadOnly
```
 

## Quick Start

### 0. Run with excel

excel template is in excel folder
```shell
regbuilder -h
regbuilder -demo
regbuilder -e <excel_path> -o <output_path>
```

### 1. Install RegBuilder
```python
git clone https://github.com/fliibs/address_planner.git
git submodule update --init --recursive


```
### 2. Create a regbank

```python
1. create a python file

    touch <my_path>/<my_file_name>.py
    
2. add head in python file

    import os,sys 
    sys.path.append(os.getcwd())
    from address_planner import *
    
3. add regbank like filling in the form 
(reference example in ./example/demo_addrspace.py) 
    
```

### 3. Run python file and generate rtl
```python
1. run python file in the main directory (root of address planner project)
    python <path-to-file>/<my_file_name>.py

2. get the result
(output is in ./build directory)
```

### 4. Generate the offline SQLite viewer

The normal generation path uses the versioned Viewer template shipped with the
Python package:

```python
top.generate("build/example")
```

The generated database uses schema v2 by default. It keeps the logical
occurrence tree (including each instance's already-computed absolute address)
separate from a content-addressed template DAG, and reuses identical Node
definitions, Field definitions and strings. The Viewer supports both v2 and the
legacy v1 layout through an internal adapter, so UI code and expansion behavior
do not depend on the physical schema.

Callers that still need a v1 database can request it explicitly during the
migration:

```python
from address_planner.sqlite_report import SCHEMA_VERSION_V1

top.report_sqlite(
    "build/example/legacy_address_map.sqlite",
    schema_version=SCHEMA_VERSION_V1,
)

# The generate() convenience API exposes the same choice under this name:
top.generate(
    "build/example-v1",
    sqlite_schema_version=SCHEMA_VERSION_V1,
)
```

`report_sqlite()` returns a `SQLiteReportInfo`; for v2,
`report_info.reuse_statistics` exposes the logical-to-physical Node, Field and
text reuse counters measured while writing the report.

The browser Viewer source is pinned as the build-time `viewer/apv_html`
submodule. Normal report generation does not require Node.js or an initialized
Viewer submodule because the validated template is vendored with Address
Planner. Maintainers updating Viewer code must rebuild, test and vendor the
self-contained template:

```shell
git submodule update --init --recursive
cd viewer/apv_html
npm ci
npm test
npm run build
npm run validate:template
cd ../..
python tools/sync_viewer_template.py
python tools/sync_viewer_template.py --check
```

`viewer-template.lock.json` records the exact Viewer commit, template hash and
supported container/schema versions (currently v1 and v2). CI rebuilds the
submodule and rejects a vendored template or lock file that has drifted from
that commit. Update Viewer source in the `apv_html` repository first, commit it,
advance the `viewer/apv_html` submodule gitlink, and then run the sync commands
above so the vendored template and lock stay reproducible.

An alternate development template can also be supplied explicitly:

```python
top.generate(
    "build/example",
    viewer_template_path="viewer/apv_html/dist/address-planner-viewer.template.html",
)
```

The generated report is a single offline file:

```text
build/example/<model>/html/<model>_address_map.html
```

It can be opened directly with `file://`. SQLite, SQLite WASM, the query Worker,
JavaScript, CSS and the compressed report database are all embedded; no server
or network request is required. The viewer queries roots first, direct children
when an AddressSpace is expanded, and Fields only when a Register is selected.
Its compact header reports the exact Node and Field totals plus the uncompressed
SQLite database size recorded in the embedded manifest.
Before the report is ready, the same header shows placeholders and a theme-aware
loading panel reports real Base64/decompression byte progress where measurable,
then names the hash, SQLite, integrity and root-query stages without inventing a
percentage. Its ten-row startup sequence keeps completed steps visible, marks
the current task, dims pending work and clips all motion inside the active track.
Append `?loadingDemo=1` to replay those captured stages slowly for visual review;
`?loadingDemo=1200` sets a 1200 ms step. Normal URLs add no delay.

The title bar also provides a compact theme button that switches between palettes
inspired by the classic VS Code Light+ and Dark+ themes. Light mode pairs a white
editor/table surface with a light-gray workbench; dark mode uses the familiar
`#1e1e1e` editor and `#252526` workbench surfaces. Both use `#007acc` blue for
primary interaction and selection cues, and cover the pre-React static loading
shell, the mounted React UI, Ant Design portal content, tables and scrollbars
rather than recoloring only the main canvas. The selected theme is persisted
through guarded `localStorage` access when the browser allows it and is restored
synchronously before React mounts, avoiding a light flash in dark mode while
remaining safe for direct `file://` use. Theme switching changes colors only;
panel geometry, column widths and all table drag, collapse, wrap and selection
interactions remain unchanged.

The Bank/Reg divider keeps either visible panel at least 160 px wide. Reaching
that limit only clamps the panel; the pointer must travel another 80 px toward
the edge before the panel snaps fully closed, making accidental collapse less
likely. Default fixed column widths reserve most of the budget for Description,
while compact address, size, position and access columns remain readable. A
column can still be narrowed to 32 px. Description is the fluid final column:
its rendered width is always the table width minus the fixed columns before it.
In the default single-line mode, the table expands to the longest Description
currently loaded, so the docked horizontal scrollbar reaches the complete text.
Each panel also has an independent wrap button beside its column-visibility eye;
wrapping keeps Description in the remaining width and lets virtual rows grow to
their measured content height. Other narrow cells continue to clip directly,
without ellipses, wrapping or overlap.

During migration, `data.json` is still generated for compatibility and semantic
comparison. The schema v2 Viewer projection intentionally omits
`node_attributes`, because none of those values are displayed. See
[the architecture document](doc/single_html_sqlite_viewer_architecture.md) for
the schema, memory model, migration plan and validation requirements.

###Architecture of regbank

```text

    AddressSpace (contain many regbanks)
    |
    ---regspace 0 (regbank contain many fields)
    |   |
    |   ---register 0
    |   |    |
    |   |    ---field 0 
    |   |    |
    |   |    ---field 1
    |   |    |
    |   |    ---field 2
    |   |
    |   ---end (end of register 0)
    |   |
    |   ---register 1
    |   |    |
    |   |    ---field 0 
    |   |    |
    |   |    ---field 1
    |   |    |
    |   |    ---field 2
    |   |
    |   ---end
    |
    ---end (end of regspace 0)
    |
    ---RegSpace 1
    |   |
    |   ---register 0
    |    .
    |    .
    |    .
    ---end
    |
    generate (generate rtl file)

Parameter:

1. AddressSpace
    name: name of AddressSpace
    size: boundry of regbanks(Byte)

2. regSpace:
    name:               name of regbank and also the rtl file name
    size:               boundry of a regbank(Byte)
    description
    software_interface: "vr" for valid ready interface and "apb" for apb interface

3. register:
    name:        name of register and a part of interface name of its field
    bit:         size of register
    description
    
4. field:
    name:           name of field and a part of interface name of field
    bit:            size of field
    sw_access:      software access type (default: ReadWrite)
    hw_access:      hardware access type (default: ReadWrite)
    description
    offset    

Access type for sw_access and hw_access:
```
![Access_type](https://github.com/fliibs/address_planner/assets/66581448/514aff41-6353-4409-8156-818d686e1b97)
