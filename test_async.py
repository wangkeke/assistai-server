import asyncio
from datetime import datetime


async def func(sleep_time):
    func_name_suffix = sleep_time     # 使用 sleep_time（函数 I/O 等待时长）作为函数名后缀，以区分任务对象
    print(f"[{datetime.now()}] 执行异步函数 {func.__name__}-{func_name_suffix}")
    print(f"[{datetime.now()}] 函数 {func.__name__}-{func_name_suffix} 执行完毕")
    return f"【[{datetime.now()}] 得到函数 {func.__name__}-{func_name_suffix} 执行结果】"


async def run():
    return await asyncio.gather(*list(func(i) for i in range(5)))


if __name__ == '__main__':
    results = asyncio.run(run())
    print(results)