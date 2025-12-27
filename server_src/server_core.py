"""Core server module that orchestrates database and model engine."""
import socket
import struct
import config
import threading
import json


class ServerCore:
    """Main server orchestrator for TradeBrain v1.0.
    
    Coordinates the database manager and model engine to provide
    a unified interface for market prediction and data management.
    """

    def __init__(self, db, model):
        """Initialize ServerCore with injected dependencies.
        
        Args:
            db: DatabaseManager instance
            model: ModelEngine instance
        """
        self.db = db
        self.model = model
        self.running = False

    def start(self):
        """Start the server and enter ready state with TCP listener."""
        print("🚀 [Server] ServerCore initialized and running.")
        print("📊 Database and Model ready for predictions.")
        
        self.running = True
        
        # 创建 TCP 服务器 socket
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # 允许重用地址，避免 TIME_WAIT 导致的端口占用问题
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # 设置立即关闭选项，确保 socket 立即释放
        # SO_LINGER: (1, 0) = 立即关闭并丢弃缓冲区数据
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack('ii', 1, 0))
        
        try:
            server_socket.bind((config.HOST, config.PORT))
            server_socket.listen(5)
            print(f"✅ Server listening on {config.HOST}:{config.PORT}")
            
            while self.running:
                try:
                    # 接受客户端连接 (阻塞操作)
                    client_socket, addr = server_socket.accept()
                    print(f"📱 New connection from {addr}")
                    
                    # 在线程中处理客户端请求
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client_socket, addr),
                        daemon=True
                    )
                    client_thread.start()
                    
                except KeyboardInterrupt:
                    print("\n⏸️  Server interrupted by user.")
                    break
                except OSError as e:
                    if self.running:
                        print(f"❌ [Server] Socket error: {e}")
                    
        except Exception as e:
            print(f"❌ [Server] Error: {e}")
        finally:
            self.running = False
            try:
                server_socket.shutdown(socket.SHUT_RDWR)
            except (OSError, ConnectionError):
                # Socket 可能已经关闭，忽略异常
                pass
            finally:
                server_socket.close()
            print("🛑 Server stopped and port released.")

    def _handle_client(self, client_socket, addr):
        """Handle individual client requests with JSON protocol.
        
        Protocol:
        - FEED_DATA: Save market tick data
        - PREDICT: Get price prediction
        - TRAIN: Trigger model training
        
        Args:
            client_socket: Connected client socket
            addr: Client address tuple (ip, port)
        """
        print(f"🔗 [Server] 客户端已连接: {addr}")
        buffer = ""
        try:
            while self.running:
                # 接收客户端数据
                data = client_socket.recv(config.BUFFER_SIZE).decode('utf-8')
                if not data:
                    break  # 客户端正常断开
                
                buffer += data
                
                # 处理缓冲区中的完整消息（以换行符分割）
                while '\n' in buffer:
                    msg_str, buffer = buffer.split('\n', 1)
                    
                    # 防御：过滤空行和空白字符
                    msg_str = msg_str.strip()
                    if not msg_str:
                        continue
                    
                    try:
                        # 解析 JSON 请求
                        req = json.loads(msg_str)
                        print(f"📨 Received from {addr}: {req}")
                        
                        # 路由不同的请求类型
                        resp = self._process_request(req)
                        
                        # 发送 JSON 响应
                        response_json = json.dumps(resp) + "\n"
                        client_socket.sendall(response_json.encode('utf-8'))
                        print(f"📤 Sent to {addr}: {resp}")
                        
                    except json.JSONDecodeError as e:
                        # 脏数据处理：返回错误响应而不断开连接
                        error_resp = {"status": "error", "msg": f"Invalid JSON: {str(e)}"}
                        response_json = json.dumps(error_resp) + "\n"
                        client_socket.sendall(response_json.encode('utf-8'))
                        print(f"❌ JSON parse error from {addr}: {e}")
                    
        except Exception as e:
            print(f"⚠️ [Server] 连接异常: {e}")
        finally:
            try:
                client_socket.close()
            except:
                pass
            print(f"🔌 [Server] 客户端断开: {addr}")

    def _process_request(self, req):
        """Process incoming request and dispatch to handlers.
        
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
        finally:
            client_socket.close()
            print(f"🔌 Connection closed from {addr}")
