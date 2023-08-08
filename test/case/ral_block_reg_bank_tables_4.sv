`ifndef RAL_BLOCK_REG_BANK_TABLES_4_SV
`define RAL_BLOCK_REG_BANK_TABLES_4_SV

class uvm_reg_internal_reg extends uvm_reg;

    `uvm_object_utils(uvm_internal_reg)

    rand uvm_reg_field field0;
    rand uvm_reg_field field1;
    rand uvm_reg_field field2;
    function new(string name = "internal_reg");
        super.new(name, ss.bit, UVM_NO_COVERAGE);
    endfunction : new 

    virtual function void build();
        this.field0=uvm_reg_field::type_id::create("field0",,get_full_name());
            this.field0.configure(this, 1, 0, RO, 0, 1'h0, 1, 0, 1);
        this.field1=uvm_reg_field::type_id::create("field1",,get_full_name());
            this.field1.configure(this, 2, 3, WO, 0, 2'h0, 1, 0, 1);
        this.field2=uvm_reg_field::type_id::create("field2",,get_full_name());
            this.field2.configure(this, 1, 5, RW, 0, 1'h0, 1, 0, 1);
        endfunction : build 

endclass : uvm_internal_reg

class uvm_reg_internal_reg_2 extends uvm_reg;

    `uvm_object_utils(uvm_internal_reg_2)

    rand uvm_reg_field field0;
    rand uvm_reg_field field1;
    rand uvm_reg_field field2;
    function new(string name = "internal_reg_2");
        super.new(name, ss.bit, UVM_NO_COVERAGE);
    endfunction : new 

    virtual function void build();
        this.field0=uvm_reg_field::type_id::create("field0",,get_full_name());
            this.field0.configure(this, 1, 0, RO, 0, 1'h0, 1, 0, 1);
        this.field1=uvm_reg_field::type_id::create("field1",,get_full_name());
            this.field1.configure(this, 2, 3, WO, 0, 2'h0, 1, 0, 1);
        this.field2=uvm_reg_field::type_id::create("field2",,get_full_name());
            this.field2.configure(this, 1, 5, RW, 0, 1'h0, 1, 0, 1);
        endfunction : build 

endclass : uvm_internal_reg_2



class ral_block_reg_bank_tables_4 extends uvm_reg_block;

    `uvm_object_untils(ral_block_reg_bank_tables_4)

    rand uvm_reg_internal_reg internal_reg;
    rand uvm_reg_internal_reg_2 internal_reg_2;
    

    function new(string name="ral_block_reg_bank_tables_4");
        super.new(name, build_coverage(UVM_NO_COVERAGE));
    endfunction : new

    virtual function void build();
        this.default_map = create_map("", 2048, 4, UVM_LITTLE_ENDIAN, 0);
        internal_reg = uvm_reg_internal_reg::type_id::create("internal_reg",,get_full_name());
        internal_reg.configure(this, null, "");
        internal_reg.build();
        internal_reg.add_hdl_path_slice("internal_reg",32,32);
        default_map.add_reg(internal_reg,`UVM_REG_INTERNAL_REG)
        internal_reg_2 = uvm_reg_internal_reg_2::type_id::create("internal_reg_2",,get_full_name());
        internal_reg_2.configure(this, null, "");
        internal_reg_2.build();
        internal_reg_2.add_hdl_path_slice("internal_reg_2",96,32);
        default_map.add_reg(internal_reg_2,`UVM_REG_INTERNAL_REG_2)
        endfunction : build 

endclass : ral_block_reg_bank_tables_4

`endif //RAL_BLOCK_REG_BANK_TABLES_4_SV