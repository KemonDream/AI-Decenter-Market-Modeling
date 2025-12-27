import sys
from database import DatabaseManager
from model_engine import ModelEngine
from server_core import ServerCore

def main():
    print("=== TradeBrain v1.0 初始化中 ===")
    
    try:
        # 1. 初始化模块
        db = DatabaseManager()
        model = ModelEngine()
        
        # 2. 注入依赖
        server = ServerCore(db, model)
        
        # 3. 运行服务器 (此调用是阻塞的)
        server.start()
        
    except Exception as e:
        print(f"💥 系统引导失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()