import asyncio

async def work():
    print(asyncio.get_event_loop())
    print(42)

async def loop(coro, wait_time):
    while True:
        await asyncio.create_task(coro())
        await asyncio.sleep(wait_time)

async def main():
    await asyncio.create_task(loop(work, 1))

    # 3.11 way:
    ''' 
    async with asyncio.TaskGroup() as tg:
        tg.create_task(loop(work, 1))
    '''


if __name__ == '__main__':
    asyncio.run(main())