class yuu_apb_base_case extends uvm_test;
  virtual yuu_apb_interface vif;

  yuu_apb_env env;
  yuu_apb_env_config cfg;
  yuu_apb_virtual_sequencer vsequencer;
  ral_block_reg_bank_tables model;
  
  `uvm_component_utils(yuu_apb_base_case)

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  function void build_phase(uvm_phase phase);
    cfg = new("cfg");
    cfg.events = new("events");
    uvm_config_db #(virtual yuu_apb_interface)::get(null, get_full_name(), "vif", vif);
  
    cfg.apb_if = vif;
    begin
      yuu_apb_master_config m_cfg = new("e0_m0");
      m_cfg.apb3_enable = 1;
      m_cfg.apb4_enable = 1;
      m_cfg.idle_enable = 1;
      m_cfg.coverage_enable = 0;
      m_cfg.index = 0;
      cfg.set_config(m_cfg);
    end
    uvm_config_db #(yuu_apb_env_config)::set(this, "env", "cfg", cfg);
    env = yuu_apb_env::type_id::create("env", this);
  endfunction : build_phase

  function void connect_phase(uvm_phase phase);
    if (cfg.mst_cfg[0].use_reg_model) begin
      model = ral_block_reg_bank_tables::type_id::create("model");
      model.build();
      model.lock_model();
      model.reset();
      model.default_map.set_sequencer(env.vsequencer.master_sequencer[0], env.master[0].adapter);
      env.master[0].predictor.map = model.default_map;
    end
    vsequencer = env.vsequencer;
  endfunction
  
endclass


`include "yuu_apb_ral_case.sv"
