from typing import Callable, NewType, Tuple

Schema = NewType("Schema", dict)
Plugin = Callable[[], Tuple[str, Schema]]
