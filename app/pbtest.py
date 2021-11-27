import pushbullet
import argparse
import asyncio
import os
import uuid
from secrets import token_urlsafe

def get_args():
    parser = argparse.ArgumentParser(description="Send a pushbullet notification")
    parser.add_argument("-k", "--key", help="API key", required=False, default=os.environ["PUSHBULLET_API_KEY"])
    parser.add_argument("-t", "--title", help="Title of the notification", required=True)
    parser.add_argument("-m", "--message", help="Message of the notification", required=True)
    parser.add_argument("-l", "--link", help="Link of the notification", required=False)
    parser.add_argument("-f", "--file", help="File to send", required=False)
    parser.add_argument("-u", "--url", help="URL to send", required=False)
    parser.add_argument("-d", "--device", help="Device to send to", required=False)
    parser.add_argument("-c", "--channel", help="Channel to send to", required=False)
    parser.add_argument("-s", "--silent", help="Silent mode", required=False, action="store_true")
    return parser.parse_args()

async def process_args(args, pb):
    if args.link:
        pb.push_link(args.title, args.link, args.message, args.device, channel=args.channel)
    elif args.url:
        pb.push_file(file_name=str(uuid.uuid4())+".png", file_url=args.url, file_type="image/png", title=args.title, body=args.message, device=args.device, channel=args.channel)
    elif args.file:
        with open(args.file, "rb") as f:
            file_data = pb.upload_file(f, os.path.basename(f.name))
        pb.push_file(**file_data)
    else:
        pb.push_note(args.title, args.message, args.device, channel=args.channel)

def on_exit():
    print("Notification sent")
    exit(0)

if __name__ == "__main__":
    args = get_args()

    pb = pushbullet.Pushbullet(args.key, token_urlsafe(32))

    asyncio.run(process_args(args, pb))
    
    on_exit()