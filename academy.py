"""
academy.py - Course content (bilingual). Each course ~3 minutes: 4 short lessons + a 3-question quiz.
Section tuple: (title_en, title_ar, body_en, body_ar, takeaway_en, takeaway_ar, interactive_key or None)
Quiz tuple: (question_en, question_ar, [(option_en, option_ar), ...], correct_index, why_en, why_ar)
"""

COURSES = [
    {"id": "basics", "art": "market", "icon": "school", "level": ("Beginner", "مبتدئ"), "mins": 3,
     "title": ("How the Stock Market Works", "كيف يعمل سوق الأسهم"),
     "tagline": ("Stocks, indices, orders and trading hours: the foundation of everything.", "الأسهم والمؤشرات والأوامر وأوقات التداول: الأساس لكل شيء."),
     "sections": [
         ("What is a stock?", "ما هو السهم؟",
          "A stock is a small piece of ownership in a company. When a company goes public it lists its shares on an exchange such as the NYSE or Nasdaq, and anyone can buy them. The price moves every second based on supply and demand: when more people want to buy than sell, the price rises.",
          "السهم هو حصة صغيرة من ملكية شركة. عندما تطرح الشركة أسهمها للاكتتاب تُدرج في بورصة مثل NYSE أو ناسداك، ويستطيع أي شخص شراءها. يتحرك السعر كل ثانية حسب العرض والطلب: إذا كان الراغبون في الشراء أكثر من البائعين يرتفع السعر.",
          "Owning a share means owning a slice of the company's future profits.", "امتلاك السهم يعني امتلاك جزء من أرباح الشركة المستقبلية.", None),
         ("How investors make money", "كيف يربح المستثمر؟",
          "There are two sources of return: price appreciation (you sell higher than you bought) and dividends (cash the company pays to shareholders). Together they form your total return. Over long periods, reinvesting gains lets returns compound: 10% a year roughly doubles money in about 7 years.",
          "للعائد مصدران: ارتفاع السعر (تبيع بأعلى مما اشتريت) والتوزيعات النقدية التي تدفعها الشركة للمساهمين. مجموعهما هو العائد الكلي. وعلى المدى الطويل، إعادة استثمار الأرباح تجعل العائد يتراكم: عائد 10% سنوياً يضاعف المال تقريباً خلال 7 سنوات.",
          "Time in the market + compounding is the most powerful force for investors.", "الوقت في السوق مع التراكم هو أقوى أداة للمستثمر.", None),
         ("Market indices", "مؤشرات السوق",
          "An index tracks a basket of stocks to measure the whole market. The S&P 500 follows 500 large US companies, the Nasdaq Composite is tech-heavy, and the Dow Jones follows 30 blue chips. You can buy the whole index in one trade through an ETF such as SPY (S&P 500) or QQQ (Nasdaq 100).",
          "المؤشر يتتبع سلة من الأسهم ليقيس أداء السوق كامل. مؤشر S&P 500 يتتبع 500 شركة أمريكية كبرى، وناسداك يغلب عليه قطاع التقنية، وداو جونز يتتبع 30 شركة عريقة. تقدر تشتري المؤشر كامل بصفقة وحدة عن طريق صندوق ETF مثل SPY أو QQQ.",
          "Most professional fund managers fail to beat the S&P 500 over 10+ years.", "أغلب مديري الصناديق المحترفين لا يتفوقون على S&P 500 على مدى 10 سنوات أو أكثر.", "live_spy"),
         ("Orders and trading hours", "الأوامر وأوقات التداول",
          "A market order buys immediately at the best available price. A limit order sets the maximum price you'll pay (or the minimum you'll accept when selling). The bid is what buyers offer, the ask is what sellers want; the gap is the spread. The US regular session runs 9:30 AM–4:00 PM New York time (4:30 PM–11:00 PM Saudi time).",
          "أمر السوق يشتري فوراً بأفضل سعر متاح. أما الأمر المحدد (Limit) فتحدد فيه أعلى سعر تدفعه (أو أقل سعر تقبله عند البيع). سعر العرض Bid هو ما يعرضه المشترون، وسعر الطلب Ask هو ما يطلبه البائعون، والفرق بينهما اسمه السبريد. الجلسة الأمريكية الرسمية من 9:30 صباحاً إلى 4:00 عصراً بتوقيت نيويورك (4:30 عصراً إلى 11:00 مساءً بتوقيت السعودية).",
          "Use limit orders on less liquid stocks to avoid paying a wide spread.", "استخدم الأوامر المحددة في الأسهم قليلة السيولة حتى لا تدفع سبريد واسع.", None)],
     "quiz": [
         ("What does owning one share mean?", "ماذا يعني امتلاك سهم واحد؟",
          [("You lent money to the company", "أقرضت الشركة مالاً"), ("You own a small part of the company", "تملك جزءاً صغيراً من الشركة"), ("You work for the company", "تعمل لدى الشركة")], 1,
          "A share is partial ownership, not a loan (that would be a bond).", "السهم ملكية جزئية وليس قرضاً (القرض اسمه سند)."),
         ("Which ETF tracks the S&P 500?", "أي صندوق يتتبع مؤشر S&P 500؟",
          [("QQQ", "QQQ"), ("SPY", "SPY"), ("GLD", "GLD")], 1, "SPY tracks the S&P 500; QQQ tracks the Nasdaq 100.", "SPY يتتبع S&P 500، وQQQ يتتبع ناسداك 100."),
         ("A limit order…", "الأمر المحدد (Limit)…",
          [("executes instantly at any price", "يُنفذ فوراً بأي سعر"), ("sets the worst price you accept", "يحدد أسوأ سعر تقبله"), ("only works after hours", "يعمل فقط بعد الإغلاق")], 1,
          "A limit order guarantees the price, not the execution.", "الأمر المحدد يضمن السعر وليس التنفيذ.")]},

    {"id": "candles", "art": "candles", "icon": "candlestick_chart", "level": ("Beginner", "مبتدئ"), "mins": 3,
     "title": ("Reading Candlestick Charts", "قراءة الشموع اليابانية"),
     "tagline": ("Understand what every candle is telling you in seconds.", "افهم ما تقوله لك كل شمعة خلال ثوانٍ."),
     "sections": [
         ("Anatomy of a candle", "تشريح الشمعة",
          "Each candle shows four prices for a period: open, high, low and close. The thick body spans open to close; the thin wicks show the high and low. A green candle closed higher than it opened; a red candle closed lower.",
          "كل شمعة تعرض أربعة أسعار للفترة: الافتتاح والأعلى والأدنى والإغلاق. الجسم العريض يمتد من الافتتاح إلى الإغلاق، والذيول الرفيعة تمثل أعلى وأدنى سعر. الشمعة الخضراء أغلقت أعلى من افتتاحها، والحمراء أغلقت أدنى.",
          "Body = the battle's result. Wicks = where price was rejected.", "الجسم = نتيجة المعركة. الذيول = الأماكن التي رُفض فيها السعر.", "candle_anatomy"),
         ("What bodies and wicks say", "ماذا تقول الأجسام والذيول",
          "A long body means strong conviction. A long upper wick means buyers pushed up but sellers rejected higher prices. A long lower wick shows buyers stepping in. A tiny body with wicks on both sides (a doji) signals indecision.",
          "الجسم الطويل يعني قناعة قوية. الذيل العلوي الطويل يعني أن المشترين دفعوا السعر للأعلى لكن البائعين رفضوه. الذيل السفلي الطويل يعني دخول المشترين. والجسم الصغير جداً مع ذيلين (دوجي) يعني تردد السوق.",
          "Read wicks as footprints of rejected prices.", "اقرأ الذيول كآثار أقدام لأسعار مرفوضة.", None),
         ("Three patterns worth knowing", "ثلاثة نماذج مهمة",
          "Hammer: small body, long lower wick after a drop; possible bottom. Bullish engulfing: a green body that fully covers the prior red one; buyers took control. Shooting star: long upper wick after a rise; possible top. Patterns matter most at support or resistance.",
          "المطرقة: جسم صغير وذيل سفلي طويل بعد هبوط؛ احتمال قاع. الابتلاع الشرائي: جسم أخضر يغطي الجسم الأحمر السابق بالكامل؛ المشترون سيطروا. الشهاب: ذيل علوي طويل بعد صعود؛ احتمال قمة. أهمية النماذج تزيد عند مناطق الدعم والمقاومة.",
          "A pattern without location is noise; a pattern at a key level is a signal.", "النموذج بدون موقع مهم مجرد ضجيج، وعند مستوى مهم يصبح إشارة.", None),
         ("Timeframes and confirmation", "الأطر الزمنية والتأكيد",
          "The same stock looks different on 5-minute, daily and weekly charts. Beginners should start with daily candles. Always confirm a signal with volume: a breakout on heavy volume is far more reliable than one on light volume.",
          "نفس السهم يبدو مختلفاً على فريم 5 دقائق واليومي والأسبوعي. المبتدئ يبدأ بالشموع اليومية. أكّد أي إشارة بحجم التداول: الاختراق مع حجم مرتفع أقوى بكثير من الاختراق بحجم ضعيف.",
          "Higher timeframe = more reliable signal.", "كلما كان الإطار الزمني أكبر كانت الإشارة أوثق.", "live_spy")],
     "quiz": [
         ("A green candle means…", "الشمعة الخضراء تعني…",
          [("close > open", "الإغلاق أعلى من الافتتاح"), ("volume was high", "الحجم كان مرتفعاً"), ("price hit a new high", "السعر سجل قمة جديدة")], 0,
          "Color only compares close with open.", "اللون يقارن الإغلاق بالافتتاح فقط."),
         ("A long upper wick shows…", "الذيل العلوي الطويل يدل على…",
          [("strong buying at the close", "شراء قوي عند الإغلاق"), ("sellers rejected higher prices", "البائعون رفضوا الأسعار الأعلى"), ("a stock split", "تجزئة السهم")], 1,
          "Price went up but couldn't stay there.", "السعر صعد لكنه لم يستطع البقاء هناك."),
         ("Which confirms a breakout best?", "ما أفضل تأكيد للاختراق؟",
          [("Low volume", "حجم منخفض"), ("High volume", "حجم مرتفع"), ("A doji", "شمعة دوجي")], 1, "Volume shows real participation.", "الحجم يعكس المشاركة الحقيقية.")]},

    {"id": "levels", "art": "levels", "icon": "horizontal_rule", "level": ("Beginner", "مبتدئ"), "mins": 3,
     "title": ("Support & Resistance", "الدعم والمقاومة"),
     "tagline": ("Find the price zones where buyers and sellers keep showing up.", "اكتشف المناطق السعرية التي يظهر فيها المشترون والبائعون مراراً."),
     "sections": [
         ("What are they?", "ما هما؟",
          "Support is a price zone where buying has repeatedly stopped a decline. Resistance is a zone where selling has repeatedly capped a rise. They are zones, not exact lines: think of them as floors and ceilings.",
          "الدعم منطقة سعرية أوقف فيها الشراء الهبوط أكثر من مرة. والمقاومة منطقة أوقف فيها البيع الصعود مراراً. هي مناطق وليست خطوطاً دقيقة: تخيلها أرضية وسقف.",
          "The more times a level holds, the more important it becomes.", "كلما صمد المستوى مرات أكثر زادت أهميته.", None),
         ("Why they work", "لماذا تنجح؟",
          "Markets have memory. Traders who bought at a level defend it, those who missed it wait to buy there again, and large orders cluster at round numbers and prior highs and lows. That creates repeated reactions at the same prices.",
          "للسوق ذاكرة. من اشترى عند مستوى يدافع عنه، ومن فاته ينتظر الشراء عنده مرة أخرى، والأوامر الكبيرة تتجمع عند الأرقام المستديرة والقمم والقيعان السابقة. هذا يصنع ردود فعل متكررة عند نفس الأسعار.",
          "Levels are where many orders are waiting.", "المستويات هي حيث تنتظر أوامر كثيرة.", "sr_live"),
         ("Breakouts and role reversal", "الاختراق وتبادل الأدوار",
          "When price closes decisively above resistance with strong volume, that old ceiling often becomes the new floor. The same happens in reverse: broken support tends to act as resistance on the way back up.",
          "عندما يغلق السعر بوضوح فوق المقاومة مع حجم قوي، غالباً يتحول السقف القديم إلى أرضية جديدة. والعكس صحيح: الدعم المكسور يتحول إلى مقاومة عند عودة السعر للأعلى.",
          "Old resistance, once broken, becomes support.", "المقاومة المكسورة تتحول إلى دعم.", None),
         ("Using levels to trade", "استخدام المستويات في التداول",
          "Buy near support in an uptrend, place your stop slightly below it, and target the next resistance. This gives a clear plan: you know exactly where you're wrong before you enter. The Catalyst Pro page does this automatically.",
          "اشترِ قرب الدعم في اتجاه صاعد، وضع وقف الخسارة تحته بقليل، واستهدف المقاومة التالية. هكذا تكون خطتك واضحة: تعرف أين تكون مخطئاً قبل أن تدخل. صفحة Catalyst Pro تسوي هذا تلقائياً.",
          "Every trade needs an exit plan before the entry.", "كل صفقة تحتاج خطة خروج قبل الدخول.", None)],
     "quiz": [
         ("Support is…", "الدعم هو…",
          [("a zone where declines have stopped", "منطقة توقف عندها الهبوط"), ("the daily high", "أعلى سعر في اليوم"), ("a company's revenue", "إيرادات الشركة")], 0,
          "Buyers have repeatedly stepped in there.", "المشترون دخلوا عندها مراراً."),
         ("After a strong breakout above resistance, that level often…", "بعد اختراق قوي للمقاومة، غالباً هذا المستوى…",
          [("disappears", "يختفي"), ("becomes support", "يصبح دعماً"), ("becomes the stop target", "يصبح الهدف")], 1, "Role reversal.", "تبادل الأدوار."),
         ("Where is a logical stop for a buy at support?", "أين يكون وقف الخسارة المنطقي لشراء عند الدعم؟",
          [("Just below support", "تحت الدعم بقليل"), ("At resistance", "عند المقاومة"), ("No stop needed", "لا حاجة لوقف")], 0,
          "If support breaks, the idea is invalid.", "إذا انكسر الدعم فالفكرة لم تعد صالحة.")]},

    {"id": "ma", "art": "ma", "icon": "show_chart", "level": ("Intermediate", "متوسط"), "mins": 3,
     "title": ("Moving Averages & Trend", "المتوسطات المتحركة والاتجاه"),
     "tagline": ("The simplest tool to tell an uptrend from a downtrend.", "أبسط أداة لتمييز الاتجاه الصاعد من الهابط."),
     "sections": [
         ("SMA and EMA", "المتوسط البسيط والأسي",
          "A moving average smooths price by averaging the last N closes. The simple average (SMA) weights every day equally; the exponential average (EMA) weights recent days more, so it reacts faster. Popular settings: 20 (short), 50 (medium) and 200 (long term).",
          "المتوسط المتحرك ينعّم حركة السعر بحساب متوسط آخر N إغلاقات. المتوسط البسيط SMA يعطي كل يوم نفس الوزن، والأسي EMA يعطي الأيام الأخيرة وزناً أكبر فيتفاعل أسرع. الإعدادات الشائعة: 20 (قصير)، 50 (متوسط)، 200 (طويل).",
          "The 200-day average is the line institutions watch most.", "متوسط 200 يوم هو الخط الأكثر متابعة من المؤسسات.", None),
         ("Reading the trend", "قراءة الاتجاه",
          "Price above a rising 200-day average: long-term uptrend. Price below a falling one: downtrend. When the 20 is above the 50 and the 50 above the 200, all timeframes agree: a strong uptrend.",
          "السعر فوق متوسط 200 الصاعد: اتجاه صاعد طويل المدى. تحته والمتوسط نازل: اتجاه هابط. وإذا كان متوسط 20 فوق 50 و50 فوق 200 فكل الأطر الزمنية متفقة: اتجاه صاعد قوي.",
          "Trade with the trend, not against it.", "تداول مع الاتجاه وليس ضده.", "ma_live"),
         ("Golden and death crosses", "التقاطع الذهبي والسلبي",
          "A golden cross happens when the 50-day crosses above the 200-day: often the start of a long uptrend. The death cross is the opposite. Try both in the Strategy Lab to see how they performed on any stock.",
          "التقاطع الذهبي يحدث عندما يعبر متوسط 50 فوق متوسط 200، وغالباً يكون بداية اتجاه صاعد طويل. والتقاطع السلبي عكسه. جرّب الاثنين في مختبر الاستراتيجيات لترى أداءهما على أي سهم.",
          "Crosses are slow but filter out a lot of noise.", "التقاطعات بطيئة لكنها تصفي كثيراً من الضجيج.", None),
         ("Limitations", "العيوب",
          "Moving averages lag because they use past prices. In sideways markets they cross back and forth and create false signals (whipsaws). Combine them with support/resistance and volume instead of using them alone.",
          "المتوسطات متأخرة لأنها تعتمد على أسعار ماضية. وفي الأسواق العرضية تتقاطع ذهاباً وإياباً وتعطي إشارات كاذبة. ادمجها مع الدعم والمقاومة والحجم بدل الاعتماد عليها وحدها.",
          "No indicator works in every market condition.", "لا يوجد مؤشر ينجح في كل ظروف السوق.", None)],
     "quiz": [
         ("Which reacts faster to new prices?", "أيهما يتفاعل أسرع مع الأسعار الجديدة؟",
          [("SMA", "المتوسط البسيط"), ("EMA", "المتوسط الأسي"), ("Both equally", "الاثنان بالتساوي")], 1, "EMA weights recent prices more.", "الأسي يعطي الأسعار الأخيرة وزناً أكبر."),
         ("A golden cross is when…", "التقاطع الذهبي هو عندما…",
          [("50-day crosses above 200-day", "يعبر متوسط 50 فوق 200"), ("price hits a new high", "يسجل السعر قمة جديدة"), ("gold rises", "يرتفع الذهب")], 0,
          "It's a long-term trend signal.", "إشارة اتجاه طويل المدى."),
         ("Moving averages struggle most in…", "المتوسطات تعاني أكثر في…",
          [("strong trends", "الاتجاهات القوية"), ("sideways markets", "الأسواق العرضية"), ("high volume", "الحجم المرتفع")], 1,
          "Sideways markets cause whipsaws.", "الأسواق العرضية تسبب إشارات كاذبة.")]},

    {"id": "momentum", "art": "osc", "icon": "speed", "level": ("Intermediate", "متوسط"), "mins": 3,
     "title": ("Momentum: RSI & MACD", "الزخم: مؤشر RSI والماكد"),
     "tagline": ("Measure the speed of a move and spot exhaustion early.", "قِس سرعة الحركة واكتشف الإرهاق مبكراً."),
     "sections": [
         ("RSI basics", "أساسيات RSI",
          "The Relative Strength Index measures the speed of recent gains versus losses on a 0–100 scale. Above 70 is often called overbought, below 30 oversold. It's calculated over 14 periods by default.",
          "مؤشر القوة النسبية RSI يقيس سرعة المكاسب الأخيرة مقابل الخسائر على مقياس من 0 إلى 100. فوق 70 يسمى غالباً تشبع شرائي، وتحت 30 تشبع بيعي. يُحسب افتراضياً على 14 فترة.",
          "Overbought is not a sell signal by itself.", "التشبع الشرائي ليس إشارة بيع بحد ذاته.", None),
         ("RSI in trends and divergence", "RSI في الاتجاهات والانحراف",
          "In strong uptrends RSI tends to stay between 40 and 80, so 'overbought' can last for weeks. A more powerful signal is divergence: price makes a higher high but RSI makes a lower high, warning that momentum is fading.",
          "في الاتجاهات الصاعدة القوية يبقى RSI غالباً بين 40 و80، لذلك قد يستمر التشبع الشرائي أسابيع. الإشارة الأقوى هي الانحراف: السعر يسجل قمة أعلى بينما RSI يسجل قمة أدنى، وهذا تحذير بأن الزخم يضعف.",
          "Divergence warns; price action confirms.", "الانحراف يحذّر، وحركة السعر تؤكد.", "rsi_live"),
         ("MACD", "مؤشر الماكد MACD",
          "MACD is the difference between the 12 and 26-period EMAs. A 9-period average of MACD is the signal line, and the histogram shows the gap between them. MACD crossing above its signal line suggests momentum is turning up.",
          "الماكد هو الفرق بين المتوسطين الأسيين 12 و26. ومتوسط الماكد لـ 9 فترات هو خط الإشارة، والهيستوغرام يوضح الفرق بينهما. عبور الماكد فوق خط الإشارة يوحي بأن الزخم يتحول للصعود.",
          "A growing histogram = accelerating momentum.", "الهيستوغرام المتزايد = زخم يتسارع.", None),
         ("Combining signals", "دمج الإشارات",
          "The best setups stack evidence: uptrend (price above the 200-day), a pullback to support, RSI turning up from 40, and a MACD bullish cross. The Scanner page looks for exactly these combinations across 175 stocks.",
          "أفضل الفرص تجمع أكثر من دليل: اتجاه صاعد (السعر فوق متوسط 200)، ارتداد إلى دعم، RSI يصعد من 40، وتقاطع إيجابي للماكد. صفحة صائد الفرص تبحث عن هذه التركيبات في 175 سهم.",
          "More confirmations = fewer but better trades.", "تأكيدات أكثر = صفقات أقل لكنها أفضل.", None)],
     "quiz": [
         ("RSI above 70 is usually called…", "RSI فوق 70 يسمى عادة…",
          [("oversold", "تشبع بيعي"), ("overbought", "تشبع شرائي"), ("neutral", "محايد")], 1, "But it can stay there in strong trends.", "لكنه قد يبقى هناك في الاتجاهات القوية."),
         ("Bearish divergence means…", "الانحراف السلبي يعني…",
          [("price higher high, RSI lower high", "السعر قمة أعلى وRSI قمة أدنى"), ("both make lower lows", "الاثنان قيعان أدنى"), ("volume spikes", "قفزة في الحجم")], 0,
          "Momentum is not confirming the new high.", "الزخم لا يؤكد القمة الجديدة."),
         ("MACD's signal line is…", "خط الإشارة في الماكد هو…",
          [("the 200-day SMA", "متوسط 200 يوم"), ("a 9-period EMA of MACD", "متوسط أسي 9 فترات للماكد"), ("the RSI", "مؤشر RSI")], 1,
          "Crossovers of MACD and its signal line generate signals.", "تقاطع الماكد مع خط الإشارة يعطي الإشارات.")]},

    {"id": "risk", "art": "risk", "icon": "shield", "level": ("Essential", "أساسي"), "mins": 3,
     "title": ("Risk Management & Stop Loss", "إدارة المخاطر ووقف الخسارة"),
     "tagline": ("The skill that separates traders who last from those who don't.", "المهارة التي تفرق بين من يستمر في السوق ومن يخرج منه."),
     "sections": [
         ("Risk first, profit second", "المخاطرة أولاً ثم الربح",
          "Professional traders think about how much they can lose before thinking about how much they can make. A common rule: never risk more than 1–2% of your account on a single trade. With 1% risk you could be wrong 20 times in a row and still keep most of your capital.",
          "المتداول المحترف يفكر في كم ممكن يخسر قبل أن يفكر في كم يربح. القاعدة الشائعة: لا تخاطر بأكثر من 1–2% من محفظتك في صفقة واحدة. مع مخاطرة 1% ممكن تخطئ 20 مرة متتالية وتبقى محافظاً على أغلب رأس مالك.",
          "Protecting capital keeps you in the game.", "حماية رأس المال تبقيك في اللعبة.", None),
         ("Placing a stop loss", "تحديد وقف الخسارة",
          "Put your stop where your trade idea is proven wrong: below support for a long, or below the breakout level. A volatility-based stop uses ATR: for example 1.5–2× ATR below entry, so normal daily noise doesn't knock you out.",
          "ضع وقف الخسارة في المكان الذي تثبت فيه أن فكرتك خاطئة: تحت الدعم في صفقة الشراء أو تحت مستوى الاختراق. والوقف المبني على التذبذب يستخدم مؤشر ATR، مثلاً 1.5 إلى 2 ضعف ATR تحت سعر الدخول حتى لا تخرجك الحركة اليومية العادية.",
          "A stop is decided before entry, never moved further away.", "الوقف يُحدد قبل الدخول ولا يُبعد أبداً.", None),
         ("Position sizing", "حجم الصفقة",
          "Shares to buy = (account × risk %) ÷ (entry − stop). If your account is $10,000, you risk 1% ($100), and entry minus stop is $2, you buy 50 shares. Try the calculator below.",
          "عدد الأسهم = (المحفظة × نسبة المخاطرة) ÷ (سعر الدخول − الوقف). إذا كانت محفظتك 10,000$ وتخاطر بـ 1% (100$) والفرق بين الدخول والوقف 2$، تشتري 50 سهم. جرّب الحاسبة تحت.",
          "Size the position from the stop, not from how confident you feel.", "حدد حجم الصفقة من الوقف، وليس من شعورك بالثقة.", "position_calc"),
         ("Reward-to-risk and the math", "العائد مقابل المخاطرة والحساب",
          "Aim for targets at least 2× your risk (2R). With 2:1 trades you can be right only 40% of the time and still make money. Never average down on a losing trade and never let a small loss become a big one.",
          "استهدف ربحاً لا يقل عن ضعف المخاطرة (2R). مع صفقات 2:1 تقدر تربح بنسبة نجاح 40% فقط وتظل رابحاً. لا تعزز صفقة خاسرة ولا تترك خسارة صغيرة تكبر.",
          "Cut losers fast, let winners run.", "اقطع الخاسرة بسرعة، واترك الرابحة تستمر.", None)],
     "quiz": [
         ("Common max risk per trade is…", "الحد الشائع للمخاطرة في الصفقة الواحدة…",
          [("1–2% of the account", "1–2% من المحفظة"), ("25%", "25%"), ("100% if confident", "100% إذا كنت واثقاً")], 0, "Small risk keeps you in the game.", "المخاطرة الصغيرة تبقيك في السوق."),
         ("$10,000 account, 1% risk, entry $50, stop $48. Shares?", "محفظة 10,000$، مخاطرة 1%، دخول 50$، وقف 48$. كم سهم؟",
          [("20", "20"), ("50", "50"), ("200", "200")], 1, "$100 ÷ $2 = 50 shares.", "100$ ÷ 2$ = 50 سهم."),
         ("With 2:1 reward-to-risk you break even at a win rate of about…", "مع عائد 2:1 تتعادل عند نسبة نجاح تقريباً…",
          [("33%", "33%"), ("50%", "50%"), ("75%", "75%")], 0, "1 win of 2R covers 2 losses of 1R.", "ربح واحد بـ 2R يغطي خسارتين بـ 1R.")]},

    {"id": "value", "art": "value", "icon": "request_quote", "level": ("Intermediate", "متوسط"), "mins": 3,
     "title": ("Valuation Basics: P/E, Growth & Margins", "أساسيات التقييم: مكرر الربحية والنمو والهوامش"),
     "tagline": ("Know whether you're buying a great company at a fair price.", "اعرف هل تشتري شركة ممتازة بسعر عادل."),
     "sections": [
         ("Revenue, earnings and EPS", "الإيرادات والأرباح وربحية السهم",
          "Revenue is what the company sells. Earnings (net income) is what's left after all costs. Divide earnings by the number of shares and you get EPS: earnings per share. Stocks often jump or drop on earnings day when EPS beats or misses expectations.",
          "الإيرادات هي مبيعات الشركة، والأرباح (صافي الدخل) هي المتبقي بعد كل التكاليف. إذا قسمت الأرباح على عدد الأسهم تحصل على ربحية السهم EPS. الأسهم غالباً تقفز أو تهبط يوم إعلان النتائج حسب تجاوز التوقعات أو الفشل فيها.",
          "Markets react to results versus expectations.", "السوق يتفاعل مع النتائج مقارنة بالتوقعات.", None),
         ("The P/E ratio", "مكرر الربحية P/E",
          "Price-to-earnings = share price ÷ EPS. It tells you how many dollars investors pay for $1 of profit. A P/E of 25 means paying $25 for $1 of annual earnings. Forward P/E uses next year's expected EPS.",
          "مكرر الربحية = سعر السهم ÷ ربحية السهم. يوضح كم دولاراً يدفعه المستثمر مقابل دولار واحد من الأرباح. مكرر 25 يعني دفع 25$ مقابل 1$ من الربح السنوي. والمكرر المستقبلي يستخدم أرباح السنة القادمة المتوقعة.",
          "Compare P/E within the same industry, not across industries.", "قارن المكرر داخل نفس الصناعة وليس بين صناعات مختلفة.", "pe_calc"),
         ("Growth, PEG and margins", "النمو ومؤشر PEG والهوامش",
          "A high P/E can be fair if earnings grow fast. PEG = P/E ÷ growth rate; below 1–2 is often considered reasonable. Margins show efficiency: a 25% net margin keeps $25 of every $100 in sales as profit.",
          "المكرر المرتفع قد يكون عادلاً إذا كانت الأرباح تنمو بسرعة. مؤشر PEG = المكرر ÷ معدل النمو، وأقل من 1–2 يعتبر غالباً معقولاً. الهوامش توضح الكفاءة: هامش صافي 25% يعني أن الشركة تحتفظ بـ 25$ من كل 100$ مبيعات كربح.",
          "Growth justifies valuation only if it's sustainable.", "النمو يبرر التقييم فقط إذا كان مستداماً.", None),
         ("Balance sheet health", "صحة الميزانية",
          "Check debt-to-equity and free cash flow. Companies with positive free cash flow can fund growth, buy back shares and pay dividends without borrowing. High debt becomes dangerous when interest rates rise. See the Financials tab of any stock.",
          "راجع نسبة الديون إلى حقوق المساهمين والتدفق النقدي الحر. الشركات ذات التدفق النقدي الحر الإيجابي تستطيع تمويل نموها وإعادة شراء أسهمها ودفع التوزيعات بدون اقتراض. والديون المرتفعة تصبح خطرة عند ارتفاع الفائدة. شوف تبويب المالية في أي سهم.",
          "Cash flow is harder to fake than earnings.", "التدفق النقدي أصعب في التجميل من الأرباح.", None)],
     "quiz": [
         ("Price $100, EPS $4. P/E?", "السعر 100$ وربحية السهم 4$. المكرر؟",
          [("4", "4"), ("25", "25"), ("400", "400")], 1, "100 ÷ 4 = 25.", "100 ÷ 4 = 25."),
         ("A PEG below 1 suggests…", "مؤشر PEG أقل من 1 يوحي بأن…",
          [("growth may be undervalued", "النمو قد يكون مقوماً بأقل من قيمته"), ("the company is bankrupt", "الشركة مفلسة"), ("no dividends", "لا توزيعات")], 0,
          "Valuation is low relative to growth.", "التقييم منخفض مقارنة بالنمو."),
         ("Where should you compare P/E ratios?", "أين تقارن مكررات الربحية؟",
          [("Within the same industry", "داخل نفس الصناعة"), ("Across all stocks equally", "بين كل الأسهم بالتساوي"), ("Only with bonds", "مع السندات فقط")], 0,
          "Industries have very different normal valuations.", "لكل صناعة مستويات تقييم طبيعية مختلفة.")]},

    {"id": "options", "art": "options", "icon": "tune", "level": ("Advanced", "متقدم"), "mins": 3,
     "title": ("Options in 3 Minutes", "عقود الخيارات في 3 دقائق"),
     "tagline": ("Calls, puts, strikes and why most options expire worthless.", "عقود الشراء والبيع وسعر التنفيذ، ولماذا تنتهي أغلب العقود بدون قيمة."),
     "sections": [
         ("What is an option?", "ما هو عقد الخيار؟",
          "An option is a contract that gives the right (not the obligation) to buy or sell 100 shares at a fixed price (the strike) before a date (the expiration). A call profits when the stock rises; a put profits when it falls. You pay a price for this right: the premium.",
          "عقد الخيار يعطيك الحق (وليس الالتزام) في شراء أو بيع 100 سهم بسعر محدد (سعر التنفيذ) قبل تاريخ معين (تاريخ الانتهاء). عقد الشراء Call يربح عندما يرتفع السهم، وعقد البيع Put يربح عندما ينخفض. وتدفع ثمناً لهذا الحق اسمه البريميوم.",
          "One contract = 100 shares, so a $2.00 premium costs $200.", "العقد الواحد = 100 سهم، فالبريميوم 2$ يكلف 200$.", None),
         ("Buying a call", "شراء عقد Call",
          "If you buy a call with a $100 strike for $3, you break even at $103 at expiration. Above that you profit; below $100 you lose the full premium. Move the sliders to see the payoff.",
          "إذا اشتريت عقد Call بسعر تنفيذ 100$ مقابل 3$، نقطة التعادل عند 103$ وقت الانتهاء. فوقها تربح، وتحت 100$ تخسر البريميوم كاملاً. حرّك المؤشرات لتشوف الربح والخسارة.",
          "Max loss when buying options = the premium paid.", "أقصى خسارة عند شراء الخيارات = البريميوم المدفوع.", "payoff"),
         ("Puts for protection", "عقود Put للحماية",
          "A put rises in value when the stock falls, so investors buy puts as insurance for stocks they own. The Put/Call ratio and open interest (shown on every stock's Options tab) reveal how traders are positioned.",
          "عقد Put ترتفع قيمته عندما ينخفض السهم، لذلك يشتريه المستثمرون كتأمين على أسهم يملكونها. نسبة Put/Call والعقود المفتوحة (في تبويب الخيارات لأي سهم) توضح كيف يتمركز المتداولون.",
          "Options can hedge risk, not only speculate.", "الخيارات تستخدم للتحوط وليس فقط للمضاربة.", None),
         ("The risks: time and volatility", "المخاطر: الوقت والتذبذب",
          "Options lose value every day as expiration approaches (time decay, or theta). They're also priced on implied volatility: buying before earnings is expensive because IV is high, and it often collapses after the report. Most options bought by retail traders expire worthless. Start small or paper trade first.",
          "الخيارات تفقد جزءاً من قيمتها كل يوم مع اقتراب الانتهاء (تآكل الوقت أو ثيتا). وتسعيرها يعتمد على التذبذب الضمني: الشراء قبل النتائج مكلف لأن التذبذب مرتفع، وغالباً ينهار بعد الإعلان. أغلب العقود التي يشتريها الأفراد تنتهي بدون قيمة. ابدأ بمبالغ صغيرة أو بحساب تجريبي.",
          "Being right on direction is not enough: timing matters.", "أن تصيب الاتجاه لا يكفي؛ التوقيت مهم.", None)],
     "quiz": [
         ("A call option profits when…", "عقد Call يربح عندما…",
          [("the stock rises above strike + premium", "يرتفع السهم فوق سعر التنفيذ + البريميوم"), ("the stock falls", "ينخفض السهم"), ("nothing happens", "لا يحدث شيء")], 0,
          "That's the breakeven at expiration.", "هذه نقطة التعادل عند الانتهاء."),
         ("One contract with a $1.50 premium costs…", "عقد واحد بريميوم 1.50$ يكلف…",
          [("$1.50", "1.50$"), ("$15", "15$"), ("$150", "150$")], 2, "1.50 × 100 shares.", "1.50 × 100 سهم."),
         ("Time decay (theta) means options…", "تآكل الوقت (ثيتا) يعني أن الخيارات…",
          [("gain value daily", "تكسب قيمة يومياً"), ("lose value as expiration nears", "تفقد قيمة مع اقتراب الانتهاء"), ("never expire", "لا تنتهي")], 1,
          "Time works against option buyers.", "الوقت يعمل ضد مشتري الخيارات.")]},

    {"id": "macro", "art": "macro", "icon": "account_balance", "level": ("Intermediate", "متوسط"), "mins": 3,
     "title": ("How Economic Data Moves Markets", "كيف تحرك البيانات الاقتصادية الأسواق"),
     "tagline": ("CPI, jobs, GDP and the Fed, explained in plain language.", "التضخم والوظائف والناتج المحلي والفيدرالي بلغة بسيطة."),
     "sections": [
         ("The indicators that matter", "المؤشرات المهمة",
          "Four releases move US markets the most: inflation (CPI and PCE), jobs (Nonfarm Payrolls and unemployment), growth (GDP, retail sales) and the Federal Reserve's interest-rate decisions. You can follow all of them on the Economy page.",
          "أربعة إصدارات تحرك السوق الأمريكي أكثر من غيرها: التضخم (CPI وPCE)، الوظائف (الوظائف غير الزراعية والبطالة)، النمو (الناتج المحلي ومبيعات التجزئة)، وقرارات الفيدرالي بشأن الفائدة. تقدر تتابعها كلها في صفحة الاقتصاد.",
          "Inflation and jobs drive the Fed; the Fed drives markets.", "التضخم والوظائف يحركان الفيدرالي، والفيدرالي يحرك الأسواق.", None),
         ("Interest rates and valuations", "الفائدة والتقييمات",
          "When the Fed raises rates, borrowing gets expensive and future profits are worth less today, which hurts high-growth stocks most. Falling rates usually help stocks, especially technology and small caps. Watch the 10-year Treasury yield as a daily barometer.",
          "عندما يرفع الفيدرالي الفائدة يصبح الاقتراض مكلفاً وتقل قيمة الأرباح المستقبلية اليوم، وهذا يضر أسهم النمو أكثر شيء. انخفاض الفائدة عادة يدعم الأسهم خصوصاً التقنية والشركات الصغيرة. راقب عائد السندات لأجل 10 سنوات كمقياس يومي.",
          "Rising yields = pressure on growth stocks.", "ارتفاع العوائد = ضغط على أسهم النمو.", None),
         ("Surprises matter more than numbers", "المفاجأة أهم من الرقم",
          "Markets price in expectations before a release. What moves prices is the surprise: actual versus expected. A strong jobs number can even push stocks down if it makes rate cuts less likely.",
          "السوق يسعّر التوقعات قبل صدور البيانات. ما يحرك الأسعار هو المفاجأة: الفعلي مقابل المتوقع. حتى رقم وظائف قوي قد يهبط بالأسهم إذا قلل احتمال خفض الفائدة.",
          "Always check actual vs expected, not just the headline.", "قارن الفعلي بالمتوقع دائماً، وليس الرقم فقط.", "macro_table"),
         ("Sector rotation", "دوران القطاعات",
          "In expansions, cyclical sectors (technology, industrials, consumer discretionary) tend to lead. When growth slows, investors rotate into defensives (utilities, healthcare, consumer staples). The sector bars on the Overview page show this rotation live.",
          "في فترات التوسع تقود القطاعات الدورية (التقنية والصناعة والسلع الكمالية). وعندما يتباطأ النمو ينتقل المستثمرون للقطاعات الدفاعية (المرافق والرعاية الصحية والسلع الأساسية). أعمدة القطاعات في صفحة النظرة العامة توضح هذا الدوران مباشرة.",
          "Follow the money between sectors.", "تتبع حركة الأموال بين القطاعات.", None)],
     "quiz": [
         ("Rising interest rates usually hurt most…", "ارتفاع الفائدة يضر أكثر…",
          [("high-growth stocks", "أسهم النمو المرتفع"), ("cash", "النقد"), ("nothing", "لا شيء")], 0, "Their value relies on distant future profits.", "قيمتها تعتمد على أرباح مستقبلية بعيدة."),
         ("What moves markets on a data release?", "ما الذي يحرك السوق عند صدور البيانات؟",
          [("The surprise vs expectations", "المفاجأة مقارنة بالتوقعات"), ("The time of day", "وقت الصدور"), ("The data source", "مصدر البيانات")], 0,
          "Expectations are already priced in.", "التوقعات مسعّرة مسبقاً."),
         ("Which are defensive sectors?", "أي القطاعات تعتبر دفاعية؟",
          [("Utilities & staples", "المرافق والسلع الأساسية"), ("Tech & semis", "التقنية وأشباه الموصلات"), ("Crypto miners", "معدّنو العملات الرقمية")], 0,
          "People keep paying bills and buying essentials.", "الناس يستمرون في دفع الفواتير وشراء الضروريات.")]},
]

# (term_en, term_ar, definition_en, definition_ar)
GLOSSARY = [
    ("Ask", "سعر الطلب", "The lowest price a seller will accept.", "أقل سعر يقبله البائع."),
    ("Bid", "سعر العرض", "The highest price a buyer is willing to pay.", "أعلى سعر يرغب المشتري في دفعه."),
    ("Spread", "السبريد", "The gap between bid and ask; a hidden trading cost.", "الفرق بين سعر العرض والطلب، وهو تكلفة تداول خفية."),
    ("Market cap", "القيمة السوقية", "Share price × shares outstanding: the market value of the whole company.", "سعر السهم × عدد الأسهم: قيمة الشركة كاملة في السوق."),
    ("P/E ratio", "مكرر الربحية", "Price ÷ earnings per share: how much you pay for $1 of profit.", "السعر ÷ ربحية السهم: كم تدفع مقابل دولار ربح."),
    ("EPS", "ربحية السهم", "Net income divided by shares outstanding.", "صافي الدخل مقسوماً على عدد الأسهم."),
    ("Dividend yield", "عائد التوزيعات", "Annual dividend ÷ price, as a percentage.", "التوزيعات السنوية ÷ السعر كنسبة مئوية."),
    ("ETF", "صندوق المؤشرات", "A fund that trades like a stock and holds a basket of assets.", "صندوق يتداول مثل السهم ويحتوي سلة من الأصول."),
    ("Index", "المؤشر", "A benchmark that tracks a group of stocks, e.g. the S&P 500.", "مقياس يتتبع مجموعة من الأسهم مثل S&P 500."),
    ("Volume", "حجم التداول", "Number of shares traded in a period.", "عدد الأسهم المتداولة خلال فترة."),
    ("Volatility", "التذبذب", "How much and how fast a price moves.", "مقدار وسرعة تحرك السعر."),
    ("Beta", "بيتا", "Sensitivity to the market: 1.5 means about 1.5× the market's moves.", "حساسية السهم للسوق: 1.5 تعني حركة أكبر بـ 1.5 مرة تقريباً."),
    ("Short selling", "البيع على المكشوف", "Selling borrowed shares to profit from a decline.", "بيع أسهم مقترضة للربح من الانخفاض."),
    ("Short interest", "نسبة البيع على المكشوف", "Shares sold short as a % of the float; high values can fuel squeezes.", "الأسهم المباعة على المكشوف كنسبة من الأسهم الحرة؛ ارتفاعها قد يسبب موجة شراء قسرية."),
    ("Stop loss", "وقف الخسارة", "A pre-set exit price that limits the loss on a trade.", "سعر خروج محدد مسبقاً يحد من الخسارة."),
    ("Take profit", "جني الأرباح", "A pre-set exit price to lock in gains.", "سعر خروج محدد مسبقاً لتثبيت الربح."),
    ("Limit order", "الأمر المحدد", "An order to trade only at a specified price or better.", "أمر يُنفذ فقط بسعر محدد أو أفضل."),
    ("Market order", "أمر السوق", "An order to trade immediately at the best available price.", "أمر يُنفذ فوراً بأفضل سعر متاح."),
    ("Support", "الدعم", "A price zone where declines tend to stop.", "منطقة سعرية يتوقف عندها الهبوط عادة."),
    ("Resistance", "المقاومة", "A price zone where rallies tend to stall.", "منطقة سعرية يتوقف عندها الصعود عادة."),
    ("Moving average", "المتوسط المتحرك", "The average of the last N closing prices, used to spot trends.", "متوسط آخر N إغلاقات، يستخدم لتحديد الاتجاه."),
    ("RSI", "مؤشر القوة النسبية", "Momentum oscillator from 0 to 100; above 70 overbought, below 30 oversold.", "مذبذب زخم من 0 إلى 100؛ فوق 70 تشبع شرائي وتحت 30 تشبع بيعي."),
    ("MACD", "الماكد", "Difference between 12 and 26-period EMAs, used for momentum shifts.", "الفرق بين المتوسطين الأسيين 12 و26 لقياس تغير الزخم."),
    ("ATR", "متوسط المدى الحقيقي", "Average daily trading range; used to size stops.", "متوسط مدى الحركة اليومية؛ يستخدم لتحديد الوقف."),
    ("Breakout", "الاختراق", "Price moving decisively beyond support or resistance.", "تحرك السعر بوضوح خارج الدعم أو المقاومة."),
    ("Call option", "عقد خيار شراء", "The right to buy 100 shares at the strike before expiration.", "حق شراء 100 سهم بسعر التنفيذ قبل الانتهاء."),
    ("Put option", "عقد خيار بيع", "The right to sell 100 shares at the strike before expiration.", "حق بيع 100 سهم بسعر التنفيذ قبل الانتهاء."),
    ("Strike price", "سعر التنفيذ", "The fixed price at which an option can be exercised.", "السعر المحدد الذي يُنفذ عنده العقد."),
    ("Implied volatility", "التذبذب الضمني", "The market's expectation of future volatility, priced into options.", "توقع السوق للتذبذب المستقبلي، ومسعّر داخل الخيارات."),
    ("Open interest", "العقود المفتوحة", "Number of option contracts currently open.", "عدد عقود الخيارات القائمة حالياً."),
    ("Bull market", "السوق الصاعد", "A sustained rise, usually 20%+ from a low.", "صعود مستمر، عادة 20% أو أكثر من القاع."),
    ("Bear market", "السوق الهابط", "A sustained decline of 20% or more from a high.", "هبوط مستمر بنسبة 20% أو أكثر من القمة."),
    ("Drawdown", "التراجع", "The drop from a peak to a trough in value.", "الانخفاض من القمة إلى القاع في القيمة."),
    ("Sharpe ratio", "نسبة شارب", "Return per unit of risk; above 1 is considered good.", "العائد لكل وحدة مخاطرة؛ فوق 1 يعتبر جيداً."),
    ("Backtest", "الاختبار التاريخي", "Testing a strategy on past data to see how it would have performed.", "اختبار استراتيجية على بيانات سابقة لمعرفة أدائها."),
    ("Earnings beat", "تجاوز التوقعات", "Reported EPS above analysts' estimate.", "ربحية سهم معلنة أعلى من توقعات المحللين."),
]


def course_art(kind, uid="a"):
    """Original SVG illustration for course cards (400x150)."""
    g = {"market": ("#1d4ed8", "#7c3aed"), "candles": ("#0f766e", "#1d4ed8"), "levels": ("#7c2d12", "#b45309"), "ma": ("#1e3a8a", "#0891b2"),
         "osc": ("#581c87", "#be185d"), "risk": ("#064e3b", "#0f766e"), "value": ("#1e293b", "#2563eb"), "options": ("#312e81", "#9333ea"),
         "macro": ("#0c4a6e", "#4338ca")}[kind]
    bg = (f'<defs><linearGradient id="g{uid}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{g[0]}"/><stop offset="1" stop-color="{g[1]}"/>'
          f'</linearGradient></defs><rect width="400" height="150" fill="url(#g{uid})"/>'
          + "".join(f'<circle cx="{x}" cy="{y}" r="{r}" fill="#fff" opacity=".06"/>' for x, y, r in ((340, 20, 70), (60, 150, 60), (250, 160, 40))))
    w = "#ffffff"
    art = {
        "market": '<g fill="#fff" opacity=".9"><rect x="60" y="80" width="30" height="50" rx="3"/><rect x="100" y="55" width="30" height="75" rx="3"/>'
                  '<rect x="140" y="95" width="30" height="35" rx="3"/><rect x="180" y="40" width="30" height="90" rx="3"/></g>'
                  f'<path d="M230 110 L270 85 L300 95 L350 45" stroke="{w}" stroke-width="6" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
                  f'<path d="M332 44 L352 42 L350 62" stroke="{w}" stroke-width="6" fill="none" stroke-linecap="round" stroke-linejoin="round"/>',
        "candles": "".join(f'<line x1="{x}" y1="{y - 22}" x2="{x}" y2="{y + h + 18}" stroke="#fff" stroke-width="3"/>'
                           f'<rect x="{x - 10}" y="{y}" width="20" height="{h}" rx="3" fill="{c}"/>'
                           for x, y, h, c in ((70, 70, 40, "#fca5a5"), (110, 60, 30, "#86efac"), (150, 45, 45, "#86efac"), (190, 55, 25, "#fca5a5"),
                                              (230, 35, 50, "#86efac"), (270, 30, 35, "#86efac"), (310, 45, 22, "#fca5a5"), (350, 20, 45, "#86efac"))),
        "levels": '<line x1="30" y1="45" x2="370" y2="45" stroke="#fecaca" stroke-width="3" stroke-dasharray="10 8"/>'
                  '<line x1="30" y1="112" x2="370" y2="112" stroke="#bbf7d0" stroke-width="3" stroke-dasharray="10 8"/>'
                  f'<polyline points="30,100 70,50 110,108 150,52 190,110 230,48 270,106 310,30 360,20" stroke="{w}" stroke-width="5" fill="none" stroke-linejoin="round"/>',
        "ma": f'<polyline points="20,120 60,105 100,112 140,85 180,92 220,65 260,72 300,45 340,52 380,28" stroke="{w}" stroke-width="3" fill="none" opacity=".6"/>'
              '<path d="M20 125 C120 115 200 90 380 45" stroke="#fde68a" stroke-width="5" fill="none"/>'
              '<path d="M20 132 C140 128 240 110 380 75" stroke="#a5f3fc" stroke-width="5" fill="none"/>',
        "osc": '<rect x="30" y="30" width="340" height="90" rx="10" fill="#fff" opacity=".08"/>'
               '<line x1="30" y1="50" x2="370" y2="50" stroke="#fecaca" stroke-dasharray="6 6"/><line x1="30" y1="100" x2="370" y2="100" stroke="#bbf7d0" stroke-dasharray="6 6"/>'
               f'<path d="M30 90 C70 40 100 40 130 70 S190 115 220 95 S280 30 310 45 S350 90 370 80" stroke="{w}" stroke-width="5" fill="none"/>',
        "risk": f'<path d="M200 25 L260 45 L260 85 C260 115 232 132 200 140 C168 132 140 115 140 85 L140 45 Z" fill="#fff" opacity=".92"/>'
                f'<path d="M175 82 L194 100 L228 64" stroke="{g[0]}" stroke-width="9" fill="none" stroke-linecap="round" stroke-linejoin="round"/>',
        "value": '<g fill="#fff"><rect x="70" y="95" width="34" height="35" rx="4" opacity=".7"/><rect x="115" y="75" width="34" height="55" rx="4" opacity=".8"/>'
                 '<rect x="160" y="55" width="34" height="75" rx="4" opacity=".9"/><rect x="205" y="35" width="34" height="95" rx="4"/></g>'
                 '<circle cx="310" cy="75" r="42" fill="#fde68a"/><text x="310" y="90" text-anchor="middle" font-size="44" font-weight="800" fill="#92400e" font-family="Arial">$</text>',
        "options": '<line x1="40" y1="100" x2="370" y2="100" stroke="#fff" stroke-width="2" opacity=".5"/>'
                   f'<polyline points="40,118 210,118 360,25" stroke="{w}" stroke-width="7" fill="none" stroke-linejoin="round"/>'
                   '<circle cx="210" cy="118" r="8" fill="#fde68a"/>',
        "macro": '<circle cx="200" cy="120" r="85" fill="none" stroke="#fff" stroke-width="12" opacity=".25"/>'
                 '<path d="M115 120 A85 85 0 0 1 285 120" fill="none" stroke="#fff" stroke-width="12" stroke-linecap="round" stroke-dasharray="180 400"/>'
                 '<line x1="200" y1="120" x2="255" y2="70" stroke="#fde68a" stroke-width="8" stroke-linecap="round"/><circle cx="200" cy="120" r="10" fill="#fff"/>',
    }[kind]
    return f'<svg viewBox="0 0 400 150" preserveAspectRatio="xMidYMid slice" xmlns="http://www.w3.org/2000/svg">{bg}{art}</svg>'


CANDLE_ANATOMY = """<svg viewBox="0 0 520 240" xmlns="http://www.w3.org/2000/svg" style="width:100%;max-width:560px">
<line x1="140" y1="20" x2="140" y2="220" stroke="#0ECB81" stroke-width="3"/><rect x="115" y="60" width="50" height="110" rx="4" fill="#0ECB81"/>
<line x1="360" y1="20" x2="360" y2="220" stroke="#F6465D" stroke-width="3"/><rect x="335" y="60" width="50" height="110" rx="4" fill="#F6465D"/>
<g font-family="Arial" font-size="13" fill="#E9EDF5">
<text x="175" y="25">{high}</text><text x="175" y="65">{close}</text><text x="175" y="172">{open}</text><text x="175" y="222">{low}</text>
<text x="395" y="25">{high}</text><text x="395" y="65">{open}</text><text x="395" y="172">{close}</text><text x="395" y="222">{low}</text>
<text x="92" y="118" text-anchor="end" fill="#8A94A7">{body}</text><text x="130" y="40" text-anchor="end" fill="#8A94A7">{wick}</text></g>
<g stroke="#8A94A7" stroke-dasharray="3 3"><line x1="145" y1="20" x2="170" y2="20"/><line x1="165" y1="60" x2="170" y2="60"/><line x1="165" y1="170" x2="170" y2="170"/><line x1="145" y1="220" x2="170" y2="220"/>
<line x1="365" y1="20" x2="390" y2="20"/><line x1="385" y1="60" x2="390" y2="60"/><line x1="385" y1="170" x2="390" y2="170"/><line x1="365" y1="220" x2="390" y2="220"/></g>
</svg>"""
