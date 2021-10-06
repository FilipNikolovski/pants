# Copyright 2021 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

import os
from dataclasses import dataclass

from pants.backend.go.target_types import GoModTarget
from pants.core.goals.tailor import (
    AllOwnedSources,
    PutativeTarget,
    PutativeTargets,
    PutativeTargetsRequest,
    group_by_dir,
)
from pants.engine.fs import PathGlobs, Paths
from pants.engine.internals.selectors import Get
from pants.engine.rules import collect_rules, rule
from pants.engine.unions import UnionRule
from pants.util.logging import LogLevel


@dataclass(frozen=True)
class PutativeGoModuleTargetsRequest(PutativeTargetsRequest):
    pass


@rule(level=LogLevel.DEBUG, desc="Determine candidate `go_mod` targets to create")
async def find_putative_go_mod_targets(
    request: PutativeGoModuleTargetsRequest, all_owned_sources: AllOwnedSources
) -> PutativeTargets:
    all_go_mod_files = await Get(Paths, PathGlobs, request.search_paths.path_globs("go.mod"))
    unowned_go_mod_files = set(all_go_mod_files.files) - set(all_owned_sources)

    putative_targets = []
    for dirname, filenames in group_by_dir(unowned_go_mod_files).items():
        putative_targets.append(
            PutativeTarget.for_target_type(
                GoModTarget,
                path=dirname,
                name=os.path.basename(dirname),
                triggering_sources=sorted(filenames),
            )
        )

    return PutativeTargets(putative_targets)


def rules():
    return [*collect_rules(), UnionRule(PutativeTargetsRequest, PutativeGoModuleTargetsRequest)]
