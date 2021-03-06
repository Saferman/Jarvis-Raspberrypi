# -*- coding:utf-8 -*-
#现在先架设IDLE中运行的框架
#采用口令模式
"""所有###前缀或后缀的需要配置"""
###当前功能只有 语音识别对应关系.docx 的 01、09、10、07、05
import serial  #请确保安装了该模块和ASRM08-A驱动
import time,sys
import platform
from extrahelp import diccreate#这里不能用*  不然出错
import threading 
import Queue
###
from tasks import func1  
from tasks import func9
from tasks import func10
from tasks import func7
from tasks import func5
from tasks import func2
###-------------------------------配置
if platform.platform().lower().find('windows')!=-1:
    port = 'com3'
    # port='/dev/ttyUSB0' ###串口位置，在我的电脑上接在不同的位置，串口号不一样.不必修改，我后面做了智能处理
else:
    port='/dev/ttyUSB0'  # 表明是树莓派平台
baud=9600  ###
timeout=0.5  ###
dic=diccreate.taskdic(10)  ###目前支持tasks文件里的func1~func15。最小1，最大FF即255
kouling=0  ###在我测试的时候发现脚本在执行任务和播放完成语音时可能会产生多余串口数据回复

ASR_data_Queue = Queue.Queue()
#
from UNO import UNO
unotask = []


def hexHandle(argv):  #返回串口数据的二位16进制字符类型
    result = ''  
    hLen = len(argv)  
    for i in xrange(hLen):  
        hvol = ord(argv[i])  
        hhex = '%02x'%hvol  
        result += hhex+' '
    return result[0:2]  

'''
def recvdata(serial):  #监视串口是否有返回数据
    while True:
        data=serial.read(8)
        if data=='':
            continue
        else:
            break
        time.sleep(0.02)
    return data
'''


def recvdata(serial):  #监视串口是否有返回数据
    while True:
        data=serial.read(8)
        if data=='':
            continue
        else:
            ASR_data_Queue.put(data)
        time.sleep(0.02)


def task(result,ser,dic):#根据result串口的二位16进制字符从dic中找到需要执行的函数
    #不能有return，他所调用的func系列函数也不能有return
    global kouling
    try:
        time.sleep(2)#为了给语音足够的时间说完而不和完成任务的语音重合
        eval(dic[result])
    except KeyError as e:   #当dic没有此索引的时候出现该错误
        print str(e)+' is not a valid key in dic'
    finally:
        #print 'kouling:'+str(kouling)
        kouling=0

class funcparameter(object):

    def __init__(self,ser, unotask):
        self.ser = ser
        self.unotask = unotask 


if __name__=='__main__':
    try:
        #有时候串口不一定是com3，所以做了这个处理
        try:
            ser=serial.Serial(port,baud,timeout=timeout)
        except:
            try:
                ser=serial.Serial('com4',baud,timeout=timeout)
            except:
                try:
                    ser=serial.Serial('com5',baud,timeout=timeout)
                except:
                    print "No com can be used!"
                    sys.exit()
        ser.flushInput()
        ser.flushOutput()
        # --------------------------------------
        from background import setup  
        personalsecurity_check_value = 0
        setup_config = [personalsecurity_check_value]
        setup.setup(ser, setup_config)  ##来自core.setup
        # --------------------------------------    

        myparam = funcparameter(ser, unotask)  #作为所有func函数接受的参

        recv_thread = threading.Thread(target=recvdata,args=(ser,))
        recv_thread.setDaemon(True)
        recv_thread.start()

        UNO = UNO()
        while True:
            ##每次循环先处理UNO相关的的事项
            UNO.monitor(ser)
            UNO.execute(ser, unotask)

            # data =recvdata(ser)
            if ASR_data_Queue.empty():
                continue
            else:
                data = ASR_data_Queue.get()
            result=hexHandle(data)
            if result=='ff':           #如果是口令的回显直接进入下一次数据读取状态
                kouling=1
                continue
            else:
                if kouling==1:
                    task(result,ser,dic)#01,kai deng,030,$返回数据经前面步骤处理到这为1E
                    setup_config[0] = 1
                else:
                    continue
            
    except KeyboardInterrupt:
        print "you use ctrl+C"
        ser.close()
    #except SerialException:#没有这个异常名
        #print "module is pulled out"
    