# Intranet v3p0 runtime setup

Address Planner and U-HDL must be deployed as two complete, independent project
roots:

```text
ADDRESS_PLANNER_ROOT/
  address_planner/__init__.py
  address_planner/_runtime.py

UHDL_ROOT/
  uhdl/__init__.py
```

Do not set `UHDL_ROOT` to `address_planner/address_planner/uhdl` or to the inner
`uhdl` package directory. The nested checkout is a legacy snapshot and the
runtime intentionally rejects it.

## Direct csh use without registering an addr_planner module

Replace the two example roots with the corresponding canonical intranet paths:

```csh
module load python3/3.11
module load uhdl/20251222

setenv ADDRESS_PLANNER_ROOT /canonical/address_planner/project/root
setenv UHDL_ROOT /canonical/uhdl/project/root

if ($?PYTHONPATH) then
    setenv PYTHONPATH "${ADDRESS_PLANNER_ROOT}:${UHDL_ROOT}:${PYTHONPATH}"
else
    setenv PYTHONPATH "${ADDRESS_PLANNER_ROOT}:${UHDL_ROOT}"
endif

test -f ${ADDRESS_PLANNER_ROOT}/address_planner/__init__.py
test -f ${ADDRESS_PLANNER_ROOT}/address_planner/_runtime.py
test -f ${UHDL_ROOT}/uhdl/__init__.py
python3 -c 'import address_planner,uhdl; print(address_planner.__file__); print(uhdl.__file__)'
python3 cmn_reg_addrmap.py
```

If the loaded U-HDL module already sets the correct `UHDL_ROOT`, do not override
it. Verify it with:

```csh
echo $UHDL_ROOT
ls ${UHDL_ROOT}/uhdl/__init__.py
```

## Module installation

Use `config/modulefiles/addr_planner/v3p0.in` as the template. Replace:

- `@ADDRESS_PLANNER_ROOT@` with the outer Address Planner project root;
- `@UHDL_MODULE@` with an exact existing lowercase module such as
  `uhdl/20251222`.

The installed modulefile must not load uppercase `UHDL`, point `UHDL_ROOT` at
the nested legacy snapshot, or repeat `module use /tools/modules-4.0` when that
path is already present in `MODULEPATH`.

After installation, validate in a clean csh:

```csh
module purge
module load addr_planner/v3p0
python3 -c 'import address_planner,uhdl; print(address_planner.__file__); print(uhdl.__file__)'
python3 cmn_reg_addrmap.py
```
