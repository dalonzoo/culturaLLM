
import random
from locust import HttpUser, task, between

class CulturaLLMUser(HttpUser):
    wait_time = between(1, 5)  # Simulate user think time between 1 and 5 seconds
    host = "http://localhost:5001"  # Assicurati che sia l'host corretto del tuo backend

    def on_start(self):
        """
        Called when a User starts. Simulates user registration and login to get a token.
        """
        self.token = None
        self.user_id = None
        self.headers = {}
        
        # Use unique credentials for each simulated user
        username = f"testuser_{random.randint(1, 100000)}"
        email = f"{username}@example.com"
        password = "testpassword"

        # Register
        response = self.client.post(
            "/api/auth/register",
            json={"username": username, "email": email, "password": password}
        )
        
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.user_id = response.json()["user"]["id"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            # If registration fails (e.g., user exists), try to log in
            login_response = self.client.post(
                "/api/auth/login",
                json={"username": username, "password": password}
            )
            if login_response.status_code == 200:
                self.token = login_response.json()["access_token"]
                self.user_id = login_response.json()["user"]["id"]
                self.headers = {"Authorization": f"Bearer {self.token}"}
            else:
                print(f"Login failed for {username}: {login_response.status_code} {login_response.text}")
                # Stop the user if login fails
                self.environment.runner.quit()


    @task
    def full_interaction_flow(self):
        """
        Simulates the complete user interaction flow from question generation to validation.
        """
        if not self.token:
            print("User has no token, skipping task.")
            return

        print(f"User {self.user_id} starting a new interaction flow.")

        # 1. Get a random theme
        theme_id = None
        with self.client.get("/api/questions/random-theme", headers=self.headers, name="/api/questions/random-theme") as response:
            if response.status_code == 200:
                theme_id = response.json()["id"]
                print(f"Step 1: Got random theme ID: {theme_id}")
            else:
                print(f"Error getting random theme: {response.status_code}")
                return

        # 2. Generate a question from the theme
        question_text = None
        with self.client.post(f"/api/questions/generate/{theme_id}", headers=self.headers, name="/api/questions/generate/[theme_id]") as response:
            if response.status_code == 200:
                question_text = response.json()["text"]
                print(f"Step 2: Generated question text: {question_text[:30]}...")
            else:
                print(f"Error generating question: {response.status_code}")
                return

        # 3. Generate a tag for the question
        tag_text = None
        with self.client.post("/api/questions/tag", json={"question": question_text}, headers=self.headers, name="/api/questions/tag") as response:
            if response.status_code == 200:
                tag_text = response.json()["tag"]
                print(f"Step 3: Generated tag: {tag_text}")
            else:
                print(f"Error generating tag: {response.status_code}")
                # Continue without a tag if generation fails
                
        # 4. Create the question in the database
        question_id = None
        question_data = {
            "text": question_text,
            "theme_id": theme_id,
            "tag": tag_text
        }
        with self.client.post("/api/questions/", json=question_data, headers=self.headers, name="/api/questions/") as response:
            if response.status_code == 200:
                question_id = response.json()["id"]
                print(f"Step 4: Created question with ID: {question_id}")
            else:
                print(f"Error creating question: {response.status_code} - {response.text}")
                return

        # 5. Submit a simulated human answer
        answer_id = None
        answer_data = {
            "text": "Questa è una risposta simulata da un utente.",
            "question_id": question_id
        }
        with self.client.post("/api/answers/", json=answer_data, headers=self.headers, name="/api/answers/") as response:
            if response.status_code == 200:
                answer_id = response.json()["id"]
                print(f"Step 5: Submitted human answer with ID: {answer_id}")
            elif response.status_code == 400 and "already answered" in response.text:
                 print(f"User {self.user_id} already answered question {question_id}. Skipping answer submission.")
            else:
                print(f"Error submitting answer: {response.status_code} - {response.text}")
                return
        
        # 6. Validate the answer with LLM
        # This endpoint validates both human and LLM answers.
        if answer_id:
            with self.client.post(f"/api/validate/llm-validate?answer_id={answer_id}", headers=self.headers, name="/api/validate/llm-validate") as response:
                if response.status_code == 200:
                    print(f"Step 6: Successfully validated answer {answer_id}.")
                else:
                    print(f"Error validating answer {answer_id}: {response.status_code} - {response.text}")
        else:
            print("Skipping validation because answer submission failed.")

        print(f"User {self.user_id} finished an interaction flow.")

