from openpyxl import load_workbook
from  excel import PyTemp
import re
import os
from pathlib import Path


RegBankMes = {}
RegMap = {}

def ReadExcel(input_path, output_path):
    input_file = Path(input_path).resolve()
    output_dir = Path(output_path).resolve()
    if not input_file.is_file():
        raise FileNotFoundError(f"Excel input does not exist: {input_file}")
    output_dir.mkdir(parents=True, exist_ok=True)
    RegBankMes.clear()
    RegMap.clear()

    workbook = load_workbook(input_file)
    regBank = workbook["REGBANK"]
    row = regBank.max_row
    column = regBank.max_column
    tableLine = -1
    regName = ''
    filedName = ''
    for i in range(row):
        iNum = 1 + i
        if regBank['A' + str(iNum)].value == 'Name':
            RegBankMes['name'] = regBank['B' + str(iNum)].value
        elif regBank['A' + str(iNum)].value == 'Size (in KB)':
            RegBankMes['size'] = regBank['B' + str(iNum)].value
        elif regBank['A' + str(iNum)].value == 'Software Interface':
            RegBankMes['interface'] = str.lower(regBank['B' + str(iNum)].value)
        elif regBank['A' + str(iNum)].value == 'Interface Width':
            RegBankMes['width'] = regBank['B' + str(iNum)].value
        elif regBank['A' + str(iNum)].value == 'Description':
            RegBankMes['description'] = regBank['B' + str(iNum)].value.replace('\n','\\n')
        elif regBank['A' + str(iNum)].value == 'Check':
            RegBankMes['check'] = str(regBank['B' + str(iNum)].value).lower()
        elif regBank['A' + str(iNum)].value == 'RegName':
            tableLine = iNum
        elif iNum > tableLine and tableLine != -1:
            for j in range(column):
                jChar = chr(ord('A') + j)
                cellName = jChar + str(tableLine)
                cellValue = str(regBank[jChar + str(iNum)].value)
                # standardized the form
                if cellValue is not None and cellValue != 'None':
                    cellValue = full2half(cellValue.replace('\\n','\n').replace('\u202c',''))
                else:
                    continue
                if regBank[cellName].value  == 'RegName':
                    regName = cellValue
                    RegMap[regName] = {}
                elif regBank[cellName].value  == 'OffsetAddress':
                    # RegMap[regName]['OffsetAddress'] = int(cellValue,16)   # byte
                    RegMap[regName]['OffsetAddress'] = cellValue   # byte
                elif regBank[cellName].value  == 'RegType':
                    RegMap[regName]['RegType'] = cellValue
                elif regBank[cellName].value  == 'FieldName':
                    if 'Field' not in RegMap[regName]:
                        RegMap[regName]['Field'] = {}
                    filedName = cellValue
                    RegMap[regName]['Field'][filedName] = {}
                elif regBank[cellName].value  == 'Position':
                    End = cellValue[cellValue.index('[')+1:cellValue.index(':')]
                    Start = cellValue[cellValue.index(':')+1:cellValue.index(']')]
                    if 'Field' not in RegMap[regName]:
                        RegMap[regName]['Position'] = cellValue
                        RegMap[regName]['offset'] = Start
                        RegMap[regName]['bit'] = int(End) - int(Start) + 1
                    else:
                        RegMap[regName]['Field'][filedName]['Position'] = cellValue
                        RegMap[regName]['Field'][filedName]['offset'] = Start
                        RegMap[regName]['Field'][filedName]['bit'] = int(End) - int(Start) + 1
                elif regBank[cellName].value  == 'FieldType':
                    RegMap[regName]['Field'][filedName]['FieldType'] = cellValue
                elif regBank[cellName].value  == 'SoftwareAccess':
                    RegMap[regName]['Field'][filedName]['SoftwareAccess'] = cellValue
                elif regBank[cellName].value  == 'HardwareAccess':
                    RegMap[regName]['Field'][filedName]['HardwareAccess'] = cellValue
                elif regBank[cellName].value  == 'DefaultValue':
                    if 'Field' not in RegMap[regName]:
                        RegMap[regName]['initValue'] = []
                    else:
                        RegMap[regName]['Field'][filedName]['initValue'] = []
                    DefaultValueList = cellValue.split(',')
                    for DefaultValue in DefaultValueList:
                        matcher = re.match(r'.*\'(\w)(\w*)',str(DefaultValue))
                        if matcher == None:
                            initValue = cellValue
                        elif matcher.group(1) == 'b':
                            initValue = '0b'+ matcher.group(2)
                        elif matcher.group(1) == 'h':
                            initValue = '0x'+matcher.group(2)
                        elif matcher.group(1) == 'd':
                            initValue = matcher.group(2)
                        if 'Field' not in RegMap[regName]:
                            RegMap[regName]['initValue'].append(initValue)
                        else:
                            RegMap[regName]['Field'][filedName]['initValue'].append(initValue)
                elif regBank[cellName].value  == 'Description':
                    if 'Field' not in RegMap[regName]:
                        RegMap[regName]['Description'] = cellValue
                    else:
                        RegMap[regName]['Field'][filedName]['Description'] = cellValue
                elif regBank[cellName].value  == 'LockDep':
                    if 'Field' not in RegMap[regName]:
                         RegMap[regName]['LockDep'] = cellValue.split(',')
                    else:
                        RegMap[regName]['Field'][filedName]['LockDep'] = cellValue.split(',')
                elif regBank[cellName].value  == 'MagicNumberDep':
                    RegMap[regName]['MagicNumberDep'] = cellValue.split(',')
                elif regBank[cellName].value  == 'MagicValue':
                    RegMap[regName]['MagicValue'] = cellValue
                elif regBank[cellName].value  == 'Parity':
                    if 'Field' not in RegMap[regName]:
                        if 'TRUE' in cellValue.upper():
                            RegMap[regName]['Parity'] = 'True'
                        else:
                            RegMap[regName]['Parity'] = 'False'
                    else:
                        raise Exception('the parity information is incorrectly entered in the field')
                elif regBank[cellName].value  == 'ResetDomain':
                    if 'Field' not in RegMap[regName]:
                        RegMap[regName]['ResetDomain'] = cellValue
                    else:
                        raise Exception('the ResetDomain information is incorrectly entered in the field')

    PrintLog(output_dir / "datalog.txt")
    
def PrintLog(log_path):
    with open(log_path, 'w', encoding='utf-8') as datalog:
        for k,v in RegMap.items():
            print(k,file=datalog)
            print(v,file=datalog)
        for k,v in RegBankMes.items():
            print(k,file=datalog)
            print(v,file=datalog)


def CreatPy(input_path, output_path):
    output_dir = Path(output_path).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    ReadExcel(input_path, output_dir)

    pyCode = PyTemp.Head.replace('{name}',RegBankMes['name']).replace('{size}',str(RegBankMes['size'])).replace('{description}',RegBankMes['description']).replace('{width}',str(RegBankMes['width'])).replace('{interface}',RegBankMes['interface'])
    pyCode = pyCode.replace(
        "import sys\nsys.path.append('.')",
        "import os\nimport sys\nruntime_root = os.environ.get('ADDRESS_PLANNER_ROOT')\n"
        "if runtime_root:\n    sys.path.insert(0, runtime_root)",
    )
    
    for index,regName in enumerate(RegMap):
        
        pyCode += '\n################################'+regName+'#######################################\n'
        RegGenTemp = PyTemp.Reg.replace('{cnt}',str(index)).replace('{name}',regName).replace('{Description}',RegMap[regName].get('Description','')).replace('{RegType}',RegMap[regName]['RegType'])
        if RegMap[regName]['RegType'] == 'Intr' or RegMap[regName]['RegType'] == 'IntrMask':
            RegGenTemp = RegGenTemp.replace('{Register}', 'InterruptRegister')
        else:
            RegGenTemp = RegGenTemp.replace('{Register}', 'Register')

        if 'Parity' in RegMap[regName]:
            RegGenTemp = RegGenTemp.replace('{Parity}',RegMap[regName]['Parity'])
        else:
            RegGenTemp = RegGenTemp.replace('{Parity}','False')

        if 'ResetDomain' in RegMap[regName]:
            RegGenTemp = RegGenTemp.replace('{ResetDomain}',RegMap[regName]['ResetDomain'])
        else:
            RegGenTemp = RegGenTemp.replace(", rst_domain='{ResetDomain}'",'')
        pyCode += RegGenTemp
        
        if RegMap[regName]['RegType'] == 'Normal':
            for fieldName,field in RegMap[regName]['Field'].items():
                RegCfg = PyTemp.RegCfg
                if field['FieldType'] == 'External':
                    RegCfg = RegCfg.replace('{Field}','External')
                else:
                    RegCfg = RegCfg.replace('{Field}','')
                if 'LockDep' not in  field:
                    RegCfg = RegCfg.replace(',lock_list={lockList}','')
                else:
                    lockList = ''
                    for item in field['LockDep']:
                        lockList += '\"' + str(item[:item.find('.')]) + '.' + str(item[item.find('.') + 1 :]) + '\",'
                    RegCfg = RegCfg.replace('{lockList}','[' + lockList[:-1] + ']')
                pyCode += RegCfg.replace('{cnt}',str(index)).replace('{name}',fieldName).replace('{bit}',str(field['bit'])).replace('{SoftwareAccess}',field['SoftwareAccess']).replace('{HardwareAccess}',field.get('HardwareAccess','Null')).replace('{initValue}',str(field['initValue'][0])).replace('{description}',field.get('Description','')).replace('{offset}',str(field['offset']))
                
        elif RegMap[regName]['RegType'] == 'Magic':
            pyCode += PyTemp.MagicRegCfg.replace('{cnt}',str(index)).replace('{MagicValue}',RegMap[regName]['MagicValue']).replace('{initValue}',RegMap[regName]['initValue'][0]).replace('{bit}',str(RegMap[regName]['bit']))
        elif RegMap[regName]['RegType'] == 'Lock':
            for fieldName,field in RegMap[regName]['Field'].items():
                pyCode += PyTemp.LockRefCfg.replace('{cnt}',str(index)).replace('{bit}',str(field['bit'])).replace('{name}',fieldName).replace('{bit}',str(field['bit'])).replace('{description}',field.get('Description','')).replace('{offset}',str(field['offset']))
        elif RegMap[regName]['RegType'] == 'Intr':
            for fieldName,field in RegMap[regName]['Field'].items():
                pyCode += PyTemp.IntrRegCfg.replace('{cnt}',str(index)).replace('{name}',fieldName).replace('{bit}',str(field['bit'])).replace('{initValue}',str(field['initValue'][0])).replace('{enableInitValue}',str(field['initValue'][1])).replace('{description}',field.get('Description','')).replace('{offset}',str(field['offset']))
        elif RegMap[regName]['RegType'] == 'IntrMask':
            for fieldName,field in RegMap[regName]['Field'].items():
                pyCode += PyTemp.IntrMaskRegCfg.replace('{cnt}',str(index)).replace('{name}',fieldName).replace('{bit}',str(field['bit'])).replace('{initValue}',str(field['initValue'][0])).replace('{enableInitValue}',str(field['initValue'][1])).replace('{maskInitValue}',str(field['initValue'][2])).replace('{description}',field.get('Description','')).replace('{offset}',str(field['offset']))
                
        ADD = PyTemp.ADD
        if 'MagicNumberDep' not in RegMap[regName]:
            ADD = ADD.replace(', magic_list={magicList}','')
        else:
            magicList = ''
            for item in RegMap[regName]['MagicNumberDep']:
                magicList += '\"' + str(item) + '\",'
            ADD = ADD.replace('{magicList}','[' + magicList[:-1] + ']')
        if 'LockDep' not in  RegMap[regName]:
            ADD = ADD.replace(', lock_list={lockList}','')
        else:
            LockList = ''
            for item in RegMap[regName]['LockDep']:
                LockList += '\"' + str(item[:item.find('.')]) + '.' + str(item[item.find('.') + 1 :]) + '\",'
            ADD = ADD.replace('{lockList}','[' + LockList[:-1] + ']')
        if RegMap[regName]['RegType'] == 'Intr' or RegMap[regName]['RegType'] == 'IntrMask':
            ADD = ADD.replace('{add}','add_intr')
        else:
            ADD = ADD.replace('{add}','add')
        pyCode += ADD.replace('{cnt}',str(index)).replace('{OffsetAddress}',str(RegMap[regName]['OffsetAddress']))

    generated_output = output_dir / "generated"
    pyCode += PyTemp.Gen.replace('{build}', str(generated_output)).replace('{name}',RegBankMes['name'])
    
    if RegBankMes['check'] == 'true':
        pyCode += PyTemp.Check.replace('{build}', str(generated_output)).replace('{name}',RegBankMes['name'])
        
    filename = RegBankMes['name']+"_rf_gen.py"
    output_file = output_dir / filename
    with open(output_file,'w') as fileWriter:
        fileWriter.write(pyCode)

    return (str(output_file),RegBankMes['name'])

def full2half(full):
    half = ''
    for char in full:
        num = ord(char)
        if num == 0x3000:
            num = 32
        elif 0xFF01 <= num <= 0xFF0E or 0xFF21 <= num <= 0xFF3B or 0xFF41 <= num <= 0xFF5B:
            num -= 0xFEE0
        char = chr(num)
        half += char
    return half
                        
# print(CreatPy())
