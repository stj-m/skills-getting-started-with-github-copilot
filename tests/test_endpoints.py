"""
Tests for FastAPI endpoints using the AAA (Arrange-Act-Assert) pattern.
"""

import pytest


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client, reset_activities):
        """
        Arrange: Activities are initialized in the database
        Act: Make a GET request to /activities
        Assert: Response contains all 9 activities with correct fields
        """
        # Arrange: (done by reset_activities fixture)

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 9
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Science Club" in data

    def test_get_activities_contains_required_fields(self, client, reset_activities):
        """
        Arrange: Activities are initialized
        Act: Make a GET request to /activities
        Assert: Each activity contains description, schedule, max_participants, participants
        """
        # Arrange: (done by reset_activities fixture)

        # Act
        response = client.get("/activities")

        # Assert
        data = response.json()
        chess_club = data["Chess Club"]
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        assert isinstance(chess_club["participants"], list)

    def test_get_activities_includes_initial_participants(self, client, reset_activities):
        """
        Arrange: Chess Club has 2 initial participants
        Act: Make a GET request to /activities
        Assert: Chess Club shows both initial participants
        """
        # Arrange: (done by reset_activities fixture)

        # Act
        response = client.get("/activities")

        # Assert
        data = response.json()
        participants = data["Chess Club"]["participants"]
        assert len(participants) == 2
        assert "michael@mergington.edu" in participants
        assert "daniel@mergington.edu" in participants


class TestRootRedirect:
    """Tests for GET / endpoint"""

    def test_root_redirects_to_static_index(self, client, reset_activities):
        """
        Arrange: Root endpoint is configured
        Act: Make a GET request to /
        Assert: Response redirects to /static/index.html
        """
        # Arrange: (done by reset_activities fixture)

        # Act
        response = client.get("/", follow_redirects=False)

        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_successful(self, client, reset_activities):
        """
        Arrange: A new student email and existing activity
        Act: Make a POST request to sign up
        Assert: Response is successful and participant is added
        """
        # Arrange
        email = "newstudent@mergington.edu"
        activity = "Chess Club"
        initial_count = len(client.get("/activities").json()["Chess Club"]["participants"])

        # Act
        response = client.post(f"/activities/{activity}/signup?email={email}")

        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Signed up {email} for {activity}"
        updated_count = len(client.get("/activities").json()["Chess Club"]["participants"])
        assert updated_count == initial_count + 1

    def test_signup_adds_participant_to_list(self, client, reset_activities):
        """
        Arrange: A new student email and existing activity with initial participants
        Act: Make a POST request to sign up
        Assert: The new participant appears in the activity's participant list
        """
        # Arrange
        email = "newstudent@mergington.edu"
        activity = "Chess Club"

        # Act
        client.post(f"/activities/{activity}/signup?email={email}")

        # Assert
        response = client.get("/activities")
        participants = response.json()["Chess Club"]["participants"]
        assert email in participants

    def test_signup_duplicate_email_returns_error(self, client, reset_activities):
        """
        Arrange: A student already signed up for an activity
        Act: Attempt to sign up the same student again
        Assert: Response is 400 Bad Request
        """
        # Arrange
        email = "michael@mergington.edu"  # Already in Chess Club
        activity = "Chess Club"

        # Act
        response = client.post(f"/activities/{activity}/signup?email={email}")

        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"].lower()

    def test_signup_nonexistent_activity_returns_404(self, client, reset_activities):
        """
        Arrange: A non-existent activity name
        Act: Attempt to sign up for that activity
        Assert: Response is 404 Not Found
        """
        # Arrange
        email = "newstudent@mergington.edu"
        activity = "Non-Existent Activity"

        # Act
        response = client.post(f"/activities/{activity}/signup?email={email}")

        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_signup_multiple_students_different_activities(self, client, reset_activities):
        """
        Arrange: Two different students and two different activities
        Act: Sign up first student to first activity, second student to second activity
        Assert: Both signups succeed and participants are correctly assigned
        """
        # Arrange
        student1 = "alice@mergington.edu"
        student2 = "bob@mergington.edu"
        activity1 = "Chess Club"
        activity2 = "Programming Class"

        # Act
        response1 = client.post(f"/activities/{activity1}/signup?email={student1}")
        response2 = client.post(f"/activities/{activity2}/signup?email={student2}")

        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200
        data = client.get("/activities").json()
        assert student1 in data[activity1]["participants"]
        assert student2 in data[activity2]["participants"]

    def test_signup_same_student_different_activities(self, client, reset_activities):
        """
        Arrange: One student and two different activities
        Act: Sign up same student to both activities
        Assert: Both signups succeed and student appears in both activities
        """
        # Arrange
        email = "versatile@mergington.edu"
        activity1 = "Chess Club"
        activity2 = "Programming Class"

        # Act
        response1 = client.post(f"/activities/{activity1}/signup?email={email}")
        response2 = client.post(f"/activities/{activity2}/signup?email={email}")

        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200
        data = client.get("/activities").json()
        assert email in data[activity1]["participants"]
        assert email in data[activity2]["participants"]


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/participants/{email} endpoint"""

    def test_unregister_successful(self, client, reset_activities):
        """
        Arrange: A participant registered in an activity
        Act: Make a DELETE request to unregister
        Assert: Participant is removed and response is successful
        """
        # Arrange
        email = "michael@mergington.edu"  # Already in Chess Club
        activity = "Chess Club"
        initial_count = len(client.get("/activities").json()["Chess Club"]["participants"])

        # Act
        response = client.delete(f"/activities/{activity}/participants/{email}")

        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Unregistered {email} from {activity}"
        updated_count = len(client.get("/activities").json()["Chess Club"]["participants"])
        assert updated_count == initial_count - 1

    def test_unregister_removes_participant_from_list(self, client, reset_activities):
        """
        Arrange: A participant registered in an activity
        Act: Make a DELETE request to unregister
        Assert: Participant no longer appears in the participant list
        """
        # Arrange
        email = "michael@mergington.edu"  # Already in Chess Club
        activity = "Chess Club"

        # Act
        client.delete(f"/activities/{activity}/participants/{email}")

        # Assert
        response = client.get("/activities")
        participants = response.json()["Chess Club"]["participants"]
        assert email not in participants

    def test_unregister_nonexistent_participant_returns_404(self, client, reset_activities):
        """
        Arrange: A participant not registered in an activity
        Act: Attempt to unregister them
        Assert: Response is 404 Not Found
        """
        # Arrange
        email = "nobody@mergington.edu"  # Not registered
        activity = "Chess Club"

        # Act
        response = client.delete(f"/activities/{activity}/participants/{email}")

        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_unregister_nonexistent_activity_returns_404(self, client, reset_activities):
        """
        Arrange: A non-existent activity
        Act: Attempt to unregister from that activity
        Assert: Response is 404 Not Found
        """
        # Arrange
        email = "michael@mergington.edu"
        activity = "Non-Existent Activity"

        # Act
        response = client.delete(f"/activities/{activity}/participants/{email}")

        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_unregister_one_participant_leaves_others(self, client, reset_activities):
        """
        Arrange: An activity with multiple participants
        Act: Unregister one participant
        Assert: Other participants remain in the list
        """
        # Arrange
        email_to_remove = "michael@mergington.edu"
        email_to_keep = "daniel@mergington.edu"
        activity = "Chess Club"

        # Act
        client.delete(f"/activities/{activity}/participants/{email_to_remove}")

        # Assert
        response = client.get("/activities")
        participants = response.json()["Chess Club"]["participants"]
        assert email_to_remove not in participants
        assert email_to_keep in participants
