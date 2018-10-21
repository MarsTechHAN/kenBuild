#!/usr/bin/python3                                                                                                                                                                           

import socket   
import base64, uuid          
import os, _thread, subprocess
import zlib,zipfile
import sys

def on_new_client(clientsocket,addr):
    try:
        filename = "temp_rcv_"+str(uuid.uuid3(uuid.NAMESPACE_OID, str(addr)))
        print("[" + filename +"] Connection Received From ",addr)      

        clientsocket.settimeout(30)      

        linkType = clientsocket.recv(4)
        print("[" + filename +"] linkType Received: 0x"+str(linkType.hex()))

        if linkType != b'WUWU':
            print("[ERROR] Unsupport linkType, discounnect...")
            clientsocket.close()
            return
        
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

        zf = zipfile.ZipFile("src/"+filename+".zip", "w", zipfile.ZIP_DEFLATED)
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