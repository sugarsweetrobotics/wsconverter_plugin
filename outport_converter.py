



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
