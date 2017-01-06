import abc
import datetime
import http.client
import json
from typing import (
    Any,
    BinaryIO,
    Dict,
    List,
    Type,
    TypeVar,
    Union,
)

import langedge.models


T = TypeVar('T', bound='Model')


class Model(metaclass=abc.ABCMeta):
    def __str__(self) -> str:
        return self.__dict__.__str__()

    @classmethod
    @abc.abstractmethod
    def from_response(cls: Type[T], response: Union[http.client.HTTPResponse, BinaryIO]) -> Any:
        ...


class Account(Model):
    def __init__(self, *, email, full_name, display_name, language_code) -> None:
        self.email = email
        self.full_name = full_name
        self.display_name = display_name
        self.language_code = language_code

    @classmethod
    def from_response(
            cls: Type['Account'], response: Union[http.client.HTTPResponse, BinaryIO]
    ) -> 'Account':
        return cls(**_read_response_as_json(response))


class Balance(Model):
    def __init__(  # type: ignore
            self,
            *,
            currency: langedge.models.Currency,  # type: ignore
            credits: float
    ) -> None:
        self.currency = currency  # type: ignore
        self.credits = credits

    @classmethod
    def from_response(
            cls: Type['Balance'], response: Union[http.client.HTTPResponse, BinaryIO]
    ) -> 'Balance':
        data = _read_response_as_json(response)
        currency = langedge.models.Currency[data.pop('currency')]  # type: ignore

        return cls(currency=currency, **data)


class Stat(Model):
    def __init__(  # type: ignore
            self,
            *,
            user_since: datetime.datetime,
            credits_spent: float,
            processing: float,
            currency: langedge.models.Currency,  # type: ignore
            customer_type: langedge.models.CustomerType,  # type: ignore
            billing_type: langedge.models.BillingType  # type: ignore
    ) -> None:
        self.user_since = user_since
        self.credits_spent = credits_spent
        self.processing = processing
        self.currency = currency  # type: ignore
        self.customer_type = customer_type  # type: ignore
        self.billing_type = billing_type  # type: ignore

    @classmethod
    def from_response(
            cls: Type['Stat'], response: Union[http.client.HTTPResponse, BinaryIO]) -> 'Stat':
        data = _read_response_as_json(response)
        user_since = datetime.datetime.fromtimestamp(data.pop('user_since'))
        currency = langedge.models.Currency[data.pop('currency')]  # type: ignore
        customer_type = langedge.models.CustomerType[data.pop('customer_type')]  # type: ignore
        billing_type = langedge.models.BillingType[data.pop('billing_type')]  # type: ignore

        return cls(
            user_since=user_since,
            currency=currency,
            customer_type=customer_type,
            billing_type=billing_type,
            **data
        )


class OrderResult(Model):
    def __init__(  # type: ignore
            self,
            *,
            order_id: int,
            job_count: int,
            credits_used: float,
            currency: langedge.models.Currency  # type: ignore
    ) -> None:
        self.order_id = order_id
        self.job_count = job_count
        self.credits_used = credits_used
        self.currency = currency  # type: ignore

    @classmethod
    def from_response(
            cls: Type['OrderResult'], response: Union[http.client.HTTPResponse, BinaryIO]
    ) -> 'OrderResult':
        data = _read_response_as_json(response)
        currency = langedge.models.Currency[data.pop('currency')]  # type: ignore

        return cls(currency=currency, **data)


class Order(Model):
    def __init__(
            self,
            *,
            order_id: int,
            total_credits: float,
            total_units: int,
            currency: langedge.models.Currency,  # type: ignore
            jobs_available: List[int],
            jobs_pending: List[int],
            jobs_reviewable: List[int],
            jobs_approved: List[int],
            jobs_revising: List[int],
            jobs_queued: int,
            total_jobs: int
    ) -> None:
        self.order_id = order_id
        self.total_credits = total_credits
        self.total_units = total_units
        self.total_jobs = total_jobs
        self.currency = currency  # type: ignore
        self.jobs_available = jobs_available
        self.jobs_pending = jobs_pending
        self.jobs_reviewable = jobs_reviewable
        self.jobs_approved = jobs_approved
        self.jobs_revising = jobs_revising
        self.jobs_queued = jobs_queued

    @classmethod
    def from_response(
            cls: Type['Order'], response: Union[http.client.HTTPResponse, BinaryIO]
    ) -> 'Order':
        data = _read_response_as_json(response)['order']
        # This API returns everything as str.
        return cls(
            order_id=int(data['order_id']),
            total_credits=float(data['total_credits']),
            currency=langedge.models.Currency[data['currency']],  # type: ignore
            jobs_available=[int(i) for i in data['jobs_available']],
            jobs_pending=[int(i) for i in data['jobs_pending']],
            jobs_reviewable=[int(i) for i in data['jobs_reviewable']],
            jobs_approved=[int(i) for i in data['jobs_approved']],
            jobs_revising=[int(i) for i in data['jobs_revising']],
            total_jobs=int(data.pop('total_jobs')),
            jobs_queued=int(data.pop('jobs_queued')),
            total_units=int(data.pop('total_units'))
        )


class Job(Model):
    def __init__(  # type: ignore
            self,
            *,
            job_id: int,
            credits: float,
            eta: int,
            order_id: int,
            currency: langedge.models.Currency,  # type: ignore
            ctime: datetime.datetime,
            status: langedge.models.JobStatus,
            slug: str,
            body_src: str,
            lc_src: langedge.models.LanguageCode,  # type: ignore
            lc_tgt: langedge.models.LanguageCode,  # type: ignore
            tier: langedge.models.Tier,  # type: ignore
            auto_approve: bool,
            callback_url: str,
            unit_count: int,
            position: int,
            body_tgt: str=None,
            custom_data: str=None
    ) -> None:
        self.job_id = job_id
        self.credits = credits
        self.eta = eta
        self.order_id = order_id
        self.currency = currency  # type: ignore
        self.ctime = ctime
        self.status = status  # type: ignore
        self.slug = slug
        self.body_src = body_src
        self.body_tgt = body_tgt
        self.lc_src = lc_src  # type: ignore
        self.lc_tgt = lc_tgt  # type: ignore
        self.tier = tier  # type: ignore
        self.callback_url = callback_url
        self.custom_data = custom_data
        self.auto_approve = auto_approve
        self.unit_count = unit_count
        self.position = position

    @classmethod
    def from_response(
            cls: Type['Job'], response: Union[http.client.HTTPResponse, BinaryIO]
    ) -> 'Job':
        ...


class _Jobs(Model):
    """This class is just for typing.

    User of this library usually don't need to touch this one.
    """
    def __init__(self, jobs: List[Job]) -> None:
        self.jobs = jobs

    @classmethod
    def _from_response(cls: Type['_Jobs'], source: Dict[str, Any]) -> Job:
        """

        This method will break argument dict.
        """
        return Job(
            currency=langedge.models.Currency[source.pop('currency')],  # type: ignore
            lc_src=langedge.models.LanguageCode[source.pop('lc_src')],  # type: ignore
            lc_tgt=langedge.models.LanguageCode[source.pop('lc_tgt')],  # type: ignore
            tier=langedge.models.Tier[source.pop('tier')],  # type: ignore
            status=langedge.models.JobStatus[source.pop('status')],  # type: ignore
            auto_approve=bool(source.pop('auto_approve')),
            ctime=datetime.datetime.fromtimestamp(source.pop('ctime')),
            **source
        )

    @classmethod
    def from_response(
            cls: Type['_Jobs'], response: Union[http.client.HTTPResponse, BinaryIO]
    ) -> '_Jobs':
        return cls([cls._from_response(job) for job in _read_response_as_json(response)['jobs']])


def _read_response_as_json(response: Union[http.client.HTTPResponse, BinaryIO]) -> Dict[str, Any]:
    return json.loads(response.read().decode())['response']
