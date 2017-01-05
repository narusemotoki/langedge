import abc
import datetime
import http.client
import json
from typing import (
    Any,
    BinaryIO,
    Dict,
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


class Order(Model):
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
            cls: Type['Order'], response: Union[http.client.HTTPResponse, BinaryIO]) -> 'Order':
        data = _read_response_as_json(response)
        currency = langedge.models.Currency[data.pop('currency')]  # type: ignore

        return cls(currency=currency, **data)


def _read_response_as_json(response: Union[http.client.HTTPResponse, BinaryIO]) -> Dict[str, Any]:
    raw = response.read().decode()
    print(raw)
    return json.loads(raw)['response']
