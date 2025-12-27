"""Network and socket communication layer for TradeBrain server.

Handles all TCP socket operations, client connection management, and 
protocol-level communication (JSON encoding/decoding).
"""
import socket
import struct
import threading
import json
import config


class SocketHandler:
    """Manages TCP server socket and client connections.
    
    Responsibilities:
    - TCP socket creation and lifecycle management
    - Client connection acceptance and threading
    - Low-level socket I/O operations
    - Message buffering and framing
    """

    def __init__(self, request_processor):
        """Initialize socket handler with request processor callback.
        
        Args:
            request_processor: Callable that processes dict requests and returns dict responses
        """
        self.request_processor = request_processor
        self.running = False
        self.server_socket = None

    def start(self, host, port):
        """Start the TCP server and listen for connections.
        
        Args:
            host: Server host address (e.g., '127.0.0.1')
            port: Server port number (e.g., 8888)
        """
        print(f"🚀 [Network] Starting TCP server on {host}:{port}")
        
        self.running = True
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # Socket options for proper cleanup
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack('ii', 1, 0))
        
        try:
            self.server_socket.bind((host, port))
            self.server_socket.listen(5)
            print(f"✅ [Network] Listening on {host}:{port}")
            
            while self.running:
                try:
                    client_socket, addr = self.server_socket.accept()
                    print(f"📱 [Network] New connection from {addr}")
                    
                    # Handle each client in a separate daemon thread
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client_socket, addr),
                        daemon=True
                    )
                    client_thread.start()
                    
                except KeyboardInterrupt:
                    print("\n⏸️ [Network] Server interrupted by user.")
                    break
                except OSError as e:
                    if self.running:
                        print(f"❌ [Network] Socket error: {e}")
                        
        except Exception as e:
            print(f"❌ [Network] Startup error: {e}")
        finally:
            self._shutdown()

    def stop(self):
        """Stop the server gracefully."""
        self.running = False
        self._shutdown()

    def _shutdown(self):
        """Cleanup server socket resources."""
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.shutdown(socket.SHUT_RDWR)
            except (OSError, ConnectionError):
                pass
            finally:
                self.server_socket.close()
        print("🛑 [Network] Server stopped and port released.")

    def _handle_client(self, client_socket, addr):
        """Handle a single client connection with buffered message processing.
        
        Args:
            client_socket: Connected socket object
            addr: Client address tuple (ip, port)
        """
        print(f"🔗 [Network] Client connected: {addr}")
        buffer = ""
        
        try:
            while self.running:
                # Receive data from client
                data = client_socket.recv(config.BUFFER_SIZE).decode('utf-8')
                if not data:
                    break  # Client disconnected normally
                
                buffer += data
                
                # Process complete messages (delimited by newlines)
                while '\n' in buffer:
                    msg_str, buffer = buffer.split('\n', 1)
                    msg_str = msg_str.strip()
                    
                    if not msg_str:
                        continue
                    
                    # Send request to processor and handle response
                    self._process_message(client_socket, addr, msg_str)
                    
        except Exception as e:
            print(f"⚠️ [Network] Connection error from {addr}: {e}")
        finally:
            self._close_client(client_socket, addr)

    def _process_message(self, client_socket, addr, msg_str):
        """Parse JSON message and send response back to client.
        
        Args:
            client_socket: Connected socket for sending response
            addr: Client address
            msg_str: Raw message string
        """
        try:
            # Parse JSON request
            req = json.loads(msg_str)
            print(f"📨 [Network] Request from {addr}: {req}")
            
            # Process request using business logic
            resp = self.request_processor(req)
            
            # Send JSON response
            response_json = json.dumps(resp) + "\n"
            client_socket.sendall(response_json.encode('utf-8'))
            print(f"📤 [Network] Response to {addr}: {resp}")
            
        except json.JSONDecodeError as e:
            # Handle malformed JSON gracefully
            error_resp = {"status": "error", "msg": f"Invalid JSON: {str(e)}"}
            response_json = json.dumps(error_resp) + "\n"
            client_socket.sendall(response_json.encode('utf-8'))
            print(f"❌ [Network] JSON parse error from {addr}: {e}")

    def _close_client(self, client_socket, addr):
        """Close client connection and cleanup.
        
        Args:
            client_socket: Socket to close
            addr: Client address
        """
        try:
            client_socket.close()
        except:
            pass
        print(f"🔌 [Network] Client disconnected: {addr}")
