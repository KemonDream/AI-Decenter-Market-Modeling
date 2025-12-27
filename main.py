import socket
import json
import numpy as np
import sqlite3
import os
import threading
import struct
from collections import deque
import tensorflow as tf
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import Dense, Conv1D, Flatten, Input, MaxPooling1D, GlobalAveragePooling1D, Dropout

# --- 配置 ---
HOST = '127.0.0.1'
PORT = 8888
DB_PATH = 'market_memory.db'
MODEL_PATH = 'cnn_fast_v1.keras'
INPUT_WINDOW = 2000
TOTAL_PREDICT_TICKS = 2000
PREDICT_STRIDE = 100
OUTPUT_STEPS = TOTAL_PREDICT_TICKS // PREDICT_STRIDE

os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
tf.config.threading.set_inter_op_parallelism_threads(1)

class FastBrain:
    def __init__(self):
        self.init_db()
        self.model = self.load_or_create_model()
        self.tick_buffer = deque(maxlen=INPUT_WINDOW)
        self.lock = threading.Lock()

    def init_db(self):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS ticks (timestamp REAL, price REAL)''')
        # 创建索引以加速查询，但在大量插入时可能略微降速，建议采集完再建索引
        # 这里为了查询方便先保留
        c.execute('''CREATE INDEX IF NOT EXISTS idx_ts ON ticks (timestamp)''')
        c.execute("SELECT Count(*) FROM ticks")
        count = c.fetchone()[0]
        print(f"📂 数据库就绪: 当前已有 {count} 条数据")
        conn.commit()
        conn.close()

    def load_or_create_model(self):
        if os.path.exists(MODEL_PATH):
            return load_model(MODEL_PATH)
        print("🆕 创建轻量化模型...")
        model = Sequential([
            Input(shape=(INPUT_WINDOW, 1)),
            Conv1D(32, 5, activation='relu', padding='same'),
            MaxPooling1D(2),
            Conv1D(64, 5, activation='relu', padding='same'),
            GlobalAveragePooling1D(), # 大幅减小模型体积
            Dropout(0.3),
            Dense(128, activation='relu'),
            Dense(OUTPUT_STEPS, activation='linear')
        ])
        model.compile(optimizer='adam', loss='mse')
        return model

    def save_bulk_data(self, data_list):
        if not data_list: return 0
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        try:
            # 🔥 显式开启事务，速度提升 100倍
            c.execute("BEGIN TRANSACTION")
            # data_list 格式应该是 [[ts, price], [ts, price]...]
            c.executemany("INSERT INTO ticks VALUES (?, ?)", data_list)
            c.execute("COMMIT")
            count = len(data_list)
            print(f"📥 高速写入: {count} 条 (最新时间戳: {data_list[-1][0]:.0f})")
            return count
        except Exception as e:
            print(f"❌ 写入失败: {e}")
            conn.rollback()
            return 0
        finally:
            conn.close()

    def train_memory(self):
        # ... (训练逻辑保持不变，参考之前的代码) ...
        # 为节省篇幅，此处省略，请将之前讨论的 train_memory 逻辑填入
        return {"status": "ok", "msg": "Training placeholder"}

    def predict(self, price):
        # ... (推理逻辑保持不变) ...
        return {"type": "WAIT"}

# --- Socket 监听优化 ---
brain = FastBrain()

def handle_client(sock):
    print("🔗 连接建立")
    buffer = ""
    while True:
        try:
            # 🔥 加大接收缓冲区到 1MB，防止丢包
            data = sock.recv(1024 * 1024).decode('utf-8')
            if not data: break
            buffer += data
            
            while '\n' in buffer:
                msg_str, buffer = buffer.split('\n', 1)
                if not msg_str: continue
                
                try:
                    msg = json.loads(msg_str)
                    response = {}
                    
                    if msg['type'] == 'FEED_DATA':
                        # 批量保存
                        count = brain.save_bulk_data(msg['data'])
                        response = {"status": "saved", "count": count}
                    
                    elif msg['type'] == 'TRAIN':
                        response = brain.train_memory()
                    
                    elif msg['type'] == 'PREDICT':
                        response = brain.predict(msg['price'])
                        
                    sock.sendall((json.dumps(response) + "\n").encode('utf-8'))
                    
                except json.JSONDecodeError:
                    print("⚠️ JSON 解析错误 (可能包不完整)")
                except Exception as e:
                    print(f"处理异常: {e}")
        except ConnectionResetError:
            break
        except Exception as e:
            print(f"Socket异常: {e}")
            break
    sock.close()
    print("🔌 连接断开")

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
server.listen(5)
print(f"🚀 高速引擎监听中 {HOST}:{PORT} ...")

while True:
    client, addr = server.accept()
    t = threading.Thread(target=handle_client, args=(client,))
    t.start()