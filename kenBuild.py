import socket, os               # Import socket module
import zlib,zipfile
import tempfile
import argparse
import subprocess
import isp_auto as isp
import serial.tools.list_ports
import sys, time
import binascii

BASH_TIPS = dict(NORMAL='\033[0m',BOLD='\033[1m',DIM='\033[2m',UNDERLINE='\033[4m',
                    DEFAULT='\033[39', RED='\033[31m', YELLOW='\033[33m', GREEN='\033[32m',
                    BG_DEFAULT='\033[49m', BG_WHITE='\033[107m')

ERROR_MSG   = BASH_TIPS['RED']+BASH_TIPS['BOLD']+'[ERROR]'+BASH_TIPS['NORMAL']
WARN_MSG    = BASH_TIPS['YELLOW']+BASH_TIPS['BOLD']+'[WARN]'+BASH_TIPS['NORMAL']
INFO_MSG    = BASH_TIPS['GREEN']+BASH_TIPS['BOLD']+'[INFO]'+BASH_TIPS['NORMAL']


def kenBuild(project_name):
    s = socket.socket()         # Create a socket object
    host = "120.55.56.237" # Get local machine name
    port = 23333                 # Reserve a port for your service.

    print("[INFO] THE SOFTWARE IS PROVIDED `AS IS`, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED")
    print("[INFO] Connecting to Cloud Build System")
    s.connect((host, port))

    print("[INFO] Cloud Build System Connected... Packing Files")

    with tempfile.TemporaryDirectory() as tmpdirname:

        zf = zipfile.ZipFile(tmpdirname + "/kenBuild_prog.zip", "w", zipfile.ZIP_DEFLATED)

        for root, dirs, files in os.walk("src/" + project_name):
            for file in files:
                zf.write(os.path.join(root, file))
        
        zf.close()

        f = open(tmpdirname + "/kenBuild_prog.zip",'rb')
        size = os.stat(tmpdirname + "/kenBuild_prog.zip").st_size
        s.send(b'WUWU') # 4 Bytes Test Build Type Tag

        dataSize = size.to_bytes(4, byteorder='big')
        s.send(dataSize) # 4 Bytes File Size

        while(size > 0): 
            if size > 2048:
                readSize = 2048
            else:
                readSize = size    
            l = f.read(readSize)  
            s.send(l)
            size = size - len(l)

        f.close()

    print("[INFO] Waiting for Cloud Build System Finish.\nIt may takes as many as 3mins depends on your program.")
    
    linkType = s.recv(4)
    if linkType == b'MEOW':
        buildStatus = True
        print("[INFO] Build Success, downloading symbol & program files.")
    else:
        buildStatus = False
        print("[INFO] Build Fail, downloading log files, linkType:",linkType)
    
    dataSize = s.recv(4)
    size = int.from_bytes(dataSize, byteorder='big')

    with tempfile.TemporaryDirectory() as tmpdirname: 
        f = open(tmpdirname + "/kenBuild_bin.zip","wb")
        
        while(size > 0): 
            if size > 2048:
                readSize = 2048
            else:
                readSize = size             
            l = s.recv(readSize)  
            f.write(l)
            size = size - len(l)
        
        f.close()
        try:
            os.mkdir("build/")
        except:
            pass

        zf = zipfile.ZipFile(tmpdirname + "/kenBuild_bin.zip", "r")
        for name in zf.namelist():
            if "_log.txt" in name:
                data = zf.read(name)
                print("[INFO] ==========Build Log From Build System==========")
                print(data.decode("utf-8"))
                print("[INFO] ===============================================")

                logf = open("build/"+project_name+"_log.txt", "wb")
                logf.write(data)
                logf.close()
            else:
                if ".bin" in name:
                    data = zf.read(name)
                    elff = open("build/"+project_name+".bin", "wb")
                    elff.write(data)
                    elff.close()
                else:
                    data = zf.read(name)
                    binf = open("build/"+project_name, "wb")
                    binf.write(data)
                    binf.close()
        zf.close()
    s.close()
    if buildStatus == False:
        sys.exit(1)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", help="COM Port", default="DEFAULT")
    parser.add_argument("-c", "--chip", help="SPI Flash type, 1 for in-chip, 0 for on-board", default=1)
    parser.add_argument("-b", "--baudrate", type=int, help="UART baudrate for uploading firmware", default=115200)
    parser.add_argument("-l", "--bootloader", help="bootloader bin path", required=False, default=None)
    parser.add_argument("-k", "--key", help="AES key in hex, if you need encrypt your firmware.", required=False, default=None)
    parser.add_argument("-v", "--verbose", help="increase output verbosity", default=False,
                        action="store_true")
    parser.add_argument("firmware", help="Project Name in src/ Folder")

    args = parser.parse_args()
    kenBuild(args.firmware)

    if args.port == "DEFAULT":
        try:
            list_port_info = next(serial.tools.list_ports.grep(isp.VID_LIST_FOR_AUTO_LOOKUP)) #Take the first one within the list
            print(INFO_MSG,"COM Port Auto Detected, Selected ",list_port_info.device,BASH_TIPS['DEFAULT'])
            _port = list_port_info.device
        except StopIteration:
            print(ERROR_MSG,"No vaild COM Port found in Auto Detect, Check Your Connection or Specify One by"+BASH_TIPS['GREEN']+'`--port/-p`',BASH_TIPS['DEFAULT'])
            sys.exit(1)
    else:
        _port = args.port
        print(INFO_MSG,"COM Port Selected Manually: ",_port,BASH_TIPS['DEFAULT'])

    loader = isp.MAIXLoader(port=_port, baudrate=args.baudrate)

    # 1. Greeting.
    print(INFO_MSG,"Trying to Enter the ISP Mode...",BASH_TIPS['DEFAULT'])
    
    retryCount = 0

    while 1:
        retryCount = retryCount + 1
        if retryCount > 15:
            print("\n" + ERROR_MSG,"No vaild Kendryte K210 found in Auto Detect, Check Your Connection or Specify One by"+BASH_TIPS['GREEN']+'`-p '+('/dev/ttyUSB0', 'COM3')[sys.platform == 'win32']+'`',BASH_TIPS['DEFAULT'])
            sys.exit(1)
        try:
            print('.', end='')
            loader.reset_to_isp_dan()
            loader.greeting()
            break
        except isp.TimeoutError:
            pass
            
        try:
            print('_', end='')
            loader.reset_to_isp_kd233()
            loader.greeting()
            break
        except isp.TimeoutError:
            pass
    timeout = 3  
    print()
    print(isp.INFO_MSG,"Greeting Message Detected, Start Downloading ISP",isp.BASH_TIPS['DEFAULT'])
    # 2. flash bootloader and firmware
    try:
        firmware_bin = open("build/" + args.firmware + ".bin", 'rb')
    except FileNotFoundError:
        print(isp.ERROR_MSG,'Unable to find the firmware at ', "build/" + args.firmware + ".bin", BASH_TIPS['DEFAULT'])
        sys.exit(1)

    # install bootloader at 0x80000000
    if args.bootloader:
        loader.install_flash_bootloader(open(args.bootloader, 'rb').read())
    else:
        loader.install_flash_bootloader(isp.ISP_PROG)

    loader.boot()

    print(INFO_MSG,"Wait For 1sec for ISP to Boot",BASH_TIPS['DEFAULT'])

    time.sleep(2)

    loader.flash_greeting()

    loader.init_flash(args.chip)

    if args.key:
        aes_key = binascii.a2b_hex(args.key)
        if len(aes_key) != 16:
            raise ValueError('AES key must by 16 bytes')

        loader.flash_firmware(firmware_bin.read(), aes_key=aes_key)
    else:
        loader.flash_firmware(firmware_bin.read())

    # 3. boot
    loader.reset_to_boot()
    print(INFO_MSG,"Rebooting...",BASH_TIPS['DEFAULT'])

    try:
        while 1:
            out = b''
            while loader._port.inWaiting() > 0:
                out += loader._port.read(1)
            print("".join(map(chr, out)), end='')
    except KeyboardInterrupt:
        sys.exit(0)


