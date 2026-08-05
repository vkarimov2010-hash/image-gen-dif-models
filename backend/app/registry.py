"""Реестр моделей kie.ai.

Единственное место, которое нужно менять, чтобы добавить новую модель:
достаточно добавить новый ModelSpec в MODEL_REGISTRY. Роутер /models и
фронтенд ничего не хардкодят — они полностью опираются на этот реестр.

Стоимость (estimated_credits) — приблизительная, для оценки ДО генерации.
Фактическая стоимость берётся из поля creditsConsumed ответа kie.ai
recordInfo и является авторитетной. Ориентировочные цифры нужно сверить на
https://kie.ai/pricing при подключении реального API-ключа.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable


class Style(str, Enum):
    PHOTOREALISTIC = "photorealistic"
    ANIME = "anime"
    DIGITAL_ART = "digital_art"
    THREE_D = "3d_render"
    SKETCH = "sketch"
    PAINTING = "painting"


class AspectPreset(str, Enum):
    SQUARE = "square"          # 1:1
    LANDSCAPE = "landscape"    # 4:3 / 16:9
    PORTRAIT = "portrait"      # 3:4
    STORY = "story"            # 9:16
    WIDE = "wide"              # 16:9


# Промт-суффиксы для моделей без отдельного параметра стиля.
STYLE_PROMPT_SUFFIX: dict[Style, str] = {
    Style.PHOTOREALISTIC: "photorealistic, highly detailed, realistic lighting",
    Style.ANIME: "anime style, vibrant colors, cel shading",
    Style.DIGITAL_ART: "digital art, concept art style",
    Style.THREE_D: "3d render, octane render, cinematic lighting",
    Style.SKETCH: "pencil sketch, hand-drawn line art",
    Style.PAINTING: "oil painting, textured brush strokes",
}


@dataclass(frozen=True)
class ModelSpec:
    id: str  # внутренний slug, используется в API и БД
    kie_model: str  # значение поля "model" в запросе к kie.ai
    display_name: str
    provider: str
    supports_negative_prompt: bool
    supports_seed: bool
    estimated_credits: int
    build_input: Callable[[str, Style, AspectPreset, str | None, int | None], dict]
    active: bool = True


def _with_style_suffix(prompt: str, style: Style) -> str:
    suffix = STYLE_PROMPT_SUFFIX[style]
    return f"{prompt}, {suffix}"


_FLUX2_ASPECT: dict[AspectPreset, str] = {
    AspectPreset.SQUARE: "1:1",
    AspectPreset.LANDSCAPE: "4:3",
    AspectPreset.PORTRAIT: "3:4",
    AspectPreset.STORY: "9:16",
    AspectPreset.WIDE: "16:9",
}


def _build_flux2_input(
    prompt: str, style: Style, aspect: AspectPreset,
    negative_prompt: str | None, seed: int | None,
) -> dict:
    return {
        "prompt": _with_style_suffix(prompt, style),
        "aspect_ratio": _FLUX2_ASPECT[aspect],
        "resolution": "1K",
    }


_IMAGEN4_ASPECT: dict[AspectPreset, str] = {
    AspectPreset.SQUARE: "1:1",
    AspectPreset.LANDSCAPE: "4:3",
    AspectPreset.PORTRAIT: "3:4",
    AspectPreset.STORY: "9:16",
    AspectPreset.WIDE: "16:9",
}


def _build_imagen4_input(
    prompt: str, style: Style, aspect: AspectPreset,
    negative_prompt: str | None, seed: int | None,
) -> dict:
    payload = {
        "prompt": _with_style_suffix(prompt, style),
        "aspect_ratio": _IMAGEN4_ASPECT[aspect],
    }
    if negative_prompt:
        payload["negative_prompt"] = negative_prompt
    if seed is not None:
        payload["seed"] = str(seed)
    return payload


_IDEOGRAM_IMAGE_SIZE: dict[AspectPreset, str] = {
    AspectPreset.SQUARE: "square_hd",
    AspectPreset.LANDSCAPE: "landscape_4_3",
    AspectPreset.PORTRAIT: "portrait_4_3",
    AspectPreset.STORY: "portrait_16_9",
    AspectPreset.WIDE: "landscape_16_9",
}

_IDEOGRAM_STYLE: dict[Style, str] = {
    Style.PHOTOREALISTIC: "REALISTIC",
    Style.ANIME: "GENERAL",
    Style.DIGITAL_ART: "GENERAL",
    Style.THREE_D: "GENERAL",
    Style.SKETCH: "GENERAL",
    Style.PAINTING: "GENERAL",
}


def _build_ideogram_input(
    prompt: str, style: Style, aspect: AspectPreset,
    negative_prompt: str | None, seed: int | None,
) -> dict:
    # Ideogram даёт структурированный style-параметр — суффикс в промт не добавляем,
    # но для стилей без прямого маппинга помогаем описанием в промте.
    effective_prompt = prompt
    if style in (Style.ANIME, Style.THREE_D, Style.SKETCH, Style.PAINTING):
        effective_prompt = f"{prompt}, {STYLE_PROMPT_SUFFIX[style]}"
    payload = {
        "prompt": effective_prompt,
        "image_size": _IDEOGRAM_IMAGE_SIZE[aspect],
        "style": _IDEOGRAM_STYLE[style],
        "rendering_speed": "BALANCED",
    }
    if negative_prompt:
        payload["negative_prompt"] = negative_prompt
    if seed is not None:
        payload["seed"] = seed
    return payload


_GPT_IMAGE2_ASPECT: dict[AspectPreset, str] = {
    AspectPreset.SQUARE: "1:1",
    AspectPreset.LANDSCAPE: "4:3",
    AspectPreset.PORTRAIT: "3:4",
    AspectPreset.STORY: "9:16",
    AspectPreset.WIDE: "16:9",
}


def _build_gpt_image2_input(
    prompt: str, style: Style, aspect: AspectPreset,
    negative_prompt: str | None, seed: int | None,
) -> dict:
    return {
        "prompt": _with_style_suffix(prompt, style),
        "aspect_ratio": _GPT_IMAGE2_ASPECT[aspect],
        "resolution": "1K",
    }


# Grok Imagine не поддерживает 4:3/3:4 — берём ближайшие доступные (3:2/2:3).
_GROK_IMAGINE_ASPECT: dict[AspectPreset, str] = {
    AspectPreset.SQUARE: "1:1",
    AspectPreset.LANDSCAPE: "3:2",
    AspectPreset.PORTRAIT: "2:3",
    AspectPreset.STORY: "9:16",
    AspectPreset.WIDE: "16:9",
}


def _build_grok_imagine_input(
    prompt: str, style: Style, aspect: AspectPreset,
    negative_prompt: str | None, seed: int | None,
) -> dict:
    return {
        "prompt": _with_style_suffix(prompt, style),
        "aspect_ratio": _GROK_IMAGINE_ASPECT[aspect],
    }


_SEEDREAM5_ASPECT: dict[AspectPreset, str] = {
    AspectPreset.SQUARE: "1:1",
    AspectPreset.LANDSCAPE: "4:3",
    AspectPreset.PORTRAIT: "3:4",
    AspectPreset.STORY: "9:16",
    AspectPreset.WIDE: "16:9",
}


def _build_seedream5_lite_input(
    prompt: str, style: Style, aspect: AspectPreset,
    negative_prompt: str | None, seed: int | None,
) -> dict:
    return {
        "prompt": _with_style_suffix(prompt, style),
        "aspect_ratio": _SEEDREAM5_ASPECT[aspect],
        "quality": "basic",
    }


_QWEN2_IMAGE_SIZE: dict[AspectPreset, str] = {
    AspectPreset.SQUARE: "1:1",
    AspectPreset.LANDSCAPE: "4:3",
    AspectPreset.PORTRAIT: "3:4",
    AspectPreset.STORY: "9:16",
    AspectPreset.WIDE: "16:9",
}


def _build_qwen2_input(
    prompt: str, style: Style, aspect: AspectPreset,
    negative_prompt: str | None, seed: int | None,
) -> dict:
    # У Qwen2 лимит промта ~800 символов на стороне kie.ai — при более длинном
    # промте задача этой модели упадёт с ошибкой, остальные модели батча не
    # затронет (см. изоляцию сбоев в generation_service).
    payload = {
        "prompt": _with_style_suffix(prompt, style),
        "image_size": _QWEN2_IMAGE_SIZE[aspect],
    }
    if seed is not None:
        payload["seed"] = seed
    return payload


_NANO_BANANA_ASPECT: dict[AspectPreset, str] = {
    AspectPreset.SQUARE: "1:1",
    AspectPreset.LANDSCAPE: "4:3",
    AspectPreset.PORTRAIT: "3:4",
    AspectPreset.STORY: "9:16",
    AspectPreset.WIDE: "16:9",
}


def _build_nano_banana_input(
    prompt: str, style: Style, aspect: AspectPreset,
    negative_prompt: str | None, seed: int | None,
) -> dict:
    return {
        "prompt": _with_style_suffix(prompt, style),
        "aspect_ratio": _NANO_BANANA_ASPECT[aspect],
    }


def _build_nano_banana2_input(
    prompt: str, style: Style, aspect: AspectPreset,
    negative_prompt: str | None, seed: int | None,
) -> dict:
    return {
        "prompt": _with_style_suffix(prompt, style),
        "image_input": [],
        "aspect_ratio": _NANO_BANANA_ASPECT[aspect],
        "resolution": "1K",
        "output_format": "png",
    }


_NANO_BANANA2_LITE_ASPECT: dict[AspectPreset, str] = {
    AspectPreset.SQUARE: "1:1",
    AspectPreset.LANDSCAPE: "4:3",
    AspectPreset.PORTRAIT: "3:4",
    AspectPreset.STORY: "9:16",
    AspectPreset.WIDE: "16:9",
}


def _build_nano_banana2_lite_input(
    prompt: str, style: Style, aspect: AspectPreset,
    negative_prompt: str | None, seed: int | None,
) -> dict:
    return {
        "prompt": _with_style_suffix(prompt, style),
        "aspect_ratio": _NANO_BANANA2_LITE_ASPECT[aspect],
    }


_ZIMAGE_ASPECT: dict[AspectPreset, str] = {
    AspectPreset.SQUARE: "1:1",
    AspectPreset.LANDSCAPE: "4:3",
    AspectPreset.PORTRAIT: "3:4",
    AspectPreset.STORY: "9:16",
    AspectPreset.WIDE: "16:9",
}


def _build_zimage_input(
    prompt: str, style: Style, aspect: AspectPreset,
    negative_prompt: str | None, seed: int | None,
) -> dict:
    # aspect_ratio у Z-Image обязателен (createTask падает с "This field is
    # required" без него) — подтверждено вручную реальными запросами к kie.ai,
    # значение "auto" не принимается, только конкретные соотношения.
    return {
        "prompt": _with_style_suffix(prompt, style),
        "aspect_ratio": _ZIMAGE_ASPECT[aspect],
    }


MODEL_REGISTRY: list[ModelSpec] = [
    ModelSpec(
        id="flux2-pro",
        kie_model="flux-2/pro-text-to-image",
        display_name="Flux-2 Pro",
        provider="Black Forest Labs",
        supports_negative_prompt=False,
        supports_seed=False,
        estimated_credits=20,
        build_input=_build_flux2_input,
    ),
    # Imagen 4, Imagen 4 Ultra и Ideogram V3 воспроизводимо возвращают мгновенный
    # transient-сбой на стороне kie.ai (см. "Известная проблема" в progress.md) —
    # выключены (active=False), пока kie.ai не починит эти модели.
    ModelSpec(
        id="imagen4",
        kie_model="google/imagen4",
        display_name="Google Imagen 4",
        provider="Google",
        supports_negative_prompt=True,
        supports_seed=True,
        estimated_credits=30,
        build_input=_build_imagen4_input,
        active=False,
    ),
    ModelSpec(
        id="ideogram-v3",
        kie_model="ideogram/v3-text-to-image",
        display_name="Ideogram V3",
        provider="Ideogram",
        supports_negative_prompt=True,
        supports_seed=True,
        estimated_credits=16,
        build_input=_build_ideogram_input,
        active=False,
    ),
    ModelSpec(
        id="imagen4-ultra",
        kie_model="google/imagen4-ultra",
        display_name="Google Imagen 4 Ultra",
        provider="Google",
        supports_negative_prompt=True,
        supports_seed=True,
        estimated_credits=45,
        build_input=_build_imagen4_input,
        active=False,
    ),
    ModelSpec(
        id="gpt-image-2",
        kie_model="gpt-image-2-text-to-image",
        display_name="GPT Image 2",
        provider="OpenAI",
        supports_negative_prompt=False,
        supports_seed=False,
        estimated_credits=6,
        build_input=_build_gpt_image2_input,
    ),
    ModelSpec(
        id="grok-imagine",
        kie_model="grok-imagine/text-to-image",
        display_name="Grok Imagine",
        provider="xAI",
        supports_negative_prompt=False,
        supports_seed=False,
        estimated_credits=4,
        build_input=_build_grok_imagine_input,
    ),
    ModelSpec(
        id="seedream5-lite",
        kie_model="seedream/5-lite-text-to-image",
        display_name="Seedream 5.0 Lite",
        provider="ByteDance",
        supports_negative_prompt=False,
        supports_seed=False,
        estimated_credits=6,
        build_input=_build_seedream5_lite_input,
    ),
    ModelSpec(
        id="qwen2-t2i",
        kie_model="qwen2/text-to-image",
        display_name="Qwen2",
        provider="Alibaba",
        supports_negative_prompt=False,
        supports_seed=True,
        estimated_credits=6,
        build_input=_build_qwen2_input,
    ),
    ModelSpec(
        id="nano-banana",
        kie_model="google/nano-banana",
        display_name="Google Nano Banana",
        provider="Google",
        supports_negative_prompt=False,
        supports_seed=False,
        estimated_credits=4,
        build_input=_build_nano_banana_input,
    ),
    ModelSpec(
        id="nano-banana-2",
        kie_model="nano-banana-2",
        display_name="Google Nano Banana 2",
        provider="Google",
        supports_negative_prompt=False,
        supports_seed=False,
        estimated_credits=8,
        build_input=_build_nano_banana2_input,
    ),
    ModelSpec(
        id="nano-banana-2-lite",
        kie_model="nano-banana-2-lite",
        display_name="Google Nano Banana 2 Lite",
        provider="Google",
        supports_negative_prompt=False,
        supports_seed=False,
        estimated_credits=4,
        build_input=_build_nano_banana2_lite_input,
    ),
    ModelSpec(
        id="z-image",
        kie_model="z-image",
        display_name="Z-Image",
        provider="Tongyi-MAI",
        supports_negative_prompt=False,
        supports_seed=False,
        estimated_credits=1,
        build_input=_build_zimage_input,
    ),
]

_REGISTRY_BY_ID: dict[str, ModelSpec] = {m.id: m for m in MODEL_REGISTRY}


def get_model(model_id: str) -> ModelSpec | None:
    return _REGISTRY_BY_ID.get(model_id)


def list_active_models() -> list[ModelSpec]:
    return [m for m in MODEL_REGISTRY if m.active]
