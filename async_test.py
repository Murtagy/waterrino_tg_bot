import asyncio

async def work():
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


asyncio.run(main())