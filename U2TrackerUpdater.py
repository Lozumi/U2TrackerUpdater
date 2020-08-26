# U2TrackerUpdater
# 批量更新任务Tracker地址中的秘钥
# 原作者：U2@杯杯杯杯具(https://gist.github.com/tongyifan/83220b417cffdd23528860ee0c518d15)
# 优化：U2@Loid(https://github.com/LoidVC/U2TrackerUpdater)

# 原作者备注
# 0. 免责：仅在本人的qBittorrent v4.1.8上测试通过，本人不承担任何责任
# 1. 安装依赖： pip3 install requests python-qbittorrent
# 2. 修改代码开头的apikey和qbittorrent_config
# 3. 运行： python3 u2.py
# 4. 中间有报错就再运行，直到显示找到0个未被更新的种子为止

# 优化备注
# 必要参数改为命令行输入

import json
import os
import time

import requests
from qbittorrent import Client
print("# U2TrackerUpdater\n# 批量更新任务Tracker地址中的秘钥\n# 原作者：U2@杯杯杯杯具(https://gist.github.com/tongyifan/83220b417cffdd23528860ee0c518d15)\n# 优化：U2@Loid(https://github.com/LoidVC/U2TrackerUpdater)")
print("# 本工具仅限于个人更新Tracker中的秘钥用，禁止利用其进行带宽和运算资源占用、数据挖掘、规律遍历、商业使用或类似的活动。\n违规操作造成的警告、禁用相关账户，封锁IP、中止或终止API等后果自负责任。")
# todo: edit me
apikey = input("输入秘钥获取API地址（站内查看）：")
cHost = input("输入客户端地址（IP:端口）")
cUser = input("输入客户端用户名：")
cPass = input("输入客户端密码：")
cConfig = '{"host": "'+cHost+'","username": "'+cUser+'","password": "'+cPass+'",}'
qbittorrent_config = json.dumps(cConfig)
# 此行往下不用修改

endpoint = "https://u2.dmhy.org/jsonrpc_torrentkey.php"
u2_tracker = ["daydream.dmhy.best", "tracker.dmhy.org"]
to_tracker = "https://daydream.dmhy.best/announce?secure={}"

qb = Client(qbittorrent_config["host"])
qb.login(qbittorrent_config["username"], qbittorrent_config["password"])


def get_u2_torrents_hash():
    torrents = qb.torrents()

    u2_torrent_info_hash = []
    for torrent in torrents:
        if any([tracker in torrent.get("tracker", "") for tracker in u2_tracker]):
            u2_torrent_info_hash.append(
                {"hash": torrent.get("hash"), "tracker": torrent.get("tracker")}
            )

    return u2_torrent_info_hash


def main():
    u2_torrent_info_hash = get_u2_torrents_hash()
    if not os.path.exists("updated_torrents.json"):
        cached_torrents = []
    else:
        with open("updated_torrents.json", "r") as fp:
            cached_torrents = json.load(fp)

    u2_torrent_info_hash = [
        t for t in u2_torrent_info_hash if t["hash"] not in cached_torrents
    ]

    batch_size = 100
    print(f"找到了{len(u2_torrent_info_hash)}个未被更新的种子～")
    updated_torrents = []
    for i in range(0, len(u2_torrent_info_hash), batch_size):
        print(f"正在获取第{i}到第{i+len(u2_torrent_info_hash[i:i+batch_size])}个种子的新secret key")

        request_data = []
        _index = {}
        for index, torrent in enumerate(u2_torrent_info_hash[i : i + batch_size]):
            request_data.append(
                {
                    "jsonrpc": "2.0",
                    "method": "query",
                    "params": [torrent["hash"]],
                    "id": index,
                }
            )
            _index[index] = torrent
        resp = requests.post(endpoint, params={"apikey": apikey}, json=request_data)

        if resp.status_code == 403:
            print("APIKEY无效，请检查（注意APIKEY不是passkey）")
            exit()

        if resp.status_code == 503:
            while resp.status_code == 503:
                wait_second = int(resp.headers["Retry-After"]) + 5
                print(f"速度过快，将在{wait_second}秒后重试")
                time.sleep(wait_second)
                resp = requests.post(
                    endpoint, params={"apikey": apikey}, json=request_data
                )

        if resp.status_code != 200:
            print(f"意外的错误：{resp.status_code}")

        response_data = resp.json()
        for item in response_data:
            if item.get("error"):
                if item["error"]["code"] == -10003:
                    qb.delete([_index[item["id"]]["hash"]])
                print(item.get("error"))
                continue

            qb._post(
                "torrents/editTracker",
                data={
                    "hash": _index[item["id"]]["hash"],
                    "origUrl": _index[item["id"]]["tracker"],
                    "newUrl": to_tracker.format(item["result"]),
                },
            )
            updated_torrents.append(_index[item["id"]]["hash"])

    with open("updated_torrents.json", "w") as fp:
        json.dump(cached_torrents + updated_torrents, fp)


if __name__ == "__main__":
    main()
