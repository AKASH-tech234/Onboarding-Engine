def validate_input(data):

    assert "skills" in data
    assert isinstance(data["skills"], list)

    for skill in data["skills"]:
        assert isinstance(skill, str)

    # Validate experience
    for exp in data.get("experience", []):
        assert "description" in exp