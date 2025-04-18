import requests
import json
import time
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor

# Zabbix API 服务器地址
ZABBIX_URL = "http://10.0.12.31/api_jsonrpc.php"
ZABBIX_USER = "Admin"
ZABBIX_PASSWORD = "zabbix"
MAX_THREADS = 5  # 最大线程数

# 登录 API 并获取 token
def zabbix_login():
    payload = {
        "jsonrpc": "2.0",
        "method": "user.login",
        "params": {
            "username": ZABBIX_USER,
            "password": ZABBIX_PASSWORD
        },
        "id": 1
    }
    response = requests.post(ZABBIX_URL, json=payload, headers={"Content-Type": "application/json-rpc"})
    response_data = response.json()
    if "result" in response_data:
        auth_token = response_data["result"]
        print("zabbix_login执行完成，response为：", auth_token)
        return auth_token
    else:
        print("登录失败，response为：", response_data)
        return None

# 获取所有主机信息
def get_hosts(auth_token):
    if auth_token is None:
        return None
    payload = {
        "jsonrpc": "2.0",
        "method": "host.get",
        "params": {
            "output": ["hostid", "name", "status"]
        },
        "id": 2
    }
    response = requests.post(ZABBIX_URL, json=payload, headers={"Content-Type": "application/json-rpc", "Authorization": f"Bearer {auth_token}"})
    response_data = response.json()
    if "result" in response_data:
        hosts = response_data["result"]
        return hosts
    else:
        print("获取主机信息失败，response为：", response_data)
        return None

# 获取主机的 IP 地址
def get_host_ip(auth_token, host_id):
    payload = {
        "jsonrpc": "2.0",
        "method": "hostinterface.get",
        "params": {
            "output": "extend",
            "hostids": host_id
        },
        "id": 3
    }
    response = requests.post(ZABBIX_URL, json=payload, headers={"Content-Type": "application/json-rpc", "Authorization": f"Bearer {auth_token}"})
    response_data = response.json()
    if "result" in response_data:
        # 提取接口信息中的 IP 地址
        interfaces = response_data["result"]
        for interface in interfaces:
            if interface["main"] == "1" and interface["useip"] == "1":  # 主接口，使用 IP
                return interface["ip"]
        return "未知"
    else:
        print(f"获取主机接口失败，host_id: {host_id}，response为：", response_data)
        return "未知"

# 获取指定主机的监控项
def get_items(auth_token, host_id):
    payload = {
        "jsonrpc": "2.0",
        "method": "item.get",
        "params": {
            "hostids": host_id,
            "output": ["itemid", "name", "lastvalue", "value_type"]
        },
        "id": 4
    }
    response = requests.post(ZABBIX_URL, json=payload, headers={"Content-Type": "application/json-rpc", "Authorization": f"Bearer {auth_token}"})
    response_data = response.json()
    if "result" in response_data:
        items = response_data["result"]
        return items
    else:
        print(f"获取监控项失败，host_id: {host_id}，response为：", response_data)
        return []

# 获取指定监控项的历史数据
def get_history(auth_token, item_id, time_from, time_till, item_type):
    payload = {
        "jsonrpc": "2.0",
        "method": "history.get",
        "params": {
            "output": ["clock", "value"],
            "history": item_type,
            "itemids": item_id,
            "sortfield": "clock",
            "sortorder": "DESC",
            "time_till": time_till
        },
        "id": 5
    }
    response = requests.post(ZABBIX_URL, json=payload, headers={"Content-Type": "application/json-rpc", "Authorization": f"Bearer {auth_token}"})
    response_data = response.json()
    if "result" in response_data:
        return response_data["result"]
    else:
        print(f"获取历史数据失败，item_id: {item_id}，response为：", response_data)
        return []

# 获取 Unix 时间戳
def get_time_stamp(date_str):
    return int(time.mktime(time.strptime(date_str, '%Y-%m-%d %H:%M:%S')))

# 采集主机数据
def collect_host_data(auth_token, host):
    host_data = {
        "host_name": host['name'],
        "host_status": host['status'],
        "host_ip": get_host_ip(auth_token, host['hostid']),  # 获取主机 IP
        "items": []
    }

    # 获取该主机的监控项信息
    items = get_items(auth_token, host['hostid'])
    if items is None:
        print(f"获取主机 {host['name']} 的监控项失败，跳过。")
        return

    for item in tqdm(items, desc=f"采集中 {host['name']} 的监控项", unit="item", leave=False):
        item_data = {
            "item_name": item['name'],
            "last_value": item['lastvalue'],
            "history": []
        }

        # 设定时间范围（以Unix时间戳表示）
        time_from = get_time_stamp('2025-01-01 00:00:00')  # 起始时间
        time_till = get_time_stamp('2025-04-12 23:59:59')  # 结束时间

        # 获取历史数据
        history = get_history(auth_token, item['itemid'], time_from, time_till, item['value_type'])
        for record in history:
            record_data = {
                "time": time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(int(record['clock']))),
                "value": record['value']
            }
            item_data["history"].append(record_data)
        host_data["items"].append(item_data)

    # 保存主机数据为json文件
    file_name = f"{host['name']}.json"
    with open(file_name, 'w', encoding='utf-8') as f:
        json.dump(host_data, f, ensure_ascii=False, indent=4)
    print(f"{host['name']}采集完成，数据保存为{file_name}")

# 主函数
def main():
    # 获取认证 token
    auth_token = zabbix_login()

    if auth_token is None:
        print("获取认证 token 失败，程序退出。")
        return

    # 获取所有主机信息
    hosts = get_hosts(auth_token)
    if hosts is None:
        print("获取主机信息失败，程序退出。")
        return

    print("获取到的主机信息：")
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        futures = [executor.submit(collect_host_data, auth_token, host) for host in hosts]
        for future in tqdm(futures, desc="总体进度", unit="host"):
            future.result()

if __name__ == "__main__":
    main()
