from typing import Union

import aioredis
from aioredis import Redis

from app import settings


class SuperRedis:
    def __init__(
        self,
        address: str,
        pool_minsize: int = settings.redis.redis_pool_minsize,
        pool_maxsize: int = settings.redis.redis_pool_maxsize,
    ) -> None:
        self._redis_address = address
        self._redis_pool_minsize = pool_minsize
        self._redis_pool_maxsize = pool_maxsize

    @property
    async def _client(self) -> Redis:
        """
        创建数据库连接池

        Returns
        -------
        redis_pool
        """
        if getattr(self, "_redis_pool", None) is None:
            self._redis_pool = await aioredis.create_redis_pool(
                self._redis_address,
                minsize=self._redis_pool_minsize,
                maxsize=self._redis_pool_maxsize,
            )

        return self._redis_pool

    async def pipeline(self):
        """
        批量执行命令

        Returns
        -------
        pipeline

        Example
        -------

        >>> pipe = G.hq_redis.pipeline()
        >>> fut1 = pipe.incr('foo') # NO `await` as it will block forever!
        >>> fut2 = pipe.incr('bar')
        >>> result = await pipe.execute()
        >>> result
        [1, 1]
        >>> await asyncio.gather(fut1, fut2)
        [1, 1]
        >>> #
        >>> # The same can be done without pipeline:
        >>> #
        >>> fut1 = G.hq_redis.incr('foo')    # the 'INCRY foo' command already sent
        >>> fut2 = G.hq_redis.incr('bar')
        >>> await asyncio.gather(fut1, fut2)
        [2, 2]
        """
        client = await self._client
        return client.pipeline()

    async def execute(self, command, *args, **kwargs) -> bool:
        """
        原生命令支持

        Parameters
        ----------
        command
        args
        kwargs

        Returns
        -------

        """
        client = await self._client
        return await client.execute(command, *args, **kwargs)

    async def flush(self) -> None:
        """
        清空数据库

        Returns
        -------

        Examples
        -------
        >>> await G.hq_redis.flush()
        """
        client = await self._client
        await client.flushdb()

    async def close(self) -> None:
        """
        关闭数据库连接

        Returns
        -------

        Examples
        -------
        >>> await G.hq_redis.close()
        """
        client = await self._client
        client.close()
        await client.wait_closed()

    # str command
    async def add(
        self,
        key: Union[str, int],
        value: Union[str, int],
        expire: int = settings.redis.default_time_out,
    ) -> bool:
        client = await self._client
        in_cache = await client.get(key)
        if in_cache is None:
            return False
        return await client.set(key, value, expire=expire)

    async def get(
        self,
        key: Union[str, int],
        default: Union[str, int] = None,
        encoding: Union[str, None] = "utf8",
    ) -> bool:
        client = await self._client
        cached_value = await client.get(key, encoding=encoding)
        return cached_value if cached_value is not None else default

    async def set(
        self,
        key: Union[str, int],
        value: Union[str, int],
        expire: int = settings.redis.default_time_out,
    ) -> bool:
        client = await self._client
        return await client.set(key, value, expire=expire)

    async def delete(self, key: Union[str, int]) -> bool:
        client = await self._client
        return await client.delete(key)

    # hash command
    async def hget(
        self, key: Union[str, int], field: Union[str, int], encoding: str = "utf8"
    ):
        """
        获取哈希字段的值

        Parameters
        ----------
        key
        field
        encoding

        Returns
        -------

        Example
        -------
        >>>await G.hq_redis.hget(PORTFOLIO_HASH, portfolio_id)
        """
        client = await self._client
        cached_value = await client.hget(key, field, encoding=encoding)
        return cached_value

    async def hgetall(self, key: Union[str, int], default: Union[str, int] = None):
        """
        获取哈希中所有的字段以及对应的值

        Parameters
        ----------
        key
        default

        Returns
        -------

        """
        client = await self._client
        cached_value = await client.hgetall(key, encoding="utf8")
        return cached_value if cached_value is not None else default

    async def hmset_dict(self, key, *args, **kwargs):
        """
        哈希批量赋值

        Parameters
        ----------
        key
        args
        kwargs

        Returns
        -------

        Examples
        -------
        >>> await G.hq_redis.hmset_dict(
        ...     'key', {'field1': 'value1', 'field2': 'value2'})

        or keyword arguments can be used:

        >>> await G.hq_redis.hmset_dict(
        ...     'key', field1='value1', field2='value2')

        or dict argument can be mixed with kwargs:

        >>> await G.hq_redis.hmset_dict(
        ...     'key', {'field1': 'value1'}, field2='value2')

        .. note:: ``dict`` and ``kwargs`` not get mixed into single dictionary,
           if both specified and both have same key(s) -- ``kwargs`` will win:

           >>> await G.hq_redis.hmset_dict('key', {'foo': 'bar'}, foo='baz')
           >>> await G.hq_redis.hget('key', 'foo', encoding='utf-8')
           'baz'
        """
        client = await self._client
        return await client.hmset_dict(key, *args, **kwargs)

    async def hdel(self, key, field, *fields):
        """
        删除一个或者多个哈希值
        Parameters
        ----------
        key
        field
        fields

        Returns
        -------

        """
        client = await self._client
        return await client.hdel(key, field, *fields)

    # set command
    async def smembers(self, key: Union[str, int], default: Union[str, int] = None):
        """
        获取集合的全部值

        Parameters
        ----------
        key
        default

        Returns
        -------

        Examples
        -------
        >>> await G.hq_redis.smembers("symbol_exchange_list:")
        """
        client = await self._client
        cached_value = await client.smembers(key, encoding="utf8")
        return cached_value if cached_value is not None else default

    async def sadd(self, key, member, *members):
        """
        向集合中添加一个或多个成员

        Parameters
        ----------
        key
        member
        members

        Returns
        -------

        Examples
        -------
        >>> portfolio_list=["a", "b"]
        >>> await G.hq_redis.sadd("portfolio", *portfolio_list)
        """
        client = await self._client
        return await client.sadd(key, member, *members)
