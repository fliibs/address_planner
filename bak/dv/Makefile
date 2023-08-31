.PHONY : comp sim clean verdi
UVM_VERBOSITY = UVM_LOW
DEBUG = -debug_all+pp
TC=base_test
FSDB = novas.fsdb

#-LDFLAGS -no-pie

CMP_OPTS += -lca \
           -kdb \
           -sverilog \
            +v2k \
            $(DEBUG) \
	    -P ~/software/verdi_2016/share/PLI/VCS/linux64/verdi.tab ~/software/verdi_2016/share/PLI/VCS/linux64/pli.a\
	    -cpp g++-4.8  -cc gcc-4.8  -LDFLAGS -Wl,--no-as-needed -CFLAGS -fPIE\
            -ntb_opts uvm-1.2 \
            +vcs+lic+wait \
            -full64\
	    -timescale=1ns/1ps -unit_timescale=1ns/1ps\
            -l compile.log  



comp : 
	vcs $(CMP_OPTS) -f tb.f

sim : 
	./simv +UVM_TESTNAME=${TC}  -l ${TC}.log

run :comp sim


clean	:
		rm -rf *.log simv *.daidir csrc *.key DVEfiles *.fsdb vc_hdrs.h verdiLog novas.*

