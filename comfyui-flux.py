import json
import subprocess
from pathlib import Path
import modal

def download_with_aria2c():
    # Ensure ComfyUI is installed before proceeding
    subprocess.run("comfy --skip-prompt install --nvidia", shell=True, check=True)

    # Base directory for ComfyUI models
    base_dir = "/root/comfy/ComfyUI/models"

    # Ensure directories exist
    Path(f"{base_dir}/unet").mkdir(parents=True, exist_ok=True)
    Path(f"{base_dir}/vae").mkdir(parents=True, exist_ok=True)
    Path(f"{base_dir}/clip").mkdir(parents=True, exist_ok=True)
    Path(f"{base_dir}/loras").mkdir(parents=True, exist_ok=True)

    # URLs for the models with correct file extensions
    urls = {
        f"{base_dir}/unet/hunyuan-video-t2v-720p-Q8_0.gguf": "https://huggingface.co/city96/HunyuanVideo-gguf/resolve/main/hunyuan-video-t2v-720p-Q8_0.gguf",
        f"{base_dir}/vae/hunyuan_video_vae_bf16.safetensors": "https://huggingface.co/Kijai/HunyuanVideo_comfy/resolve/main/hunyuan_video_vae_bf16.safetensors?download=true",
        f"{base_dir}/clip/clip_l.safetensors": "https://huggingface.co/Comfy-Org/HunyuanVideo_repackaged/resolve/main/split_files/text_encoders/clip_l.safetensors",
        f"{base_dir}/clip/llava_llama3_fp8_scaled.safetensors": "https://huggingface.co/Comfy-Org/HunyuanVideo_repackaged/resolve/main/split_files/text_encoders/llava_llama3_fp8_scaled.safetensors",
        f"{base_dir}/loras/hyvideo_FastVideo_LoRA-fp8.safetensors": "https://huggingface.co/Kijai/HunyuanVideo_comfy/resolve/main/hyvideo_FastVideo_LoRA-fp8.safetensors",
        f"{base_dir}/loras/img2vid544p.safetensors": "https://huggingface.co/leapfusion-image2vid-test/image2vid-960x544/resolve/main/img2vid544p.safetensors",
        f"{base_dir}/loras/img2vid320p.safetensors": "https://huggingface.co/leapfusion-image2vid-test/image2vid-512x320/resolve/main/img2vid.safetensors?download=true",
        f"{base_dir}/unet/hunyuan_video_t2v_720p_bf16.safetensors": "https://huggingface.co/Kijai/HunyuanVideo_comfy/resolve/main/hunyuan_video_720_cfgdistill_bf16.safetensors?download=true"
    }

    # Download each model using aria2c directly to its destination
    for destination, url in urls.items():
        subprocess.run(f"aria2c --console-log-level=error -c -x 16 -s 16 -k 1M -d {Path(destination).parent} -o {Path(destination).name} {url}", shell=True, check=True)

hunyuan = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("git")
    .apt_install("nano")
    .apt_install("ffmpeg")
    .apt_install("libgl1-mesa-glx")
    .apt_install("libglib2.0-0")
    .apt_install("aria2")  # Install aria2 for downloading
    .pip_install("comfy-cli")
    .pip_install("hf_transfer")

    .env({"HF_HUB_ENABLE_HF_TRANSFER": "1"})
    .run_function(
        download_with_aria2c
    )
    .run_commands(
        "comfy node install https://github.com/city96/ComfyUI-GGUF",
        "comfy node install https://github.com/kijai/ComfyUI-HunyuanVideoWrapper.git",
        "comfy node install https://github.com/Fannovel16/ComfyUI-Frame-Interpolation.git",
        "comfy node install https://github.com/cubiq/ComfyUI_essentials.git",
        "comfy node install https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git",
        "comfy node install https://github.com/kijai/ComfyUI-KJNodes.git",
        "comfy node install https://github.com/rgthree/rgthree-comfy.git",
        "comfy node install https://github.com/kijai/ComfyUI-Florence2.git",
        "comfy node install https://github.com/SLAPaper/ComfyUI-Image-Selector.git",
        "comfy node install https://github.com/facok/ComfyUI-TeaCacheHunyuanVideo.git",
        "comfy node install https://github.com/pythongosssss/ComfyUI-Custom-Scripts.git",
        "comfy node install https://github.com/Suzie1/ComfyUI_Comfyroll_CustomNodes"
    )
)

app = modal.App(name="hunyuan-comfyui", image=hunyuan)
@app.function(
    allow_concurrent_inputs=10,
    concurrency_limit=1,
    container_idle_timeout=30,
    timeout=3200,
    gpu="a10g", # here you can change the gpu, i recommend either a10g or T4
)
@modal.web_server(8000, startup_timeout=60)
def ui():
    subprocess.Popen("comfy launch -- --listen 0.0.0.0 --port 8000", shell=True)
