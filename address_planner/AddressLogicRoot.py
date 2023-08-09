from jinja2     import PackageLoader,Environment
import os
import builtins
import shutil



class AddressLogicRoot(object):

    def __init__(self,name,description='',path='./'):
        self.module_name = name
        self.inst_name   = ''
        self.description = description
        self.path        = path
        self.father      = None
        self._name_prefix = 'addr'

    @property
    def global_name(self):
        return self.module_name if self.father == None else '%s%s%s' % (self.father.global_name,'_',self.inst_name)

    def join_name(self,*args,join_str='_'):
        return join_str.join([x for x in args if x is not None])

    def father_until(self, T):
        if isinstance(self, T):
            return self
        elif self.father is None:
            return None
        else:
            return self.father.father_until(T)

    def module_name_until(self,T,join_str='_'):
        #print(self)
        #print(type(self))
        #print(T)
        if self.father is None or self is T or (isinstance(T,type) and isinstance(self,T)):
        #if self.father is None or isinstance(self, T) or (isinstance(T,type) and isinstance(self,T)):
            return self.module_name
        else:
            return self.join_name(self.father.module_name_until(T,join_str),self.module_name,join_str=join_str)


    def module_name_until_RegSpace(self):
        from .RegSpace import RegSpace
        return self.module_name_until(RegSpace)


    @property
    def global_path(self):
        return self.path if self.father == None else self.father.global_path
    
    @property
    def output_path(self):
        if self.father is not None:
            return self.father.output_path
        else:
            return os.path.join(self.global_path,'build/'+self.module_name)
    #########################################################################################
    # file path definition
    #########################################################################################

    @property
    def _vhead_dir(self):
        return os.path.join(self.output_path+'/vhead')

    @property
    def _chead_dir(self):
        return os.path.join(self.output_path+'/chead')

    @property
    def _html_dir(self):
        return os.path.join(self.output_path+'/html')



    @property
    def html_path(self):
        return os.path.join(self._html_dir,self.html_name)

    @property
    def chead_path(self):
        return os.path.join(self._chead_dir,self.chead_name)

    @property
    def vhead_path(self):
        return os.path.join(self._vhead_dir,self.vhead_name)
    
    @property
    def json_path(self):
        return os.path.join(self._html_dir, 'data.json')


    @property
    def html_name(self):
        return '%s_%s.html' % (self._name_prefix,self.global_name)

    @property
    def chead_name(self):
        return '%s_%s.h' % (self._name_prefix,self.module_name)

    @property
    def vhead_name(self):
        return '%s_%s.vh' % (self._name_prefix,self.module_name)
    


    #########################################################################################
    # output generate
    #########################################################################################

    def clean_dir(self):
        if os.path.exists(self.path):       shutil.rmtree(self.path)

    def build_dir(self):
        if not os.path.exists(self.path):       os.makedirs(self.path)
        if not os.path.exists(self._html_dir):  os.makedirs(self._html_dir) 
        if not os.path.exists(self._chead_dir): os.makedirs(self._chead_dir) 
        if not os.path.exists(self._vhead_dir): os.makedirs(self._vhead_dir) 

    def report_from_template(self,template,extra_in_namespace={}):
        env = Environment(loader=PackageLoader('address_planner','report_template'))
        template = env.get_template(template)
        template.globals['builtins'] = builtins
        for k,v in extra_in_namespace.items():
            template.globals[k] = v
        text = template.render(space=self)
        return text