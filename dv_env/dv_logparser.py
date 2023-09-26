import os
import time 
import re
import argparse
import sys

def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-s',
                        '--simv_log',
                        type=str,
                        help='''input simulation results file
                        ''')
    args=parser.parse_args()
    log_parser(args.simv_log,0)


def log_parser(simv_log,is_reg,common_msg_filter='',module_msg_filter='',tc_msg_filter=''):
    line_no=0
    log_file_existed = 0
    seed='0'
    cur_time=time.strftime("%Y-%m-%d",time.localtime())
    err_key_list=('ERROR','Error','FATAL','Offending','FAIL','fail','Fail','TIMEOUT')
    filter_list1=()
    filter_list2=()
    filter_list3=()
    filter_all=[]
    is_filter=0
    is_pass=0;
    is_fail=0;
    print(simv_log)
    if(os.path.exists(simv_log)):
      with open(simv_log) as f:
           for line in f:
      #  print line
             line.strip('\n') #remove blank
             line.expandtabs() #remove blank
             if(re.search('ntb_random_seed=(\d+)',line)):
                 seed=re.search('ntb_random_seed=(\d+)',line).group(1)
             fail_reason=line
             is_filter=0
             for err_info in err_key_list:
               if(re.search(err_info,line)):#fixme
                  for filter_info in filter_all:
                      filter_info = filter_info.strip()
                      filter_info = filter_info.strip('\n')
                      filter_info = filter_info.expandtabs()
                      filter_tmp_list=filter_info.split('//') 
                      filter_info=filter_tmp_list[0]
                      if(filter_info!=''):
                        if(re.search(filter_info,line)):
                          is_filter=1
                          os.write(msg_fp,str.encode("line_number="+str(line_no)+"     message="+line+"\n"))
                          break #break filter judge
                  if(is_filter==0):
                      is_fail=1;
                      break#break err info judge 
             if(is_fail==1):
                  break #break line read
             if((re.search('simulation passed',line))or(re.search('Simulation_Test_PASSED',line))):
                  is_pass=1;
             if((re.search('UVM Report Summary',line)) or (re.search('UVM Report catcher Summary',line))):
                  break#end parse
             line_no+=1
    else:
         fail_reason = "VCS license issue,Can't get license"
         is_fail = 1
    if(os.path.exists(simv_log)):
         log_f=open(simv_log,'a')
         log_file_existed = 1
    else:
         is_pass=0
         is_fail=1
    if(is_fail==1):
         if(log_file_existed):
            log_f.write('------------------------------------------------------------------------------------------\n')
            log_f.write('                   Simualtion is FAILED caused by :'+fail_reason+'\n')
         if(is_reg==0):
           print ('\033[5;32;47m                                            \033[0m')   
           print ('\033[5;31;47m        FFFFFF     AA       II   LL         \033[0m')        
           print ('\033[5;31;47m        FF        AAAA      II   LL         \033[0m')        
           print ('\033[5;31;47m        FFFFF    AA  AA     II   LL         \033[0m')        
           print ('\033[5;31;47m        FF      AAAAAAAA    II   LL         \033[0m')        
           print ('\033[5;31;47m        FF     AA      AA   II   LL         \033[0m')        
           print ('\033[5;31;47m        FF    AA        AA  II   LLLLLL     \033[0m')    
           print ('\033[5;32;47m                                            \033[0m')   
           print ('\n\tFAIL caused by : '+fail_reason)
    elif(is_pass==1):
         fail_reason=''
         if(log_file_existed):
            log_f.write('------------------------------------------------------------------------------------------\n')
            log_f.write('                   Congratulation  Simulation is PASSED\n')                
         if(is_reg==0):                                            
            print ('\033[1;32;40m                                           \033[0m')   
            print ('\033[1;32;40m        PPPPP      AA        SSSSS   SSSSS \033[0m')   
            print ('\033[1;32;40m        PP  PP    AAAA      SS      SS     \033[0m')        
            print ('\033[1;32;40m        PPPPP    AA  AA     SSSSS   SSSSS  \033[0m')    
            print ('\033[1;32;40m        PP      AAAAAAAA     SSSSS   SSSSS \033[0m')    
            print ('\033[1;32;40m        PP     AA      AA       SS      SS \033[0m')    
            print ('\033[1;32;40m        PP    AA        AA  SSSSS   SSSSS  \033[0m')     
            print ('\033[1;32;40m                                           \033[0m')   
    else:
         fail_reason='No PASS Tag found, and no error found too.'
         if(log_file_existed):
            log_f.write('------------------------------------------------------------------------------------------\n')
            log_f.write('                   Simualtion is FAILED caused by :'+fail_reason+'\n')
         if(is_reg==0):
           print ('\033[5;32;47m                                            \033[0m')   
           print ('\033[5;31;47m        FFFFFF     AA       II   LL         \033[0m')        
           print ('\033[5;31;47m        FF        AAAA      II   LL         \033[0m')        
           print ('\033[5;31;47m        FFFFF    AA  AA     II   LL         \033[0m')        
           print ('\033[5;31;47m        FF      AAAAAAAA    II   LL         \033[0m')        
           print ('\033[5;31;47m        FF     AA      AA   II   LL         \033[0m')        
           print ('\033[5;31;47m        FF    AA        AA  II   LLLLLL     \033[0m')    
           print ('\033[5;32;47m                                            \033[0m')   
           print ('\n\tFAIL caused by : '+fail_reason)
 
    if(os.path.exists(simv_log)):       
       log_f.close()
       if(is_reg==0):
          simv_path=os.getcwd()
          print("simulation log file :  " +simv_path+"/"+simv_log +"\n")
    if(is_fail==1):
       status='FAIL'
    elif(is_pass==1):
       status='PASS'
    else:
       status='FAIL'
    if(status=='PASS'):
         if(is_reg==0):
            print('log_parser, PASS')
         return 1
    else:
         if(is_reg==0):
            print('log_parser, FAIL')
         return 0


if __name__ == "__main__":
    main()
