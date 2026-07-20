"""Tower of Eternity — content-aware cutout node.

Wraps rembg (isnet-anime) so a generated portrait comes out of the workflow
already background-removed. Content-aware segmentation keeps dark clothing and
hair that color/connectivity cutouts (void-mask, border-flood) shred on the
black-void backgrounds this pipeline produces. Output is an RGBA IMAGE that
SaveImage writes as a transparent PNG — the game backend then skips its own
cutout (portrait_cache._has_real_alpha).
"""
import numpy as np
import torch

_SESSION = None


def _session():
    global _SESSION
    if _SESSION is None:
        from rembg import new_session
        _SESSION = new_session("isnet-anime")
    return _SESSION


class ToE_RembgCutout:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"images": ("IMAGE",)},
                "optional": {"post_process": ("BOOLEAN", {"default": True})}}

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("images",)
    FUNCTION = "cut"
    CATEGORY = "ToE"

    def cut(self, images, post_process=True):
        from rembg import remove
        from PIL import Image
        out = []
        for img in images:                                   # (H,W,3) float 0-1
            arr = (img.cpu().numpy() * 255.0).clip(0, 255).astype(np.uint8)
            pil = Image.fromarray(arr, "RGB")
            cut = remove(pil, session=_session(),
                         post_process_mask=post_process).convert("RGBA")
            rgba = np.asarray(cut).astype(np.float32) / 255.0
            out.append(torch.from_numpy(rgba))
        return (torch.stack(out, dim=0),)                    # (B,H,W,4)


NODE_CLASS_MAPPINGS = {"ToE_RembgCutout": ToE_RembgCutout}
NODE_DISPLAY_NAME_MAPPINGS = {"ToE_RembgCutout": "ToE Rembg Cutout"}
__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
