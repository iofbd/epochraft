from typing import Optional

import pytest

from epochraft import CheckpointableDataset, ParallelExecutorType, Sample, testing


parameterize_parallel_config = pytest.mark.parametrize(
    "max_workers, prefetch_factor, executor_type",
    [
        (None, 2, "process"),
        (2, 1, "process"),
        (4, 10, "process"),
        (None, 2, "thread"),
        (2, 1, "thread"),
        (4, 10, "thread"),
    ],
)


@parameterize_parallel_config
def test_parallel_map(
    max_workers: int, prefetch_factor: int, executor_type: ParallelExecutorType
) -> None:
    def fn(sample: Sample) -> Sample:
        return {"id": sample["id"] * 2}

    samples = testing.generate_example_sequence()
    dataset = CheckpointableDataset.from_sequence(samples).parallel_map(
        fn, max_workers=max_workers, prefetch_factor=prefetch_factor, executor_type=executor_type
    )
    samples_generated = list(dataset)

    # Should generate the same samples
    assert samples_generated == list(map(fn, samples))


@parameterize_parallel_config
def test_parallel_filter(
    max_workers: int, prefetch_factor: int, executor_type: ParallelExecutorType
) -> None:
    def fn(sample: Sample) -> bool:
        return sample["id"] % 2 == 0  # type: ignore

    samples = testing.generate_example_sequence()
    dataset = CheckpointableDataset.from_sequence(samples).parallel_filter(
        fn, max_workers=max_workers, prefetch_factor=prefetch_factor, executor_type=executor_type
    )
    samples_generated = list(dataset)

    # Should generate the same samples
    assert samples_generated == list(filter(fn, samples))


@parameterize_parallel_config
def test_parallel_filter_map(
    max_workers: int, prefetch_factor: int, executor_type: ParallelExecutorType
) -> None:
    def fn(sample: Sample) -> Optional[Sample]:
        if sample["id"] % 2 == 0:
            return {"id": sample["id"] * 3}
        else:
            return None

    samples = testing.generate_example_sequence()
    dataset = CheckpointableDataset.from_sequence(samples).parallel_filter_map(
        fn, max_workers=max_workers, prefetch_factor=prefetch_factor, executor_type=executor_type
    )
    samples_generated = list(dataset)

    # Should generate the same samples
    samples_expected = list(filter(None, map(fn, samples)))
    assert samples_generated == samples_expected


@parameterize_parallel_config
def test_unorderd_parallel_filter_map(
    max_workers: int, prefetch_factor: int, executor_type: ParallelExecutorType
) -> None:
    def fn(sample: Sample) -> Optional[Sample]:
        if sample["id"] % 2 == 0:
            return {"id": sample["id"] * 3}
        else:
            return None

    samples = testing.generate_example_sequence()
    dataset = CheckpointableDataset.from_sequence(samples).parallel_filter_map(
        fn,
        max_workers=max_workers,
        prefetch_factor=prefetch_factor,
        executor_type=executor_type,
        ordered=False,
    )

    # Sorting is the necessary because the order of the samples is not guaranteed
    samples_generated = sorted(dataset, key=lambda x: x["id"])

    # Should generate the same samples
    samples_expected = list(filter(None, map(fn, samples)))
    assert samples_generated == samples_expected


@parameterize_parallel_config
def test_parallel_filter_map_checkpointing(
    max_workers: int, prefetch_factor: int, executor_type: ParallelExecutorType
) -> None:
    def fn(sample: Sample) -> Optional[Sample]:
        if sample["id"] % 2 == 0:
            return {"id": sample["id"] * 3}
        else:
            return None

    samples = testing.generate_example_sequence()
    dataset = CheckpointableDataset.from_sequence(
        samples, repeat=True, shuffle=True
    ).parallel_filter_map(
        fn, max_workers=max_workers, prefetch_factor=prefetch_factor, executor_type=executor_type
    )

    testing.check_resumption(dataset, dataset, 0)
    testing.check_resumption(dataset, dataset, 1)
    testing.check_resumption(dataset, dataset, 123)