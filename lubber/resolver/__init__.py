from pathlib import Path

from lubber.models.project import DependencyList
from lubber.resolver.coop import CoopResolver
from lubber.resolver.types import Dependency, Resolver

resolvers: dict[str, Resolver] = {"coop": CoopResolver()}

dependency_stack: list[str] = []


def resolve(root: str, dependencies: DependencyList) -> dict[str, Dependency]:
    dependency_stack.append(root)
    resolved: dict[str, Dependency] = {}
    for name in dependencies:
        version_range = dependencies[name]
        _resolve(name, version_range, resolved)
    return resolved


def _resolve(name: str, version_range: str, resolved: dict[str, Dependency]):
    version_range = version_range.replace("^", ">=")
    dependency: Dependency = None
    for id in resolvers:
        resolver = resolvers[id]
        dependency = resolver.resolve(name, version_range)
        if dependency is not None:
            dependency.provided_by = id
            break
    if len(dependency.versions) == 0:
        raise Exception(
            f"Dependency '{name}' ({version_range}) of 'f{dependency_stack[-1]}' was resolved, but has no suitable version."
        )
    if dependency is None:
        raise Exception(
            f"Dependency '{name}' ({version_range}) of 'f{dependency_stack[-1]}' couldn't be resolved."
        )
    if len(dependency.relies_on) > 0:
        dependency_stack.append(dependency.name)
        for dependency2 in dependency.relies_on:
            _resolve(dependency2.name, dependency2.version_range, resolved)
        dependency_stack.pop()
    resolved[name] = dependency


def install(dependency: Dependency, to: Path) -> bool:
    resolver = resolvers[dependency.provided_by]
    if resolver is None:
        raise Exception("Invalid resolver during install.")
    if not to.is_dir():
        to.mkdir(parents=True, exist_ok=False)
    if not resolver.install(dependency, to):
        raise Exception(
            f"Error while installing {dependency.name}@{str(dependency.versions[0])}."
        )
