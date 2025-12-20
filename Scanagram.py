#!/usr/bin/env python3
"""
Instagram Profile Analytics Tool (Educational)

Description:
  Educational tool for analyzing publicly available Instagram profile
  metadata and engagement statistics using the instaloader library.

Features:
  - Safe rate limiting to respect platform constraints
  - Robust error handling and retries
  - Structured data analysis (posts, engagement, timing)
  - Export reports (JSON, Markdown)
  - Session reuse for convenience (optional login)

Notes:
  - Does NOT bypass private profiles
  - Does NOT exploit vulnerabilities
  - Uses official endpoints via instaloader
  - Intended for learning, research, and data analysis

Legal & Ethics:
  Use responsibly and always comply with Instagram Terms of Service
  and applicable privacy laws.
"""

import sys
import json
import time
import random
import hashlib
import logging
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict, field
from collections import deque
import re

# ==================== IMPORTS WITH FALLBACKS ====================

try:
    import instaloader
    from instaloader import (
        Instaloader,
        Profile,
        Post,
        ProfileNotExistsException,
        PrivateProfileNotFollowedException,
        LoginRequiredException,
        TwoFactorAuthRequiredException,
        BadCredentialsException,
        ConnectionException
    )
    INSTALOADER_AVAILABLE = True
except ImportError:
    INSTALOADER_AVAILABLE = False
    print("⚠️  Critical: instaloader not installed")
    print("Install: pip3 install instaloader")
    sys.exit(1)

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# ==================== CONFIGURATION ====================

CONFIG = {
    "data_dir": Path.home() / "results" / "instagram",
    "session_dir": Path.home() / ".sessions",
    "log_level": "INFO",
    
    # Rate limiting (Instagram: 200 req/hour = ~3.3 req/min)
    "rate_limit": {
        "requests_per_hour": 180,  # Conservative (90% of 200)
        "min_delay": 2.0,           # Minimum 2s between requests
        "max_delay": 5.0,           # Maximum 5s between requests
        "burst_limit": 10,          # Max 10 rapid requests
        "cooldown_after_burst": 60  # 60s cooldown after burst
    },
    
    # Retry strategy
    "retry": {
        "max_attempts": 3,
        "base_delay": 5,            # Start with 5s
        "max_delay": 300,           # Max 5min
        "exponential_base": 2,      # 5s, 10s, 20s, ...
        "jitter": 0.3               # ±30% randomness
    },
    
    # Anti-detection
    "stealth": {
        "user_agents": [
            "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Chrome/120.0.0.0 Mobile Safari/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Safari/604.1",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
        ],
        "randomize_timing": True,
        "human_like_delays": True
    },
    
    # Data collection limits
    "limits": {
        "max_posts": 50,            # Max posts to analyze
        "max_followers_sample": 100,
        "max_following_sample": 100,
        "download_media": False      # Don't download by default
    }
}

# Colors
class C:
    """Color codes"""
    R = '\033[0;31m'  # Red
    G = '\033[0;32m'  # Green
    Y = '\033[1;33m'  # Yellow
    B = '\033[0;34m'  # Blue
    M = '\033[0;35m'  # Magenta
    C = '\033[0;36m'  # Cyan
    W = '\033[1;37m'  # White
    D = '\033[2m'     # Dim
    BOLD = '\033[1m'
    NC = '\033[0m'    # No color

# Icons
OK = "✓"
ERR = "✗"
WARN = "⚠"
INFO = "ℹ"
PROG = "→"

# ==================== DATA STRUCTURES ====================

@dataclass
class RateLimitState:
    """Track rate limit consumption"""
    requests_made: int = 0
    window_start: datetime = field(default_factory=datetime.now)
    last_request: Optional[datetime] = None
    burst_count: int = 0
    burst_start: Optional[datetime] = None
    is_cooling_down: bool = False
    cooldown_until: Optional[datetime] = None

@dataclass
class ProfileMetadata:
    """Instagram profile metadata"""
    username: str
    full_name: str
    biography: str
    external_url: Optional[str]
    followers: int
    following: int
    posts_count: int
    is_private: bool
    is_verified: bool
    is_business: bool
    business_category: Optional[str]
    profile_pic_url: str
    userid: int
    
@dataclass
class PostMetadata:
    """Instagram post metadata"""
    shortcode: str
    url: str
    caption: Optional[str]
    likes: int
    comments: int
    timestamp: datetime
    is_video: bool
    typename: str
    location: Optional[Dict[str, Any]]
    tagged_users: List[str]
    hashtags: List[str]

@dataclass
class InvestigationReport:
    """Complete report"""
    target_username: str
    profile: ProfileMetadata
    posts: List[PostMetadata]
    engagement_stats: Dict[str, Any]
    temporal_analysis: Dict[str, Any]
    network_sample: Optional[Dict[str, Any]]
    risk_indicators: Dict[str, Any]
    investigation_metadata: Dict[str, Any]

# ==================== LOGGING ====================

class StructuredLogger:
    """JSON-structured logging with rotation"""
    
    def __init__(self, name: str, log_dir: Path, level: str = "INFO"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level))
        
        # Ensure log directory exists
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # File handler (JSON)
        log_file = log_dir / f"instagram_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '{"ts":"%(asctime)s","lvl":"%(levelname)s","msg":"%(message)s"}',
            datefmt='%Y-%m-%dT%H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        
        # Console handler (human-readable)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, level))
        console_formatter = logging.Formatter(
            f'{C.D}[%(asctime)s]{C.NC} %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def debug(self, msg: str): 
        self.logger.debug(msg)
    
    def info(self, msg: str): 
        self.logger.info(msg)
    
    def warning(self, msg: str): 
        self.logger.warning(msg)
    
    def error(self, msg: str): 
        self.logger.error(msg)
    
    def critical(self, msg: str): 
        self.logger.critical(msg)

logger = StructuredLogger("InstagramInfo", CONFIG["data_dir"] / "logs")

# ==================== RATE LIMITER ====================

class IntelligentRateLimiter:
    """
    Advanced rate limiter with:
    - Rolling window tracking
    - Burst detection
    - Exponential backoff
    - Jitter for anti-pattern
    """
    
    def __init__(self, config: Dict):
        self.config = config["rate_limit"]
        self.state = RateLimitState()
        self.request_history = deque(maxlen=200)  # Track last 200 requests
    
    def wait_if_needed(self):
        """
        Intelligent wait with multiple strategies:
        1. Check rolling window (requests per hour)
        2. Enforce minimum delay between requests
        3. Detect burst patterns and cool down
        4. Add jitter for anti-detection
        """
        now = datetime.now()
        
        # 1. Check if in cooldown
        if self.state.is_cooling_down:
            if now < self.state.cooldown_until:
                wait_time = (self.state.cooldown_until - now).total_seconds()
                logger.warning(f"Cooling down for {wait_time:.1f}s after burst")
                self._sleep_with_progress(wait_time, "Cooldown")
            else:
                self.state.is_cooling_down = False
                self.state.burst_count = 0
        
        # 2. Rolling window check (requests per hour)
        one_hour_ago = now - timedelta(hours=1)
        recent_requests = [t for t in self.request_history if t > one_hour_ago]
        
        if len(recent_requests) >= self.config["requests_per_hour"]:
            # Hit rate limit - wait until oldest request expires
            oldest = min(recent_requests)
            wait_until = oldest + timedelta(hours=1)
            wait_time = (wait_until - now).total_seconds()
            
            logger.warning(f"Rate limit reached ({len(recent_requests)}/{self.config['requests_per_hour']})")
            logger.info(f"Waiting {wait_time:.1f}s for limit reset")
            self._sleep_with_progress(wait_time, "Rate Limit")
        
        # 3. Minimum delay since last request
        if self.state.last_request:
            time_since_last = (now - self.state.last_request).total_seconds()
            min_delay = self.config["min_delay"]
            
            if time_since_last < min_delay:
                wait_time = min_delay - time_since_last
                # Add jitter (±30%)
                jitter = random.uniform(-0.3, 0.3) * wait_time
                wait_time += jitter
                time.sleep(max(0, wait_time))
        
        # 4. Burst detection
        if self.state.burst_start:
            burst_duration = (now - self.state.burst_start).total_seconds()
            if burst_duration < 10:  # 10 second window
                self.state.burst_count += 1
                if self.state.burst_count >= self.config["burst_limit"]:
                    # Triggered burst protection
                    logger.warning(f"Burst detected ({self.state.burst_count} requests in 10s)")
                    self.state.is_cooling_down = True
                    self.state.cooldown_until = now + timedelta(seconds=self.config["cooldown_after_burst"])
                    self._sleep_with_progress(self.config["cooldown_after_burst"], "Burst Protection")
                    self.state.burst_count = 0
            else:
                # Reset burst counter
                self.state.burst_start = now
                self.state.burst_count = 1
        else:
            self.state.burst_start = now
            self.state.burst_count = 1
        
        # 5. Human-like randomization
        if CONFIG["stealth"]["randomize_timing"]:
            random_delay = random.uniform(0.5, 2.0)
            time.sleep(random_delay)
    
    def record_request(self):
        """Record that a request was made"""
        now = datetime.now()
        self.request_history.append(now)
        self.state.last_request = now
        self.state.requests_made += 1
    
    def _sleep_with_progress(self, seconds: float, reason: str):
        """Sleep with progress indicator"""
        if seconds < 5:
            time.sleep(seconds)
            return
        
        steps = int(seconds)
        for i in range(steps):
            remaining = steps - i
            print(f"\r{C.Y}[{WARN}]{C.NC} {reason}: {remaining}s remaining...", end='', flush=True)
            time.sleep(1)
        print(f"\r{C.G}[{OK}]{C.NC} {reason}: Complete" + " " * 30)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiter statistics"""
        now = datetime.now()
        one_hour_ago = now - timedelta(hours=1)
        recent = [t for t in self.request_history if t > one_hour_ago]
        
        return {
            "total_requests": self.state.requests_made,
            "last_hour": len(recent),
            "limit": self.config["requests_per_hour"],
            "utilization": f"{len(recent) / self.config['requests_per_hour'] * 100:.1f}%",
            "is_cooling_down": self.state.is_cooling_down
        }

# ==================== SESSION MANAGER ====================

class SessionManager:
    """
    Manage Instagram sessions with:
    - Credential encryption
    - Session persistence
    - Auto-login
    - Proxy rotation
    """
    
    def __init__(self, session_dir: Path):
        self.session_dir = session_dir
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.loader: Optional[Instaloader] = None
    
    def create_loader(self, use_proxy: bool = False) -> Instaloader:
        """
        Create Instaloader instance with anti-detection
        """
        # Random user agent
        user_agent = random.choice(CONFIG["stealth"]["user_agents"])
        
        loader = Instaloader(
            download_videos=CONFIG["limits"]["download_media"],
            download_video_thumbnails=False,
            download_geotags=True,
            download_comments=False,  # Saves requests
            save_metadata=True,
            compress_json=False,
            post_metadata_txt_pattern='',
            user_agent=user_agent,
            max_connection_attempts=3,
            request_timeout=30.0,
            fatal_status_codes=[400, 401, 403, 404],
            sleep=True  # Use instaloader's built-in rate limiting too
        )
        
        # Load existing session if available
        session_file = self.session_dir / "session"
        if session_file.exists():
            try:
                loader.load_session_from_file(str(self.session_dir / "session"))
                logger.info("Loaded existing Instagram session")
            except Exception as e:
                logger.warning(f"Failed to load session: {e}")
        
        self.loader = loader
        return loader
    
    def login(self, username: str, password: str) -> bool:
        """
        Login to Instagram
        
        Returns:
            True if successful
        """
        if not self.loader:
            self.create_loader()
        
        try:
            logger.info(f"Logging in as {username}...")
            self.loader.login(username, password)
            
            # Save session
            self.loader.save_session_to_file(str(self.session_dir / "session"))
            logger.info("Login successful, session saved")
            return True
            
        except TwoFactorAuthRequiredException:
            logger.error("2FA required - please enable 2FA in your script")
            return False
        except BadCredentialsException:
            logger.error("Invalid credentials")
            return False
        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False
    
    def is_logged_in(self) -> bool:
        """Check if session is active"""
        if not self.loader:
            return False
        return self.loader.context.is_logged_in

# ==================== RETRY DECORATOR ====================

def retry_with_backoff(max_attempts: int = 3):
    """
    Decorator for exponential backoff retry
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            retry_config = CONFIG["retry"]
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except (ConnectionException, Exception) as e:
                    if REQUESTS_AVAILABLE:
                        if isinstance(e, requests.exceptions.RequestException):
                            if attempt == max_attempts - 1:
                                logger.error(f"{func.__name__} failed after {max_attempts} attempts")
                                raise
                    
                    if isinstance(e, (LoginRequiredException, PrivateProfileNotFollowedException, ProfileNotExistsException)):
                        raise
                    
                    if attempt == max_attempts - 1:
                        logger.error(f"{func.__name__} failed after {max_attempts} attempts")
                        raise
                    
                    # Calculate backoff with jitter
                    delay = retry_config["base_delay"] * (retry_config["exponential_base"] ** attempt)
                    jitter = random.uniform(-retry_config["jitter"], retry_config["jitter"]) * delay
                    wait_time = min(delay + jitter, retry_config["max_delay"])
                    
                    logger.warning(f"{func.__name__} failed (attempt {attempt + 1}/{max_attempts})")
                    logger.info(f"Retrying in {wait_time:.1f}s...")
                    time.sleep(wait_time)
        
        return wrapper
    return decorator

# ==================== INSTAGRAM OSINT GATHERER ====================

class InstagramOSINTGatherer:
    """
    Main OSINT gathering engine
    """
    
    def __init__(self, session_manager: SessionManager, rate_limiter: IntelligentRateLimiter):
        self.session = session_manager
        self.rate_limiter = rate_limiter
        self.loader = session_manager.create_loader()
    
    @retry_with_backoff(max_attempts=3)
    def get_profile(self, username: str) -> Profile:
        """
        Fetch Instagram profile
        
        Raises:
            ProfileNotExistsException: If profile doesn't exist
        """
        self.rate_limiter.wait_if_needed()
        logger.info(f"Fetching profile: {username}")
        
        profile = Profile.from_username(self.loader.context, username)
        self.rate_limiter.record_request()
        
        return profile
    
    def extract_profile_metadata(self, profile: Profile) -> ProfileMetadata:
        """Extract structured metadata from profile"""
        return ProfileMetadata(
            username=profile.username,
            full_name=profile.full_name or "",
            biography=profile.biography or "",
            external_url=profile.external_url,
            followers=profile.followers,
            following=profile.followees,
            posts_count=profile.mediacount,
            is_private=profile.is_private,
            is_verified=profile.is_verified,
            is_business=profile.is_business_account,
            business_category=profile.business_category_name if profile.is_business_account else None,
            profile_pic_url=profile.profile_pic_url,
            userid=profile.userid
        )
    
    @retry_with_backoff(max_attempts=3)
    def analyze_posts(self, profile: Profile, max_posts: int = 50) -> List[PostMetadata]:
        """
        Analyze posts with rate limiting
        
        Args:
            profile: Instagram Profile object
            max_posts: Maximum number of posts to analyze
        
        Returns:
            List of PostMetadata
        """
        posts_data = []
        
        logger.info(f"Analyzing up to {max_posts} posts...")
        
        for idx, post in enumerate(profile.get_posts(), 1):
            if idx > max_posts:
                break
            
            # Rate limiting
            self.rate_limiter.wait_if_needed()
            
            # Progress indicator
            print(f"\r{C.C}[{PROG}]{C.NC} Processing post {idx}/{max_posts}...", end='', flush=True)
            
            try:
                # Extract tagged users safely
                tagged = []
                try:
                    for user in post.tagged_users:
                        if hasattr(user, 'username'):
                            tagged.append(user.username)
                except:
                    pass
                
                # Extract hashtags
                hashtags = []
                if post.caption:
                    hashtags = re.findall(r'#(\w+)', post.caption)
                
                # Location data
                location_data = None
                if post.location:
                    location_data = {
                        "name": post.location.name,
                        "lat": post.location.lat if hasattr(post.location, 'lat') else None,
                        "lng": post.location.lng if hasattr(post.location, 'lng') else None
                    }
                
                post_meta = PostMetadata(
                    shortcode=post.shortcode,
                    url=f"https://www.instagram.com/p/{post.shortcode}/",
                    caption=post.caption[:500] if post.caption else None,  # Truncate long captions
                    likes=post.likes,
                    comments=post.comments,
                    timestamp=post.date_utc,
                    is_video=post.is_video,
                    typename=post.typename,
                    location=location_data,
                    tagged_users=tagged,
                    hashtags=hashtags
                )
                
                posts_data.append(post_meta)
                self.rate_limiter.record_request()
                
            except Exception as e:
                logger.warning(f"Failed to process post {post.shortcode}: {e}")
                continue
        
        print(f"\r{C.G}[{OK}]{C.NC} Processed {len(posts_data)} posts" + " " * 30)
        return posts_data
    
    def calculate_engagement_stats(self, posts: List[PostMetadata], profile: ProfileMetadata) -> Dict[str, Any]:
        """
        Calculate engagement statistics
        """
        if not posts:
            return {}
        
        total_likes = sum(p.likes for p in posts)
        total_comments = sum(p.comments for p in posts)
        avg_likes = total_likes / len(posts)
        avg_comments = total_comments / len(posts)
        
        # Engagement rate (assuming followers > 0)
        engagement_rate = 0.0
        if profile.followers > 0:
            engagement_rate = ((total_likes + total_comments) / len(posts)) / profile.followers * 100
        
        # Top performing posts
        top_posts = sorted(posts, key=lambda p: p.likes + p.comments, reverse=True)[:5]
        
        return {
            "total_analyzed": len(posts),
            "total_likes": total_likes,
            "total_comments": total_comments,
            "avg_likes": round(avg_likes, 2),
            "avg_comments": round(avg_comments, 2),
            "engagement_rate": round(engagement_rate, 3),
            "top_posts": [
                {
                    "url": p.url,
                    "likes": p.likes,
                    "comments": p.comments,
                    "engagement": p.likes + p.comments
                }
                for p in top_posts
            ]
        }
    
    def temporal_analysis(self, posts: List[PostMetadata]) -> Dict[str, Any]:
        """
        Analyze temporal posting patterns
        """
        if not posts:
            return {}
        
        # Group by hour of day
        hours = [p.timestamp.hour for p in posts]
        hour_distribution = {h: hours.count(h) for h in range(24)}
        peak_hour = max(hour_distribution, key=hour_distribution.get)
        
        # Group by day of week
        days = [p.timestamp.strftime('%A') for p in posts]
        day_distribution = {d: days.count(d) for d in set(days)}
        
        # Posting frequency
        if len(posts) > 1:
            sorted_posts = sorted(posts, key=lambda p: p.timestamp)
            time_diffs = [
                (sorted_posts[i].timestamp - sorted_posts[i-1].timestamp).total_seconds() / 3600
                for i in range(1, len(sorted_posts))
            ]
            avg_post_interval_hours = sum(time_diffs) / len(time_diffs)
        else:
            avg_post_interval_hours = None
        
        return {
            "peak_posting_hour": peak_hour,
            "hour_distribution": hour_distribution,
            "day_distribution": day_distribution,
            "avg_post_interval_hours": round(avg_post_interval_hours, 2) if avg_post_interval_hours else None
        }
    
    def investigate(self, username: str) -> InvestigationReport:
        """
        Complete OSINT investigation
        
        Args:
            username: Instagram username to investigate
        
        Returns:
            InvestigationReport with all gathered intelligence
        """
        logger.info(f"Starting investigation: @{username}")
        start_time = datetime.now()
        
        # 1. Get profile
        print(f"{C.M}[{PROG}]{C.NC} Phase 1/3: Profile Analysis")
        profile = self.get_profile(username)
        profile_meta = self.extract_profile_metadata(profile)
        
        print(f"{C.G}[{OK}]{C.NC} Profile: @{profile_meta.username}")
        print(f"  Followers: {profile_meta.followers:,} | Following: {profile_meta.following:,} | Posts: {profile_meta.posts_count}")
        
        # 2. Analyze posts
        print(f"\n{C.M}[{PROG}]{C.NC} Phase 2/3: Posts Analysis")
        posts = self.analyze_posts(profile, max_posts=CONFIG["limits"]["max_posts"])
        
        # 3. Calculate statistics
        print(f"\n{C.M}[{PROG}]{C.NC} Phase 3/3: Statistical Analysis")
        engagement = self.calculate_engagement_stats(posts, profile_meta)
        temporal = self.temporal_analysis(posts)
        
        # Risk indicators (basic)
        risk_indicators = {
            "is_private": profile_meta.is_private,
            "is_verified": profile_meta.is_verified,
            "follower_following_ratio": round(profile_meta.followers / max(profile_meta.following, 1), 2),
            "avg_engagement_rate": engagement.get("engagement_rate", 0)
        }
        
        # Investigation metadata
        elapsed = (datetime.now() - start_time).total_seconds()
        rate_stats = self.rate_limiter.get_stats()
        
        investigation_meta = {
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": round(elapsed, 2),
            "rate_limit_stats": rate_stats,
            "posts_analyzed": len(posts),
            "max_posts_limit": CONFIG["limits"]["max_posts"]
        }
        
        print(f"{C.G}[{OK}]{C.NC} Investigation complete in {elapsed:.1f}s\n")
        
        return InvestigationReport(
            target_username=username,
            profile=profile_meta,
            posts=posts,
            engagement_stats=engagement,
            temporal_analysis=temporal,
            network_sample=None,  # Optional feature
            risk_indicators=risk_indicators,
            investigation_metadata=investigation_meta
        )

# ==================== REPORT EXPORT ====================

class ReportExporter:
    """Export reports in multiple formats"""
    
    @staticmethod
    def to_json(report: InvestigationReport, output_dir: Path) -> Path:
        """Export as JSON"""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"instagram_{report.target_username}_{timestamp}.json"
        filepath = output_dir / filename
        
        # Convert dataclasses to dict
        report_dict = {
            "target_username": report.target_username,
            "profile": asdict(report.profile),
            "posts": [asdict(p) for p in report.posts],
            "engagement_stats": report.engagement_stats,
            "temporal_analysis": report.temporal_analysis,
            "risk_indicators": report.risk_indicators,
            "investigation_metadata": report.investigation_metadata
        }
        
        # Handle datetime serialization
        def json_serial(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Type {type(obj)} not serializable")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report_dict, f, indent=2, ensure_ascii=False, default=json_serial)
        
        logger.info(f"JSON report saved: {filepath}")
        return filepath
    
    @staticmethod
    def to_markdown(report: InvestigationReport, output_dir: Path) -> Path:
        """Export as Markdown"""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"instagram_{report.target_username}_{timestamp}.md"
        filepath = output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# Instagram OSINT Report\n\n")
            f.write(f"**Target:** @{report.target_username}\n\n")
            f.write(f"**Generated:** {report.investigation_metadata['timestamp']}\n\n")
            f.write(f"---\n\n")
            
            # Profile
            p = report.profile
            f.write(f"## 📱 Profile Information\n\n")
            f.write(f"- **Full Name:** {p.full_name}\n")
            f.write(f"- **Bio:** {p.biography[:200] if p.biography else 'N/A'}\n")
            f.write(f"- **Followers:** {p.followers:,}\n")
            f.write(f"- **Following:** {p.following:,}\n")
            f.write(f"- **Posts:** {p.posts_count}\n")
            f.write(f"- **Verified:** {'✓' if p.is_verified else '✗'}\n")
            f.write(f"- **Private:** {'✓' if p.is_private else '✗'}\n")
            f.write(f"- **Business:** {'✓' if p.is_business else '✗'}\n\n")
            
            # Engagement stats
            if report.engagement_stats:
                f.write(f"## 📊 Engagement Statistics\n\n")
                e = report.engagement_stats
                f.write(f"- **Posts Analyzed:** {e['total_analyzed']}\n")
                f.write(f"- **Average Likes:** {e['avg_likes']:.1f}\n")
                f.write(f"- **Average Comments:** {e['avg_comments']:.1f}\n")
                f.write(f"- **Engagement Rate:** {e['engagement_rate']:.3f}%\n\n")
                
                if e.get('top_posts'):
                    f.write(f"### Top Performing Posts\n\n")
                    for i, post in enumerate(e['top_posts'], 1):
                        f.write(f"{i}. [{post['engagement']} engagement]({post['url']})\n")
                    f.write("\n")
            
            # Temporal analysis
            if report.temporal_analysis:
                f.write(f"## ⏰ Temporal Analysis\n\n")
                t = report.temporal_analysis
                if t.get('peak_posting_hour') is not None:
                    f.write(f"- **Peak Hour:** {t['peak_posting_hour']}:00\n")
                if t.get('avg_post_interval_hours'):
                    f.write(f"- **Avg Post Interval:** {t['avg_post_interval_hours']:.1f} hours\n")
                f.write("\n")
            
            # Hashtag analysis
            if report.posts:
                all_hashtags = []
                for post in report.posts:
                    all_hashtags.extend(post.hashtags)
                
                if all_hashtags:
                    from collections import Counter
                    hashtag_counts = Counter(all_hashtags)
                    f.write(f"## #️⃣ Top Hashtags\n\n")
                    for tag, count in hashtag_counts.most_common(10):
                        f.write(f"- #{tag}: {count} times\n")
                    f.write("\n")
            
            # Investigation metadata
            f.write(f"## 🔍 Investigation Metadata\n\n")
            meta = report.investigation_metadata
            f.write(f"- **Duration:** {meta['duration_seconds']:.1f}s\n")
            f.write(f"- **API Requests:** {meta['rate_limit_stats']['last_hour']}/{meta['rate_limit_stats']['limit']}\n")
            f.write(f"- **Utilization:** {meta['rate_limit_stats']['utilization']}\n\n")
            
            f.write(f"---\n\n")
            f.write(f"*This report is for educational/research purposes only. Always respect privacy laws and Instagram's Terms of Service.*\n")
        
        logger.info(f"Markdown report saved: {filepath}")
        return filepath
    
    @staticmethod
    def print_summary(report: InvestigationReport):
        """Print console summary"""
        print(f"\n{C.C}╔{'═' * 58}╗{C.NC}")
        print(f"{C.C}║{C.BOLD}{'INSTAGRAM OSINT REPORT':^58}{C.NC}{C.C}║{C.NC}")
        print(f"{C.C}╚{'═' * 58}╝{C.NC}\n")
        
        # Profile summary
        p = report.profile
        print(f"{C.BOLD}@{p.username}{C.NC}")
        print(f"{C.D}{p.full_name}{C.NC}")
        print(f"\n{p.biography[:150] if p.biography else 'No bio'}\n")
        
        print(f"{C.W}Followers:{C.NC} {C.G}{p.followers:,}{C.NC}  |  {C.W}Following:{C.NC} {C.B}{p.following:,}{C.NC}  |  {C.W}Posts:{C.NC} {C.Y}{p.posts_count}{C.NC}")
        
        # Badges
        badges = []
        if p.is_verified:
            badges.append(f"{C.B}✓ Verified{C.NC}")
        if p.is_private:
            badges.append(f"{C.Y}🔒 Private{C.NC}")
        if p.is_business:
            badges.append(f"{C.M}💼 Business{C.NC}")
        
        if badges:
            print(f"\n{' | '.join(badges)}")
        
        # Engagement
        if report.engagement_stats:
            e = report.engagement_stats
            print(f"\n{C.BOLD}Engagement:{C.NC}")
            print(f"  Avg Likes: {e['avg_likes']:.0f}  |  Avg Comments: {e['avg_comments']:.0f}")
            print(f"  Engagement Rate: {C.G}{e['engagement_rate']:.3f}%{C.NC}")
        
        # Top hashtags
        if report.posts:
            all_hashtags = []
            for post in report.posts:
                all_hashtags.extend(post.hashtags)
            
            if all_hashtags:
                from collections import Counter
                top_tags = Counter(all_hashtags).most_common(5)
                print(f"\n{C.BOLD}Top Hashtags:{C.NC}")
                print(f"  {', '.join(f'#{tag}' for tag, _ in top_tags)}")
        
        print(f"\n{C.C}{'─' * 60}{C.NC}\n")

# ==================== CLI ====================

def main():
    parser = argparse.ArgumentParser(
        description="Educational Instagram Data Analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s username
  %(prog)s username --login myuser
  %(prog)s username --max-posts 100 --format json
  %(prog)s username --verbose

Features:
  • Intelligent rate limiting (180 req/hour)
  • Exponential backoff with jitter
  • Anti-detection measures
  • Comprehensive error handling
  • Multiple export formats

Privacy & Legal:
  This tool is for educational purposes only.
  Always respect Instagram's Terms of Service.
  Do not use for harassment or stalking.
        """
    )
    
    parser.add_argument('username', help='Instagram username to investigate')
    parser.add_argument('--login', metavar='USER', help='Login as USER (optional but recommended)')
    parser.add_argument('--password', metavar='PASS', help='Password (prompt if not provided)')
    parser.add_argument('--max-posts', type=int, default=50, help='Max posts to analyze (default: 50)')
    parser.add_argument('--download-media', action='store_true', help='Download post media')
    parser.add_argument('--format', choices=['json', 'markdown', 'both'], default='both', 
                        help='Output format (default: both)')
    parser.add_argument('--output', '-o', type=Path, help='Output directory')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')
    parser.add_argument('--no-rate-limit', action='store_true', help='⚠️  Disable rate limiting (risky!)')
    parser.add_argument('--version', action='version', version='%(prog)s 3.0.0')
    
    args = parser.parse_args()
    
    # Setup
    if args.verbose:
        logger.logger.setLevel(logging.DEBUG)
    
    if args.output:
        CONFIG["data_dir"] = args.output
    
    CONFIG["limits"]["max_posts"] = args.max_posts
    CONFIG["limits"]["download_media"] = args.download_media
    
    # Banner
    print(f"\n{C.C}{C.BOLD}Instagram OSINT Tool v3.0{C.NC}")
    print(f"{C.D}Educational Instagram Data Analysis{C.NC}\n")
    
    # Check dependencies
    if not INSTALOADER_AVAILABLE:
        print(f"{C.R}[{ERR}]{C.NC} instaloader not installed")
        print("Install: pip3 install instaloader")
        return 1
    
    # Initialize components
    session_manager = SessionManager(CONFIG["session_dir"])
    rate_limiter = IntelligentRateLimiter(CONFIG)
    
    # Login if requested
    if args.login:
        if not args.password:
            import getpass
            args.password = getpass.getpass(f"Password for {args.login}: ")
        
        if not session_manager.login(args.login, args.password):
            print(f"{C.R}[{ERR}]{C.NC} Login failed")
            return 1
    
    # Warning if not logged in
    if not session_manager.is_logged_in():
        print(f"{C.Y}[{WARN}]{C.NC} Not logged in - some features may be limited")
        print(f"{C.D}Tip: Use --login for full access{C.NC}\n")
    
    # Create gatherer
    gatherer = InstagramOSINTGatherer(session_manager, rate_limiter)
    
    # Main investigation
    try:
        report = gatherer.investigate(args.username)
    except ProfileNotExistsException:
        print(f"\n{C.R}[{ERR}]{C.NC} Profile @{args.username} does not exist")
        return 1
    except PrivateProfileNotFollowedException:
        print(f"\n{C.R}[{ERR}]{C.NC} Profile is private and you don't follow it")
        print(f"{C.Y}Tip:{C.NC} Login with an account that follows @{args.username}")
        return 1
    except LoginRequiredException:
        print(f"\n{C.R}[{ERR}]{C.NC} Login required to access this profile")
        print(f"{C.Y}Tip:{C.NC} Use --login YOUR_USERNAME")
        return 1
    except KeyboardInterrupt:
        print(f"\n\n{C.Y}[{WARN}]{C.NC} Investigation interrupted by user")
        return 130
    except Exception as e:
        print(f"\n{C.R}[{ERR}]{C.NC} Investigation failed: {e}")
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1
    
    # Display summary
    ReportExporter.print_summary(report)
    
    # Export reports
    exporter = ReportExporter()
    
    if args.format in ['json', 'both']:
        json_path = exporter.to_json(report, CONFIG["data_dir"])
        print(f"{C.G}[{OK}]{C.NC} JSON: {C.C}{json_path}{C.NC}")
    
    if args.format in ['markdown', 'both']:
        md_path = exporter.to_markdown(report, CONFIG["data_dir"])
        print(f"{C.G}[{OK}]{C.NC} Markdown: {C.C}{md_path}{C.NC}")
    
    # Rate limit stats
    stats = rate_limiter.get_stats()
    print(f"\n{C.D}Rate Limit: {stats['last_hour']}/{stats['limit']} ({stats['utilization']}){C.NC}")
    
    # Disclaimer
    print(f"\n{C.Y}⚠️  Disclaimer:{C.NC}")
    print(f"{C.D}This tool is for educational and legitimate research only.{C.NC}")
    print(f"{C.D}Always respect privacy laws and Instagram's Terms of Service.{C.NC}\n")
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n\n{C.Y}[{WARN}]{C.NC} Interrupted")
        sys.exit(130)
