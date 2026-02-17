"""
EdTech Digest Agent - Phase 1
Fetches articles, synthesizes weekly digest, prints to console.

Usage: python edtech_digest.py
"""

import anthropic
import requests
from datetime import datetime
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ============================================================================
# CONFIGURATION
# ============================================================================

# Article URLs for this week (you'll edit this weekly)
ARTICLE_URLS = [
    "https://marketbrief.edweek.org/product-development/as-ai-moves-quickly-lego-education-bets-on-foundations-over-fomo/2026/02",
    "https://marketbrief.edweek.org/strategy-operations/longtime-ed-tech-veteran-on-new-role-urgent-literary-needs-in-k-12/2026/01",
    "https://www.edweek.org/technology/not-meant-for-children-adults-favor-age-restrictions-on-social-media-ai/2026/02",
    "https://www.edweek.org/technology/microsoft-joins-other-companies-in-trying-to-fill-ai-training-gap-in-schools/2026/02",
    "https://www.edsurge.com/news/2026-02-06-new-report-card-grades-states-on-laws-banning-phones-in-schools",
    "https://techcrunch.com/2026/01/21/language-learning-marketplace-preplys-unicorn-status-embodies-ukrainian-resilience/",
    "https://techcrunch.com/2025/12/17/coursera-and-udemy-enter-a-merger-agreement-valued-at-around-2-5b/"
    # Add 5-8 URLs here each week
]

# Anthropic API key (set as environment variable: export ANTHROPIC_API_KEY=sk-...)
API_KEY = os.environ.get("ANTHROPIC_API_KEY")

# Email configuration
GMAIL_ADDRESS = "serenaetang@gmail.com"
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")  # Set this as environment variable
RECIPIENT_EMAIL = "serenatang@microsoft.com"

# ============================================================================
# ARTICLE FETCHING
# ============================================================================

def fetch_article(url):
    """
    Fetch article content from URL.
    
    Returns: dict with {url, title, content, error}
    
    Failure modes:
    - Network timeout
    - 404/403/paywall
    - Non-text content
    """
    try:
        print(f"Fetching: {url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; EdTechDigestBot/1.0)'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # For Phase 1, we'll just grab raw text
        # In Phase 2, we can add proper HTML parsing
        content = response.text[:5000]  # Cap at 5000 chars per article
        
        return {
            'url': url,
            'content': content,
            'error': None
        }
        
    except requests.Timeout:
        return {'url': url, 'content': None, 'error': 'Timeout'}
    except requests.HTTPError as e:
        return {'url': url, 'content': None, 'error': f'HTTP {e.response.status_code}'}
    except Exception as e:
        return {'url': url, 'content': None, 'error': str(e)}


def fetch_all_articles(urls):
    """Fetch all articles, track successes and failures."""
    articles = []
    failed = []
    
    for url in urls:
        result = fetch_article(url)
        if result['error']:
            failed.append(result)
            print(f"  ❌ Failed: {result['error']}")
        else:
            articles.append(result)
            print(f"  ✓ Success")
    
    return articles, failed


# ============================================================================
# DIGEST SYNTHESIS
# ============================================================================

def synthesize_digest(articles, failed_articles):
    """
    Use Claude to synthesize articles into a narrative digest.
    
    Failure modes:
    - API errors
    - Model refusal (shouldn't happen for news synthesis)
    - Hallucinated sources
    - Off-topic output
    """
    
    if not API_KEY:
        raise ValueError("ANTHROPIC_API_KEY not set. Run: export ANTHROPIC_API_KEY=sk-...")
    
    # Build the context from articles
    articles_text = ""
    for i, article in enumerate(articles, 1):
        articles_text += f"\n\n--- Article {i} ---\n"
        articles_text += f"URL: {article['url']}\n"
        articles_text += f"Content: {article['content']}\n"
    
    # Build the synthesis prompt
    prompt = f"""You are an expert EdTech industry analyst writing for product managers who need to understand the business landscape.

You have {len(articles)} articles from this week's EdTech news. Your job is to synthesize them into a ~500-word narrative digest.

Requirements:
- Write in an engaging, journalistic style (not bullet points)
- Identify 2-3 key themes across the articles
- Connect dots between policy, startups, and market trends
- Cite sources inline using this format: "According to EdSurge (URL), ..."
- End with one forward-looking insight or implication for PMs
- NEVER fabricate quotes or facts - only use information from the articles provided

{articles_text}

{"NOTE: " + str(len(failed_articles)) + " articles could not be fetched this week due to errors." if failed_articles else ""}

Now write the digest:"""

    print("\n📝 Synthesizing digest with Claude...")
    
    client = anthropic.Anthropic(api_key=API_KEY)
    
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1500,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    digest = message.content[0].text
    
    return digest


# ============================================================================
# QUALITY CHECKS
# ============================================================================

def check_digest_quality(digest, articles):
    """
    Run basic sanity checks on the digest.
    
    Returns: (passed: bool, issues: list)
    """
    issues = []
    
    # Check 1: Length
    word_count = len(digest.split())
    if word_count < 400 or word_count > 700:
        issues.append(f"Word count out of range: {word_count} (expected 400-700)")
    
    # Check 2: Citations present
    citation_count = digest.count('http')
    if citation_count < min(3, len(articles)):
        issues.append(f"Too few citations: {citation_count} (expected at least {min(3, len(articles))})")
    
    # Check 3: No placeholder text
    placeholders = ['[ARTICLE]', '[INSERT]', '[TODO]', 'PLACEHOLDER']
    for placeholder in placeholders:
        if placeholder.lower() in digest.lower():
            issues.append(f"Contains placeholder text: {placeholder}")
    
    passed = len(issues) == 0
    return passed, issues


def extract_key_theme(digest):
    """
    Use Claude to extract a concise key theme for the email subject line.
    
    Returns: Short theme string (e.g., "AI Policy Shifts and Funding Trends")
    """
    if not API_KEY:
        return "Weekly Update"
    
    client = anthropic.Anthropic(api_key=API_KEY)
    
    prompt = f"""Read this EdTech industry digest and extract the ONE key theme in 3-6 words for an email subject line.

Digest:
{digest}

Respond with ONLY the theme, nothing else. Examples of good themes:
- "AI Tutoring Investment Surge"
- "Policy Changes Impact K-12 Tech"
- "Consolidation in EdTech Market"

Key theme:"""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=50,
        messages=[{"role": "user", "content": prompt}]
    )
    
    theme = message.content[0].text.strip()
    return theme


# ============================================================================
# EMAIL SENDING
# ============================================================================

def send_email(digest, theme):
    """
    Send the digest via Gmail SMTP.
    
    Failure modes:
    - App password not set or incorrect
    - SMTP connection issues
    - Recipient address rejected
    """
    
    if not GMAIL_APP_PASSWORD:
        raise ValueError("GMAIL_APP_PASSWORD not set. Run: export GMAIL_APP_PASSWORD=your-app-password")
    
    print(f"\n📧 Sending email to {RECIPIENT_EMAIL}...")
    
    # Create message
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"Weekly EdTech Digest: {theme}"
    msg['From'] = GMAIL_ADDRESS
    msg['To'] = RECIPIENT_EMAIL
    msg['Date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S')
    
    # Convert digest to HTML with proper formatting
    html_digest = digest.replace('\n\n', '</p><p>').replace('\n', '<br>')
    html_body = f"""
    <html>
      <body style="font-family: Georgia, serif; font-size: 16px; line-height: 1.6; color: #333; max-width: 650px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #2c5282; border-bottom: 2px solid #2c5282; padding-bottom: 10px;">
          Weekly EdTech Digest
        </h2>
        <p style="color: #666; font-size: 14px; font-style: italic;">
          {datetime.now().strftime('%B %d, %Y')}
        </p>
        <div style="margin-top: 20px;">
          <p>{html_digest}</p>
        </div>
        <hr style="margin-top: 40px; border: none; border-top: 1px solid #ddd;">
        <p style="font-size: 12px; color: #999; text-align: center;">
          EdTech Digest Agent · Powered by Claude
        </p>
      </body>
    </html>
    """
    
    # Attach HTML body
    html_part = MIMEText(html_body, 'html')
    msg.attach(html_part)
    
    # Send via Gmail SMTP
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.send_message(msg)
        
        print(f"✓ Email sent successfully")
        return True
        
    except smtplib.SMTPAuthenticationError:
        print("❌ Authentication failed. Check your app password.")
        return False
    except Exception as e:
        print(f"❌ Email sending failed: {e}")
        return False


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 60)
    print("EdTech Digest Agent - Phase 2")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"Articles to fetch: {len(ARTICLE_URLS)}\n")
    
    # Step 1: Fetch articles
    articles, failed = fetch_all_articles(ARTICLE_URLS)
    print(f"\n✓ Fetched {len(articles)} articles successfully")
    if failed:
        print(f"✗ Failed to fetch {len(failed)} articles")
    
    # Step 2: Synthesize digest
    if len(articles) == 0:
        print("\n❌ ERROR: No articles fetched. Cannot generate digest.")
        return
    
    digest = synthesize_digest(articles, failed)
    
    # Step 3: Quality checks
    print("\n🔍 Running quality checks...")
    passed, issues = check_digest_quality(digest, articles)
    
    if not passed:
        print("⚠️  Quality issues detected:")
        for issue in issues:
            print(f"  - {issue}")
        print("\n❌ Digest failed quality checks. Not sending email.")
        print("\nDigest preview:")
        print("-" * 60)
        print(digest[:500] + "...")
        print("-" * 60)
        return
    else:
        print("✓ Quality checks passed")
    
    # Step 4: Extract theme for subject line
    print("\n📋 Extracting key theme for subject line...")
    theme = extract_key_theme(digest)
    print(f"Theme: {theme}")
    
    # Step 5: Send email
    email_sent = send_email(digest, theme)
    
    if email_sent:
        print("\n" + "=" * 60)
        print("✅ DIGEST SENT SUCCESSFULLY")
        print("=" * 60)
        print(f"Subject: Weekly EdTech Digest: {theme}")
        print(f"From: {GMAIL_ADDRESS}")
        print(f"To: {RECIPIENT_EMAIL}")
        print(f"Word count: {len(digest.split())}")
        print(f"Citations: {digest.count('http')}")
    else:
        print("\n" + "=" * 60)
        print("❌ EMAIL SENDING FAILED")
        print("=" * 60)
        print("\nDigest was generated but not sent:")
        print("-" * 60)
        print(digest)
        print("-" * 60)


if __name__ == "__main__":
    main()
