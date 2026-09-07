import db

def test_add_and_get_application():
    db.init_db()
    app_id = db.add_application("Test Corp", "Automation Engineer", "Test notes")
    assert app_id is not None
    
    apps = db.list_applications()
    assert len(apps) > 0
    assert apps[0]["company"] == "Test Corp"