import asyncio
import subprocess
import logging
from abc import ABC, abstractmethod
from typing import Callable, Optional

logger = logging.getLogger('network_scanner')
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)


class ScanStrategy(ABC):
    def __init__(self, interface):
        self.interface = interface
    
    @abstractmethod
    async def on_network(self):
        pass


class IpScanStrategy(ScanStrategy):
    def __init__(self, interface, ip=None):
        super().__init__(interface)
        self.interface = interface
        self.ip = ip or self.interface.ip
    
    async def on_network(self):
        arpa = subprocess.check_output(("arp", "-a")).decode("ascii")
        return self.ip in arpa


class MacScanStrategy(ScanStrategy):
    def __init__(self, interface, mac=None):
        super().__init__(interface)
        self.interface = interface
        self.mac = mac or self.interface.mac
    
    async def on_network(self):
        arpa = subprocess.check_output(("arp", "-a")).decode("ascii")
        return self.mac in arpa


class HostnameScanStrategy(IpScanStrategy):
    def __init__(self, interface, hostname=None):
        super().__init__(interface, ip=interface.ip)
        self.prefix = self.interface.prefix
        self.hostname = hostname or self.interface.hostname
    
    async def on_network(self):
        tasks = [asyncio.create_task(self.interface.ping(self.prefix + str(i), get_hostname=True)) for i in range(255)]
        ping_output = await asyncio.gather(*tasks)
        return any(self.hostname in x for x in ping_output)


class NetworkScanner:
    def __init__(self, ip=None, mac=None, hostname=None, strategy=IpScanStrategy):
        self.ip = ip
        self._mac = mac
        self.hostname = hostname
        self.loop = asyncio.get_event_loop()
        self.strategy = strategy(self)

    @property
    def mac(self):
        if not self._mac:
            return None
        return self._mac.lower().replace(':','-')

    @property
    def prefix(self):
        return '.'.join(self.ip.split('.')[0:3]) + '.'

    @property
    def fullname(self):
        return "\t".join(map(str, [self.ip, self.mac, self.hostname]))

    async def ping(self, ip, get_hostname=False):
        proc = await asyncio.create_subprocess_shell(' '.join(['ping', '-n', '1','-w','100','-a' if get_hostname else '', ip]), stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await proc.communicate()
        if stderr:
            logger.error(stderr.decode())
            return stderr.decode()
        elif stdout:
            logger.debug(stdout.decode())
            return stdout.decode()

    async def scan_network(self):
        """Currently just returns nasty network output. Useful for string-matching though. """
        tasks = [asyncio.create_task(self.ping(self.prefix + str(i))) for i in range(255)]
        await asyncio.gather(*tasks)
        arpa = subprocess.check_output(("arp", "-a")).decode("ascii")
        return [x for x in arpa.split('\n') if self.prefix in x]

    async def on_network(self):
        return await self.strategy.on_network()

    async def monitor(self, cb: Callable, interval=1, cb_on_change_only=False):
        state_is_connected: Optional[bool] = None
        while True:
            await self.scan_network()
            if await self.on_network():
                logger.info(f"{self.fullname} is on the network")
                if cb and (not state_is_connected or not cb_on_change_only):
                    await cb(ip=self.ip, mac=self.mac, hostname=self.hostname)
                state_is_connected = True
            else:
                logger.info(f"{self.ip} is not on the network")
                if cb and (state_is_connected or not cb_on_change_only):
                    await cb(ip=None, mac=None, hostname=None)
                state_is_connected = False
            await asyncio.sleep(interval)


if __name__ == "__main__":
    # print(asyncio.run(scan_network()))
    ns = NetworkScanner(ip='192.168.0.x', hostname='DIETPI', strategy=HostnameScanStrategy)
    async def report(ip=None, mac=None, hostname=None):
        logger.info(f"cb: {ip} {mac} {hostname}")
    logger.info(asyncio.run(ns.monitor(cb=report)))