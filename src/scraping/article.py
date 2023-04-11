from dataclasses import dataclass, field, fields
from datetime import datetime
from textwrap import TextWrapper, dedent
from typing import Any, Dict, List, Optional, Set, Iterator, Tuple

import more_itertools
from colorama import Fore, Style

from src.parser.html_parser import ArticleBody
from src.scraping.source import ArticleSource


@dataclass(frozen=True)
class Article:
    source: ArticleSource
    exception: Optional[Exception] = None

    # supported attributes as defined in the guidelines
    title: Optional[str] = None
    author: List[str] = field(default_factory=list)
    body: Optional[ArticleBody] = None
    publishing_date: Optional[datetime] = None
    topics: List[str] = field(default_factory=list)

    @classmethod
    def from_extracted(
            cls, source: ArticleSource, extracted: Dict[str, Any], exception: Optional[Exception] = None
    ) -> 'Article':
        supported_attributes: Set[str] = {article_field.name for article_field in fields(cls)}

        extracted_unsupported: Iterator[Tuple[str, Any]]
        extracted_supported: Iterator[Tuple[str, Any]]
        extracted_unsupported, extracted_supported = more_itertools.partition(
            lambda attribute_and_value: attribute_and_value[0] in supported_attributes, extracted.items()
        )

        article: Article = cls(source, exception, **dict(extracted_supported))
        for attribute, value in extracted_unsupported:
            object.__setattr__(article, attribute, value)  # Sets attributes on a frozen dataclass

        return article

    @property
    def plaintext(self) -> Optional[str]:
        body = self.body
        return str(body) if body else None

    def __getattr__(self, item):
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{item}'")

    def __str__(self):
        # the subsequent indent here is a bit wacky, but textwrapper.dedent won't work with tabs, so we have to use
        # whitespaces instead.
        title_wrapper = TextWrapper(width=80, max_lines=1, initial_indent="")
        text_wrapper = TextWrapper(width=80, max_lines=2, initial_indent="", subsequent_indent="          ")
        wrapped_title = title_wrapper.fill(
            f"{Fore.RED}--missing title--{Style.RESET_ALL}" if self.title is None else self.title.strip()
        )
        wrapped_plaintext = text_wrapper.fill(
            f"{Fore.RED}--missing plaintext--{Style.RESET_ALL}" if self.plaintext is None else self.plaintext.strip()
        )

        text = (
            f"Fundus-Article:"
            f'\n- Title: "{wrapped_title}"'
            f'\n- Text:  "{wrapped_plaintext}"'
            f"\n- URL:    {self.source.url}"
            f'\n- From:   {self.source.publisher} ({self.publishing_date.strftime("%Y-%m-%d %H:%M") if self.publishing_date else ""})'
        )

        return dedent(text)
