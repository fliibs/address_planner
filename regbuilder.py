import os 
import sys
import argparse
from subprocess import Popen
sys.path.append('/home/liuyunqi/huangtao/address_planner')
from excel.ex2py import CreatPy

def main():
    parser = argparse.ArgumentParser(description='RegBuilder Scope! ')
    parser.add_argument('-e', type=str, help='input excel file')
    parser.add_argument('-o', type=str, help='output path', default='build')
    parser.add_argument('-demo', action='store_true', help='generate an excel tamplate')

    args = parser.parse_args()

    print("Regbuilder Start")

    if args.demo:
        print("gen an excel tamplate")
        return
    
    if args.e == None: raise Exception("Input file not exist!") # simplify way

    print("[ ExcelParser ] Load input file: %s"% args.e)
    prs_out =  CreatPy(args.e, args.o)
    if prs_out == '': raise Exception("[ Generate Fail ] Fail to parse excel file, prs_out is empty")
    print("[ Regbuilder ] Start parse python file %s"% prs_out)

    cmd_exc = f'python3 {prs_out}'
    os.environ['PYTHONPATH'] = '$PYTHONPATH:/home/liuyunqi/huangtao/address_planner'
    os.system(cmd_exc)
    print("[ Generate Success ]")



main()