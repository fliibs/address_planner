import os 
import sys
import argparse
import shutil
import copy

root_path, _ = os.path.split(os.path.realpath(__file__))
dv_env = 'dv_env'
dv_setup = 'setup_dv.sh'
dv_tool_path = os.path.join(root_path, dv_env)
demo_path    = os.path.join(root_path, 'excel/excel_demo/regbank_demo.xlsx')

sys.path.append(root_path)
from excel.ex2py import CreatPy


def main():
    parser = argparse.ArgumentParser(description='RegBuilder Scope! ')
    parser.add_argument('-e', type=str, help='input excel file')
    parser.add_argument('-o', type=str, help='output path', default='build')
    parser.add_argument('-demo', action='store_true', help='generate an excel tamplate')

    args = parser.parse_args()

    if args.demo:
        print("generate an excel tamplate: ./regbank_demo.xlsx")
        shutil.copyfile(demo_path, './regbank_demo.xlsx')
        return

    print("Regbuilder Start")

    prs_out = task_parse_excel(args)
    task_regbuilder(args, prs_out[0])
    # task_dv_setup(args, prs_out[1])

    print("[ Generate Success ]")




def task_parse_excel(args, others=None):
    
    if args.e == None: raise Exception("Input file not exist!") # simplify way

    print("[ ExcelParser ] Load input file: %s"% os.path.abspath(args.e))
    prs_out, rs_name =  CreatPy(args.e, args.o)
    if prs_out == '': raise Exception("[ Generate Fail ] Fail to parse excel file, prs_out is empty")
    print("[ ExcelParser ] Successfull parse file: %s"% args.e)

    return [prs_out, rs_name]


def task_regbuilder(args, others=None):

    print("[ Regbuilder ] Start parse python file %s"% others)
    cmd_exc = f'python3 {others}'
    os.environ['PYTHONPATH'] = f'$PYTHONPATH:{root_path}'
    os.system(cmd_exc)

    return None


def task_dv_setup(args, others=None):

    dv_path = os.path.abspath(f'{args.o}/{others}/dv')
    dst_path = os.path.join(dv_path, dv_env)
    print("[ Generate DV ] output path: %s"% dv_path)
    if os.path.exists(dst_path): shutil.rmtree(dst_path)
    shutil.copytree(f'{dv_tool_path}', dst_path)

    dv_setup_path = os.path.join(dst_path, dv_setup)
    if not os.path.exists(dv_setup_path): shutil.move(dv_setup_path, dv_path)
    

    return None




if __name__=="__main__":
    main()