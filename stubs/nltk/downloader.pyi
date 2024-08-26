"""Typing for nltk.download"""

from typing import Optional

def download(
    resource_name: str,
    download_dir: str = ...,
    quiet: bool = ...,
    raise_on_error: bool = ...,
) -> None: ...
