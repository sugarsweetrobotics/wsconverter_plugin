import os, sys, json, traceback

import tornado.ioloop
import tornado.web
import tornado.websocket
from tornado.ioloop import PeriodicCallback

from tornado.options import define, options, parse_command_line


ws = None
idl_plugin = None

class IndexHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
        self.render("index.html")


class SendWebSocket(tornado.websocket.WebSocketHandler):
    #on_message -> receive data
    #write_message -> send data

    # called when connection established

    _handshake_message = 'wasanbon_converter'
    _handshake_response = 'wasanbon_converter ready'

    outports = {}
    _verbose = True

    def open(self):
        self._ready = False
        self._test = False
        if self._verbose: print " - WebSocket opened" 

    def check_origin(self, origin):
        return True

    def allow_draft76(self):
        return True

    def _on_handshake(self, message):
        tokens = message.split(' ')
        if not tokens[0] == self._handshake_message:
            print ' -- Error. Invalid message %s' % message
            return
        for t in tokens:
            if t.startswith('test='):
                print 'test is ', t
                self._test = t.split('=')[1][1:-1] == 'true'
                
            
        self.write_message(self._handshake_response)
        if self._verbose: ' -- HandShake Okay.'

        try:
            import rtcomponent
            comp = rtcomponent.component
            print comp.get_context(0).activate_component(comp.getObjRef())
        except:
            traceback.print_exc()

        self._ready = True
        global ws
        ws = self

        if self._test:
            self._start_test_mode()

    def on_message(self, message):
        if not self._ready:
            return self._on_handshake(message)
        else:
            self._on(message);

    def _on(self, message):
        if message.startswith('manager'):
            self._on_manager(message[len('manager')+1:])
        elif message.startswith('OutPort'):
            self._on_OutPort(message[len('OutPort')+1:])

    def _on_manager(self, message):
        if self._verbose: print 'manager message: ', message
        if message.startswith('addInPort'):
            if self._onAddInPort(message[len('addInPort')+1:]):
                print 'true'
                self.write_message('wsconverter addInPort true')
            else:
                self.write_message('wsconverter addInPort false')

        if message.startswith('addOutPort'):
            if self._onAddOutPort(message[len('addOutPort')+1:]):
                print 'true'
                self.write_message('wsconverter addOutPort true')
            else:
                self.write_message('wsconverter addOutPort false')

    def _on_OutPort(self, message):
        if self._verbose: print 'OutPort message: ', message
        d_ = json.loads(message.strip())
        name = d_.keys()[0]
        if not name in self.outports.keys():
            print '# Error. No OutPort (name=%s) is registerd.' % name
            return
        self.outports[name](d_[name])
            
        

    def _onAddInPort(self, message):
        name = message.split(' ')[0].strip()
        typename = message.split(' ')[1].strip()
        print 'AddInPort', name, typename

        idl_plugin.parse()
        import inport_converter as ip
        verbose = True
        ip.create_inport_converter_module(idl_plugin.get_idl_parser(), name, typename, verbose=verbose)

        modulename = name.strip() + '_InPort_' + typename.replace('::', '_').strip()
        print 'module:', modulename
        import rtcomponent
        rtcomponent.component.load(modulename)
        return True

    def _onAddOutPort(self, message):
        name = message.split(' ')[0].strip()
        typename = message.split(' ')[1].strip()
        print 'AddOutPort', name, typename

        idl_plugin.parse()
        import outport_converter as op
        verbose = True
        op.create_outport_converter_module(idl_plugin.get_idl_parser(), name, typename, verbose=verbose)

        modulename = name.strip() + '_OutPort_' + typename.replace('::', '_').strip()
        print 'module:', modulename
        import rtcomponent
        rtcomponent.component.load(modulename)
        return True
        
    # on callback start
    def _send_message(self):
        
        self.i += 1
        self.write_message(str(self.i))

    # when connection disconnected.
    def on_close(self):
        #self.callback.stop()
        print " - WebSocket closed"
        self._ready = False
        import rtcomponent
        try:
            comp = rtcomponent.component
            print comp.get_context(0).activate_component(comp.getObjRef())
        except:
            traceback.print_exc()
        


    def _start_test_mode(self):
        import RTC
        data = RTC.Time(0,0)
        test_msg = '''
'RTC::Time':
  sec: 0
  usec: 0
'''.strip()
        self.write_message(test_msg)
