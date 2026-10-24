# import json, re
# from ..config import settings

# async def generate_copy(topic: str, platform: str, tone: str, sources: list[dict]) -> tuple[dict, str, list[dict]]:
#     stages=[]
#     extracted=[{'title':s.get('title'),'url':s.get('url'),'published_date':s.get('published_date'),'content':(s.get('extracted_content') or s.get('snippet') or '')[:5000]} for s in sources[:5]]
#     evidence=json.dumps(extracted,ensure_ascii=False)[:18000]
#     if settings.groq_api_key:
#         try:
#             from langchain_groq import ChatGroq
#             from langchain_core.messages import SystemMessage, HumanMessage
#             llm=ChatGroq(api_key=settings.groq_api_key,model=settings.groq_model,temperature=0.45)
#             prompt=f'''Create a factual, useful content package about: {topic}\nPlatform: {platform}; tone: {tone}.\nIMPORTANT: base the article and all social content on the extracted source text below. Do not invent facts, quotes, statistics, dates, or claims. If source text is thin, explicitly state the limits and write cautiously. Keep source URLs in mind but do not claim they verify anything you cannot see.\nSOURCE MATERIAL:\n{evidence}\nReturn ONLY JSON with keys article_title, article (website-ready article, 400-700 words when evidence allows, with intro, informative sections and conclusion), title (social hook), caption, hashtags (array of 5-8 strings including #), call_to_action, image_prompt. Image prompt should describe an original editorial visual based on the article, no text/logos/watermarks, landscape 16:9 composition. Social caption and tags must derive from the article/source content, not just repeat the topic.'''
#             response=await llm.ainvoke([SystemMessage(content='You are a careful journalist and social content editor. Separate evidence from uncertainty. Return valid JSON only.'),HumanMessage(content=prompt)])
#             raw=response.content if isinstance(response.content,str) else str(response.content)
#             match=re.search(r'\{.*\}',raw,re.S); data=json.loads(match.group(0) if match else raw)
#             required=['article_title','article','title','caption','hashtags','call_to_action','image_prompt']
#             if all(k in data for k in required) and isinstance(data['hashtags'],list) and len(str(data['article']))>100:
#                 stages.append({'name':'LLM article + social package','status':'completed','detail':f'Generated article and {platform} copy using {settings.groq_model}.'})
#                 stages.append({'name':'Image prompt','status':'completed','detail':'Prompt generated from the article and social content.'})
#                 return data,'groq',stages
#             raise ValueError('LLM response missing required fields')
#         except Exception as e:
#             stages.append({'name':'LLM generation','status':'failed','detail':f'LLM call failed or returned invalid JSON ({type(e).__name__}); using clearly labelled fallback.'})
#     clean=topic.strip().rstrip('.!?')
#     evidence_text=' '.join((s.get('extracted_content') or s.get('snippet') or '') for s in sources[:3])
#     usable=re.sub(r'\s+',' ',evidence_text).strip()
#     article=(f'# {clean}\n\n{usable[:1400]}\n\n## What this means\n\nThe available material provides an initial starting point for understanding {clean}. The details should be checked against the original publication, including dates, context, and any figures, before this draft is published.\n\n## Conclusion\n\nUse the linked source material to confirm the key points and add relevant context for your audience. This is an automatically assembled starter article, not independently verified reporting.') if usable else f'# {clean}\n\nThis is a starter article outline about {clean}. Live source text was unavailable, so specific factual claims have deliberately been omitted. Research and verify relevant primary sources before publication.'
#     data={'article_title':f'{clean}: Key Developments and Context','article':article,'title':f'A closer look at {clean}','caption':f'What the available source material says about {clean}. Review the original reporting, confirm the context, and check dates and claims before sharing.','hashtags':['#'+re.sub(r'[^a-zA-Z0-9]','',w).title() for w in clean.split()[:3] if re.sub(r'[^a-zA-Z0-9]','',w)]+['#Insights','#Research','#Updates'],'call_to_action':'Read the sources, verify the details, and share your perspective.','image_prompt':f'Create an editorial visual illustrating {clean}, grounded in the available article context; modern professional art direction, strong composition, landscape 16:9, no text, no logos, no watermark.'}
#     stages.append({'name':'Fallback article + social package','status':'warning','detail':'Groq was not configured or failed. This is a template based on available snippets, not an LLM-written article.'})
#     stages.append({'name':'Image prompt','status':'completed','detail':'Created a fallback prompt from the topic and available research text.'})
#     return data,'demo',stages




from curses import raw
import json
import re
from json_repair import repair_json

from ..config import settings


async def generate_copy(
    topic: str,
    platform: str,
    tone: str,
    sources: list[dict],
) -> tuple[dict, str, list[dict]]:
    stages = []

    extracted = [
        {
            "title": source.get("title"),
            "url": source.get("url"),
            "published_date": source.get("published_date"),
            "content": (
                source.get("extracted_content")
                or source.get("snippet")
                or ""
            )[:5000],
        }
        for source in sources[:5]
    ]

    evidence = json.dumps(
        extracted,
        ensure_ascii=False,
    )[:18000]

    if settings.groq_api_key:
        try:
            from langchain_groq import ChatGroq
            from langchain_core.messages import (
                SystemMessage,
                HumanMessage,
            )

            llm = ChatGroq(
                api_key=settings.groq_api_key,
                model=settings.groq_model,
                temperature=0.45,
            )

            prompt = f"""
You are a professional journalist, research analyst, and social media
content strategist working for a credible digital publication.

Your task is to create a complete, publication-ready content package
based on the topic and source material provided below.

TOPIC: {topic}
PLATFORM: {platform}
TONE: {tone}

==================================================
1. SOURCE ACCURACY AND FACTUAL INTEGRITY
==================================================

Treat the supplied source material as your evidence base.

- Use only facts supported by the supplied source material.
- Never invent names, quotations, statistics, dates, events, financial
  figures, announcements, or statements.
- Do not present assumptions or speculation as established facts.
- Distinguish confirmed facts from analysis and interpretation.
- If sources disagree, explain the discrepancy instead of choosing
  an unsupported version.
- Do not claim that a source confirms something unless its supplied
  content actually supports that claim.
- URLs are references, not proof that an article was successfully
  retrieved or verified.
- Do not invent citations or source URLs.
- If evidence is insufficient, explicitly acknowledge the limitation.
- Never add unrelated information merely to increase article length.

==================================================
2. ARTICLE GENERATION
==================================================

Write a complete article of 500-700 words.

The article must be a finished draft, not an outline, summary,
introduction-only response, or collection of short paragraphs.

Required structure:

A. HEADLINE
Write an informative, engaging headline appropriate for the topic.

B. INTRODUCTION
Write 80-120 words introducing the subject, explaining its importance,
and establishing the main angle of the article.

C. MAIN BODY
Write at least four informative sections with descriptive headings.

Each section must:
- Explain a distinct aspect of the topic.
- Include relevant factual details supported by the sources.
- Explain the significance or implications of those details.
- Connect logically with the preceding section.
- Avoid repeating information already covered.

Use specific evidence wherever available. Explain who, what, when,
where, and why when those details are supported by the research.

D. CONTEXT AND ANALYSIS
Explain the broader significance, relevant background, implications,
or potential impact of the reported developments.

Clearly distinguish factual reporting from analysis.
Do not manufacture expert opinions, industry reactions, or predictions.

E. CONCLUSION
Finish with a concise conclusion that summarizes the main findings
and explains what readers should take away from the article.

LENGTH AND QUALITY RULES:

- Target 600 words, with an acceptable range of 500-700 words.
- The word count applies to the article field only.
- Use paragraphs with meaningful detail, not repetitive filler.
- Include at least four descriptive section headings in the body.
- Do not count the headline or social media copy toward article length.
- Every paragraph must contribute new information, context, or analysis.
- If the supplied evidence cannot support a responsible 500-word article,
  do not fabricate facts or pad the article. Explain the evidence
  limitation and provide the most complete accurate draft possible.
- Never return only one paragraph when a full article is requested.

==================================================
3. SOCIAL MEDIA CONTENT
==================================================

Generate original social media content derived from the article
and its supporting evidence.

ARTICLE TITLE:
- Clear, specific, and informative.
- Avoid misleading or exaggerated claims.

SOCIAL TITLE:
- Create an engaging hook appropriate for {platform}.
- Do not use clickbait that misrepresents the story.

CAPTION:
- Summarize the most important supported information.
- Explain why the topic matters to the intended audience.
- Match the requested tone: {tone}.
- Do not simply repeat the title.
- Avoid generic filler and unsupported claims.
- Keep the caption suitable for the selected platform.

HASHTAGS:
- Return 5-8 relevant hashtags.
- Every hashtag must begin with #.
- Use meaningful topic-specific tags.
- Avoid irrelevant trending tags.

CALL TO ACTION:
- Provide a relevant, natural next step for the audience.
- Do not use misleading engagement bait.

==================================================
4. IMAGE GENERATION PROMPT
==================================================

Create a detailed image-generation prompt for an original editorial
visual illustrating the article's central subject.

The prompt must specify:
- Main subject and visual narrative.
- Relevant objects, setting, or environment.
- Composition and focal point.
- Lighting, atmosphere, and visual style.
- A professional editorial art direction.
- Landscape 16:9 composition.
- No text, typography, logos, or watermarks.

The visual must reflect the actual subject of the article.
Do not depict unsupported events, fabricated people, or imaginary
scenes as documentary evidence.

==================================================
5. REQUIRED OUTPUT FORMAT
==================================================

Return exactly one valid JSON object.

Include all seven keys listed below:

{{
  "article_title": "Complete article headline",
  "article": "Full article with introduction, section headings, body, and conclusion",
  "title": "Social media hook",
  "caption": "Platform-specific caption",
  "hashtags": [
    "#RelevantTag1",
    "#RelevantTag2",
    "#RelevantTag3",
    "#RelevantTag4",
    "#RelevantTag5"
  ],
  "call_to_action": "Relevant audience action",
  "image_prompt": "Detailed editorial image-generation prompt"
}}

OUTPUT RULES:

- All seven keys are mandatory.
- All text fields must contain meaningful, non-empty strings.
- hashtags must be an array of 5-8 strings.
- The article must be complete and target 500-700 words when evidence
  supports that length.
- Use valid JSON with double quotes around keys and string values.
- Escape quotation marks and newline characters correctly.
- Do not wrap the JSON in Markdown code fences.
- Do not include explanations before or after the JSON.
- Do not omit fields.
- Do not return a partial article.
- Do not invent facts to satisfy the requested length.

==================================================
6. RESEARCH MATERIAL
==================================================

Use the following source material as the basis for the entire package:

{evidence}
"""

            response = await llm.ainvoke(
                [
                    SystemMessage(
                        content=(
                            "You are a careful journalist and social "
                            "content editor. Separate evidence from "
                            "uncertainty. Return valid JSON only."
                        )
                    ),
                    HumanMessage(content=prompt),
                ]
            )

            raw = (
                response.content
                if isinstance(response.content, str)
                else str(response.content)
            )

            
            match = re.search(r"\{.*\}", raw, re.S)
            json_text = match.group(0) if match else raw
                
            try:
                data = json.loads(json_text)
            except json.JSONDecodeError:
                data = repair_json(json_text, return_objects=True)
            
            if not isinstance(data, dict):
                raise ValueError("LLM response did not produce a JSON object")
    

            required = [
                "article_title",
                "article",
                "title",
                "caption",
                "hashtags",
                "call_to_action",
                "image_prompt",
            ]

            if (
                all(key in data for key in required)
                and isinstance(data["hashtags"], list)
                and len(str(data["article"])) > 100
            ):
                stages.append(
                    {
                        "name": "LLM article + social package",
                        "status": "completed",
                        "detail": (
                            "Generated article and "
                            f"{platform} copy using "
                            f"{settings.groq_model}."
                        ),
                    }
                )

                stages.append(
                    {
                        "name": "Image prompt",
                        "status": "completed",
                        "detail": (
                            "Prompt generated from the article "
                            "and social content."
                        ),
                    }
                )

                return data, "groq", stages

            raise ValueError(
                "LLM response missing required fields"
            )
        
        except Exception as e:
            print(f"Groq error: {type(e).__name__}: {e}")
        
            stages.append(
                {
                    "name": "LLM generation",
                    "status": "failed",
                    "detail": (
                        f"{type(e).__name__}: {e}"
                    ),
                }
            )

        # except Exception as e:
        #     stages.append(
        #         {
        #             "name": "LLM generation",
        #             "status": "failed",
        #             "detail": (
        #                 "LLM call failed or returned invalid JSON "
        #                 f"({type(e).__name__}); "
        #                 "using clearly labelled fallback."
        #             ),
        #         }
        #     )

    clean = topic.strip().rstrip(".!?")

    evidence_text = " ".join(
        (
            source.get("extracted_content")
            or source.get("snippet")
            or ""
        )
        for source in sources[:3]
    )

    usable = re.sub(
        r"\s+",
        " ",
        evidence_text,
    ).strip()

    if usable:
        article = (
            f"# {clean}\n\n"
            f"{usable[:1400]}\n\n"
            "## What this means\n\n"
            f"The available material provides an initial "
            f"starting point for understanding {clean}. "
            "The details should be checked against the original "
            "publication, including dates, context, and any "
            "figures, before this draft is published.\n\n"
            "## Conclusion\n\n"
            "Use the linked source material to confirm the key "
            "points and add relevant context for your audience. "
            "This is an automatically assembled starter article, "
            "not independently verified reporting."
        )
    else:
        article = (
            f"# {clean}\n\n"
            f"This is a starter article outline about {clean}. "
            "Live source text was unavailable, so specific "
            "factual claims have deliberately been omitted. "
            "Research and verify relevant primary sources "
            "before publication."
        )

    hashtags = [
        "#"
        + re.sub(r"[^a-zA-Z0-9]", "", word).title()
        for word in clean.split()[:3]
        if re.sub(r"[^a-zA-Z0-9]", "", word)
    ]

    hashtags += [
        "#Insights",
        "#Research",
        "#Updates",
    ]

    data = {
        "article_title": (
            f"{clean}: Key Developments and Context"
        ),
        "article": article,
        "title": f"A closer look at {clean}",
        "caption": (
            f"What the available source material says about "
            f"{clean}. Review the original reporting, confirm "
            "the context, and check dates and claims before sharing."
        ),
        "hashtags": hashtags,
        "call_to_action": (
            "Read the sources, verify the details, "
            "and share your perspective."
        ),
        "image_prompt": (
            f"Create an editorial visual illustrating {clean}, "
            "grounded in the available article context; modern "
            "professional art direction, strong composition, "
            "landscape 16:9, no text, no logos, no watermark."
        ),
    }

    stages.append(
        {
            "name": "Fallback article + social package",
            "status": "warning",
            "detail": (
                "Groq was not configured or failed. "
                "This is a template based on available snippets, "
                "not an LLM-written article."
            ),
        }
    )

    stages.append(
        {
            "name": "Image prompt",
            "status": "completed",
            "detail": (
                "Created a fallback prompt from the topic "
                "and available research text."
            ),
        }
    )

    return data, "demo", stages
