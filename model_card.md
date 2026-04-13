# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name  
 **SpotiVibe v1**  

---

## 2. Intended Use  

SpotiVibe v1 is a content-based music recommender that suggests songs from a small catalog based on a user's stated preferences. Given a taste profile (preferred genre, mood, energy level, and acoustic preference), it scores each song in the catalog and returns the top matches ranked by relevance.

The system assumes that a user's taste can be captured by four fixed attributes and that those preferences stay constant across a listening session. It does not learn from feedback, adapt over time, or account for context like time of day or activity.

This **is not** intended for real users or production deployment. Its purpose is to lay the groundwork for understanding of rule-based scoring and weighted features can approximate the behavior of a real recommendation system. Due to the limited dataset, the model is liable to bias.

---

## 3. How the Model Works  

SpotiVibe v1 works by comparing each song in the catalog against a user's taste profile and assigning it a score between 0 and 1. The higher the score, the better the match. Songs are then sorted by score and the top results are returned.

Each song is evaluated across four features:

**Genre** — the simplest check: does the song's genre match what the user prefers? It's either a full match or no match at all. This accounts for 40% of the final score.

**Mood** — a two-part check. First, does the mood label match (e.g. "chill" vs "relaxed")? Second, how positive does the song sound, measured by a property called valence? A happy mood should pair with a high-valence song. The mood label carries 70% of this sub-score and valence carries 30%. Together, mood accounts for 25% of the final score.

**Energy** — how closely does the song's intensity match what the user wants? This isn't just raw energy — it also factors in how fast the song is (tempo) and how danceable it is, since all three contribute to how energetic a song feels. This composite check accounts for 25% of the final score.

**Acousticness** — does the song fit the user's acoustic preference? Songs with an acousticness above 0.5 are considered acoustic; below 0.5 is considered electronic or produced. This is a simple yes/no check and accounts for 10% of the final score.

Compared to the starter logic, the main changes were: adding composite sub-features for mood (valence) and energy (tempo, danceability) to make scoring more nuanced and replacing the acoustic continuous gradient with a binary zone check.

---

## 4. Data  

The catalog contains 20 songs stored in `data/songs.csv`. The dataset started with 10 songs provided in the starter project, and 10 additional songs were AI-generated to expand coverage and improve testing across edge case profiles.

Each song includes the following attributes: title, artist, genre, mood, energy, tempo (BPM), valence, danceability, and acousticness.

**Genres represented:** pop, lofi, rock, ambient, synthwave, jazz, indie pop (7 total)

**Moods represented:** happy, chill, intense, relaxed, focused, moody (6 total)

The dataset is heavily skewed toward certain combinations — for example, there are no pop songs with a relaxed or chill mood, and no jazz songs with a happy mood. This means users with preferences that don't align with common genre/mood pairings in the catalog will rarely get a high-scoring match.

There are also notable gaps in musical taste the dataset does not cover: no hip-hop, R&B, classical, country, or electronic genres are included. The catalog likely reflects a narrow slice of taste — leaning toward indie, study music, and workout genres — which limits how broadly the recommender can serve different kinds of listeners.

---

## 5. Strengths  

The system works best for users whose preferences align cleanly with the catalog's genre/mood combinations — for example, a lofi/chill/low-energy/acoustic listener will consistently get well-matched recommendations because several songs in the catalog fit that profile precisely. Similarly, a jazz/relaxed listener benefits from multiple matching songs and a scoring formula that rewards acousticness and moderate energy together.

The composite energy scoring is one of the stronger design decisions. By blending raw energy, tempo, and danceability into a single score, the system captures the "feel" of a song's intensity more accurately than raw energy alone. Two songs with similar energy values but very different tempos will score differently against the same user target, which better reflects how those songs actually sound.

The acousticness zone check (above or below 0.5) is simple and interpretable — the rule is easy to reason about. If a user says they like acoustic music, the system clearly rewards songs above the threshold and penalizes those below, with no ambiguity.

The plain-language explanation output adds transparency — users can see exactly which features contributed to a recommendation, which is something many real-world recommenders intentionally obscure.

---

## 6. Limitations and Bias 

Based on my experiments, I noticed that the model had a significant bias in genre. Like I mentioned previously in the Experiments section, when I ran my "Genre Intruder" profile, it placed an over-emphasis on genre, when there were better recommendations that didn't fit the genre. Although balancing the weights helped, if this feature was rolled out in a real world recommender, a user who values energy over genre would consistently receive off-target recommendations with no way to signal that preference — since the weights are fixed for every user regardless of their actual taste shape.

The system also ignores several features that real recommenders rely on: lyrics, artist familiarity, listening history, context (time of day, activity), and song duration. A user studying late at night and a user at the gym could have the same energy target but need completely different recommendations — the system has no way to distinguish them.

Genres outside the catalog (hip-hop, R&B, classical, country) are structurally broken for any user who prefers them. Their genre score will always be 0, meaning they are effectively penalized 30% on every single song before mood or energy are even considered.

The composite energy formula also has a subtle bias toward higher-tempo songs. Because tempo and danceability are blended into the energy score, songs with moderate raw energy but fast tempos will score higher than their energy value alone would suggest. A user with a very low energy target (e.g. 0.0) will always be penalized since the composite can never reach 0.

Finally, the hardcoded `MOOD_VALENCE` map assumes universal emotional associations — for example, that "happy" always corresponds to a valence of 0.80. These mappings were set based on intuition and may not reflect how all listeners experience mood in music, making the system less reliable for users whose emotional associations differ from those assumptions.

---

## 7. Evaluation  

Four user profiles were tested, each designed to probe a specific weakness in the scoring logic:

**The Impossible Profile** (`pop / relaxed / energy 0.71 / acoustic`): This is the primary taste profile used throughout development. No song in the catalog satisfies both "pop" and "acoustic" simultaneously — pop songs in the dataset have acousticness between 0.05 and 0.18. The expected behavior was for jazz and lofi songs to surface instead, since they match mood, energy, and acousticness better. This confirmed that the system degrades gracefully when preferences conflict: it finds the best available match rather than returning nothing.

**The Energy Paradox** (`lofi / chill / energy 0.0 / acoustic`): Tested whether the composite energy formula unfairly penalizes songs that should be good matches. Because the composite blends raw energy with normalized tempo and danceability, even the chillest songs in the dataset have a composite energy above 0.0. This revealed that the formula subtly disadvantages users with extreme low-energy preferences.

**The Genre Intruder** (`synthwave / chill / energy 0.40 / acoustic`): This was the most revealing test. Night Drive Loop (synthwave) ranked first despite matching poorly on mood, energy, and acousticness — purely because the genre weight was high enough to overcome mismatches elsewhere. This directly led to rebalancing the weights from 0.40/0.25/0.25/0.10 to 0.30/0.30/0.30/0.10 so that mood and energy carry equal importance to genre.

**The Valence Trap** (`jazz / happy / energy 0.40 / acoustic`): Tested whether partial valence credit inside the mood composite could silently inflate scores for songs with no mood label match. Since no jazz song in the dataset is labeled "happy," this profile exposed how valence similarity alone can give a misleading boost to songs that feel wrong for the stated mood.

The most surprising finding was how a single weight imbalance in genre caused a structurally incorrect ranking across multiple profiles — and how a small adjustment (dropping genre from 0.40 to 0.30) meaningfully changed which songs surfaced at the top.

---

## 8. Future Work 

The first change I would make would be to balance out the weights. During my experiments, I noticed that there was a heavy bias on genre, so I would even out the split from 0.40/0.25/0.25/0.10 to 0.30/0.30/0.30/0.10.

I was also considering that for my Final Project, to truly make recommendation system AI-driven, I would refactor it (especially the scoring algorithm) into an ML algorithm. The biggest issue with the current implementation is that all teh weights are fixed. All this does is mimic what an AI-recommmendation system *should* be like. However, I would hundreds, maybe even thousands more songs to be able to be functional. It would also be cool if the recommendation system also used real songs. 

---

## 9. Personal Reflection  

Personally, from this Show assignment, I was able to learn a little more about how real recommendation system worked (especially the likes of Spotify / Tiktok). The most interesting/unexpected thing I discovered was just how reliant the recommender was on the data it is provided. The limited dataset was good enough for a learning exercise, but its nowhere good enough for a real production-level system. This project changed the way I look at recommendation systems because I never really thought about exactly **how** the data it was given impacts its recommendations. Now I will always be thinking about how and why Spotify chose the song it recommended for me in Discover Weekly (lol)