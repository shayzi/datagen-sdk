from typing import List, Tuple, Any
import sys

if sys.version_info < (3, 10):
    from importlib_metadata import entry_points, EntryPoint  # type: ignore
else:
    from importlib.metadata import entry_points, EntryPoint  # type: ignore

from dependency_injector import providers


NOT_BASE_CLASS_PLUGIN = "<NOT_BASE_CLASS_PLUGIN>"


class PluginsFactory(providers.Provider):

    __slots__ = ("_factory", "_base_class")

    def __init__(self, base_class, *args, **kwargs):
        self._base_class = base_class
        self._factory = providers.Factory(self._get_provided_type(), *args, **kwargs)
        super().__init__()

    def _get_provided_type(self) -> type:
        plugins_classes = self._collect_plugins_classes()
        return self._create_type(plugins_classes) if len(plugins_classes) > 0 else self._base_class

    def _collect_plugins_classes(self) -> Tuple[type]:
        plugins_classes = []
        for group_name, entrypoints in entry_points().items():
            if self._is_base_class_plugins_group(group_name):
                plugins_classes.extend(self._load_plugins(plugins_entrypoints=entrypoints))
        return tuple(plugins_classes)

    def _is_base_class_plugins_group(self, plugins_group_name: str) -> bool:
        return self._base_class.PLUGINS_GROUP_NAME.startswith(plugins_group_name)

    def _load_plugins(self, plugins_entrypoints: List[EntryPoint]) -> List[type]:
        plugin_classes = []
        for entrypoint in plugins_entrypoints:
            plugin = entrypoint.load()
            if self._is_base_class_plugin(plugin):
                plugin_classes.append(plugin)
        return plugin_classes

    def _create_type(self, plugins: Tuple[type]) -> type:
        name, dict_ = self._base_class.__name__, {"PLUGINS_GROUP_NAME": self._base_class.PLUGINS_GROUP_NAME}
        if self._base_class_specified_in(plugins):
            return type(name, plugins, dict_)
        else:
            # In case all dev extend some parent of the base class but not the base class itself,
            # The base class must be provided explicitly.
            return type(name, (self._base_class, *plugins), dict_)

    def _base_class_specified_in(self, plugins: Tuple[type]) -> bool:
        return any(issubclass(p, self._base_class) for p in plugins)

    def __deepcopy__(self, memo):
        copied = memo.get(id(self))
        if copied is not None:
            return copied

        copied = self.__class__(
            self._factory.provides,
            *providers.deepcopy(self._factory.args, memo),
            **providers.deepcopy(self._factory.kwargs, memo),
        )
        self._copy_overridings(copied, memo)

        return copied

    @property
    def related(self):
        """Return related providers generator."""
        yield from [self._factory]
        yield from super().related

    def _provide(self, args, kwargs):
        return self._factory(*args, **kwargs)

    def _is_base_class_plugin(self, plugin: Any) -> bool:
        plugin_group_name = getattr(plugin, "PLUGINS_GROUP_NAME", NOT_BASE_CLASS_PLUGIN)
        return self._base_class.PLUGINS_GROUP_NAME.startswith(plugin_group_name)
