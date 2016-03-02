import os, sys, types

import wasanbon
from wasanbon.core.plugins import PluginFunction, manifest

class Plugin(PluginFunction):

    def __init__(self):
        super(Plugin, self).__init__()
        pass

    def depends(self):
        return ['admin.environment', 'admin.idl']

    def _print_alternatives(self):
        print 'hoo'
        print 'foo'
        print 'hoge'
        print 'yah'

    @manifest
    def stop(self, argv):
        """ This is help text
        """
        #self.parser.add_option('-p', '--port', help='Port option (default=60000)', default=60000, action='store', dest='port')
        options, argv = self.parse_args(argv[:], self._print_alternatives)
        verbose = options.verbose_flag # This is default option
        #force   = options.force_flag
        #port = options.port

        # Create PID file
        pid_dir = os.path.join(wasanbon.home_path, 'ws')
        if not os.path.isdir(pid_dir):
            os.mkdir(pid_dir)
        pid_file = os.path.join(pid_dir, 'pid')
        if not os.path.isfile(pid_file):
            return 0

        pid = int(open(pid_file, 'r').read())

        #import psutil
        #psutil.kill(pid)
        import signal
        try:
            os.kill(pid, signal.SIGKILL)
        except:
            pass

        os.remove(pid_file)

    @manifest
    def start(self, argv):
        """ This is help text
        """
        self.parser.add_option('-p', '--port', help='Port option (default=8080)', default=8080, action='store', dest='port')
        options, argv = self.parse_args(argv[:], self._print_alternatives)
        verbose = options.verbose_flag # This is default option
        #force   = options.force_flag
        port = options.port

        # Create PID file
        pid_dir = os.path.join(wasanbon.home_path, 'ws')
        if not os.path.isdir(pid_dir):
            os.mkdir(pid_dir)
        pid_file = os.path.join(pid_dir, 'pid')
        if os.path.isfile(pid_file):
            self.stop([])
            #os.remove(pid_file)
        open(pid_file, 'w').write(str(os.getpid()))

        #import signal
        #signal.signal(signal.SIGUSR1, self.sigusr1_isr) # SIGUSR1 = 30
        #signal.signal(signal.SIGINT, self.sigint_isr) # SIGUSR1 = 30

        import time
        import tornado.ioloop
        import tornado.web
        import tornado.websocket
        import tornado.httpserver
        from tornado.ioloop import PeriodicCallback
        
        from tornado.options import define, options, parse_command_line

        import handler
        handler.idl_plugin = admin.idl

        import rtcomponent as rtcomp

        rtcomp.main(['wsconverter'])

        sys.stdout.write('- Starting WebSocket Server.\n')

        #define("port", default = 8080, help = "run on the given port", type = int)
        app = tornado.web.Application([
                (r"/", handler.IndexHandler),
                (r"/ws", handler.SendWebSocket),
                ])
        parse_command_line()
        http_server = tornado.httpserver.HTTPServer(app)
        http_server.listen(port)

        #app.listen(8080)
        tornado.ioloop.IOLoop.instance().start()
        sys.stdout.write(' - Web reactor stopped.\n')
        return 0
    
    @manifest
    def generate_converter(self, argv):
        self.parser.add_option('-l', '--language', help='Language option (default=python)', default='python', action='store', dest='language')
        options, argv = self.parse_args(argv[:], self._print_alternatives)
        verbose = options.verbose_flag # This is default option
        language = options.language


        if language == 'python':
            wasanbon.arg_check(argv, 5)
            name = argv[3]
            typename = argv[4]
            
            #value_dic = self.generate_value_dic(typename, verbose=verbose)
            admin.idl.parse()
            #gm = admin.idl.get_global_module()
            import inport_converter as ip
            ip.create_inport_converter_module(admin.idl.get_idl_parser(), name, typename, verbose=verbose)


        elif language == 'dart':
            admin.idl.parse()

            gm = admin.idl.get_global_module()

            self._parsed_types = []
            for m in gm.modules:
                print '-------', m.name, '------'
                code = ''
                for s in m.structs:
                    code = code + self.generate_class_dart(s.full_path) + '\n'
                    #self._apply_post_process_dart(code)
                #print code
                

                code = self._apply_post_process_dart(code)
                if not os.path.isdir('dart'):
                    os.mkdir('dart')
                if not os.path.isdir('dart/lib'):
                    os.mkdir('dart/lib')
                f = open('dart/lib/%s.dart' % (m.name.lower()), 'w')
                comment_code = """/// file: %s
/// generator: wasanbon
///


""" % (m.name.lower() + '.dart')
                f.write(comment_code)
                f.write(code)
                f.close()
        return 0


    def _apply_post_process_dart(self, code):
        using_module_name = []
        for token in [t.strip() for t in code.split(' ')]:
            if token.find('::') > 0:
                module_name = token[:token.find('::')]
                if not module_name in using_module_name:
                    using_module_name.append(module_name)
            pass


        import_code = ''
        for module_name in using_module_name:
            import_code = import_code + "import '%s.dart' as %s;\n" % (module_name.lower(), module_name)

        code = import_code + '\n\n' + code
        code = code.replace('::', '.')
        code = code.replace('sequence', 'List')
        
        return code


    def generate_class_dart(self, typename):
        gm = admin.idl.get_global_module()
        typs = gm.find_types(typename)
        if len(typs) == 0:
            sys.stdout.write('# Error. Type(%s) not found.\n' % typename)
            return None
        typ = typs[0]
        

        codes = ['']

        #self._parsed_types = []

        #value_dic = self.generate_value_dic(typename, verbose=False)

        def _parse_typedef(typ):
            if not typ.type.is_primitive:
                if typ.type.obj.is_struct:
                    _parse_struct(typ.type.obj)
                elif typ.type.obj.is_sequence:
                    # print 'hoge', typ.type.obj.inner_type
                    if not typ.type.obj.inner_type.is_primitive:
                        _parse_type(typ.type.obj.inner_type.obj)
            pass


        
        def _parse_struct(typ):
            # print 'Parsing struct ', typ.full_path
            code = ''
            if typ.full_path in self._parsed_types:
                return code

            else:
                self._parsed_types.append(typ.full_path)

            module_name = typ.full_path
            if module_name.find('::') > 0:
                module_name = module_name[:module_name.rfind('::')]

            for m in typ.members:
                if m.type.is_primitive:
                    pass
                elif m.type.obj.is_struct:
                    _parse_struct(m.type.obj)
                elif m.type.obj.is_typedef:
                    _parse_typedef(m.type.obj)

            code = code + 'class %s {' % typ.basename + '\n'
            for m in typ.members:
                m_type = m.type
                n = None
                if not m_type.is_primitive:
                    if m_type.obj.is_typedef:
                        m_type = m.type.obj.type # = 'typedef'
                        
                n = m_type.basename if m_type.pathname == module_name else m_type.name
                int_types = ['unsigned long', 'unsigned short', 'unsigned long long', 'unsigned char', 'long', 'short', 'char', 'byte', 'octet']
                double_types = ['double', 'long double', 'float']
                if n == 'string':
                    n = 'String'
                elif n in int_types:
                    n = 'int'
                elif n in double_types:
                    n = 'double'
                code = code + '  %s %s;\n' %(n, m.name)

            # Zero Constructor
            code = code + '\n\n'
            code = code + '  %s.zeros() {\n' % typ.basename
            for m in typ.members:
                m_type = m.type
                n = None
                if not m_type.is_primitive:
                    if m_type.obj.is_typedef:
                        m_type = m.type.obj.type # = 'typedef'
                n = m_type.basename if m_type.pathname == module_name else m_type.name

                if m_type.is_sequence:
                    code = code + '    %s = [];\n' % m.name
                elif m_type.is_primitive:
                    code = code + '    %s = 0;\n' %(m.name)                    
                elif m_type.obj.is_struct:
                    code = code + '    %s = new %s.zeros();\n' % (m.name, n)
            code = code + '  }\n'
            #

            # Constructor
            code = code + '\n\n'
            code = code + '  %s( ' % typ.name
            # Arguments
            for m in typ.members:
                m_type = m.type
                n = None
                if not m_type.is_primitive:
                    if m_type.obj.is_typedef:
                        m_type = m.type.obj.type # = 'typedef'
                n = m_type.basename if m_type.pathname == module_name else m_type.name

                int_types = ['unsigned long', 'unsigned short', 'unsigned long long', 'unsigned char', 'long', 'short', 'char', 'byte', 'octet']
                double_types = ['double', 'long double', 'float']
                if n == 'string':
                    n = 'String'
                elif n in int_types:
                    n = 'int'
                elif n in double_types:
                    n = 'double'


                code = code + '%s %s, ' % (n, m.name + '_')
            code = code[:-2]
            code = code + ') {\n'
            # content
            for m in typ.members:
                m_type = m.type
                n = None
                if not m_type.is_primitive:
                    if m_type.obj.is_typedef:
                        m_type = m.type.obj.type # = 'typedef'
                n = m_type.basename if m_type.pathname == module_name else m_type.name

                code = code + '    %s = %s;\n' % (m.name, m.name + '_')
            
            code = code + '  }\n'


            code = code + '\n'


            # Serialization Function
            code = code + '  List<String> serialize() {\n'
            code = code + '    var ls = [];\n'

            map = {}
            for m in typ.members:
                map[m.name] = m

            keys_ = [m.name for m in typ.members]
            keys_.sort()
            

            #for m in typ.members:
            for k in keys_:
                m = map[k]
                m_type = m.type
                n= None
                if not m_type.is_primitive:
                    if m_type.obj.is_typedef:
                        m_type = m.type.obj.type
                n = m_type.basename if m_type.pathname == module_name else m_type.name
                
                if m_type.is_sequence:
                    code = code + '    ls.add(%s.length.toString());\n' % m.name
                    code = code + '    %s.forEach((var elem) {\n' % m.name
                    if m_type.obj.inner_type.is_primitive:
                        code = code + '      ls.add(elem.toString());\n'
                    else:
                        code = code + '      ls.add(elem.serialize());\n'
                    code = code + '    });\n'
                    pass
                elif m_type.is_primitive:
                    code = code + '    ls.add(%s.toString());\n' % m.name
                elif m_type.obj.is_struct:
                    code = code + '    ls.addAll(%s.serialize());\n' % (m.name)
            code = code + '    return ls;\n'
            code = code + '  }\n\n'


            # Deserialization Function

            code = code + '  int parse(List<String> ls) {\n'
            code = code + '    int index = 0;\n'

            map = {}
            for m in typ.members:
                map[m.name] = m

            keys_ = [m.name for m in typ.members]
            keys_.sort()
            
            for k in keys_:
                m = map[k]
                m_type = m.type
                n = None

                if not m_type.is_primitive:
                    if m_type.obj.is_typedef:
                        m_type = m.type.obj.type
                n = m_type.basename if m_type.pathname == module_name else m_type.name
                
                if m_type.is_sequence:
                    code = code + '    var len = num.parse(ls[index]);\n'
                    code = code + '    index++;\n'
                    code = code + '    bool cleared = len != %s.length;\n' % m.name
                    code = code + '    if (cleared) %s.clear();\n' % m.name
                    code = code + '    for(int i = 0;i < len;i++) {\n'
                    if m_type.inner_type.is_primitive:
                        code = code + '      if (cleared) %s.add(num.parse(ls[index]));\n' % m.name
                        code = code + '      else %s[i] = num.parse(ls[index]);\n' % m.name
                        code = code + '      index++;\n'
                    elif m_type.is_struct:
                        code = code + '      if (cleared) {\n'
                        code = code + '        var v = new %s().zeros();\n' % m_type.name
                        code = code + '        index += v.parse(ls.sublist(index));\n' 
                        code = code + '        %s.add(v);\n' % m.name
                        code = code + '      } else {\n'
                        code = code + '        index += %s[i].parse(ls.sublist(index));\n'
                        code = code + '      }\n'
                    code = code + '    }\n'
                    pass
                elif m_type.is_primitive:
                    code = code + '    %s = num.parse(ls[index]);\n' % m.name
                    code = code + '    index++;\n'
                elif m_type.obj.is_struct:
                    code = code + '    index += %s.parse(ls.sublist(index));\n' % m.name
            code = code + '    return index;\n'
            code = code + '  }\n\n'

            # To string method
            code = code + '  String toString() {\n'
            code = code + '    String ret = "%s(";\n' % typ.name
            map = {}
            for m in typ.members:
                map[m.name] = m

            keys_ = [m.name for m in typ.members]
            keys_.sort()
            
            counter = 0
            for k in keys_:
                m = map[k]
                m_type = m.type
                n= None
                if not m_type.is_primitive:
                    if m_type.obj.is_typedef:
                        m_type = m.type.obj.type
                n = m_type.basename if m_type.pathname == module_name else m_type.name
                
                if m_type.is_sequence:
                    code = code + '    ret += "%s = [";\n' % m.name
                    code = code + '    for(int i = 0;i < %s.length;i++) {\n' % m.name
                    code = code + '      var elem = %s[i];\n' % m.name
                    code = code + '      ret += "$elem";\n'
                    code = code + '      if (i != %s.length-1) {\n' % m.name
                    code = code + '        ret += ", ";\n'
                    code = code + '      }\n'
                    code = code + '    }\n'
                    code = code + '    ret += "]";\n'
                    pass
                elif m_type.is_primitive:
                    code = code + '    ret += "%s = $%s";\n' % (m.name, m.name)
                elif m_type.obj.is_struct:
                    code = code + '    ret += "%s = $%s";\n' % (m.name, m.name)
                counter = counter  + 1
                if counter < len(keys_):
                    code = code + '    ret += ", ";\n'
            code = code + '    return ret + ")";\n'
            code = code + '  }\n\n'


            code = code + '}\n\n'
            codes[0] = codes[0] + code
            return code
            

        def _parse_type(typ):
            #print 'Parsing type ', typ
            if typ.is_struct:
                #print '-struct'
                _parse_struct(typ)
            else:
                #print '-', dir(typ)
                pass
                
            pass

        _parse_type(typ)

        
        return codes[0] #_apply_post_process_dart(codes[0])


