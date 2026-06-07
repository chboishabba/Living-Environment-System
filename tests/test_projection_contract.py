import pytest

from les.contracts_projection import (
    ProjectionContract,
    ProjectionSummaryStatistic,
)
from les.projection import project_state, summarize_projection


def test_projection_contract_projects_and_summarizes() -> None:
    contract = ProjectionContract(
        name="soil.bucket.reduction",
        projection=lambda state: {
            "n": float(state["n"]),
            "c": float(state["c"]),
            "s": float(state["s"]),
        },
        retained_variables=("n", "c", "s"),
        discarded_variables=("temperature", "ph"),
        summary_statistics=(
            ProjectionSummaryStatistic(
                name="total_buckets",
                compute=lambda reduced: sum(reduced.values()),
            ),
            ProjectionSummaryStatistic(
                name="source_n",
                source="full_state",
                compute=lambda full: full["n"],
            ),
        ),
    )

    full_state = {"n": 2, "c": 3, "s": 4, "temperature": 27.5, "ph": 6.8}

    reduced = project_state(contract, full_state)
    summary = summarize_projection(contract, full_state)

    assert reduced == {"n": 2.0, "c": 3.0, "s": 4.0}
    assert summary == {"total_buckets": 9.0, "source_n": 2}
    assert contract.retained_variables == ("n", "c", "s")
    assert contract.discarded_variables == ("temperature", "ph")


def test_projection_contract_rejects_overlapping_retained_and_discarded_variables() -> None:
    with pytest.raises(ValueError, match="overlap"):
        ProjectionContract(
            name="invalid",
            projection=lambda state: state,
            retained_variables=("n", "c"),
            discarded_variables=("c", "s"),
        )


def test_projection_contract_rejects_duplicate_summary_names() -> None:
    with pytest.raises(ValueError, match="unique names"):
        ProjectionContract(
            name="invalid",
            projection=lambda state: state,
            summary_statistics=(
                ProjectionSummaryStatistic(name="density", compute=lambda state: 1),
                ProjectionSummaryStatistic(name="density", compute=lambda state: 2),
            ),
        )
