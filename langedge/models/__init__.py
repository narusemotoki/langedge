import enum

# mypy 0.4.6 cannot check enum well.
Currency = enum.Enum('Currency', ['USD', 'JPY'])  # type: ignore
CustomerType = enum.Enum('CustomerType', ['Retail'])  # type: ignore
BillingType = enum.Enum('BillingType', ['Pre-pay'])  # type: ignore
JobType = enum.Enum('JobType', ['text'])  # type: ignore
LanguageCode = enum.Enum('LanguageCode', ['en', 'ja'])  # type: ignore
Tier = enum.Enum('Tier', ['standard', 'pro'])  # type: ignore
JobStatus = enum.Enum('JobStatus', ['available', 'reviewable'])  # type: ignore
