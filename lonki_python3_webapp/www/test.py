import sys
import asyncio

from .models import User,Blog,Comment
from .orm import create_pool


# async def test():
#     await orm.create_pool(loop=loop,user='root',password='zhujie8721*',db='project')
#
#     user = User(name='lonki',email='zhujieworkroom@126.com',passwd='lonki8721@',image='www.baidu.com')
#     print(user)
#     await user.save()
#
# loop = asyncio.get_event_loop()
# loop.run_until_complete(test())
# loop.close()

@asyncio.coroutine
def test(loop):
    yield from create_pool(loop=loop, host='localhost', port=3306, user='root', password='zhujie8721*', db='project')
    u = User(name='lonki', email='zhujieworkroom@126.com', passwd='lonki8721@', image='www.baidu.com')
    yield from u.save()

loop = asyncio.get_event_loop()
tasks = [test(loop)]
loop.run_until_complete(asyncio.wait(tasks))
loop.close()
