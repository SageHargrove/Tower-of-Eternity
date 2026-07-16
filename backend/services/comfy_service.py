import json
import time
import random
import requests
import os

COMFY_URL = "http://127.0.0.1:8188"
CHECKPOINT = os.getenv("COMFY_CHECKPOINT", "noobaiXLNAIXL_vPred10Version.safetensors")
LORA_NAME = os.getenv("COMFY_LORA", None)
LORA_STRENGTH = float(os.getenv("COMFY_LORA_STRENGTH", "0.8"))

# v-prediction checkpoints (NoobAI vPred etc.) sampled like a normal eps
# model produce exactly the artifacts we saw in portraits/cached: some
# outputs fried (crushed blacks, neon saturation), others collapsed to
# near-grayscale. The documented fix is a RescaleCFG pass and a lower CFG.
# Auto-detected from the checkpoint filename; override with COMFY_VPRED=0/1.
_vpred_env = os.getenv("COMFY_VPRED")
IS_VPRED = (_vpred_env == "1") if _vpred_env in ("0", "1") else ("vpred" in CHECKPOINT.lower().replace("_", "").replace("-", ""))
CFG = float(os.getenv("COMFY_CFG", "5.0" if IS_VPRED else "7.0"))
RESCALE_MULT = float(os.getenv("COMFY_RESCALE_CFG", "0.7"))
# Impact Pack FaceDetailer pass (installed 2026-07). COMFY_FACE_DETAILER=0
# disables; if the packs are missing, generation retries without it anyway.
FACE_DETAIL = os.getenv("COMFY_FACE_DETAILER", "1") == "1"
# xinsir union ControlNet (installed in ComfyUI/models/controlnet) — used to
# lock the body plan of non-humanoid monsters against the human-trained
# checkpoint's tendency to humanise them. See _build_workflow's control path.
CONTROLNET_MODEL = os.getenv("COMFY_CONTROLNET", "xinsir-union-promax.safetensors")


def _build_workflow(prompt: str, negative: str = "", seed: int = None, init_image_name: str = None, denoise: float = 0.45, width: int = 832, height: int = 1216, hires: bool = False, hires_denoise: float = 0.62, lora_override: str = None, lora_strength_override: float = None, face_detail: bool = None, control_image_name: str = None, control_strength: float = 0.55, control_end: float = 0.5, control_mode: str = 'canny') -> dict:
    if face_detail is None:
        face_detail = FACE_DETAIL
    if seed is None:
        seed = random.randint(0, 2**32 - 1)

    full_prompt = prompt

    neg = negative or (
        "blurry, low quality, watermark, text, signature, bad anatomy, "
        "deformed, ugly, disfigured, worst quality, jpeg artifacts"
    )

    # model source: checkpoint by default, lora loader if lora configured
    model_source = ["4", 0]
    clip_source = ["4", 1]

    # hires=True runs a second, lower-denoise KSampler pass over a latent
    # upscale of the first pass's output — single-pass generation at a
    # busy, multi-subject composition (vs. a tight single-character
    # portrait) tends to come out simpler/blurrier than this game's other
    # scene-style art, since the base checkpoint resolution is fighting the
    # composition's complexity. The upscale-and-refine pass gives the model
    # a second look at the full composition instead of trying to render all
    # that detail in one pass.
    final_samples_source = ["3", 0]
    if hires and not init_image_name:
        final_samples_source = ["14", 0]

    workflow = {
        "4": {
            "inputs": {"ckpt_name": CHECKPOINT},
            "class_type": "CheckpointLoaderSimple"
        },
        "8": {
            "inputs": {"samples": final_samples_source, "vae": ["4", 2]},
            "class_type": "VAEDecode"
        },
        "9": {
            "inputs": {"filename_prefix": "infinite_gacha", "images": ["8", 0]},
            "class_type": "SaveImage"
        }
    }

    # LoRA stack. COMFY_LORA accepts a comma-separated list, each entry
    # optionally carrying its own strength after a colon:
    #   COMFY_LORA="darkFantasy_illustrious.safetensors:0.55,addMicroDetails_illu.safetensors:0.3"
    # Entries without a strength use COMFY_LORA_STRENGTH. A per-call
    # override (lora_override, same syntax) takes precedence, so a caller
    # (e.g. the equipment icon script) can use a different stack without
    # touching the global setting. Loaders chain 10, 21, 22, ...
    lora_spec = lora_override if lora_override is not None else LORA_NAME
    default_strength = lora_strength_override if lora_strength_override is not None else LORA_STRENGTH
    if lora_spec:
        entries = []
        for part in str(lora_spec).split(","):
            part = part.strip()
            if not part:
                continue
            if ":" in part:
                name, _, s = part.rpartition(":")
                try:
                    entries.append((name.strip(), float(s)))
                except ValueError:
                    entries.append((part, default_strength))
            else:
                entries.append((part, default_strength))
        for i, (name, strength) in enumerate(entries):
            node_id = "10" if i == 0 else str(20 + i)  # 10, 21, 22, ...
            workflow[node_id] = {
                "inputs": {
                    "lora_name": name,
                    "strength_model": strength,
                    "strength_clip": strength,
                    "model": model_source,
                    "clip": clip_source
                },
                "class_type": "LoraLoader"
            }
            model_source = [node_id, 0]
            clip_source = [node_id, 1]

    # v-pred sampling correction — core ComfyUI node, sits after the
    # checkpoint/LoRA and feeds every KSampler below.
    if IS_VPRED:
        workflow["20"] = {
            "inputs": {"multiplier": RESCALE_MULT, "model": model_source},
            "class_type": "RescaleCFG"
        }
        model_source = ["20", 0]

    workflow["6"] = {
        "inputs": {"text": full_prompt, "clip": clip_source},
        "class_type": "CLIPTextEncode"
    }
    workflow["7"] = {
        "inputs": {"text": neg, "clip": clip_source},
        "class_type": "CLIPTextEncode"
    }

    # ── ControlNet (body-plan lock for non-humanoid monsters) ──────────────
    # The human-trained checkpoint humanises quadrupeds/dragons/insects (mw1
    # bug — Liam). A structural map of a reference of the RIGHT body plan, fed
    # through the xinsir union ControlNet, holds the silhouette so a spider
    # stays eight-legged, a dragon stays a dragon. control_mode picks the
    # preprocessor: 'depth' (DepthAnything — TONE-AGNOSTIC, so the model lights
    # the subject freely per the prompt: fixes the dark-render problem canny
    # had, since canny from a dark ref dragged the shading dark), 'lineart'
    # (clean anime outlines), or 'canny' (core node, raw edges). control_end
    # < 1.0 releases control partway so the LoRA/prompt still drive style.
    pos_src, neg_src = ["6", 0], ["7", 0]
    if control_image_name:
        workflow["40"] = {
            "inputs": {"image": control_image_name, "upload": "image"},
            "class_type": "LoadImage"
        }
        if control_mode == "depth":
            workflow["41"] = {
                "inputs": {"image": ["40", 0], "ckpt_name": "depth_anything_v2_vitl.pth", "resolution": 1024},
                "class_type": "DepthAnythingV2Preprocessor"
            }
            union_type = "depth"
        elif control_mode == "lineart":
            workflow["41"] = {
                "inputs": {"image": ["40", 0], "resolution": 1024},
                "class_type": "AnimeLineArtPreprocessor"
            }
            union_type = "canny/lineart/anime_lineart/mlsd"
        else:  # canny (core node)
            workflow["41"] = {
                "inputs": {"image": ["40", 0], "low_threshold": 0.35, "high_threshold": 0.75},
                "class_type": "Canny"
            }
            union_type = "canny/lineart/anime_lineart/mlsd"
        workflow["42"] = {
            "inputs": {"control_net_name": CONTROLNET_MODEL},
            "class_type": "ControlNetLoader"
        }
        workflow["44"] = {
            "inputs": {"type": union_type, "control_net": ["42", 0]},
            "class_type": "SetUnionControlNetType"
        }
        workflow["43"] = {
            "inputs": {
                "strength": control_strength,
                "start_percent": 0.0,
                "end_percent": control_end,
                "positive": ["6", 0],
                "negative": ["7", 0],
                "control_net": ["44", 0],
                "image": ["41", 0],
                "vae": ["4", 2],
            },
            "class_type": "ControlNetApplyAdvanced"
        }
        pos_src, neg_src = ["43", 0], ["43", 1]

    if init_image_name:
        workflow["11"] = {
            "inputs": {"image": init_image_name, "upload": "image"},
            "class_type": "LoadImage"
        }
        workflow["12"] = {
            "inputs": {"pixels": ["11", 0], "vae": ["4", 2]},
            "class_type": "VAEEncode"
        }
        latent_image_source = ["12", 0]
        denoise_val = denoise
        base_width, base_height = width, height
    elif hires:
        # First pass composes at the requested size — which should be the
        # checkpoint's native training res (832×1216 for NoobAI-XL); the
        # second pass upscales 1.5× and refines. The old version composed
        # the base pass at 0.65× (≈540×790) — BELOW the model's coherent
        # range, which is where the broken anatomy/proportions came from —
        # and "upscaled" merely back to native, so detail never exceeded a
        # single-pass render either.
        base_width, base_height = width, height
        workflow["5"] = {
            "inputs": {"width": base_width, "height": base_height, "batch_size": 1},
            "class_type": "EmptyLatentImage"
        }
        latent_image_source = ["5", 0]
        denoise_val = 1.0
    else:
        workflow["5"] = {
            "inputs": {"width": width, "height": height, "batch_size": 1},
            "class_type": "EmptyLatentImage"
        }
        latent_image_source = ["5", 0]
        denoise_val = 1.0

    workflow["3"] = {
        "inputs": {
            "seed": seed,
            "steps": 28,
            "cfg": CFG,
            "sampler_name": "euler_ancestral",
            "scheduler": "normal",
            "denoise": denoise_val,
            "model": model_source,
            "positive": pos_src,
            "negative": neg_src,
            "latent_image": latent_image_source
        },
        "class_type": "KSampler"
    }

    if hires and not init_image_name:
        workflow["13"] = {
            "inputs": {
                "samples": ["3", 0],
                "upscale_method": "bislerp",
                "width": (int(width * 1.5) // 8) * 8,
                "height": (int(height * 1.5) // 8) * 8,
                "crop": "disabled"
            },
            "class_type": "LatentUpscale"
        }
        workflow["14"] = {
            "inputs": {
                "seed": seed + 1,
                "steps": 20,
                "cfg": CFG,
                "sampler_name": "euler_ancestral",
                "scheduler": "normal",
                "denoise": hires_denoise,
                "model": model_source,
                "positive": pos_src,
                "negative": neg_src,
                "latent_image": ["13", 0]
            },
            "class_type": "KSampler"
        }

    # FaceDetailer (Impact Pack): detects the face in the decoded image and
    # re-renders that crop at high resolution — the fix for tiny broken
    # eyes at full-body framing. If no face is detected (monsters), it
    # passes the image through untouched. generate_portrait_comfy retries
    # without it if ComfyUI rejects the workflow (packs not installed).
    if face_detail:
        workflow["31"] = {
            "inputs": {"model_name": "bbox/face_yolov8m.pt"},
            "class_type": "UltralyticsDetectorProvider"
        }
        workflow["30"] = {
            "inputs": {
                "image": ["8", 0],
                "model": model_source,
                "clip": clip_source,
                "vae": ["4", 2],
                "positive": ["6", 0],
                "negative": ["7", 0],
                "bbox_detector": ["31", 0],
                "guide_size": 512,
                "guide_size_for": True,
                "max_size": 1024,
                "seed": seed + 2,
                "steps": 20,
                "cfg": CFG,
                "sampler_name": "euler_ancestral",
                "scheduler": "normal",
                "denoise": 0.45,
                "feather": 5,
                "noise_mask": True,
                "force_inpaint": True,
                "bbox_threshold": 0.5,
                "bbox_dilation": 10,
                "bbox_crop_factor": 3.0,
                "sam_detection_hint": "center-1",
                "sam_dilation": 0,
                "sam_threshold": 0.93,
                "sam_bbox_expansion": 0,
                "sam_mask_hint_threshold": 0.7,
                "sam_mask_hint_use_negative": "False",
                "drop_size": 10,
                "wildcard": "",
                "cycle": 1,
            },
            "class_type": "FaceDetailer"
        }
        # save the detailed image instead of the raw decode
        workflow["9"]["inputs"]["images"] = ["30", 0]

    return workflow


def _queue_prompt(workflow: dict) -> str | None:
    try:
        response = requests.post(
            f"{COMFY_URL}/prompt",
            json={"prompt": workflow},
            timeout=10.0
        )
        if response.status_code != 200:
            print(f"[ComfyUI] 400 detail: {response.text}")
            return None
        return response.json()["prompt_id"]
    except Exception as e:
        print(f"[ComfyUI] Failed to queue prompt: {e}")
        return None


def _wait_for_result(prompt_id: str, timeout: int = 180) -> str | None:
    start = time.time()
    while time.time() - start < timeout:
        try:
            resp = requests.get(f"{COMFY_URL}/history/{prompt_id}", timeout=5.0)
            history = resp.json()
            if prompt_id in history:
                outputs = history[prompt_id].get("outputs", {})
                for node_id, node_output in outputs.items():
                    if "images" in node_output:
                        return node_output["images"][0]["filename"]
        except Exception:
            pass
        time.sleep(2.0)
    return None


def _download_image(filename: str, save_path: str) -> bool:
    try:
        resp = requests.get(
            f"{COMFY_URL}/view",
            params={"filename": filename, "type": "output"},
            timeout=30.0
        )
        resp.raise_for_status()
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "wb") as f:
            f.write(resp.content)
        return True
    except Exception as e:
        print(f"[ComfyUI] Failed to download image: {e}")
        return False


def is_comfy_running() -> bool:
    try:
        requests.get(f"{COMFY_URL}/system_stats", timeout=3.0)
        return True
    except Exception:
        return False


def _upload_image(file_path: str) -> str | None:
    try:
        filename = os.path.basename(file_path)
        with open(file_path, "rb") as f:
            files = {"image": (filename, f, "image/png")}
            resp = requests.post(f"{COMFY_URL}/upload/image", files=files, timeout=30.0)
            resp.raise_for_status()
            data = resp.json()
            return data.get("name")
    except Exception as e:
        print(f"[ComfyUI] Failed to upload image {file_path}: {e}")
        return None


def generate_portrait_comfy(prompt: str, save_path: str, init_image_path: str = None, denoise: float = 0.45, negative: str = "", width: int = 832, height: int = 1216, hires: bool = False, hires_denoise: float = 0.62, lora_override: str = None, lora_strength_override: float = None, _noise_retry: bool = False, control_image_path: str = None, control_strength: float = 0.55, control_end: float = 0.5, control_mode: str = 'canny') -> bool:
    if not is_comfy_running():
        print("[ComfyUI] Server not running — skipping.")
        return False

    init_image_name = None
    if init_image_path and os.path.exists(init_image_path):
        init_image_name = _upload_image(init_image_path)

    control_image_name = None
    if control_image_path and os.path.exists(control_image_path):
        control_image_name = _upload_image(control_image_path)

    def _wf(fd=None):
        return _build_workflow(prompt, negative=negative, init_image_name=init_image_name, denoise=denoise, width=width, height=height, hires=hires, hires_denoise=hires_denoise, lora_override=lora_override, lora_strength_override=lora_strength_override, face_detail=fd, control_image_name=control_image_name, control_strength=control_strength, control_end=control_end, control_mode=control_mode)

    workflow = _wf()
    prompt_id = _queue_prompt(workflow)
    if not prompt_id and FACE_DETAIL:
        # Most likely the Impact Pack nodes aren't available — retry the
        # same generation without the FaceDetailer pass rather than failing.
        print("[ComfyUI] Queue failed with FaceDetailer — retrying without it.")
        workflow = _wf(fd=False)
        prompt_id = _queue_prompt(workflow)
    if not prompt_id and control_image_name:
        # ControlNet nodes rejected (model/nodes missing?) — fall back to a
        # plain prompt-only generation rather than failing the whole subject.
        print("[ComfyUI] Queue failed with ControlNet — retrying prompt-only.")
        control_image_name = None
        workflow = _wf()
        prompt_id = _queue_prompt(workflow)
    if not prompt_id:
        return False

    filename = _wait_for_result(prompt_id)
    if not filename:
        print("[ComfyUI] Timed out waiting for result.")
        return False

    if not _download_image(filename, save_path):
        return False

    # Rare v-pred seed collapse produces full-frame noise soup. Every valid
    # render on this pipeline has a large near-black region (the void
    # background); noise soup has none. Detect and retry once with a fresh
    # seed. `_noise_retry` guards against infinite recursion.
    if not _noise_retry and _looks_like_noise(save_path):
        print("[ComfyUI] Output looks like seed-collapse noise — retrying once.")
        return generate_portrait_comfy(prompt, save_path, init_image_path=init_image_path,
                                       denoise=denoise, negative=negative, width=width, height=height,
                                       hires=hires, hires_denoise=hires_denoise,
                                       lora_override=lora_override, lora_strength_override=lora_strength_override,
                                       _noise_retry=True, control_image_path=control_image_path,
                                       control_strength=control_strength, control_end=control_end, control_mode=control_mode)
    return True


def _looks_like_noise(path: str) -> bool:
    """True when the image has almost no dark pixels — the signature of a
    collapsed all-noise render on this pipeline (valid portraits always
    carry a large near-black void background)."""
    try:
        from PIL import Image
        im = Image.open(path).convert("L").resize((64, 64))
        px = list(im.getdata())
        dark = sum(1 for p in px if p < 45)
        return (dark / len(px)) < 0.05
    except Exception:
        return False
