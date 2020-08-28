# -*- coding: utf-8 -*
# U2TrackerUpdater
# 批量更新任务Tracker地址中的秘钥
# 原作者：
# qB-U2@杯杯杯杯具(https://gist.github.com/tongyifan/83220b417cffdd23528860ee0c518d15)
# Tr-U2@ITGR(https://gist.github.com/inertia42/f6120d118e47925095dbceb5e8e27272)
# De-U2@種崎敦美(https://github.com/XSky123/dmhy_change_securekey_deluge)
# 整合优化：U2@Loid(https://github.com/LoidVC/U2TrackerUpdater)

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
import qbittorrent
import transmissionrpc
from deluge_client import DelugeRPCClient

# 和U2的jsonrpc交互部分

endpoint = "https://u2.dmhy.org/jsonrpc_torrentkey.php"
u2_tracker = ["daydream.dmhy.best", "tracker.dmhy.org"]
to_tracker = "https://daydream.dmhy.best/announce?secure={}"


class BtClient(object):
    batch_size = 25  # 防止单次提交的info_hashes过多的情况，把他chunk成25个作为一组提交
    cache_file = "updated_torrents.json"

    apikey = None

    def __init__(self):
        self.apikey = input("输入APIKEY（站内查看API地址中的apikey=后面的部分）：")

    def getAllTorrentHashes(self) -> list:
        """
        返回所有U2的种子信息，每个列表项都是个字典，必定包含 hash项，即 {hash: string,[key: string]: any}[]

        :return:
        """
        raise NotImplementedError()

    def getCachedTorrentHashes(self) -> list:
        if not os.path.exists(self.cache_file):
            return []
        else:
            with open(self.cache_file, "r") as fp:
                return json.load(fp)

    def setCachedTorrentHashes(self, updated_torrents):
        with open(self.cache_file, "w") as fp:
            json.dump(self.getCachedTorrentHashes() + updated_torrents, fp)

    def getUnCachedTorrentHashes(self) -> list:
        return [
            t for t in self.getAllTorrentHashes() if t["hash"] not in self.getCachedTorrentHashes()
        ]

    def changeTorrentTracker(self, info, item):
        """

        :param info: getAllTorrentHashes()中返回的列表项
        :param item: u2对应info_hash的API返回值
        :return:
        """
        raise NotImplementedError()

    def deleteTorrent(self, info_hash):
        pass

    def runJob(self):
        u2_torrent_info_hash = self.getUnCachedTorrentHashes()
        print(f"找到了{len(u2_torrent_info_hash)}个未被更新的种子～")

        # 防止单次提交的info_hashes过多的情况，把他chunk成{batch_size}个作为一组提交
        updated_torrents = []
        for i in range(0, len(u2_torrent_info_hash), self.batch_size):
            deal_torrents = u2_torrent_info_hash[i:i + self.batch_size]
            print(f"正在获取第{i}到第{i + len(deal_torrents)}个种子的新secret key")

            request_data = []
            _index = {}
            for index, torrent in enumerate(deal_torrents):
                request_data.append(
                    {
                        "jsonrpc": "2.0",
                        "method": "query",
                        "params": [torrent["hash"]],
                        "id": index,
                    }
                )
                _index[index] = torrent
            resp = requests.post(endpoint, params={"apikey": self.apikey}, json=request_data)

            if resp.status_code == 503:
                while resp.status_code == 503:
                    wait_second = int(resp.headers["Retry-After"]) + 5
                    print(f"速度过快，将在{wait_second}秒后重试")
                    time.sleep(wait_second)
                    resp = requests.post(
                        endpoint, params={"apikey": self.apikey}, json=request_data
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
                        self.deleteTorrent(_index[item["id"]]["hash"])
                    print(item.get("error"))
                    continue

                print("正在编辑种子 {} 的Tracker信息".format(_index[item["id"]]["hash"]))
                self.changeTorrentTracker(_index[item["id"]], item)
                updated_torrents.append(_index[item["id"]]["hash"])

        self.setCachedTorrentHashes(updated_torrents)


class QBittorrent(BtClient):
    def __init__(self):
        super().__init__()
        self.host = input("输入客户端地址（http://IP:端口）：")
        self.user = input("输入客户端用户名：")
        self.password = input("输入客户端密码：")

        qb = qbittorrent.Client(self.host)
        print("开始连接 Qbittorrent 客户端...")
        qb.login(self.user, self.password)
        self.qb = qb

    def getAllTorrentHashes(self) -> list:
        torrents = self.qb.torrents()

        u2_torrent_info_hash = []
        for torrent in torrents:
            if any([tracker in torrent.get("tracker", "") for tracker in u2_tracker]):
                u2_torrent_info_hash.append(
                    {"hash": torrent.get("hash"), "tracker": torrent.get("tracker")}
                )
        return u2_torrent_info_hash

    def changeTorrentTracker(self, info, item):
        return self.qb._post(
            "torrents/editTracker",
            data={
                "hash": info["hash"],
                "origUrl": info["tracker"],
                "newUrl": to_tracker.format(item["result"]),
            },
        )

    def deleteTorrent(self, info_hash):
        return self.qb.delete([info_hash])


class Transmission(BtClient):

    def __init__(self):
        super().__init__()
        self.host = input("输入客户端IP（http://IP）：")
        self.port = input("输入客户端端口（通常为9091）：")
        self.user = input("输入客户端用户名：")
        self.password = input("输入客户端密码：")

        print("开始连接 Transmission 客户端...")
        tc = transmissionrpc.Client(self.host, port=self.port, user=self.user, password=self.password)
        self.tc = tc

    def getAllTorrentHashes(self) -> list:
        torrents = list(filter(lambda x: 'dmhy' in x.trackers[0]['announce'], self.tc.get_torrents()))

        u2_torrent_info_hash = []
        for torrent in torrents:
            u2_torrent_info_hash.append(
                {"hash": torrent.hashString, "tracker": torrent.trackers[0]['announce'], "id": torrent.id}
            )

        return u2_torrent_info_hash

    def changeTorrentTracker(self, info, item):
        return self.tc.change_torrent(info["id"], trackerReplace=(0, to_tracker.format(item["result"])))


class Deluge(BtClient):
    def __init__(self):
        super().__init__()
        __DE_URL__ = input("输入客户端IP（http://IP）：")
        __DE_PORT__ = int(input("输入客户端后端端口（非WebUI端口）："))
        __DE_USER__ = input("输入客户端用户名：")
        __DE_PW__ = input("输入客户端密码：")

        self.client = DelugeRPCClient(__DE_URL__, __DE_PORT__, __DE_USER__, __DE_PW__)
        print("开始连接 Deluge 客户端...")
        self.client.connect()

    def getAllTorrentHashes(self) -> list:
        print("Fetching DMHY torrents from Deluge...")
        torrent_list = self.client.core.get_torrents_status({}, ['trackers'])
        return [{"hash": str(hash_)[2:-1], "raw_hash": hash_} for hash_ in torrent_list if
                "dmhy" in str(torrent_list[hash_][b'trackers'][0][b'url'])]

    def changeTorrentTracker(self, info, item):
        self.client.core.set_torrent_trackers(info["raw_hash"], [
            {'url': to_tracker.format(item["result"]), 'tier': 0}
        ])


if __name__ == '__main__':
    # 声明
    print("# U2TrackerUpdater\n# 批量更新任务Tracker地址中的秘钥\n# 原作者：U2@杯杯杯杯具(https://gist.github.com/tongyifan/83220b417cffdd23528860ee0c518d15)\n# Tr-U2@ITGR(https://gist.github.com/inertia42/f6120d118e47925095dbceb5e8e27272)\n# De-U2@種崎敦美(https://github.com/XSky123/dmhy_change_securekey_deluge)\n# 整合优化：U2@Loid(https://github.com/LoidVC/U2TrackerUpdater)")
    print('# 原作者备注\n# 0. 免责声明：程序仅在本地客户端qBittorrent v4.2.5/Transmission v2.94/Deluge v1.3.15上测试通过，运行结果与作者无关\n# 1. 已知bug：从第 48 个请求开始会连续失败 10 次，在管理组修复之前请手动重复执行至所有种子更新完毕，直到显示找到0个未被更新的种子为止')
    print("# 优化备注\n# 1.添加交互逻辑\n# 2.整合多客户端\n# 3.本工具仅限用于于个人更新Tracker中的秘钥，禁止利用其进行带宽和运算资源占用、数据挖掘、规律遍历、商业使用或类似的活动。违规操作造成的警告、禁用相关账户，封锁IP、中止或终止API等后果自负责任。")
    termDes = input('# 我已阅读并同意上述条款（Y/N）：')
    if termDes.lower() != 'y':
        exit()

    # 客户端类型
    client = None
    clientType = input('当前客户端类型（1:qBittorrent,2:Transmission,3:Deluge）:')
    if clientType == '1':
        client = QBittorrent()
    elif clientType == '2':
        client = Transmission()
    elif clientType == '3':
        client = Deluge()
    else:
        exit()

    if client:
        client.runJob()

    input('感谢使用，祝您生活愉快。如果对您有帮助，欢迎star支持。（按任意键退出）')
