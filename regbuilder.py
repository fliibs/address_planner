import os 
import sys
import argparse
import shutil
import json
import subprocess
from pathlib import Path

root_path, _ = os.path.split(os.path.realpath(__file__))
dv_env = 'dv_env'
dv_setup = 'setup_dv.sh'
dv_tool_path = os.path.join(root_path, dv_env)
demo_path    = os.path.join(root_path, 'excel/excel_demo/regbank_demo.xlsx')

sys.path.append(root_path)
from excel.ex2py import CreatPy


def main(argv=None):
    parser = argparse.ArgumentParser(description='RegBuilder Scope! ')
    parser.add_argument('-e', type=str, help='input excel file')
    parser.add_argument('-o', type=str, help='isolated output path', default='build')
    parser.add_argument('-demo', action='store_true', help='generate an excel tamplate')

    args = parser.parse_args(argv)
    output_path = Path(args.o).resolve()
    output_path.mkdir(parents=True, exist_ok=True)

    if args.demo:
        target = output_path / 'regbank_demo.xlsx'
        shutil.copyfile(demo_path, target)
        print(json.dumps({"excel_template": str(target)}, sort_keys=True))
        return 0

    print("Regbuilder Start")

    prs_out = task_parse_excel(args)
    task_regbuilder(args, prs_out[0])
    # task_dv_setup(args, prs_out[1])

    print(json.dumps({"generated_root": str(output_path / "generated"), "script": prs_out[0]}, sort_keys=True))
    return 0





def task_parse_excel(args, others=None):
    
    if args.e == None: raise ValueError("input Excel file is required (-e)")

    print("[ ExcelParser ] Load input file: %s"% os.path.abspath(args.e))
    prs_out, rs_name =  CreatPy(args.e, args.o)
    if prs_out == '': raise Exception("[ Generate Fail ] Fail to parse excel file, prs_out is empty")
    print("[ ExcelParser ] Successfull parse file: %s"% args.e)

    return [prs_out, rs_name]


def task_regbuilder(args, others=None):

    print("[ Regbuilder ] Start parse python file %s"% others)
    environment = os.environ.copy()
    environment.setdefault('ADDRESS_PLANNER_ROOT', root_path)
    completed = subprocess.run(
        [sys.executable, str(Path(others).resolve())],
        cwd=str(Path(args.o).resolve()),
        env=environment,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"generated Excel model exited with status {completed.returncode}")
    return completed.returncode


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
    raise SystemExit(main())
