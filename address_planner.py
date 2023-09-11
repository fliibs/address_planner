# import sys,os
# from subprocess import Popen


# if len(sys.argv)>=2:    input_path = sys.argv[1]
# else:   raise Exception("Input path not exist!")
# if len(sys.argv)>=3:    output_path = sys.argv[2]
# else:   output_path = ''   

# command_ex2py = f'python3 excel/ex2py.py {input_path} {output_path}'
# pipe = Popen(command_ex2py, shell=True)
# pipe.communicate()




import json

try:
    json_file = open("build/reg_bank_table/reg_bank_table/html/data.json", 'r')
    json.load(json_file)
    print("[Check Json] Json file correct")
except:
    raise Exception("[Check Json] Error in Json file")