import asyncio
import binascii

import aioconsole
import serial_asyncio


class Repl(asyncio.Protocol):
    def connection_made(self, transport):
        self.transport = transport
        print('port opened:', self.transport)
        asyncio.ensure_future(self.send())

    def data_received(self, data):
        print('<-', repr(data), f'({binascii.hexlify(data)})')

    def connection_lost(self, exc):
        print('port closed:', exc)
        self.transport.loop.stop()

    async def send(self):
        while True:
            line = await aioconsole.ainput()
            try:
                msg = binascii.unhexlify(line)
            except ValueError as e:
                await aioconsole.aprint('not sending to device:', e)
                continue
            else:
                self.transport.write(msg)
                await aioconsole.aprint('->', repr(msg))

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    coro = serial_asyncio.create_serial_connection(
        loop,
        Repl,
        '/dev/ttyUSB0',
        baudrate=115200,
    )
    loop.run_until_complete(coro)
    loop.run_forever()
    loop.close()
