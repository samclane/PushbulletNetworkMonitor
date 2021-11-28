import pushbullet
import argparse
import asyncio
import os
from secrets import token_urlsafe

from network_scanner import NetworkScanner, HostnameScanStrategy

def get_args():
    parser = argparse.ArgumentParser(description="Send a pushbullet notification")
    parser.add_argument("-k", "--key", help="API key", required=False, default=os.environ["PUSHBULLET_API_KEY"])
    parser.add_argument("-d", "--device", help="Device to send to", required=False)
    parser.add_argument("-c", "--channel", help="Channel to send to", required=False)
    parser.add_argument("-s", "--silent", help="Silent mode", required=False, action="store_true")
    return parser.parse_args()

def on_exit():
    print("Notification sent")
    exit(0)

if __name__ == "__main__":
    args = get_args()

    pb = pushbullet.Pushbullet(args.key, token_urlsafe(32))

    ns = NetworkScanner(ip='192.168.0.x', hostname='DIETPI', strategy=HostnameScanStrategy)

    async def callback(ip=None, mac=None, hostname=None):
        pb.push_note("Network Callback", f"IP: {ip} MAC: {mac} Hostname: {hostname}", device=args.device, channel=args.channel)

    try:
        asyncio.run(ns.monitor(cb=callback, interval=5))
    finally:
        on_exit()