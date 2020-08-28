# -*- coding: utf-8 -*
# U2TrackerUpdater-1.5
# 批量更新任务Tracker地址中的秘钥
# 依赖：Python3.8(requests,qbittorrent,python-qbittorrent,transmissionrpc,deluge-client)
# 原作者：
# qB-U2@杯杯杯杯具(https://gist.github.com/tongyifan/83220b417cffdd23528860ee0c518d15)
# Tr-U2@ITGR(https://gist.github.com/inertia42/f6120d118e47925095dbceb5e8e27272)
# De-U2@種崎敦美(https://github.com/XSky123/dmhy_change_securekey_deluge)
# 整合优化：U2@Loid(https://github.com/LoidVC/U2TrackerUpdater)
# 感谢帮助：U2@vincent-163(PR#1),U2@x琳x(PR#3),感谢U2@Noira(论坛#139477)
# 原作者备注
# 0. 免责声明：程序仅在本地客户端qBittorrent v4.2.5/Transmission v2.94/Deluge v1.3.15上测试通过，运行结果与作者无关
# 1. 已知bug：从第 48 个请求开始会连续失败 10 次，在管理组修复之前请手动重复执行至所有种子更新完毕，直到显示找到0个未被更新的种子为止

# 优化备注
# 1.添加交互逻辑
# 2.整合多客户端
# 3.本工具仅限用于于个人更新Tracker中的秘钥，禁止利用其进行带宽和运算资源占用、数据挖掘、规律遍历、商业使用或类似的活动。违规操作造成的警告、禁用相关账户，封锁IP、中止或终止API等后果自负责任。

import json
import os
import time
import requests

from qbittorrent import Client
import transmissionrpc
from deluge_client import DelugeRPCClient

# 声明
print("# U2TrackerUpdater\n# 批量更新任务Tracker地址中的秘钥\n# 原作者：U2@杯杯杯杯具(https://gist.github.com/tongyifan/83220b417cffdd23528860ee0c518d15)\n# Tr-U2@ITGR(https://gist.github.com/inertia42/f6120d118e47925095dbceb5e8e27272)\n# De-U2@種崎敦美(https://github.com/XSky123/dmhy_change_securekey_deluge)\n# 整合优化：U2@Loid(https://github.com/LoidVC/U2TrackerUpdater)")
print('# 原作者备注\n# 0. 免责声明：程序仅在本地客户端qBittorrent v4.2.5/Transmission v2.94/Deluge v1.3.15上测试通过，运行结果与作者无关\n# 1. 已知bug：从第 48 个请求开始会连续失败 10 次，在管理组修复之前请手动重复执行至所有种子更新完毕，直到显示找到0个未被更新的种子为止')
print("# 优化备注\n# 1.添加交互逻辑\n# 2.整合多客户端\n# 3.本工具仅限用于于个人更新Tracker中的秘钥，禁止利用其进行带宽和运算资源占用、数据挖掘、规律遍历、商业使用或类似的活动。违规操作造成的警告、禁用相关账户，封锁IP、中止或终止API等后果自负责任。")
termDes = input('# 我已阅读并同意上述条款（Y/N）：')
if termDes != 'Y':
    exit()

def c_qB():
    apikey = input("输入APIKEY（站内查看API地址中的apikey=后面的部分）：")
    cHost = input("输入客户端地址（http://IP:端口）：")
    cUser = input("输入客户端用户名：")
    cPass = input("输入客户端密码：")
    qbittorrent_config = {"host":cHost,"username":cUser,"password":cPass}
    # 此行往下不用修改

    endpoint = "https://u2.dmhy.org/jsonrpc_torrentkey.php"
    u2_tracker = ["daydream.dmhy.best", "tracker.dmhy.org"]
    to_tracker = "https://daydream.dmhy.best/announce?secure={}"

    qb = Client(qbittorrent_config["host"])
    qb.login(qbittorrent_config["username"], qbittorrent_config["password"])


    # def get_u2_torrents_hash():
    #     torrents = qb.torrents()

    #     u2_torrent_info_hash = []
    #     for torrent in torrents:
    #         if any([tracker in torrent.get("tracker", "") for tracker in u2_tracker]):
    #             u2_torrent_info_hash.append(
    #                 {"hash": torrent.get("hash"), "tracker": torrent.get("tracker")}
    #             )

    #     return u2_torrent_info_hash

    #感谢U2@Noira
    def get_u2_torrents_hash():
        torrents = qb.torrents()

        u2_torrent_info_hash = []
        for torrent in torrents:
            hash = torrent["hash"]
            trackers = qb.get_torrent_trackers(hash)

            for tker in trackers:
                if any([tracker in tker["url"] for tracker in u2_tracker]):
                    u2_torrent_info_hash.append(
                        {"hash": hash, "tracker": tker["url"] }
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

            if resp.status_code == 503:
                while resp.status_code == 503:
                    wait_second = int(resp.headers["Retry-After"]) + 5
                    print(f"速度过快，将在{wait_second}秒后重试")
                    time.sleep(wait_second)
                    resp = requests.post(
                        endpoint, params={"apikey": apikey}, json=request_data
                    )

            if resp.status_code == 403:
                print("APIKEY无效，请检查（注意APIKEY不是passkey）")
                exit()

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
    return 0

def c_Tr():
    apikey = input("输入APIKEY（站内查看API地址中的apikey=后面的部分）：")
    cHost = input("输入客户端IP（http://IP）：")
    cPort = input("输入客户端端口（通常为9091）：")
    cUser = input("输入客户端用户名：")
    cPass = input("输入客户端密码：")
    qbittorrent_config = {"host":cHost,"username":cUser,"password":cPass}
    transmission_config = {"host": cHost,"port": cPort,"username": cUser,"password": cPass}
    # 此行往下不用修改

    endpoint = "https://u2.dmhy.org/jsonrpc_torrentkey.php"
    u2_tracker = ["daydream.dmhy.best", "tracker.dmhy.org"]
    to_tracker = "https://daydream.dmhy.best/announce?secure={}"

    tc = transmissionrpc.Client(transmission_config['host'], port=transmission_config['port'], user=transmission_config['username'], password=transmission_config['password'])

    def get_u2_torrents_hash():
        torrents = list(filter(lambda x: 'dmhy' in x.trackers[0]['announce'], tc.get_torrents()))

        u2_torrent_info_hash = []
        for torrent in torrents:
            u2_torrent_info_hash.append(
                {"hash": torrent.hashString, "tracker": torrent.trackers[0]['announce'], "id": torrent.id}
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
                    print(item.get("error"))
                    continue

                tc.change_torrent(ids=_index[item["id"]]["id"], trackerReplace=(0, to_tracker.format(item["result"])))

                updated_torrents.append(_index[item["id"]]["hash"])
        with open("updated_torrents.json", "w") as fp:
            json.dump(cached_torrents + updated_torrents, fp)


    if __name__ == "__main__":
        main()
    return 0

def c_De():
    __APIURL__ = input("输入API地址（站内查看）：")
    __DE_URL__ = input("输入客户端IP（http://IP）：")
    __DE_PORT__ = input("输入客户端后端端口（非WebUI端口）：")
    __DE_PORT__ = int(__DE_PORT__)
    __DE_USER__ = input("输入客户端用户名：")
    __DE_PW__ = input("输入客户端密码：")

    count = 0

    client = DelugeRPCClient(__DE_URL__, __DE_PORT__, __DE_USER__, __DE_PW__) 
    print("Connecting to Deluge...")
    client.connect()
    print("Fetching DMHY torrents from Deluge...")
    torrent_list = client.core.get_torrents_status({},['trackers'])
    dmhy_torrent_hash_list = [hash_ for hash_ in torrent_list if "dmhy" in str(torrent_list[hash_][b'trackers'][0][b'url'])]
    dmhy_req_list = []
    for i, hash_ in enumerate(dmhy_torrent_hash_list):
        dmhy_req_list.append({"jsonrpc": "2.0", "method": "query", "params": [str(hash_)[2:-1]], "id":i+1})
    print("Fetching Secure Code...")
    resp = requests.post(__APIURL__, json=dmhy_req_list)
    if resp.status_code != 200:
        raise(Exception("Error with Code {} Pls Try Again!".format(resp.status_code)))

    requested_secure_list = resp.json()

    error_torrent_hash_list = []
    print("Begin Updating...")
    for i, hash_ in enumerate(dmhy_torrent_hash_list):
        if "result" in requested_secure_list[i]:
            count += 1
            client.core.set_torrent_trackers(hash_, [{'url':"https://daydream.dmhy.best/announce?secure={}".format(requested_secure_list[i]["result"]), 'tier':0}])
            print("Edited Tracker for {} ({}/{})".format(str(hash_)[2:-1], count, len(requested_secure_list)))
        elif "error" in requested_secure_list[i]:
            print("Editing Tracker for {} failed {}. {}".format(str(hash_)[2:-1], 
            requested_secure_list[i]["error"]["code"], requested_secure_list[i]["error"]["message"]))
            error_torrent_hash_list.append(str(hash_)[2:-1])
        else:
            print("Editing Tracker for {} failed.".format(str(hash_)[2:-1]))
            error_torrent_hash_list.append(str(hash_)[2:-1])

    print()
    print("Successfully edited {} of {} torrents with errors occurred below:".format(count, len(requested_secure_list)))
    for each in error_torrent_hash_list:
        print(each)

    print()
    for i in range(2):
        print("Retry Time {}".format(i+1))

        dmhy_req_list.clear()
        dmhy_torrent_hash_list.clear()
        count = 0

        for i, hash_ in enumerate(error_torrent_hash_list):
            dmhy_torrent_hash_list.append(hash_)
            dmhy_req_list.append({"jsonrpc": "2.0", "method": "query", "params": [hash_], "id":i+1})

        print("Fetching Secure Code...")
        resp = requests.post(__APIURL__, json=dmhy_req_list)

        if resp.status_code != 200:
            print("Failed to fetch secure code, retry later")
            time.sleep(20)
            continue

        requested_secure_list = resp.json()
        error_torrent_hash_list.clear()

        print("Begin Updating...")

        for i, hash_ in enumerate(dmhy_torrent_hash_list):
            if "result" in requested_secure_list[i]:
                count += 1
                client.core.set_torrent_trackers(hash_, [{'url':"https://daydream.dmhy.best/announce?secure={}".format(requested_secure_list[i]["result"]), 'tier':0}])
                print("Edited Tracker for {} ({}/{})".format(str(hash_)[2:-1], count, len(requested_secure_list)))
            elif "error" in requested_secure_list[i]:
                print("Editing Tracker for {} failed {}. {}".format(str(hash_)[2:-1], 
                requested_secure_list[i]["error"]["code"], requested_secure_list[i]["error"]["message"]))
                error_torrent_hash_list.append(str(hash_)[2:-1])
            else:
                print("Editing Tracker for {} failed.".format(str(hash_)[2:-1]))
                error_torrent_hash_list.append(str(hash_)[2:-1])

        print("Successfully edited {} of {} torrents with errors occurred below:".format(count, len(requested_secure_list)))
        if len(error_torrent_hash_list) == 0:
            break
    return 0

# 客户端类型
clientType = input('当前客户端类型（1:qBittorrent,2:Transmission,3:Deluge）:')
if clientType == '1':
    c_qB()
elif clientType == '2':
    c_Tr()
elif clientType == '3':
    c_De()
else:
    exit()

input('感谢使用，祝您生活愉快。如果对您有帮助，欢迎star支持。（按任意键退出）')
