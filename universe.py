"""
universe.py - Static reference data: US stock universe (sector / industry / approx. market cap),
market tiles, sector ETFs and economic series.
Market caps are approximate ($B) and only used as a fallback for heatmap sizing.
"""
import re

# symbol: (name, sector, industry, approx_cap_$B)
STOCKS = {
    # Technology
    "NVDA": ("NVIDIA", "Technology", "Semiconductors", 4300), "MSFT": ("Microsoft", "Technology", "Software - Infrastructure", 3700),
    "AAPL": ("Apple", "Technology", "Consumer Electronics", 3500), "AVGO": ("Broadcom", "Technology", "Semiconductors", 1600),
    "TSM": ("Taiwan Semiconductor", "Technology", "Semiconductors", 1200), "ORCL": ("Oracle", "Technology", "Software - Infrastructure", 700),
    "PLTR": ("Palantir", "Technology", "Software - Infrastructure", 400), "AMD": ("AMD", "Technology", "Semiconductors", 300),
    "CSCO": ("Cisco", "Technology", "Communication Equipment", 270), "CRM": ("Salesforce", "Technology", "Software - Application", 250),
    "IBM": ("IBM", "Technology", "Information Technology Services", 250), "APP": ("AppLovin", "Technology", "Software - Application", 200),
    "NOW": ("ServiceNow", "Technology", "Software - Application", 190), "SHOP": ("Shopify", "Technology", "Software - Application", 190),
    "INTU": ("Intuit", "Technology", "Software - Application", 185), "QCOM": ("Qualcomm", "Technology", "Semiconductors", 175),
    "MU": ("Micron", "Technology", "Semiconductors", 170), "TXN": ("Texas Instruments", "Technology", "Semiconductors", 170),
    "ANET": ("Arista Networks", "Technology", "Computer Hardware", 170), "UBER": ("Uber", "Technology", "Software - Application", 190),
    "ADBE": ("Adobe", "Technology", "Software - Infrastructure", 160), "ACN": ("Accenture", "Technology", "Information Technology Services", 160),
    "ARM": ("Arm Holdings", "Technology", "Semiconductors", 160), "AMAT": ("Applied Materials", "Technology", "Semiconductor Equipment & Materials", 150),
    "LRCX": ("Lam Research", "Technology", "Semiconductor Equipment & Materials", 130), "PANW": ("Palo Alto Networks", "Technology", "Software - Infrastructure", 130),
    "KLAC": ("KLA", "Technology", "Semiconductor Equipment & Materials", 120), "CRWD": ("CrowdStrike", "Technology", "Software - Infrastructure", 120),
    "ADI": ("Analog Devices", "Technology", "Semiconductors", 115), "INTC": ("Intel", "Technology", "Semiconductors", 110),
    "DELL": ("Dell", "Technology", "Computer Hardware", 90), "CDNS": ("Cadence Design", "Technology", "Software - Application", 90),
    "MSTR": ("Strategy", "Technology", "Software - Application", 90), "SNPS": ("Synopsys", "Technology", "Software - Infrastructure", 75),
    "SNOW": ("Snowflake", "Technology", "Software - Application", 75), "NET": ("Cloudflare", "Technology", "Software - Infrastructure", 70),
    "MRVL": ("Marvell", "Technology", "Semiconductors", 65), "FTNT": ("Fortinet", "Technology", "Software - Infrastructure", 65),
    "WDAY": ("Workday", "Technology", "Software - Application", 65), "ADSK": ("Autodesk", "Technology", "Software - Application", 65),
    "DDOG": ("Datadog", "Technology", "Software - Application", 50), "SMCI": ("Super Micro Computer", "Technology", "Computer Hardware", 28),
    # Communication Services
    "GOOGL": ("Alphabet", "Communication Services", "Internet Content & Information", 3000),
    "META": ("Meta Platforms", "Communication Services", "Internet Content & Information", 1800),
    "NFLX": ("Netflix", "Communication Services", "Entertainment", 500), "TMUS": ("T-Mobile", "Communication Services", "Telecom Services", 270),
    "T": ("AT&T", "Communication Services", "Telecom Services", 200), "DIS": ("Disney", "Communication Services", "Entertainment", 200),
    "VZ": ("Verizon", "Communication Services", "Telecom Services", 180), "SPOT": ("Spotify", "Communication Services", "Internet Content & Information", 140),
    "CMCSA": ("Comcast", "Communication Services", "Telecom Services", 130), "DASH": ("DoorDash", "Communication Services", "Internet Content & Information", 110),
    "EA": ("Electronic Arts", "Communication Services", "Electronic Gaming & Multimedia", 50),
    "TTWO": ("Take-Two Interactive", "Communication Services", "Electronic Gaming & Multimedia", 45),
    "RDDT": ("Reddit", "Communication Services", "Internet Content & Information", 40), "WBD": ("Warner Bros. Discovery", "Communication Services", "Entertainment", 30),
    # Consumer Cyclical
    "AMZN": ("Amazon", "Consumer Cyclical", "Internet Retail", 2400), "TSLA": ("Tesla", "Consumer Cyclical", "Auto Manufacturers", 1300),
    "HD": ("Home Depot", "Consumer Cyclical", "Home Improvement Retail", 400), "MCD": ("McDonald's", "Consumer Cyclical", "Restaurants", 220),
    "BKNG": ("Booking Holdings", "Consumer Cyclical", "Travel Services", 175), "TJX": ("TJX Companies", "Consumer Cyclical", "Apparel Retail", 155),
    "LOW": ("Lowe's", "Consumer Cyclical", "Home Improvement Retail", 140), "MELI": ("MercadoLibre", "Consumer Cyclical", "Internet Retail", 120),
    "SBUX": ("Starbucks", "Consumer Cyclical", "Restaurants", 100), "NKE": ("Nike", "Consumer Cyclical", "Footwear & Accessories", 100),
    "RCL": ("Royal Caribbean", "Consumer Cyclical", "Travel Services", 90), "ABNB": ("Airbnb", "Consumer Cyclical", "Travel Services", 80),
    "ORLY": ("O'Reilly Automotive", "Consumer Cyclical", "Auto Parts", 80), "MAR": ("Marriott", "Consumer Cyclical", "Lodging", 75),
    "CMG": ("Chipotle", "Consumer Cyclical", "Restaurants", 55), "GM": ("General Motors", "Consumer Cyclical", "Auto Manufacturers", 55),
    "F": ("Ford", "Consumer Cyclical", "Auto Manufacturers", 45), "LULU": ("Lululemon", "Consumer Cyclical", "Apparel Retail", 25),
    "RIVN": ("Rivian", "Consumer Cyclical", "Auto Manufacturers", 15), "LCID": ("Lucid", "Consumer Cyclical", "Auto Manufacturers", 6),
    # Consumer Defensive
    "WMT": ("Walmart", "Consumer Defensive", "Discount Stores", 800), "COST": ("Costco", "Consumer Defensive", "Discount Stores", 420),
    "PG": ("Procter & Gamble", "Consumer Defensive", "Household & Personal Products", 370),
    "KO": ("Coca-Cola", "Consumer Defensive", "Beverages - Non-Alcoholic", 300), "PM": ("Philip Morris", "Consumer Defensive", "Tobacco", 250),
    "PEP": ("PepsiCo", "Consumer Defensive", "Beverages - Non-Alcoholic", 200), "MO": ("Altria", "Consumer Defensive", "Tobacco", 100),
    "MDLZ": ("Mondelez", "Consumer Defensive", "Confectioners", 85), "CL": ("Colgate-Palmolive", "Consumer Defensive", "Household & Personal Products", 70),
    "TGT": ("Target", "Consumer Defensive", "Discount Stores", 45),
    # Financial Services
    "BRK-B": ("Berkshire Hathaway", "Financial Services", "Insurance - Diversified", 1050), "JPM": ("JPMorgan Chase", "Financial Services", "Banks - Diversified", 820),
    "V": ("Visa", "Financial Services", "Credit Services", 680), "MA": ("Mastercard", "Financial Services", "Credit Services", 530),
    "BAC": ("Bank of America", "Financial Services", "Banks - Diversified", 370), "WFC": ("Wells Fargo", "Financial Services", "Banks - Diversified", 260),
    "GS": ("Goldman Sachs", "Financial Services", "Capital Markets", 230), "MS": ("Morgan Stanley", "Financial Services", "Capital Markets", 230),
    "AXP": ("American Express", "Financial Services", "Credit Services", 230), "BX": ("Blackstone", "Financial Services", "Asset Management", 200),
    "C": ("Citigroup", "Financial Services", "Banks - Diversified", 180), "SCHW": ("Charles Schwab", "Financial Services", "Capital Markets", 170),
    "BLK": ("BlackRock", "Financial Services", "Asset Management", 170), "SPGI": ("S&P Global", "Financial Services", "Financial Data & Stock Exchanges", 160),
    "PGR": ("Progressive", "Financial Services", "Insurance - Property & Casualty", 150), "KKR": ("KKR", "Financial Services", "Asset Management", 120),
    "CB": ("Chubb", "Financial Services", "Insurance - Property & Casualty", 110), "CME": ("CME Group", "Financial Services", "Financial Data & Stock Exchanges", 100),
    "ICE": ("Intercontinental Exchange", "Financial Services", "Financial Data & Stock Exchanges", 100),
    "HOOD": ("Robinhood", "Financial Services", "Capital Markets", 100), "COIN": ("Coinbase", "Financial Services", "Financial Data & Stock Exchanges", 85),
    "PYPL": ("PayPal", "Financial Services", "Credit Services", 65), "SOFI": ("SoFi", "Financial Services", "Credit Services", 30),
    # Healthcare
    "LLY": ("Eli Lilly", "Healthcare", "Drug Manufacturers - General", 800), "JNJ": ("Johnson & Johnson", "Healthcare", "Drug Manufacturers - General", 420),
    "ABBV": ("AbbVie", "Healthcare", "Drug Manufacturers - General", 380), "UNH": ("UnitedHealth", "Healthcare", "Healthcare Plans", 300),
    "ABT": ("Abbott", "Healthcare", "Medical Devices", 230), "MRK": ("Merck", "Healthcare", "Drug Manufacturers - General", 220),
    "TMO": ("Thermo Fisher", "Healthcare", "Diagnostics & Research", 180), "ISRG": ("Intuitive Surgical", "Healthcare", "Medical Instruments & Supplies", 170),
    "AMGN": ("Amgen", "Healthcare", "Drug Manufacturers - General", 160), "BSX": ("Boston Scientific", "Healthcare", "Medical Devices", 150),
    "SYK": ("Stryker", "Healthcare", "Medical Devices", 145), "PFE": ("Pfizer", "Healthcare", "Drug Manufacturers - General", 140),
    "GILD": ("Gilead", "Healthcare", "Drug Manufacturers - General", 140), "DHR": ("Danaher", "Healthcare", "Diagnostics & Research", 140),
    "VRTX": ("Vertex Pharmaceuticals", "Healthcare", "Biotechnology", 110), "HCA": ("HCA Healthcare", "Healthcare", "Medical Care Facilities", 95),
    "CVS": ("CVS Health", "Healthcare", "Healthcare Plans", 90), "ELV": ("Elevance Health", "Healthcare", "Healthcare Plans", 75),
    "REGN": ("Regeneron", "Healthcare", "Biotechnology", 60), "MRNA": ("Moderna", "Healthcare", "Biotechnology", 10),
    # Industrials
    "GE": ("GE Aerospace", "Industrials", "Aerospace & Defense", 290), "RTX": ("RTX", "Industrials", "Aerospace & Defense", 210),
    "CAT": ("Caterpillar", "Industrials", "Farm & Heavy Construction Machinery", 200), "GEV": ("GE Vernova", "Industrials", "Specialty Industrial Machinery", 170),
    "BA": ("Boeing", "Industrials", "Aerospace & Defense", 160), "HON": ("Honeywell", "Industrials", "Conglomerates", 140),
    "ETN": ("Eaton", "Industrials", "Specialty Industrial Machinery", 140), "UNP": ("Union Pacific", "Industrials", "Railroads", 135),
    "DE": ("Deere", "Industrials", "Farm & Heavy Construction Machinery", 130), "ADP": ("ADP", "Industrials", "Staffing & Employment Services", 120),
    "LMT": ("Lockheed Martin", "Industrials", "Aerospace & Defense", 110), "WM": ("Waste Management", "Industrials", "Waste Management", 90),
    "PH": ("Parker-Hannifin", "Industrials", "Specialty Industrial Machinery", 90), "NOC": ("Northrop Grumman", "Industrials", "Aerospace & Defense", 80),
    "UPS": ("UPS", "Industrials", "Integrated Freight & Logistics", 75), "FDX": ("FedEx", "Industrials", "Integrated Freight & Logistics", 55),
    # Energy
    "XOM": ("Exxon Mobil", "Energy", "Oil & Gas Integrated", 480), "CVX": ("Chevron", "Energy", "Oil & Gas Integrated", 270),
    "COP": ("ConocoPhillips", "Energy", "Oil & Gas E&P", 120), "WMB": ("Williams Companies", "Energy", "Oil & Gas Midstream", 70),
    "EOG": ("EOG Resources", "Energy", "Oil & Gas E&P", 65), "KMI": ("Kinder Morgan", "Energy", "Oil & Gas Midstream", 60),
    "MPC": ("Marathon Petroleum", "Energy", "Oil & Gas Refining & Marketing", 55), "PSX": ("Phillips 66", "Energy", "Oil & Gas Refining & Marketing", 55),
    "SLB": ("SLB", "Energy", "Oil & Gas Equipment & Services", 50), "OXY": ("Occidental Petroleum", "Energy", "Oil & Gas E&P", 45),
    # Basic Materials
    "LIN": ("Linde", "Basic Materials", "Specialty Chemicals", 220), "SHW": ("Sherwin-Williams", "Basic Materials", "Specialty Chemicals", 85),
    "ECL": ("Ecolab", "Basic Materials", "Specialty Chemicals", 75), "NEM": ("Newmont", "Basic Materials", "Gold", 70),
    "APD": ("Air Products", "Basic Materials", "Specialty Chemicals", 65), "FCX": ("Freeport-McMoRan", "Basic Materials", "Copper", 60),
    "NUE": ("Nucor", "Basic Materials", "Steel", 32),
    # Real Estate
    "PLD": ("Prologis", "Real Estate", "REIT - Industrial", 100), "WELL": ("Welltower", "Real Estate", "REIT - Healthcare Facilities", 100),
    "AMT": ("American Tower", "Real Estate", "REIT - Specialty", 95), "EQIX": ("Equinix", "Real Estate", "REIT - Specialty", 80),
    "SPG": ("Simon Property", "Real Estate", "REIT - Retail", 60), "O": ("Realty Income", "Real Estate", "REIT - Retail", 52),
    "PSA": ("Public Storage", "Real Estate", "REIT - Industrial", 50),
    # Utilities
    "NEE": ("NextEra Energy", "Utilities", "Utilities - Regulated Electric", 150), "SO": ("Southern Company", "Utilities", "Utilities - Regulated Electric", 100),
    "CEG": ("Constellation Energy", "Utilities", "Utilities - Renewable", 100), "DUK": ("Duke Energy", "Utilities", "Utilities - Regulated Electric", 95),
    "VST": ("Vistra", "Utilities", "Utilities - Independent Power Producers", 60), "AEP": ("American Electric Power", "Utilities", "Utilities - Regulated Electric", 60),
}
US_UNIVERSE = list(STOCKS)
SECTORS = sorted({v[1] for v in STOCKS.values()})


def sector_of(sym):
    return STOCKS.get(sym, (sym, "Other", "Other", 0))[1]


def industry_of(sym):
    return STOCKS.get(sym, (sym, "Other", "Other", 0))[2]


def name_of(sym):
    return STOCKS.get(sym, (sym,))[0]


def by_sector():
    out = {}
    for s, (_, sec, _, _) in STOCKS.items():
        out.setdefault(sec, []).append(s)
    return out


# Yahoo sector -> industry list (for the screener filters)
INDUSTRIES = {
    "Basic Materials": ["Agricultural Inputs", "Aluminum", "Building Materials", "Chemicals", "Coking Coal", "Copper", "Gold",
                        "Lumber & Wood Production", "Other Industrial Metals & Mining", "Other Precious Metals & Mining",
                        "Paper & Paper Products", "Silver", "Specialty Chemicals", "Steel"],
    "Communication Services": ["Advertising Agencies", "Broadcasting", "Electronic Gaming & Multimedia", "Entertainment",
                               "Internet Content & Information", "Publishing", "Telecom Services"],
    "Consumer Cyclical": ["Apparel Manufacturing", "Apparel Retail", "Auto & Truck Dealerships", "Auto Manufacturers", "Auto Parts",
                          "Department Stores", "Footwear & Accessories", "Furnishings, Fixtures & Appliances", "Gambling",
                          "Home Improvement Retail", "Internet Retail", "Leisure", "Lodging", "Luxury Goods", "Packaging & Containers",
                          "Personal Services", "Recreational Vehicles", "Residential Construction", "Resorts & Casinos", "Restaurants",
                          "Specialty Retail", "Textile Manufacturing", "Travel Services"],
    "Consumer Defensive": ["Beverages - Brewers", "Beverages - Non-Alcoholic", "Beverages - Wineries & Distilleries", "Confectioners",
                           "Discount Stores", "Education & Training Services", "Farm Products", "Food Distribution", "Grocery Stores",
                           "Household & Personal Products", "Packaged Foods", "Tobacco"],
    "Energy": ["Oil & Gas Drilling", "Oil & Gas E&P", "Oil & Gas Equipment & Services", "Oil & Gas Integrated", "Oil & Gas Midstream",
               "Oil & Gas Refining & Marketing", "Thermal Coal", "Uranium"],
    "Financial Services": ["Asset Management", "Banks - Diversified", "Banks - Regional", "Capital Markets", "Credit Services",
                           "Financial Conglomerates", "Financial Data & Stock Exchanges", "Insurance - Diversified", "Insurance - Life",
                           "Insurance - Property & Casualty", "Insurance - Reinsurance", "Insurance - Specialty", "Insurance Brokers",
                           "Mortgage Finance", "Shell Companies"],
    "Healthcare": ["Biotechnology", "Diagnostics & Research", "Drug Manufacturers - General", "Drug Manufacturers - Specialty & Generic",
                   "Health Information Services", "Healthcare Plans", "Medical Care Facilities", "Medical Devices", "Medical Distribution",
                   "Medical Instruments & Supplies", "Pharmaceutical Retailers"],
    "Industrials": ["Aerospace & Defense", "Airlines", "Airports & Air Services", "Building Products & Equipment", "Business Equipment & Supplies",
                    "Conglomerates", "Consulting Services", "Electrical Equipment & Parts", "Engineering & Construction",
                    "Farm & Heavy Construction Machinery", "Industrial Distribution", "Infrastructure Operations",
                    "Integrated Freight & Logistics", "Marine Shipping", "Metal Fabrication", "Pollution & Treatment Controls", "Railroads",
                    "Rental & Leasing Services", "Security & Protection Services", "Specialty Business Services",
                    "Specialty Industrial Machinery", "Staffing & Employment Services", "Tools & Accessories", "Trucking", "Waste Management"],
    "Real Estate": ["Real Estate - Development", "Real Estate - Diversified", "Real Estate Services", "REIT - Diversified",
                    "REIT - Healthcare Facilities", "REIT - Hotel & Motel", "REIT - Industrial", "REIT - Mortgage", "REIT - Office",
                    "REIT - Residential", "REIT - Retail", "REIT - Specialty"],
    "Technology": ["Communication Equipment", "Computer Hardware", "Consumer Electronics", "Electronic Components",
                   "Electronics & Computer Distribution", "Information Technology Services", "Scientific & Technical Instruments",
                   "Semiconductor Equipment & Materials", "Semiconductors", "Software - Application", "Software - Infrastructure", "Solar"],
    "Utilities": ["Utilities - Diversified", "Utilities - Independent Power Producers", "Utilities - Regulated Electric",
                  "Utilities - Regulated Gas", "Utilities - Regulated Water", "Utilities - Renewable"],
}

SECTOR_ETFS = {"XLK": "Technology", "XLC": "Communication Services", "XLY": "Consumer Cyclical", "XLP": "Consumer Defensive",
               "XLF": "Financial Services", "XLV": "Healthcare", "XLE": "Energy", "XLI": "Industrials", "XLB": "Basic Materials",
               "XLU": "Utilities", "XLRE": "Real Estate"}

# group -> {symbol: (english, arabic)}
MARKET_TILES = {
    ("Indices", "المؤشرات"): {"^GSPC": ("S&P 500", "إس آند بي 500"), "^IXIC": ("Nasdaq", "ناسداك"), "^DJI": ("Dow Jones", "داو جونز"),
                              "^RUT": ("Russell 2000", "راسل 2000"), "^VIX": ("VIX", "مؤشر الخوف VIX")},
    ("Futures", "العقود الآجلة"): {"ES=F": ("S&P Futures", "عقود إس آند بي"), "NQ=F": ("Nasdaq Futures", "عقود ناسداك"),
                                  "YM=F": ("Dow Futures", "عقود داو"), "RTY=F": ("Russell Futures", "عقود راسل")},
    ("Treasury Yields", "عوائد السندات"): {"^IRX": ("13W T-Bill", "أذونات 13 أسبوع"), "^FVX": ("5Y Yield", "عائد 5 سنوات"),
                                          "^TNX": ("10Y Yield", "عائد 10 سنوات"), "^TYX": ("30Y Yield", "عائد 30 سنة")},
    ("Commodities", "السلع"): {"GC=F": ("Gold", "الذهب"), "SI=F": ("Silver", "الفضة"), "CL=F": ("WTI Crude", "نفط غرب تكساس"),
                              "BZ=F": ("Brent Crude", "خام برنت"), "NG=F": ("Natural Gas", "الغاز الطبيعي"), "HG=F": ("Copper", "النحاس")},
    ("Currencies", "العملات"): {"DX-Y.NYB": ("US Dollar Index", "مؤشر الدولار"), "EURUSD=X": ("EUR/USD", "يورو/دولار"),
                               "JPY=X": ("USD/JPY", "دولار/ين"), "GBPUSD=X": ("GBP/USD", "استرليني/دولار"), "SAR=X": ("USD/SAR", "دولار/ريال")},
    ("Crypto", "العملات الرقمية"): {"BTC-USD": ("Bitcoin", "بيتكوين"), "ETH-USD": ("Ethereum", "إيثريوم"), "SOL-USD": ("Solana", "سولانا")},
}
TAPE = ["^GSPC", "^IXIC", "^DJI", "^RUT", "^VIX", "^TNX", "GC=F", "CL=F", "BTC-USD", "ETH-USD", "DX-Y.NYB", "EURUSD=X",
        "NVDA", "AAPL", "MSFT", "AMZN", "GOOGL", "META", "TSLA", "AVGO", "JPM", "LLY"]
TAPE_NAMES = {"^GSPC": "S&P 500", "^IXIC": "NASDAQ", "^DJI": "DOW", "^RUT": "RUSSELL", "^VIX": "VIX", "^TNX": "US10Y",
              "GC=F": "GOLD", "CL=F": "WTI", "BTC-USD": "BTC", "ETH-USD": "ETH", "DX-Y.NYB": "DXY", "EURUSD=X": "EURUSD"}

# FRED id -> (english, arabic, transform, unit, higher_is_bad)
MACRO_SERIES = {
    "FEDFUNDS": ("Fed Funds Rate", "سعر الفائدة الفيدرالية", "level", "%", None),
    "CPIAUCSL": ("CPI Inflation (YoY)", "التضخم CPI (سنوي)", "yoy", "%", True),
    "CPILFESL": ("Core CPI (YoY)", "التضخم الأساسي (سنوي)", "yoy", "%", True),
    "PCEPILFE": ("Core PCE (YoY)", "مؤشر PCE الأساسي", "yoy", "%", True),
    "PPIFIS": ("PPI Final Demand (YoY)", "أسعار المنتجين PPI", "yoy", "%", True),
    "UNRATE": ("Unemployment Rate", "معدل البطالة", "level", "%", True),
    "PAYEMS": ("Nonfarm Payrolls (MoM, K)", "الوظائف غير الزراعية (ألف)", "diff", "K", False),
    "ICSA": ("Initial Jobless Claims (K)", "طلبات إعانة البطالة (ألف)", "level_k", "K", True),
    "JTSJOL": ("JOLTS Job Openings (M)", "الوظائف الشاغرة (مليون)", "level_m", "M", False),
    "A191RL1Q225SBEA": ("Real GDP Growth (QoQ ann.)", "نمو الناتج المحلي", "level", "%", False),
    "RSAFS": ("Retail Sales (MoM)", "مبيعات التجزئة (شهري)", "mom", "%", False),
    "INDPRO": ("Industrial Production (YoY)", "الإنتاج الصناعي (سنوي)", "yoy", "%", False),
    "DGORDER": ("Durable Goods Orders (MoM)", "طلبات السلع المعمرة", "mom", "%", False),
    "HOUST": ("Housing Starts (K, ann.)", "بدء إنشاء المساكن (ألف)", "level", "K", False),
    "UMCSENT": ("Consumer Sentiment", "ثقة المستهلك", "level", "", False),
    "MORTGAGE30US": ("30Y Mortgage Rate", "فائدة الرهن العقاري 30 سنة", "level", "%", True),
    "T10Y2Y": ("10Y-2Y Yield Spread", "فارق عائد 10-2 سنوات", "level", "%", False),
    "M2SL": ("M2 Money Supply (YoY)", "المعروض النقدي M2 (سنوي)", "yoy", "%", None),
}

# ---------------------------------------------------------------- news -> ticker detection
_ALIASES = {
    "AAPL": ["Apple", "iPhone"], "MSFT": ["Microsoft"], "NVDA": ["Nvidia"], "AMZN": ["Amazon"], "GOOGL": ["Alphabet", "Google"],
    "META": ["Meta Platforms", "Facebook", "Instagram"], "TSLA": ["Tesla"], "AVGO": ["Broadcom"], "ORCL": ["Oracle"],
    "NFLX": ["Netflix"], "AMD": ["AMD", "Advanced Micro Devices"], "INTC": ["Intel"], "PLTR": ["Palantir"], "TSM": ["TSMC", "Taiwan Semiconductor"],
    "JPM": ["JPMorgan", "JP Morgan"], "GS": ["Goldman Sachs", "Goldman"], "MS": ["Morgan Stanley"], "BAC": ["Bank of America"],
    "WFC": ["Wells Fargo"], "C": ["Citigroup", "Citi"], "BRK-B": ["Berkshire"], "V": ["Visa Inc"], "MA": ["Mastercard"],
    "WMT": ["Walmart"], "COST": ["Costco"], "TGT": ["Target Corp"], "KO": ["Coca-Cola"], "PEP": ["PepsiCo"], "MCD": ["McDonald"],
    "SBUX": ["Starbucks"], "NKE": ["Nike"], "DIS": ["Disney"], "BA": ["Boeing"], "LMT": ["Lockheed"], "CAT": ["Caterpillar"],
    "XOM": ["Exxon"], "CVX": ["Chevron"], "LLY": ["Eli Lilly", "Lilly"], "UNH": ["UnitedHealth"], "PFE": ["Pfizer"], "MRK": ["Merck"],
    "JNJ": ["Johnson & Johnson"], "ABBV": ["AbbVie"], "MRNA": ["Moderna"], "COIN": ["Coinbase"], "HOOD": ["Robinhood"],
    "MSTR": ["MicroStrategy", "Strategy Inc"], "UBER": ["Uber"], "ABNB": ["Airbnb"], "SHOP": ["Shopify"], "CRM": ["Salesforce"],
    "ADBE": ["Adobe"], "MU": ["Micron"], "QCOM": ["Qualcomm"], "ARM": ["Arm Holdings"], "SMCI": ["Super Micro"], "DELL": ["Dell"],
    "IBM": ["IBM"], "CSCO": ["Cisco"], "F": ["Ford Motor", "Ford"], "GM": ["General Motors"], "RIVN": ["Rivian"], "LCID": ["Lucid"],
    "PYPL": ["PayPal"], "SOFI": ["SoFi"], "BLK": ["BlackRock"], "BX": ["Blackstone"], "SPOT": ["Spotify"], "RDDT": ["Reddit"],
    "NOW": ["ServiceNow"], "CRWD": ["CrowdStrike"], "PANW": ["Palo Alto Networks"], "SNOW": ["Snowflake"], "APP": ["AppLovin"],
    "MELI": ["MercadoLibre"], "HD": ["Home Depot"], "LOW": ["Lowe's"], "UPS": ["UPS"], "FDX": ["FedEx"], "GE": ["GE Aerospace"],
    "GEV": ["GE Vernova"], "CEG": ["Constellation Energy"], "VST": ["Vistra"], "NEM": ["Newmont"], "FCX": ["Freeport"],
    "DASH": ["DoorDash"], "WBD": ["Warner Bros"], "CMCSA": ["Comcast"], "VZ": ["Verizon"], "T": ["AT&T"], "TMUS": ["T-Mobile"],
    "ISRG": ["Intuitive Surgical"], "VRTX": ["Vertex"], "REGN": ["Regeneron"], "AMGN": ["Amgen"], "GILD": ["Gilead"],
    "ANET": ["Arista"], "MRVL": ["Marvell"], "AMAT": ["Applied Materials"], "LRCX": ["Lam Research"], "TXN": ["Texas Instruments"],
}
_PATTERNS = [(sym, re.compile(r"(?<![\w$])(" + "|".join(re.escape(a) for a in names) + r")(?!\w)", re.I if all(len(a) > 4 for a in names) else 0))
             for sym, names in _ALIASES.items()]
_CASHTAG = re.compile(r"\$([A-Z]{1,5})\b|\((?:NASDAQ|NYSE|NYSEARCA)?:?\s?([A-Z]{1,5})\)")


def detect_tickers(text):
    """Finds company tickers mentioned in a headline."""
    found = []
    for m in _CASHTAG.finditer(text or ""):
        s = m.group(1) or m.group(2)
        if s and s in STOCKS and s not in found:
            found.append(s)
    for sym, pat in _PATTERNS:
        if sym not in found and pat.search(text or ""):
            found.append(sym)
    return found
