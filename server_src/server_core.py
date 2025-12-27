"""Core server module for business logic orchestration.

Handles request processing, routing, and coordination with database and model.
Network communication is delegated to socket_handler module.
"""
import config
from socket_handler import SocketHandler


class ServerCore:
    """Business logic orchestrator for TradeBrain v1.0.
    
    Responsibilities:
    - Request routing and processing
    - Database and model coordination
    - Business rule implementation
    
    Network communication is handled by SocketHandler.
    """

    def __init__(self, db, model):
        """Initialize ServerCore with injected dependencies.
        
        Args:
            db: DatabaseManager instance
            model: ModelEngine instance
        """
        self.db = db
        self.model = model
        self.socket_handler = SocketHandler(request_processor=self.process_request)

    def start(self):
        """Start the server with network listener."""
        print("🚀 [Server] ServerCore initialized and running.")
        print("📊 Database and Model ready for predictions.")
        
        # Delegate network layer to SocketHandler
        self.socket_handler.start(config.HOST, config.PORT)

    def stop(self):
        """Stop the server gracefully."""
        self.socket_handler.stop()

    def process_request(self, req):
        """Process incoming request and dispatch to appropriate handler.
        
        This is the main entry point for business logic processing.
        
        Args:
            req: Dictionary with request type and parameters
            
        Returns:
            Dictionary with response data
        """
        req_type = req.get('type')
        
        try:
            if req_type == 'FEED_DATA':
                return self._handle_feed_data(req)
            elif req_type == 'PREDICT':
                return self._handle_predict(req)
            elif req_type == 'TRAIN':
                return self._handle_train(req)
            else:
                return {"status": "error", "msg": f"Unknown request type: {req_type}"}
        except Exception as e:
            return {"status": "error", "msg": str(e)}

    def _handle_feed_data(self, req):
        """Handle FEED_DATA request - save market tick data.
        
        Expected format: {"type": "FEED_DATA", "data": [[timestamp, price], ...]}
        """
        data = req.get('data', [])
        if not data:
            return {"status": "error", "msg": "No data provided"}
        
        # 调用数据库保存数据
        count = self.db.save_bulk_data(data)
        return {"status": "saved", "count": count}

    def _handle_predict(self, req):
        """Handle PREDICT request - get price prediction.
        
        Expected format: {"type": "PREDICT", "price": <float>}
        """
        price = req.get('price')
        if price is None:
            return {"status": "error", "msg": "No price provided"}
        
        # 简单逻辑：如果有足够数据则返回预测路径，否则等待
        training_data = self.db.get_training_data(limit=config.INPUT_WINDOW)
        
        if len(training_data) < config.INPUT_WINDOW:
            return {
                "type": "WAIT",
                "msg": f"Insufficient data: {len(training_data)}/{config.INPUT_WINDOW}"
            }
        
        # 这里可以调用模型进行真实预测
        # 现在返回 PATH 类型的模拟响应
        return {
            "type": "PATH",
            "price": price,
            "msg": "Prediction available"
        }

    def _handle_train(self, req):
        """Handle TRAIN request - trigger model training.
        
        Expected format: {"type": "TRAIN"}
        """
        # 获取训练数据
        training_data = self.db.get_training_data(limit=config.TRAIN_LIMIT)
        
        if len(training_data) < config.INPUT_WINDOW + config.TOTAL_PREDICT_TICKS:
            return {
                "status": "error",
                "msg": "数据不足: 需要至少 {} 条数据".format(
                    config.INPUT_WINDOW + config.TOTAL_PREDICT_TICKS
                )
            }
        
        # 调用模型训练
        try:
            result = self.model.train(training_data)
            return result
        except Exception as e:
            return {"status": "error", "msg": str(e)}
