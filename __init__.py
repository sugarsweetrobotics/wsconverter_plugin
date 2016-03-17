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
            
            admin.idl.parse()
            #gm = admin.idl.get_global_module()
            from host import inport_converter as ip
            ip.create_inport_converter_module(admin.idl.get_idl_parser(), name, typename, verbose=verbose)

            from host import outport_converter as op
            op.create_outport_converter_module(admin.idl.get_idl_parser(), name, typename, verbose=verbose)


        elif language == 'dart':
            admin.idl.parse()

            from client import dart_converter as dc
            dc.generate_converter(admin.idl.get_idl_parser(), verbose=verbose)
            
        return 0





