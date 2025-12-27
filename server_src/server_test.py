import socket
import json
import time
import sys
import os

# 将 src 目录加入路径，以便读取 config
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
import config

class TradeBrainInspector:
    def __init__(self):
        self.host = config.HOST
        self.port = config.PORT
        self.sock = None

    def connect(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(5)
            self.sock.connect((self.host, self.port))
            return True
        except Exception as e:
            print(f"❌ 连接失败: {e}")
            return False

    def send_request(self, msg_dict):
        try:
            payload = json.dumps(msg_dict) + "\n"
            self.sock.sendall(payload.encode('utf-8'))
            resp = self.sock.recv(config.BUFFER_SIZE).decode('utf-8')
            return json.loads(resp.strip())
        except Exception as e:
            return {"status": "error", "msg": str(e)}

    def run_all_tests(self):
        print("🔍 开始全局功能审计...\n")
        results = []

        # 1. 协议基础测试
        print("Test 1: 协议连通性...", end=" ")
        if self.connect():
            print("OK")
            results.append(True)
        else:
            print("FAIL")
            return # 后续测试无法进行

        # 2. 数据采集 (FEED_DATA) 完整性测试
        print("Test 2: 数据采集与事务写入...", end=" ")
        test_data = [[time.time() - i, 1.1000 + (i * 0.0001)] for i in range(100)]
        resp = self.send_request({"type": "FEED_DATA", "data": test_data})
        if resp.get('status') == 'saved' and resp.get('count') == 100:
            print("OK (100条已入库)")
            results.append(True)
        else:
            print(f"FAIL ({resp})")
            results.append(False)

        # 3. 实时推理 (PREDICT) 逻辑测试
        print("Test 3: 实时推理接口...", end=" ")
        # 连续发送数据模拟缓冲
        for _ in range(10):
            resp = self.send_request({"type": "PREDICT", "price": 1.1500})
        
        if 'type' in resp and (resp['type'] == 'PATH' or resp['type'] == 'WAIT'):
            print(f"OK (响应类型: {resp['type']})")
            results.append(True)
        else:
            print(f"FAIL ({resp})")
            results.append(False)

        # 4. 训练 (TRAIN) 触发测试
        print("Test 4: 模型训练引擎 (可能耗时)...", end=" ", flush=True)
        resp = self.send_request({"type": "TRAIN"})
        if resp.get('status') == 'ok' or (resp.get('status') == 'error' and "数据不足" in resp.get('msg')):
            print("OK (逻辑通路正常)")
            results.append(True)
        else:
            print(f"FAIL ({resp})")
            results.append(False)

        # 5. 异常鲁棒性测试
        print("Test 5: 脏数据抵御测试...", end=" ")
        self.sock.sendall(b"INVALID_JSON_DATA\n")
        try:
            resp_str = self.sock.recv(config.BUFFER_SIZE).decode('utf-8')
            resp = json.loads(resp_str.strip())
            if resp.get('status') == 'error':
                print("OK (成功捕获错误并返回通知)")
                results.append(True)
        except:
            print("FAIL (服务器可能崩溃了)")
            results.append(False)

        print("\n" + "="*30)
        print(f"审计结果: {sum(results)}/{len(results)} 通过")
        print("="*30)
        self.sock.close()

if __name__ == "__main__":
    inspector = TradeBrainInspector()
    inspector.run_all_tests()