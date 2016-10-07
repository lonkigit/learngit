from urllib import request
import time
import asyncio

def write_ip():
    file = open('point.json','w')
    ipList = open("loginIp.json","r").read()
    ips = (eval(ipList))['RECORDS']
    for ip in ips:
        #baidu map url api
        baiduMapApi = "http://api.map.baidu.com/location/ip?ak=Zf4nnTviyLkyddxNyu5Q32AKpDbKTe1i&ip=" + ip['login_ip'] + "&coor=bd09ll"
        with request.urlopen(baiduMapApi) as f:
            resp = f.read()
            respDict = eval(resp)
            if(respDict['status'] == 0):
                lon = respDict['content']['point']['x']
                lat = respDict['content']['point']['y']

                #write lon,lat
                str = '{"lon":' + lon + ', "lat":' + lat + '},\n'
                file.write(str)

    file.close()

write_ip()


