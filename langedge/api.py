import abc
import asyncio
import enum
import functools
import json
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    Iterable,
    List,
    Type,
    TypeVar,
)
import urllib.parse
import urllib.request

import langedge.credential
import langedge.models.request
import langedge.models.response


T = TypeVar('T')


class LoopContext:
    def __init__(self) -> None:
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def __enter__(self) -> asyncio.selector_events.BaseSelectorEventLoop:  # type: ignore
        return self.loop

    def __exit__(self, type, value, traceback) -> None:
        self.loop.close()


def async_wait(func: Callable[..., T]) -> Callable[..., T]:
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> T:
        with LoopContext() as loop:
            return loop.run_until_complete(asyncio.Task(func(*args, **kwargs)))  # type: ignore
    return wrapper


class EnumEncoder(json.JSONEncoder):
    def default(self, value: Any) -> Any:
        if isinstance(value, enum.Enum):
            return value.name
        return json.JSONEncoder.default(self, value)


def dump_json(source: Dict[str, Any]) -> str:
    return json.dumps(source, cls=EnumEncoder, separators=(',', ':'))


class API(metaclass=abc.ABCMeta):
    @property
    @abc.abstractmethod
    def path(self) -> str:
        ...

    def __init__(self, credential: langedge.credential.Credential) -> None:
        self.credential = credential

    async def _request(
            self,
            method: str,
            model: Type[langedge.models.response.T],
            path: str,
            params: Dict[str, Any]={},
            data: str=None
    ) -> langedge.models.response.T:
        query = urllib.parse.urlencode(self.credential.sign(params))
        headers = {
            'Accept': "application/json",
            'User-Agent': "langedge"
        }  # type: Dict[str, Any]
        url = "{}/{}/{}?{}".format(self.credential.url, self.path, path, query)
        if data:
            encoded_data = urllib.parse.urlencode({
                'data': data
            }).encode()
            headers['Content-Length'] = len(encoded_data)
            headers['Content-Type'] = "application/x-www-form-urlencoded"
        else:
            encoded_data = None

        print("req")
        with urllib.request.urlopen(
                urllib.request.Request(url, headers=headers, method=method),
                data=encoded_data
        ) as response:
            return model.from_response(response)

    async def _get(
            self,
            model: Type[langedge.models.response.T],
            path: str,
            params: Dict[str, Any]={}
    ) -> Awaitable[langedge.models.response.T]:
        return await self._request('GET', model, path, params)

    async def _post(
            self,
            model: Type[langedge.models.response.T],
            path: str,
            data: str,
    ) -> langedge.models.response.T:
        return await self._request('POST', model, path, data=data)


class Account(API):
    @property
    def path(self) -> str:
        return "account"

    @async_wait
    def get_my_account(self) -> Awaitable[Awaitable[langedge.models.response.Account]]:
        return self._get(langedge.models.response.Account, "me")

    @async_wait
    def get_balance(self) -> Awaitable[Awaitable[langedge.models.response.Balance]]:
        return self._get(langedge.models.response.Balance, "balance")

    @async_wait
    def get_stats(self) -> Awaitable[Awaitable[langedge.models.response.Stat]]:
        return self._get(langedge.models.response.Stat, "stats")


class Dummy:
    @classmethod
    def from_response(cls, response):
        print(response.read())


class Job(API):
    @property
    def path(self) -> str:
        return "translate"

    def _order(
        self, jobs: Iterable[langedge.models.request.Job]
    ) -> Awaitable[langedge.models.response.Order]:
        return self._post(langedge.models.response.Order, "jobs", data=dump_json(
            {
                'jobs': {
                    'job_{}'.format(i): job.to_dict() for i, job in enumerate(jobs)
                }
            }
        ))

    @async_wait
    def order(
            self, jobs: Iterable[langedge.models.request.Job]
    ) -> Awaitable[langedge.models.response.Order]:
        return self._order(jobs)

    @async_wait
    def bulk_order(
            self,
            jobs: Iterable[langedge.models.request.Job],
            max_chunk_size=50
    ) -> List[langedge.models.response.Order]:
        chunks = []
        chunk = []
        previous_qualification = (None, None, None)
        for job in jobs:
            qualification = (job.lc_src, job.lc_tgt, job.tier)
            if qualification != previous_qualification or len(chunk) == max_chunk_size:
                previous_qualification = qualification
                if chunk:
                    chunks.append(chunk)
                chunk = []
            chunk.append(job)
        if chunk:
            chunks.append(chunk)

        return [
            (yield from f) for f in asyncio.as_completed(
                [self._order(jobs) for jobs in chunks])
        ]
