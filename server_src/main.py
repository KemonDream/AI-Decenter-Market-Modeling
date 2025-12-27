from database import DatabaseManager
from model_engine import ModelEngine
from server_core import ServerCore

def main():
    print("=== TradeBrain v1.0 启动 ===")
    
    # 1. 初始化各模块
    db = DatabaseManager()
    model = ModelEngine()
    
    # 2. 注入依赖并启动服务器
    server = ServerCore(db, model)
    server.start()

if __name__ == "__main__":
    main()