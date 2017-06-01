
import sys
import json
import taiseia101
import logging
import os

log_level = os.getenv('LOG_LEVEL', 'DEBUG')
numeric_level = getattr(logging, log_level.upper(), None)
if not isinstance(numeric_level, int):
    raise ValueError('Invalid log level: %s' % log_level)
logging.basicConfig(level=numeric_level)

_srv_PowerControl = 0x00
_srv_OpModeConfig = 0x01
_srv_OpTimeHrConfig = 0x02
_srv_RelativeHumidityConfig = 0x03
_srv_DehumiditiferLevelConfig = 0x04
_srv_DryLevelConfig = 0x05
_srv_IndoorTempDisplay = 0x06
_srv_IndoorHumidityDisplay = 0x07
_srv_AutoSwingOnOff = 0x08
_srv_SwingLevelConfig = 0x09
_srv_WaterFullDisplay = 0x0a
_srv_CleanNotify = 0x0b
_srv_LightSecenConfig = 0x0c
_srv_AirCleanModeConfig = 0x0d
_srv_FanLevelConfig = 0x0e
_srv_SideFan = 0x0f
_srv_SoundConfig = 0x10
_srv_DefrostingDisplay = 0x11
_srv_ErrTextDisplay = 0x12
_srv_Mildew = 0x13
_srv_HumidityHighNotify = 0x14
_srv_HumidityHighValueConfig = 0x15
_srv_DashboardLock = 0x16
_srv_ControlSuspend = 0x17
_srv_SAAControlSound = 0x18
_srv_OpCurrent = 0x19
_srv_OpVoltage = 0x1a
_srv_OpWattFactor = 0x1b
_srv_RealTimeWatt = 0x1c
_srv_TotalWatt = 0x1d
_srv_EngMode = 0x50
_srv_Reserved = 0x7f

def get_device_service_name_by_id(service_id):
    current_module = sys.modules[__name__]
    for entry in dir(current_module):
        if entry.find('_srv_') == 0:
            if getattr(current_module,entry) == service_id:
                return entry.replace('_srv_','')
    return ''

class RegisterPocket(taiseia101.RegisterResponsePocket):
    
    def __init__(self, data):
        taiseia101.RegisterResponsePocket.__init__(self, data)
        for service in self.services:
            service['service_name'] = get_device_service_name_by_id(service['service_id'])
    
    def __str__(self):
        obj = json.loads(taiseia101.RegisterResponsePocket.__str__(self))
        obj['services'] = self.services
        del obj['service_count']
        return json.dumps(obj,indent=2)    
        
class ResponsePocket(taiseia101.CommonResponsePocket):
    
    def __init__(self,data):
        super(ResponsePocket,self).__init__(data)
        self.service_name = get_device_service_name_by_id(self.service_id)
    
    def __str__(self):
        obj = json.loads(taiseia101.CommonResponsePocket.__str__(self))
        obj['service_name'] = self.service_name
        return json.dumps(obj,indent=2)    

class ServicePower:
    ON  = 1
    OFF = 0

class ServiceOpMode:
    AUTO_DEHUMIDITIFY           = 0
    CONIFG_DEHUMIDITIFY         = 1
    CONTINUE_DEHUMIDITIFY       = 2
    DRY_CLOTHE                  = 3
    AIR_CLEAN                   = 4
    MILDEW                      = 5
    FAN                         = 6
    HUMAN_CONFORT               = 7
    LOW_HUMIDITIFER_DRY         = 8

class ServiceLevelBase(object):
    LEVEL_0     = 0
    LEVEL_1     = 1
    LEVEL_2     = 2
    LEVEL_3     = 3
    LEVEL_4     = 4
    LEVEL_5     = 5
    LEVEL_6     = 6
    LEVEL_7     = 7
    LEVEL_8     = 8
    LEVEL_9     = 9
    LEVEL_10    = 10
    LEVEL_11    = 11
    LEVEL_12    = 12
    LEVEL_13    = 13
    LEVEL_14    = 14
    LEVEL_15    = 15
        
class ServiceFanLevel(ServiceLevelBase):
    pass

class ServiceSwingLevel(ServiceLevelBase):
    pass

class ServicePercentBase(object):
    PERCENT_0   = 0
    PERCENT_99  = 99

class ServiceDehumiditiferLevel(ServiceLevelBase):
    pass

class ServiceSAAControlSound:
    ON  = 0
    OFF = 1

def service_read(service_id):
    packet = taiseia101.DeviceStatusReadPocket(
        type_id = taiseia101._type_Dehumiditifer,
        service_id = service_id,
        value = 0xffff
        )
    return packet
    
def service_write(service_id,value):
    packet = taiseia101.DeviceStatusWritePocket(
        type_id=taiseia101._type_Dehumiditifer,
        service_id=service_id,
        value=int(value)
        )
    return packet

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
    
    if type_id == taiseia101._type_Register:
        pocket = RegisterPocket(data)
    else:
        pocket = ResponsePocket(data)
    
    return pocket
