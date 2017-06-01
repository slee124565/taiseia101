
import sys
from taiseia101 import taiseia101
from taiseia101 import dehumiditifer

if __name__ == '__main__':
    
    #-> test RegisterRequestPocket
#     pocket = taiseia101.RegisterRequestPocket()
#     pdu = pocket()
#     hex_data = ','.join('{:02x}'.format(x) for x in pdu)
#     sys.stderr.write('%s\n' % hex_data)

    #-> test RegisterResponsePocket
#     hex_data = '45,00,00,04,00,03,00,04,50,61,6e,61,73,6f,6e,69,63,00,46,59,54,57,2d,30,35,37,36,30,31,32,31,00,80,00,03,81,00,7f,82,00,0c,84,00,06,07,00,00,89,00,0f,0a,00,00,8d,00,03,8e,00,0f,12,00,00,98,00,03,9d,00,00,d6'
#     pocket = taiseia101.parse_response_pocket(hex_data)
#     sys.stderr.write('%s\n' % str(pocket))

    #-> test taiseia101.dehumiditifer
    pocket = dehumiditifer.ServicePowerRequest(True)
    pdu = pocket()
    hex_data = ','.join('{:02x}'.format(x) for x in pdu)
    sys.stderr.write('%s\n' % hex_data)
    pocket = dehumiditifer.ServicePowerRequest(False)
    pdu = pocket()
    hex_data = ','.join('{:02x}'.format(x) for x in pdu)
    sys.stderr.write('%s\n' % hex_data)
    