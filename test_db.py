import os
import unittest
import database
import config

class TestDatabase(unittest.TestCase):
    def setUp(self):
        # Use a temporary test db
        config.DB_NAME = "test_movies.db"
        database.DB_NAME = "test_movies.db"
        database.init_db()

    def tearDown(self):
        if os.path.exists("test_movies.db"):
            os.remove("test_movies.db")

    def test_user_management(self):
        database.add_or_update_user(12345, "john_doe", "John")
        self.assertEqual(database.get_user_count(), 1)
        self.assertEqual(database.get_all_users(), [12345])

    def test_movie_catalog(self):
        movie_id = database.add_movie(
            title="Inception",
            movie_code="inc_2010",
            description="Mind bending dream heist",
            download_url="https://example.com/inception.mp4"
        )
        self.assertGreater(movie_id, 0)
        self.assertGreaterEqual(database.get_movie_count(), 1)

        # Lookup by code
        movie = database.get_movie_by_code("inc_2010")
        self.assertIsNotNone(movie)
        self.assertEqual(movie["title"], "Inception")

        # Search by title
        results = database.search_movies("Incep")
        self.assertGreaterEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "Inception")

if __name__ == "__main__":
    unittest.main()
