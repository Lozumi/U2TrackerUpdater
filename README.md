# U2TrackerUpdater
批量更新任务Tracker地址中的秘钥
## 原作者：
### qB-U2@杯杯杯杯具(https://gist.github.com/tongyifan/83220b417cffdd23528860ee0c518d15)
### Tr-U2@ITGR(https://gist.github.com/inertia42/f6120d118e47925095dbceb5e8e27272)
### De-U2@種崎敦美(https://github.com/XSky123/dmhy_change_securekey_deluge)
### 整合优化：
### U2@Loid(https://github.com/LoidVC/U2TrackerUpdater)

## 原作者备注
0. 免责声明：程序仅在本地客户端qBittorrent v4.2.5/Transmission v2.94/Deluge v1.3.15上测试通过，运行结果与作者无关
1. 已知bug：从第 48 个请求开始会连续失败 10 次，在管理组修复之前请手动重复执行至所有种子更新完毕，直到显示找到0个未被更新的种子为止

## 优化备注
1.添加交互逻辑
2.整合多客户端
3.本工具仅限用于于个人更新Tracker中的秘钥，禁止利用其进行带宽和运算资源占用、数据挖掘、规律遍历、商业使用或类似的活动。违规操作造成的警告、禁用相关账户，封锁IP、中止或终止API等后果自负责任。

## 使用方法
-1.在 https://u2.dmhy.org/privatetorrents.php 获取API地址
0.在 https://github.com/LoidVC/U2TrackerUpdater/releases 下载最新release
### 使用源码
1.安装依赖：pip install -r requirements.txt
2.运行：python U2TrackerUpdater.py
### 使用执行程序
1.运行U2TrackerUpdater.exe

##更新日志：
1.0(20200826) 适配qB
1.1(20200826) 修复参数输入，优化提示（感谢@vincent-163）
1.2(20200826) 修正依赖项，测试正常
1.3(20200827) 整合qB,Tr,De
