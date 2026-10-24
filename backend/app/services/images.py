import base64, html, re

def make_demo_image(topic: str, prompt: str) -> str:
    title = html.escape(topic[:42])
    subtitle = html.escape("AI MARKETING CONTENT ENGINE")
    # Self-contained SVG means image preview works without an image API key or network request.
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1080" viewBox="0 0 1080 1080"><defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#11152f"/><stop offset="55%" stop-color="#5234a8"/><stop offset="100%" stop-color="#f26d52"/></linearGradient><radialGradient id="orb"><stop offset="0%" stop-color="#ffe0a6" stop-opacity=".9"/><stop offset="100%" stop-color="#ff8f70" stop-opacity="0"/></radialGradient></defs><rect width="1080" height="1080" fill="url(#bg)"/><circle cx="820" cy="260" r="310" fill="url(#orb)"/><circle cx="820" cy="260" r="170" fill="none" stroke="#ffffff" stroke-opacity=".3" stroke-width="2"/><circle cx="820" cy="260" r="225" fill="none" stroke="#ffffff" stroke-opacity=".2" stroke-width="2"/><path d="M0 760 Q260 580 480 790 T1080 700 L1080 1080 L0 1080Z" fill="#0b1025" fill-opacity=".55"/><rect x="76" y="78" width="92" height="8" rx="4" fill="#ffd18c"/><text x="76" y="145" font-family="Arial,sans-serif" font-size="23" letter-spacing="4" fill="#fff" opacity=".75">{subtitle}</text><foreignObject x="76" y="570" width="900" height="270"><div xmlns="http://www.w3.org/1999/xhtml" style="font-family:Arial,sans-serif;font-size:76px;line-height:1.08;font-weight:700;color:white;overflow-wrap:anywhere">{title}</div></foreignObject><text x="78" y="930" font-family="Arial,sans-serif" font-size="24" letter-spacing="2" fill="#ffd18c">IDEAS INTO IMPACT</text></svg>'''
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()



import os
import base64
import requests
from dotenv import load_dotenv

load_dotenv()


def generate_image(
    prompt: str,
    output_path: str = "generated_image.jpg",
    steps: int = 4,
) -> str:
    """Generate an image using Cloudflare Workers AI FLUX.1 Schnell."""

    account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID")
    api_token = os.getenv("CLOUDFLARE_API_TOKEN")

    if not account_id or not api_token:
        raise ValueError("Missing Cloudflare credentials")

    model = "@cf/black-forest-labs/flux-1-schnell"

    url = (
        f"https://api.cloudflare.com/client/v4/accounts/"
        f"{account_id}/ai/run/{model}"
    )

    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
    }

    # This model accepts prompt and steps, not aspect_ratio.
    payload = {
        "prompt": prompt,
        "steps": steps,
    }

    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=180,
    )

    if not response.ok:
        raise RuntimeError(
            f"Cloudflare error {response.status_code}: "
            f"{response.text}"
        )

    result = response.json()["result"]
    return result["image"]
    # image_data = base64.b64decode(result["image"])

    # with open(output_path, "wb") as image_file:
    #     image_file.write(image_data)

    # return output_path
