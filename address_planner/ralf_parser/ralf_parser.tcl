
proc set_def {name value} {
    uplevel 2 "set DEF($name) {$value}"
}

proc get_def {name} {
    set max_level [info level]
    set var_name DEF($name)
    set current_level 0
    
    while {1} {        
        if {[uplevel $current_level "info exists $var_name"]} {
            return [uplevel $current_level set $var_name]
        }
        
        if {$current_level < $max_level} {
            set current_level [expr {$current_level + 1}]
        } else {
            error "Variable $var_name not found in any enclosing scope."
        }
    }
}


proc bits       {args} { uplevel "set var_bits       [lindex $args 0]" }
proc access     {args} { uplevel "set var_access     [lindex $args 0]" }
proc reset      {args} { uplevel "set var_reset      [lindex $args 0]" }
proc hard_reset {args} { uplevel "set var_reset      [lindex $args 0]" }
proc soft_reset {args} { }
proc bytes      {args} { uplevel "set var_bytes      [lindex $args 0]" }
proc size       {args} { uplevel "set var_size       [lindex $args 0]" }
proc endian     {args} { uplevel "set var_endian     [lindex $args 0]" }
proc attributes {args} { }
proc doc         {args} { uplevel [list set var_doc [lindex $args 0]] }
proc enum        {args} { }
proc cover       {args} { }
proc coverpoint  {args} { }
proc constraint  {args} { }
proc left_to_right {args} { }
proc noelse      {args} { }
proc shared      {args} { }
proc cross       {args} { }
proc volatile    {args} { }

proc parse_proc_arguments {-args args results} {
    upvar $results options

    set options(num_args) [llength $args     ]
    set options(name)     [lindex  $args 0   ]

    set options(is_def)     0
    set options(is_inst)    0
    

    if {$options(num_args) == 4} {
        if {![string match "@*" [lindex $args 2]]} {
            puts [lindex $args 0]
            error "4 Invalid second argument. Should start with '@', but get [lindex $args 1]."
        }
        set options(is_def)     1
        set options(def_code)   [lindex $args 3]
        set options(is_inst)    1
        set options(inst_addr)  [lindex $args 2]
        set options(inst_num)   [lindex $args 1]
    } elseif {$options(num_args) == 3} {
        if {[string match "@*" [lindex $args 1]]} {
            # error "3 Invalid second argument. Should start with '@', but get [lindex $args 1]."
            set options(is_def)     1
            set options(def_code)   [lindex $args 2]
            set options(is_inst)    1
            set options(inst_addr)  [lindex $args 1]
            set options(inst_num)   0
        } else {
            set options(is_def)     1
            set options(def_code)   [lindex $args 2]
            set options(inst_num)   [lindex $args 1]
        }
        
    } elseif {$options(num_args) == 2} {
        if {[string match "@*" [lindex $args 1]]} {
            set options(is_inst)    1
            set options(inst_addr)  [lindex $args 1]
            set options(inst_num)   0
        } else {
            set options(is_def)     1
            set options(def_code)   [lindex $args 1]
            set options(inst_num)   0
        }
    } else {
        error "Error arg number, Expected 2 or 3. "
    }
}


proc field {args} {
    parse_proc_arguments -args $args param

    set FIELD_DICT [dict create]
    set ADDR_DICT  [dict create]

    # puts "$param(name).field: $param(is_inst)"

    if {$param(is_def)} {
        eval $param(def_code)
        # create def_var data struct
        set payload [dict create]
        dict set payload name   $param(name)
        if { [info exists var_bits] } {
            dict set payload bits   $var_bits
        } else {
            dict set payload bits   1
        }
        if { [info exists var_access] } {
            dict set payload access $var_access
        } else {
            dict set payload access ro
        }
        if { [info exists var_reset] } {
            dict set payload reset  $var_reset
        } else {
            dict set payload reset  0
        }
        if { [info exists var_doc] } {
            dict set payload doc $var_doc
        } else {
            dict set payload doc "no comments"
        }
        # define def_var in up level stack.
        set_def "$param(name).field" $payload
    }

    if {$param(is_inst)} {
        # search define in up level scope, add name in def dict.
        set inst_dict [get_def "$param(name).field"]
        dict set inst_dict addr $param(inst_addr)

        # add inst to uplevel field_dict
        uplevel "dict set FIELD_DICT $param(name).field {$inst_dict}"
        # puts "field tcl finish $param(name)"
    }
}


proc register {args} {
    parse_proc_arguments -args $args param

    set FIELD_DICT [dict create]
    set ADDR_DICT  [dict create]


    if {$param(is_def)} {
        eval $param(def_code)

        # define data struct
        set payload [dict create]
        dict set payload name         $param(name)
        dict set payload FIELD_DICT   "$FIELD_DICT"
        dict set payload ADDR_DICT    "$ADDR_DICT"
        if { [info exists var_bytes] } {
            dict set payload width    $var_bytes
        } else {
            dict set payload width    4
        }
        if { [info exists var_doc] } {
            dict set payload doc $var_doc
        } else {
            dict set payload doc "no comments"
        }
        dict set payload inst_num     $param(inst_num)

        # define def_var in up level stack.
        set_def "$param(name).register" $payload
    }


    if {$param(is_inst)} {
        # search define in up level scope, add name in def dict.
        set inst_dict [get_def "$param(name).register"]
        dict set inst_dict addr $param(inst_addr)

        # add inst to uplevel field_dict
        uplevel "dict set ADDR_DICT $param(name).register {$inst_dict}"
    }
    # puts "reg tcl finish $param(name)"

}

proc memory {args} {
    parse_proc_arguments -args $args param

    set FIELD_DICT [dict create]
    set ADDR_DICT  [dict create]

    set payload [dict create]
    eval $param(def_code)
    dict set payload name       $param(name)
    dict set payload size       $var_size
    dict set payload is_memory  1

    if {$param(is_def)} { dict set payload addr 0 }
    if {$param(is_inst)} { dict set payload addr $param(inst_addr) }

    set_def "$param(name).memory" $payload
    set inst_dict [get_def "$param(name).memory"]
    uplevel "dict set ADDR_DICT $param(name).memory {$inst_dict}"
    # puts "block proc finish $param(name)"
}

proc block {args} {
    parse_proc_arguments -args $args param

    set FIELD_DICT [dict create]
    set ADDR_DICT  [dict create]

    if {$param(is_def)} {
        eval $param(def_code)

        # define data struct
        set payload [dict create]
        dict set payload name         "$param(name)"
        dict set payload FIELD_DICT   "$FIELD_DICT"
        dict set payload ADDR_DICT    "$ADDR_DICT"

        # define def_var in up level stack.
        set_def "$param(name).block" $payload
    }


    if {$param(is_inst)} {
        # search define in up level scope, add name in def dict.
        set inst_dict [get_def "$param(name).block"]
        dict set inst_dict addr $param(inst_addr)

        # add inst to uplevel field_dict
        uplevel "dict set ADDR_DICT $param(name).block {$inst_dict}"
    }

}

proc system {args} {
    parse_proc_arguments -args $args param

    set FIELD_DICT [dict create]
    set ADDR_DICT  [dict create]

    if {$param(is_def)} {
        eval $param(def_code)

        # define data struct
        set payload [dict create]
        dict set payload name         "$param(name)"
        dict set payload FIELD_DICT   "$FIELD_DICT"
        dict set payload ADDR_DICT    "$ADDR_DICT"

        # define def_var in up level stack.
        set_def "$param(name).system" $payload
    }


    if {$param(is_inst)} {
        # search define in up level scope, add name in def dict.
        set inst_dict [get_def "$param(name).system"]
        dict set inst_dict addr $param(inst_addr)

        # add inst to uplevel field_dict
        uplevel "dict set ADDR_DICT $param(name).system {$inst_dict}"
    }

}
