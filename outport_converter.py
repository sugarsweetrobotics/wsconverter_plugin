
_template = """
import yaml, traceback
import RTC
import OpenRTM_aist

_data = $CONSTRUCTOR
_port = OpenRTM_aist.InPort("$NAME", _data)


def convert(data, d_list):
  print data
$CODE
  return data
  

def _sendData(d_list)
  convert(_data, d_list)
  _port.write()
          
def execute(comp, webSocketSender):
    comp.addOutPort("out", _port)
    webSocketSender.outport["out"] = _sendData
          
"""


def create_outport_converter_module(parser, name, typename, verbose=False):
    global_module = parser.global_module
    filename = '%s_InPort_%s.py__' % (name, typename.replace('::', '_').strip())
    f = open(filename, 'w')
    import value_dic as vd
    value_dic = vd.generate_value_dic(global_module, typename, root_name='data', verbose=verbose)
    print '-------value-------'
    import yaml
    print yaml.dump(value_dic, default_flow_style=False)
    
    print '-------header-------'
    code = vd.generate_header(value_dic)
    print code
    
    #import inport_converter as ip
    global _template
    output = "%s" % _template
    code = create_converter(value_dic, list_name='d_list', indent = '  ')
    print '------data to list-----'
    print code
    output = output.replace('$NAME', name)
    typs = global_module.find_types(typename)
    output = output.replace('$CONSTRUCTOR', parser.generate_constructor_python(typs[0]))
    output = output.replace('$CODE', code)
    
    import outport_converter as op
    code = op.create_converter(value_dic)
    print '------list to data-----'
    print code
    
    f.write(output)
    f.close()




def create_converter(value_dic, list_name= '_d_list', indent = '', context = ''):
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
            code = code + '%slen = int(%s[index_])\n' % (indent_, list_name)
            code = code + '%sindex_ = index_ + 1\n' % (indent_)
            code = code + '%sfor i in range(len):\n' % (indent_)
            if type(value) is types.StringType:
                if value == 'double' or value == 'float':
                    code = code + '%s%s.append(float(%s[index_]))\n' % (indent_ + '  ', context_name, list_name)

                    code = code + '%sindex_ = index_ + 1\n' % (indent_ + '  ')
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
            code = code + '%s%s = %s[index_]\n' % (indent_, context_name, list_name)
            code = code + '%sindex_ = index_ + 1\n' % (indent_)
                #code = code + '%s%s.append(%s)\n' % (indent_, list_name, context_name) 
            pass
    return code
