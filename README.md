# kenBuild, A Kendryte K210 Cloud Build Support
This script contains the kenBuild Server End and the KenBuild Client End.

## Sample Usage
### Cloud Build Server
- Now I offer a free server at ```120.55.56.237:23333```, please do not try to attack or run a pressure test. 
- The server is on Aliyun Ease China(Hangzhou), a 4vCPU 4GB RAM Instance.
- The test server is provided "AS IS, WITHOUT WARRANTY OF ANY KIND"; the service availability is no guarantee. 
- The config has been written already to the kenBuild.py, but for now only support FreeRTOS SDK.
### Folder Structure
You don't need to have the SDK at all, but it will nice for your IDE to have proper Syntax High Light and Grammar Check
```
\-kendryte-freertos-sdk
  -kenBuild.py
  \-src
    \-hello_world
      \-main.cpp
```
### Command to Run
```Bash
python kenBuild.py hello_world
python kenBuild.py --build-only hello_world  #If you only want to build but don't want to run ISP Download.
```
 - If the build success, it will create a Build Folder under the SDK folder, and download the built .bin and symbol file into.
 - If the build fails, it will print the Error log, while downloading the whole build log to the Build Folder.
 
## Requirments
### On Windows
 - Python3(With Crypto if you want to use the Encrypt Function)
 - Install pySerial pip3 package(python -mpip install pyserial)
 - We Suggest to Use the Native Command Line Tool(like Powershell or cmd), since the WSL nor any bash Have No Access on USB Description
 - [Enable the VT100 Support on PS(Powershell) for better experience](https://stackoverflow.com/questions/51680709/colored-text-output-in-powershell-console-using-ansi-vt100-codes)
 
 ### On Linux or Mac
 - Python3(With Crypto if you want to use the Encrypt Function)
 - Install pySerial pip3 package(python -mpip install pyserial)
 - Change the command to python3, if your default python is not referring to python3
