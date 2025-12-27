"""Core server module that orchestrates database and model engine."""


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

    def start(self):
        """Start the server and enter ready state."""
        print("🚀 [Server] ServerCore initialized and running.")
        print("📊 Database and Model ready for predictions.")
        print("✅ Server is operational.")
