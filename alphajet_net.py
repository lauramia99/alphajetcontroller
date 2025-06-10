#!/usr/bin/env python3
"""
AlphaJET Printer Network Client

Provides functions to send GP commands over TCP and transfer files via FTP to an alphaJET printer.
Target printer IP: 192.168.1.185
GP command port: 3000
FTP port: 21
"""
import socket
from ftplib import FTP, FTP_TLS
import xml.etree.ElementTree as ET
import os

# Printer configuration (adjust as needed)
HOST = "192.168.1.185"
GP_PORT = 3000
FTP_PORT = 21

# FTP credentials (update securely)
FTP_USER = "administrator"
FTP_PASS = "1324"


def send_gp_command(gp_body: str, timeout: float = 5.0) -> str:
    """
    Send a <GP>...</GP> command to the printer over TCP and return the raw response.
    """
    # Ensure the body is wrapped in GP tags
    body = gp_body.strip()
    if not body.startswith("<GP>"):
        body = f"<GP>{body}</GP>"
    payload = body.encode('ascii') + b'\r\n'

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        sock.connect((HOST, GP_PORT))
        sock.sendall(payload)
        buffer = bytearray()
        while True:
            try:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                buffer.extend(chunk)
            except socket.timeout:
                break

    # Decode to text, preserving any junk
    raw = buffer.decode('ascii', errors='ignore')
    return raw


def parse_gp_response(raw: str) -> dict:
    """
    Extract the <GP>...</GP> XML block from raw, then parse into a dict of tag -> text.
    Strips any extra data before or after the <GP> element.
    """
    # Find the first and last GP tags
    start = raw.find('<GP')
    end = raw.rfind('</GP>')
    if start == -1 or end == -1:
        print(f"[Error] GP tags not found in response:\n{raw}")
        return {}

    xml_str = raw[start:end + len('</GP>')]
    try:
        root = ET.fromstring(xml_str)
        return {child.tag: child.text for child in root}
    except ET.ParseError as e:
        print(f"[Error] Failed to parse GP XML: {e}\nXML block:\n{xml_str}")
        return {}


def upload_file_ftp(local_path: str, remote_dir: str = "/", use_tls: bool = False) -> None:
    """
    Upload a file to the printer via FTP.
    """
    ftp_cls = FTP_TLS if use_tls else FTP
    with ftp_cls() as ftp:
        ftp.connect(HOST, FTP_PORT)
        ftp.login(FTP_USER, FTP_PASS)
        if use_tls:
            ftp.prot_p()
        ftp.cwd(remote_dir)
        filename = os.path.basename(local_path)
        with open(local_path, 'rb') as f:
            ftp.storbinary(f"STOR {filename}", f)


def download_file_ftp(remote_filename: str, local_dir: str = ".", use_tls: bool = False) -> None:
    """
    Download a file from the printer via FTP.
    """
    ftp_cls = FTP_TLS if use_tls else FTP
    with ftp_cls() as ftp:
        ftp.connect(HOST, FTP_PORT)
        ftp.login(FTP_USER, FTP_PASS)
        if use_tls:
            ftp.prot_p()
        local_path = os.path.join(local_dir, remote_filename)
        with open(local_path, 'wb') as f:
            ftp.retrbinary(f"RETR {remote_filename}", f.write)


if __name__ == "__main__":
    # Example: Query printer status
    print("=== Printer Status ===")
    raw_status = send_gp_command("<STATUS/>")
    print("Raw response:\n", raw_status)
    status = parse_gp_response(raw_status)
    for tag, text in status.items():
        print(f"{tag}: {text}")

    # Example: Upload a label template (uncomment to use)
    # upload_file_ftp("label_template.lbl", remote_dir="/labels")

    # Example: Download a log file (uncomment to use)
    # download_file_ftp("print.log", local_dir="./logs")
