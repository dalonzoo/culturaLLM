
import random
from locust import HttpUser, task, between

class CulturaLLMUser(HttpUser):
    wait_time = between(1, 5)
    host = "http://localhost:5001"

    def on_start(self):
        """
        Called when a User starts. Sets up credentials and performs initial authentication.
        """
        self.token = None
        self.user_id = None
        self.headers = {}
        
        # Store credentials for re-authentication
        self.username = f"testuser_{random.randint(1, 100000)}"
        self.email = f"{self.username}@example.com"
        self.password = "testpassword"
        
        self._authenticate()

    def _authenticate(self):
        """
        Handles user registration or login to obtain/refresh an authentication token.
        """
        # First, try to log in, as it's faster if the user already exists from a previous run
        login_response = self.client.post(
            "/api/auth/login",
            json={"username": self.username, "password": self.password},
            name="/api/auth/login"
        )
        if login_response.status_code == 200:
            self.token = login_response.json()["access_token"]
            self.user_id = login_response.json()["user"]["id"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
            print(f"User {self.username} logged in successfully.")
            return

        # If login fails, the user likely doesn't exist, so register them
        register_response = self.client.post(
            "/api/auth/register",
            json={"username": self.username, "email": self.email, "password": self.password},
            name="/api/auth/register"
        )
        
        if register_response.status_code == 200:
            self.token = register_response.json()["access_token"]
            self.user_id = register_response.json()["user"]["id"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
            print(f"User {self.username} registered and logged in successfully.")
        else:
            print(f"CRITICAL: Both login and registration failed for {self.username}: {register_response.status_code} {register_response.text}")
            self.token = None
            # Stop the user if authentication is impossible
            self.environment.runner.quit()

    def _execute_request(self, method, path, name, **kwargs):
        """
        A wrapper for making requests that handles re-authentication on 401 errors.
        """
        # Add auth headers to kwargs if not present
        if 'headers' not in kwargs:
            kwargs['headers'] = {}
        kwargs['headers'].update(self.headers)

        response = self.client.request(method, path, name=name, **kwargs)
        
        if response.status_code == 401:
            print(f"Request to {name} failed with 401. Re-authenticating user {self.username}.")
            self._authenticate()
            
            # Check if re-authentication was successful
            if not self.token:
                response.failure("Re-authentication failed.")
                return response

            # Retry the request with the new token
            kwargs['headers'].update(self.headers)
            response = self.client.request(method, path, name=name, **kwargs)
        
        return response

    @task
    def full_interaction_flow(self):
        """
        Simulates the complete user interaction flow, now resilient to token expiration.
        """
        if not self.token:
            print("User has no token, attempting to authenticate before starting task.")
            self._authenticate()
            if not self.token:
                print("Authentication failed, skipping task.")
                return

        print(f"User {self.user_id} starting a new interaction flow.")

        # 1. Get a random theme
        response = self._execute_request("get", "/api/questions/random-theme", "/api/questions/random-theme")
        if response.status_code != 200:
            response.failure(f"Could not get random theme, stopping flow. Status: {response.status_code}")
            return
        theme_id = response.json()["id"]
        print(f"Step 1: Got random theme ID: {theme_id}")

        # 2. Generate a question from the theme
        response = self._execute_request("post", f"/api/questions/generate/{theme_id}", "/api/questions/generate/[theme_id]")
        if response.status_code != 200:
            response.failure(f"Could not generate question, stopping flow. Status: {response.status_code}")
            return
        question_text = response.json()["text"]
        print(f"Step 2: Generated question text: {question_text[:30]}...")

        # 3. Generate a tag for the question
        response = self._execute_request("post", "/api/questions/tag", "/api/questions/tag", json={"question": question_text})
        tag_text = None
        if response.status_code == 200:
            tag_text = response.json()["tag"]
            print(f"Step 3: Generated tag: {tag_text}")
        else:
            # Non-critical, so we just log it and continue without a tag
            print(f"Warning: Could not generate tag. Status: {response.status_code}")

        # 4. Create the question in the database
        question_data = {"text": question_text, "theme_id": theme_id, "tag": tag_text}
        response = self._execute_request("post", "/api/questions/", "/api/questions/", json=question_data)
        if response.status_code != 200:
            response.failure(f"Could not create question, stopping flow. Status: {response.status_code} - {response.text}")
            return
        question_id = response.json()["id"]
        print(f"Step 4: Created question with ID: {question_id}")

        # 5. Submit a simulated human answer
        answer_data = {"text": "Questa è una risposta simulata da un utente.", "question_id": question_id}
        response = self._execute_request("post", "/api/answers/", "/api/answers/", json=answer_data)
        answer_id = None
        if response.status_code == 200:
            answer_id = response.json()["id"]
            print(f"Step 5: Submitted human answer with ID: {answer_id}")
        elif response.status_code == 400 and "already answered" in response.text:
            print(f"User {self.user_id} already answered question {question_id}. Skipping answer submission.")
        else:
            response.failure(f"Could not submit answer, stopping flow. Status: {response.status_code} - {response.text}")
            return

        # 6. Validate the answer with LLM
        if answer_id:
            response = self._execute_request("post", f"/api/validate/llm-validate?answer_id={answer_id}", "/api/validate/llm-validate")
            if response.status_code == 200:
                print(f"Step 6: Successfully validated answer {answer_id}.")
            else:
                response.failure(f"Could not validate answer {answer_id}. Status: {response.status_code} - {response.text}")
        else:
            print("Skipping validation because answer submission failed or was skipped.")

        print(f"User {self.user_id} finished an interaction flow.")

