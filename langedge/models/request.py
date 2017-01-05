from typing import (
    Any,
    Dict,
)


import langedge.models


class DictMixin:
    def to_dict(self) -> Dict[str, Any]:
        return {
            key: value for key, value in self.__dict__.items() if value is not None
        }


class Job(DictMixin):
    def __init__(  # type: ignore
            self,
            *,
            job_type: langedge.models.JobType,
            slug: str,
            body_src: str,
            lc_src: langedge.models.LanguageCode,
            lc_tgt: langedge.models.LanguageCode,
            tier: langedge.models.Tier,
            auto_approve: bool,
            comment: str=None,
            callback_url: str=None,
            custom_data: str=None,
            force: bool=False,
            use_preferred: bool=False
    ) -> None:
        self.job_type = job_type  # type: ignore
        self.slug = slug
        self.body_src = body_src
        self.lc_src = lc_src  # type: ignore
        self.lc_tgt = lc_tgt  # type: ignore
        self.tier = tier  # type: ignore
        self.auto_approve = auto_approve
        self.comment = comment
        self.callback_url = callback_url
        self.custom_data = custom_data
        self.force = force
        self.use_preferred = use_preferred
