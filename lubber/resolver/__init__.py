import semver

from pathlib import Path
from rich import print

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


def _resolve(full_name: str, version_range: str, resolved: dict[str, Dependency]):
    name_splits = full_name.split(":", 2)
    name: str = name_splits[-1]
    set_resolver: str = None if len(name_splits) < 2 else name_splits[0] 

    version_range = version_range.replace("^", ">=")
    dependency: Dependency = resolved.get(name, default=None)

    was_resolved: bool = dependency is not None

    if was_resolved:
        if set_resolver != dependency.provided_by:
            raise Exception(f"Dependency {name} from {dependency.provided_by} is not compatible with {name} from {set_resolver}.")

        resolved_versions = dependency.versions.copy()
        for version in resolved_versions:
            if not version.match(version_range):
                dependency.versions.remove(version)
            
        dependency.version_ranges.append(version_range)

    if not was_resolved:
        for id in resolvers:
            resolver = resolvers[id]
            dependency = resolver.resolve(name, version_range)
            if dependency is not None:
                dependency.provided_by = id
                break

    if len(dependency.versions) == 0:
        raise Exception(
            f"Dependency '{name}' of '{dependency_stack[-1]}' was found, but no version matched {version_range}." if not was_resolved else
            f"Dependency '{name} ({version_range})' of '{dependency_stack[-1]}' is not compatible with '{name} ({dependency.version_ranges[-2]})'."
        )
    if dependency is None:
        raise Exception(
            f"Dependency '{name}' of '{dependency_stack[-1]}' couldn't be found."
        )
    
    dependency.needed_by.append(dependency_stack[-1])

    if len(dependency.relies_on) > 0:
        dependency_stack.append(dependency.name)
        for dependency2 in dependency.relies_on:
            if dependency2.name in dependency_stack:
                raise Exception(f"Cyclic dependency! ({*dependency_stack})")
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
