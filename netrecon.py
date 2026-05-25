import sys
import csv
import socket
import requests

def get_geolocation(target_ip):
    """
    Fetches geolocation data for an IP using the ip-api public API.
    """
    try:
        url = f"http://ip-api.com/json/{target_ip}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data
    except Exception as e:
        pass
    return None

def scan_ports(target_ip, port_limit=1024):
    """
    Scans the specified number of TCP ports on a target IP.
    """
    print(f"[*] Scanning {target_ip} for the first {port_limit} TCP ports...")
    open_ports = []
    
    for port in range(1, port_limit + 1):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            result = sock.connect_ex((target_ip, port))
            if result == 0:
                print(f"[+] Port {port} is OPEN")
                try:
                    # Attempt to grab service banner
                    sock.send(b"Hello\r\n")
                    banner = sock.recv(1024).decode('utf-8', errors='ignore').strip()
                except:
                    banner = "Unknown"
                open_ports.append({'port': port, 'service': banner})
            sock.close()
        except KeyboardInterrupt:
            print("\n[!] Scan interrupted by user.")
            break
        except Exception:
            pass
            
    return open_ports

def main():
    if len(sys.argv) != 3:
        print("Usage: python netrecon.py <target_ip> <output.csv>")
        sys.exit(1)

    target_ip = sys.argv[1]
    output_csv = sys.argv[2]

    # Resolve target to IP
    try:
        target_ip = socket.gethostbyname(target_ip)
    except socket.gaierror:
        print(f"[!] Could not resolve {target_ip}. Exiting.")
        sys.exit(1)

    # 1. Fetch Geolocation
    print(f"[*] Fetching geolocation for target: {target_ip}")
    geo_data = get_geolocation(target_ip)
    
    if not geo_data:
        print("[!] Failed to retrieve geolocation data.")

    # 2. Scan Ports
    open_ports = scan_ports(target_ip)

    # 3. Write to CSV
    print(f"[*] Saving results to {output_csv}")
    try:
        with open(output_csv, mode='w', newline='', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file)
            
            # CSV Headers
            writer.writerow(['Target IP', 'Country', 'Region', 'City', 'ISP', 'Open Port', 'Banner', 'Status', 'message'])
            
            if open_ports:
                for p in open_ports:
                    writer.writerow([
                        target_ip,
                        geo_data.get('country'),
                        geo_data.get('regionName'),
                        geo_data.get('city'),
                        geo_data.get('isp'),
                        p['port'],
                        p['service'],
                        geo_data.get('status'),
                        geo_data.get('message')
                    ])
            else:
                # If no ports are open, log geolocation data anyway
                writer.writerow([
                    target_ip,
                    geo_data.get('country'),
                    geo_data.get('regionName'),
                    geo_data.get('city'),
                    geo_data.get('isp'),
                    'None',
                    'None',
                    geo_data.get('status'),
                    geo_data.get('message')
                ])
        print("[*] Scan complete. Output successfully generated.")
    except IOError as e:
        print(f"[!] Error writing to CSV: {e}")

if __name__ == "__main__":
    main()
