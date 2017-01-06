import abc
import asyncio
import enum
import json
from typing import (
    Any,
    Awaitable,
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


def _atask(awaitable: Awaitable[Any]) -> Any:
    # I can write this function as decorator something like this:
    # def _atask(func: Callable[..., T]) -> Callable[..., T]:
    #     @functools.wraps(func)
    #     def wrapper(*args, **kwargs) -> T:
    #         with LoopContext() as loop:
    #             return loop.run_until_complete(
    #                  asyncio.Task(func(*args, **kwargs)))  # type: ignore
    #     return wrapper
    #
    # However inspect.getfullargspec cannot show argument information well with decorator.
    # One of a target of this library is any user can use this one without knowledge. Argument
    # information is an important things for that. When I solve the problem, I will make this one
    # as decorator.
    with LoopContext() as loop:
        return loop.run_until_complete(asyncio.Task(awaitable))  # type: ignore


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

        with urllib.request.urlopen(
                urllib.request.Request(url, headers=headers, method=method),
                data=encoded_data
        ) as response:
            return model.from_response(response)

    def _get(
            self,
            model: Type[langedge.models.response.T],
            path: str,
            params: Dict[str, Any]={}
    ) -> Awaitable[langedge.models.response.T]:
        return self._request('GET', model, path, params)

    def _post(
            self,
            model: Type[langedge.models.response.T],
            path: str,
            data: str,
    ) -> Awaitable[langedge.models.response.T]:
        return self._request('POST', model, path, data=data)


class Account(API):
    @property
    def path(self) -> str:
        return "account"

    def get_my_account(self) -> Awaitable[Awaitable[langedge.models.response.Account]]:
        return _atask(self._get(langedge.models.response.Account, "me"))

    def get_balance(self) -> Awaitable[Awaitable[langedge.models.response.Balance]]:
        return _atask(self._get(langedge.models.response.Balance, "balance"))

    def get_stats(self) -> Awaitable[Awaitable[langedge.models.response.Stat]]:
        return _atask(self._get(langedge.models.response.Stat, "stats"))


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
    ) -> Awaitable[langedge.models.response.OrderResult]:
        print(jobs)
        return self._post(langedge.models.response.OrderResult, "jobs", data=dump_json(
            {
                'jobs': {
                    'job_{}'.format(i): job.to_dict() for i, job in enumerate(jobs)
                }
            }
        ))

    def order(
            self, jobs: Iterable[langedge.models.request.Job]
    ) -> Awaitable[langedge.models.response.Order]:
        return _atask(self._order(jobs))

    def batch_order(
            self,
            jobs: Iterable[langedge.models.request.Job],
            max_chunk_size=50
    ) -> List[langedge.models.response.Order]:
        def _batch_order():
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

        return _atask(_batch_order())

    def _list_order_jobs(self, order_id: int) -> Awaitable[langedge.models.response.Order]:
        return self._get(langedge.models.response.Order, "order/{}".format(order_id))

    def list_order_jobs(self, order_id: int) -> Awaitable[langedge.models.response.Order]:
        return _atask(self._list_order_jobs(order_id))

    def batch_list_order_jobs(
            self, order_ids: Iterable[int]) -> List[langedge.models.response.Order]:
        def _batch_list_order_jobs():
            return [
                (yield from f) for f in asyncio.as_completed(
                    [self._list_order_jobs(order_id) for order_id in order_ids])
            ]
        return _atask(_batch_list_order_jobs())

    def list_jobs(self, job_ids: Iterable[int]) -> List[langedge.models.response.Job]:
        return _atask(self._get(
            langedge.models.response._Jobs,
            "jobs/{}".format(','.join([str(job_id) for job_id in job_ids]))
        )).jobs
