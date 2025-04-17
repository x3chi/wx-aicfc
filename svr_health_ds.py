from openai import OpenAI

def ds(svr_data):
    client = OpenAI(
        api_key="sk-4572ecf05c5c46c29218838051f8be2d",  # 如何获取API Key：https://help.aliyun.com/zh/model-studio/developer-reference/get-api-key
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
    )
    reasoning_content = ""  # 定义完整思考过程
    answer_content = ""     # 定义完整回复
    is_answering = False   # 判断是否结束思考过程并开始回复
    # 创建聊天完成请求
    completion = client.chat.completions.create(
        model="deepseek-v3",  # 此处以 deepseek-r1 为例，可按需更换模型名称
        messages=[
            {"role": "user", "content": "这是服务器的运行数据，帮我分析服务器健康状态，并判断是否有维护的需要，如果有维护的需要，请明确如何维护："},
            {"role": "user", "content": f"{system_info}"}
        ],
        stream=True,
    # 解除以下注释会在最后一个chunk返回Token使用量
    #stream_options={
    #     "include_usage": True
    #}
    )

    for chunk in completion:
    # 如果chunk.choices为空，则打印usage
        if not chunk.choices:
            print("\nUsage:")
            print(chunk.usage)
        else:
            delta = chunk.choices[0].delta
        # 打印思考过程
            if hasattr(delta, 'reasoning_content') and delta.reasoning_content != None:
                print(delta.reasoning_content, end='', flush=True)
                reasoning_content += delta.reasoning_content
            else:
            # 开始回复
                if delta.content != "" and is_answering == False:
                    print("\n" + "=" * 20 + "完整回复" + "=" * 20 + "\n")
                    is_answering = True
            # 打印回复过程
                print(delta.content, end='', flush=True)
                answer_content += delta.content

import psutil
import platform
import json
import datetime
import os
import socket

def get_system_info():
    """获取全面的系统信息"""
    info = {}

    # 基础系统信息
    info["system"] = {
        "hostname": socket.gethostname(),
        "os": {
            "name": os.name,
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor()
        },
        "boot_time": datetime.datetime.fromtimestamp(psutil.boot_time()).isoformat(),
        "users": [{"name": u.name, "terminal": u.terminal, "host": u.host, "started": datetime.datetime.fromtimestamp(u.started).isoformat()} 
                 for u in psutil.users()],
        "uptime": psutil.boot_time()
    }

    # CPU 信息
    cpu_info = {
        "physical_cores": psutil.cpu_count(logical=False),
        "logical_cores": psutil.cpu_count(logical=True),
        "usage_percent": psutil.cpu_percent(interval=1, percpu=True),
        "times": psutil.cpu_times()._asdict(),
        "freq": {
            "current": psutil.cpu_freq().current if hasattr(psutil, "cpu_freq") else None,
            "min": psutil.cpu_freq().min if hasattr(psutil, "cpu_freq") else None,
            "max": psutil.cpu_freq().max if hasattr(psutil, "cpu_freq") else None
        }
    }
    info["cpu"] = cpu_info

    # 内存信息
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()
    info["memory"] = {
        "virtual": {
            "total": mem.total,
            "available": mem.available,
            "used": mem.used,
            "free": mem.free,
            "percent": mem.percent,
            "unit": "bytes"
        },
        "swap": {
            "total": swap.total,
            "used": swap.used,
            "free": swap.free,
            "percent": swap.percent,
            "sin": swap.sin,
            "sout": swap.sout
        }
    }

    # 磁盘信息
    disks = []
    for part in psutil.disk_partitions(all=False):
        usage = psutil.disk_usage(part.mountpoint)
        disks.append({
            "device": part.device,
            "mountpoint": part.mountpoint,
            "fstype": part.fstype,
            "total": usage.total,
            "used": usage.used,
            "free": usage.free,
            "percent": usage.percent
        })
    info["disks"] = disks

    # 网络信息
    net_io = psutil.net_io_counters()
    net_if = psutil.net_if_addrs()
    net_stats = psutil.net_if_stats()
    info["network"] = {
        "io_counters": {
            "bytes_sent": net_io.bytes_sent,
            "bytes_recv": net_io.bytes_recv,
            "packets_sent": net_io.packets_sent,
            "packets_recv": net_io.packets_recv
        },
        "interfaces": {}
    }
    for name in net_if:
        info["network"]["interfaces"][name] = {
            "addresses": [str(addr.address) for addr in net_if[name]],
            "stats": {
                "isup": net_stats[name].isup,
                "speed": net_stats[name].speed
            }
        }

    # 传感器信息
    try:
        sensors = {
            "temperatures": {k: [t._asdict() for t in v] 
                            for k, v in psutil.sensors_temperatures().items()},
            "fans": {k: [f._asdict() for f in v] 
                    for k, v in psutil.sensors_fans().items()} if hasattr(psutil, "sensors_fans") else {}
        }
    except AttributeError:
        sensors = {"error": "Sensor data not available"}
    info["sensors"] = sensors

    # 进程信息
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'status', 'cpu_percent', 'memory_percent']):
        try:
            processes.append({
                "pid": proc.info['pid'],
                "name": proc.info['name'],
                "status": proc.info['status'],
                "cpu_percent": proc.info['cpu_percent'],
                "memory_percent": proc.info['memory_percent']
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    info["processes"] = processes

    # 系统负载
    info["load"] = {
        "1min": os.getloadavg()[0],
        "5min": os.getloadavg()[1],
        "15min": os.getloadavg()[2]
    } if hasattr(os, "getloadavg") else {}

    # 转换为可序列化格式
    def convert(o):
        if isinstance(o, (datetime.datetime, datetime.date)):
            return o.isoformat()
        raise TypeError

    return json.loads(json.dumps(info, default=convert))

if __name__ == "__main__":
    system_info = get_system_info()
    
    # 保存到 JSON 文件
    filename = f"system_status_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(system_info, f, indent=2)
    
    print(f"系统状态已保存到: {os.path.abspath(filename)}","\n 数据传送到DeepSeek开始分析...")
    ds(system_info)