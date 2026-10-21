# Googoo Robo: monetization plan

Written 2026-10-21. This is a plan, not code. Facts were checked against the web in October 2026; numbered references are listed at the bottom. Store rules and prices change, so re-check the official pages right before you submit.

## TL;DR

- **Don't sell the GitHub Pages site.** GitHub Pages doesn't allow commercial or e-commerce use [16]. On the free plan the repo is public, so every paid mp3 can be downloaded anyway. Keep the web version as a **free demo and marketing funnel**.
- **Sell through the App Store and Google Play using a Capacitor wrap of the same code.** Use RevenueCat to handle StoreKit and Play Billing. Ship Android first, because you can build it on this Windows PC; then iOS, with a cloud Mac (Codemagic).
- **Pricing: free core plus one non-consumable "Full Googoo" unlock.** Launch at US$9.99, rising to US$14.99 later. No subscription at launch. Add one only if you start shipping new content every month.
- **The submission blocker is kids-category compliance, not payments.** You need a real parental gate (holding the gear for 2 s isn't one), no third-party requests, a privacy policy, and a licensing audit of the voice clips.
- **Fixed costs are about US$124 in year one** (Apple $99/yr + Google $25 once), plus your ElevenLabs plan. RevenueCat is free until US$2,500/month in revenue.

---

## 1. Web vs native stores

| Option | Can it make money? | Honest verdict |
|---|---|---|
| Stripe Payment Link on GitHub Pages | Technically yes | Not allowed: Pages forbids running "an online business, e-commerce site" [16]. A localStorage unlock is also trivially bypassed, because the files are public. |
| PWA on a paid host (Netlify, Cloudflare Pages) + Stripe or RevenueCat Web Billing [9] | Yes, and only about 3% in fees | Works, but parents don't find or install PWAs, especially on iOS. You'd also need real gating (signed URLs for the paid audio), which means a small server or a RevenueCat entitlement check. Fine as a **second channel later**. |
| **Capacitor wrap, sold in the stores** | Yes, 15% store fee [5] | **Recommended.** Parents trust the stores, Ask to Buy and Family Sharing work, and it's the same code. |

**4.2 "repackaged website" risk.** Apple says an app must offer "features, content, and UI that elevate it beyond a repackaged website" [1]. Googoo Robo is a 3D game with bundled offline assets and the mic, not a wrapped website, so it should pass. Still, bundle **everything** locally, make sure it fully works in airplane mode, and include no browser-like UI or links [2].

**Code changes for the Capacitor wrap.** These are small, because the app is already one page plus `audio/`.
1. Add a Capacitor project (`npx cap init`, plus `android/` and `ios/`). The web root is the output of `tools/build.py`.
2. **Bundle three.js r128 and the font locally.** Today the page loads them from cdnjs and fonts.googleapis.com, which are third-party requests that send the device's IP address. That matters for Kids Category rules ([1] 1.3) and for working offline.
3. **Microphone:** add `NSMicrophoneUsageDescription` (iOS) and `RECORD_AUDIO` (Android). Test `getUserMedia` inside WKWebView early; there are open reports of it failing depending on the hostname or scheme [12]. Also test the `audioSession` play/record switching from HANDOFF, which may not behave the same in WKWebView as in Safari. If the web mic stays flaky, the fallback is a native mic plugin.
4. **Storage:** iOS can purge WKWebView localStorage. Move `pash-stats-v1` to Capacitor Preferences. Entitlements come from RevenueCat, never from localStorage.
5. **Gating:** add an `isUnlocked(feature)` check at the existing entry points (`setRoom`, `showScreen`, the game starters, story/song pickers). Locked items show a padlock badge, and tapping one says a voice line such as "ask Mommy or Daddy". Only after the parental gate do you show the paywall.
6. **Build flag:** the web build skips purchases (free demo plus a store badge behind the gate), and the native build loads the RevenueCat plugin. Keep a single code base.

## 2. Kids store rules: compliance

**Apple Kids Category** [1][3]
- No links out, purchases or other distractions "unless reserved for a designated area behind a parental gate." A gate is an "adult-level task" [3]. Choose the age band **5 and under**.
- No third-party analytics or ads (1.3, 5.1.4). The limited exception doesn't allow IDFA or identifiable data. Developers report Firebase and AppsFlyer rejections [1].
- A privacy policy is required, and you must comply with children's privacy laws (5.1.4) [1].

**Google Play Families policy** [4][13]
- Declare the target audience as under 5. Ads SDKs must be certified (just ship with none). The app must not send AAID or other device identifiers.
- Microphone data counts as **sensitive data from children** and must be disclosed [13]. Because audio is processed on-device and never sent anywhere, the Data safety form can truthfully say "not collected", but the permission still has to be explained.
- Teacher Approved is opt-in after you're compliant [4]. It's worth applying, because it's free discovery.
- New personal developer accounts must run a **closed test with 12 testers for 14 days** before production [15]. Recruit diaspora parents early.

**COPPA (US).** The amended rule's compliance date was 2026-04-22. If you collect children's personal information, you need a written data-retention policy and a written security program [6]. **The best strategy is to collect nothing**: no accounts, no analytics, no server, and audio stays on-device. Then most COPPA duties don't apply, but you still need a privacy policy that says so.

**GDPR-K / UK Children's Code.** For under-13s, the EU consent age is 13–16 depending on the country, and the UK's is 13. The UK Code requires privacy-by-default for all under-18s [11]. The "collect nothing" design satisfies this too. Canada has no COPPA equivalent, but PIPEDA and Quebec Law 25 favour the same minimal-data approach (not researched in depth).

**Age-assurance laws.** Texas SB 2420 has been enforceable since June 2026, via Apple's Declared Age Range API [10]. For a free-to-download app that collects no data, the work mostly falls on the store. Watch for news about significant-change notices.

**What the app already does right**
- No accounts, ads, analytics or server. Stats are on-device only, so you can likely claim "Data Not Collected" on Apple's label.
- Talk-back audio is processed live and never uploaded.
- There's a hidden parent area, there's no text the child needs to read, and wrong answers aren't punished. That's good for Teacher Approved review.

**What has to change**
1. **The parental gate:** a 3-year-old can hold a button for 2 s. Add an adult task, for example "Tap the number **seven**" written as a word under shuffled digits, or a short sum. Put the paywall, restore-purchases, privacy policy link and any store or rating links behind it.
2. **Third-party requests:** cdnjs and Google Fonts must be bundled (see §1).
3. **`name.mp3`** (your son's name) must not ship in the public build.
4. **Branding:** existing lines still say "پاش" while the product is called Googoo Robo. Do the planned re-record before launch, or accept the mismatch.
5. **Content:** regenerate the 11 truncated Robo clips listed in decisions.md.
6. **Paperwork:** write a privacy policy page (hosted anywhere; it can stay on GitHub Pages, since it isn't commerce), and write a mic usage string a parent understands ("Googoo listens so he can repeat your child's words. Sound never leaves this device.").

## 3. In-app purchases

- **Use RevenueCat** with the official Capacitor SDK (`@revenuecat/purchases-capacitor`). It wraps StoreKit 2 and Play Billing and handles receipts and restores without a server. It's **free up to US$2,500 monthly tracked revenue, then 1% of all of it** [7]. Webhooks require the paid tier [7], but you don't need them.
- **Product type: a non-consumable** ("lifetime unlock"). It restores across devices, works with Apple Family Sharing (turn that on), and needs no account. Use one entitlement, `full`, mapped to one product per store.
- **Subscriptions** would need a manage/cancel flow, renewal messaging behind the gate, and continuing content to justify them. Skip them for now. If you add one later, Apple charges 15% from year two regardless of program status [5], and Google charges about 15% [5].
- **Store fees:** enroll in **Apple's Small Business Program** (15% instead of 30% under US$1M) [5]. Google charges 15% under US$1M. Sources disagree on Google's 2026 split (10% service + 5% billing), but the effective rate is about 15% either way [5].
- **Web-to-app entitlements (later):** RevenueCat Web Billing (Stripe as the gateway) plus **Redemption Links** lets a parent buy on the web without an account, then tap a one-time link to unlock the app [9][14].
  - Apple 3.1.3(b) allows web purchases to unlock content in the app, as long as the same item is also offered as an in-app purchase [1].
  - In the US storefront, apps may now link out to web checkout (3.1.1(a)) [1]. Apple's commission on linked-out purchases is still in court, with Supreme Court review pending [8], and in a kids app any such link must sit behind the parental gate anyway. **Not worth building for v1.**

## 4. Pricing

Who pays: Persian-diaspora parents in the US, Canada, the UK, Germany and Australia, a motivated niche. Big competitors such as Lingokids sell subscriptions, but a solo-built app with a fixed content set feels fairer as a one-time purchase, and parents of toddlers are tired of subscriptions.

| Model | Pros | Cons | Verdict |
|---|---|---|---|
| **One-time full unlock** | Simple, trusted, one gate, Family Sharing | Revenue stops after the sale | **Launch with this** |
| Subscription | Recurring; pays ongoing ElevenLabs costs | Needs monthly new content; churn; more review scrutiny | Only once there's a content cadence |
| Content packs | Low entry price | Many purchases, many gates, feels nickel-and-dime for toddlers | Later, as *additions* to the full unlock |

**Recommended prices** (the stores convert to local currencies):
- **Full Googoo:** US$9.99 at launch (about CA$13.99), then US$14.99. After the 15% fee you keep about US$8.49 or US$12.74 per sale. The fixed costs (about US$124 plus the voice plan) break even at roughly 15–30 sales a year.
- **Later packs** (new room, story bundle, robot skins): US$2.99–4.99 each, or included free for Full owners as a goodwill update.
- **Optional later:** "Googoo Club", US$24.99/yr, only if you release new stories and songs monthly.

**What stays free.** It has to be enough that the child loves it and the parent sees the learning.
- The robot, all poke/feed/dance reactions and **talk-back**. Talk-back is the hook, so never paywall it.
- The home room plus about 40 core words (body, family, colours), the Find game, one story and one song.
- **Paid:** the play room and bedroom, all 200+ words, colour hunt, counting, animal sounds, Say it, all stories and songs, robot skins, and the full parent progress view.

## 5. Costs

| Item | Cost | Note |
|---|---|---|
| Apple Developer Program | US$99/yr | Needed for TestFlight and the store |
| Google Play developer | US$25 once | Personal accounts face the 12-tester/14-day rule [15]; an organization account (needs a D-U-N-S number) skips it |
| RevenueCat | US$0 under US$2.5k MTR, then 1% [7] | |
| Store commission | 15% | Apple SBP and Google [5] |
| iOS builds without a Mac | **Codemagic**: 500 free macOS M2 min/month, then about US$0.095/min [17] | Enough for a hobby cadence. **Ionic Appflow shuts down 2027-12-31** [18], so don't start on it. Alternatives: Capawesome Cloud (from about US$9/mo) [18], or a used Mac mini, which pays off if you build a lot. You still need someone with an iPhone to test via TestFlight. |
| ElevenLabs | Your current paid plan (Starter is listed at about US$5–6/mo [19]) | See licensing below |
| Privacy policy and domain | US$0–15/yr | Optional custom domain |

**Licensing: verify before charging money**
- **ElevenLabs:** commercial use needs a paid plan **at the time of generation**. Anything made on the free plan is non-commercial and needs attribution [19][20]. Sources also say **beta features are excluded from commercial use** [19]. Check whether `eleven_v4` was labelled beta when you generated the 1,400 clips, and check your plan history for the first batch. Save the invoices.
- **Eleven Music** (`song_bed.mp3`): confirm its commercial terms separately.
- **Suno** (future sung songs): generate only on a paid plan. Folk rhymes such as اتل متل are traditional, but Suno flagged them. Keep them as your own chanted recordings, which you already do.
- **Tripo/Meshy:** not used (the robot is built in code), so nothing to license. If you add any generated 3D models later, use a paid plan.
- **three.js** is MIT-licensed; keep its licence file in the bundle. Check the font's licence (Google Fonts are typically OFL).
- **Iran:** the stores and Stripe don't serve Iran, so plan no revenue there. This wasn't researched in depth; get advice before taking any payments from there.

## 6. Roadmap

Effort is rough and assumes part-time work with Claude Code.

| Phase | What | Effort |
|---|---|---|
| **0. Clean up** | Parental gate; bundle three.js and the font; remove `name.mp3` from builds; fix the 11 truncated clips; licensing audit; privacy policy page; decide the free/paid split in a `FREE` table | 1–2 weeks |
| **1. Android** | Capacitor wrap; mic and audio test on 2–3 phones; Preferences storage; Play Console; recruit 12 testers and start the 14-day closed test (start this early, because it's the long pole) | 1–2 weeks of work + 2 weeks waiting |
| **2. Purchases** | RevenueCat project; `full` entitlement; paywall screen behind the gate; Restore button; sandbox tests on Android | 1 week |
| **3. iOS** | Apple account; Codemagic pipeline; WKWebView mic fixes; TestFlight with family; App Store Connect (Kids, 5 and under; privacy label; SBP enrollment) | 1–2 weeks + 1–2 review rounds |
| **4. Launch** | Store art (no text-heavy screenshots needed); a short demo video; diaspora parent groups; apply for Teacher Approved; keep the web demo with store badges behind the gate | 1 week |
| **5. Later, only if sales justify it** | Packs and skins; web purchase with Redemption Links; a subscription with a monthly content drop | As needed |

Total is about **6–9 weeks** to both stores, much of it waiting on testers and review.

## Top 5 risks

1. **Kids Category or Families rejection** (gate, third-party requests, mic justification, 4.2 wrapper). *Mitigation:* do Phase 0 properly, make the app fully offline, add no SDKs other than RevenueCat, and explain the on-device mic in the review notes.
2. **Mic and audio behaving differently in WKWebView than in Safari**, and talk-back is the core feature. *Mitigation:* prototype the iOS mic in week 1 of Phase 3, or earlier, with a 1-day spike. Keep a native mic plugin as plan B.
3. **Voice licensing gaps** (free-plan or beta-model clips) forcing a re-record of about 1,400 clips. *Mitigation:* audit now, while a planned re-record is already on the roadmap anyway.
4. **Small market and low conversion.** A niche audience, a free web version that may cannibalize sales, and almost no app-store search traffic for "Farsi toddler". *Mitigation:* a generous free tier as the hook, word of mouth in diaspora communities, and a low launch price. Treat year one as validation, not income.
5. **Compliance drift.** Adding analytics, crash reporting, accounts or a server later quietly switches on COPPA, GDPR-K and store-label obligations [6][11]. *Mitigation:* a written rule that nothing leaves the device without a fresh compliance review. Also watch the age-assurance laws and the external-link commission ruling [8][10].

## References

1. Apple App Review Guidelines (1.3, 3.1.1, 3.1.1(a), 3.1.3(b), 4.2, 5.1.4): https://developer.apple.com/app-store/review/guidelines/
2. MobiLoud, App Store guidelines for webview wrappers: https://www.mobiloud.com/blog/app-store-review-guidelines-webview-wrapper
3. Apple, Kids apps (parental gates, age bands): https://developer.apple.com/app-store/kids-apps/
4. Google Play Families policy: https://support.google.com/googleplay/android-developer/answer/9893335 and https://android-developers.googleblog.com/2022/11/helping-kids-and-families-find-high-quality-apps-for-kids.html
5. Store commissions: https://www.revenuecat.com/blog/engineering/small-business-program and https://splitmetrics.com/blog/google-play-apple-app-store-fees/ and https://pricepush.app/glossary/service-fee
6. Amended COPPA Rule, compliance 2026-04-22: https://toyassociation.org/PressRoom2/News/2026-News/updated-coppa-rule-requirements-take-effect-april-22.aspx and https://www.whitecase.com/insight-alert/unpacking-ftcs-coppa-amendments-what-you-need-know
7. RevenueCat pricing: https://www-docs.revenuecat.com/pricing and https://production-docs.revenuecat.com/docs/welcome/set-up-revenuecat/account-management
8. Apple external-link commission litigation: https://www.iclarified.com/101778/apple-seeks-court-approval-for-15-commission-on-external-app-purchases and https://thenextweb.com/news/supreme-court-apple-epic-contempt-app-store-commission
9. RevenueCat Web Billing: https://www.revenuecat.com/docs/web/revenuecat-billing
10. Texas SB 2420 and Declared Age Range: https://9to5mac.com/2026/06/03/apple-says-texas-app-store-age-assurance-rules-start-tomorrow-after-court-ruling/
11. GDPR Art. 8 and UK age of consent: https://data.parliament.uk/DepositedPapers/Files/DEP2025-0065/GDPR_age_of_consent_and_parental_controls.pdf and https://www.cpduk.co.uk/news/protection-children-data-protection-law-comparative-analysis-eu-gdpr-and-uk-gdpr
12. WKWebView getUserMedia issues with Capacitor: https://bugs.webkit.org/show_bug.cgi?id=259304 (reported via onbugs.webkit.org) and https://developer.apple.com/forums/thread/134216
13. Google Play Families data practices (mic is sensitive data): https://support.google.com/googleplay/android-developer/answer/9893335?hl=en-GB
14. RevenueCat Redemption Links: https://www.revenuecat.com/docs/web/redemption-links
15. Google Play testing requirement for new personal accounts: https://support.google.com/googleplay/android-developer/answer/14151465
16. GitHub Pages limits (no commercial use): https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits
17. Codemagic pricing: https://docs.codemagic.io/billing/pricing.md
18. Appflow shutdown and alternatives: https://capawesome.io/alternatives/ionic-appflow/ and https://capgo.app/blog/appflow-shutdown-alternative
19. ElevenLabs commercial terms: https://terms.law/ai-output-rights/elevenlabs/ and https://bigvu.tv/blog/elevenlabs-pricing-2026-plans-credits-commercial-rights-api-costs/
20. ElevenLabs help, publishing generated content: https://elevenlabs.io/docs/help-center/legal/can-i-publish-the-content-i-generate-on-the-platform/llms.txt
