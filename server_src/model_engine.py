import os
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Model, load_model
from tensorflow.keras.layers import Dense, Conv1D, Input, GlobalAveragePooling1D, Dropout, Embedding, Flatten, Concatenate
import config
from datetime import datetime

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
        
        print("✨ [Model] 初始化双塔 Embedding 模型...")
        
        # --- 塔 A: 价格形态通道 (Price Tower) ---
        price_input = Input(shape=(config.INPUT_WINDOW, 1), name='price_input')
        x = Conv1D(32, 5, activation='relu', padding='same')(price_input)
        x = Conv1D(64, 5, activation='relu', padding='same')(x)
        x = GlobalAveragePooling1D()(x)  # 输出维度: 64
        
        # --- 塔 B: 时间感知通道 (Time Tower) ---
        # 输入: [Hour_Index, Weekday_Index]
        time_input = Input(shape=(2,), name='time_input')
        
        # 拆分特征用于不同的 Embedding 层
        # Slice层: 取第0列(Hour), 取第1列(Weekday)
        hour_idx = tf.gather(time_input, [0], axis=1)
        week_idx = tf.gather(time_input, [1], axis=1)
        
        # Embedding 层: 学习时间的"语义"
        # 24小时 -> 4维向量
        emb_h = Embedding(input_dim=24, output_dim=config.EMBED_HOUR_DIM)(hour_idx)
        emb_h = Flatten()(emb_h)
        
        # 5个工作日 -> 2维向量
        emb_w = Embedding(input_dim=5, output_dim=config.EMBED_WEEK_DIM)(week_idx)
        emb_w = Flatten()(emb_w)
        
        # 合并时间特征
        time_features = Concatenate()([emb_h, emb_w])
        
        # --- 融合层 (Fusion) ---
        # 将"价格特征(64)"与"时间特征(6)"拼接 -> 70维特征
        combined = Concatenate()([x, time_features])
        
        z = Dense(128, activation='relu')(combined)
        z = Dropout(0.3)(z)
        output = Dense(config.OUTPUT_STEPS, activation='linear', name='output')(z)
        
        # 构建模型
        model = Model(inputs=[price_input, time_input], outputs=output)
        model.compile(optimizer='adam', loss='mse')
        model.summary()
        return model

    def _extract_time_features(self, timestamps):
        """辅助函数: 将 Unix Timestamp 转换为 [Hour, Weekday]"""
        features = []
        for ts in timestamps:
            dt = datetime.utcfromtimestamp(ts)
            # Hour: 0-23, Weekday: 0-4 (Monday is 0)
            # 注意: 金融数据周末通常无数据，若有需处理为0或特殊ID
            wd = dt.weekday()
            if wd > 4:  # 简单处理周末归为周五
                wd = 4
            features.append([dt.hour, wd])
        return np.array(features)

    def train(self, prices_list, timestamps_list):
        """
        接收价格列表和时间戳列表 -> 执行 Z-Score 预处理 -> 训练
        """
        if len(prices_list) < config.INPUT_WINDOW + config.TOTAL_PREDICT_TICKS + 100:
            return {"status": "error", "msg": "数据不足"}

        prices_arr = np.array(prices_list)
        ts_arr = np.array(timestamps_list)
        
        X_price, X_time, y = [], [], []
        
        # 步长采样生成训练集
        limit = len(prices_arr) - config.INPUT_WINDOW - config.TOTAL_PREDICT_TICKS
        # 训练采样步长设为 20，避免数据重叠过多导致训练太慢
        stride = 20
        
        for i in range(0, limit, stride):
            # 1. 价格窗口处理 (Z-Score)
            window = prices_arr[i : i+config.INPUT_WINDOW]
            mean = np.mean(window)
            std = np.std(window)
            if std < 1e-6: 
                std = 1e-6
            norm_input = (window - mean) / std
            
            # 2. 时间特征提取
            # 取窗口最后一个点的时间戳作为"当前时间"
            current_ts = ts_arr[i + config.INPUT_WINDOW - 1]
            time_feat = self._extract_time_features([current_ts])[0]
            
            # 3. 标签处理
            future = prices_arr[i+config.INPUT_WINDOW : i+config.INPUT_WINDOW+config.TOTAL_PREDICT_TICKS : config.PREDICT_STRIDE]
            norm_target = (future - mean) / std
            
            X_price.append(norm_input)
            X_time.append(time_feat)
            y.append(norm_target)
            
        X_price = np.array(X_price).reshape(-1, config.INPUT_WINDOW, 1)
        X_time = np.array(X_time)  # Shape: (Batch, 2)
        y = np.array(y)
        
        print(f"🏋️‍♂️ [Model] 双模态训练开始，样本数: {len(X_price)}...")
        # Keras 支持多输入: 传入字典或列表
        history = self.model.fit(
            {'price_input': X_price, 'time_input': X_time}, 
            {'output': y},
            epochs=config.EPOCHS, 
            batch_size=config.BATCH_SIZE,
            validation_split=0.2,
            verbose=1
        )
        
        self.model.save(config.MODEL_PATH)
        loss = history.history['val_loss'][-1]
        return {"status": "ok", "val_loss": float(loss)}

    def predict(self, raw_window, current_timestamp):
        """
        接收最新窗口数据和时间戳 -> 归一化 -> 推理 -> 反归一化
        
        Args:
            raw_window: 价格窗口列表
            current_timestamp: 当前时间戳 (Unix timestamp)
        """
        if len(raw_window) < config.INPUT_WINDOW:
            return None
            
        # 1. 价格处理
        arr = np.array(raw_window)
        mean = np.mean(arr)
        std = np.std(arr)
        if std < 1e-6: 
            std = 1e-6
        norm_input = (arr - mean) / std
        inp_price = norm_input.reshape(1, config.INPUT_WINDOW, 1)
        
        # 2. 时间处理
        inp_time = self._extract_time_features([current_timestamp])
        
        # 3. 双塔推理
        pred_z = self.model(
            {'price_input': inp_price, 'time_input': inp_time}, 
            training=False
        ).numpy()[0]
        
        # 反归一化还原为价格
        pred_prices = (pred_z * std) + mean
        
        # 转为相对路径 (相对于当前价格的差值)
        current_price = arr[-1]
        relative_path = pred_prices - current_price
        
        return relative_path.tolist()