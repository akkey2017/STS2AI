from __future__ import annotations


def action_mask(legal_indices: list[int], action_space_size: int) -> list[int]:
    mask = [0] * action_space_size
    for index in legal_indices:
        if index < 0 or index >= action_space_size:
            raise ValueError(f"legal action index out of range: {index}")
        mask[index] = 1
    return mask

