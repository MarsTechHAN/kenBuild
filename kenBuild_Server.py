#!/usr/bin/python3                                                                                                                                                                           

import socket   
import base64, uuid          
import os, _thread, subprocess
import zlib, lzma, zipfile
import sys
from time import gmtime, strftime

# Request Structure:
#
# Standard Rebuild Mode
# | linkType | Build Type | SDK Type |     SDK Version   | Payload Length | Payload |
#     4B           2B          2B             4B                4B           length     
#
# Increment Build Mode:
# | linkType | Build Type | SDK Type | SDK Version | UUID | Payload Length | Payload |
#     4B           2B          2B          4B        36B        4B           length    
#      \- b'MEOW'-0.0.1 Alpha , b'WUWU'-v0.1 Technincal Preview    #Different Server Structure will not have cross competibility
#                  \- b'CA'-Rebuild Everything,                             b'CB'-Incurement Build, 
#                     b'SA'-Rebuild Everything, but dont download to local, b'SB'-Incr Build, but dont download to local
#                                                                           b'UB'-Incr Build, successive file upload(only upload different files) #Not been implemented yet
#                             \- b'RT' RTOS SDK, b'ST' Standalone SDK  
#                                          \- First 4 bytes of the SDK commits, left as b'AAAA' as using the newest one (feature not supported yet, set as b'AAAA')
#                                                      \- 36B UUID for Incr Build, if it is the first time, left as b'AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAA', get the UUID from the return
#                                                                  -\ 4B of payload length, payload is packed with LZMA
#
# Return Structure:
# | Result Code | UUID | Payload Length | Payload |
#       8B         36B        4B          length
#       \- b'SUC_BULD'-Successfully finish an Rebuild All Mission
#          b'FAL_BULD'-Fail to finish an Rebuild All Mission - Due to compile Error
#          b'CRC_BULD'-Fail to finish an Rebuild All Mission - Due to Payload CRC Check Error
#
#          b'SUC_INCR'-Successfully finish an Increment Build Mission
#          b'UFD_INCR'-Fail to finish an Increment Build Mission - Due to unable to find the corresponding UUID
#          b'FAL_INCR'-Fail to finish an Increment Build Mission - Due to compile Error
#          b'CRC_INCR'-Fail to finish an Increment Build Mission - Due to upload payload CRC Check Error
#           
#          b'VERCMACH'-The server end has been moved to a new protocol, the linkType is nolonger support. 
#          b'FAILEXCD'-The payload length exceed the maximium length (4194304Bytes, or 4MB)        
#          b'BLTPMACH'-The build type is not supported yet (may due to version )
#          b''
#
#          Below has not been implemented yet
#          b'CRD_INCR'-Fail to finish an Increment Build Mission - Due to local file CRC unmatch with .kenBuild.ken
#          b'CRL_INCR'-Fail to finish an Increment Build Mission - Due to upload file CRC unmatch with .kenBuild.ken
#                
#                  \- 36Bytes Unique UUID for this build(build Tree if you are using Incr build.) 
#                           \- Payload Length, when there is no file generated, payload is 0
#

def received_from_socket(socket: socket.socket, lengh: int) -> bytes :
    bSocketBuf = b''
    try:
        while(lengh > len(bSocketBuf)): 

                if (lengh - len(bSocketBuf)) > 2048:
                    iReadLen = 2048
                else:
                    iReadLen = lengh - len(bSocketBuf) 

                bSocketBuf = bSocketBuf + clientsocket.recv(iReadLen)  
    except:       
        return b""

    return bSocketBuf

def get_fotmat_gtime():
    return strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime())

def create_log_entry(clientsocket: socket.socket, addr: str, strUUID: str) -> _io.TextIOWrapper:
    fileLogger = open("/log/log_req_" + strUUID + "_ip_" + addr + ".log", "w")
    fileLogger.write(f"[{get_fotmat_gtime()}][INFO][IO] Log file Created.\n")
    fileLogger.write(f"[{get_fotmat_gtime()}][INFO][IO] Connection Accepted, Addr: {addr}\n")
    fileLogger.flush()
    return fileLogger

def log_entry(entry: _io.TextIOWrapper, level: str, : str, comment: str) -> None:
    fileLogger.write(f"[{get_fotmat_gtime()}][{level}][{}] %s\n")


def on_new_client(clientsocket: socket.socket, addr: str):
    try:  
        clientsocket.settimeout(10)      #Set a maximium wait time
        sUUIDBuild = str(uuid.uuid3(uuid.NAMESPACE_OID, str(addr)))
        #==========linkType Decode==========
        linkType = received_from_socket(clientsocket, 4)
        if linkType is not b'MEOW':
            
        #===================================
        buildType = "reBuild"

        buildType = "AllReBuild"
        filename = "temp_rcv_"+str(uuid.uuid3(uuid.NAMESPACE_OID, str(addr)))
        else
            if linkType == b'BAKA':
                buildType = "IncrBuild"
                buildUUID = clientsocket.recv(36)
                filename = "incr_rcv_" + buildUUID.decode('utf-8')


        if linkType != b'BAKA':
            print("[" + filename +"] Unsupport linkType, discounnect...")
            clientsocket.write(b'LATS')
            clientsocket.flush()
            clientsocket.close()
            return
        else:
            print("[" + filename +"] Unsupport linkType, discounnect...")
            clientsocket.write(b'LATS')

        buildUUID = clientsocket.recv(36)

        print("[" + filename +"] linkType Received: 0x"+str(linkType.hex()))      
        print("[" + filename +"] Connection Received From ",addr)        

        dataSize = clientsocket.recv(4)
        size = int.from_bytes(dataSize, byteorder='big') 
        print("[" + filename +"] dataSize Received: 0x"+str(dataSize.hex())," ", size)

        if size > 4194304: # 4 Bytes Limit, Working for most Program
            print("[ERROR] Unsupport dataSize, discounnect...")
            clientsocket.close()
            return
        
        f = open("src/"+filename+".zip","wb")

        while(size > 0):      
            if size > 2048:
                readSize = 2048
            else:
                readSize = size     
            l = clientsocket.recv(readSize)  
            f.write(l)
            size = size - len(l)
        f.close()

        print("[" + filename +"] Received Length: ",os.stat("src/"+filename+".zip").st_size)
        

        print("[" + filename +"] Stream Received Finish")

        zf = zipfile.ZipFile("src/"+filename+".zip", "r")
        zf.extractall("src/"+filename)
        zf.close()

        print("[" + filename +"] Unzip Finish, Start Compile")
        print("[" + filename +"]  ============= Compile Result ===================")

        returnCode = 0

        try:
            res = subprocess.check_output("mkdir "+ filename +"&& cd "+ filename +" &&" \
            "cmake .. -DPROJ="+ filename +" -DTOOLCHAIN=/root/kendryte-toolchain/bin -DCMAKE_C_COMPILER_WORKS=1 -DCMAKE_CXX_COMPILER_WORKS=1&& make -j4", shell=True)
        except subprocess.CalledProcessError as e:
            print("Subprocess Ended with Build Fail, Return Code ", e.returncode)
            returnCode = e.returncode
            res = e.output

        print("[" + filename +"]  ================================================")

        f = open(filename+"/"+filename+"_log.txt", "wb")

        f.write(res)
        f.close()

        print("[" + filename +"] rePacking", )

        zf = zipfile.ZipFile("src/"+filename+".zip", "w", zipfile.ZIP_LZMA)
        if returnCode == 0:
            print("[" + filename +"] Build Success, Packing the BIN File")
            zf.write(filename+"/" + filename + ".bin", filename+"/"+ ".bin") #For Download
            zf.write(filename+"/" + filename, filename + "/") #For DEBUG
            clientsocket.send(b'MEOW') #protoLink Tag for Success
        else:
            print("[" + filename +"] Build Fail, Packing the LOG File")
            zf.write(filename+"/" + filename + "_log.txt", filename+"/"+ "_log.txt")  
            clientsocket.send(b'WANG') #protoLink Tag for Fail
        zf.close()

        size = os.stat("src/"+filename+".zip").st_size 
        dataSize = size.to_bytes(4, byteorder='big')
        print("[" + filename +"] Sending Back, Size: ", size)

        clientsocket.send(dataSize)
        

        f = open("src/"+filename+".zip",'rb')
        while(size > 0):  
            if size > 2048:
                readSize = 2048
            else:
                readSize = size   
            l = f.read(readSize)  
            clientsocket.send(l)
            size = size - len(l)

        l = f.read(size)
        clientsocket.send(l)
        f.close()

        print("[" + filename +"] Sending Sequence Finish, Cleaning Up...")
        
        #os.remove("src/"+filename+".zip")
        #os.system("rm -r src/" + filename)
        #os.system("rm -r " + filename)
        
        print("[" + filename +"] Disscount Socket")
        clientsocket.close()
    except Exception as e:
        print("[" + filename +"] Unexpeted Error Happened, ", e)
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print("[" + filename +"]",exc_type, fname, exc_tb.tb_lineno)
        try:
            clientsocket.close()
        except Exception:
            pass

s = socket.socket()         
host = socket.gethostname()
port = 23333        

print("[INFO] Socket Connected...")

s.bind((host, port))      
s.listen(5)                 

while True:
   c, addr = s.accept()     
   _thread.start_new_thread(on_new_client,(c,addr))
   print("[INFO] Got Connection From...", addr)

s.close()