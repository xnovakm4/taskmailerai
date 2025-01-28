# rate_limiter.py

import os
import json
import time
from threading import Lock

class RateLimiter:
    def __init__(self, stats_file='rate_limit_stats.json'):
        self.stats_file = stats_file
        self.lock = Lock()
        self.load_stats()

    def load_stats(self):
        if os.path.exists(self.stats_file):
            with open(self.stats_file, 'r') as file:
                self.stats = json.load(file)
        else:
            self.stats = {}

    def save_stats(self):
        with self.lock:
            with open(self.stats_file, 'w') as file:
                json.dump(self.stats, file)

    def is_allowed(self, user_email, max_requests, time_window):
        current_time = int(time.time())
        user_stats = self.stats.get(user_email, {"request_count": 0, "window_start": current_time})

        # Kontrola, zda jsme stále v časovém okně
        if current_time - user_stats['window_start'] >= time_window:
            # Resetujeme počítadlo a začneme nové okno
            user_stats['request_count'] = 1
            user_stats['window_start'] = current_time
        else:
            # Zvýšíme počítadlo
            user_stats['request_count'] += 1

        # Uložíme zpět statistiky
        self.stats[user_email] = user_stats
        self.save_stats()

        # Ověříme, zda uživatel nepřekročil limit
        if user_stats['request_count'] > max_requests:
            return False
        else:
            return True

    def get_time_until_reset(self, user_email, time_window):
        current_time = int(time.time())
        user_stats = self.stats.get(user_email, {"window_start": current_time})
        time_passed = current_time - user_stats['window_start']
        return max(0, time_window - time_passed)