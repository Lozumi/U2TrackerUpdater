# U2TrackerUpdater
批量更新任务Tracker地址中的秘钥，支持qBittorrent,Transmission,Deluge三大客户端。
## 原作者：
qB-U2@杯杯杯杯具(https://gist.github.com/tongyifan/83220b417cffdd23528860ee0c518d15)  
Tr-U2@ITGR(https://gist.github.com/inertia42/f6120d118e47925095dbceb5e8e27272)  
De-U2@種崎敦美(https://github.com/XSky123/dmhy_change_securekey_deluge)  
### 整合优化：
U2@Loid(https://github.com/LoidVC/U2TrackerUpdater)
### 感谢帮助：
U2@vincent-163(PR#1),U2@x琳x(PR#3),U2@Noira(论坛#139477)

## 原作者备注
0. 免责声明：程序仅在本地客户端qBittorrent v4.2.5/Transmission v2.94/Deluge v1.3.15上测试通过，运行结果与作者无关  
1. 已知bug：从第 48 个请求开始会连续失败 10 次，在管理组修复之前请手动重复执行至所有种子更新完毕，直到显示找到0个未被更新的种子为止  
## 优化备注
1. 添加交互逻辑  
2. 整合多客户端  
3. 本工具仅限用于于个人更新Tracker中的秘钥，禁止利用其进行带宽和运算资源占用、数据挖掘、规律遍历、商业使用或类似的活动。违规操作造成的警告、禁用相关账户，封锁IP、中止或终止API等后果自负责任。 

## 使用方法
1. 在 https://u2.dmhy.org/privatetorrents.php 获取API地址
2. 在 https://github.com/LoidVC/U2TrackerUpdater/releases 下载最新release
### 使用源码
1. 安装依赖：pip install -r requirements.txt  
2. 运行：python U2TrackerUpdater.py  
### 使用执行程序
1. 运行U2TrackerUpdater.exe

## 更新日志：
### 1.0(20200826)
1.初始版本，优化适配qB客户端  
### 1.1(20200826)
1.修复参数传入  
2.优化提示（感谢U2@vincent-163 PR#1）  
### 1.2(20200826)
1.添加依赖库 qbittorrent
### 1.3(20200827)【重大更新】
1.整合qB,Tr,De客户端  
2.优化交互逻辑  
### 1.4(20200827)
1.修正Deluge端口数据类型 
### 1.5(20200829)
1.兼容非中文系统（感谢U2@x琳x PR#3）  
2.重写qB获取种子hash值的逻辑（感谢U2@Noira 论坛#139477）  
### 1.6(20200831)【重大更新】
1.代码重构，合并重复函数（感谢U2@Rhilip PR#4）  
2.修复Transmission客户端因无 tracker 属性导致的失败（参考论坛#139514）（感谢U2@soleil PR#5）  
3.更新Transmission库文件（感谢Github@ThunderMonkey PR#6）  
