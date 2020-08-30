# -*- coding: utf-8 -*
# U2TrackerUpdater-1.6
# 批量更新任务Tracker地址中的秘钥
# 依赖：Python3.8(requests,qbittorrent,python-qbittorrent,transmissionrpc,deluge-client)
# 原作者：
# qB-U2@杯杯杯杯具(https://gist.github.com/tongyifan/83220b417cffdd23528860ee0c518d15)
# Tr-U2@ITGR(https://gist.github.com/inertia42/f6120d118e47925095dbceb5e8e27272)
# De-U2@種崎敦美(https://github.com/XSky123/dmhy_change_securekey_deluge)
# 整合优化：U2@Loid(https://github.com/LoidVC/U2TrackerUpdater)
# 感谢帮助：U2@vincent-163(PR#1),U2@x琳x(PR#3),U2@Noira(论坛#139477),U2@Rhilip(PR#4),U2@soleil(PR#5),Github@ThunderMonkey(PR#6)
# 原作者备注
# 0. 免责声明：程序仅在本地客户端qBittorrent v4.2.5/Transmission v2.94/Deluge v1.3.15上测试通过，运行结果与作者无关
# 1. 已知bug：从第 48 个请求开始会连续失败 10 次，在管理组修复之前请手动重复执行至所有种子更新完毕，直到显示找到0个未被更新的种子为止（已修复）

# 优化备注
# 1.添加交互逻辑
# 2.整合多客户端
# 3.本工具仅限用于于个人更新Tracker中的秘钥，禁止利用其进行带宽和运算资源占用、数据挖掘、规律遍历、商业使用或类似的活动。违规操作造成的警告、禁用相关账户，封锁IP、中止或终止API等后果自负责任。
# 4.执行脚本的主机和运行客户端的主机在同一局域网即可，客户端地址写运行客户端的主机的地址

import json
import os
import time

import requests
import transmission_rpc
from deluge_client import DelugeRPCClient
from qbittorrent import Client as QbittorrentClient

# 声明
notes = """
# U2TrackerUpdater-1.6
# 批量更新任务Tracker地址中的秘钥
# 依赖：Python3.8(requests,qbittorrent,python-qbittorrent,transmissionrpc,deluge-client)
# 原作者：U2@杯杯杯杯具(https://gist.github.com/tongyifan/83220b417cffdd23528860ee0c518d15)
# Tr-U2@ITGR(https://gist.github.com/inertia42/f6120d118e47925095dbceb5e8e27272)
# De-U2@種崎敦美(https://github.com/XSky123/dmhy_change_securekey_deluge)
# 整合优化：U2@Loid(https://github.com/LoidVC/U2TrackerUpdater)
# 感谢帮助：U2@vincent-163(PR#1),U2@x琳x(PR#3),U2@Noira(论坛#139477),U2@Rhilip(PR#4),U2@soleil(PR#5),Github@ThunderMonkey(PR#6)

# 原作者备注
# 0. 免责声明：程序仅在本地客户端qBittorrent v4.2.5/Transmission v2.94/Deluge v1.3.15上测试通过，运行结果与作者无关
# 1. 已知bug：从第 48 个请求开始会连续失败 10 次，在管理组修复之前请手动重复执行至所有种子更新完毕，直到显示找到0个未被更新的种子为止

# 优化备注
# 1.添加交互逻辑
# 2.整合多客户端
# 3.本工具仅限用于于个人更新Tracker中的秘钥，禁止利用其进行带宽和运算资源占用、数据挖掘、规律遍历、商业使用或类似的活动。违规操作造成的警告、禁用相关账户，封锁IP、中止或终止API等后果自负责任。
# 4.执行脚本的主机和运行客户端的主机在同一局域网即可，客户端地址写运行客户端的主机的地址
"""


# 和U2的jsonrpc交互部分

endpoint = "https://u2.dmhy.org/jsonrpc_torrentkey.php"
u2_tracker = ["daydream.dmhy.best", "tracker.dmhy.org"]
to_tracker = "https://daydream.dmhy.best/announce?secure={}"


class BtClient(object):
    batch_size = 25  # 防止单次提交的info_hashes过多的情况，把他chunk成25个作为一组提交
    cache_file = "updated_torrents.json"

    apikey = None
    cached_hashes = []

    def __init__(self):
        self.apikey = input("输入APIKEY（站内查看API地址中的apikey=后面的部分）：")

        # 加载缓存
        if os.path.exists(self.cache_file):
            with open(self.cache_file, "r") as fp:
                try:
                    self.cached_hashes = json.load(fp)
                except Exception:
                    pass

    def saveCachedTorrentHashes(self):
        with open(self.cache_file, "w") as fp:
            json.dump(self.cached_hashes, fp)

    def getAllTorrentHashes(self) -> list:
        """
        返回所有U2的种子信息，每个列表项都是个字典，必定包含 hash项，即 {hash: string,[key: string]: any}[]

        :return:
        """
        raise NotImplementedError()

    def getUnCachedTorrentHashes(self) -> list:
        return [
            t for t in self.getAllTorrentHashes() if t["hash"] not in self.cached_hashes
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
        print("找到了{}个未被更新的种子～".format(len(u2_torrent_info_hash)))

        # 防止单次提交的info_hashes过多的情况，把他chunk成{batch_size}个作为一组提交
        for i in range(0, len(u2_torrent_info_hash), self.batch_size):
            deal_torrents = u2_torrent_info_hash[i:i + self.batch_size]
            print("正在获取第{}到第{}个种子的新secret key".format(i, i + len(deal_torrents)))

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
                    print("速度过快，将在{}秒后重试".format(wait_second))
                    time.sleep(wait_second)
                    resp = requests.post(
                        endpoint, params={"apikey": self.apikey}, json=request_data
                    )

            if resp.status_code == 403:
                print("APIKEY无效，请检查（注意APIKEY不是passkey）")
                exit()

            if resp.status_code != 200:
                print("意外的错误：{}".format(resp.status_code))

            response_data = resp.json()
            for item in response_data:
                if item.get("error"):
                    if item["error"]["code"] == -10003:
                        self.deleteTorrent(_index[item["id"]]["hash"])
                    print(item.get("error"))
                    continue

                print("正在编辑种子 {} 的Tracker信息".format(_index[item["id"]]["hash"]))
                self.changeTorrentTracker(_index[item["id"]], item)
                self.cached_hashes.append(_index[item["id"]]["hash"])

            # 每个轮次结束后就更新缓存，不用等到所有结束后再缓存
            self.saveCachedTorrentHashes()


class QBittorrent(BtClient):
    def __init__(self):
        super().__init__()
        self.host = input("输入客户端地址（http://IP:端口）：")
        self.user = input("输入客户端用户名：")
        self.password = input("输入客户端密码：")

        qb = QbittorrentClient(self.host)
        print("开始连接 Qbittorrent 客户端...")
        qb.login(self.user, self.password)
        self.qb = qb

    def getAllTorrentHashes(self) -> list:
        torrents = self.qb.torrents()

        u2_torrent_info_hash = []
        for torrent in torrents:
            hashes = torrent["hash"]
            trackers = self.qb.get_torrent_trackers(hashes)

            for tker in trackers:
                if any([tracker in tker["url"] for tracker in u2_tracker]):
                    u2_torrent_info_hash.append(
                        {"hash": hashes, "tracker": tker["url"]}
                    )
                    continue

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
        self.host = input("输入客户端IP：")
        self.port = input("输入客户端端口（通常为9091）：")
        self.user = input("输入客户端用户名：")
        self.password = input("输入客户端密码：")

        print("开始连接 Transmission 客户端...")
        tc = transmission_rpc.Client(host=self.host, port=self.port, username=self.user, password=self.password)
        self.tc = tc

    def getAllTorrentHashes(self) -> list:
        torrents = list(filter(lambda x: x.trackers and 'dmhy' in x.trackers[0]['announce'], self.tc.get_torrents()))

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
    print(notes)
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