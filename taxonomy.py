"""
taxonomy.py - Classification: investment themes & sub-themes, sub-industries (curated),
extra stocks used by themes, and Arabic names for every Yahoo industry.
"""
# ---------------------------------------------------------------- themes
# key -> (english, arabic, material icon, {sub_key: (english, arabic, [tickers])})
THEMES = {
    "ai": ("Artificial Intelligence", "الذكاء الاصطناعي", "psychology", {
        "chips": ("AI Chips & Accelerators", "شرائح ومسرّعات الذكاء الاصطناعي", ["NVDA", "AMD", "AVGO", "MRVL", "ARM", "TSM", "INTC", "QCOM"]),
        "infra": ("AI Infrastructure & Data Centers", "البنية التحتية ومراكز البيانات", ["SMCI", "DELL", "ANET", "VRT", "EQIX", "DLR", "CRWV", "NBIS", "ORCL"]),
        "software": ("AI Software & Platforms", "برمجيات ومنصات الذكاء الاصطناعي", ["MSFT", "GOOGL", "META", "PLTR", "NOW", "CRM", "SNOW", "AI", "PATH", "SOUN", "APP"]),
        "memory": ("Memory & Storage", "الذاكرة والتخزين", ["MU", "WDC", "STX", "SNDK"])}),
    "semis": ("Semiconductors", "أشباه الموصلات", "memory", {
        "equip": ("Equipment & Materials", "معدات ومواد التصنيع", ["ASML", "AMAT", "LRCX", "KLAC", "TER"]),
        "analog": ("Analog & Auto Chips", "الرقائق التناظرية والسيارات", ["TXN", "ADI", "NXPI", "ON", "MCHP"]),
        "foundry": ("Foundry & Manufacturing", "المسابك والتصنيع", ["TSM", "INTC", "GFS"]),
        "design": ("Chip Design (EDA & IP)", "تصميم الرقائق", ["SNPS", "CDNS", "ARM"])}),
    "cloud": ("Cloud & SaaS", "الحوسبة السحابية والبرمجيات", "cloud", {
        "hyper": ("Hyperscalers", "مزودو السحابة العملاقة", ["AMZN", "MSFT", "GOOGL", "ORCL"]),
        "saas": ("Enterprise SaaS", "برمجيات الشركات", ["CRM", "NOW", "WDAY", "ADBE", "INTU", "HUBS", "TEAM", "ADSK"]),
        "data": ("Data & Observability", "البيانات والمراقبة", ["SNOW", "DDOG", "MDB"])}),
    "cyber": ("Cybersecurity", "الأمن السيبراني", "shield", {
        "platform": ("Security Platforms", "منصات الحماية", ["PANW", "CRWD", "FTNT", "CHKP", "S"]),
        "zerotrust": ("Zero Trust & Identity", "الثقة الصفرية والهوية", ["ZS", "OKTA", "NET"])}),
    "ev": ("EVs & Autonomy", "السيارات الكهربائية والقيادة الذاتية", "electric_car", {
        "makers": ("EV Makers", "مصنعو السيارات الكهربائية", ["TSLA", "RIVN", "LCID", "NIO", "XPEV", "LI"]),
        "battery": ("Batteries & Lithium", "البطاريات والليثيوم", ["ALB", "QS"]),
        "auto": ("Autonomous Driving", "القيادة الذاتية", ["TSLA", "GOOGL", "MBLY", "UBER"])}),
    "power": ("Clean Energy & Power", "الطاقة النظيفة والكهرباء", "bolt", {
        "solar": ("Solar", "الطاقة الشمسية", ["FSLR", "ENPH", "SEDG", "RUN", "NXT"]),
        "nuclear": ("Nuclear & Uranium", "الطاقة النووية واليورانيوم", ["CEG", "VST", "CCJ", "OKLO", "SMR", "BWXT", "LEU"]),
        "grid": ("Grid & Electrification", "الشبكات والكهربة", ["NEE", "GEV", "ETN", "PWR", "VRT"])}),
    "crypto": ("Crypto & Blockchain", "العملات الرقمية والبلوكتشين", "currency_bitcoin", {
        "exch": ("Exchanges & Brokers", "المنصات والوسطاء", ["COIN", "HOOD"]),
        "treasury": ("Bitcoin Treasury", "خزائن البيتكوين", ["MSTR"]),
        "miners": ("Bitcoin Miners", "معدّنو البيتكوين", ["MARA", "RIOT", "CLSK", "IREN"])}),
    "fintech": ("Fintech & Payments", "التقنية المالية والمدفوعات", "payments", {
        "networks": ("Payment Networks", "شبكات الدفع", ["V", "MA", "AXP", "PYPL"]),
        "digital": ("Digital Banks & Lending", "البنوك الرقمية والإقراض", ["SOFI", "AFRM", "UPST", "NU", "HOOD"])}),
    "ecom": ("E-commerce & Platforms", "التجارة الإلكترونية والمنصات", "shopping_cart", {
        "retail": ("Online Retail", "التجزئة الإلكترونية", ["AMZN", "SHOP", "MELI", "EBAY", "ETSY", "PDD", "BABA"]),
        "gig": ("Mobility & Travel Platforms", "منصات التنقل والسفر", ["UBER", "DASH", "ABNB", "BKNG", "LYFT"])}),
    "media": ("Streaming, Social & Gaming", "البث والتواصل والألعاب", "smart_display", {
        "stream": ("Streaming", "البث", ["NFLX", "DIS", "SPOT", "ROKU", "WBD"]),
        "social": ("Social Media", "التواصل الاجتماعي", ["META", "SNAP", "PINS", "RDDT"]),
        "gaming": ("Video Games", "ألعاب الفيديو", ["EA", "TTWO", "RBLX", "U"])}),
    "health": ("Healthcare Innovation", "الابتكار الصحي", "health_and_safety", {
        "glp1": ("GLP-1 & Obesity", "أدوية السمنة GLP-1", ["LLY", "NVO", "AMGN", "VKTX"]),
        "biotech": ("Biotech", "التقنية الحيوية", ["VRTX", "REGN", "MRNA", "BNTX", "GILD"]),
        "medtech": ("MedTech & Surgical Robotics", "الأجهزة الطبية والجراحة الروبوتية", ["ISRG", "BSX", "SYK", "MDT", "ABT"])}),
    "defense": ("Defense & Space", "الدفاع والفضاء", "rocket_launch", {
        "primes": ("Defense Primes", "شركات الدفاع الكبرى", ["LMT", "RTX", "NOC", "GD", "LHX"]),
        "space": ("Space Economy", "اقتصاد الفضاء", ["RKLB", "ASTS"]),
        "dtech": ("Drones & Defense Tech", "المسيّرات وتقنيات الدفاع", ["PLTR", "AVAV", "KTOS"])}),
    "robotics": ("Robotics & Quantum", "الروبوتات والحوسبة الكمية", "precision_manufacturing", {
        "robots": ("Robotics & Automation", "الروبوتات والأتمتة", ["ISRG", "TER", "ROK", "SYM", "ZBRA"]),
        "quantum": ("Quantum Computing", "الحوسبة الكمية", ["IONQ", "RGTI", "QBTS", "IBM", "GOOGL"])}),
    "dividend": ("Dividend Leaders", "رواد التوزيعات", "savings", {
        "staples": ("Staples Dividends", "توزيعات السلع الأساسية", ["KO", "PG", "PEP", "PM", "MO", "CL"]),
        "income": ("High-Yield Income", "دخل مرتفع", ["VZ", "T", "O", "ABBV", "XOM", "CVX"])}),
    "oil": ("Oil & Gas", "النفط والغاز", "oil_barrel", {
        "majors": ("Integrated Majors", "الشركات المتكاملة", ["XOM", "CVX"]),
        "upstream": ("Exploration & Services", "الاستكشاف والخدمات", ["COP", "EOG", "OXY", "SLB"]),
        "mid": ("Midstream & Refining", "النقل والتكرير", ["WMB", "KMI", "MPC", "PSX"])}),
}


def themes_of(sym):
    """[(theme_key, sub_key)] for a ticker."""
    out = []
    for tk, (_, _, _, subs) in THEMES.items():
        for sk, (_, _, tickers) in subs.items():
            if sym in tickers:
                out.append((tk, sk))
    return out


def theme_tickers(theme=None, sub=None):
    out = []
    for tk, (_, _, _, subs) in THEMES.items():
        if theme and tk != theme:
            continue
        for sk, (_, _, tickers) in subs.items():
            if sub and sk != sub:
                continue
            out += tickers
    return list(dict.fromkeys(out))


# ---------------------------------------------------------------- extra stocks used by themes (not in the core universe)
EXTRA = {
    "VRT": ("Vertiv", "Industrials", "Electrical Equipment & Parts"), "DLR": ("Digital Realty", "Real Estate", "REIT - Specialty"),
    "CRWV": ("CoreWeave", "Technology", "Software - Infrastructure"), "NBIS": ("Nebius Group", "Technology", "Software - Infrastructure"),
    "AI": ("C3.ai", "Technology", "Software - Application"), "PATH": ("UiPath", "Technology", "Software - Infrastructure"),
    "SOUN": ("SoundHound AI", "Technology", "Software - Application"), "WDC": ("Western Digital", "Technology", "Computer Hardware"),
    "STX": ("Seagate", "Technology", "Computer Hardware"), "SNDK": ("Sandisk", "Technology", "Computer Hardware"),
    "ASML": ("ASML", "Technology", "Semiconductor Equipment & Materials"), "TER": ("Teradyne", "Technology", "Semiconductor Equipment & Materials"),
    "NXPI": ("NXP Semiconductors", "Technology", "Semiconductors"), "ON": ("onsemi", "Technology", "Semiconductors"),
    "MCHP": ("Microchip", "Technology", "Semiconductors"), "GFS": ("GlobalFoundries", "Technology", "Semiconductors"),
    "MDB": ("MongoDB", "Technology", "Software - Infrastructure"), "HUBS": ("HubSpot", "Technology", "Software - Application"),
    "TEAM": ("Atlassian", "Technology", "Software - Application"), "ZS": ("Zscaler", "Technology", "Software - Infrastructure"),
    "OKTA": ("Okta", "Technology", "Software - Infrastructure"), "S": ("SentinelOne", "Technology", "Software - Infrastructure"),
    "CHKP": ("Check Point", "Technology", "Software - Infrastructure"), "NIO": ("NIO", "Consumer Cyclical", "Auto Manufacturers"),
    "XPEV": ("XPeng", "Consumer Cyclical", "Auto Manufacturers"), "LI": ("Li Auto", "Consumer Cyclical", "Auto Manufacturers"),
    "ALB": ("Albemarle", "Basic Materials", "Specialty Chemicals"), "QS": ("QuantumScape", "Consumer Cyclical", "Auto Parts"),
    "MBLY": ("Mobileye", "Consumer Cyclical", "Auto Parts"), "FSLR": ("First Solar", "Technology", "Solar"),
    "ENPH": ("Enphase Energy", "Technology", "Solar"), "SEDG": ("SolarEdge", "Technology", "Solar"), "RUN": ("Sunrun", "Technology", "Solar"),
    "NXT": ("Nextracker", "Technology", "Solar"), "CCJ": ("Cameco", "Energy", "Uranium"),
    "OKLO": ("Oklo", "Utilities", "Utilities - Independent Power Producers"), "SMR": ("NuScale Power", "Industrials", "Specialty Industrial Machinery"),
    "BWXT": ("BWX Technologies", "Industrials", "Aerospace & Defense"), "LEU": ("Centrus Energy", "Energy", "Uranium"),
    "PWR": ("Quanta Services", "Industrials", "Engineering & Construction"), "MARA": ("MARA Holdings", "Financial Services", "Capital Markets"),
    "RIOT": ("Riot Platforms", "Financial Services", "Capital Markets"), "CLSK": ("CleanSpark", "Financial Services", "Capital Markets"),
    "IREN": ("IREN", "Financial Services", "Capital Markets"), "AFRM": ("Affirm", "Technology", "Software - Infrastructure"),
    "UPST": ("Upstart", "Financial Services", "Credit Services"), "NU": ("Nu Holdings", "Financial Services", "Banks - Regional"),
    "EBAY": ("eBay", "Consumer Cyclical", "Internet Retail"), "ETSY": ("Etsy", "Consumer Cyclical", "Internet Retail"),
    "PDD": ("PDD Holdings", "Consumer Cyclical", "Internet Retail"), "BABA": ("Alibaba", "Consumer Cyclical", "Internet Retail"),
    "LYFT": ("Lyft", "Technology", "Software - Application"), "ROKU": ("Roku", "Communication Services", "Entertainment"),
    "SNAP": ("Snap", "Communication Services", "Internet Content & Information"), "PINS": ("Pinterest", "Communication Services", "Internet Content & Information"),
    "RBLX": ("Roblox", "Communication Services", "Electronic Gaming & Multimedia"), "U": ("Unity Software", "Technology", "Software - Application"),
    "NVO": ("Novo Nordisk", "Healthcare", "Drug Manufacturers - General"), "VKTX": ("Viking Therapeutics", "Healthcare", "Biotechnology"),
    "BNTX": ("BioNTech", "Healthcare", "Biotechnology"), "MDT": ("Medtronic", "Healthcare", "Medical Devices"),
    "GD": ("General Dynamics", "Industrials", "Aerospace & Defense"), "LHX": ("L3Harris", "Industrials", "Aerospace & Defense"),
    "RKLB": ("Rocket Lab", "Industrials", "Aerospace & Defense"), "ASTS": ("AST SpaceMobile", "Communication Services", "Telecom Services"),
    "AVAV": ("AeroVironment", "Industrials", "Aerospace & Defense"), "KTOS": ("Kratos Defense", "Industrials", "Aerospace & Defense"),
    "ROK": ("Rockwell Automation", "Industrials", "Specialty Industrial Machinery"), "SYM": ("Symbotic", "Industrials", "Specialty Industrial Machinery"),
    "ZBRA": ("Zebra Technologies", "Technology", "Communication Equipment"), "IONQ": ("IonQ", "Technology", "Computer Hardware"),
    "RGTI": ("Rigetti Computing", "Technology", "Computer Hardware"), "QBTS": ("D-Wave Quantum", "Technology", "Computer Hardware"),
}

# ---------------------------------------------------------------- curated sub-industries (english, arabic)
SUBIND = {
    "NVDA": ("GPUs & AI accelerators", "معالجات الرسوميات ومسرّعات الذكاء الاصطناعي"), "MSFT": ("Cloud, OS & productivity software", "السحابة وأنظمة التشغيل وبرامج الإنتاجية"),
    "AAPL": ("Smartphones & personal devices", "الهواتف الذكية والأجهزة الشخصية"), "AVGO": ("Networking chips & infrastructure software", "رقائق الشبكات وبرمجيات البنية التحتية"),
    "TSM": ("Contract chip manufacturing (foundry)", "تصنيع الرقائق للغير (مسبك)"), "ORCL": ("Databases & cloud infrastructure", "قواعد البيانات والبنية السحابية"),
    "PLTR": ("Data analytics & AI platforms", "تحليل البيانات ومنصات الذكاء الاصطناعي"), "AMD": ("CPUs, GPUs & data-center chips", "المعالجات ورقائق مراكز البيانات"),
    "CSCO": ("Networking equipment", "معدات الشبكات"), "CRM": ("CRM & enterprise cloud", "إدارة علاقات العملاء والسحابة"),
    "IBM": ("Hybrid cloud & consulting", "السحابة الهجينة والاستشارات"), "APP": ("Mobile advertising software", "برمجيات الإعلانات عبر الجوال"),
    "NOW": ("IT workflow automation", "أتمتة سير العمل التقني"), "SHOP": ("E-commerce software", "برمجيات التجارة الإلكترونية"),
    "INTU": ("Tax & accounting software", "برامج الضرائب والمحاسبة"), "QCOM": ("Mobile & wireless chips", "رقائق الجوال والاتصال اللاسلكي"),
    "MU": ("Memory chips (DRAM & NAND)", "رقائق الذاكرة"), "TXN": ("Analog & embedded chips", "الرقائق التناظرية والمدمجة"),
    "ANET": ("Cloud networking switches", "محولات شبكات السحابة"), "UBER": ("Ride-hailing & delivery", "النقل الذكي والتوصيل"),
    "ADBE": ("Creative & document software", "برامج التصميم والمستندات"), "ACN": ("IT consulting & outsourcing", "الاستشارات التقنية والتعهيد"),
    "ARM": ("Chip architecture licensing", "ترخيص معمارية الرقائق"), "AMAT": ("Wafer fabrication equipment", "معدات تصنيع الرقائق"),
    "LRCX": ("Etch & deposition equipment", "معدات الحفر والترسيب"), "PANW": ("Network & cloud security", "أمن الشبكات والسحابة"),
    "KLAC": ("Process control & inspection", "أنظمة الفحص والتحكم"), "CRWD": ("Endpoint security", "حماية الأجهزة الطرفية"),
    "ADI": ("Analog & mixed-signal chips", "الرقائق التناظرية والمختلطة"), "INTC": ("CPUs & chip manufacturing", "المعالجات وتصنيع الرقائق"),
    "DELL": ("PCs & AI servers", "الحواسيب وخوادم الذكاء الاصطناعي"), "CDNS": ("Chip design software (EDA)", "برمجيات تصميم الرقائق"),
    "MSTR": ("Bitcoin treasury & analytics software", "خزينة بيتكوين وبرمجيات التحليل"), "SNPS": ("Chip design software (EDA)", "برمجيات تصميم الرقائق"),
    "SNOW": ("Cloud data warehouse", "مستودعات البيانات السحابية"), "NET": ("Edge network & security", "شبكات الحافة والأمن"),
    "MRVL": ("Data infrastructure chips", "رقائق البنية التحتية للبيانات"), "FTNT": ("Firewalls & network security", "الجدران النارية وأمن الشبكات"),
    "WDAY": ("HR & finance cloud software", "برمجيات الموارد البشرية والمالية"), "ADSK": ("Design & engineering software", "برامج التصميم الهندسي"),
    "DDOG": ("Cloud monitoring", "مراقبة الأنظمة السحابية"), "SMCI": ("AI & data-center servers", "خوادم الذكاء الاصطناعي ومراكز البيانات"),
    "GOOGL": ("Search, ads & cloud", "البحث والإعلانات والسحابة"), "META": ("Social networks & digital ads", "الشبكات الاجتماعية والإعلانات الرقمية"),
    "NFLX": ("Video streaming", "بث الفيديو"), "TMUS": ("Wireless carrier", "مشغل اتصالات لاسلكية"), "T": ("Wireless & fiber carrier", "مشغل اتصالات وألياف"),
    "DIS": ("Media, parks & streaming", "الإعلام والمدن الترفيهية والبث"), "VZ": ("Wireless & broadband carrier", "مشغل اتصالات وإنترنت"),
    "SPOT": ("Music & audio streaming", "بث الموسيقى والصوتيات"), "CMCSA": ("Cable, broadband & media", "الكابل والإنترنت والإعلام"),
    "DASH": ("Food & grocery delivery", "توصيل الطعام والبقالة"), "EA": ("Sports & action video games", "ألعاب الفيديو الرياضية"),
    "TTWO": ("Video game publishing", "نشر ألعاب الفيديو"), "RDDT": ("Online communities", "المجتمعات الرقمية"), "WBD": ("Studios & streaming", "الاستوديوهات والبث"),
    "AMZN": ("E-commerce & cloud (AWS)", "التجارة الإلكترونية والسحابة"), "TSLA": ("Electric vehicles & energy storage", "السيارات الكهربائية وتخزين الطاقة"),
    "HD": ("Home improvement stores", "متاجر تحسين المنازل"), "MCD": ("Fast-food restaurants", "مطاعم الوجبات السريعة"),
    "BKNG": ("Online travel agency", "حجوزات السفر الإلكترونية"), "TJX": ("Off-price apparel retail", "تجزئة الملابس المخفضة"),
    "LOW": ("Home improvement stores", "متاجر تحسين المنازل"), "MELI": ("Latin American e-commerce & fintech", "تجارة إلكترونية ومدفوعات في أمريكا اللاتينية"),
    "SBUX": ("Coffee chain", "سلسلة مقاهي"), "NKE": ("Athletic footwear & apparel", "الأحذية والملابس الرياضية"), "RCL": ("Cruise lines", "الرحلات البحرية"),
    "ABNB": ("Home-sharing marketplace", "منصة تأجير المنازل"), "ORLY": ("Auto parts stores", "متاجر قطع غيار السيارات"), "MAR": ("Hotels", "الفنادق"),
    "CMG": ("Fast-casual restaurants", "مطاعم الوجبات السريعة الراقية"), "GM": ("Automaker", "صناعة السيارات"), "F": ("Automaker", "صناعة السيارات"),
    "LULU": ("Athletic apparel", "الملابس الرياضية"), "RIVN": ("Electric trucks & SUVs", "الشاحنات والسيارات الكهربائية"), "LCID": ("Luxury EVs", "سيارات كهربائية فاخرة"),
    "WMT": ("Hypermarkets & e-commerce", "الهايبرماركت والتجارة الإلكترونية"), "COST": ("Membership warehouse clubs", "متاجر الجملة بالعضوية"),
    "PG": ("Household & personal care", "المنتجات المنزلية والعناية الشخصية"), "KO": ("Soft drinks", "المشروبات الغازية"), "PM": ("Tobacco & smoke-free products", "التبغ والمنتجات البديلة"),
    "PEP": ("Snacks & beverages", "الوجبات الخفيفة والمشروبات"), "MO": ("Tobacco", "التبغ"), "MDLZ": ("Snacks & chocolate", "الوجبات الخفيفة والشوكولاتة"),
    "CL": ("Oral & personal care", "العناية بالفم والعناية الشخصية"), "TGT": ("General merchandise stores", "متاجر السلع العامة"),
    "BRK-B": ("Conglomerate & insurance", "تكتل استثماري وتأمين"), "JPM": ("Universal bank", "بنك شامل"), "V": ("Card payment network", "شبكة مدفوعات البطاقات"),
    "MA": ("Card payment network", "شبكة مدفوعات البطاقات"), "BAC": ("Universal bank", "بنك شامل"), "WFC": ("Consumer & commercial bank", "بنك أفراد وشركات"),
    "GS": ("Investment banking & trading", "الاستثمار المصرفي والتداول"), "MS": ("Wealth management & investment banking", "إدارة الثروات والاستثمار المصرفي"),
    "AXP": ("Premium credit cards", "البطاقات الائتمانية المميزة"), "BX": ("Alternative asset manager", "إدارة الأصول البديلة"), "C": ("Global bank", "بنك عالمي"),
    "SCHW": ("Online brokerage", "الوساطة الإلكترونية"), "BLK": ("Asset manager (ETFs)", "إدارة الأصول والصناديق"), "SPGI": ("Credit ratings & indices", "التصنيف الائتماني والمؤشرات"),
    "PGR": ("Auto insurance", "تأمين السيارات"), "KKR": ("Private equity", "الملكية الخاصة"), "CB": ("Property & casualty insurance", "تأمين الممتلكات"),
    "CME": ("Derivatives exchange", "بورصة المشتقات"), "ICE": ("Exchanges & mortgage data", "البورصات وبيانات الرهن"), "HOOD": ("Retail trading app", "تطبيق تداول للأفراد"),
    "COIN": ("Crypto exchange", "منصة العملات الرقمية"), "PYPL": ("Digital wallets & payments", "المحافظ والمدفوعات الرقمية"), "SOFI": ("Digital bank", "بنك رقمي"),
    "LLY": ("Diabetes & obesity drugs", "أدوية السكري والسمنة"), "JNJ": ("Pharma & medtech", "الأدوية والأجهزة الطبية"), "ABBV": ("Immunology drugs", "أدوية المناعة"),
    "UNH": ("Health insurance & services", "التأمين والخدمات الصحية"), "ABT": ("Medical devices & diagnostics", "الأجهزة الطبية والتشخيص"),
    "MRK": ("Oncology & vaccines", "أدوية السرطان واللقاحات"), "TMO": ("Lab equipment & services", "معدات وخدمات المختبرات"),
    "ISRG": ("Robotic surgery systems", "أنظمة الجراحة الروبوتية"), "AMGN": ("Biologic drugs", "الأدوية الحيوية"), "BSX": ("Cardiology devices", "أجهزة القلب"),
    "SYK": ("Orthopedic & surgical devices", "أجهزة العظام والجراحة"), "PFE": ("Vaccines & pharma", "اللقاحات والأدوية"), "GILD": ("Antiviral drugs", "الأدوية المضادة للفيروسات"),
    "DHR": ("Life-science tools", "أدوات علوم الحياة"), "VRTX": ("Cystic fibrosis & genetic medicines", "أدوية الأمراض الوراثية"), "HCA": ("Hospital operator", "تشغيل المستشفيات"),
    "CVS": ("Pharmacies & health insurance", "الصيدليات والتأمين الصحي"), "ELV": ("Health insurance", "التأمين الصحي"), "REGN": ("Biologic drugs", "الأدوية الحيوية"),
    "MRNA": ("mRNA vaccines", "لقاحات mRNA"),
    "GE": ("Jet engines", "محركات الطائرات"), "RTX": ("Aerospace & missiles", "الطيران والصواريخ"), "CAT": ("Construction & mining machinery", "معدات البناء والتعدين"),
    "GEV": ("Power & grid equipment", "معدات توليد الكهرباء والشبكات"), "BA": ("Commercial aircraft & defense", "الطائرات التجارية والدفاع"),
    "HON": ("Automation & aerospace", "الأتمتة والطيران"), "ETN": ("Electrical power management", "إدارة الطاقة الكهربائية"), "UNP": ("Freight railroad", "السكك الحديدية للشحن"),
    "DE": ("Farm machinery", "المعدات الزراعية"), "ADP": ("Payroll & HR services", "خدمات الرواتب والموارد البشرية"), "LMT": ("Fighter jets & missiles", "الطائرات المقاتلة والصواريخ"),
    "WM": ("Waste collection", "جمع النفايات"), "PH": ("Motion & control systems", "أنظمة الحركة والتحكم"), "NOC": ("Defense & space systems", "أنظمة الدفاع والفضاء"),
    "UPS": ("Parcel delivery", "توصيل الطرود"), "FDX": ("Express delivery", "التوصيل السريع"),
    "XOM": ("Integrated oil & gas", "النفط والغاز المتكامل"), "CVX": ("Integrated oil & gas", "النفط والغاز المتكامل"), "COP": ("Oil & gas exploration", "استكشاف النفط والغاز"),
    "WMB": ("Natural gas pipelines", "أنابيب الغاز الطبيعي"), "EOG": ("Shale oil production", "إنتاج النفط الصخري"), "KMI": ("Pipelines & terminals", "الأنابيب والمحطات"),
    "MPC": ("Oil refining", "تكرير النفط"), "PSX": ("Refining & chemicals", "التكرير والكيماويات"), "SLB": ("Oilfield services", "خدمات حقول النفط"),
    "OXY": ("Oil production & carbon capture", "إنتاج النفط واحتجاز الكربون"),
    "LIN": ("Industrial gases", "الغازات الصناعية"), "SHW": ("Paints & coatings", "الدهانات والطلاءات"), "ECL": ("Water & hygiene solutions", "حلول المياه والنظافة"),
    "NEM": ("Gold mining", "تعدين الذهب"), "APD": ("Industrial gases & hydrogen", "الغازات الصناعية والهيدروجين"), "FCX": ("Copper & gold mining", "تعدين النحاس والذهب"),
    "NUE": ("Steel production", "إنتاج الصلب"),
    "PLD": ("Logistics warehouses", "مستودعات لوجستية"), "WELL": ("Senior housing & healthcare properties", "عقارات الرعاية الصحية"),
    "AMT": ("Cell towers", "أبراج الاتصالات"), "EQIX": ("Data centers", "مراكز البيانات"), "SPG": ("Shopping malls", "المراكز التجارية"),
    "O": ("Net-lease retail properties", "عقارات تجارية مؤجرة"), "PSA": ("Self-storage", "التخزين الذاتي"),
    "NEE": ("Electric utility & renewables", "كهرباء وطاقة متجددة"), "SO": ("Electric & gas utility", "مرافق الكهرباء والغاز"),
    "CEG": ("Nuclear power generation", "توليد الكهرباء النووية"), "DUK": ("Electric utility", "مرافق الكهرباء"), "VST": ("Power generation", "توليد الكهرباء"),
    "AEP": ("Electric transmission & utility", "نقل وتوزيع الكهرباء"),
}

# ---------------------------------------------------------------- Arabic names for Yahoo industries
INDUSTRY_AR = {
    "Agricultural Inputs": "المدخلات الزراعية", "Aluminum": "الألمنيوم", "Building Materials": "مواد البناء", "Chemicals": "الكيماويات",
    "Coking Coal": "فحم الكوك", "Copper": "النحاس", "Gold": "الذهب", "Lumber & Wood Production": "الأخشاب",
    "Other Industrial Metals & Mining": "المعادن الصناعية والتعدين", "Other Precious Metals & Mining": "المعادن الثمينة والتعدين",
    "Paper & Paper Products": "الورق ومنتجاته", "Silver": "الفضة", "Specialty Chemicals": "الكيماويات المتخصصة", "Steel": "الصلب",
    "Advertising Agencies": "وكالات الإعلان", "Broadcasting": "البث الإذاعي والتلفزيوني", "Electronic Gaming & Multimedia": "الألعاب الإلكترونية والوسائط",
    "Entertainment": "الترفيه", "Internet Content & Information": "محتوى ومعلومات الإنترنت", "Publishing": "النشر", "Telecom Services": "خدمات الاتصالات",
    "Apparel Manufacturing": "تصنيع الملابس", "Apparel Retail": "تجزئة الملابس", "Auto & Truck Dealerships": "وكالات السيارات والشاحنات",
    "Auto Manufacturers": "صناعة السيارات", "Auto Parts": "قطع غيار السيارات", "Department Stores": "المتاجر الكبرى",
    "Footwear & Accessories": "الأحذية والإكسسوارات", "Furnishings, Fixtures & Appliances": "الأثاث والأجهزة المنزلية", "Gambling": "المراهنات",
    "Home Improvement Retail": "تجزئة تحسين المنازل", "Internet Retail": "التجزئة عبر الإنترنت", "Leisure": "الترفيه والتسلية", "Lodging": "الفنادق",
    "Luxury Goods": "السلع الفاخرة", "Packaging & Containers": "التغليف والحاويات", "Personal Services": "الخدمات الشخصية",
    "Recreational Vehicles": "المركبات الترفيهية", "Residential Construction": "البناء السكني", "Resorts & Casinos": "المنتجعات والكازينوهات",
    "Restaurants": "المطاعم", "Specialty Retail": "التجزئة المتخصصة", "Textile Manufacturing": "صناعة النسيج", "Travel Services": "خدمات السفر",
    "Beverages - Brewers": "المشروبات - التخمير", "Beverages - Non-Alcoholic": "المشروبات غير الكحولية", "Beverages - Wineries & Distilleries": "المشروبات - التقطير",
    "Confectioners": "الحلويات", "Discount Stores": "متاجر التخفيضات", "Education & Training Services": "التعليم والتدريب", "Farm Products": "المنتجات الزراعية",
    "Food Distribution": "توزيع الأغذية", "Grocery Stores": "متاجر البقالة", "Household & Personal Products": "المنتجات المنزلية والشخصية",
    "Packaged Foods": "الأغذية المعلبة", "Tobacco": "التبغ",
    "Oil & Gas Drilling": "حفر النفط والغاز", "Oil & Gas E&P": "استكشاف وإنتاج النفط والغاز", "Oil & Gas Equipment & Services": "معدات وخدمات النفط والغاز",
    "Oil & Gas Integrated": "النفط والغاز المتكامل", "Oil & Gas Midstream": "نقل النفط والغاز", "Oil & Gas Refining & Marketing": "تكرير وتسويق النفط",
    "Thermal Coal": "الفحم الحراري", "Uranium": "اليورانيوم",
    "Asset Management": "إدارة الأصول", "Banks - Diversified": "البنوك المتنوعة", "Banks - Regional": "البنوك الإقليمية", "Capital Markets": "أسواق المال",
    "Credit Services": "الخدمات الائتمانية", "Financial Conglomerates": "التكتلات المالية", "Financial Data & Stock Exchanges": "البيانات المالية والبورصات",
    "Insurance - Diversified": "التأمين المتنوع", "Insurance - Life": "التأمين على الحياة", "Insurance - Property & Casualty": "تأمين الممتلكات والحوادث",
    "Insurance - Reinsurance": "إعادة التأمين", "Insurance - Specialty": "التأمين المتخصص", "Insurance Brokers": "وسطاء التأمين",
    "Mortgage Finance": "التمويل العقاري", "Shell Companies": "شركات الاستحواذ",
    "Biotechnology": "التقنية الحيوية", "Diagnostics & Research": "التشخيص والأبحاث", "Drug Manufacturers - General": "صناعة الأدوية",
    "Drug Manufacturers - Specialty & Generic": "الأدوية المتخصصة والجنيسة", "Health Information Services": "خدمات المعلومات الصحية",
    "Healthcare Plans": "خطط الرعاية الصحية", "Medical Care Facilities": "مرافق الرعاية الطبية", "Medical Devices": "الأجهزة الطبية",
    "Medical Distribution": "التوزيع الطبي", "Medical Instruments & Supplies": "الأدوات والمستلزمات الطبية", "Pharmaceutical Retailers": "الصيدليات",
    "Aerospace & Defense": "الطيران والدفاع", "Airlines": "الطيران التجاري", "Airports & Air Services": "المطارات وخدمات الطيران",
    "Building Products & Equipment": "منتجات ومعدات البناء", "Business Equipment & Supplies": "معدات ومستلزمات الأعمال", "Conglomerates": "التكتلات الصناعية",
    "Consulting Services": "الخدمات الاستشارية", "Electrical Equipment & Parts": "المعدات الكهربائية", "Engineering & Construction": "الهندسة والإنشاءات",
    "Farm & Heavy Construction Machinery": "المعدات الزراعية والثقيلة", "Industrial Distribution": "التوزيع الصناعي", "Infrastructure Operations": "تشغيل البنية التحتية",
    "Integrated Freight & Logistics": "الشحن والخدمات اللوجستية", "Marine Shipping": "الشحن البحري", "Metal Fabrication": "تشكيل المعادن",
    "Pollution & Treatment Controls": "معالجة التلوث", "Railroads": "السكك الحديدية", "Rental & Leasing Services": "خدمات التأجير",
    "Security & Protection Services": "خدمات الأمن والحماية", "Specialty Business Services": "خدمات الأعمال المتخصصة",
    "Specialty Industrial Machinery": "الآلات الصناعية المتخصصة", "Staffing & Employment Services": "خدمات التوظيف", "Tools & Accessories": "الأدوات والإكسسوارات",
    "Trucking": "النقل بالشاحنات", "Waste Management": "إدارة النفايات",
    "Real Estate - Development": "التطوير العقاري", "Real Estate - Diversified": "العقارات المتنوعة", "Real Estate Services": "الخدمات العقارية",
    "REIT - Diversified": "صناديق الريت المتنوعة", "REIT - Healthcare Facilities": "ريت المرافق الصحية", "REIT - Hotel & Motel": "ريت الفنادق",
    "REIT - Industrial": "ريت العقارات الصناعية", "REIT - Mortgage": "ريت الرهن العقاري", "REIT - Office": "ريت المكاتب", "REIT - Residential": "ريت السكني",
    "REIT - Retail": "ريت التجزئة", "REIT - Specialty": "ريت المتخصص",
    "Communication Equipment": "معدات الاتصالات", "Computer Hardware": "أجهزة الحاسب", "Consumer Electronics": "الإلكترونيات الاستهلاكية",
    "Electronic Components": "المكونات الإلكترونية", "Electronics & Computer Distribution": "توزيع الإلكترونيات", "Information Technology Services": "خدمات تقنية المعلومات",
    "Scientific & Technical Instruments": "الأجهزة العلمية والتقنية", "Semiconductor Equipment & Materials": "معدات ومواد أشباه الموصلات",
    "Semiconductors": "أشباه الموصلات", "Software - Application": "البرمجيات التطبيقية", "Software - Infrastructure": "برمجيات البنية التحتية", "Solar": "الطاقة الشمسية",
    "Utilities - Diversified": "المرافق المتنوعة", "Utilities - Independent Power Producers": "منتجو الطاقة المستقلون", "Utilities - Regulated Electric": "مرافق الكهرباء المنظمة",
    "Utilities - Regulated Gas": "مرافق الغاز المنظمة", "Utilities - Regulated Water": "مرافق المياه المنظمة", "Utilities - Renewable": "الطاقة المتجددة",
    "Other": "أخرى",
}
