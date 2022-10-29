import os
import pandas as pd
import torch
from src.data.sequence_dataloader import SequenceDataModule


def prepare_dummy_data(path):
    """Prepares dummy data for testing."""
    pd.DataFrame({
        "raw_sequence": ["ATCGATCGATCG", "GGTGAACGATTA", "AATCGTATCGCG", "CTTATCGATCCG"],
        "component": [1, 2, 1, 10],
    }).to_csv(path, index=False, sep="\t")

def test_invalid_data():
    # prepare invalid data
    dummy_data_path = "_tmp_seq_dataloader_data.csv"
    pd.DataFrame({
        "raw_sequence": ["ZCCCACTGACTG", "ACTGACTGACTG", "AAAACCCCTTTT", "ABCDEFGHIJKL"],
        "component": [1, 2, 1, 10],
    }).to_csv(dummy_data_path, index=False, sep="\t")

    datamodule = SequenceDataModule(
        train_path=dummy_data_path,
        val_path=dummy_data_path,
        test_path=dummy_data_path,
        sequence_length=12,
        sequence_encoding="polar",
        batch_size=2,
        num_workers=1,
    )
    # check that invalid data is detected
    try:
        datamodule.setup()
        assert False, "Invalid data should have been detected."
    except ValueError:
        pass

    # remove dummy data
    os.remove(dummy_data_path)

def test_train_val_test_data_split():
    # prepare dummy data
    dummy_train_data_path = "_tmp_seq_dataloader_train_data.csv"
    dummy_val_data_path = "_tmp_seq_dataloader_val_data.csv"
    dummy_test_data_path = "_tmp_seq_dataloader_test_data.csv"
    pd.DataFrame({
        "raw_sequence": ["AAAAAAAAAA", "AAAAAAAAAA", "AAAAAAAAAA", "AAAAAAAAAA"],
        "component": [0, 0, 0, 0],
    }).to_csv(dummy_train_data_path, index=False, sep="\t")
    pd.DataFrame({
        "raw_sequence": ["CCCCCCCCCC", "CCCCCCCCCC", "CCCCCCCCCC", "CCCCCCCCCC"],
        "component": [1, 1, 1, 1],
    }).to_csv(dummy_val_data_path, index=False, sep="\t")
    pd.DataFrame({
        "raw_sequence": ["TTTTTTTTTT", "TTTTTTTTTT", "TTTTTTTTTT", "TTTTTTTTTT"],
        "component": [2, 2, 2, 2],
    }).to_csv(dummy_test_data_path, index=False, sep="\t")

    # check loading of only a single data set
    datamodule = SequenceDataModule(
        train_path=None,
        val_path=dummy_val_data_path,
        test_path=None,
        sequence_length=10
    )
    datamodule.setup()
    assert datamodule.train_dataloader is None
    assert len(datamodule.val_data) == 4
    assert datamodule.test_dataloader is None

    # check differences between train, val, and test data
    datamodule = SequenceDataModule(
        train_path=dummy_train_data_path,
        val_path=dummy_val_data_path,
        test_path=dummy_test_data_path,
        sequence_length=10,
        sequence_encoding="polar",
        batch_size=3,
        num_workers=1,
    )
    datamodule.setup()

    assert len(datamodule.train_dataloader()) == 2
    assert len(datamodule.val_dataloader()) == 2
    assert len(datamodule.test_dataloader()) == 2
    seen_nucleotide_idxs = set()
    for dl_idx, dataloader in enumerate([datamodule.train_dataloader(), datamodule.val_dataloader(), datamodule.test_dataloader()]):
        dataloader_iter = iter(dataloader)

        # first batch
        batch = next(dataloader_iter)
        assert len(batch) == 2
        assert isinstance(batch[0], torch.Tensor)
        assert isinstance(batch[1], torch.Tensor)
        assert batch[0].shape == (3, 4, 10)
        assert batch[1].shape == (3,)
        uniq_nucleotides = batch[0].max(dim=1).indices.unique().tolist()
        seen_nucleotide_idxs.update(uniq_nucleotides)
        assert len(uniq_nucleotides) == 1
        assert (batch[1] == dl_idx).all()

        # second batch
        batch = next(dataloader_iter)
        assert len(batch) == 2
        assert isinstance(batch[0], torch.Tensor)
        assert isinstance(batch[1], torch.Tensor)
        assert batch[0].shape == (1, 4, 10)
        assert batch[1].shape == (1,)
        assert batch[0].max(dim=1).indices.unique().tolist() == uniq_nucleotides
        assert (batch[1] == dl_idx).all()

    # remove dummy data
    for path in [dummy_train_data_path, dummy_val_data_path, dummy_test_data_path]:
        os.remove(path)

def test_polar_encoding():
    # prepare dummy data
    dummy_data_path = "_tmp_seq_dataloader_data.csv"
    prepare_dummy_data(dummy_data_path)

    # prepare data module
    datamodule = SequenceDataModule(
        train_path=dummy_data_path,
        val_path=dummy_data_path,
        test_path=dummy_data_path,
        sequence_length=12,
        sequence_encoding="polar",
        batch_size=2,
        num_workers=1,
    )
    datamodule.setup()

    # data checks
    assert len(datamodule.train_data) == 4
    assert len(datamodule.val_data) == 4
    assert len(datamodule.test_data) == 4
    for dataloader in [datamodule.train_dataloader(), datamodule.val_dataloader(), datamodule.test_dataloader()]:
        for batch in dataloader:
            assert len(batch) == 2
            assert isinstance(batch[0], torch.Tensor)
            assert isinstance(batch[1], torch.Tensor)
            assert batch[0].shape == (2, 4, 12)
            assert batch[1].shape == (2,)
            assert (batch[0].max(dim=1).values == 1).all()
            assert (batch[0].min(dim=1).values == -1).all()
            assert (batch[0].prod(dim=1) == -1).all()

    # remove dummy data
    os.remove(dummy_data_path)

def test_onehot_encoding():
    # prepare dummy data
    dummy_data_path = "_tmp_seq_dataloader_data.csv"
    prepare_dummy_data(dummy_data_path)

    # prepare data module
    datamodule = SequenceDataModule(
        train_path=dummy_data_path,
        val_path=dummy_data_path,
        test_path=dummy_data_path,
        sequence_length=12,
        sequence_encoding="onehot",
        batch_size=2,
        num_workers=1,
    )
    datamodule.setup()

    # data checks
    assert len(datamodule.train_data) == 4
    assert len(datamodule.val_data) == 4
    assert len(datamodule.test_data) == 4
    for dataloader in [datamodule.train_dataloader(), datamodule.val_dataloader(), datamodule.test_dataloader()]:
        for batch in dataloader:
            assert len(batch) == 2
            assert isinstance(batch[0], torch.Tensor)
            assert isinstance(batch[1], torch.Tensor)
            assert batch[0].shape == (2, 4, 12)
            assert batch[1].shape == (2,)
            assert (batch[0].max(dim=1).values == 1).all()
            assert (batch[0].min(dim=1).values == 0).all()
            assert (batch[0].sum(dim=1) == 1).all()

    # remove dummy data
    os.remove(dummy_data_path)

def test_ordinal_encoding():
    # prepare dummy data
    dummy_data_path = "_tmp_seq_dataloader_data.csv"
    prepare_dummy_data(dummy_data_path)

    # prepare data module
    datamodule = SequenceDataModule(
        train_path=dummy_data_path,
        val_path=dummy_data_path,
        test_path=dummy_data_path,
        sequence_length=12,
        sequence_encoding="ordinal",
        batch_size=2,
        num_workers=1,
    )
    datamodule.setup()

    # data checks
    assert len(datamodule.train_data) == 4
    assert len(datamodule.val_data) == 4
    assert len(datamodule.test_data) == 4
    for dataloader in [datamodule.train_dataloader(), datamodule.val_dataloader(), datamodule.test_dataloader()]:
        for batch in dataloader:
            assert len(batch) == 2
            assert isinstance(batch[0], torch.Tensor)
            assert isinstance(batch[1], torch.Tensor)
            assert batch[0].shape == (2, 12)
            assert batch[1].shape == (2,)
            assert (batch[0].max(dim=1).values == 3).all()
            assert (batch[0].min(dim=1).values == 0).all()
            assert set(batch[0].tolist()[0]) == set([0, 1, 2, 3])

    # remove dummy data
    os.remove(dummy_data_path)

def test_polar_transforms():
    # prepare dummy data
    dummy_data_path = "_tmp_seq_dataloader_data.csv"
    prepare_dummy_data(dummy_data_path)

    # prepare data module
    datamodule = SequenceDataModule(
        train_path=dummy_data_path,
        val_path=dummy_data_path,
        test_path=dummy_data_path,
        sequence_length=12,
        sequence_encoding="polar",
        sequence_transform=lambda x: x + 1,
        cell_type_transform=lambda x: x + 20,
        batch_size=2,
        num_workers=1,
    )
    datamodule.setup()

    # data checks
    assert len(datamodule.train_data) == 4
    assert len(datamodule.val_data) == 4
    assert len(datamodule.test_data) == 4
    for dataloader in [datamodule.train_dataloader(), datamodule.val_dataloader(), datamodule.test_dataloader()]:
        seen_cell_type_ids = set()
        for batch in dataloader:
            assert len(batch) == 2
            assert isinstance(batch[0], torch.Tensor)
            assert isinstance(batch[1], torch.Tensor)
            assert batch[0].shape == (2, 4, 12)
            assert batch[1].shape == (2,)
            assert (batch[0].max(dim=1).values == 2).all()
            assert (batch[0].min(dim=1).values == 0).all()
            assert (batch[0].sum(dim=1) == 2).all()
            cell_type_ids = set(batch[1].tolist())
            assert cell_type_ids.difference([21, 22, 30]) == set()
            seen_cell_type_ids.update(cell_type_ids)
        assert seen_cell_type_ids == set([21, 22, 30])

    # remove dummy data
    os.remove(dummy_data_path)

def test_onehot_transforms():
    # prepare dummy data
    dummy_data_path = "_tmp_seq_dataloader_data.csv"
    prepare_dummy_data(dummy_data_path)

    # prepare data module
    datamodule = SequenceDataModule(
        train_path=dummy_data_path,
        val_path=dummy_data_path,
        test_path=dummy_data_path,
        sequence_length=12,
        sequence_encoding="onehot",
        sequence_transform=lambda x: x + 1,
        cell_type_transform=lambda x: x + 20,
        batch_size=2,
        num_workers=1,
    )
    datamodule.setup()

    # data checks
    assert len(datamodule.train_data) == 4
    assert len(datamodule.val_data) == 4
    assert len(datamodule.test_data) == 4
    for dataloader in [datamodule.train_dataloader(), datamodule.val_dataloader(), datamodule.test_dataloader()]:
        seen_cell_type_ids = set()
        for batch in dataloader:
            assert len(batch) == 2
            assert isinstance(batch[0], torch.Tensor)
            assert isinstance(batch[1], torch.Tensor)
            assert batch[0].shape == (2, 4, 12)
            assert batch[1].shape == (2,)
            assert (batch[0].max(dim=1).values == 2).all()
            assert (batch[0].min(dim=1).values == 1).all()
            assert (batch[0].sum(dim=1) == 5).all()
            cell_type_ids = set(batch[1].tolist())
            assert cell_type_ids.difference([21, 22, 30]) == set()
            seen_cell_type_ids.update(cell_type_ids)
        assert seen_cell_type_ids == set([21, 22, 30])

    # remove dummy data
    os.remove(dummy_data_path)

def test_ordinal_transforms():
    # prepare dummy data
    dummy_data_path = "_tmp_seq_dataloader_data.csv"
    prepare_dummy_data(dummy_data_path)

    # prepare data module
    datamodule = SequenceDataModule(
        train_path=dummy_data_path,
        val_path=dummy_data_path,
        test_path=dummy_data_path,
        sequence_length=12,
        sequence_encoding="ordinal",
        sequence_transform=lambda x: x + 1,
        cell_type_transform=lambda x: x + 20,
        batch_size=2,
        num_workers=1,
    )
    datamodule.setup()

    # data checks
    assert len(datamodule.train_data) == 4
    assert len(datamodule.val_data) == 4
    assert len(datamodule.test_data) == 4
    for dataloader in [datamodule.train_dataloader(), datamodule.val_dataloader(), datamodule.test_dataloader()]:
        seen_cell_type_ids = set()
        for batch in dataloader:
            assert len(batch) == 2
            assert isinstance(batch[0], torch.Tensor)
            assert isinstance(batch[1], torch.Tensor)
            assert batch[0].shape == (2, 12)
            assert batch[1].shape == (2,)
            assert (batch[0].max(dim=1).values == 4).all()
            assert (batch[0].min(dim=1).values == 1).all()
            assert set(batch[0].tolist()[0]) == set([1, 2, 3, 4])
            cell_type_ids = set(batch[1].tolist())
            assert cell_type_ids.difference([21, 22, 30]) == set()
            seen_cell_type_ids.update(cell_type_ids)
        assert seen_cell_type_ids == set([21, 22, 30])

    # remove dummy data
    os.remove(dummy_data_path)
