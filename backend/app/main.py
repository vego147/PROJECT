import json
from datetime import datetime, timezone
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from .database import Base, engine, get_db
from .models import GeneratedPost
from .schemas import GenerateRequest, PostResponse
from .services.research import research_topic
from .services.generation_2 import generate_copy
from .services.images import make_demo_image, generate_image

Base.metadata.create_all(bind=engine)
app = FastAPI(title="AI Marketing Content Engine", version="1.0.0", description="Research, verify, generate and export social media posts.")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/api/health")
def health():
    return {"status": "ok", "service": "AI Marketing Content Engine"}

@app.post("/api/generate", response_model=PostResponse)
async def generate(request: GenerateRequest, db: Session = Depends(get_db)):
    topic = request.topic.strip()
    if len(topic) < 3:
        raise HTTPException(status_code=422, detail="Enter a topic with at least 3 characters.")
    sources, research_mode, research_stages = await research_topic(topic)
    content, generation_mode, generation_stages = await generate_copy(topic, request.platform, request.tone, sources)
    try:
        image_data = generate_image(
            prompt=content["image_prompt"],
            steps=4,
        )

    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Image generation failed: {str(e)}",
    )

    stages = research_stages + generation_stages + [{"name": "Visual generation", "status": "completed", "detail": "Image generated successfully using Cloudflare FLUX.1 Schnell."}]
    warnings = []
    if research_mode == "demo": warnings.append("Live web research is not configured. Reference links are provided, but their pages were not fetched or verified.")
    if generation_mode == "demo": warnings.append("Groq is not configured or did not respond. Content was created with a local template, not an LLM.")
    warnings.append(
    "Content has not been independently fact-checked. "
    "Verify factual claims against the original sources before publishing."
)
    verified_sources = []
    for source in sources:
        verified_sources.append({**source, "credibility": source.get("credibility", "Unverified")})
    mode = "live" if research_mode == "tavily" and generation_mode == "groq" else "hybrid" if research_mode == "tavily" or generation_mode == "groq" else "demo"

    # stages = research_stages + generation_stages

    # warnings = []

    # if research_mode == "demo":
    #     warnings.append(
    #         "Live web research is unavailable. Sources may not have been fetched or verified."
    #     )

    # if generation_mode == "fallback":
    #     warnings.append(
    #         "LLM generation failed. The content was created using a local fallback "
    #         "template and must be reviewed before publishing."
    #     )

    # if generation_mode == "demo":
    #     # Temporary compatibility with older versions of generation.py
    #     warnings.append(
    #         "Content was created using a local template, not an LLM."
    #     )

    # warnings.append(
    #     "Content has not been independently fact-checked. "
    #     "Verify factual claims against the original sources before publishing."
    # )

    # verified_sources = [
    #     {
    #         **source,
    #         "credibility": source.get("credibility", "Unverified"),
    #     }
    #     for source in sources
    # ]

    # # Explicitly represent the actual generation and research status.
    # if generation_mode == "fallback":
    #     mode = "fallback"
    # elif generation_mode == "demo":
    #     mode = "demo"
    # elif research_mode == "tavily" and generation_mode == "groq":
    #     mode = "live"
    # elif research_mode == "tavily" or generation_mode == "groq":
    #     mode = "hybrid"
    # else:
    #     mode = "demo"

    post = GeneratedPost(topic=topic, title=str(content["title"])[:300], caption=str(content["caption"]), hashtags=" ".join(content["hashtags"]), call_to_action=str(content["call_to_action"]), image_prompt=str(content["image_prompt"]), image_data=image_data, sources_json=json.dumps(verified_sources), mode=mode)
    db.add(post)
    db.commit()
    db.refresh(post)
    return PostResponse(id=post.id, topic=topic, platform=request.platform, tone=request.tone, article_title=str(content.get("article_title", topic)), article=str(content.get("article", "")), stages=stages, title=post.title, caption=post.caption, hashtags=content["hashtags"], call_to_action=post.call_to_action, image_prompt=post.image_prompt, image_data=image_data, sources=verified_sources, verification={"summary": "Sources and recency are surfaced for manual review. Automated checks are basic and do not establish that a claim is true.", "warnings": warnings, "confidence": "Basic"}, mode=mode, created_at=post.created_at)

@app.get("/api/posts")
def list_posts(limit: int = 20, db: Session = Depends(get_db)):
    limit = max(1, min(limit, 100))
    rows = db.query(GeneratedPost).order_by(GeneratedPost.id.desc()).limit(limit).all()
    return [{"id": p.id, "topic": p.topic, "article_title": p.topic, "article": "", "title": p.title, "caption": p.caption, "hashtags": p.hashtags, "call_to_action": p.call_to_action, "image_prompt": p.image_prompt, "image_data": p.image_data, "sources": json.loads(p.sources_json or "[]"), "mode": p.mode, "created_at": p.created_at} for p in rows]

@app.get("/api/posts/{post_id}")
def get_post(post_id: int, db: Session = Depends(get_db)):
    p = db.get(GeneratedPost, post_id)
    if not p:
        raise HTTPException(status_code=404, detail="Post not found.")
    return {"id": p.id, "topic": p.topic, "article_title": p.topic, "article": "", "title": p.title, "caption": p.caption, "hashtags": p.hashtags.split(), "call_to_action": p.call_to_action, "image_prompt": p.image_prompt, "image_data": p.image_data, "sources": json.loads(p.sources_json or "[]"), "mode": p.mode, "created_at": p.created_at}
