# Instagram OSINT Analytics Tool

<div align="center">

![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-educational-orange.svg)

**Educational tool for analyzing publicly available Instagram profile metadata and engagement statistics**

[Features](#features) • [Installation](#installation) • [Usage](#usage) • [Legal](#legal-disclaimer) • [Contributing](#contributing)

</div>

---

## ⚠️ IMPORTANT DISCLAIMER

**THIS TOOL IS STRICTLY FOR EDUCATIONAL AND RESEARCH PURPOSES ONLY.**

This project was created to:
- ✅ **Teach** OSINT (Open Source Intelligence) methodologies
- ✅ **Demonstrate** proper API usage and rate limiting
- ✅ **Educate** about data privacy and digital footprints
- ✅ **Practice** Python development and cybersecurity concepts

This tool is **NOT** intended for:
- ❌ Stalking, harassment, or any form of abuse
- ❌ Violating Instagram's Terms of Service
- ❌ Unauthorized data collection or surveillance
- ❌ Any illegal or unethical activities

**By using this tool you agree to use it responsibly and in compliance with all applicable laws and Instagram's Terms of Service.**

---

## 🎓 Educational Purpose

This tool demonstrates:

1. **Ethical OSINT**: How to gather publicly available information responsibly
2. **Rate Limiting**: Implementing intelligent request throttling to respect platform limits
3. **Error Handling**: Robust retry mechanisms with exponential backoff
4. **Data Analysis**: Statistical analysis of engagement metrics and temporal patterns
5. **Clean Code**: Professional Python development practices

### What Makes This Educational?

- **Transparent**: All code is open source and well-documented
- **Respectful**: Built-in rate limiting prevents API abuse
- **Limited**: Only analyzes publicly available information
- **Compliant**: Uses official APIs through `instaloader` library
- **Safe**: No exploitation, no vulnerability abuse, no bypassing of security

---

## 📋 Features

### Core Functionality
- 📊 **Profile Analysis**: Extract public metadata (followers, following, bio, etc.)
- 📈 **Engagement Metrics**: Calculate average likes, comments, engagement rate
- ⏰ **Temporal Analysis**: Identify posting patterns and peak activity times
- 🏷️ **Hashtag Analysis**: Track most frequently used hashtags
- 📍 **Location Tracking**: Analyze geotagged post locations
- 👥 **Network Analysis**: Sample follower/following relationships (optional)

### Advanced Features
- 🚦 **Intelligent Rate Limiting**: Respects Instagram's API limits (180 req/hour)
- 🔄 **Exponential Backoff**: Automatic retry with jitter for failed requests
- 🛡️ **Request Pattern Management**: Human-like timing to demonstrate realistic data access patterns
- 💾 **Session Management**: Persistent login sessions
- 📄 **Multiple Export Formats**: JSON and Markdown reports
- 📊 **Detailed Logging**: Structured JSON logs for analysis

---

## 🚀 Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### For Termux (Android)

```bash
# Update packages
pkg update && pkg upgrade

# Install Python
pkg install python

# Clone repository
git clone https://github.com/JohnP4p/Scanagram.git
cd Scanagram

# Install dependencies
pip install -r requirements.txt
```

### For Linux/macOS/Windows

```bash
# Clone repository
git clone https://github.com/JohnP4p/Scanagram.git
cd Scanagram

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

## 📖 Usage

### Basic Usage

```bash
# Analyze a public profile (no login required)
python Scanagram.py username

# Login for extended access (recommended)
python Scanagram.py username --login your_account

# Analyze more posts
python Scanagram.py username --max-posts 100

# Export only JSON
python Scanagram.py username --format json

# Verbose output
python Scanagram.py username --verbose
```

### Advanced Usage

```bash
# Full analysis with custom output directory
python Scanagram.py username \
    --login your_account \
    --max-posts 200 \
    --format both \
    --output ~/reports \
    --verbose

# Download media files (use responsibly)
python Scanagram.py username --download-media
```

### Command Line Options

```
positional arguments:
  username              Instagram username to investigate

optional arguments:
  -h, --help           Show this help message and exit
  --login USER         Login as USER (optional but recommended)
  --password PASS      Password (will prompt if not provided)
  --max-posts N        Max posts to analyze (default: 50)
  --download-media     Download post media files
  --format {json,markdown,both}
                       Output format (default: both)
  -o, --output DIR     Custom output directory
  -v, --verbose        Verbose logging
  --version            Show version and exit
```

---

## 📊 Output Examples

### Console Summary

```
╔══════════════════════════════════════════════════════════╗
║              INSTAGRAM OSINT REPORT                      ║
╚══════════════════════════════════════════════════════════╝

@example_user
John Doe

Photographer & traveler 🌍 | Based in NYC

Followers: 15,234  |  Following: 892  |  Posts: 247

✓ Verified | 💼 Business

Engagement:
  Avg Likes: 1,234  |  Avg Comments: 89
  Engagement Rate: 8.234%

Top Hashtags:
  #photography, #travel, #nature, #landscape, #adventure
```

### JSON Report Structure

```json
{
  "target_username": "example_user",
  "profile": {
    "username": "example_user",
    "full_name": "John Doe",
    "followers": 15234,
    "following": 892,
    "posts_count": 247,
    "is_verified": true,
    "is_business": true
  },
  "engagement_stats": {
    "avg_likes": 1234.5,
    "avg_comments": 89.2,
    "engagement_rate": 8.234
  },
  "temporal_analysis": {
    "peak_posting_hour": 18,
    "avg_post_interval_hours": 48.5
  }
}
```

---

## 🛡️ Security & Privacy

### What This Tool Does NOT Do

- ❌ **Does NOT bypass private profiles** - respects privacy settings
- ❌ **Does NOT exploit vulnerabilities** - uses only official APIs
- ❌ **Does NOT crack passwords** - no brute force or credential theft
- ❌ **Does NOT enable stalking** - limited to public information
- ❌ **Does NOT violate rate limits** - intelligent throttling built-in

### Rate Limiting

The tool implements multiple layers of protection:

- **Rolling Window**: Maximum 180 requests per hour (90% of Instagram's 200/hour limit)
- **Minimum Delay**: 2 seconds between requests
- **Burst Protection**: Automatic cooldown after 10 rapid requests
- **Exponential Backoff**: Smart retry with jitter on failures

### Data Privacy

- All data is stored **locally** on your device
- **No telemetry** or external data transmission
- Session files stored in `~/.sessions/` (secure with proper permissions)
- Generated reports saved in `~/results/instagram/`

---

## ⚖️ Legal Disclaimer

### Terms of Use

1. **Compliance Required**: You must comply with Instagram's Terms of Service
2. **Legal Use Only**: Only use for lawful purposes in your jurisdiction
3. **No Liability**: The authors assume no responsibility for misuse
4. **Educational Intent**: This tool is provided for learning purposes
5. **Ethical Usage**: Always respect privacy and obtain proper authorization

### What Is Allowed

✅ Analyzing your own profile for self-assessment  
✅ Research projects with proper ethical approval  
✅ Learning about OSINT methodologies  
✅ Security research (with authorization)  
✅ Marketing analysis of public business accounts  

### What Is NOT Allowed

❌ Stalking, harassment, or intimidation  
❌ Unauthorized surveillance  
❌ Violating Instagram's Terms of Service  
❌ Commercial use without proper authorization  
❌ Data scraping for spam or malicious purposes  

### Legal Notice

```
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

**By using this tool, you acknowledge that:**
- You have read and understood this disclaimer
- You will use the tool responsibly and ethically
- You will comply with all applicable laws and regulations
- You accept full responsibility for your actions

---

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

### Code of Conduct

- Be respectful and professional
- Focus on educational improvements
- Do not submit features that enable abuse
- Maintain ethical standards

### How to Contribute

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/improvement`)
3. Commit your changes (`git commit -am 'Add educational feature'`)
4. Push to the branch (`git push origin feature/improvement`)
5. Open a Pull Request

### Contribution Ideas

- Improve documentation
- Add more statistical analysis features
- Enhance error handling
- Optimize rate limiting algorithms
- Add unit tests
- Improve visualization of results

---

## 📚 Learning Resources

Want to learn more about OSINT and ethical hacking?

### Recommended Reading
- [OSINT Framework](https://osintframework.com/)
- [The Art of Social Engineering](https://www.social-engineer.org/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)

### Related Tools (Educational)
- [Sherlock](https://github.com/sherlock-project/sherlock) - Username OSINT
- [theHarvester](https://github.com/laramies/theHarvester) - Email/domain OSINT
- [Maltego](https://www.maltego.com/) - Link analysis

### Online Courses
- [Cybersecurity Fundamentals (Coursera)](https://www.coursera.org/learn/cyber-security-domain)
- [Introduction to OSINT (SANS)](https://www.sans.org/cyber-security-courses/open-source-intelligence-gathering/)

---

## 🐛 Troubleshooting

### Common Issues

**Issue**: `instaloader not installed`  
**Solution**: Run `pip install instaloader`

**Issue**: `Rate limit reached`  
**Solution**: Wait for the cooldown period (tool handles this automatically)

**Issue**: `Login required`  
**Solution**: Use `--login your_username` for extended access

**Issue**: `Profile is private`  
**Solution**: You must follow the profile with your logged-in account

**Issue**: `Two-factor authentication required`  
**Solution**: Currently 2FA is not fully supported; use an account without 2FA

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### MIT License Summary

- ✅ Commercial use allowed (with ethical constraints)
- ✅ Modification allowed
- ✅ Distribution allowed
- ✅ Private use allowed
- ⚠️ No warranty provided
- ⚠️ Author not liable for misuse

---

## 👨‍💻 Author

Created for educational purposes by JohnP4p

### Contact

- GitHub: @JohnP4p(https://github.com/JohnP4p)
- Email: decipher_busboy680@aleeas.com (security issues only)

**Note**: I do not provide support for illegal or unethical use of this tool.

---

## 🙏 Acknowledgments

- [instaloader](https://instaloader.github.io/) - The core library that makes this possible
- The OSINT community for promoting ethical intelligence gathering
- All contributors who help improve this educational resource

---

## ⭐ Star This Repository

If you found this educational tool helpful for learning about OSINT and Python development, please consider starring the repository!

---

<div align="center">

**Remember: With great power comes great responsibility.**

Use this tool wisely, ethically, and legally.

*Last updated: 2025*

</div>
