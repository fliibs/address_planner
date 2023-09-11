#!/bin/shell
#!/usr/bin/python3

echo "[ ExcelParser ] Start parse excel file"

echo "[Input] Parse excel file: $1"
prs_out=$(python excel/ex2py.py $1 $2)
echo "[Generate Python] Generate python file: $prs_out"

if [ -z "$prs_out" ]; then
    echo "[ Generate Fail ] Fail to parse excel file, prs_out is empty"
else
    echo "[ Regbuilder ] Start parse python file: $prs_out"
    python $prs_out
    echo "[ Generate Success ]"
fi  