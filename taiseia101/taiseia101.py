import sys
import logging
import os
import json

log_level = os.getenv('LOG_LEVEL', 'DEBUG')
numeric_level = getattr(logging, log_level.upper(), None)
if not isinstance(numeric_level, int):
    raise ValueError('Invalid log level: %s' % log_level)
logging.basicConfig(level=numeric_level)

_type_Register = 0x00
_type_AirConditioner = 0x01
_type_Refrigerator = 0x02
_type_WatchingMachine = 0x03
_type_Dehumiditifer = 0x04
_type_Television = 0x05
_type_DryingMachine = 0x06
_type_HeadPumpWaterHeater = 0x07
_type_AirCleaner = 0x08
_type_ElectronicPot = 0x09
_type_OpenDrinkMachine = 0x0a
_type_InductionCooker = 0x0b
_type_Dishwasher = 0x0c
_type_MicrowaveOven = 0x0d
_type_FullHeatSwitch = 0x0e
_type_Fan = 0x0f
_type_GasWaterHeater = 0x10
_type_Lamp = 0x11
_type_SmartMeterGateway = 0xe0
_type_GeneralDevice = 0xf0
_type_Error = 0xff

_cls_HomeAppliances = 0x00
_cls_PowerEquipment = 0x01
_cls_EnergyStorageEquipment = 0x02
_cls_SensorEquipment = 0x03

_srv_Register = 0x00
_srv_ReadDeviceClassID = 0x01
_srv_ReadDeviceProtocolVer = 0x02
_srv_Reserved = 0x03
_srv_ReadDeviceTypeID = 0x04
_srv_ReadDeviceBrand = 0x05
_srv_ReadDeviceModel = 0x06
_srv_ReadDeviceServices = 0x07
_srv_ReadDeviceServicesStatus = 0x08

def get_device_class_name_by_id(class_id):
    current_module = sys.modules[__name__]
    for entry in dir(current_module):
        if entry.find('_cls_') == 0:
            if getattr(current_module,entry) == class_id:
                return entry.replace('_cls_','')
    return ''
            

def get_device_type_name_by_id(type_id):
    current_module = sys.modules[__name__]
    for entry in dir(current_module):
        if entry.find('_type_') == 0:
            if getattr(current_module,entry) == type_id:
                return entry.replace('_type_','')
    return ''

class CommonRequestPocket(object):
    
    def __init__(self,type_id,is_read,service_id,value=0xffff):
        self.type_id = type_id
        self.is_read = True if is_read else False
        self.service_id = service_id
        self.high_byte_data = (value & 0xff00)/0x100
        self.low_byte_data = (value & 0x00ff)
        self.length = 6
        
    def __call__(self):
        pdu = [
            self.length,
            self.type_id,
            (0x7f & self.service_id) if self.is_read else (0x80 | self.service_id),
            self.high_byte_data,
            self.low_byte_data,
            0
            ]
        check_sum = 0
        for x in pdu[:-1]:
            check_sum ^= x
        pdu[-1] = check_sum
        logging.debug('%s pdu: %s' % (self.__class__.__name__,
                                      ','.join('{:02x}'.format(x) for x in pdu)))
        return pdu
    
class CommonResponsePocket(object):
    
    def __init__(self,data):
        self.bytes = data
        self.length = data[0]
        self.type_id = data[1]
        if self.type_id != _type_Register:
            self.service_id = data[2] & 0x7f
            self.data = data[3:-1]
        else:
            self.data = data[2:-1]
        self.check_sum = data[-1]
        
    def __str__(self):
        obj = {
            'length': self.length,
            'type': {
                'id': self.type_id,
                'name': get_device_type_name_by_id(self.type_id)
                },
            'service_id': getattr(self,'service_id'),
            'data_hex': ','.join('{:02x}'.format(x) for x in self.data)
            }
        return json.dumps(obj,indent=2)
    
class RegisterRequestPocket(CommonRequestPocket):
    
    def __init__(self):
        super(RegisterRequestPocket,self).__init__(
            type_id=_type_Register,
            is_read=True,
            service_id=_srv_Register)

class RegisterResponsePocket(CommonResponsePocket):
    
    def __init__(self,data):
        super(RegisterResponsePocket,self).__init__(data)
        
        self.device_class = {
            'multi_byte_type': True if (data[2] & 0x80) else False,
            'id': (data[2] & 0b00001111)
            }

        self.protocol = {
            'major': data[3],
            'minor': data[4]
            }

        self.fragment_offset = data[5]

        self.type_id = data[6] * 0x100 + data[7]

        try:
            n_zero = data[8:].index(0)
        except:
            logging.error('RegisterResponsePocket parsing brand error')
            raise Exception('RegisterResponsePocket data parsing error')
            
        self.brand = bytearray(data[8:8+n_zero]).decode("utf-8") 
        
        try:
            n_start = 8+n_zero+1
            n_zero = data[n_start:].index(0)
        except:
            logging.error('RegisterResponsePocket parsing model error')
            raise Exception('RegisterResponsePocket data parsing error')

        self.model = bytearray(data[n_start:n_start+n_zero]).decode("utf-8") 
        
        n_start = n_start+n_zero+1
        #pocket.service_pdu_list = []
        self.services = []
        while len(data) > (n_start+3):
            serv_pdu = data[n_start:n_start+3]
            serv = {
                'writable': True if serv_pdu[0] & 0x80 else False,
                'service_id': serv_pdu[0] & 0b01111111,
                'high_byte': serv_pdu[1],
                'low_byte': serv_pdu[2],
                'pdu_hex': ','.join('{:02x}'.format(x) for x in serv_pdu),
                'pdu': serv_pdu
                }
            self.services.append(serv)
            n_start += 3

    def __str__(self):
        obj = {
            'device_class': {
                'multi_byte_type': self.device_class['multi_byte_type'],
                'id': self.device_class['id'],
                'name': get_device_class_name_by_id(self.device_class['id'])
                },
            'protocol': {
                'major': self.protocol['major'],
                'minor': self.protocol['minor']
                },
            'fragment_offset': self.fragment_offset,
            'type': {
                'id': self.type_id,
                'name': get_device_type_name_by_id(self.type_id)
                },
            'brand': self.brand,
            'model': self.model,
            'service_count': len(self.services)
            }
        return json.dumps(obj,indent=2)
    


class DeviceInfoReadPocket(CommonRequestPocket):
    pass

class DeviceStatusReadPocket(CommonRequestPocket):

    def __init__(self,type_id,service_id,value):
        super(DeviceStatusReadPocket,self).__init__(
            type_id=type_id,
            is_read=True,
            service_id=service_id,
            value=value)

class DeviceStatusWritePocket(CommonRequestPocket):
    
    def __init__(self,type_id,service_id,value):
        super(DeviceStatusWritePocket,self).__init__(
            type_id=type_id,
            is_read=False,
            service_id=service_id,
            value=value)

def parse_response_pocket(hex_data):

    try:
        data = [int(x,16) for x in hex_data.split(',')]
    except ValueError:
        logging.error('CommonResponsePocket init hex_data (%s) format error\n' % hex_data)
        return None
    
    if len(data) != data[0]:
        logging.error('CommonResponsePocket init hex_data (%s) length error\n' % hex_data)
        return None
    
    type_id = data[1]
    logging.debug('parse_response_pocket type_id: %s' % type_id)
    
    if type_id == _type_Register:
        pocket = RegisterResponsePocket(data)
    else:
        pocket = CommonResponsePocket(data)
    
    return pocket
