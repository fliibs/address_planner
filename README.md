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

### 4. Use HTML to view related information

[Nodejs Installation](https://nodejs.org/en/download)

[Detail of React-Create-APP](https://github.com/fliibs/address_planner/tree/main/reactdemo2)

```shell
1. install the latest npm and nodejs (version of nodejs >= 12)
    # check version of npm and nodejs
    npm -v
    nodejs -v
2.  install node_modules and start npm 
    cd reactdemo2
    npm install
    npm start

(Detail in ./reactdemo2/README.md)
```

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
