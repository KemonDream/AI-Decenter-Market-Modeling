import os
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import Dense, Conv1D, Input, MaxPooling1D, GlobalAveragePooling1D, Dropout
import config

# 禁用 GPU (对于这种小模型，CPU 更快且稳定)
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
tf.config.threading.set_inter_op_parallelism_threads(1)

class ModelEngine:
    def __init__(self):
        self.model = self._load_or_create()

    def _load_or_create(self):
        if os.path.exists(config.MODEL_PATH):
            print("🧠 [Model] 加载已有模型...")
            return load_model(config.MODEL_PATH)
        
        print("✨ [Model] 初始化轻量化 CNN...")
        model = Sequential([
            Input(shape=(config.INPUT_WINDOW, 1)),
            # 特征提取
            Conv1D(32, 5, activation='relu', padding='same'),
            MaxPooling1D(2),
            Conv1D(64, 5, activation='relu', padding='same'),
            MaxPooling1D(2),
            Conv1D(128, 3, activation='relu', padding='same'),
            
            # 关键：全局池化压缩参数
            GlobalAveragePooling1D(),
            Dropout(0.3),
            
            Dense(128, activation='relu'),
            Dense(config.OUTPUT_STEPS, activation='linear')
        ])
        model.compile(optimizer='adam', loss='mse')
        return model

    def train(self, prices_list):
        """
        接收纯价格列表 -> 执行 Z-Score 预处理 -> 训练
        """
        if len(prices_list) < config.INPUT_WINDOW + config.TOTAL_PREDICT_TICKS + 100:
            return {"status": "error", "msg": "数据不足"}

        prices_arr = np.array(prices_list)
        X, y = [], []
        
        # 步长采样生成训练集
        limit = len(prices_arr) - config.INPUT_WINDOW - config.TOTAL_PREDICT_TICKS
        # 训练采样步长设为 20，避免数据重叠过多导致训练太慢
        stride = 20 
        
        for i in range(0, limit, stride):
            window = prices_arr[i : i+config.INPUT_WINDOW]
            
            # --- Z-Score 归一化 ---
            mean = np.mean(window)
            std = np.std(window)
            if std < 1e-6: std = 1e-6
            
            norm_input = (window - mean) / std
            
            # 标签归一化
            future = prices_arr[i+config.INPUT_WINDOW : i+config.INPUT_WINDOW+config.TOTAL_PREDICT_TICKS : config.PREDICT_STRIDE]
            norm_target = (future - mean) / std
            
            X.append(norm_input)
            y.append(norm_target)
            
        X = np.array(X).reshape(-1, config.INPUT_WINDOW, 1)
        y = np.array(y)
        
        print(f"🏋️‍♂️ [Model] 开始训练 {len(X)} 条样本...")
        history = self.model.fit(
            X, y, 
            epochs=config.EPOCHS, 
            batch_size=config.BATCH_SIZE,
            validation_split=0.2,
            verbose=1
        )
        
        self.model.save(config.MODEL_PATH)
        loss = history.history['val_loss'][-1]
        return {"status": "ok", "val_loss": float(loss)}

    def predict(self, raw_window):
        """
        接收最新窗口数据 -> 归一化 -> 推理 -> 反归一化
        """
        if len(raw_window) < config.INPUT_WINDOW:
            return None
            
        arr = np.array(raw_window)
        mean = np.mean(arr)
        std = np.std(arr)
        if std < 1e-6: std = 1e-6
        
        norm_input = (arr - mean) / std
        inp = norm_input.reshape(1, config.INPUT_WINDOW, 1)
        
        # 推理
        pred_z = self.model(inp, training=False).numpy()[0]
        
        # 反归一化还原为价格
        pred_prices = (pred_z * std) + mean
        
        # 转为相对路径 (相对于当前价格的差值)
        current_price = arr[-1]
        relative_path = pred_prices - current_price
        
        return relative_path.tolist()