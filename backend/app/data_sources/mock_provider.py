import random
import math
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any

from backend.app.data_sources.base import BaseDataSourceProvider, ReelRawData

# Curated high quality creators per category
CREATORS_DATA = {
    "Niche": [
        {
            "username": "tech_radar_daily",
            "name": "Tech Radar Daily",
            "verified": True,
            "followers": 1420000,
            "bio": "Latest viral tech, new websites, breakthrough apps & futuristic devices 🚀📱",
            "pic": "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150&h=150&fit=crop"
        },
        {
            "username": "app_finder_pro",
            "name": "Alex | App & Web Tools",
            "verified": True,
            "followers": 890000,
            "bio": "Finding secret web apps & mobile apps that feel illegal to know ⚡💻",
            "pic": "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150&h=150&fit=crop"
        },
        {
            "username": "gadget_velocity",
            "name": "Marcus Vance Tech",
            "verified": False,
            "followers": 430000,
            "bio": "Insane new hardware, crazy gadgets, and viral tech tests on Instagram 🎧🔥",
            "pic": "https://images.unsplash.com/photo-1570295999919-56ceb5ecca61?w=150&h=150&fit=crop"
        },
        {
            "username": "devtools_spotlight",
            "name": "DevTools & Web Apps",
            "verified": True,
            "followers": 670000,
            "bio": "Spotlighting the hottest new developer tools, frameworks & web apps daily 🛠️✨",
            "pic": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&h=150&fit=crop"
        },
        {
            "username": "mobile_future_lab",
            "name": "Kavya Tech Studio",
            "verified": False,
            "followers": 315000,
            "bio": "Hidden iOS & Android app gems, gestures, and OS updates before anyone else 📲",
            "pic": "https://images.unsplash.com/photo-1580489944761-15a19d654956?w=150&h=150&fit=crop"
        }
    ],
    "AI": [
        {
            "username": "prompt_master_ai",
            "name": "PromptMaster Studio",
            "verified": True,
            "followers": 1650000,
            "bio": "Secret photo-to-prompt tricks, Midjourney, Flux & Sora masterclasses 🤖🎨",
            "pic": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=150&h=150&fit=crop"
        },
        {
            "username": "crazy_ai_tools",
            "name": "Insane AI Websites",
            "verified": True,
            "followers": 1980000,
            "bio": "Testing mind-blowing AI websites and crazy new AI models that just dropped 🤯⚡",
            "pic": "https://images.unsplash.com/photo-1634017839464-5c339ebe3cb4?w=150&h=150&fit=crop"
        },
        {
            "username": "creative_ai_lab",
            "name": "Elena AI Vision",
            "verified": False,
            "followers": 540000,
            "bio": "Crazy AI video generation, talking avatars & photo transformations 📸✨",
            "pic": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&h=150&fit=crop"
        },
        {
            "username": "ai_breakthroughs",
            "name": "Dr. Ryan Vance | AI",
            "verified": True,
            "followers": 820000,
            "bio": "Evaluating new LLMs, autonomous coding agents & next-gen AI benchmarks 🔬💻",
            "pic": "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150&h=150&fit=crop"
        }
    ],
    "Other": [
        {
            "username": "viral_tech_culture",
            "name": "Tech & Culture Hub",
            "verified": True,
            "followers": 1820000,
            "bio": "Viral trends, tech comedy, prompt lifestyle hacks & street reactions 🎬🎤",
            "pic": "https://images.unsplash.com/photo-1517841905240-472988babdf9?w=150&h=150&fit=crop"
        },
        {
            "username": "prompt_lifestyle",
            "name": "Zoe Creative Tech",
            "verified": False,
            "followers": 610000,
            "bio": "Everyday creative tech, aesthetic photo prompts & viral media trends 📸✨",
            "pic": "https://images.unsplash.com/photo-1524504388940-b1c1722653e1?w=150&h=150&fit=crop"
        },
        {
            "username": "silicon_satire",
            "name": "Dev Life Satire",
            "verified": True,
            "followers": 950000,
            "bio": "Hilarious developer humor, startup life & tech corporate comedy 😂💻",
            "pic": "https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?w=150&h=150&fit=crop"
        },
        {
            "username": "tech_street_vibe",
            "name": "Street Tech Show",
            "verified": False,
            "followers": 780000,
            "bio": "Street interviews on AI vs Reality, viral gadget testing & pop tech 🔥🏙️",
            "pic": "https://images.unsplash.com/photo-1501196354995-cbb51c65aaea?w=150&h=150&fit=crop"
        }
    ],
    "Blockchain": [
        {
            "username": "blockchain_career_hub",
            "name": "Web3 Fresher Career Hub",
            "verified": True,
            "followers": 740000,
            "bio": "Helping freshers & junior devs land $100k+ Blockchain & Web3 jobs 💼⛓️",
            "pic": "https://images.unsplash.com/photo-1522075469751-3a6694fb2f61?w=150&h=150&fit=crop"
        },
        {
            "username": "solidity_wizard",
            "name": "Vikram | Solidity & Audits",
            "verified": True,
            "followers": 520000,
            "bio": "Smart contract security, EVM deep-dives & interview coding problems 🛡️💻",
            "pic": "https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?w=150&h=150&fit=crop"
        },
        {
            "username": "crypto_dev_roadmap",
            "name": "Maya | Web3 Roadmap",
            "verified": False,
            "followers": 380000,
            "bio": "Complete beginner to Web3 engineer roadmaps, Foundry, DeFi & ZK rollups 🚀📚",
            "pic": "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=150&h=150&fit=crop"
        },
        {
            "username": "zeroknowledge_lab",
            "name": "ZK & Layer2 Alpha",
            "verified": True,
            "followers": 410000,
            "bio": "Next-gen ZK-proofs, Arbitrum/zkSync architectures & high-demand Web3 skills 📐⚡",
            "pic": "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150&h=150&fit=crop"
        }
    ]
}

CATEGORY_CONTENT_TEMPLATES = {
    "Niche": [
        ("Secret web app that feels illegal to know: Turns any napkin sketch into a full-stack responsive web app in 15 seconds! 🚀 #TechHacks #NewWebsite #WebDev #TrendingTech", "https://images.unsplash.com/photo-1498050108023-c5249f4df085?w=600&h=1067&fit=crop"),
        ("The top 3 new Android & iOS apps released this week that will replace 10 paid apps on your phone! #2 is insane 📲🔥 #NewApps #TechTrends #Productivity", "https://images.unsplash.com/photo-1512941937669-90a1b58e7e9c?w=600&h=1067&fit=crop"),
        ("This new open-source device lets you control your PC cursor with subtle eye movements. Testing the input latency live! 👁️💻 #NewTech #Hardware #Futuristic", "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?w=600&h=1067&fit=crop"),
        ("New web app alert: Automatically converts any 1-hour YouTube video into animated visual infographics & Notion notes in 30 seconds ⚡ #TechTools #WebApps #Productivity", "https://images.unsplash.com/photo-1507238691740-187a5b1d37b8?w=600&h=1067&fit=crop"),
        ("Apple & Google just enabled this hidden cross-platform file transfer feature that bypasses Bluetooth compression entirely 📱 #TechNews #MobileApps #ViralTech", "https://images.unsplash.com/photo-1531297484001-80022131f5a1?w=600&h=1067&fit=crop"),
        ("This brand new developer tool scans your code and eliminates 80% of boilerplate backend setup. Running it on a live production build 🛠️ #DevTools #WebTech #Coding", "https://images.unsplash.com/photo-1555066931-4365d14bab8c?w=600&h=1067&fit=crop"),
        ("The most viral tech gadget on Instagram right now: A transparent mechanical pocket synthesizer that connects to any smartphone 🎧🎛️ #Gadgets #TechReels #Trending", "https://images.unsplash.com/photo-1526738549149-8e07eca6c147?w=600&h=1067&fit=crop"),
        ("New browser extension that finds the original raw source of any viral video or image on the internet in 1 second 🔍 #NewApps #TechShorts #InternetTools", "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=600&h=1067&fit=crop")
    ],
    "AI": [
        ("Give this crazy AI tool 1 selfie and use this secret prompt: [RAW 35mm photo, volumetric neon noir lighting, ultra-detailed skin textures]... The result is mindblowing 🤯📸 #PromptEngineering #AITools #Midjourney #Flux", "https://images.unsplash.com/photo-1620712943543-bcc4688e7485?w=600&h=1067&fit=crop"),
        ("This crazy new AI website turns 1 photo of your face into an 8K talking video avatar with realistic micro-expressions in any language! 🗣️✨ #AIWebsite #TalkingAvatar #GenAI", "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=600&h=1067&fit=crop"),
        ("The secret 'Negative Prompt' structure that pro AI creators use to get perfect realistic hands and eyes every single time! Save this reel 🔖👇 #AIPrompting #Flux #CreativeAI", "https://images.unsplash.com/photo-1677442136019-21780ecad995?w=600&h=1067&fit=crop"),
        ("Anthropic & OpenAI just released new model capabilities that can autonomously navigate websites, fill forms & execute full workflows live on your screen ⚡ #AIModels #LLM #AutonomousAI", "https://images.unsplash.com/photo-1485827404703-89b55fcc595e?w=600&h=1067&fit=crop"),
        ("Transform any 5-second phone video into a Hollywood-grade cinematic VFX scene with this free AI video model 🎬🔥 #VideoAI #Sora #Runway #TechReels", "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=600&h=1067&fit=crop"),
        ("Crazy AI tool that converts 2 photos of two different people into an ultra-realistic cinematic video of them conversing in a coffee shop ☕🎥 #GenerativeAI #AIVideo", "https://images.unsplash.com/photo-1590602847861-f357a9332bbc?w=600&h=1067&fit=crop"),
        ("How to reverse-engineer any viral AI image on Instagram into its exact prompt and seed parameters in 10 seconds 🔑🎨 #PromptHacks #AIDesign", "https://images.unsplash.com/photo-1507413245164-6160d8298b31?w=600&h=1067&fit=crop")
    ],
    "Other": [
        ("When your non-tech friend asks how you made that viral hyperrealistic video avatar using just a free prompt 😂🔥 #TechHumor #Viral #AILifestyle #Reels", "https://images.unsplash.com/photo-1517841905240-472988babdf9?w=600&h=1067&fit=crop"),
        ("3 crazy AI photo prompts that everyone is using on Instagram right now to make casual travel photos look like high-end Vogue editorials ✈️📸 #AITrend #ViralReels #PhotoHacks", "https://images.unsplash.com/photo-1503899036084-c55cdd92da26?w=600&h=1067&fit=crop"),
        ("Asking people in NYC if they can spot which video clip is real and which is 100% AI generated... The results will shock you 🎤😱 #StreetInterview #TechTrends", "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=600&h=1067&fit=crop"),
        ("Things in tech culture that don't feel real: Spending 6 hours debugging only to realize you had an extra comma in JSON 💀 #DeveloperLife #TechVibe #ProgrammerHumor", "https://images.unsplash.com/photo-1550745165-9bc0b252726f?w=600&h=1067&fit=crop"),
        ("How creators are using photo-to-prompt AI reverse engineering to copy any viral aesthetic on Instagram in 2 clicks 🎨✨ #CreativeTech #PromptHacks #Trending", "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=600&h=1067&fit=crop"),
        ("The aesthetic desk setup gadgets that actually boosted my productivity vs the ones that were just hype 💻🌿 #DeskSetup #TechLifestyle #Productivity", "https://images.unsplash.com/photo-1517849845537-4d257902454a?w=600&h=1067&fit=crop")
    ],
    "Blockchain": [
        ("How to land a $120k Blockchain Developer job as a Fresher in 2026: The exact 4 portfolio projects recruiters actually look for (Save for later!) 💼🚀 #BlockchainJobs #Web3Career #Solidity #FresherGuide", "https://images.unsplash.com/photo-1639762681485-074b7f938ba0?w=600&h=1067&fit=crop"),
        ("The top 5 Solidity interview questions every junior blockchain developer gets asked in technical rounds & how to answer them with code 🧠💻 #SmartContracts #BlockchainInterview #SolidityDev #Web3Jobs", "https://images.unsplash.com/photo-1622979135225-d2ba269bc1df?w=600&h=1067&fit=crop"),
        ("Step-by-step roadmap to go from complete zero to building your first gas-optimized DeFi DEX using Foundry and Hardhat 🛠️⚡ #Web3Roadmap #DeFi #Ethereum #BlockchainTutorial", "https://images.unsplash.com/photo-1642543492481-44e81e3914a7?w=600&h=1067&fit=crop"),
        ("Why Zero-Knowledge Proofs (ZK-Rollups) are the biggest hiring surge in Web3 right now & free resources to learn them as a fresher 🛡️📈 #ZKRollups #BlockchainTech #Web3Career", "https://images.unsplash.com/photo-1644357076595-ab357ca68410?w=600&h=1067&fit=crop"),
        ("How to contribute to open-source Web3 repos on GitHub to get hired directly by DAOs without applying through LinkedIn job boards 🌐💡 #Web3Fresher #BlockchainDeveloper #CryptoJobs", "https://images.unsplash.com/photo-1639762681057-408e52192e55?w=600&h=1067&fit=crop"),
        ("Reentrancy attack explained in 45 seconds: The #1 vulnerability in smart contracts that every fresher must know how to audit 🔒⚠️ #SmartContractSecurity #SolidityAudit #BlockchainInterview", "https://images.unsplash.com/photo-1621416894569-0f39ed31d247?w=600&h=1067&fit=crop"),
        ("Build a full-stack Decentralized Voting DApp on Polygon with Next.js & Solidity: Complete project walkthrough for your resume 🗳️⛓️ #BlockchainResume #Web3Projects #FresherGuide", "https://images.unsplash.com/photo-1642790551116-18e150f248e3?w=600&h=1067&fit=crop")
    ]
}

class MockPermittedProvider(BaseDataSourceProvider):
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.rate_limit_total = 1000
        self.rate_limit_remaining = 985

    def get_provider_name(self) -> str:
        return "Permitted Sandbox Feed (Mock / Seed Provider)"

    def get_provider_type(self) -> str:
        return "mock_provider"

    def check_health(self) -> Dict[str, Any]:
        return {
            "status": "operational",
            "healthy": True,
            "message": "Permitted synthetic data provider is active and ready for ingestion.",
            "configured": True,
            "rate_limit_remaining": self.rate_limit_remaining
        }

    def get_rate_limit_info(self) -> Dict[str, Any]:
        return {
            "limit": self.rate_limit_total,
            "remaining": self.rate_limit_remaining,
            "used": self.rate_limit_total - self.rate_limit_remaining,
            "provider": self.get_provider_name()
        }

    def fetch_reels_by_category(
        self, 
        category_name: str, 
        since: Optional[datetime] = None, 
        limit: int = 105
    ) -> List[ReelRawData]:
        creators = CREATORS_DATA.get(category_name, CREATORS_DATA["Other"])
        templates = CATEGORY_CONTENT_TEMPLATES.get(category_name, CATEGORY_CONTENT_TEMPLATES["Other"])
        
        now = datetime.now(timezone.utc)
        reels: List[ReelRawData] = []
        
        rng = random.Random(hash(category_name) + 42)
        
        for i in range(1, limit + 1):
            creator = rng.choice(creators)
            tmpl_idx = (i - 1) % len(templates)
            caption_base, default_img = templates[tmpl_idx]
            
            caption = f"[{category_name.upper()} #{i}] {caption_base}"
            
            is_recent_24h = (i <= int(limit * 0.65))
            if is_recent_24h:
                hours_ago = rng.uniform(0.2, 23.8)
            else:
                hours_ago = rng.uniform(24.1, 72.0)
            
            posted_at = now - timedelta(hours=hours_ago)
            
            is_viral_breakout = (i in (1, 4, 7, 12, 19, 28, 35) or rng.random() < 0.12)
            
            if is_viral_breakout:
                view_count = int(rng.uniform(250000, 2800000))
                like_ratio = rng.uniform(0.06, 0.12)
                comment_ratio = rng.uniform(0.005, 0.02)
                share_ratio = rng.uniform(0.015, 0.04)
            elif is_recent_24h:
                view_count = int(rng.uniform(15000, 350000))
                like_ratio = rng.uniform(0.04, 0.08)
                comment_ratio = rng.uniform(0.002, 0.01)
                share_ratio = rng.uniform(0.005, 0.02)
            else:
                view_count = int(rng.uniform(40000, 950000))
                like_ratio = rng.uniform(0.03, 0.07)
                comment_ratio = rng.uniform(0.001, 0.008)
                share_ratio = rng.uniform(0.004, 0.015)
                
            likes = int(view_count * like_ratio)
            comments = int(view_count * comment_ratio)
            shares = int(view_count * share_ratio)
            saves = int(likes * rng.uniform(0.15, 0.45))
            
            shortcode = f"{category_name[:2].lower()}_{i:03d}_{rng.randint(1000, 9999)}"
            media_id = f"ig_{category_name.lower()}_{i:03d}"
            
            reel = ReelRawData(
                platform_media_id=media_id,
                permalink=f"https://www.instagram.com/reel/{shortcode}/",
                caption=caption,
                thumbnail_url=default_img,
                video_url="https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
                duration=float(rng.randint(15, 60)),
                posted_at=posted_at,
                creator_platform_id=f"user_{creator['username']}",
                creator_username=creator["username"],
                creator_name=creator["name"],
                creator_profile_pic=creator["pic"],
                creator_is_verified=creator["verified"],
                creator_followers=creator["followers"],
                creator_following=rng.randint(120, 850),
                creator_bio=creator["bio"],
                creator_url=f"https://www.instagram.com/{creator['username']}/",
                view_count=view_count,
                like_count=likes,
                comment_count=comments,
                share_count=shares,
                save_count=saves
            )
            reels.append(reel)
            
        return reels
