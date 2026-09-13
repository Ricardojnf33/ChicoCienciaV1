from dataclasses import dataclass
from enum import Enum


class ExperimentVariant(str, Enum):
    B1 = "B1"
    A = "A"
    A0 = "A0"


@dataclass(frozen=True)
class VariantPolicy:
    variant: ExperimentVariant
    uses_tree_search: bool
    automatic_correction: bool

    def effective_branching(self, requested: int) -> int:
        if requested < 1:
            raise ValueError("branching deve ser pelo menos 1")
        return requested if self.uses_tree_search else 1

    @property
    def max_attempts_per_node(self) -> int:
        return 3 if self.automatic_correction else 1


POLICIES = {
    ExperimentVariant.B1: VariantPolicy(
        variant=ExperimentVariant.B1,
        uses_tree_search=False,
        automatic_correction=True,
    ),
    ExperimentVariant.A: VariantPolicy(
        variant=ExperimentVariant.A,
        uses_tree_search=True,
        automatic_correction=True,
    ),
    ExperimentVariant.A0: VariantPolicy(
        variant=ExperimentVariant.A0,
        uses_tree_search=True,
        automatic_correction=False,
    ),
}


def policy_for(variant: ExperimentVariant | str) -> VariantPolicy:
    return POLICIES[ExperimentVariant(variant)]
