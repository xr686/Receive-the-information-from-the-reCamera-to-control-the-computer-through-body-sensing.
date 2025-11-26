# Receive-the-information-from-the-reCamera-to-control-the-computer-through-body-sensing.
Receive the information from the reCamera to control the computer through body sensing.This program will monitor all UDP information sent from port 5005. Port 5005 was set up by me in Node-RED on reCamera. Once it receives the action information, it will control the computer using the principle of simulated keyboard operations to play games.接收来自reccamera的信息，通过身体感应控制计算机。这个程序将监视从端口5005发送的所有UDP信息。端口5005是我在reCamera的Node-RED中设置的。一旦接收到动作信息，它就会利用模拟键盘操作的原理来控制计算机进行游戏。


使用这个程序，你只需要下载一个控制键盘的依赖项即可：
pip install pynput
