import os
import random
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

DATABASE_PATH = Path(
    os.getenv("TEAM_MOOD_DATABASE_PATH", "data/team_mood_tracker.sqlite3")
).expanduser()


def seed_data():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS mood_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user TEXT NOT NULL,
                mood TEXT NOT NULL,
                rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
                comment TEXT,
                created_at TEXT NOT NULL
            )
            """)

        users = ["Alex", "Maria", "Kirill", "Ilsaf", "Vladimir", "Ravil"]
        moods = {1: "stressed", 2: "sad", 3: "neutral", 4: "good", 5: "happy"}

        # Clear existing
        conn.execute("DELETE FROM mood_entries")

        records = []
        today = datetime.now(timezone.utc)

        for day_offset in range(35, -1, -1):
            current_date = today - timedelta(days=day_offset)

            # 3 to 6 entries per day
            num_entries = random.randint(3, 6)

            for _ in range(num_entries):
                # Create a trend: slightly worse 7 days ago, better recently
                base_rating = random.choice([2, 3, 4])
                if day_offset > 10:
                    base_rating = random.choice([4, 5])
                elif day_offset > 5:
                    base_rating = random.choice([1, 2, 3])
                else:
                    base_rating = random.choice([3, 4, 5])

                # add some noise
                rating = min(5, max(1, base_rating + random.choice([-1, 0, 1])))
                user = random.choice(users)
                mood = moods[rating]

                # Random time within that day
                hour = random.randint(9, 18)
                minute = random.randint(0, 59)
                entry_date = current_date.replace(
                    hour=hour, minute=minute, second=0, microsecond=0
                )

                records.append(
                    (
                        user,
                        mood,
                        rating,
                        f"Sample comment for {rating}/5",
                        entry_date.isoformat(),
                    )
                )

        cursor = conn.executemany(
            """
            INSERT INTO mood_entries (user, mood, rating, comment, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            records,
        )
        print(
            f"Successfully inserted {cursor.rowcount} mock mood entries spanning the last 36 days."
        )


if __name__ == "__main__":
    seed_data()
