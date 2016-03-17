import os, sys
from common_converter import *
_template = """
import yaml, traceback
import RTC
import OpenRTM_aist

_data = $CONSTRUCTOR
_port = OpenRTM_aist.OutPort("$NAME", _data)


def convert(data, d_list):
  it = iter(d_list)
$CODE
  print 'converted:', data
  return data
  

def _sendData(d_list):
  convert(_data, d_list)
  _port.write()
          
def execute(comp, webSocketSender):
    comp.addOutPort("$NAME", _port)
    webSocketSender.outports[u"$NAME"] = _sendData
          
"""



def create_outport_converter_module(parser, name, typename, verbose=False):

    module_dir = 'modules'
    if not os.path.isdir(module_dir):
        os.mkdir(module_dir)
    global_module = parser.global_module

    typs = global_module.find_types(typename)
    if len(typs) == 0:
        print 'Invalid Type Name (%s)' % typename
        raise InvalidDataTypeException()
    
    module_name = typs[0].parent.name
    copy_idl_and_compile(parser, typs[0].filepath)

    filename = '%s_OutPort_%s.py' % (name, typename.replace('::', '_').strip())
    f = open(os.path.join(module_dir, filename), 'w')
    import value_dic as vd
    value_dic = vd.generate_value_dic(global_module, typename, root_name='data', verbose=verbose)
    #if verbose:
    #    print '-------value-------'
    #    import yaml
    #    print yaml.dump(value_dic, default_flow_style=False)
    #import inport_converter as ip
    global _template
    output = "%s" % _template
    code = create_converter(value_dic, list_name='d_list', indent = '  ')
    if verbose:
        print '------data to list-----'
        print code
    output = output.replace('$NAME', name)
    typs = global_module.find_types(typename)
    output = output.replace('$CONSTRUCTOR', parser.generate_constructor_python(typs[0]))
    output = output.replace('$CODE', code)
    
    #import outport_converter as op
    #code = op.create_converter(value_dic)
    #print '------list to data-----'
    #print code

    output = 'import %s\n' % module_name + output
    
    f.write(output)
    f.close()




def create_converter(value_dic, list_name= '_d_list', indent = '', context = ''):
    int_types = ['long', 'long long', 'unsigned long', 'short', 'unsigned short', 'char', 'unsigned char', 'byte', 'unsigned byte', 'octet']
    float_types = ['float', 'double', 'long double']
    print '-----' * 5
    print value_dic
    print '-----' * 5
    indent_ = '' + indent
    code = ''
    keys_ = value_dic.keys()
    keys_.sort()
    #for key, value in value_dic.items():
    for key in keys_:

        value = value_dic[key]
        if key.find(']') > 0: # Sequence
            context_name = context + '.' + key if len(context) > 0 else key
            context_name = context_name[:context_name.find('[')]
            type_name = key[key.find('<')+1:key.rfind('>')]
            code = code + '%s%s = []\n' % (indent_, context_name)
            #code = code + '%slen = int(%s[index_])\n' % (indent_, list_name)
            code = code + '%slen = int(it.next())\n' % (indent_, list_name)
            #code = code + '%sindex_ = index_ + 1\n' % (indent_)
            code = code + '%sfor i in range(len):\n' % (indent_)
            if type(value) is types.StringType:
                if value == 'double' or value == 'float':
                    code = code + '%s%s.append(float(it.next()))\n' % (indent_ + '  ', context_name, list_name)

                    #code = code + '%sindex_ = index_ + 1\n' % (indent_ + '  ')
            else:
                constructor_code = admin.idl.generate_constructor_python(type_name)[0]
                code = code + '%s%s.append(%s)\n' % (indent_+'  ', context_name, constructor_code)
                code = code + self.generate_outport_converter_python(value, list_name, '  ', context_name + '[i]')
                """
                root_name = key[:key.find('[')]
                root_name = context + '.' + root_name if len(context) > 0 else root_name
                code = code + '%s%s.append(len(%s))\n' % (indent_, list_name, root_name)
                if type(value) is types.StringType:
                    code = code + '%sfor elem in %s:\n' % (indent_, root_name)
                    code = code + '%s%s.apend(elem)\n' % (indent_ + '  ', list_name)
                else:
                    code = code + 'for elem in %s:\n' % (root_name)
                    code = code + self.generate_inport_converter_python(value, list_name=list_name, indent=indent_ + '  ', context = 'elem')
                    """
                pass
        else:
            context_name = context + '.' + key if len(context) > 0 else key
            context_name = context_name.replace('(', '[')
            context_name = context_name.replace(')', ']')
            if value in int_types:
                code = code + '%s%s = int(it.next())\n' % (indent_, context_name)
            elif value in float_types:
                code = code + '%s%s = float(it.next())\n' % (indent_, context_name)
            else:
                code = code + '%s%s = (it.next())\n' % (indent_, context_name)
            #code = code + '%sindex_ = index_ + 1\n' % (indent_)
                #code = code + '%s%s.append(%s)\n' % (indent_, list_name, context_name) 
            pass
    return code
