

class MatrixCFG(object):
    def __init__(self):
        self.master_mapping_list = ['name', 'protocol', 'is_active', 
                                    'addr_width', 'data_width', 
                                    'support_incr', 'support_wrap', 
                                    'support_fixed', 'rd_enable',
                                    'wr_enable', 'support_reording', 
                                    'support_exclusive', 'unique_id',
                                    'max_len', 'min_size', 
                                    'w_req_auser_width', 'r_req_auser_width',
                                    'w_user_width', 'r_user_width', 
                                    'b_user_width', 'rd_id_width', 
                                    'wr_id_width', 'rd_ost', 'wr_ost', 
                                    'ignore_signal', 'pre',
                                    'post', 'upper', 'clk', 'freq', 
                                    'rst', 'hier', 'wr_latency', 
                                    'rd_latency', 'wr_bandwidth', 
                                    'rd_bandwidth', 'cacheline_size',
                                    'support_write_evict', 
                                    'no_shareable_min_addr', 
                                    'no_shareable_max_addr',
                                    'inner_min_addr', 'inner_max_addr', 
                                    'outer_min_addr', 'outer_max_addr']
        self.slave_mapping_list  = ['name', 'protocol', 'is_active', 
                                    'addr_width', 'min_addr', 'max_addr',
                                    'data_width', 'support_incr',
                                    'support_wrap', 'support_fixed',
                                    'rd_enable', 'wr_enable',
                                    'support_reording', 'w_req_auser_width',
                                    'r_req_auser_width', 'w_user_width', 
                                    'r_user_width', 'b_user_width', 
                                    'rd_id_width', 'wr_id_width',
                                    'rd_ost', 'wr_ost', 'ignore_signal', 
                                    'pre', 'post', 'upper', 'clk', 'freq', 
                                    'rst', 'hier', 'is_mem', 'is_rom', 
                                    'cacheline_size', 'wr_latency', 
                                    'rd_latency', 'wr_bandwidth', 
                                    'rd_bandwidth', 'support_write_evict', 
                                    'no_shareable_min_addr', 
                                    'no_shareable_max_addr',
                                    'inner_min_addr', 'inner_max_addr', 
                                    'outer_min_addr', 'outer_max_addr']
        
    @property
    def master_mapping(self):
        return { elem: i for i, elem in enumerate(self.master_mapping_list) }
    
    @property
    def master_len(self):
        return len(self.master_mapping_list) + 1
    
    @property
    def slave_mapping(self):
        return { elem: i for i, elem in enumerate(self.slave_mapping_list) }
    
    @property
    def slave_len(self):
        return len(self.slave_mapping_list) + 1
     
            
matrix_cfg = MatrixCFG()

master_content = ['NA']*matrix_cfg.master_len
master_mapping = matrix_cfg.master_mapping

slave_content  = ['NA']*matrix_cfg.slave_len
slave_mapping  = matrix_cfg.slave_mapping

