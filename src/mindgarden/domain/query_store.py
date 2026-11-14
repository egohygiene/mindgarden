"""The optional query-store port consumes authorized projections, not source roots."""

from typing import Callable, Protocol


class QueryStore(Protocol):
    """Version 1: rebuildable lexical/typed view; never a policy authority.

    Callers enforce live session/revision/output limits before and after every
    operation. Implementations declare unsupported encryption/vector/evolution
    behavior explicitly. Physical locations belong only to adapter instances.
    """

    @staticmethod
    def capabilities() -> dict: ...

    def inventory(self) -> dict | None: ...

    def reset(
        self, expected_before: str, *, check_live: Callable[[], None]
    ) -> dict: ...

    def plan(self, index: dict, scope_sha256: str) -> dict: ...
    def build(
        self,
        index: dict,
        scope_sha256: str,
        reviewed_digest: str,
        *,
        check_live: Callable[[], None],
    ) -> dict: ...
    def load(self, expected_index: dict, scope_sha256: str) -> dict: ...
    def refresh_plan(self, index: dict, scope_sha256: str) -> dict: ...
    def refresh(
        self,
        index: dict,
        scope_sha256: str,
        reviewed_digest: str,
        *,
        check_live: Callable[[], None],
    ) -> dict: ...
    def migration_plan(
        self, source: "QueryStore", index: dict, scope_sha256: str
    ) -> dict: ...
    def migrate(
        self,
        source: "QueryStore",
        index: dict,
        scope_sha256: str,
        reviewed_digest: str,
        *,
        check_live: Callable[[], None],
    ) -> dict: ...
    def search(
        self, expected_index: dict, scope_sha256: str, query: str
    ) -> list[dict]: ...
    def traverse(
        self,
        expected_index: dict,
        scope_sha256: str,
        start: str,
        depth: int,
        limit: int,
    ) -> dict: ...
    def backlinks(
        self, expected_index: dict, scope_sha256: str, target: str
    ) -> list[dict]: ...
    def backup(self, expected_index: dict, scope_sha256: str) -> dict: ...
