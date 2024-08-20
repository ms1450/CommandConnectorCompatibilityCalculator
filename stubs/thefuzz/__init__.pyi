# thefuzz.pyi

from typing import Any, Callable, List, Tuple, Union

# fuzz module
class fuzz:
    @staticmethod
    def ratio(s1: str, s2: str) -> int: ...
    @staticmethod
    def partial_ratio(s1: str, s2: str) -> int: ...
    @staticmethod
    def token_sort_ratio(s1: str, s2: str) -> int: ...
    @staticmethod
    def token_set_ratio(s1: str, s2: str) -> int: ...
    @staticmethod
    def WRatio(
        s1: str,
        s2: str,
        processor: Callable[[str], str] = ...,
        score_cutoff: int = ...,
    ) -> int: ...

# process module
class process:
    @staticmethod
    def extract(
        query: str,
        choices: Union[List[str], str],
        scorer: Callable[[str, str], int] = ...,
        processor: Callable[[str], str] = ...,
        limit: int = ...,
    ) -> List[Tuple[str, int]]: ...
    @staticmethod
    def extractOne(
        query: str,
        choices: Union[List[str], str],
        scorer: Callable[[str, str], int] = ...,
        processor: Callable[[str], str] = ...,
        score_cutoff: int = ...,
    ) -> Tuple[str, int]: ...
