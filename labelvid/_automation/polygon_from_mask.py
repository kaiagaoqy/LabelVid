"""Compute polygon from mask for AI annotation."""

from __future__ import annotations

import numpy as np
import skimage
from loguru import logger
from numpy.typing import NDArray


def _get_contour_length(contour: NDArray[np.float32]) -> float:
    contour_start: NDArray[np.float32] = contour
    contour_end: NDArray[np.float32] = np.r_[contour[1:], contour[0:1]]
    return np.linalg.norm(contour_end - contour_start, axis=1).sum()


def compute_polygon_from_mask(mask: NDArray[np.bool_]) -> NDArray[np.float32]:
    """Compute polygon from binary mask.

    Args:
        mask: Binary mask of shape (H, W).

    Returns:
        Polygon points of shape (N, 2) in (x, y) format.
    """
    contours: NDArray[np.float32] = skimage.measure.find_contours(
        np.pad(mask, pad_width=1)
    )
    if len(contours) == 0:
        logger.warning("No contour found, so returning empty polygon.")
        return np.empty((0, 2), dtype=np.float32)

    contour: NDArray[np.float32] = max(contours, key=_get_contour_length)
    POLYGON_APPROX_TOLERANCE: float = 0.004
    polygon: NDArray[np.float32] = skimage.measure.approximate_polygon(
        coords=contour,
        tolerance=np.ptp(contour, axis=0).max() * POLYGON_APPROX_TOLERANCE,
    )
    polygon = np.clip(polygon, (0, 0), (mask.shape[0] - 1, mask.shape[1] - 1))
    polygon = polygon[:-1]  # drop last point that is duplicate of first point

    return polygon[:, ::-1]  # yx -> xy
