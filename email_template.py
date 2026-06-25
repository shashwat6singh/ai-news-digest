"""
Email template renderer — produces clean HTML email for the daily digest.
"""

from datetime import datetime, timezone
from fetch_news import NewsItem


EMAIL_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI Policy Digest</title>
<style>
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: #f5f4f0;
    margin: 0;
    padding: 20px;
    color: #1a1a1a;
  }}
  .container {{
    max-width: 620px;
    margin: 0 auto;
    background: #ffffff;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  }}
  .header {{
    background: #1a1a2e;
    padding: 28px 32px;
  }}
  .header h1 {{
    color: #ffffff;
    font-size: 20px;
    font-weight: 500;
    margin: 0 0 4px;
    letter-spacing: -0.3px;
  }}
  .header p {{
    color: #8888aa;
    font-size: 13px;
    margin: 0;
  }}
  .content {{
    padding: 24px 32px;
  }}
  .story {{
    border-left: 3px solid #e8e4dd;
    padding: 16px 0 16px 20px;
    margin-bottom: 24px;
  }}
  .story:last-child {{
    margin-bottom: 0;
  }}
  .story-num {{
    font-size: 11px;
    font-weight: 600;
    color: #8888aa;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin: 0 0 8px;
  }}
  .story h2 {{
    font-size: 16px;
    font-weight: 500;
    margin: 0 0 8px;
    line-height: 1.4;
    color: #1a1a1a;
  }}
  .story h2 a {{
    color: #1a1a1a;
    text-decoration: none;
  }}
  .story h2 a:hover {{
    text-decoration: underline;
  }}
  .story p {{
    font-size: 14px;
    color: #555;
    line-height: 1.6;
    margin: 0 0 10px;
  }}
  .meta {{
    display: flex;
    gap: 12px;
    align-items: center;
    font-size: 12px;
    color: #999;
  }}
  .source-badge {{
    background: #f0ede8;
    color: #555;
    padding: 2px 8px;
    border-radius: 4px;
    font-weight: 500;
  }}
  .read-link {{
    color: #4a90d9;
    text-decoration: none;
    font-weight: 500;
  }}
  .why-box {{
    background: #f7f6f2;
    border-radius: 8px;
    padding: 14px 16px;
    margin-top: 10px;
    font-size: 13px;
    color: #444;
    line-height: 1.5;
  }}
  .why-label {{
    font-weight: 600;
    color: #888;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.06em;
  }}
  .divider {{
    border: none;
    border-top: 1px solid #f0ede8;
    margin: 24px 0;
  }}
  .footer {{
    background: #f7f6f2;
    padding: 20px 32px;
    border-top: 1px solid #e8e4dd;
  }}
  .footer p {{
    font-size: 12px;
    color: #aaa;
    margin: 0;
    line-height: 1.6;
  }}
  .footer a {{
    color: #888;
  }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>AI Policy Digest</h1>
    <p>{date_str} &nbsp;·&nbsp; Top 3 stories for your HKS prep</p>
  </div>
  <div class="content">
    {stories_html}
  </div>
  <div class="footer">
    <p>
      Curated from: Tech Policy Press · CSIS · Brookings · RAND · MIT Tech Review · Stanford HAI · EU Digital Strategy · The Verge · Wired<br>
      <a href="https://github.com/{github_user}/ai-news-digest">View on GitHub</a> &nbsp;·&nbsp;
      Automated digest for HKS MPP prep
    </p>
  </div>
</div>
</body>
</html>
"""

WHY_IT_MATTERS = [
    "Directly relevant to tech policy and AI governance — core HKS focus areas.",
    "Key development in the US regulatory landscape — watch for HKS faculty reactions.",
    "International AI governance angle — EU–US divergence is a live policy debate.",
    "National security × AI intersection — a growing area in public policy research.",
    "Platform governance and algorithmic accountability — foundational HKS topics.",
]


def render_story(item: NewsItem, index: int) -> str:
    ordinals = ["#1", "#2", "#3"]
    label = ordinals[index] if index < 3 else f"#{index+1}"

    pub_str = item.published.strftime("%b %d, %Y")
    summary_short = item.summary[:280] + ("…" if len(item.summary) > 280 else "")

    why = WHY_IT_MATTERS[index % len(WHY_IT_MATTERS)]

    return f"""
    <div class="story">
      <p class="story-num">Story {label}</p>
      <h2><a href="{item.url}" target="_blank">{item.title}</a></h2>
      <p>{summary_short}</p>
      <div class="why-box">
        <span class="why-label">Why it matters for HKS</span><br>
        {why}
      </div>
      <div class="meta" style="margin-top:12px;">
        <span class="source-badge">{item.source}</span>
        <span>{pub_str}</span>
        <a class="read-link" href="{item.url}" target="_blank">Read →</a>
      </div>
    </div>
    """


def build_email(stories: list[NewsItem], github_user: str = "your-username") -> tuple[str, str]:
    """Returns (subject_line, html_body)."""
    date_str = datetime.now(timezone.utc).strftime("%A, %B %-d")  # e.g. "Thursday, June 25"

    stories_html = "<hr class='divider'>".join(
        render_story(item, i) for i, item in enumerate(stories)
    )

    html_body = EMAIL_TEMPLATE.format(
        date_str=date_str,
        stories_html=stories_html,
        github_user=github_user,
    )

    # Plain text subject with top headline
    subject = f"AI Policy Digest · {date_str} · {stories[0].title[:60]}…" if stories else f"AI Policy Digest · {date_str}"

    return subject, html_body
