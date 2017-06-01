#!/usr/bin/env python

import sys
import os
import logging

log_level = os.getenv('LOG_LEVEL', 'DEBUG')
numeric_level = getattr(logging, log_level.upper(), None)
if not isinstance(numeric_level, int):
    raise ValueError('Invalid log level: %s' % log_level)
FORMAT = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
logging.basicConfig(level=numeric_level,format=FORMAT)
logger = logging.getLogger('panasonic')

import socket
import serial
import serial.threaded
import time
import threading
import Queue
# import requests
# from requests.auth import HTTPBasicAuth
from taiseia101 import taiseia101
from taiseia101 import dehumiditifer

class SocketClientThread(threading.Thread):
    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs=None, verbose=None):
        threading.Thread.__init__(self, group=group, target=target, name=name,
                                  verbose=verbose)
        self.args = args
        self.kwargs = kwargs
        self.client_socket = None
        self.client_ip = None
        self._stop = threading.Event()

    def stop(self):
        self._stop.set()
        self.client_socket.close()
        
    def stopped(self):
        return self._stop.isSet()

    def run(self):
        # More quickly detect bad clients who quit without closing the
        # connection: After 1 second of idle, start sending TCP keep-alive
        # packets every 1 second. If 3 consecutive keep-alive packets
        # fail, assume the client is gone and close the connection.
        client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 1)
        client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 1)
        client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 3)
        client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        client_socket.settimeout(3)
        try:
            while not self.stopped():
                try:
                    data = self.client_socket.recv(1024)
                    if not data:
                        break
                    logger.info('sck client(%s) data: %s' % (self.client_ip,data))
                    if data[:4] == 'exit':
                        self.stop()
                    else:
                        q.put(data)
                except socket.timeout:
                    #logger.debug('sck client(%s) recv timeout, ignore' % (self.client_ip))
                    pass
                except socket.error as msg:
                    logger.error('sck client(%s) ERROR: %s' % (self.client_ip,msg))
                    # probably got disconnected
                    break
        except KeyboardInterrupt:
            logger.error('sck client(%s) KeyboardInterrupt: %s' % (self.client_ip))
        except socket.error as msg:
            logger.error('sck client(%s) ERROR: %s' % (self.client_ip,msg))
        finally:
            logger.info('sck client(%s) Disconnected' % (self.client_ip))
            self.client_socket.close()
            self.stop()
        
class SerialQueueThread(threading.Thread):
    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs=None, verbose=None):
        threading.Thread.__init__(self, group=group, target=target, name=name,
                                  verbose=verbose)
        self.args = args
        self.kwargs = kwargs
        self.queue = None
        self.queue_read_timeout = 3 # 3 seconds
        self.ser = None
        self._stop = threading.Event()
        return
    
    def stop(self):
        logger.debug('SerialQueueThread event set')
        self._stop.set()
        
    def stopped(self):
        return self._stop.isSet()
    
    def run(self):
        logger.debug('serial queue thread (daemon: %s) running ...' % self.daemon)
        while True:
            cmd = ''
            try:
                cmd = self.queue.get(timeout=self.queue_read_timeout)
                cmd = cmd.replace('\r\n','')
                logger.debug('recv queue cmd: %s' % cmd)
                if not self.ser is None:
                    if cmd.lower() == 'register':
                        pocket = taiseia101.RegisterRequestPocket()
                        data = pocket()
                    elif cmd.lower().find('power') == 0:
                        if cmd.lower() == 'power':
                            pocket = dehumiditifer.service_read(dehumiditifer._srv_PowerControl)
                        elif cmd.lower() == 'poweron':
                            pocket = dehumiditifer.service_write(dehumiditifer._srv_PowerControl, 
                                                                 dehumiditifer.ServicePower.ON)
                        elif cmd.lower() == 'poweroff':
                            pocket = dehumiditifer.service_write(dehumiditifer._srv_PowerControl, 
                                                                 dehumiditifer.ServicePower.OFF)
                        data = pocket()
                    elif cmd.lower().find('opmode') == 0:
                        if cmd.lower() == 'opmode':
                            pocket = dehumiditifer.service_read(dehumiditifer._srv_OpModeConfig)
                        else:
                            mode_id = cmd.lower().replace('opmode', '').strip()
                            pocket = dehumiditifer.service_write(dehumiditifer._srv_OpModeConfig, 
                                                                 int(mode_id))
                        data = pocket()
                    elif cmd.lower().find('fanlevel') == 0:
                        if cmd.lower() == 'fanlevel':
                            pocket = dehumiditifer.service_read(dehumiditifer._srv_FanLevelConfig)
                        else:
                            level = cmd.lower().replace('fanlevel', '').strip()
                            pocket = dehumiditifer.service_write(dehumiditifer._srv_FanLevelConfig, 
                                                                 int(level))
                        data = pocket()
                    elif cmd.lower().find('swinglevel') == 0:
                        if cmd.lower() == 'swinglevel':
                            pocket = dehumiditifer.service_read(dehumiditifer._srv_SwingLevelConfig)
                        else:
                            level = cmd.lower().replace('swinglevel', '').strip()
                            pocket = dehumiditifer.service_write(dehumiditifer._srv_SwingLevelConfig, 
                                                                 int(level))
                        data = pocket()
                    elif cmd.lower().find('timehr') == 0:
                        if cmd.lower() == 'timehr':
                            pocket = dehumiditifer.service_read(dehumiditifer._srv_OpTimeHrConfig)
                        else:
                            hours = cmd.lower().replace('timehr', '').strip()
                            pocket = dehumiditifer.service_write(dehumiditifer._srv_OpTimeHrConfig, 
                                                                 int(hours))
                        data = pocket()
                    elif cmd.lower().find('dehumidify') == 0:
                        if cmd.lower() == 'dehumidify':
                            pocket = dehumiditifer.service_read(dehumiditifer._srv_DehumiditiferLevelConfig)
                        else:
                            level = cmd.lower().replace('dehumidify', '').strip()
                            pocket = dehumiditifer.service_write(dehumiditifer._srv_DehumiditiferLevelConfig, 
                                                                 int(level))
                        data = pocket()
                    elif cmd.lower().find('airclean') == 0:
                        if cmd.lower() == 'airclean':
                            pocket = dehumiditifer.service_read(dehumiditifer._srv_AirCleanModeConfig)
                        else:
                            level = cmd.lower().replace('airclean', '').strip()
                            pocket = dehumiditifer.service_write(dehumiditifer._srv_AirCleanModeConfig, 
                                                                 int(level))
                        data = pocket()
                    elif cmd.lower().find('sound') == 0:
                        if cmd.lower() == 'sound':
                            pocket = dehumiditifer.service_read(dehumiditifer._srv_SAAControlSound)
                        else:
                            value = cmd.lower().replace('sound', '').strip()
                            pocket = dehumiditifer.service_write(dehumiditifer._srv_SAAControlSound, 
                                                                 int(value))
                        data = pocket()
                    else:
                        # hex string to byte array
                        try:
                            data = bytearray([int(entry,16) for entry in cmd.split(',')])
                        except ValueError:
                            data = []
                            logger.warning('recv HA cmd format invalue: %s, ignore' % cmd)
                    
                    if len(data) > 0:
                        data_hex = ','.join('{:02x}'.format(x) for x in data)
                        logger.debug('send bytes command %s' % data_hex)
                        ser.write(data)
                    else:
                        logger.debug('no data for serial port')

            except Queue.Empty:
                #logger.debug('serial cmd queue recv timeout')
                pass
            finally:
                if self.stopped():
                    break
        logger.debug('-- serial queue thread exit --')
    
class SerialToNet(serial.threaded.Protocol):
    """serial->socket"""

    buff = []
    
    def __init__(self):
        self.client_threads = []
        self.buff = []
        self.connected = False
        self.cmd_queue = None

    def __call__(self):
        return self
    
    def connection_made(self, transport):
        self.connected = True
        logger.debug('serial connect made')
        
    def connection_lost(self, exc):
        self.connected = False
        logger.warning('serial connect lost: %s' % str(exc))

    def data_received(self, data):
        data_hex = ','.join('{:02x}'.format(ord(x)) for x in data)
        logger.debug('serial recv %s' % (data_hex))
        for x in data:
            #logger.debug('buff append data %s len %s' % (type(x),len(x)))
            self.buff.append(ord(x))
            if self.buff[0] == len(self.buff):
#                 from panasonic.taiseia101 import taiseia101
                logger.debug('data frame receive complete')
                data_hex = ','.join('{:02x}'.format(x) for x in self.buff)
                logger.info('data frame hex: %s' % data_hex)
#                 pocket = taiseia101.parse_response_pocket(data_hex)
                pocket = dehumiditifer.parse_response_pocket(data_hex)
                logger.debug('recv pocket: %s, %s' % (pocket.__class__.__name__,str(pocket)))
#                 if pocket.device_type['id'] == 0x13:
#                     for pdu in pocket.service_pdu_list:
#                         service = taiseia101.fan.FanServie(pdu)
#                         logger.info('fan service: %s\n' % str(service.getJson()))
                self.buff = []
                
#                 logger.debug('send data frame hex string for all socket clients')
#                 for sck_client in self.client_threads:
#                     sck_client.client_socket.sendall(str(pocket)+'\n')


if __name__ == '__main__':  # noqa
    import argparse

    parser = argparse.ArgumentParser(
        description='TaiSEIA SA Socket Server',
        epilog="""\
NOTE: no security measures are implemented. Anyone can remotely connect
to this service over the network.

Only one connection at once is supported. When the connection is terminated
it waits for the next connect.
""")

    parser.add_argument(
        'SERIALPORT',
        help="serial port name")

    parser.add_argument(
        'BAUDRATE',
        type=int,
        nargs='?',
        help='set baud rate, default: %(default)s',
        default=9600)

    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='suppress non error messages',
        default=False)

    parser.add_argument(
        '--develop',
        action='store_true',
        help='Development mode, prints Python internals on errors',
        default=False)

    group = parser.add_argument_group('serial port')

    group.add_argument(
        "--parity",
        choices=['N', 'E', 'O', 'S', 'M'],
        type=lambda c: c.upper(),
        help="set parity, one of {N E O S M}, default: N",
        default='N')

    group.add_argument(
        '--rtscts',
        action='store_true',
        help='enable RTS/CTS flow control (default off)',
        default=False)

    group.add_argument(
        '--xonxoff',
        action='store_true',
        help='enable software flow control (default off)',
        default=False)

    group.add_argument(
        '--rts',
        type=int,
        help='set initial RTS line state (possible values: 0, 1)',
        default=None)

    group.add_argument(
        '--dtr',
        type=int,
        help='set initial DTR line state (possible values: 0, 1)',
        default=None)

    group = parser.add_argument_group('network settings')

    group.add_argument(
        '-P', '--localport',
        type=int,
        help='local TCP port, default: %(default)s',
        default=7778)

    args = parser.parse_args()
    
    # connect to serial port
    ser = serial.serial_for_url(args.SERIALPORT, do_not_open=True)
    ser.baudrate = args.BAUDRATE
    ser.parity = args.parity
    ser.rtscts = args.rtscts
    ser.xonxoff = args.xonxoff
    
    if args.rts is not None:
        ser.rts = args.rts

    if args.dtr is not None:
        ser.dtr = args.dtr

    if not args.quiet:
        logger.info(
            '--- TCP/IP to Serial redirect on {p.name}  {p.baudrate},{p.bytesize},{p.parity},{p.stopbits} ---\n'
            '--- type Ctrl-C / BREAK to quit\n'.format(p=ser))

    try:
        ser.open()
    except serial.SerialException as e:
        logger.error('Could not open serial port {}: {}\n'.format(ser.name, e))
        sys.exit(1)
        
    # setup serial port command queue
    q = Queue.Queue()
    client_threads = []
 
    # setup serial cmd receiver thread
    ser_q_worker = SerialQueueThread()
    ser_q_worker.ser = ser
    ser_q_worker.queue = q
    ser_q_worker.start()

    # setup serial port data receiver thread
    ser_to_net = SerialToNet()
    ser_to_net.cmd_queue = q
    ser_to_net.client_threads = client_threads
    serial_worker = serial.threaded.ReaderThread(ser, ser_to_net)
    serial_worker.start()
    
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.settimeout(1)
    srv.bind(('', args.localport))
    srv.listen(2)

    
    try:
        intentional_exit = False
        logger.info('Waiting for connection on {}...\n'.format(args.localport))
        while True:
            try:
                #logger.info('Waiting for connection on {}...\n'.format(args.localport))
                client_socket, addr = srv.accept()
                logger.info('Connected by {}\n'.format(addr))
                
                client_thread = SocketClientThread()
                client_thread.client_socket = client_socket
                client_thread.client_ip = addr[0]
                client_thread.start()
                client_threads.append(client_thread)
            except socket.timeout:
                #logger.debug('sck serv accept timeout, check serial connnection')
                if ser_to_net.connected:
                    pass
                else:
                    logger.warning('serial connect lost')
                    raise KeyboardInterrupt
            
            for t in client_threads:
                if t.stopped():
                    logger.debug('remove stopped client sck thread (%s)' % t.client_ip)
                    client_threads.remove(t)
            
    except KeyboardInterrupt:
        pass

    logger.debug('stoping serial_worker thread ...')
    serial_worker.stop()
    serial_worker.join()

    logger.debug('stoping ser_q_worker thread ...')
    ser_q_worker.stop()
    ser_q_worker.join()
    
    logger.debug('stoping sck_client threads')
    for t in client_threads:
        logger.debug('close sck_client(%s) connection' % t.client_ip)
        t.stop()
        t.join()

    logger.warning('--- exit ---')
    sys.exit(1)
