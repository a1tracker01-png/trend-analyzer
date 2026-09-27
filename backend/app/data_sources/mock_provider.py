import random
import math
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any

from backend.app.data_sources.base import BaseDataSourceProvider, ReelRawData

# Curated high quality creators per category strictly focused on South Asia (India, Pakistan, Bangladesh, Nepal)
CREATORS_DATA = {
    "Niche": [
        {
            "username": "techburner",
            "name": "Shlok | Tech Burner 🇮🇳",
            "verified": True,
            "followers": 4800000,
            "bio": "Insane gadget experiments, crazy new smartphones & quirky tech hacks in India 🔥📱",
            "pic": "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150&h=150&fit=crop",
            "country": "India"
        },
        {
            "username": "videowalisarkar",
            "name": "Bilal Munir | VideoWaliSarkar 🇵🇰",
            "verified": True,
            "followers": 2300000,
            "bio": "Unboxing top smartphones, speed tests & gadget camera battles in Pakistan ⚡🇵🇰",
            "pic": "https://images.unsplash.com/photo-1570295999919-56ceb5ecca61?w=150&h=150&fit=crop",
            "country": "Pakistan"
        },
        {
            "username": "sohag360",
            "name": "Sohag 360 | Tech Studio BD 🇧🇩",
            "verified": True,
            "followers": 1750000,
            "bio": "Honest smartphone reviews, secret website hacks & mobile tricks in Bangladesh 🇧🇩📲",
            "pic": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&h=150&fit=crop",
            "country": "Bangladesh"
        },
        {
            "username": "gadgetbytenepal",
            "name": "GadgetByte Nepal 🇳🇵",
            "verified": True,
            "followers": 1200000,
            "bio": "Nepal's #1 tech media: Laptop comparisons, budget phones & gadget prices in NPR 🇳🇵⚡",
            "pic": "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150&h=150&fit=crop",
            "country": "Nepal"
        },
        {
            "username": "technicalguruji",
            "name": "Gaurav Chaudhary | Tech Guruji 🇮🇳",
            "verified": True,
            "followers": 5200000,
            "bio": "Namaskar Dosto! Latest breakthrough tech, futuristic gadgets & consumer electronics 🇮🇳🚀",
            "pic": "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150&h=150&fit=crop",
            "country": "India"
        }
    ],
    "AI": [
        {
            "username": "beebomco",
            "name": "Beebom AI Innovations 🇮🇳",
            "verified": True,
            "followers": 3100000,
            "bio": "Insane AI websites, secret ChatGPT prompt hacks, Flux & Sora masterclasses 🤖✨",
            "pic": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=150&h=150&fit=crop",
            "country": "India"
        },
        {
            "username": "hisham.sarwar",
            "name": "Hisham Sarwar | AI Skills 🇵🇰",
            "verified": True,
            "followers": 1450000,
            "bio": "Mastering AI workflows, LLM prompting & freelance tech mastery across Pakistan 🚀🇵🇰",
            "pic": "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150&h=150&fit=crop",
            "country": "Pakistan"
        },
        {
            "username": "jhankarmahbub",
            "name": "Jhankar Mahbub | AI Hero 🇧🇩",
            "verified": True,
            "followers": 1600000,
            "bio": "Making AI coding, prompt engineering & tech simple for everyone in Bangladesh 🤖🇧🇩",
            "pic": "https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?w=150&h=150&fit=crop",
            "country": "Bangladesh"
        },
        {
            "username": "fusemachines",
            "name": "Fusemachines AI Nepal 🇳🇵",
            "verified": True,
            "followers": 620000,
            "bio": "Democratizing AI, deep learning & next-gen AI agent architectures from Kathmandu 🇳🇵🧠",
            "pic": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&h=150&fit=crop",
            "country": "Nepal"
        },
        {
            "username": "varunmayya",
            "name": "Varun Mayya | GenAI & Agents 🇮🇳",
            "verified": True,
            "followers": 1950000,
            "bio": "Testing mind-blowing autonomous AI agents, talking avatars & synthetic media 🤯⚡",
            "pic": "https://images.unsplash.com/photo-1522075469751-3a6694fb2f61?w=150&h=150&fit=crop",
            "country": "India"
        }
    ],
    "Other": [
        {
            "username": "ezsnippet",
            "name": "Neeraj Walia | EZSnippet 🇮🇳",
            "verified": True,
            "followers": 2800000,
            "bio": "Coding memes, tech corporate satire & hilarious developer relatable moments 😂💻",
            "pic": "https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?w=150&h=150&fit=crop",
            "country": "India"
        },
        {
            "username": "azadchaiwala",
            "name": "Azad Chaiwala | Tech Hustle 🇵🇰",
            "verified": True,
            "followers": 2100000,
            "bio": "Tech lifestyle, Pakistani startup culture & developer wealth creation 🚀🇵🇰",
            "pic": "https://images.unsplash.com/photo-1501196354995-cbb51c65aaea?w=150&h=150&fit=crop",
            "country": "Pakistan"
        },
        {
            "username": "learnwithsumit",
            "name": "Sumit Saha | Dev Culture 🇧🇩",
            "verified": True,
            "followers": 1350000,
            "bio": "Full stack developer journey, Bangladeshi tech culture & coding humor 🎬🇧🇩",
            "pic": "https://images.unsplash.com/photo-1524504388940-b1c1722653e1?w=150&h=150&fit=crop",
            "country": "Bangladesh"
        },
        {
            "username": "routineofnepalbanda",
            "name": "RONB Tech & Youth Vibe 🇳🇵",
            "verified": True,
            "followers": 3400000,
            "bio": "Viral tech discoveries, Nepali startup breakthroughs & youth culture in Nepal 🇳🇵🔥",
            "pic": "https://images.unsplash.com/photo-1517841905240-472988babdf9?w=150&h=150&fit=crop",
            "country": "Nepal"
        },
        {
            "username": "striver_79",
            "name": "Raj Vikramaditya | SDE Life 🇮🇳",
            "verified": True,
            "followers": 1650000,
            "bio": "FAANG interview humor, Bangalore tech park life & fresher placement memes 💻🇮🇳",
            "pic": "https://images.unsplash.com/photo-1517849845537-4d257902454a?w=150&h=150&fit=crop",
            "country": "India"
        }
    ],
    "Blockchain": [
        {
            "username": "polygon.technology",
            "name": "Polygon MATIC Web3 🇮🇳",
            "verified": True,
            "followers": 1850000,
            "bio": "Built in India for the world: Zero-Knowledge rollups, EVM scaling & Web3 devs ⛓️🇮🇳",
            "pic": "https://images.unsplash.com/photo-1639762681485-074b7f938ba0?w=150&h=150&fit=crop",
            "country": "India"
        },
        {
            "username": "waqarzaka",
            "name": "Waqar Zaka | Web3 Pakistan 🇵🇰",
            "verified": True,
            "followers": 2400000,
            "bio": "Championing crypto legalization, TenUp smart contracts & Web3 education in Pakistan 🇵🇰⚡",
            "pic": "https://images.unsplash.com/photo-1621416894569-0f39ed31d247?w=150&h=150&fit=crop",
            "country": "Pakistan"
        },
        {
            "username": "blockchainbangladesh",
            "name": "Blockchain Bangladesh & Web3 🇧🇩",
            "verified": True,
            "followers": 580000,
            "bio": "Smart contract development, Solidity roadmaps & Web3 fresher careers in Dhaka 💼🇧🇩",
            "pic": "https://images.unsplash.com/photo-1622979135225-d2ba269bc1df?w=150&h=150&fit=crop",
            "country": "Bangladesh"
        },
        {
            "username": "web3nepal",
            "name": "Web3 Nepal Community 🇳🇵",
            "verified": True,
            "followers": 490000,
            "bio": "Building Nepal's Web3 ecosystem: Foundry audits, DeFi protocols & dev bounties 🇳🇵⛓️",
            "pic": "https://images.unsplash.com/photo-1644357076595-ab357ca68410?w=150&h=150&fit=crop",
            "country": "Nepal"
        },
        {
            "username": "pushpendratech",
            "name": "Pushpendra Singh | Web3 🇮🇳",
            "verified": True,
            "followers": 1250000,
            "bio": "Hindi Web3 guides, Solidity tutorials & how freshers land remote crypto roles 🇮🇳💼",
            "pic": "https://images.unsplash.com/photo-1642543492481-44e81e3914a7?w=150&h=150&fit=crop",
            "country": "India"
        }
    ]
}

CATEGORY_CONTENT_TEMPLATES = {
    "Niche": [
        ("Secret website that feels illegal to know: Turns any handwritten UI napkin sketch into a full responsive React & Tailwind app in 15 seconds! 🚀 #DesiTech #IndiaTech #TechBurner #WebDev", "https://images.unsplash.com/photo-1498050108023-c5249f4df085?w=600&h=1067&fit=crop"),
        ("Top 3 new Android & iOS productivity apps released this week that will replace 10 paid apps on your phone! #2 is insane 📲🔥 #VideoWaliSarkar #PakistanTech #NewApps", "https://images.unsplash.com/photo-1512941937669-90a1b58e7e9c?w=600&h=1067&fit=crop"),
        ("Testing Nepal's first open-source smart gadget in Kathmandu: Zero input latency cursor control with eye movements 🇳🇵👁️💻 #GadgetByteNepal #NepalTech #Hardware", "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?w=600&h=1067&fit=crop"),
        ("New web app alert: Automatically converts any 1-hour Bangla/Hindi lecture video into animated visual infographics & Notion notes in 30s ⚡ #Sohag360 #BangladeshTech #Productivity", "https://images.unsplash.com/photo-1507238691740-187a5b1d37b8?w=600&h=1067&fit=crop"),
        ("Namaskar Dosto! Hidden cross-platform file transfer feature on Android & iPhone that transfers 4K videos at 120MB/s without internet 📱 #TechnicalGuruji #TechTips #India", "https://images.unsplash.com/photo-1531297484001-80022131f5a1?w=600&h=1067&fit=crop"),
        ("This new developer tool scans your code and eliminates 80% of boilerplate backend setup. Running it on a live production build 🛠️ #DevTools #WebTech #Coding", "https://images.unsplash.com/photo-1555066931-4365d14bab8c?w=600&h=1067&fit=crop"),
        ("The most viral budget gadget in South Asia right now: A transparent mechanical pocket synthesizer under ₹2,000 / PKR 6,500 🎧🎛️ #Gadgets #TechReels #Trending", "https://images.unsplash.com/photo-1526738549149-8e07eca6c147?w=600&h=1067&fit=crop"),
        ("New browser extension that finds the original raw source of any viral video or image on the internet in 1 second 🔍 #NewApps #TechShorts #InternetTools", "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=600&h=1067&fit=crop")
    ],
    "AI": [
        ("Give this crazy AI tool 1 selfie and use this secret prompt: [RAW 35mm photo, volumetric South Asian neon lighting, ultra-detailed textures]... Result is mindblowing 🤯📸 #Beebom #AITools #Midjourney", "https://images.unsplash.com/photo-1620712943543-bcc4688e7485?w=600&h=1067&fit=crop"),
        ("This crazy new AI website turns 1 photo of your face into an 8K talking video avatar in Urdu, Hindi, Bengali & Nepali! 🗣️✨ #AIWebsite #TalkingAvatar #GenAI", "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=600&h=1067&fit=crop"),
        ("The secret 'Negative Prompt' structure that pro AI creators use to get perfect realistic hands and eyes every single time! Save this reel 🔖👇 #HishamSarwar #AIPrompting #CreativeAI", "https://images.unsplash.com/photo-1677442136019-21780ecad995?w=600&h=1067&fit=crop"),
        ("Top 5 free AI tools every developer in Bangladesh & India must master in 2026 to 10x their workflow and build full-stack apps faster 🚀💻 #JhankarMahbub #AIHero #ProgrammingHero", "https://images.unsplash.com/photo-1485827404703-89b55fcc595e?w=600&h=1067&fit=crop"),
        ("Kathmandu AI Lab demo: Transforming phone videos into Hollywood cinematic VFX with open-source generative video models 🎬🔥 #Fusemachines #VideoAI #NepalTech", "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=600&h=1067&fit=crop"),
        ("Varun Mayya explains: Autonomous AI agents can now browse websites, book flights, and write full codebases completely hands-free ⚡ #VarunMayya #AutonomousAI #LLMs", "https://images.unsplash.com/photo-1590602847861-f357a9332bbc?w=600&h=1067&fit=crop"),
        ("How to reverse-engineer any viral AI image on Instagram into its exact prompt and seed parameters in 10 seconds 🔑🎨 #PromptHacks #AIDesign #SouthAsiaAI", "https://images.unsplash.com/photo-1507413245164-6160d8298b31?w=600&h=1067&fit=crop")
    ],
    "Other": [
        ("Bangalore vs Karachi vs Dhaka dev life: Spending 6 hours debugging only to realize you had an extra comma in JSON 💀😂 #EZSnippet #DeveloperHumor #TechLife", "https://images.unsplash.com/photo-1517841905240-472988babdf9?w=600&h=1067&fit=crop"),
        ("When your non-tech relatives in South Asia think you can hack any account because you opened DevTools in Chrome 😂🔥 #AzadChaiwala #TechHumor #ViralReels", "https://images.unsplash.com/photo-1503899036084-c55cdd92da26?w=600&h=1067&fit=crop"),
        ("Asking developers in Bengaluru tech parks if they can differentiate real code from Claude 3.7 Sonnet code... The reactions are insane 🎤😱 #Striver #TakeUForward #CodingHumor", "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=600&h=1067&fit=crop"),
        ("Full-stack junior vs senior developer in Dhaka: How we handle production database crashes on a Friday evening 💻🔥 #LearnWithSumit #DevCulture #Bangladesh", "https://images.unsplash.com/photo-1550745165-9bc0b252726f?w=600&h=1067&fit=crop"),
        ("Viral Kathmandu startup scene: Things happening in Nepali tech colleges that feel like Silicon Valley in 2026 🇳🇵🚀 #RoutineOfNepalBanda #RONB #NepalTech", "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=600&h=1067&fit=crop"),
        ("3 aesthetic desk setup gadgets under ₹1,500 / PKR 4,500 / 2,000 BDT that actually boosted my productivity vs the hype 💻🌿 #DeskSetup #DesiTech", "https://images.unsplash.com/photo-1517849845537-4d257902454a?w=600&h=1067&fit=crop")
    ],
    "Blockchain": [
        ("How to land a remote $120k Web3 & Solidity job as a Fresher in India, Pakistan, BD or Nepal: The exact 4 portfolio projects recruiters look for 💼🚀 #Polygon #Solidity #FresherGuide", "https://images.unsplash.com/photo-1639762681485-074b7f938ba0?w=600&h=1067&fit=crop"),
        ("Waqar Zaka explains: Top 5 Solidity smart contract interview questions every junior blockchain developer gets asked in technical rounds 🧠🇵🇰 #WaqarZaka #Web3Pakistan #TenUp", "https://images.unsplash.com/photo-1622979135225-d2ba269bc1df?w=600&h=1067&fit=crop"),
        ("Step-by-step roadmap to go from complete zero to building your first gas-optimized DeFi DEX using Foundry on Polygon MATIC 🛠️⚡ #PolygonTech #Web3Roadmap #Ethereum", "https://images.unsplash.com/photo-1642543492481-44e81e3914a7?w=600&h=1067&fit=crop"),
        ("Why Zero-Knowledge Proofs (ZK-Rollups) are creating massive hiring demand across South Asia in 2026 & free resources to learn them as a fresher 🛡️📈 #ZKRollups #BlockchainBangladesh", "https://images.unsplash.com/photo-1644357076595-ab357ca68410?w=600&h=1067&fit=crop"),
        ("Pushpendra Singh Digital: How to contribute to open-source Web3 GitHub repos to get hired directly by DAOs without LinkedIn job boards 🌐💡 #PushpendraTech #CryptoIndia", "https://images.unsplash.com/photo-1639762681057-408e52192e55?w=600&h=1067&fit=crop"),
        ("Reentrancy attack explained in 45 seconds: The #1 vulnerability in smart contracts that every fresher must know how to audit 🔒⚠️ #SmartContractSecurity #SolidityAudit #Web3Nepal", "https://images.unsplash.com/photo-1621416894569-0f39ed31d247?w=600&h=1067&fit=crop"),
        ("Build a full-stack Decentralized Voting DApp on Polygon with Next.js & Solidity: Complete resume project walkthrough for South Asian freshers 🗳️⛓️ #Web3Projects #FresherGuide", "https://images.unsplash.com/photo-1642790551116-18e150f248e3?w=600&h=1067&fit=crop")
    ]
}

class MockPermittedProvider(BaseDataSourceProvider):
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.rate_limit_total = 1000
        self.rate_limit_remaining = 985

    def get_provider_name(self) -> str:
        return "South Asia Regional Feed (India, Pakistan, Bangladesh, Nepal)"

    def get_provider_type(self) -> str:
        return "mock_provider"

    def check_health(self) -> Dict[str, Any]:
        return {
            "status": "operational",
            "healthy": True,
            "message": "South Asia regional feed (India, Pakistan, Bangladesh, Nepal) is active.",
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
                country=creator.get("country", "India"),
                view_count=view_count,
                like_count=likes,
                comment_count=comments,
                share_count=shares,
                save_count=saves
            )
            reels.append(reel)
            
        return reels
