`ifndef RAL_BLOCK_REG_BANK_TABLES_SV
`define RAL_BLOCK_REG_BANK_TABLES_SV

class uvm_reg_internal_reg extends uvm_reg;

    `uvm_object_utils(uvm_internal_reg)

    rand uvm_reg_field field0;
    rand uvm_reg_field field1;
    rand uvm_reg_field field2;
    rand uvm_reg_field field3;
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
        this.field3=uvm_reg_field::type_id::create("field3",,get_full_name());
            this.field3.configure(this, 3, 7, RW, 0, 3'h0, 1, 0, 1);
        endfunction : build 

endclass : uvm_internal_reg

class uvm_reg_external_reg extends uvm_reg;

    `uvm_object_utils(uvm_external_reg)

    rand uvm_reg_field field0;
    rand uvm_reg_field field1;
    rand uvm_reg_field field2;
    rand uvm_reg_field field3;
    function new(string name = "external_reg");
        super.new(name, ss.bit, UVM_NO_COVERAGE);
    endfunction : new 

    virtual function void build();
        this.field0=uvm_reg_field::type_id::create("field0",,get_full_name());
            this.field0.configure(this, 1, 1, RW, 0, 1'h0, 1, 0, 1);
        this.field1=uvm_reg_field::type_id::create("field1",,get_full_name());
            this.field1.configure(this, 1, 3, RW, 0, 1'h0, 1, 0, 1);
        this.field2=uvm_reg_field::type_id::create("field2",,get_full_name());
            this.field2.configure(this, 3, 5, RW, 0, 3'h0, 1, 0, 1);
        this.field3=uvm_reg_field::type_id::create("field3",,get_full_name());
            this.field3.configure(this, 4, 8, RW, 0, 4'h0, 1, 0, 1);
        endfunction : build 

endclass : uvm_external_reg



class ral_block_reg_bank_tables extends uvm_reg_block;

    `uvm_object_untils(ral_block_reg_bank_tables)

    rand uvm_reg_internal_reg internal_reg;
    rand uvm_reg_external_reg external_reg;
    

    function new(string name="ral_block_reg_bank_tables");
        super.new(name, build_coverage(UVM_NO_COVERAGE));
    endfunction : new

    virtual function void build();
        this.default_map = create_map("", space.offset, 4, UVM_LITTLE_ENDIAN, 0);
        internal_reg = uvm_reg_internal_reg::type_id::create("internal_reg",,get_full_name());
        internal_reg.configure(this, null, "");
        internal_reg.build();
        internal_reg.add_hdl_path_slice("internal_reg",32,32);
        default_map.add_reg(internal_reg,`UVM_REG_INTERNAL_REG)
        external_reg = uvm_reg_external_reg::type_id::create("external_reg",,get_full_name());
        external_reg.configure(this, null, "");
        external_reg.build();
        external_reg.add_hdl_path_slice("external_reg",96,32);
        default_map.add_reg(external_reg,`UVM_REG_EXTERNAL_REG)
        endfunction : build 

endclass : ral_block_reg_bank_tables

`endif //RAL_BLOCK_REG_BANK_TABLES_SV