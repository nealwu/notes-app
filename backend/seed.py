import sqlite3
from datetime import datetime, timedelta

DATABASE = "notes.db"

notes = [
    {
        "title": "standup mar 3",
        "content": "project aurora update - backend team blocked on db migration, scripts work locally but keep timing out in staging (dataset is way bigger there). frontend ahead of schedule on dashboard, sarah finishing the filter panel\n\naction items\n- sarah: migration staging env w/ realistic dataset by wed\n- mike: review PR #342 (caching layer)\n- me: write tech spec for notification system before next standup\n- devops: figure out why staging db connections maxing out during migration\n\nalso talked about team offsite, probably week of april 14. need to finalize by friday for travel booking",
        "tags": "meeting,aurora,team",
    },
    {
        "title": "react perf tips",
        "content": "things to remember:\n- useMemo for expensive computations but dont overuse it, memo itself has a cost\n- React.memo for components that rerender with same props, especially list items\n- useCallback for stable function refs passed to memoized children\n- lazy loading with React.lazy() + Suspense, should be doing this for every route\n- virtualize long lists - react-window or react-virtuoso (virtuoso has nicer api but heavier)\n\ngot 40% render improvement on dashboard after memo + virtualization. main bottleneck was activity feed rerendering 500+ items on every state change, after virtualizing we only render ~20 visible\n\nalso look into:\n- react devtools profiler\n- why-did-you-render library\n- zustand or jotai instead of context for frequently changing state",
        "tags": "react,frontend,performance",
    },
    {
        "title": "q2 roadmap brainstorm",
        "content": "features to consider:\n1. search across all content - most requested by far. users cant find anything, even basic keyword search would be huge. ideally semantic/smart search\n2. ai writing assistant - autocomplete, grammar, tone. claude or gpt-4 apis. medium effort high value\n3. collab features (realtime editing) - big lift, need to evaluate crdts vs ot. probably q3. yjs looks good\n4. mobile app - lots of demand but offline sync is hard. maybe start with responsive pwa?\n5. api for 3rd party integrations - enterprise customers asking for this\n\nsearch keeps coming up in support tickets, counted 23 mentioning search/findability last month. should be top priority for q2\n\nalso need to factor in tech debt - notification system is fragile and weve been putting off the db migration for 2 quarters",
        "tags": "product,roadmap",
    },
    {
        "title": "postgres docker setup",
        "content": "quick ref:\n\ndocker run --name my-postgres -e POSTGRES_PASSWORD=secret -p 5432:5432 -d postgres:15\n\nconnect: psql -h localhost -U postgres\n\npersistent data:\ndocker run --name my-postgres -e POSTGRES_PASSWORD=secret -v pgdata:/var/lib/postgresql/data -p 5432:5432 -d postgres:15\n\nuseful psql:\n\\l - list databases\n\\dt - list tables\n\\d+ tablename - describe with details\n\\x - toggle expanded display\n\nreset everything: docker rm -f my-postgres && docker volume rm pgdata\n\nfor docker-compose see infra/docker-compose.dev.yml",
        "tags": "docker,postgres",
    },
    {
        "title": "acme corp meeting",
        "content": "met with their vp eng + 2 senior devs about api integration\n\nwhat they want:\n- rest api with oauth2 (asked specifically about pkce for their spa)\n- webhooks for doc created/updated/shared events\n- rate limiting 1000 req/min per key, higher tiers available\n- batch endpoints for bulk ops (they do 500+ record updates regularly)\n- python and js sdks nice to have\n\ntimeline: working prototype by end of q2. budget flexible if we hit deadline. theyre evaluating a competitor too but prefer our ux\n\ntheir concerns:\n- pagination for large result sets (50k+ items)\n- idempotency keys for posts? theyve been burned by dupe creates\n- webhook delivery sla - need ordering + at-least-once guarantees\n\nnext: ill draft api spec by next wed. followup meeting march 15",
        "tags": "meeting,client,acme",
    },
    {
        "title": "memory leak in workers",
        "content": "BUG: background workers eating memory, ~50mb/hour. after 12hrs they get OOM killed and we lose tasks\n\ninvestigation:\n- started after deploying v2.3.1 tuesday\n- used memory_profiler to trace\n- top growth in sqlalchemy.pool.QueuePool\n\nroot cause: creating new db connections per task but not closing on exceptions. pool grows unbounded:\n\n    conn = get_connection()\n    result = do_work(conn)  # if this throws, conn leaks\n    conn.close()\n\nfix: try/finally + max_connections limit (was unlimited, set to 20)\n\nfixed in PR #287, deployed to staging. memory stable at ~200mb for 48hrs. prod deploy thursday\n\nTODO: add memory metric to monitoring dashboard (filed JIRA-1124)",
        "tags": "bug,backend",
    },
    {
        "title": "DDIA reading notes",
        "content": 'ch 3 - storage & retrieval:\n- lsm trees vs b-trees: lsm better for write heavy (append only, sequential), b-trees for read heavy (in-place updates)\n- sstables used by leveldb, rocksdb, cassandra\n- WAL for crash recovery\n- column storage for analytics - only read cols you need, better compression\n- oltp vs olap distinction\n\nch 5 - replication:\n- leader based: one leader writes, followers replicate async\n- sync vs async followers. most systems semi-sync (one sync, rest async)\n- read-after-write consistency is what users expect ("i just saved this why cant i see it")\n- monotonic reads: wont see time go backward across replicas\n\nch 7 - transactions:\n- ACID is basically a marketing term lol, implementations vary wildly\n- serializable isolation strongest but most expensive\n- write skew and phantoms only appear under certain isolation levels\n\nneed to reread partitioning and batch processing chapters',
        "tags": "books,distributed-systems",
    },
    {
        "title": "pasta recipe",
        "content": "2 cups 00 flour (all purpose ok but 00 is silkier)\n3 eggs\n1 tbsp olive oil\npinch salt\n\nmound flour, well in center, crack eggs in, add oil + salt. fork to gradually mix flour from inner wall. knead 10 min til smooth and elastic (should bounce back when you poke it). wrap in plastic, rest 30 min room temp - DONT SKIP this, gluten needs to relax\n\ndivide into 4, roll thin (setting 5-6 on pasta machine). cut to shape - fettuccine ~1/4 inch, tagliatelle ~3/8, pappardelle ~3/4\n\ntips:\n- dough should feel like playdoh. too dry = wet your hands slightly. too sticky = dust flour\n- for ravioli roll thinner, should almost see your hand thru it\n- fresh pasta cooks in 2-3 min, done when it floats\n- can dry on rack 30min or freeze on sheet pan then bag it\n\nvariations: 1 tbsp tomato paste for red, or blend handful basil/spinach for green (reduce to 2 eggs + 2-3 tbsp puree)",
        "tags": "recipe,cooking",
    },
    {
        "title": "event driven vs request response",
        "content": 'need to decide communication patterns for new microservices. currently monolith w/ sync internal calls\n\nevent driven (kafka/rabbitmq):\n+ better decoupling, services dont need to know about each other\n+ natural audit trail\n+ handles spikes via buffering\n+ easy to add new consumers\n- complex debugging, tracing across async events is hard\n- eventual consistency ("i just did X why dont i see it")\n- ordering, dedup, dead letter queues\n- harder to reason about system state\n\nrequest-response (rest/grpc):\n+ simpler mental model\n+ immediate feedback\n+ easier to debug\n+ transactions straightforward\n- tight coupling\n- cascading failures\n- hard to scale independently\n- latency in deep call chains\n\nDECISION: hybrid. rest/grpc for sync queries (loading pages, submitting forms). events for async state changes (emails, search index updates, analytics)\n\nstart with rabbitmq (simpler than kafka at our scale), migrate later if needed. use correlation IDs everywhere for tracing',
        "tags": "architecture,decisions",
    },
    {
        "title": "llm lessons learned",
        "content": 'from building the doc Q&A feature:\n\n1. chunking matters MORE than the model. switched from fixed 500-token chunks to semantic chunking (paragraph/section boundaries) and results got way better. 10-15% overlap between chunks important too\n\n2. always show source citations. users dont trust answers without them. also helps us debug bad answers\n\n3. streaming responses feel 10x faster even if total time is same. user satisfaction went up a lot when we switched\n\n4. cache embeddings aggressively. $0.0001/1k tokens adds up w/ millions of chunks. store in postgres w/ pgvector, only recompute when source changes\n\n5. prompt engineering is iterative. v5 was way better than v1. key wins: "if you dont know say so" (reduced hallucination ~60%), including doc titles in context, explicit output format\n\n6. "ai generated, may contain errors" disclaimer goes a long way. added thumbs up/down feedback too\n\n7. context window mgmt is tricky. rank chunks by relevance, fit as many as possible. re-ranking with cross-encoder after initial retrieval helped a lot\n\n8. have a fallback - when model cant answer confidently, show top matching chunks as search results instead',
        "tags": "ai,llm",
    },
    {
        "title": "ML feature ideas",
        "content": 'brainstorm from thursdays meeting:\n\n- semantic search: embeddings to find by meaning not keywords. user searches "how to handle errors" finds "exception handling patterns" even tho it doesnt contain "errors". most impactful thing we could build\n- auto-categorization: classify items into topics. could be simple (tfidf + logreg) or llm zero-shot. good for organizing without manual tags\n- smart suggestions: "you might also like" based on content similarity. pairwise similarity + top-K\n- summarization: tldr for long docs or across collections. map-reduce for stuff exceeding context window\n- anomaly detection: flag unusual patterns. more enterprise analytics, not sure it fits us\n- sentiment analysis: tone across customer feedback. could help w/ support ticket triage\n\npriority: semantic search, highest impact lowest effort. prototype in 2-3 sprints with openai embeddings + pgvector or faiss. search is #1 user complaint\n\nill write up technical design doc by next wednesday',
        "tags": "ml,product,brainstorm",
    },
    {
        "title": "career chat w/ manager",
        "content": 'want to move toward tech lead in next year. manager says opportunities are there but need to show more cross-team leadership + technical vision\n\nneed more experience with system design and mentoring. suggested leading design reviews, writing more rfcs\n\nshould volunteer to lead api redesign - touches multiple services, requires coordination with platform team. good visibility\n\n"senior engineers are distinguished by ability to influence through writing not just code" - need to write more design docs\n\nbook recs: staff engineer (will larson), an elegant puzzle (same author), managers path (camille fournier)\n\naction items:\n- talk to dir of eng about leading api redesign\n- set up weekly 1:1s with alex (new junior dev) for mentoring\n- write caching architecture proposal as RFC\n- sign up for eng all-hands talk\n\nreflection: biggest gap is im too heads-down in code. need to zoom out, think about team priorities, find problems before theyre assigned, speak up more in meetings',
        "tags": "career,1on1",
    },
    {
        "title": "git commands i forget",
        "content": 'git log --oneline --graph --all\ngit log --author="Neal" --since="2 weeks ago"\ngit stash -u  (include untracked)\ngit stash pop\ngit cherry-pick <hash>\ngit bisect start/bad/good\ngit reflog  (find lost commits)\ngit diff --stat\ngit diff --cached  (staged changes)\ngit rebase -i HEAD~3\ngit clean -fd  (DANGEROUS)\ngit log -p -- path/to/file\ngit blame -L 10,20 file.py\ngit shortlog -sn  (commit count by author)\n\nless common:\ngit worktree add ../feature-branch feature-branch\ngit diff branch1...branch2\ngit rev-parse --short HEAD\ngit commit --fixup=<hash> && git rebase -i --autosquash\n\nmy aliases:\nco = checkout\nbr = branch\nst = status\nlg = log --oneline --graph --all --decorate',
        "tags": "git,reference",
    },
    {
        "title": "aurora retro",
        "content": "what went well:\n- delivered on time despite scope changes\n- good cross-team collab (shoutout devops + qa)\n- new ci/cd pipeline: deploy time 30min -> 5min (wasnt even in scope lol)\n- caching layer: p95 latency 800ms -> 200ms\n- zero P0 bugs first week\n\nwhat sucked:\n- requirements changed 3x mid-sprint, product spec wasnt detailed enough at kickoff. should have pushed back harder\n- not enough automated tests, manual qa was bottleneck last 2 weeks. delayed release 3 days\n- db migration massively underestimated (2 weeks instead of 3 days). data was dirtier than expected\n- communication w/ design broke down week 3, they changed figma and we didnt notice til code review\n\naction items:\n- freeze reqs after sprint planning. changes go to next sprint unless P0\n- mandate 80% coverage for new code, set up ci gates\n- migration estimates: always 3x the initial estimate\n- shared slack channel w/ design + weekly syncs\n- write tech spec BEFORE coding, not during",
        "tags": "retro,aurora",
    },
    {
        "title": "sourdough",
        "content": "500g bread flour (or 400 bread + 100 whole wheat for more flavor)\n350g water (70% hydration, adjust for flour/humidity)\n100g active starter (should be bubbly, doubled in 4-8hrs after feeding)\n10g salt\n\n9am - mix flour + water only, autolyse 30min\n9:30 - add starter + salt, squeeze thru fingers to mix, stretch and fold in bowl\n10-2pm - bulk ferment at room temp (~75-78F). stretch and fold every 30min for first 2hrs (4 sets, each set is 4 folds NSEW). dough should feel stronger after each set\n2pm - preshape: turn onto unfloured surface, round w/ bench scraper. rest 20min\n2:20 - final shape: flip, fold edges to center, flip seam down, drag w/ scraper for tension\n2:30 - seam up into floured banneton (rice flour is best). cover, fridge 12-18hrs\n\nnext morning:\n- preheat oven 500F w/ dutch oven inside, at least 45min\n- turn onto parchment, score w/ razor at 30deg angle\n- into dutch oven on parchment\n- 20min covered at 500\n- remove lid, 450, 20-25min more til deep golden\n- cool on wire rack AT LEAST 1hr (inside is still cooking!!)\n\ntroubleshooting:\n- dense/gummy = underfermented, bulk longer or warmer spot\n- flat/spreads = overfermented or weak shaping\n- no ear = blade not sharp enough or angle too steep\n\nthe overnight cold ferment is what gives it good flavor. dont skip it",
        "tags": "recipe,baking",
    },
    {
        "title": "tokyo trip planning",
        "content": "dates: may 15-25 (tentative)\n\nflights: check google flights for LAX->NRT vs LAX->HND. HND is closer to city center but NRT has more options. budget ~$800-1000 rt\n\naccommodation:\n- shinjuku area is good base, central to everything\n- look at hotel gracery shinjuku or hyatt regency\n- ryokan for 1-2 nights? hakone is close and has onsens\n- budget ~$150-200/night\n\nmust do:\n- tsukiji outer market (go early for fresh sushi)\n- teamlab borderless (or planets? check which is better)\n- meiji shrine + harajuku area\n- akihabara for electronics\n- shibuya crossing at night\n- day trip to kamakura (great buddha, hiking trails)\n- golden gai for tiny bars\n\nfood:\n- ramen: fuunji (tsukemen) in shinjuku, ichiran for solo dining\n- sushi: check tabelog not google reviews\n- conveyor belt sushi for casual meals\n- 7-eleven onigiri is actually amazing lol\n- try yakitori alley under the train tracks in yurakucho\n\nneed to get:\n- pocket wifi or esim (ubigi?)\n- suica/pasmo card for trains\n- cash - japan is still pretty cash heavy\n- JR pass? only worth it if doing day trips outside tokyo\n\nreminder: golden week is may 3-6, might still be crowded around then",
        "tags": "travel,japan",
    },
    {
        "title": "apartment stuff todo",
        "content": "- call landlord about the leak under kitchen sink (getting worse)\n- schedule dryer vent cleaning, hasnt been done in 2 yrs\n- get quotes for replacing living room blinds, the vertical ones are awful\n- bathroom caulk is peeling around tub, need to redo\n- look into getting a bidet attachment (toto washlet or tushy?)\n- figure out why bedroom outlet stopped working. might be tripped breaker?\n- renters insurance renewal is april 15, compare rates this time\n\nfurniture:\n- need a proper desk, current one is too small. ikea bekant or uplift standing desk?\n- bookshelf for office, the books are just in piles on the floor\n- new couch eventually, current one is shot but thats a big purchase\n\nwifi has been terrible in the bedroom, maybe get a mesh system? eero or tp-link deco",
        "tags": "home,todo",
    },
    {
        "title": "gift ideas",
        "content": "mom birthday (april 2):\n- she mentioned wanting a nice cutting board, check etsy for walnut ones\n- kindle paperwhite? she reads a lot but idk if shed use it\n- cooking class together could be fun\n\ndad:\n- needs new running shoes but idk his size lol\n- that book about woodworking he mentioned\n\nsarah (her bday is sometime in may?? check):\n- shes really into pottery lately, maybe a class or supplies\n- nice candle set\n\nalex wedding gift (june 15):\n- check registry\n- budget ~$150",
        "tags": "gifts,personal",
    },
    {
        "title": "workout routine",
        "content": "current split (3 days/wk, trying to be consistent)\n\nmonday - push:\n- bench press 4x8\n- overhead press 3x10\n- incline db press 3x10\n- lateral raises 3x15\n- tricep pushdowns 3x12\n\nwednesday - pull:\n- deadlifts 4x5\n- barbell rows 4x8\n- pull ups 3x max\n- face pulls 3x15\n- bicep curls 3x12\n\nfriday - legs:\n- squats 4x8\n- romanian deadlifts 3x10\n- leg press 3x12\n- walking lunges 3x10 each\n- calf raises 4x15\n\ntrying to hit 150g protein/day. protein shake after workout + high protein meals\n\ncurrent maxes (january):\n- bench: 185\n- squat: 245\n- deadlift: 315\n\ngoal by summer: 200/275/350",
        "tags": "fitness,personal",
    },
    {
        "title": "books to read",
        "content": "fiction:\n- project hail mary (andy weir) - everyone says its great\n- the three body problem - been on my list forever\n- klara and the sun (ishiguro)\n- piranesi (susanna clarke) - sarah recommended\n\nnonfiction:\n- staff engineer (will larson) - manager recommended\n- thinking fast and slow - classic, never actually read it\n- the making of the atomic bomb - supposedly amazing\n- breath by james nestor\n- why we sleep (matthew walker)\n\ncurrently reading: designing data intensive applications (slowly... its dense)",
        "tags": "books,personal",
    },
    {
        "title": "car stuff",
        "content": "oil change overdue!! was supposed to do it at 45k, currently at 47.2k\nneed to schedule asap, go to the valvoline on main st (no appointment needed)\n\nalso:\n- passenger side wiper streaking, need to replace both\n- registration renewal due june, check if i can do it online\n- that weird rattle from the dashboard is back when its cold. dealer said they couldnt reproduce it last time ugh\n- need to get winter tires off, its march already\n- check tire pressure, low tire light was on last week but went away?\n\ninsurance renewal in august, shop around this time. paying $180/mo feels high for a 2019 civic",
        "tags": "car,todo",
    },
    {
        "title": "doctor visit notes",
        "content": "annual physical march 1\n\neverything mostly fine. blood pressure slightly elevated (132/85), dr said keep an eye on it, probably stress + caffeine. should aim for under 120/80\n\nblood work results:\n- cholesterol total: 195 (borderline, want under 200)\n- ldl: 118 (want under 100 ideally)\n- hdl: 52 (ok but could be higher)\n- a1c: 5.4 (normal)\n- vitamin d: 22 (low! need to supplement, 2000 IU daily)\n\nrecommendations:\n- reduce sodium and saturated fat\n- more cardio (at least 150min/wk moderate intensity)\n- vitamin d supplement\n- come back in 6 months for bp recheck\n- schedule dermatologist for that mole on my back\n\nnext appt: september (set a reminder!!)",
        "tags": "health,personal",
    },
    {
        "title": "podcast recs from mike",
        "content": '- hardcore history (dan carlin) - really long episodes but amazing. start with "blueprint for armageddon" about ww1\n- lex fridman - good tech/ai interviews but theyre like 3 hours each lol\n- acquired - deep dives on companies. the nvidia episode was great\n- huberman lab - neuroscience stuff, practical health tips\n- 99% invisible - design and architecture\n- the daily - for news, short episodes\n\nalso he mentioned a youtube channel called veritasium thats really good for science stuff',
        "tags": "podcasts,recommendations",
    },
    {
        "title": "new laptop research",
        "content": 'current macbook pro is 2019, getting slow. options:\n\nmacbook pro 14" m3 pro:\n- 18gb ram, 512gb ssd: ~$2000\n- great battery, great screen\n- can run all my dev stuff easily\n- 36gb ram option is $2400 tho\n\nmacbook air 15" m3:\n- $1500 for 16gb/512gb\n- lighter, fanless\n- might not be enough for docker + multiple services\n\nframework laptop:\n- cool concept, modular/repairable\n- linux support is good\n- but i rely on some mac-only stuff (imessage, airdrop)\n\nprobably going m3 pro 14" with 36gb ram. expensive but itll last 4-5 years. can sell current one for maybe $400-500\n\nwait for wwdc in june? new chips might drop prices on current gen',
        "tags": "tech,shopping",
    },
    {
        "title": "onboarding checklist template",
        "content": "day 1:\n- laptop + accounts (github, slack, jira, aws, datadog)\n- clone repos: main-app, api-service, infra, docs\n- run setup script (./scripts/setup-dev.sh)\n- meet with buddy/mentor\n- read team norms doc\n\nweek 1:\n- read architecture overview, understand request flow frontend -> db\n- local dev env + all tests passing\n- first PR (well assign a starter bug)\n- attend standup + sprint planning\n- shadow a prod deploy\n- set up datadog dashboard\n\nmonth 1:\n- own a small feature end to end\n- lightning talk on something learned\n- 1:1 with each team member\n- review 5+ PRs\n- read incident runbooks\n\nmonth 2-3:\n- join oncall rotation (w/ buddy first time)\n- lead a sprint planning\n- contribute to a design doc/rfc\n- propose one improvement to tooling or process",
        "tags": "onboarding,team",
    },
    {
        "title": "db migration plan",
        "content": "mysql -> postgres migration:\n\n1. pgloader for schema + data migration. handles most type conversions auto (tinyint(1)->boolean, datetime->timestamp etc). manual: enums, json->jsonb, fts indexes\n2. dual-write both dbs for 2 weeks. reads from mysql still. verify postgres handles write load\n3. nightly consistency checks - row counts + hash comparisons\n4. switch reads to postgres, keep dual-write. watch query perf (postgres better at complex joins/CTEs, might be slower on heavy GROUP BY)\n5. monitor 1 week - slow queries, connection pool, replication lag\n6. cut over writes to postgres only (point of no return)\n7. keep mysql read-only 1 month then decommission\n\nrisks:\n- 12 stored procs need rewriting, billing one is complex (budget 2 days)\n- mysql-specific queries: GROUP_CONCAT->STRING_AGG, IFNULL->COALESCE, backticks->double quotes\n- auto_increment vs serial/identity\n- ORM handles most differences but 14 files have raw sql, need manual review\n\nrollback: replay postgres WAL to rebuild mysql. keep dual-write code 2 weeks after cutover",
        "tags": "database,migration",
    },
    {
        "title": "restaurants to try",
        "content": 'from various recommendations:\n\n- osteria mozza (italian, $$$) - mikes favorite, need reservations\n- jitlada (thai) - apparently the spiciest thai in the city. ask for "thai spicy"\n- pine & crane (taiwanese) - casual, sarah says the three cup chicken is amazing\n- bestia (italian/industrial) - been wanting to go forever, always booked\n- guerrilla tacos - fancy tacos, sounds weird but supposedly incredible\n- konbi (japanese sandwiches) - always a line but worth it for the egg sandwich\n- republique (brunch) - go on weekday to avoid insane wait\n\nalready tried and loved:\n- petit trois - french, the omelette is life changing no joke\n- howlin rays - hot chicken, the wait is brutal but so good\n- sushi gen - lunch special is best deal in the city',
        "tags": "food,restaurants",
    },
    {
        "title": "tax stuff 2024",
        "content": "deadline april 15\n\nneed to gather:\n- w2 from work (should be in workday)\n- 1099-INT from savings accounts (ally, hysa)\n- 1099-DIV from brokerage\n- 1098 for student loan interest\n- receipts for home office deduction?? ask accountant if this applies to me\n\ncontributions:\n- maxed 401k ($23,000)\n- roth ira: $7,000 (did i do this?? check fidelity)\n- hsa: $3,850\n\nuse turbotax or switch to freetaxusa this year? turbotax is getting expensive for what it is. mike swears by freetaxusa\n\nreminder: estimated tax payments if freelance income > $1k (did some consulting in q4)\n\nTODO: schedule call with accountant by end of march",
        "tags": "taxes,finance",
    },
    {
        "title": "meeting notes - product sync",
        "content": 'weekly sync w/ product team\n\nlaunch update:\n- search feature pushed to april (was march), need more testing\n- mobile app beta going out next week to 50 users\n- enterprise sso is done but need security review\n\nmetrics review:\n- activation rate dropped 3% this month. probably the onboarding change we made? should revert or iterate quickly\n- support tickets up 15% mostly about search/findability (surprise surprise)\n\ndecisions:\n- killing the "smart folders" feature, nobody uses it. redirecting eng resources to search\n- adding a feedback widget to the app, just a simple thumbs up/down on features\n\nnext week: user research readout on search behaviors. block your calendars',
        "tags": "meeting,product",
    },
    {
        "title": "camping gear checklist",
        "content": "for big sur trip (april 19-21)\n\nshelter/sleep:\n- tent (check if stakes are all there from last time)\n- sleeping bags x2\n- sleeping pads\n- pillow\n\ncooking:\n- camp stove + fuel canister\n- lighter/matches\n- pot, pan, utensils\n- cooler + ice\n- water filter or purification tabs\n- coffee!! dont forget the coffee. and the aeropress\n\nfood plan:\n- night 1: burgers + corn on cob\n- day 2 breakfast: scrambled eggs, bacon, toast on camp stove\n- day 2 dinner: chili (make ahead, just reheat)\n- snacks: trail mix, jerky, fruit, granola bars\n\nclothes:\n- layers!! big sur gets cold at night even in april\n- rain jacket just in case\n- hiking boots\n- flip flops for camp\n\nother:\n- headlamps (with fresh batteries)\n- first aid kit\n- bug spray\n- trash bags\n- firewood (buy near campsite, dont bring from home - invasive species)\n- camp chairs\n- bluetooth speaker\n\nreservation confirmation #: BSP-44821\nsite 73 at pfeiffer big sur. check in after 2pm",
        "tags": "camping,travel",
    },
    {
        "title": "random project ideas",
        "content": "things id like to build when i have time (lol):\n\n1. personal finance dashboard - pull data from plaid api, visualize spending patterns, set budgets. might already exist but i want to customize it\n\n2. recipe scaler - input a recipe url, it parses ingredients and lets you scale to different serving sizes. could use llm to parse unstructured recipe text\n\n3. bookmark manager w/ auto-tagging - i have 2000 bookmarks and zero organization. save url, auto-extract content, generate tags and summary\n\n4. local-first notes app - like obsidian but custom. crdt-based sync, markdown, works offline. ok this is basically a 6 month project lol\n\n5. workout tracker that actually shows progressive overload trends. most apps suck at visualization\n\n6. email client that auto-categorizes and prioritizes. probably impossible to make better than gmail but the idea is fun",
        "tags": "ideas,projects",
    },
    {
        "title": "python asyncio stuff",
        "content": "patterns i keep forgetting:\n\ngather:\nresults = await asyncio.gather(task1(), task2(), task3())\nuse return_exceptions=True so one failure doesnt cancel everything\n\nsemaphore for rate limiting:\nsem = asyncio.Semaphore(10)\nasync with sem: await do_work()\nessential for external apis\n\nqueue for producer-consumer:\nqueue = asyncio.Queue(maxsize=100)  # bounded for backpressure\nawait queue.put(item)\nitem = await queue.get()\nqueue.task_done()  # dont forget!!\nawait queue.join()\n\ntimeout:\ntry:\n    result = await asyncio.wait_for(coro(), timeout=5.0)\nexcept asyncio.TimeoutError:\n    handle_timeout()\n\ntaskgroup (3.11+):\nasync with asyncio.TaskGroup() as tg:\n    tg.create_task(coro1())\n    tg.create_task(coro2())\npreferred way for structured concurrency now\n\nGOTCHA: never create_task() without keeping a reference. gc can cancel unreferenced tasks silently",
        "tags": "python,async",
    },
    {
        "title": "movies to watch",
        "content": "- past lives - heard its beautiful, celine song\n- oppenheimer - still havent seen it lol\n- the holdovers - paul giamatti\n- poor things - yorgos lanthimos\n- anatomy of a fall - french courtroom drama\n- all of us strangers - andrew scott\n- the zone of interest - about the holocaust but from a unique angle\n- american fiction - supposed to be really funny\n\nalready watched and loved recently:\n- killers of the flower moon - long but incredible\n- bottoms - stupid funny\n- godzilla minus one - surprisingly emotional??\n\ntv:\n- shogun (FX) - everyone at work wont shut up about it\n- the bear season 2 - need to finish\n- beef - already watched but would rewatch",
        "tags": "movies,tv,personal",
    },
    {
        "title": "budget march",
        "content": "income: $7,200 (after tax/401k/etc)\n\nfixed:\n- rent: $2,100\n- utilities: ~$120\n- internet: $60\n- phone: $45\n- car insurance: $180\n- car payment: $350\n- student loans: $280\n- subscriptions: ~$80 (spotify, netflix, nyt, gym, icloud)\ntotal fixed: ~$3,215\n\nvariable:\n- groceries: $400 budget (been going over, need to meal plan)\n- eating out: $300 budget (this is where i always blow it)\n- gas: $120\n- misc/fun: $200\ntotal variable: ~$1,020\n\nsavings goal: $1,500/month\n- $500 to roth ira\n- $500 to emergency fund (want to hit 6 months by end of year)\n- $500 to travel fund\n\nthat leaves ~$1,465 buffer which never feels like enough. need to cut eating out honestly. been spending like $500+ on restaurants lol",
        "tags": "finance,budget",
    },
    {
        "title": "rest api design notes",
        "content": 'team guidelines:\n\nurls: nouns for resources (/users, /notes not /getUsers). nested for relationships (/users/123/notes). plural consistently. lowercase with hyphens\n\nmethods: GET read, POST create, PUT full replace, PATCH partial update (prefer this), DELETE remove\n\nresponses:\n- errors: { error: { code: "NOT_FOUND", message: "...", details: {} } }\n- collections: { data: [...], meta: { total, page } } (never bare arrays)\n- return resource in body for POST/PUT/PATCH\n- 201 creation, 200 update, 204 deletion\n\npagination: cursor-based for large/changing collections, offset for small/stable. always include { next_cursor, has_more } or { total, page, per_page }\n\nversioning: /api/v1/ url prefix (simplest). header-based is more "correct" but harder to debug\n\nauth: bearer tokens, short-lived access (15min) + refresh tokens. api keys for server-to-server\n\nother:\n- iso 8601 dates always\n- filtering via query params: /notes?tag=python&created_after=2024-01-01\n- rate limit everything, return limits in X-RateLimit-Limit + X-RateLimit-Remaining headers',
        "tags": "api,best-practices",
    },
    {
        "title": "pragmatic programmer notes",
        "content": 'key takeaways from re-read:\n\n- DRY: not just code, its about knowledge duplication. same business rule in 2 places = guaranteed to get out of sync. auto-generate docs from code where possible\n\n- tracer bullets: build thin end-to-end slices early. instead of all DB then all API then all UI, build one feature all the way through. surfaces integration problems early\n\n- rubber duck debugging: explaining problem out loud reveals the solution. actually works, ive solved bugs mid-sentence lol\n\n- broken windows: fix bad code early or it spreads. one hacky workaround = permission for more. clean codebase = social pressure to keep it clean\n\n- good enough software: know when to stop polishing. users needs > developer perfectionism\n\n- orthogonality: keep components independent. if changing A requires changing B theyre not orthogonal. test: can you unit test each in isolation?\n\n- reversibility: make decisions easy to change. interfaces, config, abstraction layers. not over-engineering, just not painting yourself into corners\n\n- estimating: orders of magnitude first (days? weeks? months?). break into smaller tasks. track estimates vs actuals to calibrate\n\n"care about your craft. why spend your life developing software unless you care about doing it well"',
        "tags": "books,engineering",
    },
    {
        "title": "sleep stuff",
        "content": "been sleeping terribly. researching fixes:\n\n- no screens 1hr before bed (yeah right... but at least use night shift/f.lux)\n- bedroom should be cold, 65-68F\n- consistent sleep/wake time even on weekends (this is the hardest one)\n- no caffeine after 2pm\n- magnesium glycinate before bed? some studies show it helps\n- blackout curtains - mine let in too much light from the street\n- white noise machine or app\n\nordered from amazon:\n- blackout curtains (should arrive tuesday)\n- magnesium glycinate supplement\n- sleep mask as backup\n\nalso want to try the huberman lab sleep cocktail: mag threonate + theanine + apigenin. sounds like bro science but lots of people swear by it\n\nif nothing works maybe see a sleep specialist. insurance should cover it",
        "tags": "health,sleep",
    },
    {
        "title": "interview prep notes (for giving interviews)",
        "content": "things ive noticed from giving interviews lately:\n\n- best signal comes from open-ended problems, not leetcode gotchas\n- watch for: do they clarify requirements before diving in? do they think about edge cases? can they communicate their thinking?\n- let awkward silences happen, dont rush to fill them. candidates need time to think\n- take notes DURING the interview not after. details fade fast\n- its ok if they dont finish. how they approach it matters more than completion\n- red flags: cant explain their own code, gets defensive about feedback, doesnt ask questions\n- green flags: asks good clarifying questions, considers tradeoffs, admits when they dont know something, iterates on their solution\n\nneed to write up our new interview question for the product eng role. want something open-ended where they improve an existing app",
        "tags": "interviewing,team",
    },
    {
        "title": "garden plan spring",
        "content": "raised bed layout (4x8 ft):\n- tomatoes on the north side so they dont shade everything (cherry + beefsteak)\n- basil next to tomatoes (companion planting, supposedly helps)\n- peppers (jalapeno + bell) middle row\n- lettuce and spinach on south edge (partial shade from peppers is fine)\n- herbs in pots on the patio: rosemary, thyme, mint (NEVER plant mint in the bed, it takes over everything)\n\nschedule:\n- start seeds indoors: mid march (tomatoes, peppers) - USE THE GROW LIGHT this time, last years seedlings were leggy\n- transplant outdoors: after last frost, probably mid april\n- direct sow: lettuce, spinach, radishes late march\n\ntodo:\n- buy seed starting mix + trays\n- check if drip irrigation timer still works from last year\n- add compost to raised bed, its compacted from winter\n- order seeds: burpee or baker creek\n\nlearned from last year: dont plant too close together. i crammed everything in and got tons of fungal issues from poor airflow",
        "tags": "garden,personal",
    },
    {
        "title": "team offsite planning",
        "content": "offsite week of april 14 (mon-wed probably)\n\nvenue options:\n- that coworking space in santa monica sarah found - $500/day, has breakout rooms\n- just use the office but order nice food? boring but free\n- airbnb somewhere? could be fun but logistics are harder\n\nagenda ideas:\n- half day: team building / fun activity (escape room? cooking class? hiking?)\n- half day: q2 planning and prioritization\n- half day: hack time on something fun / exploratory\n- team retro (bigger picture than sprint retros)\n- optional dinner monday night\n\nbudget: need to check with finance. probably $200-300/person total?\n\nlogistics:\n- 12 people total\n- 3 remote (fly them in? or just zoom them in for the work sessions)\n- dietary restrictions: mike is vegetarian, priya is gluten free\n\ntodo: send out a poll for date preferences and activity votes by end of this week",
        "tags": "team,planning,offsite",
    },
    {
        "title": "coffee notes",
        "content": "dialing in the new grinder (baratza encore)\n\nfor pour over (v60):\n- 15g coffee : 250g water\n- grind: medium fine (setting 14-16 on encore)\n- 205F water\n- bloom with 2x coffee weight (30g) for 30sec\n- pour in circles, total brew time should be ~3:00-3:30\n- if sour: grind finer or hotter water\n- if bitter: grind coarser or cooler water\n\nfor aeropress:\n- 17g coffee : 220g water\n- grind: medium (setting 18-20)\n- inverted method: steep 1:30, flip and press\n- james hoffmann method is good too but more involved\n\nbeans i like:\n- counter culture hologram (good everyday, chocolate + citrus)\n- onyx southern weather (more interesting, berry notes)\n- local roasters: check out that new place on 5th street\n\nstore beans in airtight container, use within 3 weeks of roast date. freezing is ok for long term if you vacuum seal",
        "tags": "coffee,personal",
    },
    {
        "title": "typescript utility types",
        "content": "cheat sheet:\n\nPartial<T> - all props optional\nRequired<T> - all props required\nPick<T, K> - select specific props: Pick<User, 'id' | 'name'>\nOmit<T, K> - remove props: Omit<User, 'password'>\nRecord<K, V> - object type: Record<string, number>\nReturnType<T> - extract function return type\nParameters<T> - extract function params as tuple\nExclude<T, U> - remove from union: Exclude<'a'|'b'|'c', 'a'> = 'b'|'c'\nExtract<T, U> - keep intersection of unions\nNonNullable<T> - remove null/undefined\nReadonly<T> - all props readonly\n\nconditional: T extends U ? X : Y\ntemplate literal: `${string}-${number}` matches 'foo-42'\nmapped: { [K in keyof T]: Transform<T[K]> }\ninfer: T extends Promise<infer U> ? U : T\n\npatterns:\n- DeepPartial<T>: recursive optional (not built in but easy)\n- branded types: type UserId = string & { __brand: 'UserId' }\n- discriminated unions: { ok: true, data: T } | { ok: false, error: Error }\n\nuse `satisfies` (ts 5.0+) for type checking without widening",
        "tags": "typescript,reference",
    },
    {
        "title": "quarterly review prep",
        "content": "q1 numbers:\n\ngrowth:\n- mau up 23% (12k -> 14.8k), mostly organic + word of mouth\n- wau up 31% - engagement growing faster than signups, good sign\n- free to paid conversion: 4.2% (was 3.1%)\n\nperformance:\n- api p95 down 800ms -> 340ms (caching + query optimization)\n- uptime 99.94% (missed 99.95% sla by one incident, march 3 redis outage)\n- error rate 0.12% (was 0.31%)\n\nbusiness:\n- churn 5.2% -> 3.8% (new onboarding + proactive support)\n- nps 42 (was 35). detractors mainly cite search and no mobile app\n- mrr $47.2k (was $38.1k)\n- 3 enterprise deals: acme ($2.4k/mo), techstart ($1.8k/mo), global systems ($3.2k/mo)\n\nwins: shipped realtime collab, reduced onboarding time 40%, closed enterprise deals\nchallenges: mobile delayed 6wks, still hiring sr backend (3 months open), search is still #1 complaint\n\nq2 priorities: search improvements, mobile launch, soc2, api for integrations",
        "tags": "business,quarterly-review",
    },
    {
        "title": "local dev env setup",
        "content": 'for new machines (mac):\n\n1. homebrew: /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"\n2. brew install git node python docker && brew install --cask visual-studio-code iterm2\n3. ssh keys: ssh-keygen -t ed25519, add to github\n4. clone repos: main-app, api-service, infra, docs\n5. nvm: brew install nvm && nvm install 20 && nvm alias default 20\n6. pyenv: brew install pyenv && pyenv install 3.12 && pyenv global 3.12\n7. docker desktop - bump memory to 4gb (default 2gb isnt enough for full stack)\n8. vscode extensions: eslint, prettier, python, gitlens, docker, copilot, error lens\n9. shell: brew install zsh-autosuggestions zsh-syntax-highlighting\n\ncopy .env.example -> .env and fill in local values. ask someone for shared dev api keys\n\nthen run ./scripts/setup-dev.sh from main-app. starts docker containers (postgres, redis, elasticsearch), runs migrations, seeds test data',
        "tags": "devops,setup",
    },
    {
        "title": "concert schedule",
        "content": "upcoming shows:\n\n- japanese breakfast @ the wiltern, march 22 (bought tickets!!! sec 204 row B)\n- boygenius @ the forum, april 5 (SOLD OUT. check stubhub closer to date, willing to pay up to $150)\n- khruangbin @ hollywood bowl, may 18 (on sale march 15, set alarm)\n- tyler the creator @ something, summer? tba\n\npast shows this year:\n- mitski january - incredible, cried lol\n- lcd soundsystem february - so much fun, danced the whole time\n\nneed to check:\n- is coachella worth it this year? lineup seems mid but its always fun. weekend 2 is cheaper",
        "tags": "music,personal",
    },
    {
        "title": "docker networking debug",
        "content": "containers cant reach each other by service name? checklist:\n\n1. same docker network? docker network ls / docker network inspect\n2. docker-compose: services auto-join <project>_default network. separate compose files = separate networks, use explicit external network\n3. dns check: docker exec container1 nslookup container2\n4. firewall? check iptables, docker manages its own chains but custom rules can interfere\n5. listening on 0.0.0.0 not 127.0.0.1? this is THE most common issue\n   docker exec container2 netstat -tlnp\n6. EXPOSE is documentation only, doesnt publish port. need -p or ports: in compose. but container-to-container uses internal port not mapped host port\n7. health checks: use depends_on with condition, otherwise container1 starts before container2 is ready\n\nfix is almost always: change bind address to 0.0.0.0 (flask run --host=0.0.0.0, uvicorn --host 0.0.0.0)",
        "tags": "docker,debugging",
    },
    {
        "title": "meal prep ideas",
        "content": "trying to stop ordering uber eats every day. goal: prep on sunday for the week\n\nbatch cooking:\n- big pot of chili or curry (lasts 4-5 days, freezes well)\n- rice in rice cooker (keeps in fridge ~4 days)\n- roasted vegetables: sweet potato, broccoli, bell peppers. toss in olive oil, 400F 25min\n- protein: bake chicken thighs (seasoned with whatever) or ground turkey\n\nquick lunches:\n- grain bowls: rice + roasted veg + protein + sauce (tahini or sriracha mayo)\n- wraps: tortilla + whatever is in the fridge\n- big salad with lots of protein\n\nbreakfasts:\n- overnight oats: oats + milk + chia seeds + fruit. make 3-4 jars sunday night\n- egg muffin cups: eggs + spinach + cheese in muffin tin, bake 20min at 350. grab and go\n\nsnacks: hard boiled eggs, hummus + veggies, fruit, mixed nuts, string cheese\n\nthe key is making it easy enough that its less effort than ordering food. if its too complicated i wont do it",
        "tags": "cooking,meal-prep",
    },
    {
        "title": "spanish learning",
        "content": 'been using duolingo for 3 months, 90 day streak! but i can barely have a conversation lol\n\nsupplementing with:\n- language transfer (podcast/app) - really good for understanding grammar intuitively\n- dreaming spanish (youtube) - comprehensible input method. just watch and listen, dont study\n- changed my phone language to spanish\n- trying to think in spanish during the day\n\nvocab im always forgetting:\n- todavia = still/yet\n- ya = already\n- sin embargo = however\n- desarrollar = to develop (lol same root as english)\n- realizar vs darse cuenta (both mean "to realize" but different contexts)\n- por vs para... honestly still confused about this\n\ngoal: have a basic conversation by the tokyo trip... wait thats japanese lol. ok by end of summer. maybe take a class or find a language exchange partner on tandem',
        "tags": "spanish,learning,personal",
    },
    {
        "title": "neural nets refresher",
        "content": "basics:\n- perceptron: output = f(w*x + b), weighted sum + activation\n- MLP: stacked fully connected layers. universal approx theorem = single hidden layer can approximate any continuous function (but might need exponentially many neurons)\n- backprop: chain rule for gradients, update weights to reduce loss\n\nactivations:\n- relu: max(0,x) most common. simple, fast. downside: dead neurons\n- leaky relu: max(0.01x, x) fixes dead neuron problem\n- sigmoid: 1/(1+e^-x) for binary classification output\n- softmax: probability distribution for multiclass\n- gelu: used in transformers\n\nloss: mse for regression, cross-entropy for classification, contrastive for embeddings\n\noptimizers: sgd (simple but finicky), adam (usually default, adaptive lr per param), adamw (decoupled weight decay, used in llm training)\n\nregularization: dropout (zero out neurons randomly), l2/weight decay, batchnorm (stabilize training), layernorm (preferred in transformers)\n\nlr scheduling: cosine annealing, warmup + linear decay (critical for transformers), reduce on plateau\n\nkey insight: most practical improvements come from data quality not model architecture",
        "tags": "ml,deep-learning",
    },
    {
        "title": "call with mom",
        "content": 'talked to mom sunday\n\n- dad\'s knee surgery went well, hes doing physical therapy 3x/week. says it hurts but hes already walking better\n- cousin lisa is pregnant! due in august\n- they might sell the house and downsize?? this is big news. said theyre just "thinking about it" but sounded pretty serious\n- she wants me to come visit for easter (march 31). check flights or maybe drive, its only 5hrs\n- she asked about my job for the 100th time, tried to explain what i do. she said "so you make websites?" lol close enough\n- reminder: call aunt carol for her birthday march 20',
        "tags": "family,personal",
    },
    {
        "title": "morning routine (aspirational lol)",
        "content": "trying to build a consistent morning routine instead of doomscrolling in bed for 30min\n\n6:30 - wake up (alarm across the room so i have to get up)\n6:35 - glass of water\n6:40 - 10 min meditation (headspace app)\n6:50 - quick workout or stretching (even just 15 min)\n7:10 - shower\n7:30 - breakfast (overnight oats or eggs, not just coffee)\n7:45 - review calendar + plan the day\n8:00 - start work on the hardest task first (eat the frog)\n\ncurrently doing:\n6:30 - alarm goes off\n6:30-7:15 - snooze / phone / reddit\n7:15 - panic, shower\n7:30 - coffee, no food\n7:45 - open laptop, check slack/email for 30min before doing anything useful\n\n... work in progress",
        "tags": "personal,habits",
    },
]


def seed():
    conn = sqlite3.connect(DATABASE)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            tags TEXT DEFAULT '',
            created_at TEXT,
            updated_at TEXT
        )
    """
    )

    # Clear existing notes
    conn.execute("DELETE FROM notes")

    base_time = datetime(2025, 1, 15, 9, 0, 0)
    for i, note in enumerate(notes):
        t = base_time + timedelta(days=i * 2, hours=i % 12)
        conn.execute(
            "INSERT INTO notes (title, content, tags, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (
                note["title"],
                note["content"],
                note["tags"],
                t.isoformat(),
                t.isoformat(),
            ),
        )

    conn.commit()
    print(f"Seeded {len(notes)} notes.")
    conn.close()


if __name__ == "__main__":
    seed()
