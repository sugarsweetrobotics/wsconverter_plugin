import os, sys, subprocess, traceback
from common_converter import *

_template = """
import yaml, traceback, json
import RTC
import OpenRTM_aist

_data = $CONSTRUCTOR
_port = OpenRTM_aist.InPort("$NAME", _data)


def convert(data):
  print data
$CODE
  return d_list
  

class DataListener(OpenRTM_aist.ConnectorDataListenerT):
  def __init__(self, webSocketSender):
      self._ws = webSocketSender
      pass

  def __del__(self):
      print "dtor of ", self._name

  def __call__(self, info, cdrdata):

      data = OpenRTM_aist.ConnectorDataListenerT.__call__(self, info, cdrdata, $CONSTRUCTOR)

      #convert(data)

      try:
          #self._ws.write_message('InPort {' + yaml.safe_dump({'$NAME' : convert(data)}) + '}')
          self._ws.write_message('InPort ' + json.dumps({'$NAME' : convert(data)}) )
      except:
          print 'write_message_error.'
          traceback.print_exc()
          
def execute(comp, webSocketSender):
    comp.addInPort("$NAME", _port)

    _port.addConnectorDataListener(OpenRTM_aist.ConnectorDataListenerType.ON_BUFFER_WRITE,
                                   DataListener(webSocketSender))
    
"""

def create_inport_converter_module(parser, name, typename, verbose=False):
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

    filename = '%s_InPort_%s.py' % (name, typename.replace('::', '_').strip())
    f = open(os.path.join(module_dir, filename), 'w')
    import value_dic as vd
    value_dic = vd.generate_value_dic(global_module, typename, root_name='data', verbose=verbose)

    global _template
    output = "%s" % _template
    code = create_converter(value_dic, list_name='d_list', indent = '  ')

    output = output.replace('$NAME', name)
    typs = global_module.find_types(typename)
    output = output.replace('$CONSTRUCTOR', parser.generate_constructor_python(typs[0]))
    output = output.replace('$CODE', code)

    output = 'import %s\n' % module_name + output

    f.write(output)
    f.close()

def create_converter(value_dic, list_name= '_d_list', indent = '', context = ''):
    #def generate_inport_converter_python(self, value_dic, list_name= '_d_list', indent = '', context = ''):
    """ serialize to list
    """
    indent_ = '' + indent
    code = '%s%s = []\n' % (indent, list_name)
    keys_ = value_dic.keys()
    keys_.sort()
    #for key, value in value_dic.items():
    for key in keys_:
        value = value_dic[key]
        if key.find(']') >= 0: # Sequence
            root_name = key[:key.find('[')]
            root_name = context + '.' + root_name if len(context) > 0 else root_name
            code = code + '%s%s.append(str(len(%s)))\n' % (indent_, list_name, root_name)
            if type(value) is types.StringType:
                code = code + '%sfor elem in %s:\n' % (indent_, root_name)
                code = code + '%s%s.append(str(elem))\n' % (indent_ + '  ', list_name)
            else:
                code = code + 'for elem in %s:\n' % (root_name)
                code = code + create_converter(value, list_name=list_name, indent=indent_ + '  ', context = 'elem')
                pass
        else:
            context_name = context + '.' + key if len(context) > 0 else key
            context_name = context_name.replace('(', '[')
            context_name = context_name.replace(')', ']')

            code = code + '%s%s.append(str(%s))\n' % (indent_, list_name, context_name) 
            pass
    return code
    
