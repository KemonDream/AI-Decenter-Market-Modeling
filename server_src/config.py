import os

# --- 通信配置 ---
HOST = '127.0.0.1'
PORT = 8888
BUFFER_SIZE = 1024 * 1024  # 1MB 接收缓冲

# --- 路径配置 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, '..', 'data')
if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)

DB_PATH = os.path.join(DATA_DIR, 'market_memory.db')
MODEL_PATH = os.path.join(DATA_DIR, 'cnn_lightweight_v1.keras')

# --- 模型超参数 ---
INPUT_WINDOW = 2000       # 回看 2000 Tick
TOTAL_PREDICT_TICKS = 2000 # 预测未来 2000 Tick
PREDICT_STRIDE = 100      # 每 100 个点取一个样
OUTPUT_STEPS = TOTAL_PREDICT_TICKS // PREDICT_STRIDE

# --- 训练配置 ---
TRAIN_LIMIT = 500000      # 最大训练样本数
BATCH_SIZE = 128
EPOCHS = 5