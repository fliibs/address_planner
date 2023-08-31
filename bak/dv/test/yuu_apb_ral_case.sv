/////////////////////////////////////////////////////////////////////////////////////
// Copyright 2019 seabeam@yahoo.com - Licensed under the Apache License, Version 2.0
// For more information, see LICENCE in the main folder
/////////////////////////////////////////////////////////////////////////////////////
`ifndef YUU_APB_RAL_CASE_SV
`define YUU_APB_RAL_CASE_SV

class yuu_master_ral_virtual_sequence extends yuu_apb_virtual_sequence;
   ral_block_reg_bank_tables model;

  `uvm_object_utils(yuu_master_ral_virtual_sequence)

  function new(string name="yuu_master_ral_virtual_sequence");
    super.new(name);
  endfunction : new

  task body();
    fork
      begin
        uvm_status_e    status;
        uvm_reg_data_t  value;

        #5000ns;

        model.internal_reg.write(status, 32'hffffffff);
        model.external_reg.write(status, 32'hffffffff);
        #1000ns;
        model.internal_reg.read(status, value);
        `uvm_info("body", $sformatf("internal reg read value is %8h", value), UVM_LOW);
        model.external_reg.read(status, value);
        `uvm_info("body", $sformatf("external reg read value is %8h", value), UVM_LOW);
      end
    join
  endtask
endclass : yuu_master_ral_virtual_sequence


class sanity_test extends yuu_apb_base_case;
  `uvm_component_utils(sanity_test)

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction : new

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    cfg.mst_cfg[0].idle_enable = 0;
    cfg.mst_cfg[0].use_reg_model = 1;
  endfunction : build_phase

  task run_phase(uvm_phase phase);
    yuu_master_ral_virtual_sequence seq;
    seq = yuu_master_ral_virtual_sequence::type_id::create("seq");
    seq.model = model;
    phase.raise_objection(this);
    seq.start(vsequencer);
    phase.drop_objection(this);
  endtask : run_phase
endclass : sanity_test

`endif
