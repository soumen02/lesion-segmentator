from monai.transforms import MapTransform, Resize, Orientation
from monai.utils import ensure_tuple_rep
from monai.data import MetaTensor
from monai.transforms.utils import InterpolateMode
import nibabel as nib
import logging
import numpy as np

class Restored(MapTransform):
    def __init__(
        self,
        keys,
        ref_image,
        has_channel=True,
        invert_orient=False,
        mode=InterpolateMode.NEAREST,
        config_labels=None,
        align_corners=None,
        meta_key_postfix="meta_dict",
    ):
        super().__init__(keys)
        self.ref_image = ref_image
        self.has_channel = has_channel
        self.invert_orient = invert_orient
        self.config_labels = config_labels
        self.mode = ensure_tuple_rep(mode, len(self.keys))
        self.align_corners = ensure_tuple_rep(align_corners, len(self.keys))
        self.meta_key_postfix = meta_key_postfix

    def __call__(self, data):
        d = dict(data)
        meta_dict = (
            d[self.ref_image].meta
            if d.get(self.ref_image) is not None and isinstance(d[self.ref_image], MetaTensor)
            else d.get(f"{self.ref_image}_{self.meta_key_postfix}", {})
        )

        for idx, key in enumerate(self.keys):
            result = d[key]
            current_size = result.shape[1:] if self.has_channel else result.shape
            spatial_shape = meta_dict.get("spatial_shape", current_size)
            spatial_size = spatial_shape[-len(current_size):]

            # Resize if needed
            if not np.array_equal(current_size, spatial_size):
                resizer = Resize(spatial_size=spatial_size, mode=self.mode[idx])
                result = resizer(result, mode=self.mode[idx], align_corners=self.align_corners[idx])

            # We skip orientation inversion since we want to keep RAS orientation
            if self.invert_orient:
                orig_affine = meta_dict.get("original_affine", None)
                if orig_affine is not None:
                    orig_axcodes = nib.orientations.aff2axcodes(orig_affine)
                    inverse_transform = Orientation(axcodes=orig_axcodes)
                    with inverse_transform.trace_transform(False):
                        result = inverse_transform(result)
                else:
                    logging.info("Failed invert orientation - original_affine is not on the image header")

            # Handle label indices if needed
            if self.config_labels is not None:
                new_pred = result * 0.0
                for j, (label_name, idx) in enumerate(self.config_labels.items(), 1):
                    if label_name != "background":
                        new_pred[result == j] = idx
                result = new_pred

            # Remove batch dimension if present
            d[key] = result if len(result.shape) <= 3 else result[0] if result.shape[0] == 1 else result

            # Keep the RAS affine
            meta = d.get(f"{key}_{self.meta_key_postfix}")
            if meta is None:
                meta = dict()
                d[f"{key}_{self.meta_key_postfix}"] = meta
            meta["affine"] = meta_dict.get("affine")  # Use the current affine, not the original

        return d