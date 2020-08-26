# U2TrackerUpdater
批量更新任务Tracker地址中的秘钥  
原作者：U2@杯杯杯杯具(https://gist.github.com/tongyifan/83220b417cffdd23528860ee0c518d15)  
优化：U2@Loid(https://github.com/LoidVC/U2TrackerUpdater)  

## 原作者备注
0. 免责：仅在本人的qBittorrent v4.1.8上测试通过，本人不承担任何责任  
1. 中间有报错就再运行，直到显示找到0个未被更新的种子为止  

## 优化备注  
0. 必要参数改为命令行输入  
1. 本工具仅限于个人更新Tracker中的秘钥用，禁止利用其进行带宽和运算资源占用、数据挖掘、规律遍历、商业使用或类似的活动。  
2. 违规操作造成的警告、禁用相关账户，封锁IP、中止或终止API等后果自负责任。  

## 使用方法  
0.下载最新release  
### 使用源码  
1. 安装依赖：`pip install -r requirements.txt`  
2. 运行：`python U2TrackerUpdater.py`  
### 使用执行程序  
1. 运行`U2TrackerUpdater.exe`  
