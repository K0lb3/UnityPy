from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Generator, Iterator, List, Tuple, Union

from attrs import define

if TYPE_CHECKING:
    from ..classes import AssetBundle, AssetInfo, Object, PPtr


@define(slots=True)
class ContainerHelper:
    """Helper class to allow multidict containers
    without breaking compatibility with old versions"""

    container: List[Tuple[str, AssetInfo]]
    container_dict: Dict[str, PPtr[Object]]
    path_dict: Dict[int, str]

    def __init__(self, container: Union[List[Tuple[str, AssetInfo]], AssetBundle]) -> None:
        if not isinstance(container, (list)):
            container = container.m_Container
        self.container = container
        self.container_dict = {key: value.asset for key, value in container}
        self.path_dict = {value.asset.path_id: key for key, value in container}

    def items(self) -> Generator[Tuple[str, PPtr[Object]], None, None]:
        return ((key, value.asset) for key, value in self.container)

    def keys(self) -> list[str]:
        return list({key for key, value in self.container})

    def values(self) -> list[PPtr[Object]]:
        return list({value.asset for key, value in self.container})

    def __getitem__(self, key) -> PPtr[Object]:
        return self.container_dict[key]

    def __setitem__(self, key, value) -> None:
        raise NotImplementedError("Assigning to container is not allowed!")

    def __delitem__(self, key) -> None:
        raise NotImplementedError("Deleting from the container is not allowed!")

    def __iter__(self) -> Iterator[str]:
        return iter(self.keys())

    def __len__(self) -> int:
        return len(self.container)

    def __getattr__(self, name: str) -> PPtr[Object]:
        return self.container_dict[name]

    def __str__(self) -> str:
        return f"{{{', '.join(f'{key}: {value}' for key, value in self.items())}}}"

    def __dict__(self) -> Dict[str, PPtr[Object]]:
        return self.container_dict

    def __contains__(self, key: str) -> bool:
        return key in self.container_dict
